with open('arcade/views.py', 'a', encoding='utf-8') as f:
    f.write('''

@user_passes_test(lambda u: u.is_staff)
def board_notice_update(request, pk):
    from .forms import NoticeForm
    notice = get_object_or_404(Notice, pk=pk)
    if request.method == 'POST':
        form = NoticeForm(request.POST, request.FILES, instance=notice)
        if form.is_valid():
            form.save()
            return redirect('board_notice_detail', pk=notice.pk)
    else:
        form = NoticeForm(instance=notice)
    return render(request, 'arcade/board_form.html', {'form': form, 'title': '공지사항 수정'})

@user_passes_test(lambda u: u.is_staff)
def board_notice_delete(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    if request.method == 'POST':
        notice.delete()
        return redirect('board_notice')
    return render(request, 'arcade/board_confirm_delete.html', {'object': notice, 'title': '공지사항 삭제', 'cancel_url': reverse('board_notice_detail', args=[pk])})

@user_passes_test(lambda u: u.is_staff)
def board_awards_update(request, pk):
    from .forms import AwardForm
    award = get_object_or_404(Award, pk=pk)
    if request.method == 'POST':
        form = AwardForm(request.POST, request.FILES, instance=award)
        if form.is_valid():
            form.save()
            return redirect('board_awards_detail', pk=award.pk)
    else:
        form = AwardForm(instance=award)
    return render(request, 'arcade/board_form.html', {'form': form, 'title': '대회수상 수정'})

@user_passes_test(lambda u: u.is_staff)
def board_awards_delete(request, pk):
    award = get_object_or_404(Award, pk=pk)
    if request.method == 'POST':
        award.delete()
        return redirect('board_awards')
    return render(request, 'arcade/board_confirm_delete.html', {'object': award, 'title': '대회수상 삭제', 'cancel_url': reverse('board_awards_detail', args=[pk])})

@user_passes_test(lambda u: u.is_staff)
def board_cert_update(request, pk):
    from .forms import CertificationForm
    cert = get_object_or_404(Certification, pk=pk)
    if request.method == 'POST':
        form = CertificationForm(request.POST, request.FILES, instance=cert)
        if form.is_valid():
            form.save()
            return redirect('board_cert_detail', pk=cert.pk)
    else:
        form = CertificationForm(instance=cert)
    return render(request, 'arcade/board_form.html', {'form': form, 'title': '자격취득 수정'})

@user_passes_test(lambda u: u.is_staff)
def board_cert_delete(request, pk):
    cert = get_object_or_404(Certification, pk=pk)
    if request.method == 'POST':
        cert.delete()
        return redirect('board_cert')
    return render(request, 'arcade/board_confirm_delete.html', {'object': cert, 'title': '자격취득 삭제', 'cancel_url': reverse('board_cert_detail', args=[pk])})
''')
