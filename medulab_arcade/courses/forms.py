from django import forms
from django.contrib.auth.models import User
from .models import (
    LearningProgram,
    ProgramType,
    Item,
    Chapter,
    HomeworkAssignment,
    HomeworkSubmission,
)


class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class CourseForm(forms.ModelForm):
    class Meta:
        model = LearningProgram
        fields = ['name', 'description', 'image', 'program_type', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '과정명을 입력하세요'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'placeholder': '과정에에 대한 설명을 작성하세요 (작품 소개와 유사)', 'rows': 4}),
            'program_type': forms.Select(attrs={'class': 'form-input'}),
        }

class ProgramTypeForm(forms.ModelForm):
    class Meta:
        model = ProgramType
        fields = ['name', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '유형 명칭 (예: 파이썬, 로봇)'}),
            'order': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '목록 정렬 순서'}),
        }

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['chapter', 'number', 'key', 'title', 'item_type', 'explain_html', 'hint', 'answer_code', 'example_input', 'expected_output', 'due_date']
        widgets = {
            'chapter': forms.Select(attrs={'class': 'form-input'}),
            'number': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '정렬 순서(번호)'}),
            'key': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '식별 키 (예: ex01)'}),
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '아이템 제목'}),
            'item_type': forms.Select(attrs={'class': 'form-input'}),
            'explain_html': forms.Textarea(attrs={'class': 'form-input', 'rows': 10, 'placeholder': 'HTML 형식의 학습 설명을 입력하세요'}),
            'hint': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': '힌트 내용'}),
            'answer_code': forms.Textarea(attrs={'class': 'form-input code-font', 'rows': 10, 'placeholder': '정답 코드(파이썬)'}),
            'example_input': forms.Textarea(attrs={'class': 'form-input code-font', 'rows': 3, 'placeholder': '테스트 시 사용할 입력값 (여러 줄일 경우 줄바꿈)'}),
            'expected_output': forms.Textarea(attrs={'class': 'form-input code-font', 'rows': 5, 'placeholder': '예상 출력 결과'}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
        }

class HomeworkForm(forms.ModelForm):
    attachment_files = forms.FileField(
        required=False,
        widget=MultiFileInput(attrs={'class': 'form-input', 'multiple': True}),
        label='?? ?? ??'
    )

    class Meta:
        model = HomeworkAssignment
        fields = ['program', 'title', 'description', 'assigned_users', 'linked_items', 'external_url', 'due_date', 'is_active']
        widgets = {
            'program': forms.Select(attrs={'class': 'form-input', 'id': 'id_program'}),
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '?? ??? ?????'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': '???? ??? ???? ??? ?????'}),
            'assigned_users': forms.SelectMultiple(attrs={'class': 'form-input', 'style': 'display:none;', 'id': 'id_assigned_users'}),
            'linked_items': forms.SelectMultiple(attrs={'class': 'form-input', 'style': 'display:none;', 'id': 'id_linked_items'}),
            'external_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://...'}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
        }


class HomeworkSubmissionForm(forms.ModelForm):
    class Meta:
        model = HomeworkSubmission
        fields = ['file', 'note']
        widgets = {
            'file': forms.ClearableFileInput(attrs={'class': 'form-input'}),
            'note': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': '?? ?? ???? ??? ?????'}),
        }


class HomeworkSubmissionReviewForm(forms.ModelForm):
    class Meta:
        model = HomeworkSubmission
        fields = ['status', 'teacher_comment']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-input'}),
            'teacher_comment': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': '?? ??? ?????'}),
        }
