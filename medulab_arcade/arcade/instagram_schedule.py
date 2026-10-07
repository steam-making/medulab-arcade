"""인스타그램 예약 게시 추천 시간 계산.

이 계정의 게시물 반응(좋아요 + 댓글x2)을 요일/시간대별로 평균 내어 상위 시간대를 추천한다.
데이터가 부족하면 일반적인 한국 인스타그램 이용 패턴 기반 시간대로 보충한다.
"""
from collections import defaultdict
from datetime import datetime, timedelta

from django.utils import timezone

WEEKDAY_LABELS = ['월', '화', '수', '목', '금', '토', '일']

# (요일 0=월, 시, 분, 설명) - 학부모 대상 학원 계정 기준의 일반 추천
GENERAL_SLOTS = [
    (1, 20, 0, '평일 저녁 - 아이를 재운 뒤 학부모가 가장 많이 보는 시간'),
    (2, 12, 0, '평일 점심 - 짧게 훑어보는 시간'),
    (3, 21, 0, '평일 밤 - 하루 중 반응이 높은 시간'),
    (5, 10, 0, '주말 오전 - 가족이 함께 보는 시간'),
]

MIN_POSTS_FOR_DATA = 8      # 이 개수 이상 게시물에 반응 데이터가 있어야 데이터 기반 추천
MIN_POSTS_PER_SLOT = 2      # 한 시간대에 최소 이만큼 게시한 기록이 있어야 후보


def _next_occurrence(weekday, hour, minute=0, now=None):
    now = timezone.localtime(now or timezone.now())
    candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    candidate += timedelta(days=(weekday - candidate.weekday()) % 7)
    if candidate <= now + timedelta(minutes=10):
        candidate += timedelta(days=7)
    return candidate


def _slot(weekday, hour, minute, reason, source, extra=''):
    when = _next_occurrence(weekday, hour, minute)
    return {
        'label': f'{WEEKDAY_LABELS[weekday]}요일 {hour:02d}:{minute:02d}',
        'reason': reason,
        'source': source,
        'extra': extra,
        'value': when.strftime('%Y-%m-%dT%H:%M'),
        'next_text': f'{when.month}/{when.day}({WEEKDAY_LABELS[when.weekday()]}) {when:%H:%M}',
    }


def recommend_post_times(limit=4):
    """반환: {'slots': [...], 'data_based': bool, 'analyzed_posts': int}"""
    from .models import InstagramPost

    posts = list(InstagramPost.objects.filter(posted_at__isnull=False, is_excluded=False)
                 .values_list('posted_at', 'like_count', 'comments_count'))
    with_metrics = [p for p in posts if (p[1] or p[2])]

    slots = []
    data_based = len(with_metrics) >= MIN_POSTS_FOR_DATA
    if data_based:
        buckets = defaultdict(list)
        for posted_at, likes, comments in posts:
            local = timezone.localtime(posted_at)
            buckets[(local.weekday(), local.hour)].append((likes or 0) + 2 * (comments or 0))
        ranked = sorted(
            ((sum(v) / len(v), len(v), key) for key, v in buckets.items() if len(v) >= MIN_POSTS_PER_SLOT),
            reverse=True,
        )
        for avg, n, (weekday, hour) in ranked[:limit]:
            slots.append(_slot(weekday, hour, 0, f'이 계정 게시물 {n}건의 평균 반응 {avg:.1f}점', 'data',
                               extra=f'평균 반응 {avg:.1f}'))

    used = {(s['label']) for s in slots}
    for weekday, hour, minute, reason in GENERAL_SLOTS:
        if len(slots) >= limit:
            break
        slot = _slot(weekday, hour, minute, reason, 'general')
        if slot['label'] not in used:
            slots.append(slot)
            used.add(slot['label'])

    return {'slots': slots, 'data_based': data_based and any(s['source'] == 'data' for s in slots),
            'analyzed_posts': len(with_metrics)}
