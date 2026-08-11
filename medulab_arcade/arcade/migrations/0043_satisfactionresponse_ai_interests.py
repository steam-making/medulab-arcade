from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arcade', '0042_satisfaction_survey'),
    ]

    operations = [
        migrations.AddField(
            model_name='satisfactionresponse',
            name='ai_interests',
            field=models.JSONField(default=list, verbose_name='배우고 싶은 AI 분야'),
        ),
    ]
