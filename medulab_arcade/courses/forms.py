from django import forms
from django.contrib.auth.models import User

from .models import (
    Chapter,
    HomeworkAssignment,
    HomeworkSubmission,
    Item,
    LearningProgram,
    ProgramType,
)


ANSWER_ZIP_MAX_UPLOAD_BYTES = 200 * 1024 * 1024


class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class CourseForm(forms.ModelForm):
    class Meta:
        model = LearningProgram
        fields = ["name", "description", "image", "picture_zip", "answer_zip", "program_type", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input", "placeholder": "과정명을 입력하세요"}),
            "description": forms.Textarea(
                attrs={"class": "form-input", "placeholder": "과정 설명을 작성하세요", "rows": 4}
            ),
            "program_type": forms.Select(attrs={"class": "form-input"}),
        }


class ProgramTypeForm(forms.ModelForm):
    class Meta:
        model = ProgramType
        fields = ["name", "order"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input", "placeholder": "유형 이름을 입력하세요"}),
            "order": forms.NumberInput(attrs={"class": "form-input", "placeholder": "정렬 순서"}),
        }


class ChapterForm(forms.ModelForm):
    class Meta:
        model = Chapter
        fields = ['number', 'title', 'content']
        widgets = {
            'number': forms.NumberInput(attrs={'class': 'form-input'}),
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'content': forms.Textarea(attrs={'rows': 3, 'class': 'form-textarea'}),
        }

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            "chapter",
            "number",
            "key",
            "title",
            "item_type",
            "explain_html",
            "hint",
            "answer_code",
            "example_input",
            "expected_output",
            "due_date",
        ]
        widgets = {
            "chapter": forms.Select(attrs={"class": "form-input"}),
            "number": forms.NumberInput(attrs={"class": "form-input", "placeholder": "정렬 순서(번호)"}),
            "key": forms.TextInput(attrs={"class": "form-input", "placeholder": "항목 키 예: ex01"}),
            "title": forms.TextInput(attrs={"class": "form-input", "placeholder": "항목 제목"}),
            "item_type": forms.Select(attrs={"class": "form-input"}),
            "explain_html": forms.Textarea(
                attrs={"class": "form-input", "rows": 10, "placeholder": "HTML 형식의 설명을 입력하세요"}
            ),
            "hint": forms.Textarea(attrs={"class": "form-input", "rows": 3, "placeholder": "힌트 내용"}),
            "answer_code": forms.Textarea(
                attrs={"class": "form-input code-font", "rows": 10, "placeholder": "정답 코드"}
            ),
            "example_input": forms.Textarea(
                attrs={
                    "class": "form-input code-font",
                    "rows": 3,
                    "placeholder": "테스트용 입력값(여러 줄이면 줄바꿈)",
                }
            ),
            "expected_output": forms.Textarea(
                attrs={"class": "form-input code-font", "rows": 5, "placeholder": "예상 출력 결과"}
            ),
            "due_date": forms.DateTimeInput(attrs={"class": "form-input", "type": "datetime-local"}),
        }


class AnswerZipImportForm(forms.Form):
    answer_zip = forms.FileField(
        label="answer.zip",
        widget=forms.ClearableFileInput(attrs={"class": "form-input", "accept": ".zip"}),
    )

    def clean_answer_zip(self):
        uploaded = self.cleaned_data["answer_zip"]
        if not (uploaded.name or "").lower().endswith(".zip"):
            raise forms.ValidationError("ZIP 파일만 업로드할 수 있습니다.")
        if uploaded.size > ANSWER_ZIP_MAX_UPLOAD_BYTES:
            raise forms.ValidationError("answer.zip 파일은 200MB 이하만 업로드할 수 있습니다.")
        return uploaded


class HomeworkForm(forms.ModelForm):
    attachment_files = forms.FileField(
        required=False,
        widget=MultiFileInput(attrs={"class": "form-input", "multiple": True}),
        label="숙제 첨부 파일",
    )

    class Meta:
        model = HomeworkAssignment
        fields = [
            "program",
            "title",
            "description",
            "assigned_users",
            "linked_items",
            "external_url",
            "due_date",
            "is_active",
        ]
        widgets = {
            "program": forms.Select(attrs={"class": "form-input", "id": "id_program"}),
            "title": forms.TextInput(attrs={"class": "form-input", "placeholder": "숙제 제목을 입력하세요"}),
            "description": forms.Textarea(
                attrs={
                    "class": "form-input",
                    "rows": 3,
                    "placeholder": "학생에게 보여줄 설명이나 안내를 적어주세요",
                }
            ),
            "assigned_users": forms.SelectMultiple(
                attrs={"class": "form-input", "style": "display:none;", "id": "id_assigned_users"}
            ),
            "linked_items": forms.SelectMultiple(
                attrs={"class": "form-input", "style": "display:none;", "id": "id_linked_items"}
            ),
            "external_url": forms.URLInput(attrs={"class": "form-input", "placeholder": "https://..."}),
            "due_date": forms.DateTimeInput(attrs={"class": "form-input", "type": "datetime-local"}),
        }


class HomeworkSubmissionForm(forms.ModelForm):
    class Meta:
        model = HomeworkSubmission
        fields = ["file", "note"]
        widgets = {
            "file": forms.ClearableFileInput(attrs={"class": "form-input"}),
            "note": forms.Textarea(
                attrs={
                    "class": "form-input",
                    "rows": 3,
                    "placeholder": "제출 파일 설명이나 메모를 적어주세요",
                }
            ),
        }


class HomeworkSubmissionReviewForm(forms.ModelForm):
    class Meta:
        model = HomeworkSubmission
        fields = ["status", "teacher_comment"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-input"}),
            "teacher_comment": forms.Textarea(
                attrs={"class": "form-input", "rows": 4, "placeholder": "평가 메모를 적어주세요"}
            ),
        }
