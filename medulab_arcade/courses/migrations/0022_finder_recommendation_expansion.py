from django.db import migrations


def seed_more_finder_rules(apps, schema_editor):
    FinderRecommendation = apps.get_model('courses', 'FinderRecommendation')

    rows = [
        {
            'title': '피지컬 로봇 코딩',
            'reason': '유아 단계에서 블록 코딩 경험이 있다면 로봇 교구와 센서를 활용해 손으로 만지고 움직이며 코딩 개념을 확장하기 좋은 트랙입니다.',
            'age': 'kids',
            'experience': 'block',
            'goal': 'logic',
            'program_keyword': '로봇',
            'priority': 1,
        },
        {
            'title': '엔트리 심화',
            'reason': '초등 저학년이 이미 블록 코딩 경험이 있다면 반복·조건·이벤트를 더 깊게 다루며 작품 완성도를 높이는 심화 트랙이 적합합니다.',
            'age': 'elem_low',
            'experience': 'block',
            'goal': 'logic',
            'program_keyword': '엔트리',
            'priority': 2,
        },
        {
            'title': '파이썬 베이직',
            'reason': '초등 저학년이 텍스트 코딩 경험을 갖고 있다면 기초 문법을 안정적으로 정리하면서 프로젝트 감각까지 키우는 과정이 잘 맞습니다.',
            'age': 'elem_low',
            'experience': 'text',
            'goal': 'logic',
            'program_keyword': '파이썬',
            'priority': 3,
        },
        {
            'title': '올림피아드 베이직',
            'reason': '초등 고학년이 이미 텍스트 코딩 경험이 있다면 자료구조와 문제 해결 패턴을 체계적으로 익히는 알고리즘 입문 트랙이 효과적입니다.',
            'age': 'elem_high',
            'experience': 'text',
            'goal': 'contest',
            'program_keyword': '올림피아드',
            'priority': 0,
        },
        {
            'title': 'COS Pro 실전',
            'reason': '초등 고학년이 텍스트 코딩 경험을 바탕으로 자격증까지 목표한다면 실전 문제 풀이 중심의 자격증 대비 트랙이 적합합니다.',
            'age': 'elem_high',
            'experience': 'text',
            'goal': 'app_cert',
            'program_keyword': 'COS Pro',
            'priority': 1,
        },
        {
            'title': '파이썬 프로젝트',
            'reason': '초등 고학년이 텍스트 코딩 경험을 가지고 있다면 간단한 게임·자동화 결과물을 직접 만들며 실전 감각을 키우는 방향이 좋습니다.',
            'age': 'elem_high',
            'experience': 'text',
            'goal': 'logic',
            'program_keyword': '파이썬',
            'priority': 2,
        },
        {
            'title': '파이썬 입문',
            'reason': '중고등 학생이 처음 시작한다면 문법 이해와 문제 해결 감각을 동시에 잡을 수 있는 파이썬 입문 과정이 가장 안정적입니다.',
            'age': 'secondary',
            'experience': 'none',
            'goal': 'logic',
            'program_keyword': '파이썬',
            'priority': 0,
        },
        {
            'title': '파이썬 베이직',
            'reason': '중고등 학생이 블록 코딩 경험이 있다면 텍스트 코딩으로 자연스럽게 넘어가며 문법과 로직을 연결하는 과정이 잘 맞습니다.',
            'age': 'secondary',
            'experience': 'block',
            'goal': 'logic',
            'program_keyword': '파이썬',
            'priority': 1,
        },
        {
            'title': '파이썬 실전',
            'reason': '중고등 학생이 텍스트 코딩 경험이 있다면 함수·파일처리·자료구조를 활용해 실전 문제를 다루는 심화형 트랙이 적합합니다.',
            'age': 'secondary',
            'experience': 'text',
            'goal': 'logic',
            'program_keyword': '파이썬',
            'priority': 2,
        },
        {
            'title': '알고리즘 입문',
            'reason': '중고등 학생이 처음 대회를 준비한다면 문법보다 문제 해결 구조를 먼저 잡아주는 알고리즘 입문 트랙이 효율적입니다.',
            'age': 'secondary',
            'experience': 'none',
            'goal': 'contest',
            'program_keyword': '알고리즘',
            'priority': 0,
        },
        {
            'title': '알고리즘 베이직',
            'reason': '중고등 학생이 블록 코딩 경험이 있다면 조건문·반복문에서 한 단계 나아가 알고리즘 기본기를 체계적으로 다지는 것이 좋습니다.',
            'age': 'secondary',
            'experience': 'block',
            'goal': 'contest',
            'program_keyword': '알고리즘',
            'priority': 1,
        },
        {
            'title': '올림피아드 심화',
            'reason': '중고등 학생이 이미 텍스트 코딩 경험이 있다면 실전 기출과 고난도 로직 훈련 중심의 심화 트랙이 가장 적합합니다.',
            'age': 'secondary',
            'experience': 'text',
            'goal': 'contest',
            'program_keyword': '올림피아드',
            'priority': 2,
        },
        {
            'title': '정보처리기능사',
            'reason': '중고등 학생이 처음 자격증을 준비한다면 기초 이론과 실습을 함께 익히는 국가자격 대비 과정이 안정적인 선택입니다.',
            'age': 'secondary',
            'experience': 'none',
            'goal': 'app_cert',
            'program_keyword': '정보처리기능사',
            'priority': 0,
        },
        {
            'title': 'COS Pro',
            'reason': '중고등 학생이 블록 코딩 경험이 있다면 비교적 빠르게 실습형 자격증에 도전할 수 있는 코스로 연결하는 것이 좋습니다.',
            'age': 'secondary',
            'experience': 'block',
            'goal': 'app_cert',
            'program_keyword': 'COS Pro',
            'priority': 1,
        },
        {
            'title': '웹/앱 포트폴리오',
            'reason': '중고등 학생이 텍스트 코딩 경험을 갖고 있다면 실제 결과물을 만들며 포트폴리오와 실무 감각을 함께 쌓는 트랙이 효과적입니다.',
            'age': 'secondary',
            'experience': 'text',
            'goal': 'app_cert',
            'program_keyword': '웹',
            'priority': 2,
        },
    ]

    for row in rows:
        FinderRecommendation.objects.update_or_create(
            title=row['title'],
            age=row['age'],
            experience=row['experience'],
            goal=row['goal'],
            defaults={
                'reason': row['reason'],
                'program_keyword': row['program_keyword'],
                'priority': row['priority'],
                'is_active': True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0021_finder_models'),
    ]

    operations = [
        migrations.RunPython(seed_more_finder_rules, migrations.RunPython.noop),
    ]
