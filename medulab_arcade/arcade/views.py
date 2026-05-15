import json
import zipfile
import io
import re
import os
import uuid
import base64
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.db import DatabaseError
from django.db.models import Count, Q
from django.contrib.auth import login
from django.contrib import messages
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from .badge_service import get_active_badges_with_user_state, get_recent_user_badges, get_user_badge_count
from .models import Badge, Project, Category, Like, Bookmark, Tag, UserProfile, EmailChangeRequest, SignupEmailVerification, ScheduleEvent
from .forms import ProjectUploadForm, SignUpForm, AdminUserForm, AdminUserProfileForm, BadgeForm, ScheduleEventForm, UserProfileUpdateForm


SCHEDULE_EVENT_COLORS = {
    ScheduleEvent.EVENT_TYPE_HOLIDAY: '#ff5d6c',
    ScheduleEvent.EVENT_TYPE_ACADEMIC: '#3b82f6',
    ScheduleEvent.EVENT_TYPE_COMPETITION: '#f5c451',
    ScheduleEvent.EVENT_TYPE_SEMINAR: '#00ffb4',
}


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


def schedule_view(request):
    events = ScheduleEvent.objects.filter(is_active=True).order_by('start_date', 'end_date', 'title')
    today = timezone.localdate()
    upcoming_events = events.filter(start_date__gte=today)
    calendar_events = []

    for event in events:
        color = SCHEDULE_EVENT_COLORS.get(event.event_type, '#00b4ff')
        calendar_events.append({
            'id': event.id,
            'title': event.title,
            'start': event.start_date.isoformat(),
            'end': (event.end_date + timedelta(days=1)).isoformat(),
            'backgroundColor': color,
            'borderColor': color,
            'textColor': '#08080f' if event.event_type in {ScheduleEvent.EVENT_TYPE_COMPETITION, ScheduleEvent.EVENT_TYPE_SEMINAR} else '#ffffff',
            'extendedProps': {
                'description': event.description,
                'eventType': event.event_type,
                'eventTypeLabel': event.get_event_type_display(),
            },
        })

    context = {
        'calendar_events_json': calendar_events,
        'upcoming_competitions': upcoming_events.filter(event_type=ScheduleEvent.EVENT_TYPE_COMPETITION)[:4],
        'seminar_events': upcoming_events.filter(event_type__in=[ScheduleEvent.EVENT_TYPE_ACADEMIC, ScheduleEvent.EVENT_TYPE_SEMINAR])[:6],
    }
    return render(request, 'arcade/schedule.html', context)


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
def project_preview(request, project_id):
    """관리자/작성자용 작품 미리보기 페이지"""
    project = get_object_or_404(Project, pk=project_id)
    if not (request.user.is_staff or request.user == project.author):
        messages.error(request, '작품 미리보기 권한이 없습니다.')
        return redirect('my_projects')

    user_liked = False
    user_bookmarked = False
    if request.user.is_authenticated:
        user_liked = Like.objects.filter(user=request.user, project=project).exists()
        user_bookmarked = Bookmark.objects.filter(user=request.user, project=project).exists()

    context = {
        'project': project,
        'user_liked': user_liked,
        'user_bookmarked': user_bookmarked,
        'is_preview_mode': True,
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
        form = ProjectUploadForm(request.POST, request.FILES, instance=project, user=request.user)
        if form.is_valid():
            updated = form.save(commit=False)
            
            # 일반 사용자는 본인이 제작자여야 하며 제작자를 바꿀 수 없음
            if not request.user.is_staff:
                updated.author = request.user
            # 수동 썸네일이 없고 자동 썸네일이 전달된 경우 적용
            if not request.FILES.get('thumbnail'):
                import json as _json
                raw = request.POST.get('auto_thumbnail_b64_list', '')
                try:
                    b64_list = _json.loads(raw) if raw else []
                except Exception:
                    b64_list = [request.POST.get('auto_thumbnail_b64', '')]
                _apply_auto_thumbnails(updated, b64_list)
            updated.save()
            form.save_m2m()
            messages.success(request, '작품 정보가 수정되었습니다! ✨')
            return redirect('my_projects')
    else:
        form = ProjectUploadForm(instance=project, user=request.user)
    
    context = {
        'form': form,
        'is_edit': True,
        'project': project,
    }
    return render(request, 'arcade/upload.html', context)


def _apply_auto_thumbnails(project, b64_list):
    """base64 PNG 리스트를 Project thumbnail/thumbnail_2/thumbnail_3에 설정"""
    fields = ['thumbnail', 'thumbnail_2', 'thumbnail_3']
    for i, b64_data in enumerate(b64_list[:3]):
        if not b64_data:
            continue
        try:
            img_bytes = base64.b64decode(b64_data)
            img_io = io.BytesIO(img_bytes)
            filename = f'auto_{uuid.uuid4().hex[:8]}.png'
            setattr(project, fields[i], InMemoryUploadedFile(
                img_io, fields[i], filename, 'image/png', len(img_bytes), None
            ))
        except Exception:
            continue


@login_required
def upload(request):
    """작품 업로드 페이지"""
    if request.method == 'POST':
        form = ProjectUploadForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            project = form.save(commit=False)
            
            # 제작자 결정: 관리자면 폼 선택값 우선, 아니면 현재 사용자
            if not request.user.is_staff or not project.author:
                project.author = request.user
            # 수동 썸네일이 없을 때 자동 생성 썸네일 적용 (최대 3개)
            if not request.FILES.get('thumbnail'):
                import json as _json
                raw = request.POST.get('auto_thumbnail_b64_list', '')
                try:
                    b64_list = _json.loads(raw) if raw else []
                except Exception:
                    b64_list = [request.POST.get('auto_thumbnail_b64', '')]
                _apply_auto_thumbnails(project, b64_list)
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
        form = ProjectUploadForm(user=request.user)

    return render(request, 'arcade/upload.html', {'form': form})


@login_required
@require_POST
def analyze_zip(request):
    """ZIP 파일을 분석하여 메타데이터(arcade.json) 추출 + 썸네일 자동 생성"""
    zip_file = request.FILES.get('project_zip')
    if not zip_file:
        return JsonResponse({'error': '파일이 없습니다.'}, status=400)

    try:
        zip_bytes = zip_file.read()
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            # arcade.json 또는 arcade_info.json 파일 찾기
            json_path = None
            for name in zf.namelist():
                lower_name = name.lower()
                if lower_name.endswith('arcade.json') or lower_name.endswith('arcade_info.json'):
                    if json_path is None or name.count('/') < json_path.count('/'):
                        json_path = name

            guessed = False
            if not json_path:
                result = guess_project_metadata(zf, zip_file.name)
                guessed = True
            else:
                with zf.open(json_path) as f:
                    data = json.loads(f.read().decode('utf-8'))
                category_names = data.get('categories', [])
                if isinstance(category_names, str):
                    category_names = [category_names]
                matched_category_ids = list(Category.objects.filter(
                    name__in=category_names
                ).values_list('id', flat=True))
                tags_list = data.get('tags', [])
                tags_str = ', '.join(tags_list) if isinstance(tags_list, list) else str(tags_list)
                result = {
                    'title': data.get('title', ''),
                    'description': data.get('description', ''),
                    'tags_str': tags_str,
                    'category_ids': matched_category_ids,
                }

            # 썸네일 자동 생성 (최대 3개)
            tags_set = set(t.strip() for t in result.get('tags_str', '').split(',') if t.strip())
            result['thumbnail_b64_list'] = generate_auto_thumbnails(zf, result.get('title', ''), tags_set)
            # 하위 호환
            result['thumbnail_b64'] = result['thumbnail_b64_list'][0] if result['thumbnail_b64_list'] else ''

            return JsonResponse({'success': True, 'data': result, 'guessed': guessed})

    except Exception as e:
        return JsonResponse({'error': f'ZIP 분석 중 오류 발생: {str(e)}'}, status=500)


def _get_pil_font(size):
    """한글 지원 폰트 탐색 (없으면 기본 폰트)"""
    from PIL import ImageFont
    candidates = [
        # Windows
        'C:/Windows/Fonts/malgun.ttf',
        'C:/Windows/Fonts/malgunbd.ttf',
        'C:/Windows/Fonts/gulim.ttc',
        'C:/Windows/Fonts/arial.ttf',
        # Linux/Mac
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/System/Library/Fonts/AppleSDGothicNeo.ttc',
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def generate_auto_thumbnails(zf, title, tags):
    """
    ZIP 안에서 이미지를 최대 3장 추출하거나, 부족하면 Pillow로 3가지 스타일 썸네일을 생성.
    반환값: base64 PNG 문자열 리스트 (최대 3개, 실패 항목은 제외)
    """
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return []

    THUMB_W, THUMB_H = 480, 270

    # ── 장르별 포인트 색상 ─────────────────────────────────────────────────
    GENRE_COLORS = {
        '슈팅게임': (233, 69, 96),   '플랫포머': (75, 160, 255),
        '퍼즐게임': (160, 100, 255),  '러닝게임': (0, 220, 130),
        '대전게임': (255, 140, 0),    'RPG': (200, 80, 255),
        '아케이드': (0, 210, 200),    '겨울테마': (100, 200, 255),
        'AI/ML': (0, 255, 160),       '퀴즈게임': (255, 200, 0),
        '타워디펜스': (255, 100, 50), '리듬게임': (255, 80, 200),
        'Pygame': (100, 180, 100),    'HTML5캔버스': (255, 165, 0),
    }
    accent = (233, 69, 96)
    for genre, color in GENRE_COLORS.items():
        if genre in tags:
            accent = color
            break
    ar, ag, ab = accent

    # ── 폰트 준비 ─────────────────────────────────────────────────────────
    font_big   = _get_pil_font(40)
    font_mid   = _get_pil_font(22)
    font_tag   = _get_pil_font(13)
    font_small = _get_pil_font(12)
    font_wm    = _get_pil_font(11)

    # ── 태그 우선순위 정렬 ────────────────────────────────────────────────
    priority_order = [
        '슈팅게임', '플랫포머', '퍼즐게임', '러닝게임', '대전게임', 'RPG',
        '아케이드', '겨울테마', 'AI/ML', '퀴즈게임', '타워디펜스', '리듬게임',
        'Pygame', 'HTML5캔버스', '2인용', '스코어경쟁', '키보드컨트롤',
    ]
    show_tags = [t for t in priority_order if t in tags][:4]
    if not show_tags:
        show_tags = sorted(tags)[:4]

    display_title = title if len(title) <= 11 else title[:10] + '…'

    results = []

    # ── ZIP 안 실제 이미지 먼저 최대 3장 추출 ─────────────────────────────
    image_exts = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')
    priority_kw = ['screenshot', 'thumbnail', 'thumb', 'preview', 'cover', 'banner']
    candidates = []
    for name in zf.namelist():
        lower = name.lower()
        base_n = os.path.basename(lower)
        if not lower.endswith(image_exts):
            continue
        score = sum(10 for kw in priority_kw if kw in base_n)
        if lower.count('/') == 0:
            score += 5
        candidates.append((score, name))
    candidates.sort(key=lambda x: -x[0])

    for _, img_name in candidates[:3]:
        try:
            with zf.open(img_name) as f:
                raw = f.read()
            img = Image.open(io.BytesIO(raw)).convert('RGB')
            img.thumbnail((THUMB_W, THUMB_H), Image.LANCZOS)
            canvas = Image.new('RGB', (THUMB_W, THUMB_H), (18, 18, 35))
            canvas.paste(img, ((THUMB_W - img.width) // 2, (THUMB_H - img.height) // 2))
            buf = io.BytesIO()
            canvas.save(buf, format='PNG', optimize=True)
            results.append(base64.b64encode(buf.getvalue()).decode())
        except Exception:
            continue

    # ── 부족한 슬롯은 Pillow 생성으로 채움 ───────────────────────────────
    needed = 3 - len(results)
    if needed <= 0:
        return results[:3]

    def _draw_tag_chips(draw, tags_list, cx_start, cy, font, accent_rgb):
        """태그 칩 row 그리기 (중앙 정렬)"""
        if not tags_list:
            return
        pad_x, chip_h, gap = 12, 22, 7
        widths = []
        for t in tags_list:
            bb = draw.textbbox((0, 0), t, font=font)
            widths.append(bb[2] - bb[0] + pad_x * 2)
        total = sum(widths) + gap * (len(tags_list) - 1)
        x = cx_start - total // 2
        ar2, ag2, ab2 = accent_rgb
        for i, t in enumerate(tags_list):
            w = widths[i]
            draw.rounded_rectangle(
                [(x, cy), (x + w, cy + chip_h)], radius=11,
                fill=(min(ar2 + 40, 255), min(ag2 + 30, 255), min(ab2 + 30, 255)),
            )
            bb = draw.textbbox((0, 0), t, font=font)
            draw.text((x + (w - (bb[2] - bb[0])) // 2, cy + 4), t,
                      font=font, fill=(255, 255, 255))
            x += w + gap

    def _img_to_b64(img):
        buf = io.BytesIO()
        img.save(buf, format='PNG', optimize=True)
        return base64.b64encode(buf.getvalue()).decode()

    def _watermark(draw, accent_rgb):
        draw.text((10, THUMB_H - 20), 'MEDULAB ARCADE', font=font_wm, fill=accent_rgb)

    # ── 스타일 1: 포스터 (어두운 그라디언트 + 중앙 제목 + 태그 칩) ───────
    if needed > 0:
        img = Image.new('RGB', (THUMB_W, THUMB_H))
        draw = ImageDraw.Draw(img)
        for y in range(THUMB_H):
            t = y / THUMB_H
            draw.line([(0, y), (THUMB_W, y)],
                      fill=(int(12 + t * 8), int(12 + t * 6), int(28 + t * 20)))
        # 후광 원
        for cx, cy, rad, ratio in [(390, 55, 85, 0.07), (75, 225, 60, 0.05)]:
            c = (int(ar * ratio + 12), int(ag * ratio + 12), int(ab * ratio + 28))
            for dr in range(rad, 0, -5):
                draw.ellipse([(cx - dr, cy - dr), (cx + dr, cy + dr)], outline=c)
        draw.rectangle([(0, 0), (THUMB_W, 5)], fill=accent)
        # 제목
        bb = draw.textbbox((0, 0), display_title, font=font_big)
        tx = (THUMB_W - (bb[2] - bb[0])) // 2
        draw.text((tx + 2, 95), display_title, font=font_big, fill=(0, 0, 0))
        draw.text((tx, 93), display_title, font=font_big, fill=(255, 255, 255))
        # 태그 칩
        _draw_tag_chips(draw, show_tags[:3], THUMB_W // 2, 152, font_tag, accent)
        draw.rectangle([(0, THUMB_H - 4), (THUMB_W, THUMB_H)], fill=accent)
        _watermark(draw, accent)
        results.append(_img_to_b64(img))
        needed -= 1

    # ── 스타일 2: 스포트라이트 (액센트 방사형 + 큰 이모지/제목 하단) ──────
    if needed > 0:
        img = Image.new('RGB', (THUMB_W, THUMB_H), (10, 10, 22))
        draw = ImageDraw.Draw(img)
        # 중앙 방사형 그라디언트 (동심원으로 근사)
        max_r = int((THUMB_W ** 2 + THUMB_H ** 2) ** 0.5 // 2) + 10
        for r in range(max_r, 0, -4):
            ratio = r / max_r
            bg = (int(ar * (1 - ratio) * 0.45 + 10),
                  int(ag * (1 - ratio) * 0.45 + 10),
                  int(ab * (1 - ratio) * 0.45 + 22))
            draw.ellipse(
                [(THUMB_W // 2 - r, THUMB_H // 2 - r),
                 (THUMB_W // 2 + r, THUMB_H // 2 + r)],
                fill=bg,
            )
        # 제목 하단 좌측
        draw.text((22, THUMB_H - 78), display_title, font=font_big, fill=(255, 255, 255))
        # 장르 태그 한 줄
        genre_tag = show_tags[0] if show_tags else ''
        if genre_tag:
            bb = draw.textbbox((0, 0), genre_tag, font=font_mid)
            draw.rounded_rectangle(
                [(20, THUMB_H - 44), (20 + bb[2] - bb[0] + 20, THUMB_H - 20)],
                radius=10, fill=accent,
            )
            draw.text((30, THUMB_H - 42), genre_tag, font=font_mid, fill=(255, 255, 255))
        # 우측 상단 PLAY 버튼 느낌
        draw.rounded_rectangle([(THUMB_W - 80, 14), (THUMB_W - 14, 44)],
                                radius=15, fill=accent)
        bb = draw.textbbox((0, 0), 'PLAY', font=font_tag)
        draw.text((THUMB_W - 80 + (66 - (bb[2] - bb[0])) // 2, 22),
                  'PLAY', font=font_tag, fill=(255, 255, 255))
        _watermark(draw, accent)
        results.append(_img_to_b64(img))
        needed -= 1

    # ── 스타일 3: 피처 카드 (기능 목록 + 기술 스택) ──────────────────────
    if needed > 0:
        img = Image.new('RGB', (THUMB_W, THUMB_H), (14, 14, 26))
        draw = ImageDraw.Draw(img)
        # 좌측 액센트 세로 바
        draw.rectangle([(0, 0), (5, THUMB_H)], fill=accent)
        # 상단 제목
        draw.text((20, 20), display_title, font=font_mid, fill=(255, 255, 255))
        bb = draw.textbbox((0, 0), display_title, font=font_mid)
        lx = 20 + bb[2] - bb[0] + 10
        draw.line([(lx, 32), (THUMB_W - 20, 32)],
                  fill=(ar // 3, ag // 3, ab // 3), width=1)
        # 특징 목록 (태그 → bullet list)
        bullets = show_tags[:4]
        if not bullets:
            bullets = ['직접 플레이해보세요!']
        for i, b in enumerate(bullets):
            y = 50 + i * 28
            draw.rounded_rectangle([(18, y + 2), (26, y + 14)],
                                    radius=4, fill=accent)
            draw.text((34, y), b, font=font_small, fill=(220, 220, 220))
        # 하단 기술 스택
        tech_tags = [t for t in show_tags if t in ('Pygame', 'HTML5캔버스', 'JavaScript',
                                                     'Python', 'AI/ML', 'CSS3')][:3]
        if tech_tags:
            draw.text((20, THUMB_H - 38), '🛠  ' + '  ·  '.join(tech_tags),
                      font=font_small, fill=(ar, ag, ab))
        draw.rectangle([(0, THUMB_H - 4), (THUMB_W, THUMB_H)], fill=accent)
        _watermark(draw, accent)
        results.append(_img_to_b64(img))

    return results[:3]


# 하위 호환용 단일 반환 래퍼
def generate_auto_thumbnail(zf, title, tags):
    results = generate_auto_thumbnails(zf, title, tags)
    return results[0] if results else ''


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


def check_username(request):
    """아이디(Username) 중복 확인 API (AJAX)"""
    username = request.GET.get('username', '').strip()
    if not username:
        return JsonResponse({'available': False, 'message': '아이디를 입력해주세요.'})
    
    exists = User.objects.filter(username__iexact=username).exists()
    return JsonResponse({
        'available': not exists,
        'message': '이미 사용 중인 아이디입니다.' if exists else '사용 가능한 아이디입니다.'
    })


def signup(request):
    """회원가입"""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_active = False
            user.save(update_fields=['is_active'])
            verification = SignupEmailVerification.issue(user)
            confirm_url = request.build_absolute_uri(reverse('confirm_signup_email', args=[verification.token]))
            subject = '[메듀랩] 회원가입 이메일 인증'
            body = (
                f'{user.username}님, 메듀랩 회원가입을 완료하려면 아래 링크를 눌러 주세요.\n\n'
                f'{confirm_url}\n\n'
                '이 링크는 24시간 동안만 유효합니다.'
            )
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@medulab.local')
            try:
                send_mail(subject, body, from_email, [user.email], fail_silently=False)
                messages.success(request, '회원가입 정보가 저장되었습니다. 입력한 이메일 주소로 인증 메일을 보냈습니다. 링크를 눌러 가입을 완료해 주세요.')
            except Exception:
                messages.warning(request, '회원가입 정보는 저장되었지만 인증 메일 발송에 실패했습니다. 이메일 설정 확인 후 다시 시도해 주세요.')
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'arcade/signup.html', {'form': form})


@login_required
def profile_view(request):
    """마이페이지 - 대시보드 및 정보 수정"""
    user = request.user
    profile = user.profile
    
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=profile, user=user)
        if form.is_valid():
            new_email = form.cleaned_data.get('email')
            email_changed = form.email_changed()
            form.save()
            if email_changed:
                change_request = EmailChangeRequest.issue(user, new_email)
                confirm_url = request.build_absolute_uri(reverse('confirm_email_change', args=[change_request.token]))
                subject = '[메듀랩] 이메일 변경 인증'
                body = (
                    f'{user.username}님의 이메일 변경 요청입니다.\n\n'
                    f'아래 링크를 눌러야 새 이메일 주소로 변경됩니다.\n'
                    f'{confirm_url}\n\n'
                    '이 링크는 24시간 동안만 유효합니다.'
                )
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@medulab.local')
                try:
                    send_mail(subject, body, from_email, [new_email], fail_silently=False)
                    messages.success(request, '프로필 정보는 저장되었고, 새 이메일 주소로 인증 메일을 보냈습니다. 링크를 눌러야 이메일이 변경됩니다.')
                except Exception:
                    messages.warning(request, '프로필 정보는 저장되었지만 인증 메일 발송에 실패했습니다. 이메일 설정을 확인한 뒤 다시 시도해 주세요.')
            else:
                messages.success(request, '회원 정보가 성공적으로 수정되었습니다.')
            return redirect('profile')
    else:
        form = UserProfileUpdateForm(instance=profile, user=user)
    
    # 활동 통계 및 내역 조회
    my_projects = Project.objects.filter(author=user).prefetch_related('categories')
    liked_projects = Project.objects.filter(likes__user=user).prefetch_related('author', 'categories')
    bookmarked_projects = Project.objects.filter(bookmarks__user=user).prefetch_related('author', 'categories')
    
    # 받은 총 좋아요/즐겨찾기 수 계산
    total_likes_received = Like.objects.filter(project__author=user).count()
    total_bookmarks_received = Bookmark.objects.filter(project__author=user).count()
    recent_badges = get_recent_user_badges(user, limit=8)
    badge_catalog = get_active_badges_with_user_state(user)
    
    context = {
        'profile': profile,
        'form': form,
        'my_projects': my_projects,
        'liked_projects': liked_projects,
        'bookmarked_projects': bookmarked_projects,
        'total_likes': total_likes_received,
        'total_bookmarks': total_bookmarks_received,
        'badge_count': get_user_badge_count(user),
        'recent_badges': recent_badges,
        'badge_catalog': badge_catalog,
    }
    return render(request, 'arcade/profile.html', context)


def confirm_email_change(request, token):
    change_request = get_object_or_404(EmailChangeRequest, token=token, is_used=False)

    if change_request.is_expired:
        change_request.is_used = True
        change_request.save(update_fields=['is_used'])
        messages.error(request, '이메일 변경 인증 링크가 만료되었습니다. 다시 요청해 주세요.')
        return redirect('profile')

    if User.objects.filter(email__iexact=change_request.new_email).exclude(pk=change_request.user_id).exists():
        change_request.is_used = True
        change_request.save(update_fields=['is_used'])
        messages.error(request, '이미 다른 회원이 사용 중인 이메일 주소입니다.')
        return redirect('profile')

    change_request.user.email = change_request.new_email
    change_request.user.save(update_fields=['email'])
    change_request.is_used = True
    change_request.save(update_fields=['is_used'])
    messages.success(request, '이메일 주소 인증이 완료되었습니다. 새 이메일 주소로 변경되었습니다.')
    return redirect('profile')


def confirm_signup_email(request, token):
    verification = get_object_or_404(SignupEmailVerification, token=token, is_used=False)

    if verification.is_expired:
        verification.is_used = True
        verification.save(update_fields=['is_used'])
        messages.error(request, '회원가입 인증 링크가 만료되었습니다. 다시 가입을 진행해 주세요.')
        return redirect('signup')

    verification.user.is_active = True
    verification.user.save(update_fields=['is_active'])
    verification.is_used = True
    verification.save(update_fields=['is_used'])
    messages.success(request, '이메일 인증이 완료되었습니다. 이제 로그인할 수 있습니다.')
    return redirect('login')


# ────────────────────────────────────────────────
# 회원 관리 (관리자 전용 CRUD)
# ────────────────────────────────────────────────

def staff_check(user):
    return user.is_staff

@login_required
@user_passes_test(staff_check)
def member_list(request):
    """회원 목록 조회"""
    search = request.GET.get('q', '')
    user_type = request.GET.get('type', '')
    
    users = User.objects.all().select_related('profile').order_by('-date_joined')
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search)
        )
    if user_type:
        users = users.filter(profile__user_type=user_type)

    type_filters = [
        {
            'code': code,
            'label': label,
            'active': user_type == code,
        }
        for code, label in UserProfile.USER_TYPE_CHOICES
    ]
        
    context = {
        'users': users,
        'search_query': search,
        'current_type': user_type,
        'user_types': UserProfile.USER_TYPE_CHOICES,
        'type_filters': type_filters,
    }
    return render(request, 'arcade/admin/member_list.html', context)

@login_required
@user_passes_test(staff_check)
def member_create(request):
    """신규 회원 등록"""
    if request.method == 'POST':
        user_form = AdminUserForm(request.POST)
        profile_form = AdminUserProfileForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            # 프로필 정보 업데이트
            profile.user_type = profile_form.cleaned_data['user_type']
            profile.is_approved = profile_form.cleaned_data['is_approved']
            profile.save()
            
            messages.success(request, f'회원 "{user.username}" 계정이 생성되었습니다.')
            return redirect('member_list')
    else:
        user_form = AdminUserForm()
        profile_form = AdminUserProfileForm()
        
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'title': '신규 회원 등록',
    }
    return render(request, 'arcade/admin/member_form.html', context)

@login_required
@user_passes_test(staff_check)
def member_edit(request, user_id):
    """회원 정보 수정"""
    target_user = get_object_or_404(User, pk=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=target_user)
    
    if request.method == 'POST':
        user_form = AdminUserForm(request.POST, instance=target_user)
        profile_form = AdminUserProfileForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, f'회원 "{target_user.username}" 정보가 수정되었습니다.')
            return redirect('member_list')
    else:
        user_form = AdminUserForm(instance=target_user)
        profile_form = AdminUserProfileForm(instance=profile)
        
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'target_user': target_user,
        'title': '회원 정보 수정',
    }
    return render(request, 'arcade/admin/member_form.html', context)


@login_required
@user_passes_test(staff_check)
@require_POST
def member_approve(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=target_user)
    profile.is_approved = True
    profile.approved_at = timezone.now()
    profile.save(update_fields=['is_approved', 'approved_at'])
    messages.success(request, f'회원 "{target_user.username}" 을 승인했습니다.')
    redirect_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('member_list')
    return redirect(redirect_url)

@login_required
@user_passes_test(staff_check)
@require_POST
def member_delete(request, user_id):
    """회원 삭제"""
    target_user = get_object_or_404(User, pk=user_id)
    if target_user == request.user:
        messages.error(request, '본인 계정은 삭제할 수 없습니다.')
    else:
        username = target_user.username
        target_user.delete()
        messages.success(request, f'회원 "{username}" 계정이 삭제되었습니다.')
    return redirect('member_list')


# ────────────────────────────────────────────────
# 배지 관리 (관리자 전용 CRUD)
# ────────────────────────────────────────────────

@login_required
@user_passes_test(staff_check)
@login_required
@user_passes_test(staff_check)
def schedule_admin_list(request):
    """일정 관리 목록"""
    events = ScheduleEvent.objects.select_related().order_by('start_date', 'end_date', 'title')

    # 필터링
    event_type = request.GET.get('event_type', '')
    is_active = request.GET.get('is_active', '')
    search = request.GET.get('q', '')

    if event_type:
        events = events.filter(event_type=event_type)
    if is_active in ('0', '1'):
        events = events.filter(is_active=is_active == '1')
    if search:
        events = events.filter(Q(title__icontains=search) | Q(description__icontains=search))

    context = {
        'events': events,
        'search_query': search,
        'current_event_type': event_type,
        'current_is_active': is_active,
        'event_types': ScheduleEvent.EVENT_TYPE_CHOICES,
        'title': '일정 관리',
    }
    return render(request, 'arcade/admin/schedule_list.html', context)


@login_required
@user_passes_test(staff_check)
def schedule_admin_create(request):
    """신규 일정 등록"""
    if request.method == 'POST':
        form = ScheduleEventForm(request.POST)
        if form.is_valid():
            event = form.save()
            messages.success(request, f'일정 "{event.title}"이 등록되었습니다.')
            return redirect('schedule_admin_list')
    else:
        form = ScheduleEventForm()

    context = {
        'form': form,
        'title': '신규 일정 등록',
    }
    return render(request, 'arcade/admin/schedule_form.html', context)


@login_required
@user_passes_test(staff_check)
def schedule_admin_edit(request, event_id):
    """일정 수정"""
    event = get_object_or_404(ScheduleEvent, pk=event_id)

    if request.method == 'POST':
        form = ScheduleEventForm(request.POST, instance=event)
        if form.is_valid():
            event = form.save()
            messages.success(request, f'일정 "{event.title}"이 수정되었습니다.')
            return redirect('schedule_admin_list')
    else:
        form = ScheduleEventForm(instance=event)

    context = {
        'form': form,
        'event': event,
        'title': '일정 수정',
    }
    return render(request, 'arcade/admin/schedule_form.html', context)


@login_required
@user_passes_test(staff_check)
@require_POST
def schedule_admin_delete(request, event_id):
    """일정 삭제"""
    event = get_object_or_404(ScheduleEvent, pk=event_id)
    title = event.title
    try:
        event.delete()
        messages.success(request, f'일정 "{title}"이 삭제되었습니다.')
    except DatabaseError:
        messages.error(request, f'일정 "{title}"을 삭제할 수 없습니다.')
    return redirect('schedule_admin_list')


def badge_list(request):
    """배지 목록 조회"""
    search = request.GET.get('q', '')
    category = request.GET.get('category', '')
    criteria_type = request.GET.get('criteria_type', '')
    is_active = request.GET.get('is_active', '')

    badges = Badge.objects.select_related('related_program').order_by('sort_order', 'name')

    if search:
        badges = badges.filter(
            Q(code__icontains=search) |
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(criteria_type__icontains=search) |
            Q(related_program__name__icontains=search)
        )
    if category:
        badges = badges.filter(category=category)
    if criteria_type:
        badges = badges.filter(criteria_type=criteria_type)
    if is_active in ('0', '1'):
        badges = badges.filter(is_active=is_active == '1')

    context = {
        'badges': badges,
        'search_query': search,
        'current_category': category,
        'current_criteria_type': criteria_type,
        'current_is_active': is_active,
        'categories': Badge.CATEGORY_CHOICES,
        'criteria_types': Badge.objects.exclude(criteria_type='')
        .order_by('criteria_type')
        .values_list('criteria_type', flat=True)
        .distinct(),
        'title': '배지 관리',
    }
    return render(request, 'arcade/admin/badge_list.html', context)


@login_required
@user_passes_test(staff_check)
def badge_create(request):
    """신규 배지 등록"""
    if request.method == 'POST':
        form = BadgeForm(request.POST)
        if form.is_valid():
            badge = form.save()
            messages.success(request, f'배지 "{badge.name}"이 생성되었습니다.')
            return redirect('badge_list')
    else:
        form = BadgeForm()

    context = {
        'form': form,
        'title': '신규 배지 등록',
    }
    return render(request, 'arcade/admin/badge_form.html', context)


@login_required
@user_passes_test(staff_check)
def badge_edit(request, badge_id):
    """배지 정보 수정"""
    badge = get_object_or_404(Badge, pk=badge_id)

    if request.method == 'POST':
        form = BadgeForm(request.POST, instance=badge)
        if form.is_valid():
            badge = form.save()
            messages.success(request, f'배지 "{badge.name}" 정보가 수정되었습니다.')
            return redirect('badge_list')
    else:
        form = BadgeForm(instance=badge)

    context = {
        'form': form,
        'badge': badge,
        'title': '배지 정보 수정',
    }
    return render(request, 'arcade/admin/badge_form.html', context)


@login_required
@user_passes_test(staff_check)
@require_POST
def badge_delete(request, badge_id):
    """배지 삭제"""
    badge = get_object_or_404(Badge, pk=badge_id)
    name = badge.name
    try:
        badge.delete()
    except DatabaseError:
        messages.error(request, f'배지 "{name}"을 삭제할 수 없습니다.')
    else:
        messages.success(request, f'배지 "{name}"이 삭제되었습니다.')
    return redirect('badge_list')


def signup(request):
    """회원가입"""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '회원가입이 완료되었습니다. 이제 로그인할 수 있습니다.')
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'arcade/signup.html', {'form': form})


@login_required
def profile_view(request):
    """마이페이지 - 대시보드 및 정보 수정"""
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=profile, user=user)
        if form.is_valid():
            form.save()
            messages.success(request, '회원 정보가 성공적으로 수정되었습니다.')
            return redirect('profile')
    else:
        form = UserProfileUpdateForm(instance=profile, user=user)

    my_projects = Project.objects.filter(author=user).prefetch_related('categories')
    liked_projects = Project.objects.filter(likes__user=user).prefetch_related('author', 'categories')
    bookmarked_projects = Project.objects.filter(bookmarks__user=user).prefetch_related('author', 'categories')

    total_likes_received = Like.objects.filter(project__author=user).count()
    total_bookmarks_received = Bookmark.objects.filter(project__author=user).count()
    recent_badges = get_recent_user_badges(user, limit=8)
    badge_catalog = get_active_badges_with_user_state(user)

    context = {
        'profile': profile,
        'form': form,
        'my_projects': my_projects,
        'liked_projects': liked_projects,
        'bookmarked_projects': bookmarked_projects,
        'total_likes': total_likes_received,
        'total_bookmarks': total_bookmarks_received,
        'badge_count': get_user_badge_count(user),
        'recent_badges': recent_badges,
        'badge_catalog': badge_catalog,
    }
    return render(request, 'arcade/profile.html', context)
