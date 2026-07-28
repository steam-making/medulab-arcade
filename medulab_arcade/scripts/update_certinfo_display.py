"""
CertInfo 전체 동기화 스크립트 (없으면 생성, 있으면 업데이트)
Usage: python scripts/update_certinfo_display.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medulab_arcade.settings')
import django; django.setup()
from arcade.models import CertInfo

DATA = [
    {
        'name': 'AICE Associate',
        'display_name': 'AICE Associate',
        'issuer': 'KT·한국경제신문',
        'category': 'ai',
        'target_grades': 'adult',
        'order': 10,
        'is_national_cert': True,
        'description': (
            'KT·한국경제신문 공동 주관의 국가공인 AI 자격시험.\n'
            'Python 기반 머신러닝·딥러닝 실무 능력을 평가합니다.\n'
            '대학생·취업 준비생·직장인에게 추천합니다.'
        ),
        'grade_info': [
            {'grade': 'Associate', 'content': '국가공인 AI 자격 / 머신러닝·딥러닝 / AI 프로젝트 포트폴리오', 'target': '대학·일반'},
        ],
    },
    {
        'name': 'AICE Generative',
        'display_name': 'AICE Generative 1~2급',
        'issuer': 'KT·한국경제신문',
        'category': 'ai',
        'target_grades': 'mid_high,adult',
        'order': 20,
        'is_national_cert': False,
        'description': (
            'KT와 한국경제신문이 공동 주관하는 생성형 AI 활용 자격시험.\n'
            '생성형 AI 도구(ChatGPT, Copilot 등)의 원리와 실무 활용을 평가합니다.'
        ),
        'grade_info': [
            {'grade': '2급', 'content': '생성형 AI 개념 / 프롬프트 기초 / AI 도구 활용 실습', 'target': '중·고등'},
            {'grade': '1급', 'content': '고급 프롬프트 엔지니어링 / AI 결과 검증·활용 프로젝트', 'target': '고등·대학'},
        ],
    },
    {
        'name': 'AICE Basic',
        'display_name': 'AICE Basic',
        'issuer': 'KT·한국경제신문',
        'category': 'ai',
        'target_grades': 'mid_high',
        'order': 30,
        'is_national_cert': False,
        'description': (
            'Python 기반 AI 분석 입문 자격시험.\n'
            '머신러닝 기초 개념과 데이터 시각화를 실습 중심으로 평가합니다.'
        ),
        'grade_info': [
            {'grade': 'Basic', 'content': 'Python 기반 AI 분석 / 머신러닝 기초 / 데이터 시각화', 'target': '중·고등'},
        ],
    },
    {
        'name': 'AICE Junior',
        'display_name': 'AICE Junior',
        'issuer': 'KT·한국경제신문',
        'category': 'ai',
        'target_grades': 'elem_5_6,mid_high',
        'order': 40,
        'is_national_cert': False,
        'description': (
            '초등 고학년~중학생을 위한 AI 입문 자격시험.\n'
            '노코딩 데이터 분석과 생성형 AI 기초를 체험합니다.'
        ),
        'grade_info': [
            {'grade': 'Junior', 'content': '노코딩 데이터 분석 / 생성형 AI 기초 / AI 프로젝트 실습', 'target': '초등 5~6학년·중학생'},
        ],
    },
    {
        'name': 'AICE Future',
        'display_name': 'AICE Future 1~3급',
        'issuer': 'KT·한국경제신문',
        'category': 'ai',
        'target_grades': 'elem_3_4,elem_5_6',
        'order': 50,
        'is_national_cert': False,
        'description': (
            '초등학생을 위한 AI 체험·입문 자격시험.\n'
            '노코딩 AI 도구로 데이터를 분류하고 간단한 AI 모델을 체험합니다.'
        ),
        'grade_info': [
            {'grade': '3급', 'content': 'AI 기초 개념 / 데이터 분류 입문 / 노코딩 AI 체험', 'target': '초등 3~4학년'},
            {'grade': '2급', 'content': '데이터 분석·분류 중급 / 간단한 모델 실습', 'target': '초등 4~6학년'},
            {'grade': '1급', 'content': 'AI 모델 설계 기초 / 데이터 전처리 / 결과 해석', 'target': '초등 5~6학년'},
        ],
    },
    {
        'name': 'COS Entry',
        'display_name': 'COS Entry 1~4급',
        'issuer': '한국생산성본부(KPC)',
        'category': 'block_coding',
        'target_grades': 'elem_1_2,elem_3_4,elem_5_6',
        'order': 60,
        'is_national_cert': False,
        'description': (
            '한국생산성본부(KPC)에서 시행하는 블록코딩 자격시험.\n'
            'Scratch·Entry로 순서·반복·조건 등 프로그래밍 기초를 평가합니다.'
        ),
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
        'issuer': 'KAIT(한국정보통신진흥협회)',
        'category': 'block_coding,python',
        'target_grades': 'elem_1_2,elem_3_4,elem_5_6,mid_high',
        'order': 70,
        'is_national_cert': False,
        'description': (
            'KAIT(한국정보통신진흥협회)에서 시행하는 코딩 자격시험.\n'
            '블록코딩에서 Python 텍스트코딩까지 단계별로 평가합니다.'
        ),
        'grade_info': [
            {'grade': '3급', 'content': '블록코딩 기초 / 순서·반복·조건 구조', 'target': '초등 1~3학년'},
            {'grade': '2급', 'content': '블록코딩 중급 / 함수·리스트 활용', 'target': '초등 3~6학년'},
            {'grade': '1급', 'content': 'Python 연계 텍스트코딩 / 알고리즘 기초', 'target': '초등 5학년~중학생'},
        ],
    },
    {
        'name': 'COS Pro',
        'display_name': 'COS Pro 1~3급',
        'issuer': '한국생산성본부(KPC)',
        'category': 'python',
        'target_grades': 'elem_5_6,mid_high,adult',
        'order': 80,
        'is_national_cert': False,
        'description': (
            '한국생산성본부(KPC)에서 시행하는 Python 코딩 자격시험.\n'
            '알고리즘·자료구조 중심의 실력을 단계별로 평가합니다.'
        ),
        'grade_info': [
            {'grade': '3급', 'content': 'Python 기초 문법 / 조건·반복·함수 / 알고리즘 입문', 'target': '초등 5학년~중학생'},
            {'grade': '2급', 'content': '중급 알고리즘 / 자료구조 / 객체지향 기초', 'target': '중·고등'},
            {'grade': '1급', 'content': '고급 알고리즘 / 자료구조 심화 / 프로젝트', 'target': '고등·대학'},
        ],
    },
    {
        'name': 'ITQ',
        'display_name': 'ITQ 파워포인트/한글/엑셀',
        'issuer': '한국생산성본부(KPC)',
        'category': 'doc_work',
        'target_grades': 'elem_3_4,elem_5_6,mid_high',
        'order': 90,
        'is_national_cert': True,
        'description': (
            '한국생산성본부(KPC)에서 시행하는 국가공인 정보기술자격시험.\n'
            '파워포인트·한글·엑셀 등 OA 소프트웨어 실무 능력을 평가합니다.\n'
            '3과목 모두 A등급 취득 시 OA Master 인증을 받을 수 있습니다.'
        ),
        'grade_info': [
            {'grade': '파워포인트', 'content': '프레젠테이션 슬라이드 제작 / 디자인·애니메이션 활용', 'target': '초등 3~6학년'},
            {'grade': '한글', 'content': '문서 편집·서식·표 작성 / 보고서 제작', 'target': '초등 3~6학년'},
            {'grade': '엑셀', 'content': '수식·함수 / 차트·데이터 정리', 'target': '초등 3~6학년'},
            {'grade': 'OA Master', 'content': '3과목(파워포인트·한글·엑셀) 모두 A등급 취득 시 인증', 'target': '초등 5학년~중학생'},
        ],
    },
]

print("🔄 CertInfo 동기화 시작...\n")

for d in DATA:
    obj, created = CertInfo.objects.update_or_create(
        name=d['name'],
        defaults={
            'display_name': d['display_name'],
            'issuer': d.get('issuer', ''),
            'category': d.get('category', ''),
            'target_grades': d.get('target_grades', ''),
            'order': d.get('order', 0),
            'is_national_cert': d.get('is_national_cert', False),
            'description': d.get('description', ''),
            'grade_info': d['grade_info'],
        }
    )
    status = '✅ 생성' if created else '🔁 업데이트'
    print(f"{status}: {obj.name} → {obj.display_name}")

print("\n📋 최종 CertInfo 목록:")
for c in CertInfo.objects.all().order_by('order', 'name'):
    print(f"  [{c.category or 'None'}] {c.name} | 표시명: {c.display_name or '(없음)'} | 등급표: {len(c.grade_info or [])}행")
