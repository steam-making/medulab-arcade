import os
import secrets
import shutil
import uuid
import zipfile
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.signals import user_logged_in
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


class ScheduleEvent(models.Model):
    EVENT_TYPE_HOLIDAY = 'holiday'
    EVENT_TYPE_ACADEMIC = 'academic'
    EVENT_TYPE_COMPETITION = 'competition'
    EVENT_TYPE_SEMINAR = 'seminar'
    EVENT_TYPE_CERTIFICATION = 'certification'
    EVENT_TYPE_CHOICES = [
        (EVENT_TYPE_HOLIDAY, '휴원'),
        (EVENT_TYPE_ACADEMIC, '정규수업'),
        (EVENT_TYPE_SEMINAR, '특강/세미나'),
        (EVENT_TYPE_COMPETITION, '대회'),
        (EVENT_TYPE_CERTIFICATION, '자격시험'),
    ]

    title = models.CharField('일정명', max_length=120)
    description = models.TextField('상세 설명', blank=True)
    
    # 일반 일정용 (대회, 특강 등)
    start_date = models.DateTimeField('시작일시', null=True, blank=True)
    end_date = models.DateTimeField('종료일시', null=True, blank=True)
    
    # 정규수업 등 반복 일정용
    days_of_week = models.CharField('반복 요일', max_length=50, blank=True, help_text='0:일, 1:월, 2:화, 3:수, 4:목, 5:금, 6:토 (콤마로 구분)')
    start_time = models.TimeField('시작 시간', null=True, blank=True)
    end_time = models.TimeField('종료 시간', null=True, blank=True)

    event_type = models.CharField('일정 유형', max_length=20, choices=EVENT_TYPE_CHOICES, default=EVENT_TYPE_ACADEMIC)
    external_url = models.URLField('링크 URL', max_length=500, blank=True, help_text='대회페이지나 관련 자료 링크')
    image = models.ImageField('이미지 (포스터)', upload_to='schedule/posters/', blank=True, null=True)
    is_active = models.BooleanField('노출 여부', default=True)

    class Meta:
        verbose_name = '학원 일정'
        verbose_name_plural = '학원 일정'
        ordering = ['start_date', 'start_time', 'title']

    def __str__(self):
        if self.start_date:
            return f'{self.title} ({self.start_date:%Y.%m.%d %H:%M})'
        elif self.start_time:
            return f'{self.title} (반복: {self.start_time:%H:%M})'
        return self.title


class ScheduleAttachment(models.Model):
    event = models.ForeignKey(ScheduleEvent, on_delete=models.CASCADE, related_name='attachments', verbose_name='일정')
    file = models.FileField('첨부 파일', upload_to='schedule/attachments/')
    uploaded_at = models.DateTimeField('등록일', auto_now_add=True)

    class Meta:
        verbose_name = '첨부 파일'
        verbose_name_plural = '첨부 파일'
        ordering = ['uploaded_at']

    def __str__(self):
        return self.file.name.split('/')[-1]


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


class Notice(models.Model):
    title = models.CharField('제목', max_length=200)
    content = models.TextField('내용')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='작성자')
    created_at = models.DateTimeField('작성일', auto_now_add=True)
    updated_at = models.DateTimeField('수정일', auto_now=True)
    view_count = models.PositiveIntegerField('조회수', default=0)
    is_pinned = models.BooleanField('상단 고정', default=False)
    attachment = models.FileField('첨부파일', upload_to='notices/', blank=True, null=True)

    class Meta:
        verbose_name = '공지사항'
        verbose_name_plural = '공지사항'
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return self.title


class Award(models.Model):
    title = models.CharField('제목 (게시물용)', max_length=200, blank=True, null=True)
    student_name = models.CharField('학생 이름', max_length=50)
    competition_type = models.ForeignKey(
        'CompetitionType',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='awards',
        verbose_name='대회종류'
    )
    competition_year = models.PositiveSmallIntegerField('대회년도', blank=True, null=True)
    competition_name = models.CharField('대회명', max_length=100)
    division = models.CharField('부문', max_length=100, blank=True, null=True)
    award_name = models.CharField('상격 (예: 대상, 금상)', max_length=50)
    organization = models.CharField('수여기관', max_length=100, blank=True, null=True)
    date_awarded = models.DateField('수상일자')
    thumbnail = models.ImageField('대표 이미지', upload_to='awards/', blank=True, null=True)
    content = models.TextField('내용', blank=True)
    created_at = models.DateTimeField('등록일', auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.competition_type:
            self.competition_name = self.competition_type.name
            if not self.organization and self.competition_type.organization:
                self.organization = self.competition_type.organization
        if not self.title:
            self.title = f"[{self.competition_name}] {self.student_name} {self.award_name} 수상"
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = '대회수상'
        verbose_name_plural = '대회수상'
        ordering = ['-date_awarded', '-created_at']

    def __str__(self):
        return f"{self.student_name} - {self.competition_name} ({self.award_name})"

    @property
    def masked_name(self):
        if not self.student_name:
            return ""
        if len(self.student_name) == 2:
            return self.student_name[0] + "*"
        elif len(self.student_name) > 2:
            return self.student_name[0] + "*" * (len(self.student_name) - 2) + self.student_name[-1]
        return self.student_name


class Certification(models.Model):
    title = models.CharField('제목 (게시물용)', max_length=200, blank=True, null=True)
    student_name = models.CharField('학생 이름', max_length=50)
    cert_info = models.ForeignKey(
        'CertInfo',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='certifications',
        verbose_name='자격종류'
    )
    cert_name = models.CharField('자격증명', max_length=100)
    issuer = models.CharField('발급기관', max_length=100, blank=True, null=True)
    date_acquired = models.DateField('취득일자')
    thumbnail = models.ImageField('자격증/배지 이미지', upload_to='certs/', blank=True, null=True)
    content = models.TextField('내용', blank=True)
    created_at = models.DateTimeField('등록일', auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.cert_info:
            self.cert_name = self.cert_info.name
            if not self.issuer and self.cert_info.issuer:
                self.issuer = self.cert_info.issuer
        if not self.title:
            self.title = f"[{self.cert_name}] {self.student_name} 자격 취득"
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = '자격취득'
        verbose_name_plural = '자격취득'
        ordering = ['-date_acquired', '-created_at']

    def __str__(self):
        return f"{self.student_name} - {self.cert_name}"

    @property
    def masked_name(self):
        if not self.student_name:
            return ""
        if len(self.student_name) == 2:
            return self.student_name[0] + "*"
        elif len(self.student_name) > 2:
            return self.student_name[0] + "*" * (len(self.student_name) - 2) + self.student_name[-1]
        return self.student_name


class CertInfo(models.Model):
    CATEGORY_CHOICES = [
        ('ai',           'AI'),
        ('block_coding', '블록코딩'),
        ('python',       '파이썬코딩'),
        ('robot',        '로봇'),
        ('doc_work',     '문서작업'),
    ]
    GRADE_KEYS = ['kids_5_7', 'elem_1_2', 'elem_3_4', 'elem_5_6', 'mid_high', 'adult']

    name = models.CharField('자격증명', max_length=100)
    display_name = models.CharField('카드 표시명', max_length=150, blank=True, default='',
        help_text='목록 카드에 표시할 이름 (비워두면 name 사용). 예) COS Entry 1~4급')
    is_national_cert = models.BooleanField('국가공인 자격증', default=False)
    issuer = models.CharField('발급기관', max_length=100, blank=True, null=True)
    description = models.TextField('자격내용 및 소개', blank=True, null=True)
    grade_info = models.JSONField('등급표 (JSON)', blank=True, null=True,
        help_text='[{"grade":"3급","content":"평가내용","target":"추천대상"}, ...]')
    thumbnail = models.ImageField('대표 이미지(로고 등)', upload_to='certinfo/', blank=True, null=True)
    link = models.URLField('관련 링크', blank=True, null=True)
    order = models.IntegerField('정렬순서', default=0)
    category = models.CharField('분류', max_length=20, choices=CATEGORY_CHOICES, blank=True, null=True)
    target_grades = models.CharField('대상 학년(콤마구분)', max_length=200, blank=True, default='',
        help_text='ex) elem_1_2,elem_3_4')
    created_at = models.DateTimeField('등록일', auto_now_add=True)

    class Meta:
        verbose_name = '자격종류'
        verbose_name_plural = '자격종류'
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.name

    def target_grade_list(self):
        return [g.strip() for g in self.target_grades.split(',') if g.strip()]


class CompetitionType(models.Model):
    name = models.CharField('대회명', max_length=100)
    organization = models.CharField('주최/주관', max_length=100, blank=True, null=True)
    description = models.TextField('대회 소개', blank=True, null=True)
    thumbnail = models.ImageField('대표 이미지(포스터/로고)', upload_to='competition_types/', blank=True, null=True)
    link = models.URLField('관련 링크', blank=True, null=True)
    order = models.IntegerField('정렬순서', default=0)
    created_at = models.DateTimeField('등록일', auto_now_add=True)

    class Meta:
        verbose_name = '대회종류'
        verbose_name_plural = '대회종류'
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.name


class Contest(models.Model):
    title = models.CharField('공모전명', max_length=200)
    organizer = models.CharField('주최/주관', max_length=100)
    category = models.CharField('분야', max_length=100, help_text='AI, 게임, 코딩, 로봇, 소프트웨어 등 콤마(,)로 구분')
    target_audience = models.CharField('참가 대상', max_length=100)
    start_date = models.DateField('접수 시작일', null=True, blank=True)
    end_date = models.DateField('접수 마감일', null=True, blank=True)
    thumbnail = models.ImageField('포스터/대표 이미지', upload_to='contests/', blank=True, null=True)
    link = models.URLField('관련 링크', blank=True, null=True)
    description = models.TextField('공모전 소개 및 상세 설명', blank=True)
    is_active = models.BooleanField('노출 여부', default=True)
    created_at = models.DateTimeField('등록일', auto_now_add=True)

    class Meta:
        verbose_name = '추천 공모전'
        verbose_name_plural = '추천 공모전'
        ordering = ['end_date', '-created_at']

    def __str__(self):
        return self.title

    @property
    def d_day(self):
        from django.utils import timezone
        import datetime
        if not self.end_date:
            return None
        today = timezone.localdate() if timezone.is_aware(timezone.now()) else datetime.date.today()
        delta = self.end_date - today
        return delta.days

    @property
    def category_list(self):
        if not self.category:
            return []
        return [c.strip() for c in self.category.split(',') if c.strip()]


class Attendance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendances', verbose_name='학생')
    date = models.DateField('출석일', default=timezone.localdate)
    is_present = models.BooleanField('출석 여부', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '출석 기록'
        verbose_name_plural = '출석 기록'
        unique_together = ('user', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.date:%Y-%m-%d} 출석"


class AvatarDraft(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='avatar_draft')
    data = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '아바타 임시저장'
        verbose_name_plural = '아바타 임시저장'

    def __str__(self):
        return f"{self.user.username} 아바타 초안"


@receiver(user_logged_in)
def auto_attendance_on_login(sender, request, user, **kwargs):
    today = timezone.localdate()
    Attendance.objects.get_or_create(user=user, date=today)


class SiteConfig(models.Model):
    key = models.CharField('키', max_length=100, unique=True)
    value = models.TextField('값', blank=True)

    class Meta:
        verbose_name = '사이트 설정'
        verbose_name_plural = '사이트 설정'

    def __str__(self):
        return self.key

    @classmethod
    def get_value(cls, key, default=None):
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_value(cls, key, value):
        cls.objects.update_or_create(key=key, defaults={'value': str(value)})

    @classmethod
    def delete_key(cls, key):
        cls.objects.filter(key=key).delete()


class NavItem(models.Model):
    SECTION_NOTICES = 'notices'
    SECTION_LEARNING = 'learning'
    SECTION_CHOICES = [
        (SECTION_NOTICES, '공지/일정'),
        (SECTION_LEARNING, '러닝센터'),
    ]

    section = models.CharField('섹션', max_length=20, choices=SECTION_CHOICES)
    emoji = models.CharField('이모지', max_length=10, default='')
    name = models.CharField('메뉴 이름', max_length=50)
    url_name = models.CharField('URL 이름', max_length=100, blank=True,
                                help_text='Django URL 이름 (예: board_notice, ai_favorites)')
    url_extra = models.CharField('URL 추가', max_length=200, blank=True,
                                 help_text='URL 뒤에 붙일 내용 (예: #works)')
    order = models.IntegerField('순서', default=0)
    is_active = models.BooleanField('활성화', default=True)
    is_accent = models.BooleanField('강조색 (노란색)', default=False)
    new_tab = models.BooleanField('새 탭으로 열기', default=False)

    class Meta:
        verbose_name = '네비게이션 메뉴'
        verbose_name_plural = '네비게이션 메뉴'
        ordering = ['section', 'order', 'id']

    def __str__(self):
        return f'[{self.get_section_display()}] {self.emoji} {self.name}'


from django.db.models.signals import post_delete

def _clear_nav_cache(sender, **kwargs):
    from django.core.cache import cache
    cache.delete('nav_items_qs')

post_save.connect(_clear_nav_cache, sender=NavItem)
post_delete.connect(_clear_nav_cache, sender=NavItem)


class ProblemRoom(models.Model):
    team_name = models.CharField('팀명', max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'problem_room'
        verbose_name = '문제찾기 팀방'
        verbose_name_plural = '문제찾기 팀방'

    def __str__(self):
        return self.team_name


class ProblemMember(models.Model):
    room = models.ForeignKey(ProblemRoom, on_delete=models.CASCADE, related_name='members', verbose_name='팀방')
    name = models.CharField('이름', max_length=20)
    session_key = models.CharField('세션키', max_length=64, db_index=True)
    is_leader = models.BooleanField('조장', default=False)
    data = models.JSONField('선택 데이터', default=dict)
    last_seen = models.DateTimeField('최근 접속', auto_now=True)

    class Meta:
        db_table = 'problem_member'
        verbose_name = '문제찾기 팀원'
        verbose_name_plural = '문제찾기 팀원'
        unique_together = [('room', 'session_key')]

    def __str__(self):
        return f"{self.room.team_name} - {self.name}"


# ── 작품 평가단 ──────────────────────────────────────────────

def _gallery_upload_path(instance, filename):
    return f'gallery/{instance.room_id}/{filename}'


class GalleryRoom(models.Model):
    STATUS = [('waiting', '대기중'), ('voting', '투표중'), ('done', '완료')]
    name = models.CharField('방 이름', max_length=50)
    status = models.CharField('상태', max_length=10, choices=STATUS, default='waiting')
    current_index = models.IntegerField('현재 포스터 인덱스', default=-1)
    vote_duration = models.IntegerField('평가 시간(초)', default=0)  # 0=무제한
    poster_started_at = models.DateTimeField('포스터 시작 시각', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'gallery_room'
        verbose_name = '작품 평가단 방'
        verbose_name_plural = '작품 평가단 방'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class GalleryPoster(models.Model):
    room = models.ForeignKey(GalleryRoom, on_delete=models.CASCADE, related_name='posters')
    image = models.ImageField('이미지', upload_to=_gallery_upload_path)
    title = models.CharField('제목', max_length=100, blank=True)
    order = models.PositiveIntegerField('순서', default=0)

    class Meta:
        db_table = 'gallery_poster'
        verbose_name = '포스터'
        verbose_name_plural = '포스터'
        ordering = ['order']

    def __str__(self):
        return f"{self.room.name} #{self.order}"


class GalleryCriteria(models.Model):
    room = models.ForeignKey(GalleryRoom, on_delete=models.CASCADE, related_name='criteria')
    name = models.CharField('항목명', max_length=50)
    description = models.CharField('설명', max_length=200, blank=True)
    max_score = models.PositiveIntegerField('배점', default=20)
    order = models.PositiveIntegerField('순서', default=0)

    class Meta:
        db_table = 'gallery_criteria'
        verbose_name = '평가항목'
        verbose_name_plural = '평가항목'
        ordering = ['order']

    def __str__(self):
        return f'{self.name} ({self.max_score}점)'


class GalleryMember(models.Model):
    room = models.ForeignKey(GalleryRoom, on_delete=models.CASCADE, related_name='members')
    name = models.CharField('이름', max_length=30)
    session_key = models.CharField('세션키', max_length=64)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'gallery_member'
        verbose_name = '평가단 참여자'
        verbose_name_plural = '평가단 참여자'
        unique_together = [('room', 'session_key')]

    def __str__(self):
        return f"{self.room.name} - {self.name}"


class GalleryVote(models.Model):
    poster = models.ForeignKey(GalleryPoster, on_delete=models.CASCADE, related_name='votes')
    criteria = models.ForeignKey(GalleryCriteria, on_delete=models.CASCADE, null=True, blank=True, related_name='votes')
    voter_name = models.CharField('투표자 이름', max_length=30)
    voter_session = models.CharField('세션키', max_length=64)
    score = models.IntegerField('별점', default=5)  # 1~5
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'gallery_vote'
        verbose_name = '투표'
        verbose_name_plural = '투표'
        unique_together = [('poster', 'voter_session', 'criteria')]

    def __str__(self):
        return f"{self.poster} ← {self.voter_name}"


@receiver(post_delete, sender=GalleryRoom)
def _delete_gallery_room_files(sender, instance, **kwargs):
    folder = os.path.join(settings.MEDIA_ROOT, 'gallery', str(instance.id))
    if os.path.exists(folder):
        shutil.rmtree(folder)


class SatisfactionSurvey(models.Model):
    title = models.CharField('제목', max_length=200)
    slug = models.SlugField('슬러그', max_length=100, unique=True)
    is_active = models.BooleanField('활성', default=True)
    active_date = models.DateField('수업 날짜', null=True, blank=True)
    expected_count = models.IntegerField('예상 참여 인원', default=0)
    sessions_data = models.JSONField('차시 목록', default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'satisfaction_survey'
        verbose_name = '만족도 조사'
        verbose_name_plural = '만족도 조사'

    def __str__(self):
        return self.title


class SatisfactionResponse(models.Model):
    survey = models.ForeignKey(SatisfactionSurvey, on_delete=models.CASCADE, related_name='responses')
    respondent_name = models.CharField('이름', max_length=30)
    respondent_school = models.CharField('학교', max_length=50, blank=True)
    respondent_grade = models.CharField('학년', max_length=20, blank=True)
    session_key = models.CharField('세션키', max_length=100)
    overall_score = models.IntegerField('전체 만족도')
    session_scores = models.JSONField('차시별 만족도', default=dict)
    favorite_sessions = models.JSONField('재미있었던 차시', default=list)
    hardest_sessions = models.JSONField('어려웠던 차시', default=list)
    attend_again = models.CharField('재참여 의향', max_length=60, blank=True)
    recommend = models.CharField('추천 의향', max_length=60, blank=True)
    ai_interests = models.JSONField('배우고 싶은 AI 분야', default=list)
    good_points = models.TextField('좋았던 점', blank=True)
    bad_points = models.TextField('아쉬웠던 점', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'satisfaction_response'
        verbose_name = '만족도 응답'
        verbose_name_plural = '만족도 응답'
        unique_together = [('survey', 'session_key')]

    def __str__(self):
        return f"{self.survey.title} - {self.respondent_name}"
