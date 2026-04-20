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
