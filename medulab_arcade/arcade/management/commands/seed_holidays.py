import logging
from datetime import date

from django.core.management.base import BaseCommand

from arcade.holiday_utils import seed_holidays_for_year

logger = logging.getLogger(__name__)


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
        target_year = options["year"]
        dry_run = options["dry_run"]

        years = [target_year] if target_year else [date.today().year, date.today().year + 1]

        total_created = 0
        total_skipped = 0

        for year in years:
            self.stdout.write(f"\n--- {year}년 공휴일 처리 중 ---")
            created, skipped = seed_holidays_for_year(year, dry_run=dry_run)
            total_created += created
            total_skipped += skipped

        action = "dry-run" if dry_run else "complete"
        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone! (new {total_created}, skipped {total_skipped})"
            )
        )
