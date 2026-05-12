from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from courses.management.commands.seed_rc_code_python_ab import (
    PROGRAM_TYPE_NAME,
    build_python_a_data,
    build_python_b_data,
)
from courses.models import Chapter, Item, LearningProgram, ProgramType


PROGRAM_SPECS = [
    {
        "name": "RC.CODE Python A 대회 연습",
        "description": (
            "RC.CODE Python A(12세 이하) 원문 가이드를 바탕으로 구성한 대회 연습 과정입니다. "
            "대회 개요와 출제 범위를 먼저 익히고 공식 객관식 5문제와 프로그래밍 5문제를 "
            "입력 형식, 출력 형식, 채점 포인트까지 포함해 연습할 수 있도록 보강했습니다. "
            "이후 추가 문제와 실전 20문제 세트로 기본 문법, 반복문, 조건문, 리스트, 조합 탐색, "
            "369 pass 규칙, 동적 계획법까지 단계적으로 익힐 수 있습니다."
        ),
        "chapters": build_python_a_data,
    },
    {
        "name": "RC.CODE Python B 대회 연습",
        "description": (
            "RC.CODE Python B(18세 이하) 원문 가이드를 바탕으로 구성한 대회 연습 과정입니다. "
            "공식 객관식 5문제와 프로그래밍 5문제를 원문 문제 구조에 가깝게 정리하고, "
            "입력·출력 설명과 핵심 알고리즘 포인트를 함께 제공하도록 보강했습니다. "
            "직사각형 넓이, 수 뒤집기, 최적 배치, 그리디 병합, DP 배달 점수 문제를 통해 "
            "함수, 자료구조, 완전탐색, 그리디, 동적 계획법까지 폭넓게 연습할 수 있습니다."
        ),
        "chapters": build_python_b_data,
    },
]


class Command(BaseCommand):
    help = "Refresh RC.CODE Python A/B course content in place without removing progress data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--program",
            choices=["A", "B", "ALL"],
            default="ALL",
            help="Refresh only one RC.CODE course or both.",
        )

    def _iter_specs(self, selected_program):
        if selected_program == "A":
            return [PROGRAM_SPECS[0]]
        if selected_program == "B":
            return [PROGRAM_SPECS[1]]
        return PROGRAM_SPECS

    @transaction.atomic
    def handle(self, *args, **options):
        selected_program = options["program"]
        program_type, _ = ProgramType.objects.get_or_create(
            name=PROGRAM_TYPE_NAME,
            defaults={"order": 40},
        )

        for spec in self._iter_specs(selected_program):
            self.refresh_program(
                program_type=program_type,
                course_name=spec["name"],
                description=spec["description"],
                chapters_data=spec["chapters"](),
            )

    def refresh_program(self, program_type, course_name, description, chapters_data):
        try:
            program = LearningProgram.objects.get(name=course_name)
        except LearningProgram.DoesNotExist as exc:
            raise CommandError(
                f"'{course_name}' 과정을 찾을 수 없습니다. 먼저 seed_rc_code_python_ab 명령으로 과정을 생성해 주세요."
            ) from exc

        program.description = description
        program.program_type = program_type
        program.is_active = True
        program.save(update_fields=["description", "program_type", "is_active"])

        existing_chapters = {chapter.number: chapter for chapter in program.chapters.all()}
        updated_items = 0
        created_items = 0
        updated_chapters = 0
        created_chapters = 0

        for chapter_index, chapter_data in enumerate(chapters_data, start=1):
            chapter = existing_chapters.get(chapter_index)
            if chapter is None:
                chapter = Chapter.objects.create(
                    program=program,
                    number=chapter_index,
                    title=chapter_data["title"],
                    content=chapter_data["content"],
                )
                created_chapters += 1
            else:
                chapter.title = chapter_data["title"]
                chapter.content = chapter_data["content"]
                chapter.save(update_fields=["title", "content"])
                updated_chapters += 1

            existing_items = {item.number: item for item in chapter.items.all()}

            for item_index, item_data in enumerate(chapter_data["items"], start=1):
                key = f"rc_{program.id}_{chapter_index:02d}_{item_index:02d}"
                item = existing_items.get(item_index)
                fields = {
                    "key": key,
                    "title": item_data["title"],
                    "item_type": item_data["item_type"],
                    "explain_html": item_data["explain_html"],
                    "hint": item_data["hint"],
                    "answer_code": item_data["answer_code"],
                    "example_input": item_data["example_input"],
                    "expected_output": item_data["expected_output"],
                }

                if item is None:
                    Item.objects.create(
                        chapter=chapter,
                        number=item_index,
                        **fields,
                    )
                    created_items += 1
                else:
                    for field_name, value in fields.items():
                        setattr(item, field_name, value)
                    item.save(update_fields=list(fields.keys()))
                    updated_items += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"'{course_name}' 동기화 완료: 챕터 {updated_chapters}개 수정, {created_chapters}개 생성 / "
                f"문항 {updated_items}개 수정, {created_items}개 생성"
            )
        )
