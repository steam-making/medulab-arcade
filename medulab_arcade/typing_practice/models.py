from django.contrib.auth.models import User
from django.db import models


PRACTICE_TYPE_CHOICES = [
    ("key", "자리연습"),
    ("word", "단어연습"),
    ("short", "짧은글연습"),
    ("long", "긴글연습"),
]

RANKING_PRACTICE_TYPE_CHOICES = [
    ("word", "단어연습"),
    ("short", "짧은글연습"),
    ("long", "긴글연습"),
]

LANGUAGE_CHOICES = [
    ("ko", "한국어"),
    ("en", "영어"),
    ("ja", "일본어"),
    ("zh", "중국어"),
]

AGE_GROUP_CHOICES = [
    ("seed", "새싹부"),
    ("growth", "성장부"),
    ("challenge", "챌린지부"),
]

MASTER_CATEGORY_CHOICES = [
    ("peak_speed", "최강타속마스터"),
    ("avg_speed", "안정타속마스터"),
    ("accuracy", "정확도마스터"),
    ("stamina", "끈기마스터"),
]


class TypingScore(models.Model):
    PRACTICE_TYPES = PRACTICE_TYPE_CHOICES
    LANGUAGES = LANGUAGE_CHOICES

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="typing_scores")
    practice_type = models.CharField("연습 유형", max_length=10, choices=PRACTICE_TYPES)
    language = models.CharField("언어", max_length=10, choices=LANGUAGES)
    score = models.IntegerField("점수", default=0)
    speed = models.IntegerField("타속(WPM)", default=0)
    accuracy = models.FloatField("정확도(%)", default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-score", "-speed", "-created_at"]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.get_practice_type_display()}({self.get_language_display()}): {self.score}"
        )


class TypingHallOfFame(models.Model):
    language = models.CharField("언어", max_length=10, choices=LANGUAGE_CHOICES, default="ko")
    practice_type = models.CharField(
        "연습 유형",
        max_length=10,
        choices=RANKING_PRACTICE_TYPE_CHOICES,
        blank=True,
        null=True,
    )
    category = models.CharField("레전드 부문", max_length=20, choices=MASTER_CATEGORY_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="typing_legends")
    record_value = models.FloatField("기록 값", default=0)
    score = models.IntegerField("점수", default=0)
    speed = models.IntegerField("타속", default=0)
    accuracy = models.FloatField("정확도", default=0)
    quarter_key = models.CharField("갱신 분기", max_length=10, blank=True)
    achieved_at = models.DateTimeField("기록 일시")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "타자 명예의 전당"
        verbose_name_plural = "타자 명예의 전당"
        unique_together = ("language", "practice_type", "category")

    def __str__(self):
        practice_name = self.get_practice_type_display() if self.practice_type else "통합"
        return f"{practice_name} {self.get_category_display()} - {self.user.username}"


class TypingContent(models.Model):
    CONTENT_TYPES = [
        ("word", "단어"),
        ("short", "짧은글"),
        ("long", "긴글"),
    ]
    LANGUAGES = LANGUAGE_CHOICES

    content_type = models.CharField("콘텐츠 유형", max_length=10, choices=CONTENT_TYPES)
    language = models.CharField("기본 언어", max_length=10, choices=LANGUAGES, default="ko")
    emoji = models.CharField("이모지", max_length=10, blank=True, default="⌨️")
    title = models.CharField("제목", max_length=100, blank=True, help_text="연습 주제 또는 제목")
    text_ko = models.TextField(
        "한국어 내용",
        blank=True,
        null=True,
        help_text="단어는 쉼표나 줄바꿈으로, 문장은 줄바꿈으로 구분하세요.",
    )
    text_en = models.TextField("영어 내용", blank=True, null=True)
    text_ja = models.TextField("일본어 내용", blank=True, null=True)
    text_zh = models.TextField("중국어 내용", blank=True, null=True)
    text = models.TextField("내용(구버전)", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "타자연습 콘텐츠"
        verbose_name_plural = "타자연습 콘텐츠 목록"

    def __str__(self):
        preview = self.title or self.text_ko or self.text or "내용 없음"
        return f"[{self.get_content_type_display()}] {preview[:20]}"
