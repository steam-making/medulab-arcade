import logging

from django.core.management.base import BaseCommand

from arcade.models import SchoolClass
from arcade.views import generate_invoices_for_class

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "운영 중인 모든 수업에 대해 이번 달 학원비 청구서를 일괄 생성합니다 (이미 생성된 학생은 건너뜀)."

    def handle(self, *args, **options):
        total_created = 0
        for school_class in SchoolClass.objects.filter(is_active=True):
            created = generate_invoices_for_class(school_class)
            if created:
                self.stdout.write(f'{school_class.name}: {created}건 생성')
            total_created += created
        self.stdout.write(self.style.SUCCESS(f'총 {total_created}건의 청구서를 생성했습니다.'))
