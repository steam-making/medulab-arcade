from django.core.management.base import BaseCommand
from django.utils import timezone

from arcade.instagram_sync import publish_draft
from arcade.models import InstagramUploadDraft


class Command(BaseCommand):
    help = "예약 시각이 지난 인스타그램 업로드 초안을 게시합니다 (crontab에서 5분마다 실행)."

    def handle(self, *args, **options):
        due_ids = list(
            InstagramUploadDraft.objects.filter(
                status=InstagramUploadDraft.STATUS_SCHEDULED, scheduled_at__lte=timezone.now(),
            ).order_by('scheduled_at').values_list('pk', flat=True)
        )
        if not due_ids:
            self.stdout.write('게시할 예약이 없습니다.')
            return

        for pk in due_ids:
            # 중복 실행 방지: 상태를 '게시중'으로 먼저 선점한 프로세스만 게시한다
            claimed = InstagramUploadDraft.objects.filter(
                pk=pk, status=InstagramUploadDraft.STATUS_SCHEDULED,
            ).update(status=InstagramUploadDraft.STATUS_PUBLISHING)
            if not claimed:
                continue
            draft = InstagramUploadDraft.objects.get(pk=pk)
            result = publish_draft(draft)
            if result.get('success'):
                self.stdout.write(self.style.SUCCESS(f'#{pk} 게시 완료: {result.get("permalink", "")}'))
            else:
                self.stderr.write(self.style.ERROR(f'#{pk} 게시 실패: {draft.error_message}'))
