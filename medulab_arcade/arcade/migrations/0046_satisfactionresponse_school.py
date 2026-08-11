from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arcade', '0045_satisfactionresponse_grade'),
    ]

    operations = [
        migrations.AddField(
            model_name='satisfactionresponse',
            name='respondent_school',
            field=models.CharField(blank=True, max_length=50, verbose_name='학교'),
        ),
    ]
