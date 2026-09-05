from django.core.management.base import BaseCommand

from courses.models import Chapter, Item, LearningProgram, ProgramType

PROGRAM_TYPE_NAME = "자격증 대비"

# 3급 목차 구조 (제목만 — 설명 내용은 관리자가 나중에 채워 넣음)
CHAPTERS_3 = [
    {
        "title": "AICE FUTURE와의 첫 만남",
        "content": "AICE Future 시험과 AI Codiny에 대해 전체적으로 살펴봅니다.",
        "items": [
            ("국영수코 시대, 코딩 교육의 중요성", "example"),
            ("실전형 AI 인재 양성 로드맵, AICE", "example"),
            ("AICE Future 특징", "example"),
        ],
    },
    {
        "title": "처음 만나는 인공지능, AI 이해하기",
        "content": "인공지능 이론과 AI 학습 플랫폼 AI Codiny를 처음 만나봅니다.",
        "items": [
            ("인공지능이란?", "example"),
            ("약 인공지능과 강 인공지능", "example"),
            ("인공지능의 발전사", "example"),
            ("인공지능 윤리", "example"),
            ("AI Codiny란?", "example"),
            ("AI Codiny 구성 살펴보기", "example"),
            ("AI Codiny에서 인공지능과 대화하기", "example"),
        ],
    },
    {
        "title": "AI 코디니 기능 익히기",
        "content": "AI Codiny 기본 기능과 알고리즘·순차 구조를 익힙니다.",
        "items": [
            ("AI Codiny 프로그램", "example"),
            ("오브젝트 다루기", "example"),
            ("소리 추가하기", "example"),
            ("오브젝트 조작 코딩하기", "example"),
            ("소리 블록 추가하기", "example"),
            ("인공지능 비서 코딩하기", "example"),
            ("알고리즘이란?", "example"),
            ("순차 구조 이해하기", "example"),
            ("좌표 이해하기", "example"),
            ("장면 추가하기", "example"),
            ("순차 구조를 활용한 코딩하기", "example"),
        ],
    },
    {
        "title": "AI 코디니와 함께 쉽고 재미있는 AI 해보기",
        "content": "음성합성·음성인식·호출어·변수·비교연산 등을 실습하며 AI를 직접 만들어봅니다.",
        "items": [
            ("음성합성이란?", "example"),
            ("음성합성의 원리와 구조", "example"),
            ("음성합성 코딩하기", "example"),
            ("외국어 음성합성과 목소리 설정", "example"),
            ("음성합성을 활용한 코딩하기", "example"),
            ("음성합성을 활용한 햄버거 가게 코딩하기", "project"),
            ("음성인식이란?", "example"),
            ("문자형으로 출력하기", "example"),
            ("음성인식 코딩하기", "example"),
            ("음성인식 후 움직이는 오브젝트", "example"),
            ("코디니의 길 찾기", "project"),
            ("호출어란?", "example"),
            ("호출어 사용하기", "example"),
            ("조건 명령 블록", "example"),
            ("반복 명령 블록", "example"),
            ("호출어를 사용한 코딩", "example"),
            ("호출어를 사용한 인공지능 비서 프로그램", "example"),
            ("영어로 말하는 관광 안내 로봇 지니", "project"),
            ("변수란?", "example"),
            ("변수를 활용한 코딩", "example"),
            ("음성인식에 변수 사용하기", "example"),
            ("변수를 활용한 가족 소개 프로그램", "project"),
            ("말을 잘 알아듣는 지니", "example"),
            ("문장 덧붙이기", "example"),
            ("문장 결합하기", "example"),
            ("동물농장 프로그램", "project"),
            ("비교 연산 블록", "example"),
            ("변수로 횟수 계산하기", "example"),
            ("숫자 맞히기 게임 코딩하기", "project"),
        ],
    },
    {
        "title": "AICE FUTURE 도전하기",
        "content": "실전 모의평가로 AICE Future 3급 검정 시험을 대비합니다.",
        "items": [
            ("AICE FUTURE 모의평가 실습 방법", "example"),
            ("AICE FUTURE 3급 검정 실전 대비 가이드", "example"),
            ("AICE Future 대비 모의평가 1차", "objective"),
            ("AICE Future 대비 모의평가 2차", "objective"),
            ("AICE Future 대비 모의평가 3차", "objective"),
            ("AICE Future 대비 모의평가 4차", "objective"),
            ("AICE Future 대비 모의평가 5차", "objective"),
            ("AICE Future 대비 모의평가 6차", "objective"),
            ("AICE Future 대비 모의평가 7차", "objective"),
            ("AICE Future 대비 모의평가 8차", "objective"),
            ("AICE Future 대비 모의평가 9차", "objective"),
            ("AICE Future 대비 모의평가 10차", "objective"),
            ("AICE Future 대비 모의평가 정답 및 해설", "example"),
        ],
    },
]

PROGRAMS = [
    {
        "name": "AICE Future 3급 대비",
        "description": "AICE Future 3급 자격증 취득을 위한 과정입니다. AI Codiny로 직접 실습하며 인공지능 기초 이론부터 음성합성·음성인식·변수·비교연산까지 익히고, 실전 모의평가로 시험을 대비합니다.",
        "chapters": CHAPTERS_3,
    },
    {
        "name": "AICE Future 2급 대비",
        "description": "AICE Future 2급 자격증 취득을 위한 과정입니다. (준비 중)",
        "chapters": [],
    },
    {
        "name": "AICE Future 1급 대비",
        "description": "AICE Future 1급 자격증 취득을 위한 과정입니다. (준비 중)",
        "chapters": [],
    },
]


class Command(BaseCommand):
    help = "AICE Future 1/2/3급 과정을 생성합니다 (3급은 목차 구조까지, 1/2급은 빈 과정)."

    def add_arguments(self, parser):
        parser.add_argument("--replace", action="store_true", help="이미 있으면 챕터/문항을 지우고 다시 생성")

    def handle(self, *args, **options):
        program_type, _ = ProgramType.objects.get_or_create(
            name=PROGRAM_TYPE_NAME, defaults={"order": 0}
        )

        for prog_data in PROGRAMS:
            program, created = LearningProgram.objects.get_or_create(
                name=prog_data["name"],
                defaults={
                    "description": prog_data["description"],
                    "program_type": program_type,
                    "is_active": True,
                },
            )
            if not created and not options["replace"] and program.chapters.exists():
                self.stdout.write(self.style.WARNING(
                    f"'{prog_data['name']}' 은(는) 이미 챕터가 있습니다. --replace 옵션 없이는 건너뜁니다."
                ))
                continue

            program.description = prog_data["description"]
            program.program_type = program_type
            program.is_active = True
            program.save()
            program.chapters.all().delete()

            item_total = 0
            key_prefix = prog_data["name"].split()[1].lower() if len(prog_data["name"].split()) > 1 else "aice"

            for chapter_index, chapter_data in enumerate(prog_data["chapters"], start=1):
                chapter = Chapter.objects.create(
                    program=program,
                    number=chapter_index,
                    title=chapter_data["title"],
                    content=chapter_data["content"],
                )
                for item_index, (item_title, item_type) in enumerate(chapter_data["items"], start=1):
                    item_total += 1
                    Item.objects.create(
                        chapter=chapter,
                        number=item_index,
                        key=f"{key_prefix}_{chapter_index:02d}_{item_index:02d}",
                        title=item_title,
                        item_type=item_type,
                        explain_html="",
                    )

            self.stdout.write(self.style.SUCCESS(
                f"'{prog_data['name']}' 생성 완료 (챕터 {len(prog_data['chapters'])}개, 문항 {item_total}개)"
            ))
