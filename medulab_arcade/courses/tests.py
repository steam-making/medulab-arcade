import io
import tempfile
import zipfile
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from courses.management.commands.seed_ai_sw_olympiad_programs import (
    ELEMENTARY_5_6_PAST_EXAM_ITEMS,
    MIDDLE_1_3_PAST_EXAM_ITEMS,
    PAST_EXAM_ITEMS,
)
from courses.models import (
    AnswerZipImportBatch,
    Chapter,
    Item,
    LearningEnrollment,
    LearningProgram,
    OlympiadAnswerExample,
    OlympiadAnswerSubmission,
    ProgramType,
    UserProgress,
)
from courses.views import parse_olympiad_feedback


def make_test_image(name="direct.png"):
    buffer = io.BytesIO()
    Image.new("RGB", (1, 1), color="white").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


class SeedAiSwOlympiadProgramsTests(TestCase):
    def test_seed_adds_elementary_3_4_past_exam_chapters(self):
        call_command("seed_ai_sw_olympiad_programs")

        program = LearningProgram.objects.get(name="AI SW 사고력 올림피아드 초등 3~4학년")
        chapters = list(program.chapters.order_by("number"))
        round_one_items = list(chapters[0].items.order_by("number"))

        self.assertEqual(len(chapters), 9)
        self.assertEqual(chapters[0].number, 1)
        self.assertEqual(chapters[0].title, "제1회 기출문제")
        self.assertEqual(chapters[-1].number, 9)
        self.assertEqual(chapters[-1].title, "제9회 기출문제")
        self.assertEqual([item.title for item in round_one_items], ["문제 2", "문제 3"])
        self.assertEqual([item.number for item in round_one_items], [2, 3])
        self.assertIn("(초3~4)", round_one_items[0].explain_html)
        self.assertIn("필요한 물건들을 나열하시오", round_one_items[0].explain_html)

    def test_seed_adds_elementary_5_6_past_exam_chapters(self):
        call_command("seed_ai_sw_olympiad_programs")

        program = LearningProgram.objects.get(name="AI SW 사고력 올림피아드 초등 5~6학년")
        chapters = list(program.chapters.order_by("number"))
        round_one_items = list(chapters[0].items.order_by("number"))
        round_nine_items = list(chapters[-1].items.order_by("number"))

        self.assertEqual(len(chapters), 9)
        self.assertEqual(chapters[0].number, 1)
        self.assertEqual(chapters[0].title, "제1회 기출문제")
        self.assertEqual(chapters[-1].number, 9)
        self.assertEqual(chapters[-1].title, "제9회 기출문제")
        self.assertEqual([item.key for item in round_one_items], [
            "ai_sw_olympiad_5_6_round_1_question_2",
            "ai_sw_olympiad_5_6_round_1_question_3",
        ])
        self.assertEqual([item.title for item in round_nine_items], ["문제 1", "문제 2", "문제 3", "문제 4"])
        self.assertIn("(초5~6)", round_one_items[0].explain_html)
        self.assertNotIn("(초3~4)", round_one_items[0].explain_html)
        self.assertFalse(Item.objects.filter(key="ai_sw_olympiad_2_intro").exists())

    def test_seed_adds_elementary_5_6_pdf_specific_problem_text(self):
        call_command("seed_ai_sw_olympiad_programs")

        round_one_q2 = Item.objects.get(key="ai_sw_olympiad_5_6_round_1_question_2")
        round_two_q4 = Item.objects.get(key="ai_sw_olympiad_5_6_round_2_question_4")
        round_nine_q2 = Item.objects.get(key="ai_sw_olympiad_5_6_round_9_question_2")

        self.assertIn("5학년 전체를 5개 반으로 나누어 학급의 이름을 정하려고 한다", round_one_q2.explain_html)
        self.assertIn("방법 ①", round_one_q2.explain_html)
        self.assertIn("방법 ②", round_one_q2.explain_html)
        self.assertIn("2-1", round_one_q2.explain_html)
        self.assertIn("2-2", round_one_q2.explain_html)
        self.assertIn("65536개의 선물을 자동 포장하였다", round_two_q4.explain_html)
        self.assertIn("장난감이 5개나 없었고", round_two_q4.explain_html)
        self.assertIn("32768개의 선물은 배송을 시작하였고", round_two_q4.explain_html)
        self.assertIn("좌석 배치도를 참고하여 교실에서 학생들의 좌석을 배치하는 소프트웨어", round_nine_q2.explain_html)
        self.assertIn("2-1", round_nine_q2.explain_html)
        self.assertIn("2-2", round_nine_q2.explain_html)

    def test_seed_adds_middle_1_3_past_exam_chapters(self):
        call_command("seed_ai_sw_olympiad_programs")

        program = LearningProgram.objects.get(name="AI SW 사고력 올림피아드 중1~3학년")
        chapters = list(program.chapters.order_by("number"))
        round_one_items = list(chapters[0].items.order_by("number"))
        expected_item_count = sum(len(exam["questions"]) for exam in MIDDLE_1_3_PAST_EXAM_ITEMS)

        self.assertEqual(len(chapters), len(MIDDLE_1_3_PAST_EXAM_ITEMS))
        self.assertEqual(chapters[0].number, 1)
        self.assertEqual(chapters[0].title, "제1회 기출문제")
        self.assertEqual(chapters[-1].number, 9)
        self.assertEqual(chapters[-1].title, "제9회 기출문제")
        self.assertEqual([item.key for item in round_one_items], [
            "ai_sw_olympiad_middle_1_3_round_1_question_1",
            "ai_sw_olympiad_middle_1_3_round_1_question_2",
            "ai_sw_olympiad_middle_1_3_round_1_question_4",
        ])
        self.assertIn("(중1~3)", round_one_items[0].explain_html)
        self.assertNotIn("(초5~6)", round_one_items[0].explain_html)
        self.assertEqual(
            Item.objects.filter(chapter__program=program, item_type="olympiad").count(),
            expected_item_count,
        )
        self.assertFalse(Item.objects.filter(key="ai_sw_olympiad_3_intro").exists())

    def test_seed_adds_middle_1_3_pdf_specific_problem_text(self):
        call_command("seed_ai_sw_olympiad_programs")

        round_one_q1 = Item.objects.get(key="ai_sw_olympiad_middle_1_3_round_1_question_1")
        round_five_q2 = Item.objects.get(key="ai_sw_olympiad_middle_1_3_round_5_question_2")
        round_nine_q4 = Item.objects.get(key="ai_sw_olympiad_middle_1_3_round_9_question_4")

        self.assertIn("토끼와 거북이가 서로 경주하여 목표지점에 먼저 도달", round_one_q1.explain_html)
        self.assertIn("1-1", round_one_q1.explain_html)
        self.assertIn("1-4", round_one_q1.explain_html)
        self.assertIn("2019년 4월 4일 강원도 고성군", round_five_q2.explain_html)
        self.assertIn("빅데이터 분석을 활용", round_five_q2.explain_html)
        self.assertIn("앱을 통해 주문하는 배달 음식점", round_nine_q4.explain_html)
        self.assertIn("각 음식은 1일 최대 100그릇", round_nine_q4.explain_html)

    def test_seed_is_idempotent_for_past_exam_chapters(self):
        call_command("seed_ai_sw_olympiad_programs")
        call_command("seed_ai_sw_olympiad_programs")

        program = LearningProgram.objects.get(name="AI SW 사고력 올림피아드 초등 3~4학년")
        expected_item_count = sum(len(exam["questions"]) for exam in PAST_EXAM_ITEMS)

        self.assertEqual(program.chapters.count(), 9)
        self.assertEqual(
            Item.objects.filter(chapter__program=program, item_type="olympiad").count(),
            expected_item_count,
        )

    def test_seed_is_idempotent_for_elementary_5_6_past_exam_chapters(self):
        call_command("seed_ai_sw_olympiad_programs")
        call_command("seed_ai_sw_olympiad_programs")

        program = LearningProgram.objects.get(name="AI SW 사고력 올림피아드 초등 5~6학년")
        expected_item_count = sum(len(exam["questions"]) for exam in ELEMENTARY_5_6_PAST_EXAM_ITEMS)

        self.assertEqual(program.chapters.count(), 9)
        self.assertEqual(
            Item.objects.filter(chapter__program=program, item_type="olympiad").count(),
            expected_item_count,
        )
        self.assertFalse(Item.objects.filter(chapter__program=program, key="ai_sw_olympiad_2_intro").exists())

    def test_seed_is_idempotent_for_middle_1_3_past_exam_chapters(self):
        call_command("seed_ai_sw_olympiad_programs")
        call_command("seed_ai_sw_olympiad_programs")

        program = LearningProgram.objects.get(name="AI SW 사고력 올림피아드 중1~3학년")
        expected_item_count = sum(len(exam["questions"]) for exam in MIDDLE_1_3_PAST_EXAM_ITEMS)

        self.assertEqual(program.chapters.count(), len(MIDDLE_1_3_PAST_EXAM_ITEMS))
        self.assertEqual(
            Item.objects.filter(chapter__program=program, item_type="olympiad").count(),
            expected_item_count,
        )
        self.assertFalse(Item.objects.filter(chapter__program=program, key="ai_sw_olympiad_3_intro").exists())

    def test_seed_removes_elementary_5_6_legacy_intro_item(self):
        program_type = ProgramType.objects.create(name="대회 준비", order=40)
        program = LearningProgram.objects.create(
            name="AI SW 사고력 올림피아드 초등 5~6학년",
            description="old",
            program_type=program_type,
        )
        legacy_chapter = Chapter.objects.create(
            program=program,
            number=1,
            title="초등 5~6학년 답안 작성 훈련",
        )
        Item.objects.create(
            chapter=legacy_chapter,
            number=1,
            key="ai_sw_olympiad_2_intro",
            title="답안 작성 훈련 안내",
            item_type="olympiad",
        )

        call_command("seed_ai_sw_olympiad_programs")

        self.assertFalse(Item.objects.filter(key="ai_sw_olympiad_2_intro").exists())
        self.assertEqual(program.chapters.count(), 9)
        self.assertEqual(program.chapters.get(number=1).title, "제1회 기출문제")

    def test_seed_removes_middle_1_3_legacy_intro_item(self):
        program_type = ProgramType.objects.create(name="대회 준비", order=40)
        program = LearningProgram.objects.create(
            name="AI SW 사고력 올림피아드 중1~3학년",
            description="old",
            program_type=program_type,
        )
        legacy_chapter = Chapter.objects.create(
            program=program,
            number=1,
            title="중등 1~3학년 답안 작성 훈련",
        )
        Item.objects.create(
            chapter=legacy_chapter,
            number=1,
            key="ai_sw_olympiad_3_intro",
            title="답안 작성 훈련 안내",
            item_type="olympiad",
        )

        call_command("seed_ai_sw_olympiad_programs")

        self.assertFalse(Item.objects.filter(key="ai_sw_olympiad_3_intro").exists())
        self.assertEqual(program.chapters.count(), len(MIDDLE_1_3_PAST_EXAM_ITEMS))
        self.assertEqual(program.chapters.get(number=1).title, "제1회 기출문제")

    def test_seed_removes_legacy_single_chapter_round_items(self):
        program_type = ProgramType.objects.create(name="대회 준비", order=40)
        program = LearningProgram.objects.create(
            name="AI SW 사고력 올림피아드 초등 3~4학년",
            description="old",
            program_type=program_type,
        )
        legacy_chapter = Chapter.objects.create(
            program=program,
            number=1,
            title="초등 3~4학년 답안 작성 훈련",
        )
        Item.objects.create(
            chapter=legacy_chapter,
            number=1,
            key="ai_sw_olympiad_1_intro",
            title="답안 작성 훈련 안내",
            item_type="olympiad",
        )
        Item.objects.create(
            chapter=legacy_chapter,
            number=2,
            key="ai_sw_olympiad_3_4_round_1",
            title="제1회 기출문제: 물건 분류와 모둠 구성",
            item_type="olympiad",
        )

        call_command("seed_ai_sw_olympiad_programs")

        self.assertFalse(Item.objects.filter(key="ai_sw_olympiad_1_intro").exists())
        self.assertFalse(Item.objects.filter(key="ai_sw_olympiad_3_4_round_1").exists())
        self.assertEqual(program.chapters.count(), 9)
        self.assertEqual(program.chapters.get(number=1).title, "제1회 기출문제")

    def test_seed_adds_problem_specific_olympiad_hints(self):
        call_command("seed_ai_sw_olympiad_programs")

        round_one_q2 = Item.objects.get(key="ai_sw_olympiad_3_4_round_1_question_2")
        round_one_q3 = Item.objects.get(key="ai_sw_olympiad_3_4_round_1_question_3")

        self.assertIn("[문제 분석]", round_one_q2.hint)
        self.assertIn("[예시답안 요약 힌트]", round_one_q2.hint)
        self.assertIn("물건", round_one_q2.hint)
        self.assertIn("24명", round_one_q3.hint)
        self.assertNotEqual(round_one_q2.hint, round_one_q3.hint)

    def test_seed_adds_problem_specific_elementary_5_6_olympiad_hints(self):
        call_command("seed_ai_sw_olympiad_programs")

        round_one_q2 = Item.objects.get(key="ai_sw_olympiad_5_6_round_1_question_2")
        round_two_q2 = Item.objects.get(key="ai_sw_olympiad_5_6_round_2_question_2")

        self.assertIn("[문제 분석]", round_one_q2.hint)
        self.assertIn("[예시답안 요약 힌트]", round_one_q2.hint)
        self.assertIn("이름", round_one_q2.hint)
        self.assertIn("게임 중독", round_two_q2.hint)
        self.assertNotEqual(round_one_q2.hint, round_two_q2.hint)

    def test_seed_adds_problem_specific_middle_1_3_olympiad_hints(self):
        call_command("seed_ai_sw_olympiad_programs")

        round_one_q1 = Item.objects.get(key="ai_sw_olympiad_middle_1_3_round_1_question_1")
        round_nine_q5 = Item.objects.get(key="ai_sw_olympiad_middle_1_3_round_9_question_5")

        self.assertIn("[문제 분석]", round_one_q1.hint)
        self.assertIn("[예시답안 요약 힌트]", round_one_q1.hint)
        self.assertIn("경주 게임", round_one_q1.hint)
        self.assertIn("핵융합", round_nine_q5.hint)
        self.assertNotEqual(round_one_q1.hint, round_nine_q5.hint)


class OlympiadAnswerZipManageTests(TestCase):
    def setUp(self):
        call_command("seed_ai_sw_olympiad_programs")
        self.program = LearningProgram.objects.get(name="AI SW 사고력 올림피아드 초등 3~4학년")
        self.staff = User.objects.create_user(username="teacher", password="pass", is_staff=True)
        self.client.force_login(self.staff)

    def make_zip_upload(self, files):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for path, content in files.items():
                archive.writestr(path, content)
        buffer.seek(0)
        return SimpleUploadedFile("answer.zip", buffer.read(), content_type="application/zip")

    def test_download_answer_zip_template_contains_chapter_problem_folders(self):
        response = self.client.get(reverse("download_answer_zip_template", args=[self.program.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            names = archive.namelist()

        self.assertIn("제1회 기출문제/문제 2/README.txt", names)
        self.assertIn("제1회 기출문제/문제 3/README.txt", names)
        self.assertIn("제9회 기출문제/문제 3/README.txt", names)

    def test_manage_page_shows_direct_example_upload_button(self):
        response = self.client.get(reverse("chapter_manage", args=[self.program.id]))

        self.assertContains(response, "+예시답안")
        self.assertContains(response, reverse("olympiad_example_add", args=[
            Item.objects.get(chapter__program=self.program, chapter__number=1, number=2).id
        ]))

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_uploaded_answer_zip_creates_olympiad_answer_examples(self):
        upload = self.make_zip_upload({
            "README.txt": b"instructions",
            "제1회 기출문제/문제 2/01.jpg": b"image-one",
            "제1회 기출문제/문제 2/02.png": b"image-two",
            "제1회 기출문제/문제 3/01.jpg": b"image-three",
        })

        preview_response = self.client.post(
            reverse("chapter_manage", args=[self.program.id]),
            {"import_action": "preview_answer_zip", "answer_zip": upload},
        )
        self.assertEqual(preview_response.status_code, 200)
        batch = AnswerZipImportBatch.objects.get(program=self.program, status=AnswerZipImportBatch.STATUS_PREVIEW)
        self.assertEqual(batch.import_rule, "olympiad_answer_examples_by_chapter_item")
        self.assertEqual(batch.preview_data["file_count"], 3)

        apply_response = self.client.post(reverse("answer_zip_apply", args=[self.program.id, batch.id]))
        self.assertEqual(apply_response.status_code, 302)

        item_2 = Item.objects.get(chapter__program=self.program, chapter__number=1, number=2)
        item_3 = Item.objects.get(chapter__program=self.program, chapter__number=1, number=3)
        self.assertEqual(OlympiadAnswerExample.objects.filter(item=item_2).count(), 2)
        self.assertEqual(OlympiadAnswerExample.objects.filter(item=item_3).count(), 1)

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_direct_problem_example_image_upload_creates_example(self):
        item = Item.objects.get(chapter__program=self.program, chapter__number=1, number=2)
        image = make_test_image()

        response = self.client.post(
            reverse("olympiad_example_add", args=[item.id]),
            {"image": image, "caption": "직접 등록"},
        )

        self.assertEqual(response.status_code, 302)
        example = OlympiadAnswerExample.objects.get(item=item)
        self.assertEqual(example.caption, "직접 등록")
        self.assertEqual(example.order, 1)

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_direct_problem_example_image_upload_appends_order(self):
        item = Item.objects.get(chapter__program=self.program, chapter__number=1, number=2)
        OlympiadAnswerExample.objects.create(item=item, image=make_test_image("old.png"), order=3)
        image = make_test_image("new.png")

        self.client.post(reverse("olympiad_example_add", args=[item.id]), {"image": image})

        self.assertEqual(list(item.olympiad_examples.order_by("order").values_list("order", flat=True)), [3, 4])

    def test_item_page_shows_example_upload_form_for_staff(self):
        item = Item.objects.get(chapter__program=self.program, chapter__number=1, number=2)
        response = self.client.get(reverse("item_page", args=[item.id]))
        self.assertContains(response, "+ 예시답안 직접 추가")
        self.assertContains(response, reverse("olympiad_example_add", args=[item.id]))
        self.assertContains(response, 'name="next"')

    def test_item_page_hides_example_upload_form_for_non_staff(self):
        item = Item.objects.get(chapter__program=self.program, chapter__number=1, number=2)
        self.client.logout()

        response = self.client.get(reverse("item_page", args=[item.id]))

        self.assertNotContains(response, "+ 예시답안 직접 추가")
        self.assertNotContains(response, 'name="caption"')

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_direct_problem_example_image_upload_with_next_redirects_to_next(self):
        item = Item.objects.get(chapter__program=self.program, chapter__number=1, number=2)
        image = make_test_image()
        next_url = reverse("item_page", args=[item.id])

        response = self.client.post(
            reverse("olympiad_example_add", args=[item.id]),
            {"image": image, "caption": "직접 등록", "next": next_url},
        )

        self.assertRedirects(response, next_url)
        example = OlympiadAnswerExample.objects.get(item=item)
        self.assertEqual(example.caption, "직접 등록")

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_direct_problem_example_image_upload_rejects_fake_image_content(self):
        item = Item.objects.get(chapter__program=self.program, chapter__number=1, number=2)
        image = SimpleUploadedFile("fake.png", b"not-an-image", content_type="image/png")

        response = self.client.post(reverse("olympiad_example_add", args=[item.id]), {"image": image})

        self.assertEqual(response.status_code, 302)
        self.assertFalse(OlympiadAnswerExample.objects.filter(item=item).exists())

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_direct_problem_example_image_upload_rejects_unsafe_next_redirect(self):
        item = Item.objects.get(chapter__program=self.program, chapter__number=1, number=2)

        response = self.client.post(
            reverse("olympiad_example_add", args=[item.id]),
            {"image": make_test_image(), "next": "https://evil.example/phish"},
        )

        self.assertRedirects(response, reverse("chapter_manage", args=[self.program.id]))


class OlympiadAnswerSubmissionFeedbackTests(TestCase):
    def setUp(self):
        self.program = LearningProgram.objects.create(name="올림피아드 제출 테스트")
        self.chapter = Chapter.objects.create(program=self.program, number=1, title="제출 단원")
        self.item = Item.objects.create(
            chapter=self.chapter,
            number=1,
            key="olympiad_feedback",
            title="문제 1",
            item_type="olympiad",
            hint="24명을 공정하게 나누는 기준과 이유를 함께 쓰세요.",
        )
        self.student = User.objects.create_user(username="student", password="pass")
        self.student.profile.user_type = "medulab_member"
        self.student.profile.is_approved = True
        self.student.profile.save()
        LearningEnrollment.objects.create(user=self.student, program=self.program)
        self.client.force_login(self.student)

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_student_submission_generates_deterministic_feedback(self):
        response = self.client.post(
            reverse("submit_olympiad_answer", args=[self.item.id]),
            {
                "answer_image": make_test_image("answer.png"),
                "edited_text": "24명을 같은 수로 나누고 기준을 설명했습니다.",
            },
        )

        self.assertEqual(response.status_code, 302)
        submission = OlympiadAnswerSubmission.objects.get(item=self.item, student=self.student)
        self.assertIn("사진 확인", submission.feedback)
        self.assertIn("AI 평가점수", submission.feedback)
        self.assertRegex(submission.feedback, r"\d{1,3}/100점")
        self.assertIn("답안 보완 포인트", submission.feedback)
        self.assertIn("다음 제출 팁", submission.feedback)
        self.assertIn("24명", submission.feedback)
        self.assertIn("조건, 풀이 과정, 결론", submission.feedback)
        feedback_sections = parse_olympiad_feedback(submission.feedback)
        self.assertEqual(feedback_sections[0]["kind"], "score")
        self.assertIsNotNone(feedback_sections[0]["score"])
        self.assertIn("improvement", {section["kind"] for section in feedback_sections})
        item_response = self.client.get(reverse("item_page", args=[self.item.id]))
        self.assertContains(item_response, "feedback-score")
        self.assertContains(item_response, "feedback-improvement")
        progress = UserProgress.objects.get(user=self.student, item=self.item)
        self.assertTrue(progress.completed)

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_feedback_generation_failure_does_not_block_submission(self):
        with patch("courses.views.build_olympiad_submission_feedback", side_effect=RuntimeError("feedback failed")):
            response = self.client.post(
                reverse("submit_olympiad_answer", args=[self.item.id]),
                {"answer_image": make_test_image("answer.png")},
            )

        self.assertEqual(response.status_code, 302)
        submission = OlympiadAnswerSubmission.objects.get(item=self.item, student=self.student)
        self.assertIn("AI 평가점수", submission.feedback)
        self.assertIn("평가 보류", submission.feedback)
        self.assertIn("정상 제출", submission.feedback)
        self.assertIn("자동 보완 피드백", submission.feedback)
        self.assertEqual(submission.status, OlympiadAnswerSubmission.STATUS_SUBMITTED)
        progress = UserProgress.objects.get(user=self.student, item=self.item)
        self.assertTrue(progress.completed)
