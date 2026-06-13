with open('arcade/views.py', 'a', encoding='utf-8') as f:
    f.write('''

@user_passes_test(lambda u: u.is_staff)
def board_notice_create(request):
    from .forms import NoticeForm
    if request.method == 'POST':
        form = NoticeForm(request.POST, request.FILES)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.author = request.user
            notice.save()
            return redirect('board_notice')
    else:
        form = NoticeForm()
    return render(request, 'arcade/board_form.html', {'form': form, 'title': '공지사항 글쓰기'})

@user_passes_test(lambda u: u.is_staff)
def board_awards_create(request):
    from .forms import AwardForm
    if request.method == 'POST':
        form = AwardForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('board_awards')
    else:
        form = AwardForm()
    return render(request, 'arcade/board_form.html', {'form': form, 'title': '대회수상 글쓰기'})

@user_passes_test(lambda u: u.is_staff)
def board_cert_create(request):
    from .forms import CertificationForm
    if request.method == 'POST':
        form = CertificationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('board_cert')
    else:
        form = CertificationForm()
    return render(request, 'arcade/board_form.html', {'form': form, 'title': '자격취득 글쓰기'})
''')
