from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Award, CompetitionType


class AwardBoardTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username="staff", password="pass", is_staff=True)

    def test_create_award_creates_new_competition_type_from_search_text(self):
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse("board_awards_create"),
            {
                "student_name": "홍길동",
                "competition_type": "",
                "competition_type_search": "신규 코딩 대회",
                "division": "초등부",
                "award_name": "금상",
                "organization": "메듀랩",
                "date_awarded": "2026-06-20",
                "content": "수상 내용",
            },
        )

        self.assertRedirects(response, reverse("board_awards"))
        award = Award.objects.get(student_name="홍길동")
        self.assertEqual(award.division, "초등부")
        self.assertIsNotNone(award.competition_type)
        self.assertEqual(award.competition_type.name, "신규 코딩 대회")
        self.assertEqual(award.competition_type.organization, "메듀랩")

    def test_create_award_shows_reason_when_competition_type_missing(self):
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse("board_awards_create"),
            {
                "student_name": "홍길동",
                "competition_type": "",
                "competition_type_search": "",
                "division": "초등부",
                "award_name": "금상",
                "organization": "메듀랩",
                "date_awarded": "2026-06-20",
                "content": "수상 내용",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "저장하지 못했습니다. 아래 항목을 확인해 주세요.")
        self.assertContains(response, "대회종류를 선택하거나 새 대회종류명을 입력해 주세요.")
        self.assertEqual(Award.objects.count(), 0)
        self.assertEqual(CompetitionType.objects.count(), 0)
