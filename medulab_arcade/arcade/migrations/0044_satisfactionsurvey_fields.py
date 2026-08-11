from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arcade', '0043_satisfactionresponse_ai_interests'),
    ]

    operations = [
        migrations.AddField(
            model_name='satisfactionsurvey',
            name='active_date',
            field=models.DateField(blank=True, null=True, verbose_name='수업 날짜'),
        ),
        migrations.AddField(
            model_name='satisfactionsurvey',
            name='expected_count',
            field=models.IntegerField(default=0, verbose_name='예상 참여 인원'),
        ),
        migrations.AddField(
            model_name='satisfactionsurvey',
            name='sessions_data',
            field=models.JSONField(default=list, verbose_name='차시 목록'),
        ),
    ]
