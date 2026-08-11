from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arcade', '0046_satisfactionresponse_school'),
    ]

    operations = [
        migrations.AddField(
            model_name='satisfactionresponse',
            name='motivations',
            field=models.JSONField(default=list, verbose_name='참여 동기'),
        ),
    ]
