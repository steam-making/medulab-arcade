import json
import zipfile
import io
import re
import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.db.models import Count, Q
from django.contrib.auth import login
from django.contrib import messages
from .models import Project, Category, Like, Bookmark, Tag
from .forms import ProjectUploadForm, SignUpForm


def home(request):
    """메인 페이지 - 작품 리스트"""
    category_slug = request.GET.get('category', '')
    search = request.GET.get('q', '')

    projects = Project.objects.filter(status='approved').select_related('author').prefetch_related('categories', 'tags')

    if category_slug:
        projects = projects.filter(categories__name=category_slug)
    if search:
        projects = projects.filter(
            Q(title__icontains=search) |
            Q(author_display_name__icontains=search) |
            Q(description__icontains=search)
        )

    # 유저의 좋아요/즐겨찾기 상태
    user_likes = set()
    user_bookmarks = set()
    if request.user.is_authenticated:
        user_likes = set(Like.objects.filter(user=request.user).values_list('project_id', flat=True))
        user_bookmarks = set(Bookmark.objects.filter(user=request.user).values_list('project_id', flat=True))

    categories = Category.objects.all()
    featured = Project.objects.filter(status='approved', is_featured=True)[:4]

    total_plays = sum(p.play_count for p in Project.objects.filter(status='approved'))
    total_projects = Project.objects.filter(status='approved').count()

    context = {
        'projects': projects,
        'categories': categories,
        'featured': featured,
        'current_category': category_slug,
        'search_query': search,
        'user_likes': user_likes,
        'user_bookmarks': user_bookmarks,
        'total_plays': total_plays,
        'total_projects': total_projects,
    }
    return render(request, 'arcade/home.html', context)


def play(request, slug):
    """작품 플레이 페이지"""
    project = get_object_or_404(Project, slug=slug, status='approved')

    # 플레이 카운트 증가
    Project.objects.filter(pk=project.pk).update(play_count=project.play_count + 1)

    user_liked = False
    user_bookmarked = False
    if request.user.is_authenticated:
        user_liked = Like.objects.filter(user=request.user, project=project).exists()
        user_bookmarked = Bookmark.objects.filter(user=request.user, project=project).exists()

    context = {
        'project': project,
        'user_liked': user_liked,
        'user_bookmarked': user_bookmarked,
    }
    response = render(request, 'arcade/play.html', context)
    return xframe_options_sameorigin(lambda req: response)(request)


@login_required
@require_POST
def delete_project(request, project_id):
    """작품 삭제"""
    project = get_object_or_404(Project, pk=project_id)
    
    # 본인 또는 관리자만 삭제 가능
    if project.author != request.user and not request.user.is_staff:
        messages.error(request, '본인의 작품만 삭제할 수 있습니다.')
        return redirect('my_projects')
    
    title = project.title
    project.delete()
    messages.success(request, f'"{title}" 작품이 삭제되었습니다.')
    return redirect('my_projects')


@login_required
def edit_project(request, project_id):
    """작품 수정"""
    project = get_object_or_404(Project, pk=project_id)
    
    # 본인 또는 관리자만 수정 가능
    if project.author != request.user and not request.user.is_staff:
        messages.error(request, '본인의 작품만 수정할 수 있습니다.')
        return redirect('my_projects')
    
    if request.method == 'POST':
        form = ProjectUploadForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save()
            # ManyToMany 필드는 ModelForm.save()에서 기본적으로 처리되지만 
            # 커스텀 save 로직이 있을 수 있으니 명시적으로 확인 (ProjectUploadForm.save는 save_m2m을 지원함)
            messages.success(request, '작품 정보가 수정되었습니다! ✨')
            return redirect('my_projects')
    else:
        form = ProjectUploadForm(instance=project)
    
    context = {
        'form': form,
        'is_edit': True,
        'project': project,
    }
    return render(request, 'arcade/upload.html', context)


@login_required
def upload(request):
    """작품 업로드 페이지"""
    if request.method == 'POST':
        form = ProjectUploadForm(request.POST, request.FILES)
        if form.is_valid():
            project = form.save(commit=False)
            project.author = request.user
            # 관리자는 바로 승인, 학생은 심사 대기
            if request.user.is_staff:
                project.status = 'approved'
            else:
                project.status = 'pending'
            project.save()
            form.save_m2m()  # ManyToMany 필드(categories, tags) 저장을 위해 필구
            if project.status == 'approved':
                messages.success(request, '작품이 등록되었습니다! 🎉')
            else:
                messages.success(request, '작품이 제출되었습니다! 선생님 승인 후 공개됩니다. ⏳')
            return redirect('home')
    else:
        form = ProjectUploadForm()

    return render(request, 'arcade/upload.html', {'form': form})


@login_required
@require_POST
def analyze_zip(request):
    """ZIP 파일을 분석하여 메타데이터(arcade.json) 추출"""
    zip_file = request.FILES.get('project_zip')
    if not zip_file:
        return JsonResponse({'error': '파일이 없습니다.'}, status=400)

    try:
        with zipfile.ZipFile(io.BytesIO(zip_file.read())) as zf:
            # arcade.json 또는 arcade_info.json 파일 찾기 (대소문자 구분 없음, 최상위 또는 폴더 안 포함)
            json_path = None
            for name in zf.namelist():
                lower_name = name.lower()
                if lower_name.endswith('arcade.json') or lower_name.endswith('arcade_info.json'):
                    # 가장 얕은 경로의 파일을 선택
                    if json_path is None or name.count('/') < json_path.count('/'):
                        json_path = name
            
            if not json_path:
                # JSON이 없으면 스마트 추측 로직 실행
                result = guess_project_metadata(zf, zip_file.name)
                return JsonResponse({'success': True, 'data': result, 'guessed': True})
            
            with zf.open(json_path) as f:
                data = json.loads(f.read().decode('utf-8'))
                
                # 카테고리 이름으로 ID 조회
                category_names = data.get('categories', [])
                if isinstance(category_names, str):
                    category_names = [category_names]
                
                matched_category_ids = list(Category.objects.filter(
                    name__in=category_names
                ).values_list('id', flat=True))
                
                # 태그 리스트를 쉼표 문자열로 변환
                tags_list = data.get('tags', [])
                if isinstance(tags_list, list):
                    tags_str = ", ".join(tags_list)
                else:
                    tags_str = str(tags_list)
                    
                result = {
                    'title': data.get('title', ''),
                    'description': data.get('description', ''),
                    'tags_str': tags_str,
                    'category_ids': matched_category_ids,
                }
                return JsonResponse({'success': True, 'data': result})
                
    except Exception as e:
        return JsonResponse({'error': f'ZIP 분석 중 오류 발생: {str(e)}'}, status=500)


def guess_project_metadata(zf, zip_filename):
    """ZIP 파일의 구성과 내용을 정밀 분석하여 풍성한 정보를 추측함"""
    zip_basename = os.path.basename(zip_filename)
    title = os.path.splitext(zip_basename)[0]

    file_list = zf.namelist()
    categories = set()
    tags = set()
    features = []
    controls = []
    tech_stack = []

    # ── 1. 파일명 키워드 분석 (한글·영문 복합 매핑) ───────────────────────
    title_lower = title.lower().replace('_', ' ').replace('-', ' ')
    title_keyword_map = {
        '싸움': ['대전게임', '액션'], '전투': ['대전게임', '액션'],
        '배틀': ['대전게임', '액션'], 'battle': ['대전게임', '액션'],
        '슈팅': ['슈팅게임', '액션'], '총': ['슈팅게임'],
        'shoot': ['슈팅게임'], 'shooter': ['슈팅게임'],
        '달리기': ['러닝게임', '아케이드'], '런': ['러닝게임'],
        'run': ['러닝게임'], 'runner': ['러닝게임'],
        '퍼즐': ['퍼즐게임', '두뇌게임'], 'puzzle': ['퍼즐게임'],
        '점프': ['플랫포머', '점프액션'], 'jump': ['플랫포머'],
        '플랫폼': ['플랫포머'], 'platform': ['플랫포머'],
        '뱀': ['클래식게임', '아케이드'], 'snake': ['클래식게임', '아케이드'],
        '테트리스': ['퍼즐게임', '클래식게임'], 'tetris': ['퍼즐게임', '클래식게임'],
        '블록': ['퍼즐게임', '블록게임'], 'block': ['퍼즐게임', '블록게임'],
        '미로': ['퍼즐게임', '미로탐험'], 'maze': ['퍼즐게임', '미로탐험'],
        '피하기': ['회피게임', '아케이드'], 'dodge': ['회피게임', '아케이드'],
        '눈덩이': ['눈덩이', '겨울테마', '대전게임'],
        '눈싸움': ['눈덩이', '대전게임', '겨울테마'],
        '눈': ['겨울테마'], '겨울': ['겨울테마'],
        '축구': ['스포츠게임', '축구'], '농구': ['스포츠게임', '농구'],
        '야구': ['스포츠게임', '야구'], '스포츠': ['스포츠게임'],
        '자동차': ['레이싱', '자동차'], '레이싱': ['레이싱게임'],
        'racing': ['레이싱게임'], 'car': ['레이싱', '자동차'],
        '우주': ['우주배경', '슈팅게임'], 'space': ['우주배경'],
        'galaxy': ['우주배경', '슈팅게임'],
        '좀비': ['좀비게임', '생존게임'], 'zombie': ['좀비게임', '생존게임'],
        '타워': ['타워디펜스', '전략게임'], 'tower': ['타워디펜스'],
        '카드': ['카드게임', '보드게임'], 'card': ['카드게임'],
        '보드': ['보드게임', '전략게임'],
        '퀴즈': ['퀴즈게임', '교육용'], 'quiz': ['퀴즈게임', '교육용'],
        'rpg': ['RPG', '롤플레잉'], '롤플레잉': ['RPG'],
        '핑퐁': ['탁구게임', '아케이드'], '탁구': ['탁구게임', '아케이드'],
        'pong': ['탁구게임', '아케이드'],
        '벽돌': ['아케이드', '클래식게임'], 'breakout': ['아케이드', '클래식게임'],
        '팩맨': ['클래식게임', '아케이드'], 'pacman': ['클래식게임', '아케이드'],
        '포켓몬': ['수집게임'], '수집': ['수집게임'],
        '방어': ['타워디펜스', '전략게임'], 'defense': ['타워디펜스'],
        '생존': ['생존게임'], 'survive': ['생존게임'], 'survival': ['생존게임'],
        '탐험': ['탐험게임', 'RPG'], 'adventure': ['탐험게임'],
        '음악': ['리듬게임'], '리듬': ['리듬게임'], 'rhythm': ['리듬게임'],
    }
    for keyword, related_tags in title_keyword_map.items():
        if keyword in title_lower or keyword in title:
            for t in related_tags:
                tags.add(t)

    # ── 2. 파일 구성 기반 기술 스택 감지 ─────────────────────────────────
    has_html = any(f.endswith('.html') for f in file_list)
    has_py   = any(f.endswith('.py') for f in file_list)
    has_js   = any(f.endswith('.js') for f in file_list)
    has_css  = any(f.endswith('.css') for f in file_list)
    has_image = any(f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.bmp')) for f in file_list)
    has_sound = any(f.lower().endswith(('.mp3', '.wav', '.ogg', '.flac')) for f in file_list)
    has_json  = any(f.endswith('.json') and 'arcade' not in f.lower() for f in file_list)

    # 카테고리는 이름으로 DB에서 조회 (ID 하드코딩 방지)
    def _cat_id(name):
        try:
            return Category.objects.get(name=name).id
        except Category.DoesNotExist:
            return None

    if has_py:
        cid = _cat_id('Python')
        if cid: categories.add(cid)
        tech_stack.append('Python')
        tags.add('Python')
    if has_html or has_js:
        cid = _cat_id('HTML/JS')
        if cid: categories.add(cid)
        if has_html: tech_stack.append('HTML5')
        if has_js:   tech_stack.append('JavaScript')
    if has_css:
        cid = _cat_id('CSS')
        if cid: categories.add(cid)
        tech_stack.append('CSS3')
    if has_image:
        tags.add('이미지 활용')
    if has_sound:
        tags.add('사운드 포함')
        features.append("배경음악 및 효과음")
    if has_json:
        tags.add('데이터파일')

    # ── 3. Python 소스 정밀 스캔 ──────────────────────────────────────────
    py_files = [f for f in file_list if f.endswith('.py') and '__pycache__' not in f]
    py_files.sort(key=lambda x: (x.count('/'), 'main' not in x.lower(), 'game' not in x.lower()))

    extracted_docstring = ""

    for py_file in py_files[:5]:
        try:
            with zf.open(py_file) as f:
                content = f.read().decode('utf-8', errors='ignore')
            lower = content.lower()

            # 제작자 주석/docstring 추출
            if not extracted_docstring:
                doc = re.search(r'^\s*[\'"]{3}(.*?)[\'"]{3}', content, re.DOTALL)
                if doc:
                    extracted_docstring = doc.group(1).strip()
                else:
                    lines = content.split('\n')
                    block = []
                    for line in lines:
                        stripped = line.strip()
                        if stripped.startswith('#'):
                            block.append(stripped.lstrip('#').strip())
                        elif not stripped:
                            continue
                        else:
                            break
                    if len(block) >= 2:
                        extracted_docstring = '\n'.join(block)

            # ── Pygame 감지 ──
            if 'pygame' in lower:
                cid = _cat_id('게임')
                if cid: categories.add(cid)
                tags.add('Pygame')
                tags.add('게임개발')
                if 'Pygame' not in tech_stack:
                    tech_stack.append('Pygame')

                # 키보드 조작
                keys = []
                if any(k in content for k in ['K_LEFT', 'K_RIGHT', 'K_UP', 'K_DOWN']): keys.append('방향키')
                if 'K_SPACE' in content: keys.append('스페이스바')
                if any(k in content for k in ['K_w', 'K_a', 'K_s', 'K_d', 'K_W', 'K_A', 'K_S', 'K_D']): keys.append('WASD')
                if 'K_RETURN' in content or 'K_KP_ENTER' in content: keys.append('엔터키')
                if any(k in content for k in ['K_z', 'K_x', 'K_c', 'K_Z', 'K_X', 'K_C']): keys.append('Z/X/C키')
                if any(k in content for k in ['K_1', 'K_2', 'K_3', 'K_4']): keys.append('숫자키')
                if keys:
                    controls.append(f"키보드: {', '.join(keys)}")
                    tags.add('키보드컨트롤')

                # 마우스 조작
                if 'mouse.get_pos' in lower or 'mousebuttondown' in lower or 'mousebuttonup' in lower:
                    controls.append("마우스 클릭 / 포인터")
                    tags.add('마우스컨트롤')

                # 게임 기능
                if 'score' in lower or 'point' in lower:
                    features.append("점수 시스템 (스코어보드)")
                    tags.add('스코어경쟁')
                if 'colliderect' in lower or 'spritecollide' in lower or 'collide' in lower:
                    features.append("충돌 감지 & 물리 엔진")
                    tags.add('충돌물리')
                if 'gravity' in lower or 'jump' in lower:
                    features.append("중력 & 점프 물리")
                    tags.add('플랫포머')
                if 'level' in lower:
                    features.append("단계별 레벨 시스템")
                    tags.add('레벨시스템')
                if 'life' in lower or ' hp' in lower or 'health' in lower or 'lives' in lower:
                    features.append("체력(HP) / 목숨 시스템")
                    tags.add('HP시스템')
                if 'enemy' in lower or 'monster' in lower or 'boss' in lower:
                    features.append("적(Enemy) / 몬스터 AI")
                    tags.add('적AI')
                if 'sprite' in lower:
                    features.append("스프라이트 기반 오브젝트")
                if 'animation' in lower or 'frame' in lower:
                    features.append("스프라이트 애니메이션")
                    tags.add('애니메이션')
                if 'mixer' in lower or 'sound' in lower or 'music' in lower:
                    features.append("Pygame 사운드 믹서")
                    tags.add('사운드 포함')

                # FPS 감지
                fps_match = re.search(r'clock\.tick\((\d+)\)', content)
                if fps_match:
                    features.append(f"게임 루프 {fps_match.group(1)} FPS 고정")

                # 장르 정밀 추론
                if any(w in lower for w in ['bullet', 'shoot', 'fire', 'laser', 'missile', 'projectile']):
                    tags.add('슈팅게임')
                if any(w in lower for w in ['gravity', 'jump', 'platform', 'fall']):
                    tags.add('플랫포머')
                if any(w in lower for w in ['puzzle', 'match', 'board', 'tile', 'grid']):
                    tags.add('퍼즐게임')
                if any(w in lower for w in ['snow', 'snowball', 'ice']):
                    tags.add('겨울테마')

                # 2인용 감지
                if any(w in lower for w in ['player1', 'player2', 'player_1', 'player_2', ' p1 ', ' p2 ']):
                    tags.add('2인용')
                    features.append("2인 대전 모드")

            # ── Turtle 감지 ──
            if 'turtle' in lower:
                tags.add('터틀그래픽')
                tags.add('기초코딩')
                if 'Turtle' not in tech_stack: tech_stack.append('Turtle')
                features.append("거북이(Turtle) 그래픽")

            # ── AI/ML 라이브러리 감지 ──
            ml_libs = {'numpy': 'NumPy', 'pandas': 'Pandas', 'tensorflow': 'TensorFlow',
                       'keras': 'Keras', 'sklearn': 'Scikit-learn', 'torch': 'PyTorch',
                       'cv2': 'OpenCV', 'matplotlib': 'Matplotlib'}
            for lib, lib_name in ml_libs.items():
                if lib in lower:
                    if lib_name not in tech_stack: tech_stack.append(lib_name)
                    if lib in ('tensorflow', 'keras', 'torch', 'sklearn'):
                        cid = _cat_id('AI/ML')
                        if cid: categories.add(cid)
                        tags.add('AI/ML')
                    if lib in ('numpy', 'pandas'):
                        tags.add('데이터분석')
                    if lib == 'matplotlib':
                        tags.add('데이터시각화')
                    if lib == 'cv2':
                        tags.add('이미지처리')
                        features.append("OpenCV 이미지 처리")

            # ── 코드 구조 감지 ──
            if 'random' in lower:
                tags.add('랜덤요소')
            if content.count('class ') >= 2:
                tags.add('객체지향')
            if content.count('def ') >= 5:
                tags.add('함수활용')
            if 'threading' in lower or 'multiprocessing' in lower:
                features.append("멀티스레딩")
            if 'socket' in lower or 'network' in lower:
                features.append("네트워크 통신")
                tags.add('네트워크')
            if 'tkinter' in lower:
                tech_stack.append('Tkinter')
                tags.add('GUI앱')
                features.append("Tkinter GUI 인터페이스")
            if 'sqlite' in lower or 'database' in lower or 'db.' in lower:
                features.append("데이터베이스 연동")
                tags.add('DB활용')

        except Exception:
            continue

    # ── 4. HTML / JS 정밀 스캔 ────────────────────────────────────────────
    web_files = [f for f in file_list if f.endswith(('.html', '.js'))]
    web_files.sort(key=lambda x: (x.count('/'), 'index' not in x.lower(), 'main' not in x.lower(), 'game' not in x.lower()))

    for web_file in web_files[:5]:
        try:
            with zf.open(web_file) as f:
                content = f.read().decode('utf-8', errors='ignore')
            lower = content.lower()

            # 제작자 주석 추출
            if not extracted_docstring:
                if web_file.endswith('.html'):
                    doc = re.search(r'<!--\s*(.*?)-->', content[:3000], re.DOTALL)
                    if doc and len(doc.group(1).strip()) > 10:
                        extracted_docstring = doc.group(1).strip()
                elif web_file.endswith('.js'):
                    doc = re.search(r'/\*[\*!]?\s*(.*?)\*/', content[:3000], re.DOTALL)
                    if doc and len(doc.group(1).strip()) > 10:
                        extracted_docstring = doc.group(1).strip()

            # Canvas / WebGL
            if '<canvas' in lower or "createelement('canvas')" in lower or 'createelement("canvas")' in lower:
                cid = _cat_id('게임')
                if cid: categories.add(cid)
                tags.add('HTML5캔버스')
                tags.add('게임개발')
                if 'Canvas API' not in tech_stack: tech_stack.append('Canvas API')
                features.append("HTML5 Canvas 2D 렌더링")
            if 'webgl' in lower or 'three.js' in lower or 'three(' in lower:
                tags.add('WebGL3D')
                if 'Three.js' not in tech_stack: tech_stack.append('Three.js')
                features.append("WebGL / 3D 그래픽")

            # 게임 루프
            if 'requestanimationframe' in lower:
                features.append("게임 루프 (requestAnimationFrame)")
                tags.add('웹애니메이션')

            # 키보드 조작
            keys = []
            if any(w in lower for w in ['arrowleft', 'arrowright', 'arrowup', 'arrowdown']): keys.append('방향키')
            if any(w in lower for w in ['"space"', "'space'", 'keycode===32', 'keycode==32', 'keycode === 32']): keys.append('스페이스바')
            if any(w in lower for w in ['key==="w"', "key==='w'", 'keycode===87', 'keycode==87']): keys.append('WASD')
            if any(w in lower for w in ['key==="enter"', "key==='enter'", 'keycode===13']): keys.append('엔터키')
            if keys:
                controls.append(f"키보드: {', '.join(keys)}")
                tags.add('키보드조작')
            elif any(w in lower for w in ['addeventlistener("keydown"', "addeventlistener('keydown'", 'onkeydown']):
                controls.append("키보드 인터랙션")
                tags.add('키보드조작')

            # 마우스 / 터치
            if any(w in lower for w in ['mousedown', 'mouseup', 'addeventlistener("click"', "addeventlistener('click'"]):
                controls.append("마우스 클릭")
                tags.add('마우스클릭')
            if 'touchstart' in lower or 'touchmove' in lower:
                controls.append("터치스크린")
                tags.add('모바일지원')

            # 점수 / 레벨
            if 'score' in lower:
                features.append("점수 시스템")
                tags.add('스코어경쟁')
            if 'level' in lower:
                features.append("레벨 시스템")
                tags.add('레벨시스템')
            if 'highscore' in lower or 'high_score' in lower or 'best' in lower:
                features.append("최고점수 기록")
            if 'localstorage' in lower:
                features.append("최고점수 저장 (LocalStorage)")
                tags.add('기록저장')

            # 오디오
            if '<audio' in lower or 'new audio(' in lower or 'audiocontext' in lower:
                tags.add('웹사운드')
                features.append("웹 오디오 재생")

            # 체력 / 레이어
            if any(w in lower for w in ['lives', 'health', ' hp', 'lifes']):
                features.append("체력 / 목숨 시스템")
                tags.add('HP시스템')
            if 'enemy' in lower or 'monster' in lower:
                features.append("적(Enemy) 오브젝트")
                tags.add('적AI')

            # 장르 정밀 추론
            if any(w in lower for w in ['bullet', 'shoot', 'fire', 'laser', 'missile']):
                tags.add('슈팅게임')
            if any(w in lower for w in ['gravity', 'jump', 'platform', 'fall']):
                tags.add('플랫포머')
            if any(w in lower for w in ['puzzle', 'match', 'board', 'tile', 'grid']):
                tags.add('퍼즐게임')
            if any(w in lower for w in ['snow', 'snowball', 'ice']):
                tags.add('겨울테마')

            # 2인용
            if any(w in lower for w in ['player1', 'player2', 'p1', 'p2']):
                tags.add('2인용')
                features.append("2인 대전")

            # 기술 감지
            if 'math.random' in lower:
                tags.add('랜덤요소')
            if 'fetch(' in lower or 'xmlhttprequest' in lower or 'axios' in lower:
                features.append("외부 API 통신")
                tags.add('API연동')
            if 'websocket' in lower:
                features.append("WebSocket 실시간 통신")
                tags.add('실시간통신')

        except Exception:
            continue

    # ── 5. 중복 제거 (순서 유지) ──────────────────────────────────────────
    seen = set()
    features   = [x for x in features   if not (x in seen or seen.add(x))]
    seen = set()
    controls   = [x for x in controls   if not (x in seen or seen.add(x))]
    seen = set()
    tech_stack = [x for x in tech_stack if not (x in seen or seen.add(x))]

    # ── 6. 설명 생성 (구조화된 한국어 형식) ──────────────────────────────
    genre_priority = ['슈팅게임', '플랫포머', '퍼즐게임', '러닝게임', '대전게임',
                      '레이싱게임', '보드게임', '카드게임', '퀴즈게임', '타워디펜스',
                      'RPG', '탐험게임', '리듬게임', '생존게임', '클래식게임', '아케이드']
    detected_genre = next((t for t in genre_priority if t in tags), None)
    if detected_genre is None:
        detected_genre = "게임" if (_cat_id('게임') in categories) else "프로그램"

    tech_str = ' · '.join(tech_stack) if tech_stack else '웹 기술'

    desc_parts = []

    # 제작자 노트
    if extracted_docstring:
        clean_doc = re.sub(r'\n{3,}', '\n\n', extracted_docstring.strip())
        desc_parts.append(f"📝 제작자 소개\n{clean_doc}")

    # 본문 소개
    intro = f"📌 작품 소개\n{title}은(는) {tech_str}로 제작된 {detected_genre}입니다."
    if '2인용' in tags:
        intro += "\n두 플레이어가 함께 즐길 수 있는 대전 방식의 게임입니다."
    if '겨울테마' in tags:
        intro += "\n눈과 얼음을 소재로 한 겨울 테마 작품입니다."
    desc_parts.append(intro)

    # 조작법
    if controls:
        ctrl_lines = '\n'.join(f"  • {c}" for c in controls)
        desc_parts.append(f"🕹️ 조작법\n{ctrl_lines}")

    # 주요 기능
    if features:
        feat_lines = '\n'.join(f"  • {f}" for f in features[:7])
        desc_parts.append(f"⭐ 주요 기능\n{feat_lines}")

    # 기술 스택
    if tech_stack:
        desc_parts.append(f"🛠️ 기술 스택\n  {tech_str}")

    desc_parts.append("✨ 직접 실행해보고 의견을 남겨주세요!")
    description = '\n\n'.join(desc_parts)

    # ── 7. 태그 우선순위 정렬 → 상위 10개 선택 ───────────────────────────
    TAG_PRIORITY = [
        # 장르 (가장 중요)
        '슈팅게임', '플랫포머', '퍼즐게임', '러닝게임', '대전게임', '레이싱게임',
        '보드게임', '카드게임', 'RPG', '타워디펜스', '리듬게임', '생존게임',
        '클래식게임', '아케이드', '탐험게임', '퀴즈게임', '회피게임',
        # 특수 테마
        '2인용', '겨울테마', '눈덩이', '우주배경', '좀비게임',
        # 핵심 기술
        'Pygame', 'HTML5캔버스', 'JavaScript', 'Python',
        # 게임 기능
        '스코어경쟁', '레벨시스템', 'HP시스템', '적AI', '충돌물리',
        # 입력
        '키보드컨트롤', '키보드조작', '마우스컨트롤', '마우스클릭', '모바일지원',
        # 기타
        '랜덤요소', '사운드 포함', '이미지 활용', '애니메이션',
        '기록저장', '게임개발', '객체지향', '함수활용',
    ]
    sorted_tags = []
    for p in TAG_PRIORITY:
        if p in tags:
            sorted_tags.append(p)
    for t in sorted(tags):
        if t not in sorted_tags:
            sorted_tags.append(t)

    final_tags = sorted_tags[:10]

    return {
        'title': title,
        'description': description,
        'tags_str': ', '.join(final_tags),
        'category_ids': list(categories),
    }


@login_required
def my_projects(request):
    """내 작품 관리 (선생님은 모든 작품, 학생은 본인 작품)"""
    if request.user.is_staff:
        # 선생님은 모든 작품을 최신순으로 조회
        projects = Project.objects.all().select_related('author').prefetch_related('categories', 'tags').order_by('-created_at')
    else:
        # 학생은 본인이 올린 작품만 조회
        projects = Project.objects.filter(author=request.user).select_related('author').prefetch_related('categories', 'tags').order_by('-created_at')
    
    return render(request, 'arcade/my_projects.html', {
        'projects': projects,
        'is_teacher': request.user.is_staff
    })


@login_required
def approve_project(request, project_id):
    """작품 즉시 승인 (선생님 전용)"""
    if not request.user.is_staff:
        messages.error(request, '작품 승인 권한이 없습니다.')
        return redirect('my_projects')
        
    project = get_object_or_404(Project, pk=project_id)
    project.status = 'approved'
    project.save()
    
    messages.success(request, f'"{project.title}" 작품이 승인되어 아케이드에 공개되었습니다! 🚀')
    return redirect('my_projects')


@require_POST
@login_required
def toggle_like(request, project_id):
    """좋아요 토글 (AJAX)"""
    project = get_object_or_404(Project, pk=project_id)
    like, created = Like.objects.get_or_create(user=request.user, project=project)
    if not created:
        like.delete()
    return JsonResponse({
        'liked': created,
        'count': project.likes.count(),
    })


@require_POST
@login_required
def toggle_bookmark(request, project_id):
    """즐겨찾기 토글 (AJAX)"""
    project = get_object_or_404(Project, pk=project_id)
    bookmark, created = Bookmark.objects.get_or_create(user=request.user, project=project)
    if not created:
        bookmark.delete()
    return JsonResponse({
        'bookmarked': created,
        'count': project.bookmarks.count(),
    })


def signup(request):
    """회원가입"""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '가입 완료! 환영합니다! 🎮')
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'arcade/signup.html', {'form': form})
