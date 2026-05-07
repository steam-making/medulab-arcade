import os
import secrets
import shutil
import uuid
import zipfile
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import slugify


class UserProfile(models.Model):
    USER_TYPE_CHOICES = [
        ('student', '학생회원'),
        ('general', '일반회원'),
        ('medulab_member', '메듀랩 회원'),
        ('medulab_teacher', '메듀랩 강사'),
        ('medulab_staff', '메듀랩 스탭'),
    ]

    AUTO_APPROVE_TYPES = ('student', 'general')
    FULL_ACCESS_TYPES = ('medulab_member', 'medulab_teacher', 'medulab_staff')

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    real_name = models.CharField('이름', max_length=20, blank=True)
    birth_date = models.DateField('생년월일', null=True, blank=True)
    phone_number = models.CharField('전화번호', max_length=20, blank=True)
    nickname = models.CharField(
        '닉네임',
        max_length=30,
        blank=True,
        help_text='표시할 이름입니다. 비워 두면 이름, 그다음 아이디를 사용합니다.',
    )
    user_type = models.CharField(
        '회원 유형',
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='general',
    )
    is_approved = models.BooleanField('승인 여부', default=False)
    approved_at = models.DateTimeField('승인일시', null=True, blank=True)
    created_at = models.DateTimeField('가입일', auto_now_add=True)

    class Meta:
        verbose_name = '사용자 프로필'
        verbose_name_plural = '사용자 프로필'

    def __str__(self):
        return f'{self.user.username} ({self.get_user_type_display()})'

    @property
    def is_full_member(self):
        return self.user_type in self.FULL_ACCESS_TYPES and self.is_approved

    @property
    def needs_approval(self):
        return self.user_type in self.FULL_ACCESS_TYPES and not self.is_approved

    @property
    def display_name(self):
        return self.nickname or self.real_name or self.user.username


class Badge(models.Model):
    CATEGORY_TYPING = 'typing'
    CATEGORY_LEARNING = 'learning'
    CATEGORY_MILESTONE = 'milestone'
    CATEGORY_CHOICES = [
        (CATEGORY_TYPING, '타자연습'),
        (CATEGORY_LEARNING, '학습과정'),
        (CATEGORY_MILESTONE, '성장기록'),
    ]

    code = models.CharField('배지 코드', max_length=120, unique=True)
    name = models.CharField('배지명', max_length=100)
    description = models.TextField('설명', blank=True)
    icon = models.CharField('아이콘', max_length=10, default='🏅')
    color = models.CharField('포인트 색상', max_length=7, default='#f5c451')
    category = models.CharField('배지 분류', max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_MILESTONE)
    criteria_type = models.CharField('획득 조건 유형', max_length=50, blank=True)
    criteria_value = models.PositiveIntegerField('획득 조건 값', default=1)
    related_program = models.ForeignKey(
        'courses.LearningProgram',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='completion_badges',
        verbose_name='연결 과정',
    )
    is_active = models.BooleanField('활성화 여부', default=True)
    sort_order = models.PositiveIntegerField('정렬 순서', default=0)
    created_at = models.DateTimeField('생성일', auto_now_add=True)

    class Meta:
        verbose_name = '배지'
        verbose_name_plural = '배지'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earned_badges', verbose_name='사용자')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='awarded_users', verbose_name='배지')
    awarded_at = models.DateTimeField('획득일', auto_now_add=True)

    class Meta:
        verbose_name = '사용자 배지'
        verbose_name_plural = '사용자 배지'
        ordering = ['-awarded_at']
        unique_together = ('user', 'badge')

    def __str__(self):
        return f'{self.user.username} - {self.badge.name}'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not hasattr(instance, '_skip_profile'):
        UserProfile.objects.get_or_create(user=instance)


class EmailChangeRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_change_requests')
    new_email = models.EmailField('새 이메일 주소')
    token = models.CharField(max_length=64, unique=True, db_index=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']
        verbose_name = '이메일 변경 요청'
        verbose_name_plural = '이메일 변경 요청'

    def __str__(self):
        return f'{self.user.username} -> {self.new_email}'

    @classmethod
    def issue(cls, user, new_email, hours=24):
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        return cls.objects.create(
            user=user,
            new_email=new_email,
            token=secrets.token_urlsafe(32),
            expires_at=timezone.now() + timedelta(hours=hours),
        )

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at


class SignupEmailVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='signup_email_verifications')
    token = models.CharField(max_length=64, unique=True, db_index=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']
        verbose_name = '가입 이메일 인증'
        verbose_name_plural = '가입 이메일 인증'

    def __str__(self):
        return f'{self.user.username} signup verification'

    @classmethod
    def issue(cls, user, hours=24):
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        return cls.objects.create(
            user=user,
            token=secrets.token_urlsafe(32),
            expires_at=timezone.now() + timedelta(hours=hours),
        )

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at


def project_thumbnail_path(instance, filename):
    ext = filename.split('.')[-1]
    return f'thumbnails/{instance.slug}_{uuid.uuid4().hex[:8]}.{ext}'


def project_zip_path(instance, filename):
    return f'uploads/{instance.slug}_{uuid.uuid4().hex[:8]}.zip'


class Category(models.Model):
    name = models.CharField('카테고리명', max_length=50)
    icon = models.CharField('아이콘(이모지)', max_length=10, default='🎮')
    order = models.IntegerField('정렬순서', default=0)

    class Meta:
        verbose_name = '카테고리'
        verbose_name_plural = '카테고리'
        ordering = ['order']

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField('태그명', max_length=30, unique=True)

    class Meta:
        verbose_name = '태그'
        verbose_name_plural = '태그'

    def __str__(self):
        return self.name


class Project(models.Model):
    STATUS_CHOICES = [
        ('pending', '심사중'),
        ('approved', '승인됨'),
        ('rejected', '반려됨'),
    ]

    title = models.CharField('작품명', max_length=100)
    slug = models.CharField('슬러그', max_length=120, unique=True, blank=True)
    description = models.TextField('작품 소개', max_length=500)
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='작성자')
    author_display_name = models.CharField('표시 이름 (예: 김민준 중2)', max_length=50)
    categories = models.ManyToManyField(Category, blank=True, verbose_name='카테고리')
    tags = models.ManyToManyField(Tag, blank=True, verbose_name='태그')

    thumbnail = models.ImageField('썸네일 1', upload_to=project_thumbnail_path, blank=True, null=True)
    thumbnail_2 = models.ImageField('썸네일 2', upload_to=project_thumbnail_path, blank=True, null=True)
    thumbnail_3 = models.ImageField('썸네일 3', upload_to=project_thumbnail_path, blank=True, null=True)
    thumbnail_emoji = models.CharField('썸네일 이모지', max_length=10, default='🎮')
    color = models.CharField('카드 배경색', max_length=7, default='#1a1a2e')
    accent = models.CharField('포인트 색상', max_length=7, default='#e94560')

    project_zip = models.FileField('작품 파일(ZIP)', upload_to=project_zip_path, blank=True, null=True)
    entry_file = models.CharField(
        '시작 파일명',
        max_length=100,
        default='index.html',
        help_text='ZIP 내부의 메인 파일명(예: index.html)',
    )
    project_path = models.CharField('압축 해제 경로', max_length=300, blank=True)
    external_url = models.URLField(
        '외부 링크 URL',
        max_length=500,
        blank=True,
        null=True,
        help_text='드라이브나 외부 저장소의 공유 링크를 사용할 수 있습니다.',
    )

    status = models.CharField('상태', max_length=10, choices=STATUS_CHOICES, default='pending')
    is_featured = models.BooleanField('추천 작품', default=False)
    play_count = models.PositiveIntegerField('플레이 수', default=0)

    created_at = models.DateTimeField('등록일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)

    class Meta:
        verbose_name = '학생 작품'
        verbose_name_plural = '학생 작품'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} - {self.author_display_name}'

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title, allow_unicode=True)
            if not base_slug:
                base_slug = uuid.uuid4().hex[:8]
            slug = base_slug
            counter = 1
            while Project.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug

        if self.pk:
            try:
                old_instance = Project.objects.get(pk=self.pk)
                if old_instance.project_zip != self.project_zip:
                    self.project_path = ''
            except Project.DoesNotExist:
                pass

        super().save(*args, **kwargs)
        if self.project_zip and not self.project_path:
            self._extract_zip()

    def _extract_zip(self):
        if not self.project_zip:
            return

        extract_dir = os.path.join(settings.MEDIA_ROOT, 'projects', self.slug)
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        os.makedirs(extract_dir, exist_ok=True)

        try:
            zip_file = self.project_zip.open('rb')
            try:
                zip_file.seek(0)
                with zipfile.ZipFile(zip_file) as zf:
                    zf.extractall(extract_dir)
            finally:
                zip_file.close()

            try:
                zip_path = self.project_zip.path
            except ValueError:
                zip_path = None

            self.project_path = f'projects/{self.slug}'
            Project.objects.filter(pk=self.pk).update(
                project_path=self.project_path,
                project_zip=None,
            )

            if zip_path and os.path.exists(zip_path):
                try:
                    os.remove(zip_path)
                except OSError:
                    pass
        except Exception as exc:
            print(f'ZIP 압축 해제 오류: {exc}')

    @property
    def play_url(self):
        if self.external_url:
            return self.external_url
        if self.project_path:
            return f'{settings.MEDIA_URL}{self.project_path}/{self.entry_file}'
        return ''

    @property
    def like_count(self):
        return self.likes.count()

    @property
    def bookmark_count(self):
        return self.bookmarks.count()

    def delete(self, *args, **kwargs):
        if self.project_path:
            extract_dir = os.path.join(settings.MEDIA_ROOT, self.project_path)
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)

        try:
            if self.project_zip and self.project_zip.path and os.path.isfile(self.project_zip.path):
                os.remove(self.project_zip.path)
        except (ValueError, FileNotFoundError):
            pass

        for thumb_field in (self.thumbnail, self.thumbnail_2, self.thumbnail_3):
            try:
                if thumb_field and thumb_field.path and os.path.isfile(thumb_field.path):
                    os.remove(thumb_field.path)
            except (ValueError, FileNotFoundError):
                pass

        super().delete(*args, **kwargs)


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'project')
        verbose_name = '좋아요'
        verbose_name_plural = '좋아요'


class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'project')
        verbose_name = '즐겨찾기'
        verbose_name_plural = '즐겨찾기'
