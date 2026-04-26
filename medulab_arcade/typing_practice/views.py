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
                "entries": [
                    build_rank_entry(row, "avg_speed", practice_type=practice_type)
                    for row in rank_rows(rows, "avg_speed")[:5]
                ],
            })

        overall_group_rows = overall_rows.get(age_group, [])
        groups.append({
            "code": age_group,
            "label": label,
            "score_section": {
                "category": "stamina",
                "label": "누적점수",
                "entries": [build_rank_entry(row, "stamina") for row in rank_rows(overall_group_rows, "stamina")[:5]],
            },
            "practice_sections": practice_sections,
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
                    "attempts": leader["attempts"],
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
                legend.attempts = leader["attempts"]
                legend.quarter_key = quarter_info["key"]
                legend.achieved_at = leader["first_created_at"]
                legend.save(update_fields=[
                    "user", "record_value", "score", "speed", "accuracy", "attempts",
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
                "attempts": leader["attempts"],
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
            legend.attempts = leader["attempts"]
            legend.quarter_key = quarter_info["key"]
            legend.achieved_at = leader["first_created_at"]
            legend.save(update_fields=[
                "user", "record_value", "score", "speed", "accuracy", "attempts",
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
                    "attempts": legend.attempts,
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
    """Generate typing content that matches the selected theme and content type."""
    if request.method != 'POST':
        return JsonResponse({'status': 'invalid method'}, status=405)

    try:
        data = json.loads(request.body)
        title = (data.get('title') or '').strip()
        c_type = data.get('content_type', 'word')
        count = max(1, min(int(data.get('count', 10)), 30))

        if not title:
            return JsonResponse({'status': 'error', 'message': '\uc8fc\uc81c\ub97c \uc785\ub825\ud574 \uc8fc\uc138\uc694.'})
        if c_type not in {'word', 'short', 'long'}:
            return JsonResponse({'status': 'error', 'message': '\ucf58\ud150\uce20 \uc720\ud615\uc774 \uc62c\ubc14\ub974\uc9c0 \uc54a\uc2b5\ub2c8\ub2e4.'})

        knowledge_base = {
            'it': {
                'emoji': '\U0001f4bb',
                'keywords': ['it', '\ucef4\ud4e8\ud130', '\ucf54\ub529', '\ud504\ub85c\uadf8\ub798\ubc0d', '\uc778\uacf5\uc9c0\ub2a5', 'ai', '\uc18c\ud504\ud2b8\uc6e8\uc5b4', '\uc571', '\uc6f9', '\uae30\uc220'],
                'word': ['\ud0a4\ubcf4\ub4dc', '\ub9c8\uc6b0\uc2a4', '\ubaa8\ub2c8\ud130', '\ucf54\ub529', '\uc54c\uace0\ub9ac\uc998', '\ub370\uc774\ud130', '\uc11c\ubc84', '\ubcf4\uc548', '\uc571\uac1c\ubc1c', '\ud074\ub77c\uc6b0\ub4dc', '\ub85c\ubd07', '\uc13c\uc11c', '\ud504\ub85c\uc138\uc11c', '\uba54\ubaa8\ub9ac', '\ud30c\uc774\uc36c', '\uc790\ubc14\uc2a4\ud06c\ub9bd\ud2b8', '\ub124\ud2b8\uc6cc\ud06c', '\ubc31\uc5c5', '\ub514\ubc84\uae45', '\uc5c5\ub370\uc774\ud2b8'],
                'short': ['\ucf54\ub529\uc740 \ubb38\uc81c\ub97c \ud574\uacb0\ud558\ub294 \ud798\uc744 \uae38\ub7ec\uc90d\ub2c8\ub2e4.', '\ucef4\ud4e8\ud130 \uae30\uc220\uc740 \uc6b0\ub9ac\uc758 \uc0dd\ud65c\uc744 \ub354 \ud3b8\ub9ac\ud558\uac8c \ub9cc\ub4ed\ub2c8\ub2e4.', '\uc778\uacf5\uc9c0\ub2a5\uc740 \ub2e4\uc591\ud55c \ubd84\uc57c\uc5d0\uc11c \uc0c8\ub85c\uc6b4 \uac00\ub2a5\uc131\uc744 \ubcf4\uc5ec\uc90d\ub2c8\ub2e4.', '\ubcf4\uc548 \uc2b5\uad00\uc740 \uc548\uc804\ud55c \ub514\uc9c0\ud138 \uc0dd\ud65c\uc758 \uc2dc\uc791\uc785\ub2c8\ub2e4.', '\ud074\ub77c\uc6b0\ub4dc \uc11c\ube44\uc2a4\ub294 \uc5b8\uc81c \uc5b4\ub514\uc11c\ub098 \uc790\ub8cc\ub97c \uc774\uc5b4\uc90d\ub2c8\ub2e4.'],
                'long': ['\ucef4\ud4e8\ud130 \uae30\uc220\uc740 \uacf5\ubd80\uc640 \uc0dd\ud65c \ubc29\uc2dd\uc744 \ube60\ub974\uac8c \ubc14\uafb8\uace0 \uc788\uc2b5\ub2c8\ub2e4. \uc6b0\ub9ac\ub294 \ud0a4\ubcf4\ub4dc\ub97c \ub450\ub4dc\ub9ac\uba70 \uc815\ubcf4\ub97c \ucc3e\uace0, \ud504\ub85c\uadf8\ub7a8\uc744 \ub9cc\ub4e4\uace0, \uc0c8\ub85c\uc6b4 \uc544\uc774\ub514\uc5b4\ub97c \uc2dc\ud5d8\ud569\ub2c8\ub2e4. \uae30\ubcf8\uae30\ub97c \ucc28\uadfc\ucc28\uadfc \uc775\ud788\uba74 \ub204\uad6c\ub098 \uae30\uc220\uc744 \ub3c4\uad6c\ub85c \ud65c\uc6a9\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4.', '\ucf54\ub529\uc740 \ub2e8\uc21c\ud788 \uba85\ub839\uc5b4\ub97c \uc785\ub825\ud558\ub294 \uc77c\uc774 \uc544\ub2c8\ub77c \ubb38\uc81c\ub97c \ub2e8\uacc4\ubcc4\ub85c \ud574\uacb0\ud558\ub294 \uc5f0\uc2b5\uc785\ub2c8\ub2e4. \uc791\uc740 \uc2e4\uc218\ub3c4 \ub2e4\uc2dc \uc0b4\ud3b4\ubcf4\uace0 \uace0\uce58\uba74\uc11c \ub17c\ub9ac\uc801\uc778 \uc0dd\uac01\uc774 \uc790\ub77c\ub0a9\ub2c8\ub2e4. \uafb8\uc900\ud788 \uc5f0\uc2b5\ud558\uba74 \uc2a4\uc2a4\ub85c \uc6d0\ud558\ub294 \uacb0\uacfc\ub97c \ub9cc\ub4e4\uc5b4 \ub0b4\ub294 \ud798\uc774 \ucee4\uc9d1\ub2c8\ub2e4.']
            },
            'fruit': {
                'emoji': '\U0001f34e',
                'keywords': ['\uacfc\uc77c', '\uc0ac\uacfc', '\ubc14\ub098\ub098', '\ud3ec\ub3c4', '\ub538\uae30', '\ubcf5\uc22d\uc544', '\uc74c\uc2dd'],
                'word': ['\uc0ac\uacfc', '\ubc14\ub098\ub098', '\ud3ec\ub3c4', '\ub538\uae30', '\ubcf5\uc22d\uc544', '\uc218\ubc15', '\ucc38\uc678', '\uade4', '\uc624\ub80c\uc9c0', '\uccb4\ub9ac', '\uc790\ub450', '\uba5c\ub860', '\ub9dd\uace0', '\ud0a4\uc704', '\uc11d\ub958', '\ub808\ubaac', '\ub77c\uc784', '\ubb34\ud654\uacfc', '\ube14\ub8e8\ubca0\ub9ac', '\ud30c\uc778\uc560\ud50c'],
                'short': ['\uacfc\uc77c\uc740 \uc0c1\ud07c\ud55c \ub9db\uacfc \ud5a5\uc73c\ub85c \uae30\ubd84\uc744 \uc88b\uac8c \ud569\ub2c8\ub2e4.', '\uacc4\uc808\ub9c8\ub2e4 \ub9db\uc788\ub294 \uacfc\uc77c\uc774 \ub2e4\ub974\uac8c \ucc3e\uc544\uc635\ub2c8\ub2e4.', '\uc798 \uc775\uc740 \uacfc\uc77c\uc740 \uc0c9\uacfc \ud5a5\ub9cc\uc73c\ub85c\ub3c4 \uc990\uac70\uc6c0\uc744 \uc90d\ub2c8\ub2e4.', '\uacfc\uc77c\uc740 \uac04\uc2dd\uc73c\ub85c \uba39\uae30 \uc88b\uace0 \uc218\ubd84\ub3c4 \ud48d\ubd80\ud569\ub2c8\ub2e4.', '\ub2e4\uc591\ud55c \uacfc\uc77c\uc744 \uace0\ub974\uba74 \uc2dd\ud0c1\uc774 \ub354\uc6b1 \ud654\uc0ac\ud574\uc9d1\ub2c8\ub2e4.'],
                'long': ['\uacfc\uc77c\uc740 \uacc4\uc808\uc758 \ubcc0\ud654\ub97c \uac00\uc7a5 \uc27d\uac8c \ub290\ub07c\uac8c \ud574 \uc8fc\ub294 \uba39\uac70\ub9ac\uc785\ub2c8\ub2e4. \ubd04\uc5d0\ub294 \ub538\uae30 \ud5a5\uc774 \ud37c\uc9c0\uace0 \uc5ec\ub984\uc5d0\ub294 \uc218\ubc15\uacfc \ucc38\uc678\uac00 \uc2dc\uc6d0\ud568\uc744 \ub354\ud569\ub2c8\ub2e4. \uac00\uc744\uc5d0\ub294 \uc0ac\uacfc\uc640 \ubc30\uac00 \ud48d\uc131\ud558\uac8c \uc775\uc5b4 \uac00\uace0 \uaca8\uc6b8\uc5d0\ub294 \uade4\uc774 \uc2dd\ud0c1\uc744 \ubc1d\uac8c \ucc44\uc6cc \uc90d\ub2c8\ub2e4.', '\uc0c9\uc774 \uace0\uc6b4 \uacfc\uc77c\uc744 \uc798 \uc50c\uc5b4 \ud55c\uc785 \ud06c\uae30\ub85c \ub2f4\uc544 \ub450\uba74 \ubcf4\uae30\ub9cc \ud574\ub3c4 \uae30\ubd84\uc774 \uc88b\uc544\uc9d1\ub2c8\ub2e4. \uac00\uc871\uacfc \ud568\uaed8 \uc88b\uc544\ud558\ub294 \uacfc\uc77c\uc744 \ub098\ub204\uc5b4 \uba39\uc73c\uba70 \uacc4\uc808 \uc774\uc57c\uae30\ub97c \ub098\ub204\ub294 \uc2dc\uac04\uc740 \uc0dd\uac01\ubcf4\ub2e4 \uc624\ub798 \uae30\uc5b5\uc5d0 \ub0a8\uc2b5\ub2c8\ub2e4.']
            },
            'animal': {
                'emoji': '\U0001f43e',
                'keywords': ['\ub3d9\ubb3c', '\uac15\uc544\uc9c0', '\uace0\uc591\uc774', '\ud638\ub791\uc774', '\uc0ac\uc790', '\ud1a0\ub07c', '\ud391\uadc4', '\uc0c8'],
                'word': ['\uac15\uc544\uc9c0', '\uace0\uc591\uc774', '\ud1a0\ub07c', '\uc0ac\uc790', '\ud638\ub791\uc774', '\uae30\ub9b0', '\ucf54\ub07c\ub9ac', '\ud391\uadc4', '\ub3c5\uc218\ub9ac', '\ub3cc\uace0\ub798', '\ud310\ub2e4', '\uacf0', '\uc5ec\uc6b0', '\ub291\ub300', '\uc218\ub2ec', '\uc6d0\uc22d\uc774', '\ud558\ub9c8', '\uc5bc\ub8e9\ub9d0', '\uc591', '\uc5fc\uc18c'],
                'short': ['\ub3d9\ubb3c\uc740 \uc800\ub9c8\ub2e4 \ub2e4\ub978 \ubaa8\uc2b5\uacfc \uc2b5\uc131\uc744 \uac00\uc9c0\uace0 \uc788\uc2b5\ub2c8\ub2e4.', '\ubc18\ub824\ub3d9\ubb3c\uacfc \ud568\uaed8\ud558\uba74 \uc77c\uc0c1\uc5d0 \ub530\ub73b\ud55c \uc6c3\uc74c\uc774 \ub298\uc5b4\ub0a9\ub2c8\ub2e4.', '\ub3d9\ubb3c\uc758 \uc6c0\uc9c1\uc784\uc744 \uad00\ucc30\ud558\uba74 \uc790\uc5f0\uc758 \uc9c8\uc11c\ub97c \ubc30\uc6b8 \uc218 \uc788\uc2b5\ub2c8\ub2e4.', '\uc232\uacfc \ubc14\ub2e4\uc5d0\ub294 \ub2e4\uc591\ud55c \ub3d9\ubb3c\ub4e4\uc774 \uac01\uc790\uc758 \ubc29\uc2dd\uc73c\ub85c \uc0b4\uc544\uac11\ub2c8\ub2e4.', '\ub3d9\ubb3c\uc744 \uc544\ub07c\ub294 \ub9c8\uc74c\uc740 \uc790\uc5f0\uc744 \uc9c0\ud0a4\ub294 \ub9c8\uc74c\uacfc \uc774\uc5b4\uc9d1\ub2c8\ub2e4.'],
                'long': ['\ub3d9\ubb3c\uc740 \uc0ac\ub294 \uacf3\uc5d0 \ub530\ub77c \ubab8\uc758 \ubaa8\uc591\uacfc \uc0dd\ud65c \ubc29\uc2dd\uc774 \ub2ec\ub77c\uc9d1\ub2c8\ub2e4. \ubd81\uadf9\uc5d0 \uc0ac\ub294 \ub3d9\ubb3c\uc740 \ucd94\uc704\ub97c \uacac\ub514\ub294 \ud138\uacfc \uc9c0\ubc29\uce35\uc744 \uac00\uc9c0\uace0 \uc788\uace0, \uc0ac\ub9c9\uc758 \ub3d9\ubb3c\uc740 \ubb3c\uc744 \uc544\ub07c\uba70 \uc6c0\uc9c1\uc785\ub2c8\ub2e4. \uadf8\ub798\uc11c \ub3d9\ubb3c\uc744 \uc0b4\ud3b4\ubcf4\uba74 \uc790\uc5f0\ud658\uacbd\uc758 \ud2b9\uc9d5\ub3c4 \ud568\uaed8 \uc774\ud574\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4.', '\ubc18\ub824\ub3d9\ubb3c\uacfc \uc9c0\ub0b4\ub2e4 \ubcf4\uba74 \uba39\uc774 \uc8fc\uae30\uc640 \uc0b0\ucc45, \ud734\uc2dd \uc2dc\uac04\uc744 \uafb8\uc900\ud788 \ucc59\uaca8\uc57c \ud569\ub2c8\ub2e4. \uc791\uc740 \uc2b5\uad00\uc774 \uc313\uc5ec \uc2e0\ub8b0\uac00 \uc0dd\uae30\uace0 \uc11c\ub85c\uc758 \uc0dd\ud65c\ub3c4 \uc548\uc815\ub429\ub2c8\ub2e4. \uc0dd\uba85\uc744 \ub3cc\ubcf4\ub294 \uc77c\uc5d0\ub294 \ucc45\uc784\uac10\uacfc \ubc30\ub824\uac00 \uaf2d \ud544\uc694\ud569\ub2c8\ub2e4.']
            },
            'space': {
                'emoji': '\U0001f680',
                'keywords': ['\uc6b0\uc8fc', '\ud589\uc131', '\ubcc4', '\ub2ec', '\ud0dc\uc591', '\ub85c\ucf13', '\uc740\ud558', '\ucc9c\uccb4'],
                'word': ['\uc6b0\uc8fc', '\ud589\uc131', '\ubcc4\uc790\ub9ac', '\ud0dc\uc591', '\ub2ec', '\uc740\ud558\uc218', '\ub85c\ucf13', '\ud0d0\uc0ac\uc120', '\uc911\ub825', '\ucc9c\uccb4\ub9dd\uc6d0\uacbd', '\uc6b0\uc8fc\ubcf5', '\uada4\ub3c4', '\ud654\uc131', '\ubaa9\uc131', '\ud1a0\uc131', '\uae08\uc131', '\uc9c0\uad6c', '\ube14\ub799\ud640', '\ud61c\uc131', '\uc18c\ud589\uc131'],
                'short': ['\uc6b0\uc8fc\ub294 \ub05d\uc5c6\uc774 \ub113\uace0 \uc2e0\ube44\ub85c\uc6b4 \uc774\uc57c\uae30\ub85c \uac00\ub4dd\ud569\ub2c8\ub2e4.', '\ubc24\ud558\ub298\uc758 \ubcc4\uc744 \ubcf4\uba74 \uba40\ub9ac \uc788\ub294 \ud589\uc131\uc744 \ub5a0\uc62c\ub9ac\uac8c \ub429\ub2c8\ub2e4.', '\uc6b0\uc8fc \ud0d0\uc0ac\ub294 \uc0c8\ub85c\uc6b4 \uc9c0\uc2dd\uc744 \ubc1c\uacac\ud558\ub294 \ub3c4\uc804\uc785\ub2c8\ub2e4.', '\ub85c\ucf13\uc740 \uac15\ud55c \ucd94\uc9c4\ub825\uc73c\ub85c \ud558\ub298\uc744 \ud5a5\ud574 \ub0a0\uc544\uc624\ub985\ub2c8\ub2e4.', '\uc6b0\uc8fc\uc5d0 \ub300\ud55c \ud638\uae30\uc2ec\uc740 \uacfc\ud559\uc758 \ubc1c\uc804\uc744 \uc774\ub055\ub2c8\ub2e4.'],
                'long': ['\uc6b0\uc8fc\ub294 \uc6b0\ub9ac\uac00 \uc0c1\uc0c1\ud558\ub294 \uac83\ubcf4\ub2e4 \ud6e8\uc52c \ub113\uace0 \uc870\uc6a9\ud55c \uacf5\uac04\uc785\ub2c8\ub2e4. \uc218\ub9ce\uc740 \ubcc4\uacfc \ud589\uc131, \uc740\ud558\uac00 \uc11c\ub85c \ub2e4\ub978 \uc18d\ub3c4\ub85c \uc6c0\uc9c1\uc774\uba70 \uac70\ub300\ud55c \uc9c8\uc11c\ub97c \uc774\ub8e8\uace0 \uc788\uc2b5\ub2c8\ub2e4. \ub9dd\uc6d0\uacbd\uc73c\ub85c \ubc24\ud558\ub298\uc744 \ubc14\ub77c\ubcf4\uba74 \uc544\uc8fc \uba3c \uacf3\uc758 \ube5b\uc774 \uc9c0\uae08 \uc6b0\ub9ac\uc5d0\uac8c \ub3c4\ucc29\ud558\ub294 \ub180\ub77c\uc6b4 \uc21c\uac04\uc744 \ub9cc\ub098\uac8c \ub429\ub2c8\ub2e4.', '\uc6b0\uc8fc \ud0d0\uc0ac\ub294 \ub9ce\uc740 \uc2dc\uac04\uacfc \uae30\uc220, \ud611\ub825\uc774 \ud544\uc694\ud55c \uc77c\uc785\ub2c8\ub2e4. \ud0d0\uc0ac\uc120 \ud55c \ub300\ub97c \ubcf4\ub0b4\uae30 \uc704\ud574 \uacfc\ud559\uc790\uc640 \uc5d4\uc9c0\ub2c8\uc5b4\uac00 \ud568\uaed8 \uacc4\ud68d\uc744 \uc138\uc6b0\uace0 \uc791\uc740 \uc624\ub958\uae4c\uc9c0 \uc810\uac80\ud569\ub2c8\ub2e4. \uadf8 \uacfc\uc815\uc5d0\uc11c \uc6b0\ub9ac\ub294 \uc0c8\ub85c\uc6b4 \uc9c0\uc2dd\ubfd0 \uc544\ub2c8\ub77c \ub3c4\uc804\ud558\ub294 \ud0dc\ub3c4\ub3c4 \ubc30\uc6b0\uac8c \ub429\ub2c8\ub2e4.']
            },
            'sports': {
                'emoji': '\u26bd',
                'keywords': ['\uc6b4\ub3d9', '\ucd95\uad6c', '\ub18d\uad6c', '\uc57c\uad6c', '\ubc30\ub4dc\ubbfc\ud134', '\uc218\uc601', '\uc2a4\ud3ec\uce20'],
                'word': ['\ucd95\uad6c', '\ub18d\uad6c', '\uc57c\uad6c', '\ubc30\uad6c', '\uc218\uc601', '\ub2ec\ub9ac\uae30', '\ubc30\ub4dc\ubbfc\ud134', '\ud0c1\uad6c', '\uccb4\uc870', '\uace8\ud504', '\ud14c\ub2c8\uc2a4', '\uc591\uad81', '\ud0dc\uad8c\ub3c4', '\uc720\ub3c4', '\uc2a4\ucf00\uc774\ud2b8', '\ub4f1\uc0b0', '\uc904\ub118\uae30', '\ub9c8\ub77c\ud1a4', '\ud558\ud0a4', '\uc11c\ud551'],
                'short': ['\uc6b4\ub3d9\uc740 \ubab8\uacfc \ub9c8\uc74c\uc744 \uac74\uac15\ud558\uac8c \ub9cc\ub4e4\uc5b4 \uc90d\ub2c8\ub2e4.', '\ud300 \uc2a4\ud3ec\uce20\ub294 \ud611\ub3d9\uacfc \uc18c\ud1b5\uc758 \uc911\uc694\uc131\uc744 \uc54c\ub824 \uc90d\ub2c8\ub2e4.', '\uafb8\uc900\ud55c \uc5f0\uc2b5\uc740 \uc790\uc2e0\uac10 \uc788\ub294 \uc6c0\uc9c1\uc784\uc73c\ub85c \uc774\uc5b4\uc9d1\ub2c8\ub2e4.', '\uacbd\uae30\uc5d0\uc11c\ub294 \uc2e4\ub825\ub9cc\ud07c \uc9d1\uc911\ub825\uacfc \uc608\uc808\ub3c4 \uc911\uc694\ud569\ub2c8\ub2e4.', '\uc6b4\ub3d9 \ud6c4\uc5d0 \ub290\ub07c\ub294 \uc0c1\ucf8c\ud568\uc740 \ud070 \uc990\uac70\uc6c0\uc774 \ub429\ub2c8\ub2e4.'],
                'long': ['\uc6b4\ub3d9\uc740 \uae30\ub85d\uc744 \uacbd\uc7c1\ud558\ub294 \ud65c\ub3d9\uc774\uae30\ub3c4 \ud558\uc9c0\ub9cc \uc2a4\uc2a4\ub85c \uc131\uc7a5\ud558\ub294 \uacfc\uc815\uc744 \ub290\ub07c\uac8c \ud574 \uc8fc\ub294 \uc2dc\uac04\uc785\ub2c8\ub2e4. \ucc98\uc74c\uc5d0\ub294 \uc5b4\ub835\uac8c \ub290\uaef4\uc9c0\ub358 \ub3d9\uc791\ub3c4 \ubc18\ubcf5\ud574\uc11c \uc5f0\uc2b5\ud558\uba74 \uc870\uae08\uc529 \uc790\uc5f0\uc2a4\ub7ec\uc6cc\uc9d1\ub2c8\ub2e4. \uadf8\ub807\uac8c \uc313\uc778 \uacbd\ud5d8\uc740 \ub2e4\ub978 \uacf5\ubd80\ub098 \uc0dd\ud65c \uc2b5\uad00\uc5d0\ub3c4 \uc88b\uc740 \uc601\ud5a5\uc744 \uc90d\ub2c8\ub2e4.', '\ud300 \uc2a4\ud3ec\uce20\uc5d0\uc11c\ub294 \ud63c\uc790 \uc798\ud558\ub294 \uac83\ubcf4\ub2e4 \uc11c\ub85c\ub97c \ubbff\uace0 \uc6c0\uc9c1\uc774\ub294 \ud0dc\ub3c4\uac00 \uc911\uc694\ud569\ub2c8\ub2e4. \ud328\uc2a4\ub97c \uc5f0\uacb0\ud558\uace0 \uc5ed\ud560\uc744 \ub098\ub204\uba70 \ud750\ub984\uc744 \ub9cc\ub4dc\ub294 \uacfc\uc815\uc5d0\uc11c \ud611\ub3d9\uc2ec\uc774 \uc790\ub78d\ub2c8\ub2e4. \ud568\uaed8 \ub540 \ud758\ub9b0 \uae30\uc5b5\uc740 \uc624\ub798 \ub0a8\ub294 \uc751\uc6d0\uc774 \ub429\ub2c8\ub2e4.']
            },
            'history': {
                'emoji': '\U0001f3fa',
                'keywords': ['\uc5ed\uc0ac', '\ud55c\uad6d\uc0ac', '\uc138\uacc4\uc0ac', '\uc655', '\uc870\uc120', '\uace0\uad6c\ub824', '\ubc31\uc81c', '\uc2e0\ub77c'],
                'word': ['\ud55c\uad6d\uc0ac', '\uc138\uacc4\uc0ac', '\uc870\uc120', '\uace0\uad6c\ub824', '\ubc31\uc81c', '\uc2e0\ub77c', '\uace0\ub824', '\ud6c8\ubbfc\uc815\uc74c', '\ub3c5\ub9bd\uc6b4\ub3d9', '\ubb38\ud654\uc7ac', '\uc655\uc2e4', '\uc720\uc801\uc9c0', '\ud55c\uc591', '\uad81\uafd0', '\uc7a5\uad70', '\uc5f0\ud45c', '\uac1c\ud601', '\uc678\uad50', '\uc804\ud1b5', '\uae30\ub85d'],
                'short': ['\uace0\uc870\uc120\uc740 \ub2e8\uad70 \uc2e0\ud654\uc640 \ud568\uaed8 \ud55c\uad6d\uc0ac\uc758 \uc2dc\uc791\uc73c\ub85c \uc54c\ub824\uc838 \uc788\uc2b5\ub2c8\ub2e4.', '\uad11\uac1c\ud1a0\ub300\uc655\uc740 \uace0\uad6c\ub824\uc758 \uc601\ud1a0\ub97c \ud06c\uac8c \ub113\ud78c \uc655\uc73c\ub85c \uae30\uc5b5\ub429\ub2c8\ub2e4.', '\uc2e0\ub77c\ub294 \ud654\ub791\ub3c4\ub97c \ud1b5\ud574 \uc0c8\ub85c\uc6b4 \uc778\uc7ac\ub97c \uae38\ub7ec \ub0c8\uc2b5\ub2c8\ub2e4.', '\uace0\ub824\ub294 \uae08\uc18d \ud65c\uc790\uc640 \uccad\uc790 \ubb38\ud654\ub85c \ub192\uc740 \uc218\uc900\uc744 \ubcf4\uc5ec \uc8fc\uc5c8\uc2b5\ub2c8\ub2e4.', '\uc138\uc885\ub300\uc655\uc740 \ud6c8\ubbfc\uc815\uc74c\uc744 \ucc3d\uc81c\ud558\uc5ec \ubc31\uc131\ub4e4\uc774 \uae00\uc744 \ub354 \uc27d\uac8c \uc775\ud788\uac8c \ud588\uc2b5\ub2c8\ub2e4.', '\uc784\uc9c4\uc65c\ub780 \ub54c \uc774\uc21c\uc2e0\uc740 \uac70\ubd81\uc120\uacfc \ud568\uaed8 \ubc14\ub2e4\ub97c \uc9c0\ucf1c \ub0c8\uc2b5\ub2c8\ub2e4.', '\uc720\uad00\uc21c\uc740 3\u00b71 \uc6b4\ub3d9\uc5d0\uc11c \ub300\ud55c\ub3c5\ub9bd\uc744 \uc678\uce58\uba70 \uc6a9\uae30\ub97c \ubcf4\uc5ec \uc8fc\uc5c8\uc2b5\ub2c8\ub2e4.', '\ud765\uc120\ub300\uc6d0\uad70\uc740 \uc11c\uc6d0 \uc815\ub9ac\uc640 \uacbd\ubcf5\uad81 \uc911\uac74\uc744 \ucd94\uc9c4\ud588\uc2b5\ub2c8\ub2e4.', '\uac11\uc624\uac1c\ud601\uc740 \uc870\uc120 \uc0ac\ud68c\ub97c \ubc14\uafb8\uae30 \uc704\ud55c \uc2dc\ub3c4\uc600\uc2b5\ub2c8\ub2e4.', '\ub300\ud55c\ubbfc\uad6d \uc784\uc2dc\uc815\ubd80\ub294 \ub3c5\ub9bd\uc6b4\ub3d9\uc758 \uc911\uc2ec \uc5ed\ud560\uc744 \ub9e1\uc558\uc2b5\ub2c8\ub2e4.'],
                'long': ['\uace0\uc870\uc120\uc744 \uc2dc\uc791\uc73c\ub85c \uace0\uad6c\ub824\u00b7\ubc31\uc81c\u00b7\uc2e0\ub77c\uac00 \uc131\uc7a5\ud558\uba74\uc11c \ud55c\ubc18\ub3c4\uc5d0\ub294 \ub2e4\uc591\ud55c \uad6d\uac00\uac00 \ubc1c\uc804\ud588\uc2b5\ub2c8\ub2e4. \uadf8 \uacfc\uc815\uc5d0\uc11c \uc0ac\ub78c\ub4e4\uc740 \uc804\uc7c1\uacfc \uad50\ub958\ub97c \uacaa\uc73c\uba70 \uc0c8\ub85c\uc6b4 \ubb38\ud654\ub97c \ub9cc\ub4e4\uc5b4 \uac14\uace0, \uadf8 \ud750\ub984\uc740 \uc624\ub298\ub0a0 \ud55c\uad6d \ubb38\ud654\uc758 \ubc14\ud0d5\uc774 \ub418\uc5c8\uc2b5\ub2c8\ub2e4.', '\uace0\ub824\ub294 \uae08\uc18d \ud65c\uc790\uc640 \uccad\uc790\ub85c \ub192\uc740 \ubb38\ud654 \uc218\uc900\uc744 \ubcf4\uc5ec \uc8fc\uc5c8\uace0, \uc870\uc120\uc740 \ud6c8\ubbfc\uc815\uc74c\uacfc \uacbd\ubcf5\uad81, \uc2e4\ud559 \ub4f1\uc744 \ud1b5\ud574 \uc790\uc2e0\ub9cc\uc758 \uc9c0\uc2dd\uacfc \uc81c\ub3c4\ub97c \ubc1c\uc804\uc2dc\ucf30\uc2b5\ub2c8\ub2e4. \ud55c\uad6d\uc0ac\ub97c \uc0b4\ud3b4\ubcf4\uba74 \uc2dc\ub300\ub9c8\ub2e4 \ub2ec\ub77c\uc9c4 \uc0b6\uc758 \ubaa8\uc2b5\uacfc \uac00\uce58\uad00\uc744 \ud568\uaed8 \uc774\ud574\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4.', '\uc77c\uc81c\uac15\uc810\uae30\uc5d0\ub294 \ub9ce\uc740 \uc0ac\ub78c\ub4e4\uc774 \ud559\uad50\uc640 \uac70\ub9ac, \ud574\uc678 \uac01\uc9c0\uc5d0\uc11c \ub3c5\ub9bd\uc744 \uc704\ud574 \ub178\ub825\ud588\uc2b5\ub2c8\ub2e4. 3\u00b71 \uc6b4\ub3d9\uacfc \uc784\uc2dc\uc815\ubd80 \uc218\ub9bd\uc740 \uadf8 \ub73b\uc744 \ubaa8\uc544 \ub300\ud55c\ubbfc\uad6d\uc758 \ubbf8\ub798\ub97c \uc900\ube44\ud55c \uc911\uc694\ud55c \uc7a5\uba74\uc73c\ub85c \ub0a8\uc544 \uc788\uc2b5\ub2c8\ub2e4.']
            },
        }

        fallback_category = {
            'emoji': '\u2728',
            'keywords': [],
            'word': [title, f'{title} \uc5f0\uc2b5', f'{title} \uae30\ubcf8', f'{title} \uc751\uc6a9', f'{title} \ud0a4\uc6cc\ub4dc', f'{title} \ud0d0\uad6c', f'{title} \ud504\ub85c\uc81d\ud2b8', f'{title} \ud559\uc2b5', f'{title} \uc9d1\uc911', f'{title} \ucc4c\ub9b0\uc9c0'],
            'short': [
                f'{title} \uc8fc\uc81c\ub294 \ub2e4\uc591\ud55c \uc0dd\uac01\uc744 \uc790\uc5f0\uc2a4\ub7fd\uac8c \uc774\ub04c\uc5b4 \ub0c5\ub2c8\ub2e4.',
                f'{title} \ub0b4\uc6a9\uc744 \ucc28\ubd84\ud788 \uc77d\uace0 \ubc18\ubcf5\ud574\uc11c \uc785\ub825\ud574 \ubcf4\uc138\uc694.',
                f'{title} \uc5f0\uc2b5\uc740 \uc18d\ub3c4\uc640 \uc815\ud655\ub3c4\ub97c \ud568\uaed8 \ud0a4\uc6b0\ub294 \ub370 \ub3c4\uc6c0\uc774 \ub429\ub2c8\ub2e4.',
                f'{title} \uc8fc\uc81c\ub97c \uc775\ud788\uba70 \ud45c\ud604\ub825\uacfc \uc9d1\uc911\ub825\uc744 \ud568\uaed8 \ub192\uc5ec \ubcf4\uc138\uc694.',
                f'{title} \ud575\uc2ec \ub2e8\uc5b4\ub97c \uc775\ud788\uba74 \uad00\ub828 \ub0b4\uc6a9\uc744 \ub354 \uc27d\uac8c \uc774\ud574\ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4.',
            ],
            'long': [
                f'{title} \uc8fc\uc81c\ub294 \uc77d\uace0 \uc774\ud574\ud55c \ub4a4 \ucc28\ubd84\ud558\uac8c \uc785\ub825\ud558\uae30\uc5d0 \uc88b\uc740 \ub0b4\uc6a9\uc785\ub2c8\ub2e4. \uc775\uc219\ud55c \ud45c\ud604\ubd80\ud130 \ucc9c\ucc9c\ud788 \ub530\ub77c \uce58\uba74\uc11c \uc18d\ub3c4\ubcf4\ub2e4 \uc815\ud655\ub3c4\ub97c \uba3c\uc800 \uc7a1\uc544 \ubcf4\uc138\uc694. \ubb38\uc7a5\uc744 \ubc18\ubcf5\ud574\uc11c \uc785\ub825\ud558\uba74 \uc190\uac00\ub77d \uc6c0\uc9c1\uc784\uacfc \uc9d1\uc911\ub825\uc774 \ud568\uaed8 \uc548\uc815\ub429\ub2c8\ub2e4.',
                f'{title} \uad00\ub828 \ub0b4\uc6a9\uc744 \uc815\ub9ac\ud558\uba70 \uc785\ub825 \uc5f0\uc2b5\uc744 \ud558\uba74 \ub2e8\uc21c\ud55c \ud0c0\uc790 \uc5f0\uc2b5\uc744 \ub118\uc5b4 \ud559\uc2b5 \ud6a8\uacfc\uae4c\uc9c0 \uc5bb\uc744 \uc218 \uc788\uc2b5\ub2c8\ub2e4. \ud55c \uc904\uc529 \ud638\ud761\uc744 \ub9de\ucdb0 \uc785\ub825\ud558\uba74 \uc2e4\uc218\ub294 \uc904\uace0 \uc804\uccb4 \ud750\ub984\uc740 \ub354 \uc790\uc5f0\uc2a4\ub7ec\uc6cc\uc9d1\ub2c8\ub2e4.',
            ],
        }

        title_lower = title.lower()
        selected = fallback_category
        for info in knowledge_base.values():
            if any(keyword in title_lower for keyword in info['keywords']):
                selected = info
                break

        pool = list(selected.get(c_type) or fallback_category[c_type])
        if not pool:
            pool = list(fallback_category[c_type])

        target_count = count
        generated_ko_list = []
        while len(generated_ko_list) < target_count:
            shuffled = list(pool)
            random.shuffle(shuffled)
            remaining = target_count - len(generated_ko_list)
            generated_ko_list.extend(shuffled[:remaining])

        if c_type == 'long':
            ko_text = '\n\n'.join(generated_ko_list)
        elif c_type == 'short':
            ko_text = '\n'.join(generated_ko_list)
        else:
            ko_text = ', '.join(generated_ko_list)

        def to_target_text(source_text, target_code):
            try:
                translated = GoogleTranslator(source='auto', target='zh-CN' if target_code == 'zh' else target_code).translate(source_text)
                if target_code == 'ja':
                    kks = pykakasi.kakasi()
                    converted = kks.convert(translated)
                    return ''.join(item['kana'] for item in converted).strip() or translated
                if target_code == 'zh':
                    pinyin_list = pinyin(translated, style=Style.NORMAL)
                    return ' '.join(item[0] for item in pinyin_list if item and item[0]).strip() or translated
                return translated
            except Exception:
                return ''

        results = {
            'ko': ko_text,
            'en': to_target_text(ko_text, 'en'),
            'ja': to_target_text(ko_text, 'ja'),
            'zh': to_target_text(ko_text, 'zh'),
            'emoji': selected.get('emoji', '\u2728'),
        }

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
        'ranking_data_json': ranking_data,
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
