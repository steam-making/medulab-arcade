from django.db import migrations, models
import django.db.models.deletion


def seed_finder_data(apps, schema_editor):
    FinderQuestion = apps.get_model('courses', 'FinderQuestion')
    FinderOption = apps.get_model('courses', 'FinderOption')
    FinderRecommendation = apps.get_model('courses', 'FinderRecommendation')

    if FinderQuestion.objects.exists():
        return

    q1 = FinderQuestion.objects.create(indicator='STEP 01', title='현재 학습 대상의 연령이나 학년은 어떻게 되나요?', order=1)
    q2 = FinderQuestion.objects.create(indicator='STEP 02', title='코딩을 배워본 경험이 있으신가요?', order=2)
    q3 = FinderQuestion.objects.create(indicator='STEP 03', title='학습을 통해 달성하고 싶은 가장 큰 목표는 무엇인가요?', order=3)

    for idx, (text, value) in enumerate([
        ('👶 유아 (5세 ~ 7세)', 'kids'),
        ('🎒 초등 저학년 (1 ~ 2학년)', 'elem_low'),
        ('🏫 초등 고학년 (3 ~ 6학년)', 'elem_high'),
        ('📖 중학생 또는 고등학생', 'secondary'),
    ], start=1):
        FinderOption.objects.create(question=q1, text=text, value=value, order=idx)

    for idx, (text, value) in enumerate([
        ('✨ 완전히 처음 입문해요', 'none'),
        ('🧩 블록 코딩(엔트리/스크래치 등) 경험이 있어요', 'block'),
        ('💻 파이썬, C언어 등 프로그래밍 언어 경험이 있어요', 'text'),
    ], start=1):
        FinderOption.objects.create(question=q2, text=text, value=value, order=idx)

    for idx, (text, value) in enumerate([
        ('🧠 사고력 향상과 컴퓨터 작동 원리 기초 이해', 'logic'),
        ('🏆 정보올림피아드 등 알고리즘 대회 출전 및 입상', 'contest'),
        ('🛠️ 실제 웹/앱 포트폴리오 제작 및 SW 자격증 취득', 'app_cert'),
    ], start=1):
        FinderOption.objects.create(question=q3, text=text, value=value, order=idx)

    rows = [
        ('스크래치', '5~7세 아이들이 놀이 형태로 코딩의 개념을 습득하고, 순차적 구조와 논리적 생각을 키우기 아주 좋은 트랙입니다.', 'kids', '', '', '스크래치', 0),
        ('엔트리 기초', '초등 저학년 눈높이에 맞춰 블록을 조립하며 애니메이션과 게임을 만들어보는 기초 코딩 입문 트랙입니다.', 'elem_low', 'none', '', '엔트리', 0),
        ('피지컬 로봇 코딩', '단순 블록 코딩을 넘어 직접 하드웨어 교구와 모터를 연결하고 조작하며 하드웨어 제어 능력을 함께 키우는 트랙입니다.', 'elem_low', 'block', '', '로봇', 1),
        ('C/C++', '알고리즘 대회 및 정보올림피아드 입상을 목적으로 C/C++ 기초 학습과 핵심적인 구조를 선행하는 고난도 트랙입니다.', 'elem_high', '', 'contest', 'C/C++', 0),
        ('COS Pro', '기본 파이썬 문법을 바탕으로 SW 사고력을 증명할 수 있는 YBM 공인 자격증(COS Pro) 취득 트랙입니다.', 'elem_high', '', 'app_cert', 'COS Pro', 1),
        ('파이썬 스타터', '초등 고학년 학생들이 처음으로 텍스트 코딩을 접할 때 거부감 없이 파이썬 언어의 기초 개념을 습득할 수 있는 입문 트랙입니다.', 'elem_high', 'none', 'logic', '파이썬', 2),
        ('파이썬 베이직', '블록 코딩 지식을 기반으로 실제 파이썬 언어의 핵심 제어문과 문법을 탄탄하게 확장해나가는 실력 향상 트랙입니다.', 'elem_high', 'block', 'logic', '파이썬', 3),
        ('올림피아드', '정보올림피아드 및 코딩테스트 통과를 위해 심화 자료구조, 수학적 논리 전개, 고난도 알고리즘 기출을 실전적으로 훈련하는 트랙입니다.', 'secondary', '', 'contest', '올림피아드', 0),
        ('정보처리기능사', '컴퓨터 전반에 걸친 이론과 프로그래밍 능력을 다지며 국가기술자격증(정보처리기능사) 취득을 단기에 공략하는 트랙입니다.', 'secondary', '', 'app_cert', '정보처리기능사', 1),
        ('파이썬', '텍스트 프로그래밍 언어의 표준인 파이썬을 학습하여 논리 구조와 데이터를 활용하는 능력을 완성하는 핵심 트랙입니다.', 'secondary', '', 'logic', '파이썬', 2),
    ]

    for title, reason, age, exp, goal, keyword, priority in rows:
        FinderRecommendation.objects.create(
            title=title,
            reason=reason,
            age=age,
            experience=exp,
            goal=goal,
            program_keyword=keyword,
            priority=priority,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0020_roadmaptrack_alter_roadmapnode_roadmap_track'),
    ]

    operations = [
        migrations.CreateModel(
            name='FinderQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('indicator', models.CharField(default='STEP 01', max_length=30, verbose_name='단계 표시')),
                ('title', models.CharField(max_length=255, verbose_name='질문')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='정렬 순서')),
                ('is_active', models.BooleanField(default=True, verbose_name='활성화 여부')),
            ],
            options={'verbose_name': '프로그램 찾기 질문', 'verbose_name_plural': '프로그램 찾기 질문 목록', 'ordering': ['order', 'id']},
        ),
        migrations.CreateModel(
            name='FinderRecommendation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=120, verbose_name='추천 제목')),
                ('reason', models.TextField(verbose_name='추천 설명')),
                ('age', models.CharField(blank=True, choices=[('', '전체'), ('kids', '유아 (5~7세)'), ('elem_low', '초등 저학년 (1~2학년)'), ('elem_high', '초등 고학년 (3~6학년)'), ('secondary', '중고등')], max_length=30, verbose_name='연령/학년 조건')),
                ('experience', models.CharField(blank=True, choices=[('', '무관'), ('none', '완전 초심자'), ('block', '블록 코딩 경험'), ('text', '텍스트 코딩 경험')], max_length=30, verbose_name='경험 조건')),
                ('goal', models.CharField(blank=True, choices=[('', '무관'), ('logic', '사고력/기초 이해'), ('contest', '대회/올림피아드'), ('app_cert', '포트폴리오/자격증')], max_length=30, verbose_name='목표 조건')),
                ('program_keyword', models.CharField(blank=True, help_text='개설 과정명에서 찾을 키워드. 비워두면 추천 제목으로 매칭합니다.', max_length=100, verbose_name='매칭 프로그램 키워드')),
                ('priority', models.PositiveIntegerField(default=0, help_text='같은 조건일 때 숫자가 낮을수록 먼저 적용됩니다.', verbose_name='우선순위')),
                ('is_active', models.BooleanField(default=True, verbose_name='활성화 여부')),
            ],
            options={'verbose_name': '프로그램 찾기 추천 규칙', 'verbose_name_plural': '프로그램 찾기 추천 규칙 목록', 'ordering': ['priority', 'id']},
        ),
        migrations.CreateModel(
            name='FinderOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=255, verbose_name='선택지 텍스트')),
                ('value', models.CharField(choices=[('kids', '유아 (5~7세)'), ('elem_low', '초등 저학년 (1~2학년)'), ('elem_high', '초등 고학년 (3~6학년)'), ('secondary', '중고등'), ('none', '완전 초심자'), ('block', '블록 코딩 경험'), ('text', '텍스트 코딩 경험'), ('logic', '사고력/기초 이해'), ('contest', '대회/올림피아드'), ('app_cert', '포트폴리오/자격증')], max_length=30, verbose_name='선택지 값')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='정렬 순서')),
                ('is_active', models.BooleanField(default=True, verbose_name='활성화 여부')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='courses.finderquestion', verbose_name='질문')),
            ],
            options={'verbose_name': '프로그램 찾기 선택지', 'verbose_name_plural': '프로그램 찾기 선택지 목록', 'ordering': ['order', 'id']},
        ),
        migrations.RunPython(seed_finder_data, migrations.RunPython.noop),
    ]
