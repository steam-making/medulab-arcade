"""
대한민국 공휴일 자동 등록 유틸리티

Schedule 페이지 로드 시 자동으로 호출되거나,
management command `python manage.py seed_holidays` 로도 실행 가능.
"""
import logging
from datetime import date

from arcade.models import ScheduleEvent

logger = logging.getLogger(__name__)

HOLIDAY_EVENT_TYPE = ScheduleEvent.EVENT_TYPE_HOLIDAY

HOLIDAY_NAME_MAP = {
    "New Year's Day": "새해 첫날",
    "The day preceding Korean New Year": "설날 연휴",
    "Korean New Year": "설날",
    "The second day of Korean New Year": "설날 연휴",
    "Alternative holiday for Korean New Year": "설날 대체공휴일",
    "Independence Movement Day": "삼일절",
    "Alternative holiday for Independence Movement Day": "삼일절 대체공휴일",
    "Children's Day": "어린이날",
    "Buddha's Birthday": "부처님오신날",
    "Alternative holiday for Buddha's Birthday": "부처님오신날 대체공휴일",
    "Local Election Day": "지방선거일",
    "Memorial Day": "현충일",
    "Constitution Day": "제헌절",
    "Liberation Day": "광복절",
    "Alternative holiday for Liberation Day": "광복절 대체공휴일",
    "The day preceding Chuseok": "추석 연휴",
    "Chuseok": "추석",
    "The second day of Chuseok": "추석 연휴",
    "National Foundation Day": "개천절",
    "Alternative holiday for National Foundation Day": "개천절 대체공휴일",
    "Hangul Day": "한글날",
    "Alternative holiday for Hangul Day": "한글날 대체공휴일",
    "Christmas Day": "크리스마스",
    "Alternative holiday for Christmas Day": "크리스마스 대체공휴일",
}


def seed_holidays_for_year(year, dry_run=False):
    """
    특정 연도의 대한민국 공휴일을 ScheduleEvent에 등록합니다.
    이미 존재하는 항목은 건너뜁니다.
    
    Returns:
        tuple: (created_count, skipped_count)
    """
    try:
        import holidays
    except ImportError:
        logger.warning("holidays 패키지가 설치되지 않았습니다. pip install holidays")
        return (0, 0)

    kr_holidays = holidays.KR(years=year)
    created = 0
    skipped = 0

    for holiday_date, english_name in sorted(kr_holidays.items()):
        korean_name = HOLIDAY_NAME_MAP.get(english_name, english_name)
        title = korean_name

        exists = ScheduleEvent.objects.filter(
            title=title,
            start_date=holiday_date,
            event_type=HOLIDAY_EVENT_TYPE,
        ).exists()

        if exists:
            skipped += 1
            continue

        if not dry_run:
            ScheduleEvent.objects.create(
                title=title,
                description=f"{year}년 {korean_name} ({english_name})",
                start_date=holiday_date,
                end_date=holiday_date,
                event_type=HOLIDAY_EVENT_TYPE,
                is_active=True,
            )
        created += 1

    return (created, skipped)


def ensure_holidays():
    """
    Schedule 페이지에서 호출. 올해와 내년 공휴일이 없으면 자동 등록.
    """
    today = date.today()
    needs_seeding = False
    for y in [today.year, today.year + 1]:
        if not ScheduleEvent.objects.filter(
            start_date__year=y,
            event_type=HOLIDAY_EVENT_TYPE,
        ).exists():
            needs_seeding = True
            break

    if not needs_seeding:
        return  # 이미 공휴일이 등록되어 있음

    total_created = 0
    total_skipped = 0
    for y in [today.year, today.year + 1]:
        c, s = seed_holidays_for_year(y)
        total_created += c
        total_skipped += s

    if total_created > 0:
        logger.info(
            f"공휴일 자동 등록 완료: 신규 {total_created}건, 기존 {total_skipped}건"
        )
    return (total_created, total_skipped)
