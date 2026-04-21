import json
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from .models import TypingScore, TypingContent
from deep_translator import GoogleTranslator

import pykakasi
from pypinyin import pinyin, Style

@login_required
def translate_api(request):
    """텍스트를 특정 언어로 번역하고 가나/병음으로 변환하는 API"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            text = data.get('text', '')
            original_target = data.get('target', 'en')
            
            # GoogleTranslator 타겟 매핑 (zh -> zh-CN)
            target_lang = 'zh-CN' if original_target == 'zh' else original_target
            
            if not text:
                return JsonResponse({'status': 'error', 'message': '텍스트가 없습니다.'})
            
            # 1. 기본 구글 번역 수행
            translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
            
            # 2. 언어별 후처리 (가나/병음 변환)
            final_result = translated
            
            if original_target == 'ja':
                # 일본어 -> 가타카나 변환
                kks = pykakasi.kakasi()
                converted = kks.convert(translated)
                final_result = "".join([item['kana'] for item in converted])
            elif original_target == 'zh':
                # 중국어 -> 병음(Pinyin) 변환 (성조 없이 알파벳만)
                pinyin_list = pinyin(translated, style=Style.NORMAL)
                final_result = " ".join([item[0] for item in pinyin_list])
            
            # 쉼표 뒤 공백 정리 및 노이지 문자 제거
            final_result = final_result.replace(' ,', ',').replace(' .', '.').strip('.')
            
            return JsonResponse({'status': 'success', 'translated': final_result})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'invalid method'}, status=405)

@login_required
def generate_content_api(request):
    """주제를 기반으로 연습 콘텐츠를 자동 생성하는 AI 마법사 API"""
    if request.method != 'POST':
        return JsonResponse({'status': 'invalid method'}, status=405)
    
    try:
        data = json.loads(request.body)
        title = data.get('title', '').strip()
        c_type = data.get('content_type', 'word')
        count = int(data.get('count', 10))

        if not title:
            return JsonResponse({'status': 'error', 'message': '주제를 입력해 주세요.'})

        # --- 카테고리 지능형 매칭 데이터베이스 (대폭 확장) ---
        KNOWLEDGE_BASE = {
            'it': {
                'emoji': '💻',
                'keywords': ['컴퓨터', '인터넷', '소프트웨어', 'it', '기술', '코딩'],
                'word': ['컴퓨터', '인터넷', '소프트웨어', '알고리즘', '데이터베이스', '프로그래밍', '서버', '네트워크', '코딩', '인공지능', '클라우드', '보안', '애플리케이션', '하드웨어', '모바일', '브라우저', '운영체제', '프로세서', '메모리', '스토리지', '인터페이스', '백엔드', '프론트엔드', '풀스택', '디버깅', '컴파일러', '프레임워크', '라이브러리', '가상화', '컨테이너', '마이크로서비스', '블록체인', '암호화', '방화벽', '해킹', '빅데이터', '머신러닝', '딥러닝', '로봇공학', '사물인터넷', '상호작용', '사용자 경험', '객체지향', '함수형 프로그래밍', '멀티태스킹', '병렬처리', '디지털', '시스템', '플랫폼', '가젯'],
                'short': ['코딩은 논리적인 사고를 키워줍니다.', '인공지능 기술이 세상을 바꾸고 있습니다.', '데이터는 현대의 새로운 석유입니다.', '보안은 모든 IT 시스템의 핵심입니다.', '클라우드 환경에서는 언제 어디서나 작업이 가능합니다.', '인터넷은 전 세계를 하나로 연결합니다.', '소프트웨어 업데이트는 보안의 시작입니다.', '강력한 암호는 개인정보를 보호합니다.', '스마트폰은 우리 삶의 필수품이 되었습니다.', '미래의 기술은 더욱 놀랍게 발전할 것입니다.']
            },
            'fruit': {
                'emoji': '🍎',
                'keywords': ['과일', '음식', '채소', '요리', '식품'],
                'word': ['사과', '바나나', '포도', '수박', '딸기', '오렌지', '파인애플', '메론', '키위', '망고', '복숭아', '체리', '배', '자두', '감', '귤', '레몬', '라임', '자몽', '블루베리', '라즈베리', '크랜베리', '석류', '무화과', '대추', '밤', '호두', '땅콩', '아몬드', '코코넛', '아보카도', '파파야', '구아바', '리치', '망고스틴', '두리안', '용과', '살구', '유자', '모과', '앵두', '보리수', '오디', '산딸기', '참외', '토마토', '방울토마토', '한라봉', '천혜향', '샤인머스캣'],
                'short': ['과일을 많이 먹으면 건강에 좋습니다.', '신선한 사과가 맛있습니다.', '여름에는 수박이 최고입니다.', '비타민 씨가 풍부한 과일을 추천합니다.', '계절마다 제철 과일이 바뀝니다.', '달콤한 포도가 송이송이 열렸습니다.', '상큼한 오렌지 주스 한 잔 어떠세요?', '딸기는 아이들이 가장 좋아하는 과일입니다.', '과일 바구니에는 정성이 가득 담겨 있습니다.', '아침에 먹는 사과는 보약과 같습니다.']
            },
            'animal': {
                'emoji': '🦁',
                'keywords': ['동물', '생물', '자연', '곤충', '새'],
                'word': ['사자', '호랑이', '코끼리', '기린', '팬더', '토끼', '강아지', '고양이', '원숭이', '여우', '늑대', '곰', '얼룩말', '하마', '사슴', '독수리', '참새', '까치', '비둘기', '타조', '펭귄', '악어', '거북이', '뱀', '개구리', '도마뱀', '고래', '상어', '돌고래', '문어', '오징어', '꽃게', '새우', '조개', '불가사리', '해파리', '나비', '꿀벌', '무당벌레', '잠자리', '메뚜기', '지렁이', '달팽이', '캥거루', '코알라', '낙타', '다람쥐', '햄스터', '앵무새', '공룡'],
                'short': ['강아지는 사람을 잘 따릅니다.', '고양이는 귀여운 동물입니다.', '사자는 밀림의 왕이라고 불립니다.', '지구에는 다양한 동물이 살고 있습니다.', '자연을 보호해야 동물이 안전합니다.', '코끼리는 코가 아주 깁니다.', '새들은 아침마다 노래를 부릅니다.', '바닷속에는 신비로운 생물들이 많습니다.', '동물원은 아이들에게 인기 만점입니다.', '멸종 위기 동물을 함께 지켜주세요.']
            },
            'space': {
                'emoji': '🚀',
                'keywords': ['우주', '과학', '미래', '별', '천문'],
                'word': ['우주선', '지구', '태양', '달', '화성', '은하계', '블랙홀', '위성', '별', '수성', '금성', '목성', '토성', '천왕성', '해왕성', '명왕성', '안드로메다', '성운', '혜성', '유성', '소행성', '우주복', '우주정거장', '로켓', '천문대', '망원경', '우주비행사', '무중력', '광년', '우주먼지', '빅뱅', '평행우주', '외계인', '우주의 신비', '행성', '항성', '궤도', '대기권', '우주탐사', '아폴로', '나사', '일식', '월식', '별자리', '북극성', '은하수', '코스모스', '양자역학', '상대성 이론', '우주선장'],
                'short': ['우주는 끝이 없이 넓습니다.', '인류는 화성 탐사를 준비하고 있습니다.', '지구는 푸른 행성입니다.', '밤하늘에는 수많은 별이 빛납니다.', '우주 비행사는 특별한 훈련을 받습니다.', '태양계에는 여덟 개의 행성이 있습니다.', '블랙홀은 빛조차 빠져나가지 못합니다.', '달 뒤편에는 무엇이 있을까요?', '우주 정거장에서 지구를 바라봅니다.', '우주 탐험은 인간의 끊임없는 꿈입니다.']
            },
            'travel': {
                'emoji': '✈️',
                'keywords': ['여행', '관광', '바다', '해외', '휴가'],
                'word': ['여권', '비행기', '호텔', '배낭', '지도', '카메라', '공항', '여행사', '휴게소', '바닷가', '산책', '구경', '기차', '축제', '휴가', '캐리어', '선글라스', '돗자리', '텐트', '캠핑', '숙소', '게스트하우스', '유적지', '박물관', '기념품', '면세점', '현지식', '풍경', '가이드', '여행지', '산행', '해변', '리조트', '기내식', '환전', '비자', '여행보험', '자유여행', '패키지여행', '크루즈', '기차여행', '도착', '출발', '인삿말', '지도앱', '보조배터리', '포켓와이파이', '관광지', '추억', '사진첩'],
                'short': ['새로운 나라로 여행을 떠납니다.', '여행은 새로운 에너지를 줍니다.', '가족과 함께 즐거운 휴가를 보냅니다.', '멋진 풍경을 카메라에 담습니다.', '여행지에서 맛있는 음식을 먹습니다.', '비행기를 타고 구름 위를 날아갑니다.', '낯선 곳에서의 만남은 늘 설렙니다.', '배낭 하나 메고 세상을 걷습니다.', '여행의 목적지는 마음속에 있습니다.', '다시 가고 싶은 여행지를 추억합니다.']
            },
            'proverb': {
                'emoji': '📚',
                'keywords': ['속담', '격언', '고사성어', '지혜', '교훈'],
                'word': ['속담', '명언', '교훈', '지혜', '옛말', '가식', '진실', '노력', '성공', '인내', '희망', '우정', '사랑', '가족', '인생'],
                'short': ['가는 말이 고와야 오는 말이 곱습니다.', '세 살 버릇 여든까지 간다.', '발 없는 말이 천 리를 간다.', '천 리 길도 한 걸음부터 시작됩니다.', '고생 끝에 낙이 온다는 말을 믿으세요.', '등잔 밑이 어둡다는 말이 있습니다.', '백지장도 맞들면 낫다는 교훈이 있습니다.', '소 잃고 외양간 고친다는 말이 되지 마세요.', '호랑이도 제 말 하면 온다는 말이 있습니다.', '돌다리도 두들겨 보고 건너야 안전합니다.']
            },
            'saying': {
                'emoji': '💡',
                'keywords': ['명언', '동기부여', '성공', '인생', '꿈', '행복'],
                'word': ['성공', '도전', '열정', '행복', '미래', '현재', '기회', '변화', '성장', '용기', '믿음', '긍정', '목표', '실행', '습관'],
                'short': ['오늘의 노력이 내일의 영광이 됩니다.', '당신의 꿈을 믿고 나아가세요.', '실패는 성공으로 가는 과정일 뿐입니다.', '긍정적인 생각이 긍정적인 삶을 만듭니다.', '지금 바로 시작하는 것이 가장 빠릅니다.', '어제보다 더 나은 오늘을 만드세요.', '당신은 생각보다 훨씬 강한 사람입니다.', '기회는 준비된 사람에게 찾아옵니다.', '작은 습관이 모여 인생을 바꿉니다.', '행복은 멀리 있지 않고 내 마음속에 있습니다.']
            }
        }

        # 1-1. 주제에서 키워드 추출 및 매칭 (더 정교한 매칭)
        selected_category = 'it' # 기본값
        title_lower = title.lower()
        for cat_key, info in KNOWLEDGE_BASE.items():
            if cat_key in title_lower or any(k in title_lower for k in info.get('keywords', [])):
                selected_category = cat_key
                break
        
        info = KNOWLEDGE_BASE[selected_category]
        emoji = info['emoji']
        
        # 1-2. 개수만큼 데이터 추출 (랜덤성 및 조합 기능 강화)
        raw_pool = info.get(c_type, ["안녕", "반가워"])
        generated_ko_list = []
        
        # 기본 풀을 섞어서 추가
        pool_copy = list(raw_pool)
        random.shuffle(pool_copy)
        
        # 중복 없이 최대한 채우기
        generated_ko_list.extend(pool_copy)
        
        # 부족할 경우 중복을 허용하되 수식어를 붙여 변형 시도 (단어일 때)
        if len(generated_ko_list) < count and c_type == 'word':
            adjectives = ['빨간', '파란', '예쁜', '귀여운', '빠른', '멋진', '신비한', '달콤한', '신선한', '작은', '거대한']
            while len(generated_ko_list) < count:
                new_item = f"{random.choice(adjectives)} {random.choice(raw_pool)}"
                generated_ko_list.append(new_item)
                if len(generated_ko_list) >= count * 2: break # 안전장치
        
        # 그래도 부족하면 단순 반복 (섞어서)
        while len(generated_ko_list) < count:
            generated_ko_list.append(random.choice(raw_pool))
            if len(generated_ko_list) >= count * 2: break
        
        # 최종 갯수 맞춤 (중복 제거보다는 순서 섞기로 대응)
        random.shuffle(generated_ko_list)
        generated_ko_list = generated_ko_list[:count]
        
        # 문자열 결합 (단어는 쉼표, 문장은 줄바꿈)
        ko_text = ", ".join(generated_ko_list) if c_type == 'word' else "\n".join(generated_ko_list)

        # 2. 다국어 자동 번역 수행
        results = {'ko': ko_text, 'emoji': emoji}
        targets = [('en', 'en'), ('ja', 'ja'), ('zh', 'zh-CN')]

        for lang_code, target_key in targets:
            translated = GoogleTranslator(source='auto', target=target_key).translate(ko_text)
            
            # 가나/병음 후처리 로직 재사용
            final_val = translated
            if lang_code == 'ja':
                kks = pykakasi.kakasi()
                converted = kks.convert(translated)
                final_val = "".join([item['kana'] for item in converted])
            elif lang_code == 'zh':
                pinyin_list = pinyin(translated, style=Style.NORMAL)
                final_val = " ".join([item[0] for item in pinyin_list])
            
            final_val = final_val.replace(' ,', ',').replace(' .', '.').strip('.')
            results[lang_code] = final_val

        return JsonResponse({
            'status': 'success',
            'data': results
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def is_staff_check(user):
    return user.is_staff

@login_required
def typing_home(request):
    """타자연습 메인 대시보드"""
    # 개인 최고 기록들
    user_best = TypingScore.objects.filter(user=request.user).order_by('-score')[:5]
    
    # 전체 랭킹 (간단히 표시용)
    top_scores = TypingScore.objects.all().order_by('-score')[:10]
    
    # 선택 가능한 단어 테마 (한/영 구분)
    word_themes_ko = TypingContent.objects.filter(content_type='word', language='ko')
    word_themes_en = TypingContent.objects.filter(content_type='word', language='en')

    # 선택 가능한 짧은글 테마 (한/영 구분)
    short_themes_ko = TypingContent.objects.filter(content_type='short', language='ko')
    short_themes_en = TypingContent.objects.filter(content_type='short', language='en')

    # 선택 가능한 긴글 목록
    long_texts = TypingContent.objects.filter(content_type='long').order_by('title')
    
    return render(request, 'typing_practice/typing_home.html', {
        'user_best': user_best,
        'top_scores': top_scores,
        'word_themes_ko': word_themes_ko,
        'word_themes_en': word_themes_en,
        'short_themes_ko': short_themes_ko,
        'short_themes_en': short_themes_en,
        'long_texts': long_texts
    })

@login_required
def practice_keys(request):
    """자리연습 페이지 (단계 선택 포함)"""
    level = request.GET.get('level')
    lang = request.GET.get('lang', 'ko')
    if not level:
        return render(request, 'typing_practice/select_level.html', {'language': lang})
    return render(request, 'typing_practice/practice_keys.html', {'level': level, 'language': lang})

@login_required
def practice_text(request, content_type):
    """단어 또는 짧은글 연습 페이지 (테마 선택 포함)"""
    lang = request.GET.get('lang', 'ko')
    theme_id = request.GET.get('theme')
    
    if not theme_id:
        # 테마 선택 페이지 노출
        # 선택한 언어의 데이터 필드가 비어있지 않은 테마들만 필터링
        filter_kwargs = {
            'content_type': content_type,
            f'text_{lang}__isnull': False
        }
        themes = TypingContent.objects.filter(**filter_kwargs).exclude(**{f'text_{lang}': ''}).order_by('-id')
        
        # 만약 해당 언어로 필터링된 결과가 없으면 전체 목록을 보여주거나 예외 처리
        if not themes.exists() and lang == 'ko':
             themes = TypingContent.objects.filter(content_type=content_type).order_by('-id')

        return render(request, 'typing_practice/select_theme.html', {
            'content_type': content_type,
            'language': lang,
            'themes': themes
        })
    
    raw_contents = TypingContent.objects.filter(id=theme_id)
    if not raw_contents.exists():
        # 잘못된 테마 ID 접근 시 리다이렉트
        return redirect('typing_home')
        
    theme = raw_contents.first()
    
    # 각 언어별 텍스트 가져와서 리스트화
    def get_parts(text, is_word):
        if not text: return []
        if is_word:
            # 다국어 구분자(전각 쉼표 등)를 일반 쉼표로 통합
            clean_text = text.replace('\n', ',').replace('、', ',').replace('，', ',')
            return [p.strip() for p in clean_text.split(',') if p.strip()]
        else:
            return [p.strip() for p in text.split('\n') if p.strip()]

    parts_ko = get_parts(theme.text_ko or theme.text, content_type == 'word')
    parts_en = get_parts(theme.text_en, content_type == 'word')
    parts_ja = get_parts(theme.text_ja, content_type == 'word')
    parts_zh = get_parts(theme.text_zh, content_type == 'word')

    # 최대 길이에 맞춰 순회하며 객체 생성
    max_len = max(len(parts_ko), len(parts_en), len(parts_ja), len(parts_zh))
    processed_list = []
    for i in range(max_len):
        processed_list.append({
            'ko': parts_ko[i] if i < len(parts_ko) else '',
            'en': parts_en[i] if i < len(parts_en) else '',
            'ja': parts_ja[i] if i < len(parts_ja) else '',
            'zh': parts_zh[i] if i < len(parts_zh) else '',
        })
            
    # 단어 연습인 경우 랜덤하게 섞고 30개로 제한
    if content_type == 'word':
        random.shuffle(processed_list)
        processed_list = processed_list[:30]
            
    return render(request, 'typing_practice/practice_text.html', {
        'content_type': content_type,
        'language': lang,
        'theme_title': theme.title,
        'contents_json': json.dumps(processed_list)
    })

@login_required
def practice_long(request, pk=None):
    """긴글 연습 페이지 (목록 선택 포함)"""
    if not pk:
        # 긴글 목록 선택 페이지
        long_texts = TypingContent.objects.filter(content_type='long').order_by('title')
        return render(request, 'typing_practice/select_long.html', {'long_texts': long_texts})
        
    content = get_object_or_404(TypingContent, pk=pk)
    
    # 긴글 연습에서도 다국어 지원을 위해 직렬화된 데이터를 넘겨줄 준비 (문장 단위 zip)
    def get_parts(text):
        if not text: return []
        return [p.strip() for p in text.split('\n') if p.strip()]

    parts_ko = get_parts(content.text_ko or content.text)
    parts_en = get_parts(content.text_en)
    parts_ja = get_parts(content.text_ja)
    parts_zh = get_parts(content.text_zh)

    max_len = max(len(parts_ko), len(parts_en), len(parts_ja), len(parts_zh))
    processed_list = []
    for i in range(max_len):
        processed_list.append({
            'ko': parts_ko[i] if i < len(parts_ko) else '',
            'en': parts_en[i] if i < len(parts_en) else '',
            'ja': parts_ja[i] if i < len(parts_ja) else '',
            'zh': parts_zh[i] if i < len(parts_zh) else '',
        })

    return render(request, 'typing_practice/practice_long.html', {
        'content': content,
        'contents_json': json.dumps(processed_list)
    })

@login_required
def save_score(request):
    """연습 결과 저장 API"""
    if request.method == 'POST':
        try:
            profile = getattr(request.user, 'profile', None)
            if not profile or not profile.is_full_member:
                return JsonResponse({'status': 'not_saved', 'message': '메듀랩 정회원만 기록이 저장됩니다.'})

            data = json.loads(request.body)
            TypingScore.objects.create(
                user=request.user,
                practice_type=data.get('type', 'key'),
                language=data.get('lang', 'ko'),
                score=data.get('score', 0),
                speed=data.get('speed', 0),
                accuracy=data.get('accuracy', 0.0)
            )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'invalid method'}, status=405)

@login_required
def typing_ranking(request):
    """전체 랭킹 페이지"""
    rankings = TypingScore.objects.all().order_by('-score')[:50]
    return render(request, 'typing_practice/ranking.html', {'rankings': rankings})

# --- 콘텐츠 관리 전용 View (관리자용) ---

@user_passes_test(is_staff_check)
def content_manage(request):
    """타자 콘텐츠 관리 목록 (필터링 포함)"""
    c_type = request.GET.get('type')
    if c_type in ['word', 'short', 'long']:
        contents = TypingContent.objects.filter(content_type=c_type).order_by('-id')
    else:
        contents = TypingContent.objects.all().order_by('-id')
    return render(request, 'typing_practice/content_manage.html', {
        'contents': contents,
        'active_type': c_type or 'all'
    })

@user_passes_test(is_staff_check)
def content_edit(request, pk=None):
    """콘텐츠 추가 또는 수정"""
    if pk:
        content = get_object_or_404(TypingContent, pk=pk)
    else:
        content = None

    if request.method == 'POST':
        c_type = request.POST.get('content_type')
        lang = request.POST.get('language')
        emoji = request.POST.get('emoji', '⌨️')
        title = request.POST.get('title', '')
        
        text_ko = request.POST.get('text_ko', '')
        text_en = request.POST.get('text_en', '')
        text_ja = request.POST.get('text_ja', '')
        text_zh = request.POST.get('text_zh', '')

        if pk:
            content.content_type = c_type
            content.language = lang
            content.emoji = emoji
            content.title = title
            content.text_ko = text_ko
            content.text_en = text_en
            content.text_ja = text_ja
            content.text_zh = text_zh
            content.save()
        else:
            TypingContent.objects.create(
                content_type=c_type,
                language=lang,
                emoji=emoji,
                title=title,
                text_ko=text_ko,
                text_en=text_en,
                text_ja=text_ja,
                text_zh=text_zh
            )
        return redirect('typing_content_manage')

    return render(request, 'typing_practice/content_edit.html', {'content': content})

@user_passes_test(is_staff_check)
def content_delete(request, pk):
    """콘텐츠 삭제"""
    content = get_object_or_404(TypingContent, pk=pk)
    if request.method == 'POST':
        content.delete()
        return redirect('typing_content_manage')
    return render(request, 'typing_practice/content_confirm_delete.html', {'content': content})
