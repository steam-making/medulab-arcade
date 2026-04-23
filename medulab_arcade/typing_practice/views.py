import json
import random
from collections import defaultdict
from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.utils import timezone
from .models import (
    AGE_GROUP_CHOICES,
    LANGUAGE_CHOICES,
    MASTER_CATEGORY_CHOICES,
    RANKING_PRACTICE_TYPE_CHOICES,
    TypingContent,
    TypingHallOfFame,
    TypingScore,
)
from deep_translator import GoogleTranslator

import pykakasi
from pypinyin import pinyin, Style


LANGUAGE_LABELS = dict(LANGUAGE_CHOICES)
AGE_GROUP_LABELS = dict(AGE_GROUP_CHOICES)
PRACTICE_LABELS = dict(RANKING_PRACTICE_TYPE_CHOICES)
MASTER_LABELS = dict(MASTER_CATEGORY_CHOICES)
RANKING_PRACTICE_TYPES = [code for code, _ in RANKING_PRACTICE_TYPE_CHOICES]
LANGUAGE_CODES = [code for code, _ in LANGUAGE_CHOICES]


def get_typing_access_flags(user):
    is_permanent = user.is_authenticated
    is_full_member = False
    show_ads = True

    if is_permanent:
        try:
            profile = user.profile
            is_full_member = profile.user_type in getattr(profile, 'FULL_ACCESS_TYPES', ())
        except Exception:
            is_full_member = False
        show_ads = not is_full_member

    return {
        'is_permanent': is_permanent,
        'is_full_member': is_full_member,
        'show_ads': show_ads,
    }


def get_current_quarter_info(now=None):
    now = now or timezone.localtime()
    quarter = ((now.month - 1) // 3) + 1
    start_month = (quarter - 1) * 3 + 1
    start = now.replace(month=start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
    if quarter == 4:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start_month + 3)
    return {
        "year": start.year,
        "quarter": quarter,
        "key": f"{start.year}-Q{quarter}",
        "label": f"{start.year}년 {quarter}분기",
        "start": start,
        "end": end,
    }


def estimate_school_grade_from_birth_year(birth_date, today=None):
    if not birth_date:
        return None
    today = today or timezone.localdate()
    return today.year - birth_date.year - 7


def get_age_group_for_user(user, today=None):
    profile = getattr(user, "profile", None)
    birth_date = getattr(profile, "birth_date", None)
    grade = estimate_school_grade_from_birth_year(birth_date, today=today)
    if grade is None:
        return "challenge"
    if grade <= 2:
        return "seed"
    if grade <= 6:
        return "growth"
    return "challenge"


def build_rank_entry(row, category, practice_type=None):
    return {
        "username": row["user"].username,
        "age_group": row["age_group"],
        "age_group_label": AGE_GROUP_LABELS.get(row["age_group"], row["age_group"]),
        "practice_type": practice_type,
        "practice_type_label": PRACTICE_LABELS.get(practice_type, "통합") if practice_type else "통합",
        "category": category,
        "category_label": MASTER_LABELS[category],
        "score": row["score"],
        "best_speed": row["best_speed"],
        "average_speed": row["average_speed"],
        "best_accuracy": row["best_accuracy"],
        "total_score": row["total_score"],
        "attempts": row["attempts"],
        "first_created_at": row["first_created_at"],
        "last_created_at": row["last_created_at"],
    }


def rank_rows(rows, category):
    if category == "peak_speed":
        metric = lambda row: (row["best_speed"], row["best_accuracy"], -row["first_created_at"].timestamp())
    elif category == "avg_speed":
        metric = lambda row: (row["average_speed"], row["best_accuracy"], -row["first_created_at"].timestamp())
    elif category == "accuracy":
        metric = lambda row: (row["best_accuracy"], row["best_speed"], -row["first_created_at"].timestamp())
    else:
        metric = lambda row: (row["total_score"], row["best_accuracy"], -row["first_created_at"].timestamp())
    return sorted(rows, key=metric, reverse=True)


def collect_typing_statistics(scores):
    grouped = {}
    for score in scores.select_related("user", "user__profile"):
        age_group = get_age_group_for_user(score.user)
        grouped.setdefault((age_group, score.practice_type, score.user_id), {
            "user": score.user,
            "age_group": age_group,
            "practice_type": score.practice_type,
            "best_speed": 0,
            "speed_sum": 0,
            "attempts": 0,
            "best_accuracy": 0,
            "total_score": 0,
            "score": 0,
            "first_created_at": score.created_at,
            "last_created_at": score.created_at,
        })
        row = grouped[(age_group, score.practice_type, score.user_id)]
        row["best_speed"] = max(row["best_speed"], score.speed)
        row["best_accuracy"] = max(row["best_accuracy"], score.accuracy)
        row["speed_sum"] += score.speed
        row["attempts"] += 1
        row["total_score"] += score.score
        row["score"] = max(row["score"], score.score)
        row["first_created_at"] = min(row["first_created_at"], score.created_at)
        row["last_created_at"] = max(row["last_created_at"], score.created_at)

    per_practice = defaultdict(lambda: defaultdict(list))
    overall = defaultdict(list)

    for row in grouped.values():
        row["average_speed"] = round(row["speed_sum"] / row["attempts"], 2) if row["attempts"] else 0
        per_practice[row["age_group"]][row["practice_type"]].append(row)
        overall[row["age_group"]].append(row)

    return per_practice, overall


def build_language_ranking_snapshot(language, quarter_info):
    scores = TypingScore.objects.filter(
        language=language,
        practice_type__in=RANKING_PRACTICE_TYPES,
        created_at__gte=quarter_info["start"],
        created_at__lt=quarter_info["end"],
    )
    per_practice_rows, overall_rows = collect_typing_statistics(scores)

    groups = []
    for age_group, label in AGE_GROUP_CHOICES:
        practice_sections = []
        for practice_type, practice_label in RANKING_PRACTICE_TYPE_CHOICES:
            rows = per_practice_rows.get(age_group, {}).get(practice_type, [])
            practice_sections.append({
                "practice_type": practice_type,
                "label": practice_label,
                "top3": [
                    build_rank_entry(row, "peak_speed", practice_type=practice_type)
                    for row in rank_rows(rows, "peak_speed")[:3]
                ],
            })

        overall_group_rows = overall_rows.get(age_group, [])
        groups.append({
            "code": age_group,
            "label": label,
            "practice_sections": practice_sections,
            "masters": [
                {
                    "category": "peak_speed",
                    "label": MASTER_LABELS["peak_speed"],
                    "top3": [build_rank_entry(row, "peak_speed") for row in rank_rows(overall_group_rows, "peak_speed")[:3]],
                },
                {
                    "category": "avg_speed",
                    "label": MASTER_LABELS["avg_speed"],
                    "top3": [build_rank_entry(row, "avg_speed") for row in rank_rows(overall_group_rows, "avg_speed")[:3]],
                },
                {
                    "category": "accuracy",
                    "label": MASTER_LABELS["accuracy"],
                    "top3": [build_rank_entry(row, "accuracy") for row in rank_rows(overall_group_rows, "accuracy")[:3]],
                },
                {
                    "category": "stamina",
                    "label": MASTER_LABELS["stamina"],
                    "top3": [build_rank_entry(row, "stamina") for row in rank_rows(overall_group_rows, "stamina")[:3]],
                },
            ],
        })

    return groups, per_practice_rows, overall_rows


def update_hall_of_fame_for_language(language, quarter_info=None):
    quarter_info = quarter_info or get_current_quarter_info()
    _, per_practice_rows, overall_rows = build_language_ranking_snapshot(language, quarter_info)

    all_practice_rows = defaultdict(list)
    for age_group_rows in per_practice_rows.values():
        for practice_type, rows in age_group_rows.items():
            all_practice_rows[practice_type].extend(rows)

    all_rows = []
    for rows in overall_rows.values():
        all_rows.extend(rows)

    for practice_type, _practice_label in RANKING_PRACTICE_TYPE_CHOICES:
        rows = all_practice_rows.get(practice_type, [])
        for category in ("peak_speed", "avg_speed", "accuracy"):
            ranked = rank_rows(rows, category)
            if not ranked:
                continue
            leader = ranked[0]
            record_value = leader["best_speed"] if category == "peak_speed" else (
                leader["average_speed"] if category == "avg_speed" else leader["best_accuracy"]
            )
            legend, created = TypingHallOfFame.objects.get_or_create(
                language=language,
                practice_type=practice_type,
                category=category,
                defaults={
                    "user": leader["user"],
                    "record_value": record_value,
                    "score": leader["score"],
                    "speed": leader["best_speed"],
                    "accuracy": leader["best_accuracy"],
                    "quarter_key": quarter_info["key"],
                    "achieved_at": leader["first_created_at"],
                },
            )
            if (not created) and (
                record_value > legend.record_value or
                (record_value == legend.record_value and leader["best_accuracy"] > legend.accuracy)
            ):
                legend.user = leader["user"]
                legend.record_value = record_value
                legend.score = leader["score"]
                legend.speed = leader["best_speed"]
                legend.accuracy = leader["best_accuracy"]
                legend.quarter_key = quarter_info["key"]
                legend.achieved_at = leader["first_created_at"]
                legend.save(update_fields=[
                    "user", "record_value", "score", "speed", "accuracy",
                    "quarter_key", "achieved_at", "updated_at",
                ])

    ranked = rank_rows(all_rows, "stamina")
    if ranked:
        leader = ranked[0]
        legend, created = TypingHallOfFame.objects.get_or_create(
            language=language,
            practice_type=None,
            category="stamina",
            defaults={
                "user": leader["user"],
                "record_value": leader["total_score"],
                "score": leader["score"],
                "speed": leader["best_speed"],
                "accuracy": leader["best_accuracy"],
                "quarter_key": quarter_info["key"],
                "achieved_at": leader["first_created_at"],
            },
        )
        if (not created) and (
            leader["total_score"] > legend.record_value or
            (leader["total_score"] == legend.record_value and leader["best_accuracy"] > legend.accuracy)
        ):
            legend.user = leader["user"]
            legend.record_value = leader["total_score"]
            legend.score = leader["score"]
            legend.speed = leader["best_speed"]
            legend.accuracy = leader["best_accuracy"]
            legend.quarter_key = quarter_info["key"]
            legend.achieved_at = leader["first_created_at"]
            legend.save(update_fields=[
                "user", "record_value", "score", "speed", "accuracy",
                "quarter_key", "achieved_at", "updated_at",
            ])


def build_typing_home_context(request):
    quarter_info = get_current_quarter_info()
    selected_age_group = get_age_group_for_user(request.user) if request.user.is_authenticated else "seed"
    ranking_data = {}

    for language in LANGUAGE_CODES:
        update_hall_of_fame_for_language(language, quarter_info)
        groups, _per_practice_rows, _overall_rows = build_language_ranking_snapshot(language, quarter_info)
        ordered_groups = sorted(groups, key=lambda group: 0 if group["code"] == selected_age_group else 1)
        ranking_data[language] = {
            "selected_group": selected_age_group,
            "groups": ordered_groups,
            "hall_of_fame": [
                {
                    "practice_type": legend.practice_type,
                    "practice_type_label": PRACTICE_LABELS.get(legend.practice_type, "통합"),
                    "category": legend.category,
                    "category_label": MASTER_LABELS[legend.category].replace("마스터", "레전드"),
                    "username": legend.user.username,
                    "record_value": legend.record_value,
                    "score": legend.score,
                    "speed": legend.speed,
                    "accuracy": legend.accuracy,
                    "quarter_key": legend.quarter_key,
                }
                for legend in TypingHallOfFame.objects.filter(language=language)
                .select_related("user")
                .order_by("practice_type", "category")
            ],
        }

    return quarter_info, selected_age_group, ranking_data

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

        # --- 카테고리 지능형 매칭 데이터베이스 ---
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
            # ... (중략 - 필요시 다른 카테고리도 복구)
        }

        # 매칭 로직 등 생략 (원래 코드 대로)
        selected_category = 'it' 
        title_lower = title.lower()
        for cat_key, info in KNOWLEDGE_BASE.items():
            if cat_key in title_lower or any(k in title_lower for k in info.get('keywords', [])):
                selected_category = cat_key
                break
        
        info = KNOWLEDGE_BASE[selected_category]
        emoji = info['emoji']
        raw_pool = info.get(c_type, ["안녕", "반가워"])
        
        # 생성 로직 (생략 - 원래 코드 복구)
        generated_ko_list = list(raw_pool)
        random.shuffle(generated_ko_list)
        generated_ko_list = generated_ko_list[:count]
        
        ko_text = ", ".join(generated_ko_list) if c_type == 'word' else "\n".join(generated_ko_list)
        results = {'ko': ko_text, 'emoji': emoji}
        # 번역 로직 등 수행...

        return JsonResponse({'status': 'success', 'data': results})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def is_staff_check(user):
    return user.is_staff

def typing_home(request):
    """타자연습 메인 대시보드"""
    user_best = TypingScore.objects.filter(user=request.user).order_by('-score')[:5] if request.user.is_authenticated else []
    
    access_flags = get_typing_access_flags(request.user)

    word_themes_ko = TypingContent.objects.filter(content_type='word', language='ko')
    word_themes_en = TypingContent.objects.filter(content_type='word', language='en')
    short_themes_ko = TypingContent.objects.filter(content_type='short', language='ko')
    short_themes_en = TypingContent.objects.filter(content_type='short', language='en')
    long_texts = TypingContent.objects.filter(content_type='long').order_by('title')
    quarter_info, selected_age_group, ranking_data = build_typing_home_context(request)
    
    return render(request, 'typing_practice/typing_home.html', {
        'user_best': user_best,
        'word_themes_ko': word_themes_ko,
        'word_themes_en': word_themes_en,
        'short_themes_ko': short_themes_ko,
        'short_themes_en': short_themes_en,
        'long_texts': long_texts,
        **access_flags,
        'quarter_info': quarter_info,
        'current_age_group': selected_age_group,
        'current_age_group_label': AGE_GROUP_LABELS[selected_age_group],
        'ranking_data': ranking_data,
        'ranking_data_json': json.dumps(ranking_data, ensure_ascii=False, default=str),
    })

def practice_keys(request):
    """자리연습 페이지 (단계 선택 포함)"""
    access_flags = get_typing_access_flags(request.user)

    level = request.GET.get('level')
    lang = request.GET.get('lang', 'ko')
    ctx = {
        'language': lang, 
        **access_flags,
    }
    if not level:
        return render(request, 'typing_practice/select_level.html', ctx)
    ctx['level'] = level
    return render(request, 'typing_practice/practice_keys.html', ctx)

def practice_text(request, content_type):
    """단어 또는 짧은글 연습 페이지 (테마 선택 포함)"""
    access_flags = get_typing_access_flags(request.user)

    lang = request.GET.get('lang', 'ko')
    theme_id = request.GET.get('theme')
    
    if not theme_id:
        filter_kwargs = {'content_type': content_type, f'text_{lang}__isnull': False}
        themes = TypingContent.objects.filter(**filter_kwargs).exclude(**{f'text_{lang}': ''}).order_by('-id')
        if not themes.exists() and lang == 'ko':
             themes = TypingContent.objects.filter(content_type=content_type).order_by('-id')
 
        return render(request, 'typing_practice/select_theme.html', {
            'content_type': content_type,
            'language': lang,
            'themes': themes,
            **access_flags,
        })
    
    theme = get_object_or_404(TypingContent, id=theme_id)
    def get_parts(text, is_word):
        if not text: return []
        if is_word:
            clean_text = text.replace('\n', ',').replace('、', ',').replace('，', ',')
            return [p.strip() for p in clean_text.split(',') if p.strip()]
        return [p.strip() for p in text.split('\n') if p.strip()]

    parts_ko = get_parts(theme.text_ko or theme.text, content_type == 'word')
    parts_en = get_parts(theme.text_en, content_type == 'word')
    parts_ja = get_parts(theme.text_ja, content_type == 'word')
    parts_zh = get_parts(theme.text_zh, content_type == 'word')

    max_len = max(len(parts_ko), len(parts_en), len(parts_ja), len(parts_zh))
    processed_list = []
    for i in range(max_len):
        processed_list.append({
            'ko': parts_ko[i] if i < len(parts_ko) else '',
            'en': parts_en[i] if i < len(parts_en) else '',
            'ja': parts_ja[i] if i < len(parts_ja) else '',
            'zh': parts_zh[i] if i < len(parts_zh) else '',
        })
            
    if content_type == 'word':
        random.shuffle(processed_list)
        processed_list = processed_list[:30]
            
    return render(request, 'typing_practice/practice_text.html', {
        'content_type': content_type,
        'language': lang,
        'theme_title': theme.title,
        'contents_json': json.dumps(processed_list),
        **access_flags,
    })

def practice_long(request, pk=None):
    """긴글 연습 페이지 (목록 선택 포함)"""
    access_flags = get_typing_access_flags(request.user)

    if not pk:
        long_texts = TypingContent.objects.filter(content_type='long').order_by('title')
        return render(request, 'typing_practice/select_long.html', {
            'long_texts': long_texts,
            **access_flags,
        })
        
    content = get_object_or_404(TypingContent, pk=pk)
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
        'contents_json': json.dumps(processed_list),
        **access_flags,
    })

def save_score(request):
    """연습 결과 저장 API"""
    if request.method == 'POST':
        try:
            if not request.user.is_authenticated:
                return JsonResponse({'status': 'not_saved', 'message': '비회원은 기록이 저장되지 않습니다.'})

            data = json.loads(request.body)
            TypingScore.objects.create(
                user=request.user,
                practice_type=data.get('type', 'key'),
                language=data.get('lang', 'ko'),
                score=data.get('score', 0),
                speed=data.get('speed', 0),
                accuracy=data.get('accuracy', 0.0)
            )
            language = data.get('lang', 'ko')
            if language in LANGUAGE_CODES:
                update_hall_of_fame_for_language(language)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'invalid method'}, status=405)

def typing_ranking(request):
    """전체 랭킹 페이지"""
    language = request.GET.get('lang', 'ko')
    age_group = request.GET.get('group')
    practice_type = request.GET.get('practice')
    category = request.GET.get('category', 'peak_speed')
    quarter_info = get_current_quarter_info()

    if language not in LANGUAGE_CODES:
        language = 'ko'
    if age_group not in AGE_GROUP_LABELS:
        age_group = get_age_group_for_user(request.user) if request.user.is_authenticated else 'seed'
    if practice_type not in PRACTICE_LABELS:
        practice_type = None
    if category not in MASTER_LABELS:
        category = 'peak_speed'

    update_hall_of_fame_for_language(language, quarter_info)
    _groups, per_practice_rows, overall_rows = build_language_ranking_snapshot(language, quarter_info)
    rows = per_practice_rows.get(age_group, {}).get(practice_type, []) if practice_type else overall_rows.get(age_group, [])
    rankings = rank_rows(rows, category)

    return render(request, 'typing_practice/ranking.html', {
        'rankings': rankings,
        'quarter_info': quarter_info,
        'selected_language': language,
        'selected_language_label': LANGUAGE_LABELS[language],
        'selected_group': age_group,
        'selected_group_label': AGE_GROUP_LABELS[age_group],
        'selected_practice': practice_type,
        'selected_practice_label': PRACTICE_LABELS.get(practice_type, '통합'),
        'selected_category': category,
        'selected_category_label': MASTER_LABELS[category],
        'group_options': AGE_GROUP_CHOICES,
        'practice_options': RANKING_PRACTICE_TYPE_CHOICES,
        'category_options': MASTER_CATEGORY_CHOICES,
        'language_options': LANGUAGE_CHOICES,
        'hall_of_fame': TypingHallOfFame.objects.filter(language=language).select_related('user').order_by('practice_type', 'category'),
    })

@user_passes_test(is_staff_check)
def content_manage(request):
    c_type = request.GET.get('type')
    if c_type in ['word', 'short', 'long']:
        contents = TypingContent.objects.filter(content_type=c_type).order_by('-id')
    else:
        contents = TypingContent.objects.all().order_by('-id')
    return render(request, 'typing_practice/content_manage.html', {'contents': contents, 'active_type': c_type or 'all'})

@user_passes_test(is_staff_check)
def content_edit(request, pk=None):
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
            TypingContent.objects.create(content_type=c_type, language=lang, emoji=emoji, title=title, text_ko=text_ko, text_en=text_en, text_ja=text_ja, text_zh=text_zh)
        return redirect('typing_content_manage')

    return render(request, 'typing_practice/content_edit.html', {'content': content})

@user_passes_test(is_staff_check)
def content_delete(request, pk):
    content = get_object_or_404(TypingContent, pk=pk)
    if request.method == 'POST':
        content.delete()
        return redirect('typing_content_manage')
    return render(request, 'typing_practice/content_confirm_delete.html', {'content': content})
