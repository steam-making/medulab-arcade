import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gpt_eval_site.settings")

import django

django.setup()

from courses.models import Chapter, Item, LearningProgram, ProgramType

PROGRAM_NAME = "로봇코딩과정 프로보 커넥트"
PROGRAM_DESCRIPTION = "프로보 커넥트 로봇을 활용해 조립, 센서, 모터, 제어 원리와 게임형 미션을 단계적으로 익히는 로봇코딩 과정입니다. LV1부터 LV6까지 전체 커리큘럼을 반영했습니다."

LEVEL_DESCRIPTIONS = {
    1: "로봇의 기초와 구조를 이해하고, 재미있는 이론과 3D 조립도를 바탕으로 생체모방 로봇을 직접 만들며 친근하게 배워가는 단계",
    2: "제작한 게임 로봇으로 친구들과 시합하며 경쟁심과 협동심을 함께 배워가고, 만든 로봇의 알고리즘과 CPU, IR, LED, FND 등에 대해 이해해나가는 단계",
    3: "서보모터와 RF리모컨의 활용으로 주변에서 볼 수 있는 자동차나 중장비 등을 로봇으로 만들어보고 원리를 이해하는 단계",
    4: "캐터필러와 고속모터의 다양한 활용으로 독특하고 속도감 있는 로봇의 움직임을 구현하며 실생활 로봇과 유사하게 만들고 복잡한 링크구조를 이해해 나가는 단계",
    5: "게임형 로봇을 중심으로 규칙 변경, 점수 기록, 반응 속도 훈련을 하며 창의적 응용과 놀이형 알고리즘 구성을 익히는 단계",
    6: "센서와 다양한 게임 미션을 결합해 팀 활동, 전략, 대회 운영까지 경험하며 프로보 커넥트의 심화 활용을 완성하는 단계",
}

LEVEL_ITEMS = {
    1: [
        "아기돼지도니", "아기새로봇버디", "물개로봇토토", "토끼로봇로빗", "원숭이로봇우키", "개구리로봇크록",
        "강아지로봇몽이", "배틀로봇어퍼", "보행로봇 워로우", "땅굴로봇터보", "거미로봇타란튤", "공룡로봇티라",
    ],
    2: [
        "기억력게임탭탭", "접시쌓기게임웨이터리", "CPR실습로봇피아르", "비행기게임점핑에어", "가위바위보위너", "팔씨름게임쉐이크스틱",
        "외계인사격레이저건", "하마게임하몽", "역도게임라차차", "스피드터치해머샷", "테이블농구슈터", "나만의 창작로봇",
    ],
    3: [
        "개미로봇앤보", "청소로봇워시", "경찰바이크싸이카", "투석기로봇던저", "배틀로봇러쉬", "펜싱로봇스피어",
        "사륜구동터프", "복싱로봇어택", "탐사머신탐머", "익룡로봇꺄오기", "미사일발사슈크", "나만의창작로봇",
    ],
    4: [
        "F1자동차스피온", "서스펜션카락크", "버킷굴삭기블라스터", "바이크로봇스톰", "탱크로봇CT-1", "스마트모빌리티몰리",
        "공룡로봇알로", "운반로봇딜리", "지게차로봇포리", "굴삭기로봇카베이터", "폐기물처리로봇로이", "나만의창작로봇",
    ],
    5: [
        "참참참", "왓타임", "스틱 붕붕이", "제로 캐치", "롱 트랙볼", "무.꽃.피",
        "손가락 펀치", "틈새 게임", "줄넘기", "스피드 클라이밍", "스캔 드로잉", "로봇 대회",
    ],
    6: [
        "균형잡기", "폴짝폴짝 눈치 게임", "뒤집기 게임", "두더지 게임", "스핀 터치", "찌르기 게임",
        "턴 프레스", "LED 트래킹", "자석 사냥", "반사 게임", "로봇 대회", "로봇 대회",
    ],
}

program_type, _ = ProgramType.objects.get_or_create(name="코딩", defaults={"order": 0})
program, _ = LearningProgram.objects.get_or_create(
    name=PROGRAM_NAME,
    defaults={
        "description": PROGRAM_DESCRIPTION,
        "program_type": program_type,
        "is_active": True,
    },
)
program.description = PROGRAM_DESCRIPTION
program.program_type = program_type
program.is_active = True
program.save()

Item.objects.filter(chapter__program=program).delete()
Chapter.objects.filter(program=program).delete()

item_count = 0
for level in range(1, 7):
    chapter = Chapter.objects.create(
        program=program,
        number=level,
        title=f"Lv{level}",
        content=LEVEL_DESCRIPTIONS[level],
    )
    for idx, robot_name in enumerate(LEVEL_ITEMS[level], start=1):
        Item.objects.create(
            chapter=chapter,
            number=idx,
            key=f"lv{level}_{idx:02d}",
            title=f"Lv{level}-{idx} {robot_name}",
            item_type="project",
            hint="",
        )
        item_count += 1

print({"program_id": program.id, "chapters": 6, "items": item_count})
