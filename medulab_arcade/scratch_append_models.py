with open('arcade/models.py', 'a', encoding='utf-8') as f:
    f.write('''

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
    title = models.CharField('제목 (게시물용)', max_length=200)
    student_name = models.CharField('학생 이름', max_length=50)
    competition_name = models.CharField('대회명', max_length=100)
    award_name = models.CharField('상격 (예: 대상, 금상)', max_length=50)
    date_awarded = models.DateField('수상일자')
    thumbnail = models.ImageField('대표 이미지', upload_to='awards/', blank=True, null=True)
    content = models.TextField('내용', blank=True)
    created_at = models.DateTimeField('등록일', auto_now_add=True)

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
    title = models.CharField('제목 (게시물용)', max_length=200)
    student_name = models.CharField('학생 이름', max_length=50)
    cert_name = models.CharField('자격증명', max_length=100)
    date_acquired = models.DateField('취득일자')
    thumbnail = models.ImageField('자격증/배지 이미지', upload_to='certs/', blank=True, null=True)
    content = models.TextField('내용', blank=True)
    created_at = models.DateTimeField('등록일', auto_now_add=True)

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
''')
