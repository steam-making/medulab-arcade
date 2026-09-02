from django.core.management.base import BaseCommand

from arcade.instagram_sync import sync_posts


class Command(BaseCommand):
    help = "인스타그램 게시물을 그래프 API로 동기화합니다 (crontab 등록용)."

    def handle(self, *args, **options):
        result = sync_posts()
        if result.get('success'):
            self.stdout.write(self.style.SUCCESS(f"동기화 완료: {result.get('count', 0)}건"))
        else:
            self.stderr.write(self.style.ERROR(f"동기화 실패: {result.get('error')}"))
