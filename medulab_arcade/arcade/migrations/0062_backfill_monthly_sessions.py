from django.db import migrations


def backfill_monthly_sessions(apps, schema_editor):
    SchoolClass = apps.get_model('arcade', 'SchoolClass')
    for school_class in SchoolClass.objects.all():
        if not school_class.days_of_week:
            continue
        day_count = len([d for d in school_class.days_of_week.split(',') if d.strip()])
        if day_count:
            school_class.monthly_sessions = day_count * 4
            school_class.save(update_fields=['monthly_sessions'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('arcade', '0061_schoolclass_monthly_sessions_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_monthly_sessions, noop_reverse),
    ]
