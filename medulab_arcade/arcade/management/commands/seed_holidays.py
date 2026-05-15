import logging
from datetime import date

from django.core.management.base import BaseCommand, CommandError

from arcade.models import ScheduleEvent

logger = logging.getLogger(__name__)

HOLIDAY_EVENT_TYPE = ScheduleEvent.EVENT_TYPE_HOLIDAY

# 한국 공휴일 이름 매핑 (영문→한글)
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


class Command(BaseCommand):
    help = "대한민국 공휴일을 ScheduleEvent에 자동으로 등록합니다."

    def add_arguments(self, parser):
        parser.add_argument(
            "--year",
            type=int,
            default=None,
            help="등록할 연도 (기본값: 올해 + 다음해)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="실제 저장 없이 등록될 내역만 미리보기",
        )

    def handle(self, *args, **options):
        try:
            import holidays
        except ImportError:
            raise CommandError("holidays 패키지가 필요합니다. pip install holidays")

        target_year = options["year"]
        dry_run = options["dry_run"]

        years = [target_year] if target_year else [date.today().year, date.today().year + 1]

        total_created = 0
        total_skipped = 0

        for year in years:
            kr_holidays = holidays.KR(years=year)
            self.stdout.write(f"\n--- {year}년 공휴일 처리 중 ---")

            for holiday_date, english_name in sorted(kr_holidays.items()):
                korean_name = HOLIDAY_NAME_MAP.get(english_name, english_name)
                title = f"[공휴일] {korean_name}"

                # 이미 존재하는지 확인
                exists = ScheduleEvent.objects.filter(
                    title=title,
                    start_date=holiday_date,
                    event_type=HOLIDAY_EVENT_TYPE,
                ).exists()

                if exists:
                    total_skipped += 1
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

                total_created += 1
                self.stdout.write(
                    f"  {'[PREVIEW]' if dry_run else '[CREATED]'} "
                    f"{holiday_date.isoformat()} - {title}"
                )

        action = "dry-run" if dry_run else "complete"
        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone! (new {total_created}, skipped {total_skipped})"
            )
        )
