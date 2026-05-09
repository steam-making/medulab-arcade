import re

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from courses.models import Chapter, Item, LearningProgram


EXPECTED_EXAM_TITLE = "출제예상 모의고사"
PAST_EXAM_TITLE = "기출문제"
SLIDE6_TITLES = {"슬라이드 6", "슬라이드6"}


def extract_round_number(title: str) -> int:
    match = re.search(r"(\d+)\s*회", title or "")
    return int(match.group(1)) if match else 0


def make_expected_title(round_number: int) -> str:
    return f"제 {round_number:02d}회 출제예상 모의고사"


def make_past_title(round_number: int) -> str:
    return f"제 {round_number:02d}회 기출문제"


def renumber_items(chapter: Chapter) -> None:
    for index, item in enumerate(chapter.items.order_by("number", "id"), start=1):
        if item.number != index:
            item.number = index
            item.save(update_fields=["number"])


class Command(BaseCommand):
    help = "ITQ 파워포인트 과정의 슬라이드6/출제예상 모의고사/기출문제 구조를 정리합니다."

    def add_arguments(self, parser):
        parser.add_argument(
            "--program-id",
            type=int,
            default=3,
            help="대상 LearningProgram ID (기본값: 3)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        program_id = options["program_id"]

        try:
            program = LearningProgram.objects.get(id=program_id)
        except LearningProgram.DoesNotExist as exc:
            raise CommandError(f"LearningProgram id={program_id} 를 찾을 수 없습니다.") from exc

        chapters = list(program.chapters.order_by("number", "id"))
        slide6_chapter = next((chapter for chapter in chapters if (chapter.title or "").strip() in SLIDE6_TITLES), None)
        if slide6_chapter is None:
            slide6_chapter = next((chapter for chapter in chapters if chapter.number == 7), None)

        if slide6_chapter is None:
            raise CommandError("슬라이드 6 챕터를 찾지 못했습니다.")

        slide6_chapter.title = "슬라이드 6"
        if not slide6_chapter.content:
            slide6_chapter.content = "슬라이드 6 학습 내용입니다."
        slide6_chapter.save(update_fields=["title", "content"])

        expected_exam_chapter = next((chapter for chapter in chapters if (chapter.title or "").strip() == EXPECTED_EXAM_TITLE), None)
        past_exam_chapter = next((chapter for chapter in chapters if (chapter.title or "").strip() == PAST_EXAM_TITLE), None)

        if expected_exam_chapter is None:
            expected_exam_chapter = Chapter.objects.create(
                program=program,
                number=slide6_chapter.number + 1,
                title=EXPECTED_EXAM_TITLE,
                content="제 1회부터 제 15회까지 출제예상 모의고사를 차례대로 학습합니다.",
            )

        if past_exam_chapter is None:
            past_exam_chapter = Chapter.objects.create(
                program=program,
                number=expected_exam_chapter.number + 1,
                title=PAST_EXAM_TITLE,
                content="제 1회부터 제 10회까지 기출문제를 복습합니다.",
            )

        base_slide_items = []
        expected_items_to_move = []
        for item in slide6_chapter.items.order_by("number", "id"):
            if "출제예상 모의고사" in (item.title or ""):
                expected_items_to_move.append(item)
            else:
                base_slide_items.append(item)

        for item in expected_items_to_move:
            item.chapter = expected_exam_chapter
            item.save(update_fields=["chapter"])

        expected_by_round = {}
        for item in expected_exam_chapter.items.order_by("number", "id"):
            round_number = extract_round_number(item.title)
            if round_number:
                expected_by_round.setdefault(round_number, item)

        for round_number in range(1, 16):
            item = expected_by_round.get(round_number)
            if item is None:
                Item.objects.create(
                    chapter=expected_exam_chapter,
                    number=round_number,
                    key=f"itq_ppt_expected_{round_number:02d}",
                    title=make_expected_title(round_number),
                    item_type="problem",
                    explain_html="",
                )
            else:
                updates = []
                expected_title = make_expected_title(round_number)
                if item.title != expected_title:
                    item.title = expected_title
                    updates.append("title")
                expected_key = f"itq_ppt_expected_{round_number:02d}"
                if item.key != expected_key:
                    item.key = expected_key
                    updates.append("key")
                if updates:
                    item.save(update_fields=updates)

        past_by_round = {}
        for item in past_exam_chapter.items.order_by("number", "id"):
            round_number = extract_round_number(item.title)
            if round_number:
                past_by_round.setdefault(round_number, item)

        for round_number in range(1, 11):
            item = past_by_round.get(round_number)
            if item is None:
                Item.objects.create(
                    chapter=past_exam_chapter,
                    number=round_number,
                    key=f"itq_ppt_past_{round_number:02d}",
                    title=make_past_title(round_number),
                    item_type="problem",
                    explain_html="",
                )
            else:
                updates = []
                past_title = make_past_title(round_number)
                if item.title != past_title:
                    item.title = past_title
                    updates.append("title")
                past_key = f"itq_ppt_past_{round_number:02d}"
                if item.key != past_key:
                    item.key = past_key
                    updates.append("key")
                if updates:
                    item.save(update_fields=updates)

        for stale_item in expected_exam_chapter.items.order_by("number", "id"):
            round_number = extract_round_number(stale_item.title)
            if not 1 <= round_number <= 15:
                stale_item.delete()

        for stale_item in past_exam_chapter.items.order_by("number", "id"):
            round_number = extract_round_number(stale_item.title)
            if not 1 <= round_number <= 10:
                stale_item.delete()

        ordered_chapters = []
        for chapter in program.chapters.order_by("number", "id"):
            title = (chapter.title or "").strip()
            if chapter.id == slide6_chapter.id:
                ordered_chapters.append(chapter)
            elif chapter.id == expected_exam_chapter.id:
                continue
            elif chapter.id == past_exam_chapter.id:
                continue
            else:
                ordered_chapters.append(chapter)

        insert_index = ordered_chapters.index(slide6_chapter) + 1
        ordered_chapters.insert(insert_index, expected_exam_chapter)
        ordered_chapters.insert(insert_index + 1, past_exam_chapter)

        for index, chapter in enumerate(ordered_chapters, start=1):
            updates = []
            if chapter.number != index:
                chapter.number = index
                updates.append("number")
            if chapter.id == expected_exam_chapter.id:
                chapter.title = EXPECTED_EXAM_TITLE
                chapter.content = "제 1회부터 제 15회까지 출제예상 모의고사를 차례대로 학습합니다."
                updates.extend([field for field in ("title", "content") if field not in updates])
            elif chapter.id == past_exam_chapter.id:
                chapter.title = PAST_EXAM_TITLE
                chapter.content = "제 1회부터 제 10회까지 기출문제를 복습합니다."
                updates.extend([field for field in ("title", "content") if field not in updates])
            elif chapter.id == slide6_chapter.id and chapter.title != "슬라이드 6":
                chapter.title = "슬라이드 6"
                updates.append("title")
            if updates:
                chapter.save(update_fields=updates)

        renumber_items(slide6_chapter)
        renumber_items(expected_exam_chapter)
        renumber_items(past_exam_chapter)

        self.stdout.write(self.style.SUCCESS(f"'{program.name}' 과정 구조를 정리했습니다."))
