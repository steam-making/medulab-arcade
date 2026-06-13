with open('arcade/forms.py', 'a', encoding='utf-8') as f:
    f.write('''

class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = ['title', 'content', 'is_pinned', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '공지 제목', 'style': 'width:100%; padding: 10px; margin-bottom: 15px; border-radius:8px; background: rgba(255,255,255,0.05); color:white; border: 1px solid rgba(255,255,255,0.1);'}),
            'content': forms.Textarea(attrs={'class': 'form-input', 'rows': 10, 'style': 'width:100%; padding: 10px; margin-bottom: 15px; border-radius:8px; background: rgba(255,255,255,0.05); color:white; border: 1px solid rgba(255,255,255,0.1);'}),
        }

class AwardForm(forms.ModelForm):
    class Meta:
        model = Award
        fields = ['title', 'student_name', 'competition_name', 'award_name', 'organization', 'date_awarded', 'thumbnail', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '게시물 제목', 'style': 'width:100%; padding: 10px; margin-bottom: 15px; border-radius:8px; background: rgba(255,255,255,0.05); color:white; border: 1px solid rgba(255,255,255,0.1);'}),
            'student_name': forms.TextInput(attrs={'class': 'form-input', 'style': 'width:100%; padding: 10px; margin-bottom: 15px; border-radius:8px; background: rgba(255,255,255,0.05); color:white; border: 1px solid rgba(255,255,255,0.1);'}),
            'competition_name': forms.TextInput(attrs={'class': 'form-input', 'style': 'width:100%; padding: 10px; margin-bottom: 15px; border-radius:8px; background: rgba(255,255,255,0.05); color:white; border: 1px solid rgba(255,255,255,0.1);'}),
            'award_name': forms.TextInput(attrs={'class': 'form-input', 'style': 'width:100%; padding: 10px; margin-bottom: 15px; border-radius:8px; background: rgba(255,255,255,0.05); color:white; border: 1px solid rgba(255,255,255,0.1);'}),
            'organization': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '예: 교육부', 'style': 'width:100%; padding: 10px; margin-bottom: 15px; border-radius:8px; background: rgba(255,255,255,0.05); color:white; border: 1px solid rgba(255,255,255,0.1);'}),
            'date_awarded': forms.DateInput(attrs={'class': 'form-input', 'type': 'date', 'style': 'width:100%; padding: 10px; margin-bottom: 15px; border-radius:8px; background: rgba(255,255,255,0.05); color:white; border: 1px solid rgba(255,255,255,0.1);'}),
            'content': forms.Textarea(attrs={'class': 'form-input', 'rows': 5, 'style': 'width:100%; padding: 10px; margin-bottom: 15px; border-radius:8px; background: rgba(255,255,255,0.05); color:white; border: 1px solid rgba(255,255,255,0.1);'}),
        }

class CertificationForm(forms.ModelForm):
    class Meta:
        model = Certification
        fields = ['title', 'student_name', 'cert_name', 'issuer', 'date_acquired', 'thumbnail', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '게시물 제목', 'style': 'width:100%; padding: 10px; margin-bottom: 15px; border-radius:8px; background: rgba(255,255,255,0.05); color:white; border: 1px solid rgba(255,255,255,0.1);'}),
            'student_name': forms.TextInput(attrs={'class': 'form-input', 'style': 'width:100%; padding: 10px; margin-bottom: 15px; border-radius:8px; background: rgba(255,255,255,0.05); color:white; border: 1px solid rgba(255,255,255,0.1);'}),
            'cert_name': forms.TextInput(attrs={'class': 'form-input', 'style': 'width:100%; padding: 10px; margin-bottom: 15px; border-radius:8px; background: rgba(255,255,255,0.05); color:white; border: 1px solid rgba(255,255,255,0.1);'}),
            'issuer': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '예: 대한상공회의소', 'style': 'width:100%; padding: 10px; margin-bottom: 15px; border-radius:8px; background: rgba(255,255,255,0.05); color:white; border: 1px solid rgba(255,255,255,0.1);'}),
            'date_acquired': forms.DateInput(attrs={'class': 'form-input', 'type': 'date', 'style': 'width:100%; padding: 10px; margin-bottom: 15px; border-radius:8px; background: rgba(255,255,255,0.05); color:white; border: 1px solid rgba(255,255,255,0.1);'}),
            'content': forms.Textarea(attrs={'class': 'form-input', 'rows': 5, 'style': 'width:100%; padding: 10px; margin-bottom: 15px; border-radius:8px; background: rgba(255,255,255,0.05); color:white; border: 1px solid rgba(255,255,255,0.1);'}),
        }
''')
