"""
CertInfo 자격증 데이터 초기 설정 스크립트
Usage: python scripts/setup_certinfo.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medulab_arcade.settings')
import django; django.setup()
from arcade.models import CertInfo

CERTS = [
    # 블록코딩
    dict(name='COS Entry 4급', issuer='YBM', category='block_coding', target_grades='elem_1_2', order=10,
         description='Scratch/Entry 기반 블록코딩 기초 능력 평가 (YBM 시행)'),
    dict(name='COS Entry 3급', issuer='YBM', category='block_coding', target_grades='elem_1_2,elem_3_4', order=11,
         description='Scratch/Entry 기반 블록코딩 중급 능력 평가 (YBM 시행)'),
    dict(name='COS Entry 2급', issuer='YBM', category='block_coding', target_grades='elem_3_4', order=12,
         description='Entry 심화 블록코딩 프로젝트 능력 평가 (YBM 시행)'),
    dict(name='COS Entry 1급', issuer='YBM', category='block_coding', target_grades='elem_3_4,elem_5_6', order=13,
         description='Entry 고급 블록코딩 프로젝트 능력 평가 (YBM 시행)'),
    dict(name='KAIT 코딩활용능력 3급', issuer='KAIT', category='block_coding', target_grades='elem_1_2,elem_3_4', order=20,
         description='블록코딩 기초 능력 평가 (한국정보통신진흥협회 시행)'),
    dict(name='KAIT 코딩활용능력 2급', issuer='KAIT', category='block_coding', target_grades='elem_3_4,elem_5_6', order=21,
         description='블록코딩 중급 능력 평가 (한국정보통신진흥협회 시행)'),

    # 파이썬코딩
    dict(name='KAIT 코딩활용능력 1급', issuer='KAIT', category='python', target_grades='elem_5_6,mid_high', order=22,
         description='Python 연계 텍스트코딩 능력 평가 (한국정보통신진흥협회 시행)'),
    dict(name='COS Pro 3급', issuer='YBM', category='python', target_grades='elem_5_6,mid_high', order=30,
         description='Python/Java/C 텍스트코딩 논리적 사고 평가 3급 (YBM 시행)'),
    dict(name='COS Pro 2급', issuer='YBM', category='python', target_grades='mid_high', order=31,
         description='Python/Java/C 텍스트코딩 논리적 사고 평가 2급 (YBM 시행)'),
    dict(name='COS Pro 1급', issuer='YBM', category='python', target_grades='mid_high,adult', order=32,
         description='Python/Java/C 텍스트코딩 논리적 사고 평가 1급 (YBM 시행)'),

    # AI
    dict(name='AICE Future 3급', issuer='KT·한국경제신문', category='ai', target_grades='elem_3_4', order=40,
         description='AI 기초 체험 및 데이터 분류 이해 (KT·한국경제신문 시행)'),
    dict(name='AICE Future 2급', issuer='KT·한국경제신문', category='ai', target_grades='elem_3_4,elem_5_6', order=41,
         description='AI 활용 기초 능력 평가 (KT·한국경제신문 시행)'),
    dict(name='AICE Future 1급', issuer='KT·한국경제신문', category='ai', target_grades='elem_5_6', order=42,
         description='AI 활용 중급 능력 평가 (KT·한국경제신문 시행)'),
    dict(name='AICE Junior', issuer='KT·한국경제신문', category='ai', target_grades='elem_5_6,mid_high', order=43,
         description='노코딩 데이터 분석, 생성형 AI 활용 기초 (KT·한국경제신문 시행)'),
    dict(name='AICE Basic', issuer='KT·한국경제신문', category='ai', target_grades='mid_high', order=44,
         description='AI 데이터 분석 및 모델 기초 능력 평가 (KT·한국경제신문 시행)'),
    dict(name='AICE Generative 2급', issuer='KT·한국경제신문', category='ai', target_grades='mid_high', order=45,
         description='생성형 AI 활용 능력 평가 2급 (KT·한국경제신문 시행)'),
    dict(name='AICE Generative 1급', issuer='KT·한국경제신문', category='ai', target_grades='mid_high,adult', order=46,
         description='생성형 AI 활용 능력 평가 1급 (KT·한국경제신문 시행)'),
    dict(name='AICE Associate', issuer='KT·한국경제신문', category='ai', target_grades='adult', order=47,
         description='국가공인 AI 역량 자격증. AI 분석·개발 실무 능력 평가 (KT·한국경제신문 시행)'),

    # 로봇
    dict(name='프로보 커넥트', issuer='프로보', category='robot', target_grades='elem_1_2,elem_3_4', order=60,
         description='조립식 교육용 로봇 프로보 커넥트 단계별 과정. 모터·센서 기초 학습'),
    dict(name='올로AI', issuer='로보티즈', category='robot', target_grades='elem_3_4,elem_5_6,mid_high', order=61,
         description='로보티즈 올로AI 로봇 과정. 센서 기반 제어 및 AI 연동'),
    dict(name='엑스로보', issuer='엑스로보', category='robot', target_grades='elem_5_6,mid_high,adult', order=62,
         description='다이나믹셀 기반 고급 로봇 제어. 자율주행·AI 비전 연동'),
]

created = updated = 0
for data in CERTS:
    obj, is_new = CertInfo.objects.get_or_create(name=data['name'], defaults=data)
    if not is_new:
        for k, v in data.items():
            setattr(obj, k, v)
        obj.save()
        updated += 1
    else:
        created += 1
    print(f"{'생성' if is_new else '업데이트'}: [{obj.category}] {obj.name} → {obj.target_grades}")

print(f"\n완료: 생성 {created}개, 업데이트 {updated}개")
