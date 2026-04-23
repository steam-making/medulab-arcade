import io
import sys
import openpyxl
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, Http404
from .models import LearningProgram, Chapter, Item, LearningEnrollment, UserProgress, ProgramType, HomeworkAssignment
from .forms import CourseForm, ProgramTypeForm, ItemForm, HomeworkForm
from django.db.models import Count, Q

# --- 권한 체크 유틸리티 ---
def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def require_full_member(view_func):
    """메듀랩 정회원만 접근 가능하도록 하는 데코레이터"""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        profile = getattr(request.user, 'profile', None)
        # 관리자는 항상 통과
        if request.user.is_staff or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        if not profile or not profile.is_full_member:
            messages.warning(request, '메듀랩 정회원만 이용 가능합니다.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped

# --- Python 오류 한글 가이드 매핑 ---
PYTHON_ERROR_GUIDE = {
    "NameError": "정의되지 않은 이름을 사용했습니다. 오타가 있거나, 변수를 만들기 전에 사용한 건 아닌지 확인해 보세요.",
    "SyntaxError": "파이썬 문법에 어긋나는 부분이 있습니다. 괄호를 안 닫았거나, 콜론(:)이 빠졌는지 확인해 보세요.",
    "IndentationError": "들여쓰기(강제 공백)가 잘못되었습니다. 줄 앞의 빈칸이 일정한지 확인해 보세요.",
    "TypeError": "데이터 타입이 맞지 않습니다. 숫자와 글자를 더하려고 한 것은 아닌지 확인해 보세요.",
    "ZeroDivisionError": "0으로 나눌 수 없습니다. 나누는 값(분모)이 0이 되지 않도록 코드를 수정해 보세요.",
    "IndexError": "목록(List)의 범위를 벗어난 위치에 접근하려고 했습니다.",
    "KeyError": "딕셔너리에 존재하지 않는 키를 사용했습니다.",
    "ValueError": "부적절한 값을 사용했습니다. 글자를 숫자로 바꾸려고 한 건 아닌지 확인해 보세요.",
    "AttributeError": "해당 객체에 없는 기능을 사용하려고 했습니다.",
    "ModuleNotFoundError": "설치되지 않았거나 존재하지 않는 모듈을 불러오려고 했습니다.",
}

# --- Python 코드 안전 실행 유틸리티 ---
def safe_exec(code, input_str=""):
    old_stdout = sys.stdout
    sys.stdout = captured = io.StringIO()
    
    # input() 가로채기 위한 클래스
    class MockInput:
        def __init__(self, data):
            # splitlines()를 사용하여 \r\n, \n 등 모든 종류의 줄바꿈을 깔끔하게 제거
            self.lines = data.splitlines() if data else []
            self.idx = 0
        def __call__(self, prompt=""):
            if self.idx < len(self.lines):
                res = self.lines[self.idx]
                self.idx += 1
                return res
            return ""

    try:
        # 빌트인 함수 제한 및 input 가로채기
        allowed_builtins = {
            "print": print,
            "range": range,
            "len": len,
            "int": int,
            "str": str,
            "float": float,
            "list": list,
            "dict": dict,
            "sum": sum,
            "abs": abs,
            "round": round,
            "input": MockInput(input_str),
            "type": type,
        }
        exec(code, {"__builtins__": allowed_builtins})
        output = captured.getvalue()
    except Exception as e:
        error_type = type(e).__name__
        korean_hint = PYTHON_ERROR_GUIDE.get(error_type, "오류가 발생했습니다. 코드를 다시 차근차근 확인해 보세요.")
        # SyntaxError/IndentationError 등은 e.msg에 메시지가 있고 str(e)에 위치가 포함됨
        output = f"Traceback (Error Notification):\n{e}\n\n[💡 도움말]\n{korean_hint}"
    finally:
        sys.stdout = old_stdout
    return output

# --- (1) 관리자용 학습 프로그램 목록 ---
@login_required
@user_passes_test(is_admin)
def learning_program_list(request):
    programs = LearningProgram.objects.all().order_by("-created_at")
    return render(request, "courses/learning_program_list.html", {
        "programs": programs
    })

# --- (1-1) 과정 등록 ---
@login_required
@user_passes_test(is_admin)
def learning_program_create(request):
    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "새 과정이 성공적으로 등록되었습니다.")
            return redirect("learning_program_list")
    else:
        form = CourseForm()
    
    return render(request, "courses/learning_program_form.html", {
        "form": form,
        "title": "새 과정 등록"
    })

# --- (1-2) 과정 수정 ---
@login_required
@user_passes_test(is_admin)
def learning_program_edit(request, program_id):
    program = get_object_or_404(LearningProgram, id=program_id)
    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES, instance=program)
        if form.is_valid():
            form.save()
            messages.success(request, f"'{program.name}' 과정이 수정되었습니다.")
            return redirect("learning_program_list")
    else:
        form = CourseForm(instance=program)
    
    return render(request, "courses/learning_program_form.html", {
        "form": form,
        "title": "과정 정보 수정",
        "program": program
    })

# --- (1-3) 과정 삭제 ---
@login_required
@user_passes_test(is_admin)
def learning_program_delete(request, program_id):
    program = get_object_or_404(LearningProgram, id=program_id)
    if request.method == "POST":
        name = program.name
        program.delete()
        messages.success(request, f"'{name}' 과정이 삭제되었습니다.")
        return redirect("learning_program_list")
    return render(request, "courses/learning_program_confirm_delete.html", {"program": program})

# --- (1-4) 유형 관리 목록 ---
@login_required
@user_passes_test(is_admin)
def program_type_list(request):
    types = ProgramType.objects.all().order_by("order", "name")
    return render(request, "courses/program_type_list.html", {"types": types})

# --- (1-5) 유형 등록 ---
@login_required
@user_passes_test(is_admin)
def program_type_create(request):
    if request.method == "POST":
        form = ProgramTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "새 과정 유형이 등록되었습니다.")
            return redirect("program_type_list")
    else:
        form = ProgramTypeForm()
    return render(request, "courses/program_type_form.html", {"form": form, "title": "새 유형 등록"})

# --- (1-6) 유형 수정 ---
@login_required
@user_passes_test(is_admin)
def program_type_edit(request, type_id):
    p_type = get_object_or_404(ProgramType, id=type_id)
    if request.method == "POST":
        form = ProgramTypeForm(request.POST, instance=p_type)
        if form.is_valid():
            form.save()
            messages.success(request, f"'{p_type.name}' 유형이 수정되었습니다.")
            return redirect("program_type_list")
    else:
        form = ProgramTypeForm(instance=p_type)
    return render(request, "courses/program_type_form.html", {"form": form, "title": "유형 수정"})

# --- (1-7) 유형 삭제 ---
@login_required
@user_passes_test(is_admin)
def program_type_delete(request, type_id):
    p_type = get_object_or_404(ProgramType, id=type_id)
    if request.method == "POST":
        p_type.delete()
        messages.success(request, "유형이 삭제되었습니다.")
        return redirect("program_type_list")
    return render(request, "courses/program_type_confirm_delete.html", {"type": p_type})

# --- (1-8) 엑셀 템플릿 다운로드 ---
@login_required
@user_passes_test(is_admin)
def download_course_template(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "CourseTemplate"
    
    headers = [
        '장번호', '장제목', '장설명', 
        '아이템키(ex01)', '아이템제목', '유형(example/problem)', 
        '설명HTML', '힌트', '정답코드', '예상출력'
    ]
    ws.append(headers)
    
    # 샘플 데이터 한 줄
    ws.append([1, '파이썬 기초', '기본 문법을 배웁니다', 'ex01', 'Hello World', 'example', '<p>화면에 출력해보세요</p>', 'print 사용', 'print("Hello")', 'Hello'])
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=medulab_course_template.xlsx'
    wb.save(response)
    return response

# --- (2) 학생용 나의 코스 목록 ---
@login_required
@require_full_member
def student_course_list(request):
    # 모든 활성 프로그램
    all_programs = LearningProgram.objects.filter(is_active=True).order_by("id")
    
    # 내가 수강 중인 프로그램 ID 목록
    enrolled_ids = LearningEnrollment.objects.filter(user=request.user)\
                                           .values_list("program_id", flat=True)
    
    return render(request, "courses/student_course_list.html", {
        "programs": all_programs,
        "enrolled_ids": enrolled_ids,
    })

# --- (3) 수강 신청 ---
@login_required
@require_full_member
def student_course_apply(request, program_id):
    program = get_object_or_404(LearningProgram, id=program_id)
    
    # 중복 체크
    if LearningEnrollment.objects.filter(user=request.user, program=program).exists():
        messages.warning(request, "이미 신청한 과정입니다.")
    else:
        LearningEnrollment.objects.create(user=request.user, program=program)
        messages.success(request, f"'{program.name}' 수강 신청이 완료되었습니다!")
        
    return redirect("course_home", program_id=program.id)

# --- (4) 코스 홈 (챕터 구성) ---
@login_required
@require_full_member
def course_home(request, program_id):
    program = get_object_or_404(LearningProgram, id=program_id)
    chapters = Chapter.objects.filter(program=program).order_by("number")
    
    # 챕터별 진도율 계산하여 챕터 객체에 주입
    for ch in chapters:
        total_items = Item.objects.filter(chapter=ch).count()
        completed_items = UserProgress.objects.filter(
            user=request.user, 
            item__chapter=ch, 
            completed=True
        ).count()
        ch.progress = round((completed_items / total_items * 100)) if total_items > 0 else 0
        
    return render(request, "learning_program/course_home.html", {
        "program": program,
        "chapters": chapters,
    })

# --- (5) 챕터 상세 (항목 목록) ---
@login_required
def chapter_detail(request, chapter_id):
    chapter = get_object_or_404(Chapter, id=chapter_id)
    items = Item.objects.filter(chapter=chapter).order_by("number")
    
    # 완료 정보 로드하여 item 객체에 주입
    progress_map = {p.item_id: p.completed for p in UserProgress.objects.filter(user=request.user, item__in=items)}
    for item in items:
        item.is_completed = progress_map.get(item.id, False)
        
    return render(request, "learning_program/chapter_detail.html", {
        "chapter": chapter,
        "items": items,
        "program": chapter.program
    })

# --- (6) 학습 아이템 페이지 ---
@login_required
def item_page(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    program = item.chapter.program
    
    # 이전/다음 이동 로직 (챕터 내 또는 전체 과정 내)
    all_items = list(Item.objects.filter(chapter__program=program).order_by('chapter__number', 'number'))
    try:
        current_idx = all_items.index(item)
        prev_item = all_items[current_idx - 1] if current_idx > 0 else None
        next_item = all_items[current_idx + 1] if current_idx < len(all_items) - 1 else None
    except ValueError:
        prev_item = next_item = None

    # 유저 진행 상황 (기존 코드 등 로드)
    progress, _ = UserProgress.objects.get_or_create(user=request.user, item=item)

    # 템플릿 결정 (과정 이름이나 유형에 따라 분기 가능)
    template_name = "learning_program/item_page.html"
    p_name = program.name.lower()
    p_type_name = program.program_type.name.lower() if program.program_type else ""
    
    if "python" in p_name or "파이썬" in p_name or "python" in p_type_name or "파이썬" in p_type_name:
        template_name = "learning_program/item_page_python.html"
    elif item.answer_code or item.expected_output:
        # 데이터가 있으면 실습 문항으로 간주하여 파이썬 페이지 노출
        template_name = "learning_program/item_page_python.html"
    elif "ppt" in p_name or "파워포인트" in p_name or "ppt" in p_type_name or "파워포인트" in p_type_name:
        template_name = "learning_program/item_page_ppt.html"

    return render(request, template_name, {
        "item": item,
        "prev_item": prev_item,
        "next_item": next_item,
        "program": program,
        "user_progress": progress
    })

# --- (7) 코드 채점 API ---
@login_required
def grade_code(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)
    
    item_id = request.POST.get("item_id")
    code = request.POST.get("code", "")
    input_str = request.POST.get("input", "")
    
    item = get_object_or_404(Item, id=item_id)
    output = safe_exec(code, input_str)
    
    # 정답 비교 (줄바꿈 문자 정규화 및 공백 제거)
    def normalize(s):
        if not s: return ""
        # \r\n을 \n으로 통일하고 양끝 공백 제거
        return "\n".join([line.strip() for line in s.replace("\r\n", "\n").strip().split("\n")]).strip()

    user_out = normalize(output)
    expected_out = normalize(item.expected_output)
    
    is_correct = (user_out == expected_out)
    score = 100 if is_correct else 0
    
    # 결과 저장
    progress, _ = UserProgress.objects.get_or_create(user=request.user, item=item)
    progress.code = code
    progress.last_output = output
    progress.score = score
    progress.completed = is_correct
    progress.save()
    
    return JsonResponse({
        "is_correct": is_correct,
        "output": output,
        "expected": expected_out,
        "score": score
    })

# --- (8) 챕터 관리 및 엑셀 업로드 ---
@login_required
@user_passes_test(is_admin)
def chapter_manage(request, program_id):
    program = get_object_or_404(LearningProgram, id=program_id)
    
    if request.method == "POST" and request.FILES.get("excel_file"):
        file = request.FILES["excel_file"]
        try:
            wb = openpyxl.load_workbook(file)
            # 기존 데이터 유지 혹은 삭제 (여기서는 덮어쓰기 개념으로 기존 아이템 삭제)
            Chapter.objects.filter(program=program).delete()
            
            for sheet in wb.sheetnames:
                ws = wb[sheet]
                for row in ws.iter_rows(min_row=2, values_only=True):
                    if not row[0]: continue  # 빈 행 스킵
                    
                    ch_num, ch_title, ch_desc, item_key, item_title, item_type, \
                    item_html, item_hint, item_ans, item_exp = (list(row) + [None]*10)[:10]
                    
                    chapter, _ = Chapter.objects.get_or_create(
                        program=program, 
                        number=ch_num,
                        defaults={"title": ch_title, "content": ch_desc}
                    )
                    
                    Item.objects.create(
                        chapter=chapter,
                        key=item_key,
                        title=item_title,
                        item_type=item_type or 'example',
                        explain_html=item_html,
                        hint=item_hint,
                        answer_code=item_ans,
                        expected_output=item_exp
                    )
            messages.success(request, "엑셀 데이터를 성공적으로 불러왔습니다.")
        except Exception as e:
            messages.error(request, f"엑셀 처리 중 오류 발생: {str(e)}")
            
    chapters = Chapter.objects.filter(program=program)
    return render(request, "courses/chapter_manage.html", {"program": program, "chapters": chapters})

# --- (9) 아이템 등록 ---
@login_required
@user_passes_test(is_admin)
def item_create(request, chapter_id):
    chapter = get_object_or_404(Chapter, id=chapter_id)
    if request.method == "POST":
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.chapter = chapter
            item.save()
            messages.success(request, f"'{item.title}' 아이템이 등록되었습니다.")
            return redirect("chapter_detail", chapter_id=chapter.id)
    else:
        # 마지막 번호 + 1 자동 제안
        last_num = Item.objects.filter(chapter=chapter).count() + 1
        form = ItemForm(initial={'chapter': chapter, 'number': last_num})
    
    return render(request, "courses/item_form.html", {
        "form": form,
        "title": f"[{chapter.title}] 새 아이템 추가",
        "chapter": chapter
    })

# --- (10) 아이템 수정 ---
@login_required
@user_passes_test(is_admin)
def item_edit(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    if request.method == "POST":
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f"'{item.title}' 아이템이 수정되었습니다.")
            return redirect("item_page", item_id=item.id)
    else:
        form = ItemForm(instance=item)
    
    return render(request, "courses/item_form.html", {
        "form": form,
        "title": "아이템 수정",
        "item": item
    })

# --- (11) 아이템 삭제 ---
@login_required
@user_passes_test(is_admin)
def item_delete(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    chapter_id = item.chapter.id
    if request.method == "POST":
        title = item.title
        item.delete()
        messages.success(request, f"'{title}' 아이템이 삭제되었습니다.")
        return redirect("chapter_detail", chapter_id=chapter_id)
    return render(request, "courses/item_confirm_delete.html", {"item": item})
# --- (8) 학생용 숙제 관리 (홈플레이) ---
@login_required
@require_full_member
def student_homework_list(request):
    # 내가 수강 신청한 프로그램 ID 목록
    enrolled_ids = LearningEnrollment.objects.filter(user=request.user).values_list("program_id", flat=True)
    
    # 노출 조건:
    # 1. (내가 수강 중인 과정의 과제) AND (특정 배정이 없는 전체 공개 과제)
    # 2. OR (내가 직접 배정인원으로 등록된 모든 과제)
    assignments = HomeworkAssignment.objects.filter(
        Q(program_id__in=enrolled_ids, assigned_users__isnull=True) |
        Q(assigned_users=request.user),
        is_active=True
    ).select_related('program').prefetch_related('linked_items', 'assigned_users').distinct().order_by('due_date', '-created_at')
    
    # 각 과제별 진행 상태 및 완료 여부 계산
    for assignment in assignments:
        items = assignment.linked_items.all()
        if items.exists():
            completed_count = UserProgress.objects.filter(
                user=request.user, 
                item__in=items, 
                completed=True
            ).count()
            assignment.is_completed = (completed_count == items.count())
            assignment.progress_text = f"{completed_count}/{items.count()}"
        else:
            assignment.is_completed = True
            assignment.progress_text = "N/A"
        
    return render(request, "courses/student_homework_list.html", {
        "assignments": assignments,
    })

# --- (9) 관리자용 숙제 관리 (CRUD) ---
@login_required
@user_passes_test(is_admin)
def homework_admin_list(request):
    assignments = HomeworkAssignment.objects.all().select_related('program').order_by('-created_at')
    return render(request, "courses/homework_admin_list.html", {"assignments": assignments})

@login_required
@user_passes_test(is_admin)
def homework_create(request):
    if request.method == "POST":
        form = HomeworkForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "새 과제가 등록되었습니다.")
            return redirect("homework_admin_list")
    else:
        form = HomeworkForm()
    return render(request, "courses/homework_form.html", {"form": form, "title": "새 과제 등록"})

@login_required
@user_passes_test(is_admin)
def homework_edit(request, homework_id):
    assignment = get_object_or_404(HomeworkAssignment, id=homework_id)
    if request.method == "POST":
        form = HomeworkForm(request.POST, instance=assignment)
        if form.is_valid():
            form.save()
            messages.success(request, f"'{assignment.title}' 과제가 수정되었습니다.")
            return redirect("homework_admin_list")
    else:
        form = HomeworkForm(instance=assignment)
    return render(request, "courses/homework_form.html", {"form": form, "title": "과제 수정"})

@login_required
@user_passes_test(is_admin)
def homework_delete(request, homework_id):
    assignment = get_object_or_404(HomeworkAssignment, id=homework_id)
    if request.method == "POST":
        assignment.delete()
        messages.success(request, "과제가 삭제되었습니다.")
        return redirect("homework_admin_list")
    return render(request, "courses/homework_confirm_delete.html", {"assignment": assignment})

# --- (10) API: 프로그램 구조 조회 (과정 → 단원 → 문제) ---
@login_required
@user_passes_test(is_admin)
def api_program_structure(request, program_id):
    """과정 ID를 받아 단원(Chapter)과 하위 문제(Item)들을 JSON으로 반환"""
    chapters = Chapter.objects.filter(program_id=program_id).order_by('number')
    data = []
    for ch in chapters:
        items = Item.objects.filter(chapter=ch).order_by('number')
        data.append({
            'chapter_id': ch.id,
            'chapter_title': f"{ch.number}장: {ch.title}",
            'items': [{'id': item.id, 'title': f"{item.number}. {item.title}", 'type': item.get_item_type_display()} for item in items]
        })
    return JsonResponse({'chapters': data})

# --- (11) API: 학생 검색 ---
@login_required
@user_passes_test(is_admin)
def api_search_users(request):
    """학생 이름/아이디로 검색하여 JSON 반환"""
    query = request.GET.get('q', '').strip()
    from django.contrib.auth.models import User
    users = User.objects.filter(is_staff=False, is_superuser=False)
    if query:
        users = users.filter(Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query))
    users = users[:50]
    data = [{'id': u.id, 'username': u.username, 'name': u.get_full_name() or u.username} for u in users]
    return JsonResponse({'users': data})
