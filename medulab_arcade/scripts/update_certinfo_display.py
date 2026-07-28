"""
CertInfo display_name, grade_info 업데이트 + AICE Generative 추가
Usage: python scripts/update_certinfo_display.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medulab_arcade.settings')
import django; django.setup()
from arcade.models import CertInfo

DATA = [
    {
        'name': 'COS Entry',
        'display_name': 'COS Entry 1~4급',
        'grade_info': [
            {'grade': '4급', 'content': 'Scratch·Entry 기초 / 순서·반복 구조', 'target': '초등 1~2학년'},
            {'grade': '3급', 'content': 'Entry 조건·신호 활용 / 기초 프로젝트', 'target': '초등 1~3학년'},
            {'grade': '2급', 'content': 'Entry 심화 / 함수·리스트 활용 프로젝트', 'target': '초등 3~4학년'},
            {'grade': '1급', 'content': '고급 블록코딩 프로젝트 / 복합 알고리즘', 'target': '초등 4~6학년'},
        ],
    },
    {
        'name': 'KAIT 코딩활용능력',
        'display_name': 'KAIT 코딩활용능력 1~3급',
        'grade_info': [
            {'grade': '3급', 'content': '블록코딩 기초 / 순서·반복·조건 구조', 'target': '초등 1~3학년'},
            {'grade': '2급', 'content': '블록코딩 중급 / 함수·리스트 활용', 'target': '초등 3~6학년'},
            {'grade': '1급', 'content': 'Python 연계 텍스트코딩 / 알고리즘 기초', 'target': '초등 5학년~중학생'},
        ],
    },
    {
        'name': 'COS Pro',
        'display_name': 'COS Pro 1~3급',
        'grade_info': [
            {'grade': '3급', 'content': 'Python 기초 문법 / 조건·반복·함수 / 알고리즘 입문', 'target': '초등 5학년~중학생'},
            {'grade': '2급', 'content': '중급 알고리즘 / 자료구조 / 객체지향 기초', 'target': '중·고등'},
            {'grade': '1급', 'content': '고급 알고리즘 / 자료구조 심화 / 프로젝트', 'target': '고등·대학'},
        ],
    },
    {
        'name': 'AICE Future',
        'display_name': 'AICE Future 1~3급',
        'grade_info': [
            {'grade': '3급', 'content': 'AI 기초 개념 / 데이터 분류 입문 / 노코딩 AI 체험', 'target': '초등 3~4학년'},
            {'grade': '2급', 'content': '데이터 분석·분류 중급 / 간단한 모델 실습', 'target': '초등 4~6학년'},
            {'grade': '1급', 'content': 'AI 모델 설계 기초 / 데이터 전처리 / 결과 해석', 'target': '초등 5~6학년'},
        ],
    },
    {
        'name': 'ITQ',
        'display_name': 'ITQ 파워포인트/한글/엑셀',
        'grade_info': [
            {'grade': '파워포인트', 'content': '프레젠테이션 슬라이드 제작 / 디자인·애니메이션 활용', 'target': '초등 3~6학년'},
            {'grade': '한글', 'content': '문서 편집·서식·표 작성 / 보고서 제작', 'target': '초등 3~6학년'},
            {'grade': '엑셀', 'content': '수식·함수 / 차트·데이터 정리', 'target': '초등 3~6학년'},
            {'grade': 'OA Master', 'content': '3과목(파워포인트·한글·엑셀) 모두 A등급 취득 시 인증', 'target': '초등 5학년~중학생'},
        ],
    },
    {
        'name': 'AICE Junior',
        'display_name': 'AICE Junior',
        'grade_info': [
            {'grade': 'Junior', 'content': '노코딩 데이터 분석 / 생성형 AI 기초 / AI 프로젝트 실습', 'target': '초등 5~6학년·중학생'},
        ],
    },
    {
        'name': 'AICE Basic',
        'display_name': 'AICE Basic',
        'grade_info': [
            {'grade': 'Basic', 'content': 'Python 기반 AI 분석 / 머신러닝 기초 / 데이터 시각화', 'target': '중·고등'},
        ],
    },
    {
        'name': 'AICE Associate',
        'display_name': 'AICE Associate',
        'grade_info': [
            {'grade': 'Associate', 'content': '국가공인 AI 자격 / 머신러닝·딥러닝 / AI 프로젝트 포트폴리오', 'target': '대학·일반'},
        ],
    },
]

for d in DATA:
    try:
        ci = CertInfo.objects.get(name=d['name'])
        ci.display_name = d['display_name']
        ci.grade_info = d['grade_info']
        ci.save()
        print(f"✅ 업데이트: {ci.name} → {ci.display_name}")
    except CertInfo.DoesNotExist:
        print(f"⚠️  없음: {d['name']}")

# AICE Generative 추가/업데이트
ci_gen, created = CertInfo.objects.update_or_create(
    name='AICE Generative',
    defaults=dict(
        display_name='AICE Generative 1~2급',
        issuer='KT·한국경제신문',
        category='ai',
        target_grades='mid_high,adult',
        order=35,
        description=(
            'KT와 한국경제신문이 공동 주관하는 생성형 AI 활용 자격시험.\n'
            '생성형 AI 도구(ChatGPT, Copilot 등)의 원리와 실무 활용을 평가합니다.'
        ),
        grade_info=[
            {'grade': '2급', 'content': '생성형 AI 개념 / 프롬프트 기초 / AI 도구 활용 실습', 'target': '중·고등'},
            {'grade': '1급', 'content': '고급 프롬프트 엔지니어링 / AI 결과 검증·활용 프로젝트', 'target': '고등·대학'},
        ],
    )
)
print(f"{'✅ 생성' if created else '✅ 업데이트'}: AICE Generative")

print("\n📋 최종 CertInfo 목록:")
for c in CertInfo.objects.all().order_by('order', 'name'):
    print(f"  [{c.category}] {c.name} | 표시명: {c.display_name or '(없음)'} | 등급표: {len(c.grade_info or [])}행")
