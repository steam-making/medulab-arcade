from django.db import models
from django.contrib.auth.models import User

class TypingScore(models.Model):
    PRACTICE_TYPES = [
        ('key', '자리연습'),
        ('word', '단어연습'),
        ('short', '짧은글연습'),
        ('long', '긴글연습'),
    ]
    LANGUAGES = [
        ('ko', '한국어'),
        ('en', '영어'),
        ('ja', '일본어'),
        ('zh', '중국어'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='typing_scores')
    practice_type = models.CharField("연습 유형", max_length=10, choices=PRACTICE_TYPES)
    language = models.CharField("언어", max_length=10, choices=LANGUAGES)
    
    score = models.IntegerField("점수", default=0)
    speed = models.IntegerField("타수 (WPM)", default=0)
    accuracy = models.FloatField("정확도 (%)", default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-score', '-speed', '-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_practice_type_display()}({self.get_language_display()}): {self.score}점"

class TypingContent(models.Model):
    CONTENT_TYPES = [
        ('word', '단어'),
        ('short', '짧은글'),
        ('long', '긴글'),
    ]
    LANGUAGES = [
        ('ko', '한국어'),
        ('en', '영어'),
        ('ja', '일본어'),
        ('zh', '중국어'),
    ]

    content_type = models.CharField("콘텐츠 유형", max_length=10, choices=CONTENT_TYPES)
    language = models.CharField("기본 언어", max_length=10, choices=LANGUAGES, default='ko')
    emoji = models.CharField("이모지", max_length=10, blank=True, default="⌨️")
    title = models.CharField("제목", max_length=100, blank=True, help_text="연습 주제 또는 제목")
    
    # 다국어 텍스트 필드
    text_ko = models.TextField("한국어 내용", blank=True, null=True, help_text="단어는 쉼표나 줄바꿈으로 구분, 문장은 줄바꿈으로 구분하세요.")
    text_en = models.TextField("영어 내용", blank=True, null=True)
    text_ja = models.TextField("일본어 내용", blank=True, null=True)
    text_zh = models.TextField("중국어 내용", blank=True, null=True)
    
    # 하위 호환성을 위해 유지 (마이그레이션 후 삭제 고려)
    text = models.TextField("내용(구)", blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "타자연습 콘텐츠"
        verbose_name_plural = "타자연습 콘텐츠 목록"

    def __str__(self):
        return f"[{self.get_content_type_display()}] {self.title or self.text_ko[:20] or '내용 없음'}"
