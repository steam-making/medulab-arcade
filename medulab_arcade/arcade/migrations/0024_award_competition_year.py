from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arcade', '0023_award_division'),
    ]

    operations = [
        migrations.AddField(
            model_name='award',
            name='competition_year',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='대회년도'),
        ),
    ]
