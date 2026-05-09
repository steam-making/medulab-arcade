from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

class ProgramType(models.Model):
    name = models.CharField("프로그램 유형", max_length=50, unique=True)
    order = models.PositiveIntegerField("정렬 순서", default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "프로그램 유형"
        verbose_name_plural = "프로그램 유형 목록"

    def __str__(self):
        return self.name

class LearningProgram(models.Model):
    name = models.CharField("과정명", max_length=100)
    description = models.TextField("과정 설명", blank=True)
    image = models.ImageField("대표 이미지", upload_to="learning_programs/", blank=True, null=True)
    picture_zip = models.FileField("picture.zip", upload_to="learning_programs/picture_zips/", blank=True, null=True)
    answer_zip = models.FileField("answer.zip", upload_to="learning_programs/answer_zips/", blank=True, null=True)
    program_type = models.ForeignKey(
        ProgramType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="learning_programs",
        verbose_name="유형"
    )
    is_active = models.BooleanField("활성화 여부", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_url(self):
        return reverse("course_home", args=[self.id])

    def __str__(self):
        return self.name


class AnswerZipImportBatch(models.Model):
    STATUS_PREVIEW = "preview"
    STATUS_APPLIED = "applied"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PREVIEW, "미리보기"),
        (STATUS_APPLIED, "적용 완료"),
        (STATUS_FAILED, "실패"),
    ]

    program = models.ForeignKey(LearningProgram, on_delete=models.CASCADE, related_name="answer_zip_import_batches")
    zip_file = models.FileField("answer.zip", upload_to="learning_programs/answer_zip_imports/%Y/%m/", blank=True, null=True)
    import_rule = models.CharField("가져오기 규칙", max_length=50, default="top_level_folder_chapter")
    status = models.CharField("상태", max_length=20, choices=STATUS_CHOICES, default=STATUS_PREVIEW)
    preview_data = models.JSONField("미리보기 데이터", default=dict, blank=True)
    message = models.TextField("처리 메시지", blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="answer_zip_import_batches", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    applied_at = models.DateTimeField("적용일", blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "정답 ZIP 가져오기 배치"
        verbose_name_plural = "정답 ZIP 가져오기 배치"

    def __str__(self):
        return f"{self.program.name} - {self.status}"

class Chapter(models.Model):
    program = models.ForeignKey(LearningProgram, on_delete=models.CASCADE, related_name="chapters")
    number = models.PositiveIntegerField("장 번호")  # 1, 2, 3...
    title = models.CharField("장 제목", max_length=200, blank=True)
    content = models.TextField("장 설명", blank=True, null=True)

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"{self.program.name} - {self.number}장: {self.title}"

class Item(models.Model):
    ITEM_TYPES = [
        ('example', '예제'),
        ('objective', '객관식'),
        ('problem', '실습문제'),
        ('project', '프로젝트'),
        ('homework', '과제'),
    ]
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="items")
    number = models.PositiveIntegerField("항목 순서", default=1)
    key = models.CharField("키워드/ID", max_length=100, help_text="예: ex01, prob02")
    title = models.CharField("제목", max_length=200)
    item_type = models.CharField("유형", max_length=50, choices=ITEM_TYPES, default='example')
    explain_html = models.TextField("설명 (HTML 가능)", blank=True, null=True)
    hint = models.TextField("힌트", blank=True, null=True)
    answer_code = models.TextField("정답 코드", blank=True, null=True)
    example_input = models.TextField("테스트용 입력값", blank=True, null=True)
    expected_output = models.TextField("예상 출력값", blank=True, null=True)
    due_date = models.DateTimeField("제출 기한", blank=True, null=True)

    class Meta:
        ordering = ["chapter", "number"]

    def __str__(self):
        return f"{self.chapter.number}장-{self.number}: {self.title}"

class LearningEnrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="learning_enrollments")
    program = models.ForeignKey(LearningProgram, on_delete=models.CASCADE, related_name="enrollments")
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'program')

    def __str__(self):
        return f"{self.user.username} - {self.program.name}"

class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="learning_progress")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="user_progress")
    code = models.TextField("제출한 코드", blank=True)
    last_output = models.TextField("마지막 출력", blank=True)
    score = models.IntegerField("점수", default=0)
    completed = models.BooleanField("완료 여부", default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'item')

    def __str__(self):
        return f"{self.user.username} - {self.item.title} ({'O' if self.completed else 'X'})"

class HomeworkAssignment(models.Model):
    program = models.ForeignKey(LearningProgram, on_delete=models.CASCADE, related_name="assignments", verbose_name="관련 과정")
    title = models.CharField("숙제 제목", max_length=200)
    description = models.TextField("설명", blank=True)
    assigned_users = models.ManyToManyField(User, related_name="assigned_homeworks", verbose_name="배정된 학생들", blank=True)
    linked_items = models.ManyToManyField(Item, related_name="assignments", verbose_name="연결된 문제들", blank=True)
    external_url = models.URLField("외부 URL", blank=True, null=True)
    due_date = models.DateTimeField("제출 기한", blank=True, null=True)
    is_active = models.BooleanField("활성화 여부", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['due_date', '-created_at']
        verbose_name = "과제(홈플레이)"
        verbose_name_plural = "과제 목록"

    def __str__(self):
        return f"[{self.program.name}] {self.title}"


class HomeworkAttachment(models.Model):
    assignment = models.ForeignKey(HomeworkAssignment, on_delete=models.CASCADE, related_name="attachments")
    title = models.CharField("파일명", max_length=200, blank=True)
    file = models.FileField("첨부 파일", upload_to="homework/attachments/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at"]
        verbose_name = "숙제 첨부 파일"
        verbose_name_plural = "숙제 첨부 파일"

    def __str__(self):
        return self.title or self.file.name.split("/")[-1]


class HomeworkSubmission(models.Model):
    STATUS_SUBMITTED = "submitted"
    STATUS_REVISION = "revision"
    STATUS_COMPLETED = "completed"
    STATUS_CHOICES = [
        (STATUS_SUBMITTED, "제출 완료"),
        (STATUS_REVISION, "보완 필요"),
        (STATUS_COMPLETED, "평가 완료"),
    ]

    assignment = models.ForeignKey(HomeworkAssignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="homework_submissions")
    file = models.FileField("제출 파일", upload_to="homework/submissions/%Y/%m/")
    note = models.TextField("학생 메모", blank=True)
    status = models.CharField("제출 상태", max_length=20, choices=STATUS_CHOICES, default=STATUS_SUBMITTED)
    teacher_comment = models.TextField("관리자 평가", blank=True)
    submitted_at = models.DateTimeField("제출일", auto_now_add=True)
    reviewed_at = models.DateTimeField("평가일", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        unique_together = ("assignment", "student")
        verbose_name = "숙제 제출"
        verbose_name_plural = "숙제 제출"

    def __str__(self):
        return f"{self.assignment.title} - {self.student.username}"
