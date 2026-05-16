from django.core.management.base import BaseCommand
from django.db import transaction

from courses.models import Chapter, Item, LearningProgram, ProgramType


PROGRAM_TYPE_NAME = "대회 준비"

PROGRAMS = [
    {
        "name": "AI SW 사고력 올림피아드 초등 3~4학년",
        "description": (
            "초등학교 3~4학년 학생을 위한 AI·SW 사고력 올림피아드 대비 과정입니다. "
            "기출문제를 바탕으로 문제 조건 파악, 분류 기준 세우기, 알고리즘 순서화, "
            "그림·표·순서도를 활용한 수기 답안 작성 훈련을 진행합니다."
        ),
        "chapter_title": "초등 3~4학년 답안 작성 훈련",
    },
    {
        "name": "AI SW 사고력 올림피아드 초등 5~6학년",
        "description": (
            "초등학교 5~6학년 학생을 위한 AI·SW 사고력 올림피아드 대비 과정입니다. "
            "생활·교과 융합 문제를 분석하고, 데이터·규칙·절차를 구조화하여 "
            "채점자가 이해하기 쉬운 수상권 답안을 작성하는 훈련을 진행합니다."
        ),
        "chapter_title": "초등 5~6학년 답안 작성 훈련",
    },
    {
        "name": "AI SW 사고력 올림피아드 중1~3학년",
        "description": (
            "중학교 1~3학년 학생을 위한 AI·SW 사고력 올림피아드 대비 과정입니다. "
            "AI·데이터·시스템·윤리 문제를 통합적으로 분석하고, 근거와 표현력을 갖춘 "
            "논리적 답안 작성 능력을 기릅니다."
        ),
        "chapter_title": "중등 1~3학년 답안 작성 훈련",
    },
]

INTRO_HINT = """정답을 바로 찾으려 하지 말고, 답안의 구조를 먼저 잡아보세요.
1. 문제에서 요구한 조건을 밑줄 치듯 정리합니다.
2. 필요한 정보와 분류 기준을 먼저 나열합니다.
3. 해결 방법을 번호, 표, 그림, 순서도 중 하나로 표현합니다.
4. 마지막에 왜 이 방법이 좋은지 이유를 씁니다.
5. 안전성, 공정성, 편리성까지 고려하면 더 좋은 답안이 됩니다."""

INTRO_HTML = """
<h2>AI SW 사고력 올림피아드 답안 작성 훈련</h2>
<p>이 과정은 실제 대회처럼 종이에 직접 답안을 작성하고, 작성한 답안을 사진으로 제출하는 방식으로 훈련합니다.</p>
<ul>
  <li>문제 원문을 읽고 조건을 빠뜨리지 않는 연습</li>
  <li>분류 기준, 규칙, 알고리즘 순서를 세우는 연습</li>
  <li>표·그림·순서도로 생각을 표현하는 연습</li>
  <li>제출 후 예시답안과 비교하며 보완하는 연습</li>
</ul>
<p>관리자가 기출문제를 추가하면 이 화면에서 문제를 풀고 답안 사진을 제출할 수 있습니다.</p>
""".strip()


class Command(BaseCommand):
    help = "AI SW 사고력 올림피아드 3개 대비 과정을 생성합니다."

    def add_arguments(self, parser):
        parser.add_argument(
            "--replace",
            action="store_true",
            help="같은 이름의 기존 과정이 있으면 안내 챕터를 다시 생성합니다.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        program_type, _ = ProgramType.objects.get_or_create(
            name=PROGRAM_TYPE_NAME,
            defaults={"order": 40},
        )
        replace = options["replace"]

        for index, data in enumerate(PROGRAMS, start=1):
            program, created = LearningProgram.objects.get_or_create(
                name=data["name"],
                defaults={
                    "description": data["description"],
                    "program_type": program_type,
                    "is_active": True,
                },
            )
            program.description = data["description"]
            program.program_type = program_type
            program.is_active = True
            program.save(update_fields=["description", "program_type", "is_active"])

            if replace:
                program.chapters.all().delete()

            if not program.chapters.exists():
                chapter = Chapter.objects.create(
                    program=program,
                    number=1,
                    title=data["chapter_title"],
                    content="기출문제 기반 수기 답안 작성 훈련을 시작합니다.",
                )
                Item.objects.create(
                    chapter=chapter,
                    number=1,
                    key=f"ai_sw_olympiad_{index}_intro",
                    title="답안 작성 훈련 안내",
                    item_type="olympiad",
                    explain_html=INTRO_HTML,
                    hint=INTRO_HINT,
                )

            status = "생성" if created else "업데이트"
            self.stdout.write(self.style.SUCCESS(f"{status}: {program.name}"))
