from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.validators import UnicodeUsernameValidator

from .models import Badge, Project, ScheduleEvent, Tag, UserProfile


BADGE_CRITERIA_HELP = (
    '지원 조건: typing_total_count(누적 타자 기록 수), typing_accuracy(정확도 이상), '
    'typing_speed(타속 이상), typing_practice_first(유형별 첫 기록), '
    'program_completion(연결 과정 이수), program_completion_count(서로 다른 과정 이수 수), '
    'homework_completion_count(완료 숙제 수), mission_completion_count(완료 미션 수)'
)


class ProjectUploadForm(forms.ModelForm):
    tags_str = forms.CharField(
        label='태그(쉼표로 구분)',
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': '예: pygame, 액션, 2인용',
                'class': 'form-input',
            }
        ),
        help_text='태그를 쉼표(,)로 구분해 입력해 주세요.',
    )

    class Meta:
        model = Project
        fields = [
            'author',
            'title',
            'description',
            'categories',
            'author_display_name',
            'thumbnail',
            'thumbnail_emoji',
            'color',
            'accent',
            'project_zip',
            'entry_file',
            'external_url',
        ]
        widgets = {
            'categories': forms.CheckboxSelectMultiple(),
            'title': forms.TextInput(
                attrs={'placeholder': '작품 이름을 입력해 주세요.', 'class': 'form-input'}
            ),
            'description': forms.Textarea(
                attrs={'placeholder': '작품 설명을 작성해 주세요.', 'class': 'form-input', 'rows': 8}
            ),
            'external_url': forms.URLInput(
                attrs={'placeholder': 'https://...', 'class': 'form-input'}
            ),
            'author_display_name': forms.TextInput(
                attrs={'placeholder': '예: 김민준 (중2)', 'class': 'form-input'}
            ),
            'thumbnail_emoji': forms.TextInput(
                attrs={'placeholder': '🎮', 'class': 'form-input'}
            ),
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'form-color'}),
            'accent': forms.TextInput(attrs={'type': 'color', 'class': 'form-color'}),
            'entry_file': forms.TextInput(
                attrs={'placeholder': 'index.html', 'class': 'form-input'}
            ),
            'project_zip': forms.FileInput(attrs={'accept': '.zip', 'class': 'form-file'}),
            'thumbnail': forms.FileInput(attrs={'accept': 'image/*', 'class': 'form-file'}),
            'author': forms.Select(
                attrs={'class': 'form-input author-select', 'size': '7'}
            ),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['author'].queryset = User.objects.all().order_by('-date_joined')
        self.fields['author'].label = '실제 제작 회원'
        self.fields['author'].required = False

        if user and not self.instance.pk and hasattr(user, 'profile'):
            self.fields['author_display_name'].initial = user.profile.display_name

        if self.instance.pk:
            self.fields['tags_str'].initial = ', '.join(
                tag.name for tag in self.instance.tags.all()
            )

        if not self.instance.pk:
            self.fields['description'].initial = (
                "[작품 설명]\n"
                "\n\n"
                "[조작 방법]\n"
                "- 이동: \n"
                "- 공격/점프: \n\n"
                "[시작 후기]\n"
                "게임이나 프로그램을 어떻게 만들었는지 적어 주세요."
            )

    def clean_tags_str(self):
        tags_str = self.cleaned_data.get('tags_str', '')
        if not tags_str:
            return []

        tag_list = list(dict.fromkeys(tag.strip() for tag in tags_str.split(',') if tag.strip()))
        if len(tag_list) > 10:
            raise forms.ValidationError('태그는 최대 10개까지 등록할 수 있습니다.')
        return tag_list

    def clean_project_zip(self):
        uploaded = self.cleaned_data.get('project_zip')
        if uploaded:
            if not uploaded.name.lower().endswith('.zip'):
                raise forms.ValidationError('ZIP 파일만 업로드할 수 있습니다.')
            if uploaded.size > 50 * 1024 * 1024:
                raise forms.ValidationError('파일 크기는 50MB 이하여야 합니다.')
        return uploaded

    def clean(self):
        cleaned_data = super().clean()
        project_zip = cleaned_data.get('project_zip')
        external_url = cleaned_data.get('external_url')

        if not self.instance.project_path and not project_zip and not external_url:
            raise forms.ValidationError(
                '작품 파일(ZIP)을 업로드하거나 외부 링크 URL을 입력해 주세요.'
            )
        return cleaned_data

    def save(self, commit=True):
        project = super().save(commit=commit)
        tag_names = self.cleaned_data.get('tags_str', [])

        if commit:
            self._save_tags(project, tag_names)
        else:
            original_save_m2m = self.save_m2m

            def save_m2m():
                original_save_m2m()
                self._save_tags(project, tag_names)

            self.save_m2m = save_m2m

        return project

    def _save_tags(self, project, tag_names):
        project.tags.clear()
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            project.tags.add(tag)


class SignUpForm(UserCreationForm):
    USER_TYPE_CHOICES = [
        ('student', '학생회원'),
        ('general', '일반회원'),
        ('medulab_member', '메듀랩 회원'),
        ('medulab_teacher', '메듀랩 강사'),
        ('medulab_staff', '메듀랩 스탭'),
    ]

    real_name = forms.CharField(
        label='이름',
        widget=forms.TextInput(attrs={'placeholder': '실명을 입력해 주세요.', 'class': 'form-input'}),
    )
    birth_date = forms.CharField(
        label='생년월일',
        required=True,
        widget=forms.TextInput(attrs={'placeholder': '예: 1989.01.16', 'class': 'form-input'}),
    )
    phone_number = forms.CharField(
        label='전화번호',
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': '숫자만 입력해도 됩니다',
                'class': 'form-input',
                'inputmode': 'numeric',
                'autocomplete': 'tel',
            }
        ),
        help_text='하이픈 없이 숫자만 입력해도 자동으로 정리됩니다.',
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'placeholder': '이메일 주소(선택)', 'class': 'form-input'}),
    )
    user_type = forms.ChoiceField(
        label='회원 유형',
        choices=USER_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'user-type-radio'}),
        initial='general',
    )

    class Meta:
        model = User
        fields = ('real_name', 'birth_date', 'username', 'phone_number', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'ID'
        self.fields['username'].validators = [UnicodeUsernameValidator()]
        self.fields['username'].help_text = '한글, 영문, 숫자, @/./+/-/_ 만 사용할 수 있습니다.'
        self.fields['username'].widget.attrs.update(
            {
                'placeholder': '사용할 아이디를 입력해 주세요.',
                'class': 'form-input',
                'id': 'id_username_field',
            }
        )
        self.fields['email'].widget.attrs.update(
            {
                'placeholder': '이메일 주소(선택)',
                'class': 'form-input',
            }
        )
        if 'password1' in self.fields:
            self.fields['password1'].widget.attrs.update(
                {'class': 'form-input', 'placeholder': '비밀번호'}
            )
        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs.update(
                {'class': 'form-input', 'placeholder': '비밀번호 확인'}
            )
        self.order_fields(
            ['real_name', 'birth_date', 'username', 'phone_number', 'email', 'password1', 'password2', 'user_type']
        )

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date', '').strip()
        if not birth_date:
            return None

        import datetime

        for fmt in ('%Y.%m.%d', '%Y-%m-%d', '%Y%m%d'):
            try:
                return datetime.datetime.strptime(birth_date, fmt).date()
            except ValueError:
                continue
        raise forms.ValidationError('날짜 형식이 올바르지 않습니다. (예: 1989.01.16)')

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip()
        if not email:
            return ''
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('이미 가입된 이메일 주소입니다.')
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number', '')
        digits = ''.join(ch for ch in phone_number if ch.isdigit())
        if not digits:
            return ''
        if len(digits) < 9 or len(digits) > 11:
            raise forms.ValidationError('전화번호는 숫자 기준 9자리에서 11자리로 입력해 주세요.')
        return digits

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            user_type = self.cleaned_data.get('user_type', 'general')
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.user_type = user_type
            profile.real_name = self.cleaned_data.get('real_name')
            profile.birth_date = self.cleaned_data.get('birth_date')
            profile.phone_number = self.cleaned_data.get('phone_number', '')
            profile.is_approved = user_type in UserProfile.AUTO_APPROVE_TYPES
            profile.save()
        return user


class AdminUserForm(forms.ModelForm):
    password = forms.CharField(
        label='비밀번호',
        required=False,
        widget=forms.PasswordInput(
            attrs={'placeholder': '변경 시에만 입력해 주세요.', 'class': 'form-input'}
        ),
        help_text='비밀번호를 변경할 때만 입력하고, 유지하려면 비워 두세요.',
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'is_staff', 'is_active')
        labels = {
            'username': '로그인 아이디',
            'email': '이메일 주소',
            'is_staff': '관리자 권한',
            'is_active': '활성 상태',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class AdminUserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('user_type', 'is_approved')
        labels = {'user_type': '회원 유형', 'is_approved': '승인 여부'}
        widgets = {
            'user_type': forms.Select(attrs={'class': 'form-input'}),
            'is_approved': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


class BadgeForm(forms.ModelForm):
    class Meta:
        model = Badge
        fields = (
            'code',
            'name',
            'description',
            'icon',
            'color',
            'category',
            'criteria_type',
            'criteria_value',
            'related_program',
            'is_active',
            'sort_order',
        )
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-input'}),
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'icon': forms.TextInput(attrs={'class': 'form-input'}),
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'form-color'}),
            'category': forms.Select(attrs={'class': 'form-input'}),
            'criteria_type': forms.TextInput(attrs={'class': 'form-input'}),
            'criteria_value': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'related_program': forms.Select(attrs={'class': 'form-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['criteria_type'].help_text = BADGE_CRITERIA_HELP
        self.fields['criteria_value'].help_text = '조건 달성 기준값입니다. 예: 정확도 90, 타속 250, 이수 과정 3개.'
        self.fields['related_program'].help_text = 'program_completion 조건일 때 연결할 과정을 선택합니다.'


class EmailOrUsernameAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label='아이디 또는 이메일',
        widget=forms.TextInput(
            attrs={
                'placeholder': '아이디 또는 이메일 주소',
                'class': 'form-input',
                'autofocus': True,
            }
        ),
    )
    password = forms.CharField(
        label='비밀번호',
        widget=forms.PasswordInput(
            attrs={'placeholder': '비밀번호', 'class': 'form-input'}
        ),
    )


class UserProfileUpdateForm(forms.ModelForm):
    USER_TYPE_CHOICES = SignUpForm.USER_TYPE_CHOICES

    username = forms.CharField(
        label='아이디',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'readonly': 'readonly'}),
    )
    email = forms.EmailField(
        label='이메일 주소',
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-input'}),
    )
    real_name = forms.CharField(
        label='이름',
        widget=forms.TextInput(attrs={'class': 'form-input'}),
    )
    birth_date = forms.CharField(
        label='생년월일',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': '예: 2016.03.15'}),
    )
    phone_number = forms.CharField(
        label='전화번호',
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-input',
                'placeholder': '숫자만 입력해도 됩니다',
                'inputmode': 'numeric',
                'autocomplete': 'tel',
            }
        ),
        help_text='하이픈 없이 숫자만 입력해도 자동으로 정리됩니다.',
    )
    user_type = forms.ChoiceField(
        label='회원 유형',
        choices=USER_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-input'}),
    )
    nickname = forms.CharField(
        label='닉네임(표시 이름)',
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-input', 'placeholder': '작품 등록 때 사용할 기본 이름'}
        ),
        help_text='닉네임이 없으면 이름을 먼저 쓰고, 이름도 없으면 아이디를 사용합니다.',
    )

    class Meta:
        model = UserProfile
        fields = ('real_name', 'birth_date', 'phone_number', 'user_type', 'nickname')

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['username'].initial = user.username
            self.fields['email'].initial = user.email
        self.fields['username'].disabled = True
        self.fields['real_name'].initial = self.instance.real_name
        self.fields['birth_date'].initial = (
            self.instance.birth_date.strftime('%Y.%m.%d') if self.instance.birth_date else ''
        )
        self.fields['phone_number'].initial = self.instance.phone_number
        self.fields['user_type'].initial = self.instance.user_type

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip()
        if not email:
            return ''
        user = self.instance.user
        if User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
            raise forms.ValidationError('이미 다른 회원이 사용 중인 이메일 주소입니다.')
        return email

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date', '').strip()
        if not birth_date:
            return None

        import datetime

        for fmt in ('%Y.%m.%d', '%Y-%m-%d', '%Y%m%d'):
            try:
                return datetime.datetime.strptime(birth_date, fmt).date()
            except ValueError:
                continue
        raise forms.ValidationError('날짜 형식이 올바르지 않습니다. (예: 2016.03.15)')

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number', '')
        digits = ''.join(ch for ch in phone_number if ch.isdigit())
        if not digits:
            return ''
        if len(digits) < 9 or len(digits) > 11:
            raise forms.ValidationError('전화번호는 숫자 기준 9자리에서 11자리로 입력해 주세요.')
        return digits

    def save(self, commit=True):
        profile = super().save(commit=False)
        previous_user_type = self.instance.user_type
        new_user_type = self.cleaned_data['user_type']
        user = profile.user

        user.email = self.cleaned_data['email']
        profile.real_name = self.cleaned_data['real_name']
        profile.birth_date = self.cleaned_data['birth_date']
        profile.phone_number = self.cleaned_data['phone_number']
        profile.user_type = new_user_type
        profile.nickname = self.cleaned_data['nickname']

        if new_user_type in UserProfile.AUTO_APPROVE_TYPES:
            profile.is_approved = True
        elif previous_user_type != new_user_type:
            profile.is_approved = False
            profile.approved_at = None

        if commit:
            user.email = self.cleaned_data['email']
            profile.real_name = self.cleaned_data['real_name']
            profile.birth_date = self.cleaned_data['birth_date']
            profile.phone_number = self.cleaned_data['phone_number']
            profile.user_type = new_user_type
            profile.nickname = self.cleaned_data['nickname']

            if new_user_type in UserProfile.AUTO_APPROVE_TYPES:
                profile.is_approved = True
            elif previous_user_type != new_user_type:
                profile.is_approved = False
                profile.approved_at = None

            if commit:
                user.save(update_fields=['email'])
                profile.save()
            return profile


class ScheduleEventForm(forms.ModelForm):
    class Meta:
        model = ScheduleEvent
        fields = ['title', 'description', 'start_date', 'end_date', 'event_type', 'image', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'title': '일정명',
            'description': '상세 설명',
            'start_date': '시작일',
            'end_date': '종료일',
            'event_type': '일정 유형',
            'image': '이미지 (포스터)',
            'is_active': '노출 여부',
        }
        help_texts = {
            'is_active': '체크하면 학원 일정 페이지에 노출됩니다.',
            'image': '대회 포스터나 관련 이미지를 첨부할 수 있습니다. (선택사항)',
        }
