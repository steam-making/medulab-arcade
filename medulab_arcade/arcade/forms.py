from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Project, Tag


class ProjectUploadForm(forms.ModelForm):
    tags_str = forms.CharField(
        label='태그 (쉼표로 구분)',
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '예: Pygame, 액션, 2인용 (최대 10개)',
            'class': 'form-input',
        }),
        help_text='태그를 쉼표(,)로 구분하여 입력해주세요.'
    )

    class Meta:
        model = Project
        fields = [
            'title', 'description', 'categories', 'author_display_name',
            'thumbnail', 'thumbnail_emoji', 'color', 'accent',
            'project_zip', 'entry_file', 'external_url',
        ]
        widgets = {
            'categories': forms.CheckboxSelectMultiple(),
            'title': forms.TextInput(attrs={
                'placeholder': '작품 이름을 입력하세요',
                'class': 'form-input',
            }),
            'description': forms.Textarea(attrs={
                'placeholder': '작품에 대한 설명을 작성해주세요',
                'class': 'form-input',
                'rows': 8,
            }),
            'external_url': forms.URLInput(attrs={
                'placeholder': 'https://...',
                'class': 'form-input',
            }),
            'author_display_name': forms.TextInput(attrs={
                'placeholder': '예: 김민준 (중2)',
                'class': 'form-input',
            }),
            'thumbnail_emoji': forms.TextInput(attrs={
                'placeholder': '🎮',
                'class': 'form-input',
            }),
            'color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-color',
            }),
            'accent': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-color',
            }),
            'entry_file': forms.TextInput(attrs={
                'placeholder': 'index.html',
                'class': 'form-input',
            }),
            'project_zip': forms.FileInput(attrs={
                'accept': '.zip',
                'class': 'form-file',
            }),
            'thumbnail': forms.FileInput(attrs={
                'accept': 'image/*',
                'class': 'form-file',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # 기존 태그들을 쉼표로 구분된 문자열로 변환
            self.fields['tags_str'].initial = ', '.join([t.name for t in self.instance.tags.all()])
            
        if not self.instance.pk:  # 신규 등록인 경우에만 양식 제공
            self.fields['description'].initial = (
                "[작품 설명]\n"
                "\n\n"
                "[조작 방법]\n"
                "- 이동: \n"
                "- 공격/점프: \n\n"
                "[제작 후기 및 팁]\n"
                "게임을 더 재미있게 즐기는 법을 알려주세요!"
            )

    def clean_tags_str(self):
        tags_str = self.cleaned_data.get('tags_str', '')
        if not tags_str:
            return []
        
        # 쉼표로 분리 후 공백 제거 및 중복 제거
        tag_list = list(set([t.strip() for t in tags_str.split(',') if t.strip()]))
        
        if len(tag_list) > 10:
            raise forms.ValidationError('태그는 최대 10개까지만 등록할 수 있습니다.')
            
        return tag_list

    def save(self, commit=True):
        project = super().save(commit=commit)
        tag_names = self.cleaned_data.get('tags_str', [])
        
        if commit:
            self._save_tags(project, tag_names)
        else:
            # commit=False인 경우 (views.py에서 나중에 처리)
            # 이 부분은 view에서 form.save_m2m() 호출 시 실행되도록 save_m2m을 확장하거나
            # 수동으로 처리해야 함. 여기선 간단하게 save_m2m에 추가함.
            old_save_m2m = self.save_m2m
            def new_save_m2m():
                old_save_m2m()
                self._save_tags(project, tag_names)
            self.save_m2m = new_save_m2m
            
        return project

    def _save_tags(self, project, tag_names):
        project.tags.clear()
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            project.tags.add(tag)

    def clean(self):
        cleaned_data = super().clean()
        project_zip = cleaned_data.get('project_zip')
        external_url = cleaned_data.get('external_url')

        # 신규 등록이거나 기존에 압축 해제된 경로가 없는 경우, 둘 중 하나는 필수
        if not self.instance.project_path and not project_zip and not external_url:
            raise forms.ValidationError('작품 파일(ZIP)을 업로드하거나 외부 링크 URL을 입력해주세요.')
        
        return cleaned_data

    def clean_project_zip(self):
        f = self.cleaned_data.get('project_zip')
        if f:
            if not f.name.endswith('.zip'):
                raise forms.ValidationError('ZIP 파일만 업로드 가능합니다.')
            if f.size > 50 * 1024 * 1024:
                raise forms.ValidationError('파일 크기는 50MB 이하여야 합니다.')
        return f


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'placeholder': '이메일 주소',
        'class': 'form-input',
    }))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'placeholder': '사용자 이름',
            'class': 'form-input',
        })
        self.fields['password1'].widget.attrs.update({
            'placeholder': '비밀번호',
            'class': 'form-input',
        })
        self.fields['password2'].widget.attrs.update({
            'placeholder': '비밀번호 확인',
            'class': 'form-input',
        })
