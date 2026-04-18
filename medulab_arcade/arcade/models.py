import os
import uuid
import zipfile
import shutil
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.db.models.signals import post_save
from django.dispatch import receiver


# ────────────────────────────────────────────────
# 사용자 프로필 (회원 유형 & 승인 관리)
# ────────────────────────────────────────────────
class UserProfile(models.Model):
    USER_TYPE_CHOICES = [
        ('student', '학생회원'),
        ('general', '일반회원'),
        ('medulab_member', '메듀랩회원'),
        ('medulab_teacher', '메듀랩강사'),
        ('medulab_staff', '메듀랩스탭'),
    ]

    # 자동 승인 대상 유형
    AUTO_APPROVE_TYPES = ('student', 'general')
    # 정회원(교육 프로그램 + 기록 저장 사용 가능) 유형
    FULL_ACCESS_TYPES = ('medulab_member', 'medulab_teacher', 'medulab_staff')

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    nickname = models.CharField('닉네임', max_length=30, blank=True, help_text='표시용 이름입니다. 미설정 시 아이디가 사용됩니다.')
    user_type = models.CharField('회원 유형', max_length=20, choices=USER_TYPE_CHOICES, default='general')
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
        """정회원 여부: 메듀랩 계열이면서 승인된 경우"""
        return self.user_type in self.FULL_ACCESS_TYPES and self.is_approved

    @property
    def needs_approval(self):
        """승인 대기 상태인지"""
        return self.user_type in self.FULL_ACCESS_TYPES and not self.is_approved


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """User 생성 시 프로필 자동 생성"""
    if created and not hasattr(instance, '_skip_profile'):
        UserProfile.objects.get_or_create(user=instance)


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
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='제작자')
    author_display_name = models.CharField('표시 이름 (예: 김민준 중2)', max_length=50)
    categories = models.ManyToManyField(Category, blank=True, verbose_name='카테고리')
    tags = models.ManyToManyField(Tag, blank=True, verbose_name='태그')

    thumbnail   = models.ImageField('썸네일 1', upload_to=project_thumbnail_path, blank=True, null=True)
    thumbnail_2 = models.ImageField('썸네일 2', upload_to=project_thumbnail_path, blank=True, null=True)
    thumbnail_3 = models.ImageField('썸네일 3', upload_to=project_thumbnail_path, blank=True, null=True)
    thumbnail_emoji = models.CharField('썸네일 이모지 (이미지 없을 때)', max_length=10, default='🎮')
    color = models.CharField('카드 배경색', max_length=7, default='#1a1a2e')
    accent = models.CharField('포인트 색상', max_length=7, default='#e94560')

    # 작품 파일 (ZIP 업로드 → 서버에서 압축 해제)
    project_zip = models.FileField('작품 파일 (ZIP)', upload_to=project_zip_path, blank=True, null=True)
    entry_file = models.CharField('시작 파일명', max_length=100, default='index.html',
                                  help_text='ZIP 안의 메인 파일명 (예: index.html)')
    project_path = models.CharField('압축 해제 경로', max_length=300, blank=True)
    
    # 외부 링크 (대용량 파일 공유용)
    external_url = models.URLField('외부 링크 URL', max_length=500, blank=True, null=True,
                                   help_text='대용량 파일 다운로드 링크 (원드라이브 공유 링크 등)')

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

        # ZIP 파일이 변경되었는지 확인 (수정 시)
        if self.pk:
            try:
                old_instance = Project.objects.get(pk=self.pk)
                if old_instance.project_zip != self.project_zip:
                    self.project_path = ''  # 재압축 해제 유도
            except Project.DoesNotExist:
                pass

        super().save(*args, **kwargs)
        # ZIP 파일 압축 해제
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
            # zipfile 객체에 파일 객체를 전달하여 더 안전하게 접근
            zip_file = self.project_zip.open('rb')
            try:
                zip_file.seek(0)
                with zipfile.ZipFile(zip_file) as zf:
                    zf.extractall(extract_dir)
            finally:
                zip_file.close()

            # 압축 해제 성공 시 원본 ZIP의 물리 경로 미리 확보
            try:
                zip_path = self.project_zip.path
            except ValueError:
                zip_path = None
            
            # DB 업데이트 (경로 저장 및 원본 ZIP 필드 비우기)
            self.project_path = f'projects/{self.slug}'
            Project.objects.filter(pk=self.pk).update(
                project_path=self.project_path,
                project_zip=None
            )
            
            # 서버 물리 파일 삭제 (용량 절약)
            if zip_path and os.path.exists(zip_path):
                try:
                    os.remove(zip_path)
                except OSError:
                    pass
                
        except Exception as e:
            print(f'ZIP 압축 해제 오류: {e}')

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
        # 1. 압축 해제된 폴더 삭제
        if self.project_path:
            extract_dir = os.path.join(settings.MEDIA_ROOT, self.project_path)
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)

        # 2. 관련 파일 삭제 (ZIP, 썸네일)
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

        # 3. DB 레코드 삭제
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
