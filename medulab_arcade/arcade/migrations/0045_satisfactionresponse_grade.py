from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arcade', '0044_satisfactionsurvey_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='satisfactionresponse',
            name='respondent_grade',
            field=models.CharField(blank=True, max_length=20, verbose_name='학년'),
        ),
    ]
