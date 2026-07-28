"""
6단계 로드맵 업데이트 스크립트
- 블록코딩(COS) 트랙 추가/업데이트
- 파이썬(COS Pro) 트랙 추가/업데이트
- AI(AICE) 트랙 전체 채우기
- 로봇 통합 트랙 추가/업데이트
Usage: python scripts/update_roadmap_6stage.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medulab_arcade.settings')
import django; django.setup()
from courses.models import RoadmapTrack, RoadmapNode


def upsert_track(title, badge, color, color_rgb, order):
    t, created = RoadmapTrack.objects.get_or_create(
        title=title,
        defaults=dict(badge=badge, color=color, order=order)
    )
    if not created:
        t.badge = badge; t.color = color; t.order = order
        t.save()
    print(f"{'생성' if created else '업데이트'} 트랙: [{t.id}] {t.title}")
    return t


def upsert_node(track, grade, title, subtitle, span=1, link=''):
    n, created = RoadmapNode.objects.get_or_create(
        roadmap_track=track, roadmap_grade=grade,
        defaults=dict(title=title, subtitle=subtitle, span_width=span, link_url=link)
    )
    if not created:
        n.title = title; n.subtitle = subtitle; n.span_width = span; n.link_url = link
        n.save()
    print(f"  {'생성' if created else '업데이트'} [{grade}]: {title} / {subtitle[:40]}")


# ──────────────────────────────────────────────────────────────
# 1. 블록코딩 트랙 (COS Entry + KAIT)
# ──────────────────────────────────────────────────────────────
t_block = upsert_track(
    title='블록코딩·COS',
    badge='BLOCK CODING',
    color='#f97316',
    color_rgb='249, 115, 22',
    order=10,
)
upsert_node(t_block, 'kids_5_7', '코딩 체험',        'Code.org 기초 / 언플러그드 코딩')
upsert_node(t_block, 'elem_1_2', 'COS Entry 4·3급',  'Entry 기초 / 순차·반복·조건')
upsert_node(t_block, 'elem_3_4', 'COS Entry 2·1급',  'Entry 심화 / KAIT 3·2급 / 프로젝트')
upsert_node(t_block, 'elem_5_6', 'KAIT 1급 준비',    'KAIT 코딩활용능력 1급 / Python 전환')
upsert_node(t_block, 'mid_high', 'Python 심화',       'COS Pro 2·1급 / 알고리즘 문제풀이')
upsert_node(t_block, 'adult',    'AI 개발',            'Python 전문 / NumPy·Pandas / 데이터')


# ──────────────────────────────────────────────────────────────
# 2. 파이썬·COS Pro 트랙
# ──────────────────────────────────────────────────────────────
t_python = upsert_track(
    title='파이썬·COS Pro',
    badge='PYTHON',
    color='#3b82f6',
    color_rgb='59, 130, 246',
    order=11,
)
upsert_node(t_python, 'kids_5_7', '-',               '해당 없음')
upsert_node(t_python, 'elem_1_2', '-',               '해당 없음')
upsert_node(t_python, 'elem_3_4', 'Python 맛보기',  '기초 문법 / 변수·조건·반복')
upsert_node(t_python, 'elem_5_6', 'COS Pro 3급',    'Python 문법 / 함수·리스트 / 자격 도전')
upsert_node(t_python, 'mid_high', 'COS Pro 2·1급',  '알고리즘 / 객체지향 / API / 프로젝트')
upsert_node(t_python, 'adult',    'AI·데이터 개발', 'ML 기초 / 업무자동화 / 웹·앱 연동')


# ──────────────────────────────────────────────────────────────
# 3. AI·AICE 트랙 (기존 id=3 업데이트)
# ──────────────────────────────────────────────────────────────
try:
    t_ai = RoadmapTrack.objects.get(id=3)
    t_ai.title = 'AI·AICE'; t_ai.badge = 'AI'; t_ai.color = '#a855f7'
    t_ai.order = 12; t_ai.save()
    print(f"업데이트 트랙: [3] AI·AICE")
except RoadmapTrack.DoesNotExist:
    t_ai = upsert_track('AI·AICE', 'AI', '#a855f7', '168, 85, 247', 12)

upsert_node(t_ai, 'kids_5_7', 'AI 체험',            '생활속 AI / 음성·이미지 인식 놀이')
upsert_node(t_ai, 'elem_1_2', 'AI 입문',             'Entry AI 블록 / AICE Future 입문')
upsert_node(t_ai, 'elem_3_4', 'AICE Future',         'AICE Future 3·2·1급 / 데이터 분류')
upsert_node(t_ai, 'elem_5_6', 'AICE Junior',         '노코딩 데이터분석 / 생성형 AI 기초')
upsert_node(t_ai, 'mid_high', 'AICE Basic·Generative','AI 분석 / 생성형 AI 2·1급 / 프로젝트')
upsert_node(t_ai, 'adult',    'AICE Associate',       '국가공인 AI 자격 / AI 개발·포트폴리오')


# ──────────────────────────────────────────────────────────────
# 4. 로봇 통합 트랙 (새 트랙)
# ──────────────────────────────────────────────────────────────
t_robot = upsert_track(
    title='로봇 통합',
    badge='ROBOT',
    color='#f59e0b',
    color_rgb='245, 158, 11',
    order=13,
)
upsert_node(t_robot, 'kids_5_7', '레고형 기초',       '로봇 조립 놀이 / 프로보 입문')
upsert_node(t_robot, 'elem_1_2', '프로보 커넥트',     '모터·센서 기초 / 미션 제작')
upsert_node(t_robot, 'elem_3_4', '프로보→올로AI',     '프로보 심화 / 올로AI 입문 / 라인트레이싱')
upsert_node(t_robot, 'elem_5_6', '올로AI·엑스로보',   '센서 제어 / 장애물감지 / 엑스로보 입문')
upsert_node(t_robot, 'mid_high', 'AI 로봇',            '엑스로보 심화 / AI 비전 / 자율주행')
upsert_node(t_robot, 'adult',    'Python 로봇제어',    '자율주행·스마트팩토리 / IoT 융합')


# ──────────────────────────────────────────────────────────────
# 5. 타자 트랙 adult 노드 추가 (기존 id=7)
# ──────────────────────────────────────────────────────────────
try:
    t_typing = RoadmapTrack.objects.get(id=7)
    upsert_node(t_typing, 'adult', '목표타자', '단어 500타 / 짧은글 450타 / 긴글 400타')
except RoadmapTrack.DoesNotExist:
    print("타자 트랙(id=7)을 찾을 수 없습니다.")

print("\n✅ 로드맵 6단계 업데이트 완료!")
print("\n최종 트랙 목록:")
for t in RoadmapTrack.objects.all().order_by('order', 'id'):
    nodes = RoadmapNode.objects.filter(roadmap_track=t).count()
    print(f"  [{t.id}] {t.title} ({nodes}개 노드)")
