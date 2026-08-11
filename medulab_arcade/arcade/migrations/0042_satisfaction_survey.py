from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('arcade', '0041_gallery_room_timer'),
    ]

    operations = [
        migrations.CreateModel(
            name='SatisfactionSurvey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='제목')),
                ('slug', models.SlugField(max_length=100, unique=True, verbose_name='슬러그')),
                ('is_active', models.BooleanField(default=True, verbose_name='활성')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': '만족도 조사',
                'verbose_name_plural': '만족도 조사',
                'db_table': 'satisfaction_survey',
            },
        ),
        migrations.CreateModel(
            name='SatisfactionResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('respondent_name', models.CharField(max_length=30, verbose_name='이름')),
                ('session_key', models.CharField(max_length=100, verbose_name='세션키')),
                ('overall_score', models.IntegerField(verbose_name='전체 만족도')),
                ('session_scores', models.JSONField(default=dict, verbose_name='차시별 만족도')),
                ('favorite_sessions', models.JSONField(default=list, verbose_name='재미있었던 차시')),
                ('hardest_sessions', models.JSONField(default=list, verbose_name='어려웠던 차시')),
                ('attend_again', models.CharField(blank=True, max_length=60, verbose_name='재참여 의향')),
                ('recommend', models.CharField(blank=True, max_length=60, verbose_name='추천 의향')),
                ('good_points', models.TextField(blank=True, verbose_name='좋았던 점')),
                ('bad_points', models.TextField(blank=True, verbose_name='아쉬웠던 점')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('survey', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='arcade.satisfactionsurvey')),
            ],
            options={
                'verbose_name': '만족도 응답',
                'verbose_name_plural': '만족도 응답',
                'db_table': 'satisfaction_response',
                'unique_together': {('survey', 'session_key')},
            },
        ),
    ]
