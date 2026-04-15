from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import TypingScore, TypingContent
import json

@login_required
def typing_home(request):
    """타자연습 메인 대시보드"""
    # 개인 최고 기록들
    user_best = TypingScore.objects.filter(user=request.user).order_by('-score')[:5]
    
    # 전체 랭킹 (간단히 표시용)
    top_scores = TypingScore.objects.all().order_by('-score')[:10]
    
    # 선택 가능한 긴글 목록
    long_texts = TypingContent.objects.filter(content_type='long').order_by('title')
    
    return render(request, 'typing_practice/typing_home.html', {
        'user_best': user_best,
        'top_scores': top_scores,
        'long_texts': long_texts
    })

@login_required
def practice_keys(request):
    """자리연습 페이지"""
    return render(request, 'typing_practice/practice_keys.html')

@login_required
def practice_text(request, content_type):
    """단어 또는 짧은글 연습 페이지"""
    lang = request.GET.get('lang', 'ko')
    raw_contents = TypingContent.objects.filter(content_type=content_type, language=lang)
    
    processed_list = []
    for item in raw_contents:
        # 콤마(,) 또는 줄바꿈(\n)으로 분리
        if content_type == 'word':
            parts = [p.strip() for p in item.text.replace('\n', ',').split(',') if p.strip()]
        else:
            parts = [p.strip() for p in item.text.split('\n') if p.strip()]
            
        for p in parts:
            processed_list.append({'text': p})
            
    # JSON 형태로 데이터를 전달하여 JS에서 처리
    return render(request, 'typing_practice/practice_text.html', {
        'content_type': content_type,
        'language': lang,
        'contents_json': json.dumps(processed_list)
    })

@login_required
def practice_long(request, pk):
    """긴글 연습 페이지"""
    content = TypingContent.objects.get(pk=pk)
    return render(request, 'typing_practice/practice_long.html', {'content': content})

@login_required
def save_score(request):
    """연습 결과 저장 API"""
    if request.method == 'POST':
        try:
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
    # 유형별/언어별 필터링 가능하도록 확장 예정
    rankings = TypingScore.objects.all().order_by('-score')[:50]
    return render(request, 'typing_practice/ranking.html', {'rankings': rankings})
