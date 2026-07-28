"""
자격종류 DB 정리 스크립트
- COS Entry 4/3/2/1급 → COS Entry 하나로 통합
- KAIT 코딩활용능력 3/2/1급 → KAIT 코딩활용능력 하나로 통합
- COS Pro 3/2/1급 → COS Pro 하나로 통합
- 올로AI, 엑스로보 삭제
- ITQ OA Master → category=doc_work
Usage: python scripts/fix_certinfo_groups.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medulab_arcade.settings')
import django; django.setup()
from arcade.models import CertInfo

# 1. COS Entry 통합
CertInfo.objects.filter(name__startswith='COS Entry').delete()
CertInfo.objects.update_or_create(
    name='COS Entry',
    defaults=dict(
        issuer='YBM',
        category='block_coding',
        target_grades='elem_1_2,elem_3_4,elem_5_6',
        order=10,
        description=(
            'YBM이 시행하는 Scratch·Entry 기반 블록코딩 자격시험.\n'
            '4급: 순서·반복 기초 / 초등 1~2학년 권장\n'
            '3급: 조건·신호 활용 / 초등 1~3학년 권장\n'
            '2급: Entry 심화 프로젝트 / 초등 3~4학년 권장\n'
            '1급: 고급 블록코딩 프로젝트 / 초등 4~6학년 권장'
        ),
    )
)
print("✅ COS Entry 통합 완료")

# 2. KAIT 코딩활용능력 통합
CertInfo.objects.filter(name__startswith='KAIT 코딩활용능력').delete()
CertInfo.objects.update_or_create(
    name='KAIT 코딩활용능력',
    defaults=dict(
        issuer='KAIT',
        category='block_coding',
        target_grades='elem_1_2,elem_3_4,elem_5_6,mid_high',
        order=20,
        description=(
            '한국정보통신진흥협회(KAIT)가 시행하는 코딩활용능력 자격시험.\n'
            '3급: 블록코딩 기초 / 초등 1~3학년 권장\n'
            '2급: 블록코딩 중급 / 초등 3~6학년 권장\n'
            '1급: Python 연계 텍스트코딩 / 초등 5~중학생 권장'
        ),
    )
)
print("✅ KAIT 코딩활용능력 통합 완료")

# 3. COS Pro 통합
CertInfo.objects.filter(name__startswith='COS Pro').delete()
CertInfo.objects.update_or_create(
    name='COS Pro',
    defaults=dict(
        issuer='YBM',
        category='python',
        target_grades='elem_5_6,mid_high,adult',
        order=30,
        description=(
            'YBM이 시행하는 Python·Java·C 계열 텍스트코딩 자격시험.\n'
            '3급: Python 기초 문법·알고리즘 / 초등 5~중학생 권장\n'
            '2급: 중급 알고리즘·자료구조 / 중·고등 권장\n'
            '1급: 고급 알고리즘·프로젝트 / 고등·대학 권장'
        ),
    )
)
print("✅ COS Pro 통합 완료")

# 4. 올로AI, 엑스로보 삭제
deleted, _ = CertInfo.objects.filter(name__in=['올로AI', '엑스로보']).delete()
print(f"✅ 올로AI·엑스로보 삭제 완료 ({deleted}개)")

# 5. ITQ OA Master → doc_work
updated = CertInfo.objects.filter(name__icontains='ITQ').update(category='doc_work', order=50)
print(f"✅ ITQ → 문서작업 분류 완료 ({updated}개)")

# 기존 doc_work 없으면 ITQ 직접 입력
if not CertInfo.objects.filter(name__icontains='ITQ').exists():
    CertInfo.objects.create(
        name='ITQ OA Master',
        issuer='한국생산성본부(KPC)',
        category='doc_work',
        target_grades='elem_3_4,elem_5_6',
        order=50,
        description='ITQ 시험 3과목(한글·엑셀·파워포인트) 모두 A등급 취득 시 OA Master 인증.'
    )

print("\n현재 자격종류 목록:")
for c in CertInfo.objects.all().order_by('order', 'name'):
    print(f"  [{c.category}] {c.name} | {c.target_grades}")
