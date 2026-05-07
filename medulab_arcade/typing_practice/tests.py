from datetime import date

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone

from typing_practice.models import TypingHallOfFame, TypingScore, TypingUnlockProgress
from typing_practice.views import (
    get_age_group_for_user,
    get_current_quarter_info,
    update_hall_of_fame_for_language,
)


class TypingRankingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.seed_user = User.objects.create_user(username="seed", password="pw")
        self.seed_user.profile.birth_date = date(2018, 5, 1)
        self.seed_user.profile.save()

        self.growth_user = User.objects.create_user(username="growth", password="pw")
        self.growth_user.profile.birth_date = date(2014, 7, 1)
        self.growth_user.profile.save()

        self.challenge_user = User.objects.create_user(username="challenge", password="pw")
        self.challenge_user.profile.birth_date = date(2008, 3, 1)
        self.challenge_user.profile.save()

    def test_age_group_uses_birth_year_estimate(self):
        today = date(2026, 4, 22)
        self.assertEqual(get_age_group_for_user(self.seed_user, today=today), "seed")
        self.assertEqual(get_age_group_for_user(self.growth_user, today=today), "growth")
        self.assertEqual(get_age_group_for_user(self.challenge_user, today=today), "challenge")

    def test_hall_of_fame_updates_with_best_records(self):
        quarter = get_current_quarter_info()
        now = timezone.now()

        TypingScore.objects.create(
            user=self.seed_user,
            practice_type="word",
            language="ko",
            score=210,
            speed=320,
            accuracy=97.5,
            created_at=now,
        )
        TypingScore.objects.create(
            user=self.growth_user,
            practice_type="word",
            language="ko",
            score=250,
            speed=330,
            accuracy=96.0,
            created_at=now,
        )
        TypingScore.objects.create(
            user=self.challenge_user,
            practice_type="short",
            language="ko",
            score=500,
            speed=290,
            accuracy=99.0,
            created_at=now,
        )

        update_hall_of_fame_for_language("ko", quarter)

        peak = TypingHallOfFame.objects.get(language="ko", practice_type="word", category="peak_speed")
        stamina = TypingHallOfFame.objects.get(language="ko", practice_type=None, category="stamina")

        self.assertEqual(peak.user, self.growth_user)
        self.assertEqual(stamina.user, self.challenge_user)
        self.assertEqual(stamina.quarter_key, quarter["key"])

    def test_ranking_page_loads_with_filters(self):
        self.client.force_login(self.growth_user)
        response = self.client.get("/typing/ranking/", {
            "lang": "ko",
            "group": "growth",
            "practice": "word",
            "category": "peak_speed",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "명예의 전당")

    def test_save_score_merges_authenticated_unlock_progress(self):
        self.client.force_login(self.growth_user)
        response = self.client.post(
            "/typing/api/save-score/",
            data={
                "type": "key",
                "lang": "ko",
                "score": 900,
                "speed": 90,
                "accuracy": 91,
                "unlocks": {
                    "key_levels": ["home", "top", "bottom", "number", "shift", "all"],
                    "word_unlocked": True,
                    "short_unlocked": False,
                    "long_unlocked": False,
                },
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        progress = TypingUnlockProgress.objects.get(user=self.growth_user, language="ko")
        self.assertEqual(progress.key_levels, ["home", "top", "bottom", "number", "shift", "all"])
        self.assertTrue(progress.word_unlocked)

        response = self.client.post(
            "/typing/api/save-score/",
            data={
                "type": "short",
                "lang": "ko",
                "score": 3600,
                "speed": 450,
                "accuracy": 98,
                "unlocks": {
                    "key_levels": ["home"],
                    "word_unlocked": False,
                    "short_unlocked": False,
                    "long_unlocked": True,
                },
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        progress.refresh_from_db()
        self.assertEqual(progress.key_levels, ["home", "top", "bottom", "number", "shift", "all"])
        self.assertTrue(progress.word_unlocked)
        self.assertTrue(progress.long_unlocked)

    def test_typing_home_renders_server_unlock_state_for_authenticated_user(self):
        TypingUnlockProgress.objects.create(
            user=self.growth_user,
            language="ko",
            key_levels=["home", "top", "bottom", "number", "shift", "all"],
            word_unlocked=True,
            short_unlocked=True,
        )
        self.client.force_login(self.growth_user)

        response = self.client.get("/typing/?lang=ko")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"short_unlocked": true')
