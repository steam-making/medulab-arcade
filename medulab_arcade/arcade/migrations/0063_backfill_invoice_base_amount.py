from django.db import migrations


def backfill_base_amount(apps, schema_editor):
    """base_amount 필드 도입 이전에 생성된 청구서는 0으로 남아있으므로
    amount + absence_deduction 으로 정상 수업비를 복원한다."""
    TuitionInvoice = apps.get_model('arcade', 'TuitionInvoice')
    for invoice in TuitionInvoice.objects.filter(base_amount=0):
        restored = invoice.amount + invoice.absence_deduction
        if restored:
            invoice.base_amount = restored
            invoice.save(update_fields=['base_amount'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('arcade', '0062_backfill_monthly_sessions'),
    ]

    operations = [
        migrations.RunPython(backfill_base_amount, noop_reverse),
    ]
