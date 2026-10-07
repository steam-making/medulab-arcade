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

MIN_POSTS_FOR_DATA = 30     # 반응 데이터가 있는 게시물이 이 개수 이상일 때만 데이터 기반 추천
MIN_POSTS_PER_BUCKET = 5    # 평일/주말 x 3시간 구간에 최소 이만큼 게시한 기록이 있어야 후보
RECENT_DAYS = 730           # 계정이 커지기 전의 오래된 게시물 영향을 줄이기 위해 최근 2년 위주로 계산
BLOCK_HOURS = 3
EARLIEST_RECOMMEND_HOUR = 6  # 새벽(0~6시)은 추천하지 않음


def _next_occurrence(weekday, hour, minute=0, now=None):
    now = timezone.localtime(now or timezone.now())
    candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    candidate += timedelta(days=(weekday - candidate.weekday()) % 7)
    if candidate <= now + timedelta(minutes=10):
        candidate += timedelta(days=7)
    return candidate


def _next_in_group(is_weekend, hour, minute=0, now=None):
    """평일/주말 그룹에 속하는 가장 가까운 미래 시각 (그룹 안에서 가장 이른 날)"""
    weekdays = (5, 6) if is_weekend else (0, 1, 2, 3, 4)
    return min(_next_occurrence(w, hour, minute, now) for w in weekdays)


def _slot(when, label, reason, source):
    return {
        'label': label,
        'reason': reason,
        'source': source,
        'value': when.strftime('%Y-%m-%dT%H:%M'),
        'next_text': f'{when.month}/{when.day}({WEEKDAY_LABELS[when.weekday()]}) {when:%H:%M}',
    }


def recommend_post_times(limit=4):
    """반환: {'slots': [...], 'data_based': bool, 'analyzed_posts': int}"""
    from .models import InstagramPost

    now = timezone.now()
    posts = list(InstagramPost.objects.filter(posted_at__isnull=False, is_excluded=False)
                 .values_list('posted_at', 'like_count', 'comments_count'))
    with_metrics = [p for p in posts if (p[1] or p[2])]

    recent = [p for p in with_metrics if p[0] >= now - timedelta(days=RECENT_DAYS)]
    pool = recent if len(recent) >= MIN_POSTS_FOR_DATA else with_metrics

    slots = []
    if len(pool) >= MIN_POSTS_FOR_DATA:
        buckets = defaultdict(list)
        for posted_at, likes, comments in pool:
            local = timezone.localtime(posted_at)
            block = local.hour // BLOCK_HOURS * BLOCK_HOURS
            if block < EARLIEST_RECOMMEND_HOUR:
                continue
            buckets[(local.weekday() >= 5, block)].append((likes or 0) + 2 * (comments or 0))
        ranked = sorted(
            ((sum(v) / len(v), len(v), key) for key, v in buckets.items() if len(v) >= MIN_POSTS_PER_BUCKET),
            reverse=True,
        )
        for avg, n, (is_weekend, block) in ranked[:limit]:
            hour = block + BLOCK_HOURS // 2  # 구간 가운데 시각 (예: 9~12시 -> 10:00)
            when = _next_in_group(is_weekend, hour)
            kind = '주말' if is_weekend else '평일'
            slots.append(_slot(
                when, f'{kind} {block:02d}~{block + BLOCK_HOURS:02d}시 (추천 {hour:02d}:00)',
                f'최근 게시물 {n}건 평균 반응 {avg:.1f}점', 'data'))

    used = {s['label'] for s in slots}
    for weekday, hour, minute, reason in GENERAL_SLOTS:
        if len(slots) >= limit:
            break
        when = _next_occurrence(weekday, hour, minute)
        slot = _slot(when, f'{WEEKDAY_LABELS[weekday]}요일 {hour:02d}:{minute:02d}', reason, 'general')
        if slot['label'] not in used:
            slots.append(slot)
            used.add(slot['label'])

    return {'slots': slots, 'data_based': any(s['source'] == 'data' for s in slots),
            'analyzed_posts': len(pool)}
