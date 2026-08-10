import json
import zipfile
import io
import re
import os
import uuid
import base64
from collections import OrderedDict
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.db import DatabaseError
from django.db.models import Count, Q, Case, When, Value, IntegerField
from django.contrib.auth import login
from django.contrib import messages
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from .badge_service import get_active_badges_with_user_state, get_recent_user_badges, get_user_badge_count
from .models import Badge, Project, Category, Like, Bookmark, Tag, UserProfile, EmailChangeRequest, SignupEmailVerification, ScheduleAttachment, ScheduleEvent, Notice, Award, Certification, CertInfo, CompetitionType, Contest
from .forms import ProjectUploadForm, SignUpForm, AdminUserForm, AdminUserProfileForm, BadgeForm, ScheduleEventForm, TimetableForm, UserProfileUpdateForm
from .holiday_utils import ensure_holidays


SCHEDULE_EVENT_COLORS = {
    ScheduleEvent.EVENT_TYPE_HOLIDAY: '#ff5d6c',
    ScheduleEvent.EVENT_TYPE_ACADEMIC: '#3b82f6',
    ScheduleEvent.EVENT_TYPE_COMPETITION: '#f5c451',
    ScheduleEvent.EVENT_TYPE_SEMINAR: '#00ffb4',
    ScheduleEvent.EVENT_TYPE_CERTIFICATION: '#a855f7',
}

def get_certinfo_group_name(name):
    return re.sub(r'\s+', ' ', (name or '').strip())


def home(request):
    """메인 페이지 - 작품 리스트"""
    category_slug = request.GET.get('category', '')
    search = request.GET.get('q', '')

    projects = Project.objects.filter(status='approved').select_related('author').prefetch_related('categories', 'tags')

    if category_slug:
        projects = projects.filter(categories__name=category_slug)
    if search:
        projects = projects.filter(
            Q(title__icontains=search) |
            Q(author_display_name__icontains=search) |
            Q(description__icontains=search)
        )

    # 유저의 좋아요/즐겨찾기 상태
    user_likes = set()
    user_bookmarks = set()
    if request.user.is_authenticated:
        user_likes = set(Like.objects.filter(user=request.user).values_list('project_id', flat=True))
        user_bookmarks = set(Bookmark.objects.filter(user=request.user).values_list('project_id', flat=True))

    categories = Category.objects.all()
    featured = Project.objects.filter(status='approved', is_featured=True)[:4]

    total_plays = sum(p.play_count for p in Project.objects.filter(status='approved'))
    total_projects = Project.objects.filter(status='approved').count()

    from arcade.models import Award, Certification
    total_awards = Award.objects.count()
    total_certs = Certification.objects.count()

    context = {
        'projects': projects,
        'categories': categories,
        'featured': featured,
        'current_category': category_slug,
        'search_query': search,
        'user_likes': user_likes,
        'user_bookmarks': user_bookmarks,
        'total_plays': total_plays,
        'total_projects': total_projects,
        'total_awards': total_awards,
        'total_certs': total_certs,
    }
    return render(request, 'arcade/home.html', context)


def ai_prompts(request):
    return render(request, 'arcade/ai_prompts.html')


def ai_favorites(request):
    return render(request, 'arcade/ai_favorites.html')


def login_helper(request):
    from .models import SiteConfig
    val = SiteConfig.get_value('lh_unlock_expiry')
    expiry_ts = float(val) if val else None
    now_ts = timezone.now().timestamp()
    is_unlocked = bool(expiry_ts and expiry_ts > now_ts)
    remaining_minutes = int((expiry_ts - now_ts) / 60) if is_unlocked else 0
    links_json = SiteConfig.get_value('lh_link_overrides', '{}')
    return render(request, 'arcade/login_helper.html', {
        'is_unlocked': is_unlocked,
        'remaining_minutes': remaining_minutes,
        'is_admin': request.user.is_staff,
        'links_json': links_json,
    })


@require_POST
def api_login_helper_links_save(request):
    from .models import SiteConfig
    from django.conf import settings as django_settings
    if not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': '권한 없음'}, status=403)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'ok': False, 'error': 'invalid json'}, status=400)
    overrides = data.get('overrides', {})
    SiteConfig.set_value('lh_link_overrides', json.dumps(overrides, ensure_ascii=False))
    return JsonResponse({'ok': True})


@require_POST
def api_login_helper_lock(request):
    from .models import SiteConfig
    from django.conf import settings as django_settings
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'ok': False}, status=400)
    correct_pw = getattr(django_settings, 'LOGIN_HELPER_PASSWORD', 'medu2025!')
    if not request.user.is_staff and data.get('password', '') != correct_pw:
        return JsonResponse({'ok': False, 'error': '비밀번호가 틀렸습니다'}, status=403)
    SiteConfig.delete_key('lh_unlock_expiry')
    return JsonResponse({'ok': True})


@require_POST
def api_login_helper_unlock(request):
    from .models import SiteConfig
    from django.conf import settings as django_settings
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'ok': False, 'error': '잘못된 요청'}, status=400)

    password = data.get('password', '')
    hours = int(data.get('hours', 3))
    hours = min(max(hours, 1), 24)

    correct_pw = getattr(django_settings, 'LOGIN_HELPER_PASSWORD', 'medu2025!')
    if not request.user.is_staff and password != correct_pw:
        return JsonResponse({'ok': False, 'error': '비밀번호가 틀렸습니다'}, status=403)

    now_ts = timezone.now().timestamp()
    if data.get('extend'):
        val = SiteConfig.get_value('lh_unlock_expiry')
        current_expiry = float(val) if val else now_ts
        expiry_ts = max(current_expiry, now_ts) + hours * 3600
    else:
        expiry_ts = now_ts + hours * 3600

    SiteConfig.set_value('lh_unlock_expiry', expiry_ts)
    return JsonResponse({'ok': True, 'hours': hours})


def team_name(request):
    return render(request, 'arcade/team_name.html')


def problem_finder(request):
    return render(request, 'arcade/problem_finder.html')


PROMPTS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'presentation_prompts.json')

def _load_presentation_prompts():
    if os.path.exists(PROMPTS_FILE):
        with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def presentation_script(request):
    prompts = _load_presentation_prompts()
    return render(request, 'arcade/presentation_script.html', {'custom_prompts': json.dumps(prompts)})


@require_POST
def api_presentation_prompt_save(request):
    if not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': '권한이 없습니다.'}, status=403)
    try:
        body = json.loads(request.body)
        target = body.get('target')
        content = body.get('content', '').strip()
        if target not in ('elementary', 'middle'):
            return JsonResponse({'ok': False, 'error': '잘못된 대상입니다.'})
        prompts = _load_presentation_prompts()
        prompts[target] = content
        os.makedirs(os.path.dirname(PROMPTS_FILE), exist_ok=True)
        with open(PROMPTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, ensure_ascii=False, indent=2)
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)})


@require_POST
def api_problem_join(request):
    from .models import ProblemRoom, ProblemMember
    import secrets
    try:
        body = json.loads(request.body)
    except Exception:
        return JsonResponse({'ok': False, 'error': 'invalid json'}, status=400)
    team = body.get('team', '').strip()
    name = body.get('name', '').strip()
    stored_key = body.get('session_key', '')
    want_leader = bool(body.get('is_leader', False))
    if not team or not name:
        return JsonResponse({'ok': False, 'error': '팀과 이름을 입력해주세요'}, status=400)
    room, _ = ProblemRoom.objects.get_or_create(team_name=team)
    session_key = stored_key if stored_key else secrets.token_urlsafe(32)
    # 조장 요청 시 최근 90초 내 활성 조장이 있는지만 확인
    active_cutoff = timezone.now() - timedelta(seconds=90)
    already_has_leader = room.members.filter(
        is_leader=True, last_seen__gte=active_cutoff
    ).exclude(session_key=session_key).exists()
    if want_leader and already_has_leader:
        return JsonResponse({'ok': False, 'error': '이미 조장이 있습니다'}, status=400)
    member, created = ProblemMember.objects.get_or_create(
        room=room, session_key=session_key,
        defaults={'name': name, 'is_leader': want_leader, 'data': {}}
    )
    if not created:
        update_fields = ['name', 'last_seen']
        if want_leader and not member.is_leader:
            member.is_leader = True
            update_fields.append('is_leader')
        member.name = name
        member.save(update_fields=update_fields)
    return JsonResponse({
        'ok': True, 'room_id': room.id,
        'member_id': member.id, 'session_key': session_key,
        'is_leader': member.is_leader,
    })


def api_problem_team_info(request):
    from .models import ProblemRoom, ProblemMember
    team = request.GET.get('team', '').strip()
    if not team:
        return JsonResponse({'has_leader': False, 'leader_name': None})
    try:
        room = ProblemRoom.objects.get(team_name=team)
        active_cutoff = timezone.now() - timedelta(seconds=90)
        leader = room.members.filter(is_leader=True, last_seen__gte=active_cutoff).first()
        # 요청자 본인이 조장이면 has_leader=False로 — 재입장 허용
        my_key = request.GET.get('session_key', '')
        is_me = bool(my_key and leader and leader.session_key == my_key)
        return JsonResponse({
            'has_leader': bool(leader) and not is_me,
            'leader_name': leader.name if leader else None,
        })
    except ProblemRoom.DoesNotExist:
        return JsonResponse({'has_leader': False, 'leader_name': None})


@require_POST
def api_problem_update(request):
    from .models import ProblemMember
    try:
        body = json.loads(request.body)
    except Exception:
        return JsonResponse({'ok': False, 'error': 'invalid json'}, status=400)
    member_id = body.get('member_id')
    session_key = body.get('session_key', '')
    try:
        member = ProblemMember.objects.get(id=member_id, session_key=session_key)
        member.data = body.get('data', {})
        member.save(update_fields=['data', 'last_seen'])
        return JsonResponse({'ok': True})
    except ProblemMember.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'not found'}, status=404)


def api_problem_room_state(request, room_id):
    from .models import ProblemRoom, ProblemMember
    cutoff = timezone.now() - timedelta(seconds=90)
    try:
        room = ProblemRoom.objects.get(id=room_id)
    except ProblemRoom.DoesNotExist:
        return JsonResponse({'ok': False}, status=404)
    member_id = request.GET.get('member_id')
    session_key = request.GET.get('session_key', '')
    if member_id and session_key:
        ProblemMember.objects.filter(
            id=member_id, room=room, session_key=session_key
        ).update(last_seen=timezone.now())
    members = list(room.members.filter(last_seen__gte=cutoff).values('id', 'name', 'is_leader', 'data'))
    n = len(members)
    threshold = n / 2

    def collect_single(field):
        result = {}
        for m in members:
            val = m['data'].get(field)
            if val:
                result.setdefault(val, [])
                result[val].append(m['name'])
        return result

    def collect_multi(field):
        result = {}
        for m in members:
            for v in (m['data'].get(field) or []):
                result.setdefault(v, [])
                result[v].append(m['name'])
        return result

    def majority_single(d):
        for val, names in d.items():
            if len(names) > threshold:
                return val
        return None

    def majority_multi(d):
        return [v for v, names in d.items() if len(names) > threshold]

    def collect_customs(field):
        seen, result = set(), []
        for m in members:
            v = (m['data'].get(field) or '').strip()
            if v and v not in seen:
                seen.add(v)
                result.append({'value': v, 'author': m['name']})
        return result

    def collect_exps_with_custom():
        result = {}
        for m in members:
            for v in (m['data'].get('exps') or []):
                result.setdefault(v, []).append(m['name'])
            custom_val = (m['data'].get('expCustom') or '').strip()
            if custom_val and m['name'] not in result.get(custom_val, []):
                result.setdefault(custom_val, []).append(m['name'])
        return result

    sel = {
        'area':    collect_single('area'),
        'subArea': collect_single('subArea'),
        'exps':    collect_exps_with_custom(),
        'freq':    collect_single('freq'),
        'situation': collect_single('situation'),
        'affected':  collect_single('affected'),
        'severity':  collect_single('severity'),
        'solution':  collect_single('solution'),
    }
    maj = {
        'area':      majority_single(sel['area']),
        'subArea':   majority_single(sel['subArea']),
        'exps':      majority_multi(sel['exps']),
        'freq':      majority_single(sel['freq']),
        'situation': majority_single(sel['situation']),
        'affected':  majority_single(sel['affected']),
        'severity':  majority_single(sel['severity']),
        'solution':  majority_single(sel['solution']),
    }
    customs = {
        'area':     collect_customs('areaCustom'),
        'subArea':  collect_customs('subAreaCustom'),
        'exp':      collect_customs('expCustom'),
        'affected': collect_customs('affectedCustom'),
        'severity': collect_customs('severityCustom'),
        'solution': collect_customs('solutionCustom'),
        'situation': collect_customs('situationCustom'),
    }
    sit_seen, situation_options = set(), []
    for m in members:
        for ex in (m['data'].get('selectedExamples') or []):
            if ex and ex not in sit_seen:
                sit_seen.add(ex); situation_options.append(ex)
        cust = (m['data'].get('situationCustom') or '').strip()
        if cust and cust not in sit_seen:
            sit_seen.add(cust); situation_options.append(cust)
    leader = next((m for m in members if m['is_leader']), None)
    leader_step = leader['data'].get('current_step', 1) if leader else 1
    req_member_id = request.GET.get('member_id')
    my_is_leader = any(str(m['id']) == str(req_member_id) and m['is_leader'] for m in members)
    return JsonResponse({
        'ok': True,
        'team_name': room.team_name,
        'member_count': n,
        'threshold': threshold,
        'members': [{'name': m['name'], 'is_leader': m['is_leader'], 'data': m['data']} for m in members],
        'leader_name': leader['name'] if leader else None,
        'leader_step': leader_step,
        'my_is_leader': my_is_leader,
        'selections': sel,
        'majority': maj,
        'customs': customs,
        'situation_options': situation_options,
    })


def my_avatar(request):
    from .models import AvatarDraft
    draft_data = {}
    if request.user.is_authenticated:
        try:
            draft_data = request.user.avatar_draft.data
        except AvatarDraft.DoesNotExist:
            pass
    return render(request, 'arcade/my_avatar.html', {
        'draft_data': json.dumps(draft_data),
        'user_authenticated': request.user.is_authenticated,
    })


@require_POST
def api_avatar_draft_save(request):
    from .models import AvatarDraft
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'login required'}, status=401)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'invalid json'}, status=400)
    AvatarDraft.objects.update_or_create(user=request.user, defaults={'data': data})
    return JsonResponse({'ok': True})


def schedule_view(request):
    ensure_holidays()
    events = ScheduleEvent.objects.filter(is_active=True).order_by('start_date', 'start_time', 'title')
    today = timezone.localdate()
    upcoming_events = events.filter(start_date__gte=today)
    academic_events = events.filter(event_type=ScheduleEvent.EVENT_TYPE_ACADEMIC)
    
    calendar_events = []

    for event in events:
        color = SCHEDULE_EVENT_COLORS.get(event.event_type, '#00b4ff')
        attachments = list(event.attachments.all())
        cal_event = {
            'id': event.id,
            'title': event.title,
            'backgroundColor': color,
            'borderColor': color,
            'textColor': '#08080f' if event.event_type in {ScheduleEvent.EVENT_TYPE_COMPETITION, ScheduleEvent.EVENT_TYPE_SEMINAR} else '#ffffff',
            'extendedProps': {
                'description': event.description or '',
                'eventType': event.event_type,
                'eventTypeLabel': event.get_event_type_display(),
                'imageUrl': event.image.url if event.image else '',
                'externalUrl': event.external_url or '',
                'attachments': [{'name': a.file.name.split('/')[-1], 'url': a.file.url} for a in attachments],
            },
        }

        if event.event_type == ScheduleEvent.EVENT_TYPE_ACADEMIC and event.days_of_week:
            # 반복 일정 설정 (FullCalendar)
            days = [int(d) for d in event.days_of_week.split(',')]
            cal_event['daysOfWeek'] = days
            if event.start_time:
                cal_event['startTime'] = event.start_time.strftime('%H:%M:%S')
            if event.end_time:
                cal_event['endTime'] = event.end_time.strftime('%H:%M:%S')
            
            day_names = ['일', '월', '화', '수', '목', '금', '토']
            days_str = ', '.join([day_names[d] for d in days])
            time_str = ''
            if event.start_time and event.end_time:
                time_str = f" {event.start_time.strftime('%H:%M')} ~ {event.end_time.strftime('%H:%M')}"
            
            cal_event['extendedProps']['startDate'] = f"매주 {days_str}요일{time_str}"
            cal_event['extendedProps']['endDate'] = ""
        else:
            if event.start_date:
                cal_event['start'] = event.start_date.isoformat()
                cal_event['extendedProps']['startDate'] = event.start_date.strftime('%Y.%m.%d %H:%M')
            if event.end_date:
                cal_event['end'] = event.end_date.isoformat()
                cal_event['extendedProps']['endDate'] = event.end_date.strftime('%Y.%m.%d %H:%M')
            else:
                cal_event['extendedProps']['endDate'] = ""

        calendar_events.append(cal_event)

        if getattr(event, 'days_of_week', None):
            day_names = ['일', '월', '화', '수', '목', '금', '토']
            days = [int(d) for d in event.days_of_week.split(',')]
            days_str = ', '.join([day_names[d] for d in days])
            event.parsed_days_str = days_str
        
    context = {
        'calendar_events_json': calendar_events,
        'upcoming_competitions': upcoming_events.filter(event_type=ScheduleEvent.EVENT_TYPE_COMPETITION)[:4],
        'upcoming_certifications': upcoming_events.filter(event_type=ScheduleEvent.EVENT_TYPE_CERTIFICATION)[:4],
        'academic_events': academic_events[:6],
        'seminar_events': upcoming_events.filter(event_type=ScheduleEvent.EVENT_TYPE_SEMINAR)[:6],
    }
    return render(request, 'arcade/schedule.html', context)


def play(request, slug):
    """작품 플레이 페이지"""
    project = get_object_or_404(Project, slug=slug, status='approved')

    # 플레이 카운트 증가
    Project.objects.filter(pk=project.pk).update(play_count=project.play_count + 1)

    user_liked = False
    user_bookmarked = False
    if request.user.is_authenticated:
        user_liked = Like.objects.filter(user=request.user, project=project).exists()
        user_bookmarked = Bookmark.objects.filter(user=request.user, project=project).exists()

    context = {
        'project': project,
        'user_liked': user_liked,
        'user_bookmarked': user_bookmarked,
    }
    response = render(request, 'arcade/play.html', context)
    return xframe_options_sameorigin(lambda req: response)(request)


@login_required
def project_preview(request, project_id):
    """관리자/작성자용 작품 미리보기 페이지"""
    project = get_object_or_404(Project, pk=project_id)
    if not (request.user.is_staff or request.user == project.author):
        messages.error(request, '작품 미리보기 권한이 없습니다.')
        return redirect('my_projects')

    user_liked = False
    user_bookmarked = False
    if request.user.is_authenticated:
        user_liked = Like.objects.filter(user=request.user, project=project).exists()
        user_bookmarked = Bookmark.objects.filter(user=request.user, project=project).exists()

    context = {
        'project': project,
        'user_liked': user_liked,
        'user_bookmarked': user_bookmarked,
        'is_preview_mode': True,
    }
    response = render(request, 'arcade/play.html', context)
    return xframe_options_sameorigin(lambda req: response)(request)


@login_required
@require_POST
def delete_project(request, project_id):
    """작품 삭제"""
    project = get_object_or_404(Project, pk=project_id)
    
    # 본인 또는 관리자만 삭제 가능
    if project.author != request.user and not request.user.is_staff:
        messages.error(request, '본인의 작품만 삭제할 수 있습니다.')
        return redirect('my_projects')
    
    title = project.title
    project.delete()
    messages.success(request, f'"{title}" 작품이 삭제되었습니다.')
    return redirect('my_projects')


@login_required
def edit_project(request, project_id):
    """작품 수정"""
    project = get_object_or_404(Project, pk=project_id)
    
    # 본인 또는 관리자만 수정 가능
    if project.author != request.user and not request.user.is_staff:
        messages.error(request, '본인의 작품만 수정할 수 있습니다.')
        return redirect('my_projects')
    
    if request.method == 'POST':
        form = ProjectUploadForm(request.POST, request.FILES, instance=project, user=request.user)
        if form.is_valid():
            updated = form.save(commit=False)
            
            # 일반 사용자는 본인이 제작자여야 하며 제작자를 바꿀 수 없음
            if not request.user.is_staff:
                updated.author = request.user
            # 수동 썸네일이 없고 자동 썸네일이 전달된 경우 적용
            if not request.FILES.get('thumbnail'):
                import json as _json
                raw = request.POST.get('auto_thumbnail_b64_list', '')
                try:
                    b64_list = _json.loads(raw) if raw else []
                except Exception:
                    b64_list = [request.POST.get('auto_thumbnail_b64', '')]
                _apply_auto_thumbnails(updated, b64_list)
            updated.save()
            form.save_m2m()
            messages.success(request, '작품 정보가 수정되었습니다! ✨')
            return redirect('my_projects')
    else:
        form = ProjectUploadForm(instance=project, user=request.user)
    
    context = {
        'form': form,
        'is_edit': True,
        'project': project,
    }
    return render(request, 'arcade/upload.html', context)


def _apply_auto_thumbnails(project, b64_list):
    """base64 PNG 리스트를 Project thumbnail/thumbnail_2/thumbnail_3에 설정"""
    fields = ['thumbnail', 'thumbnail_2', 'thumbnail_3']
    for i, b64_data in enumerate(b64_list[:3]):
        if not b64_data:
            continue
        try:
            img_bytes = base64.b64decode(b64_data)
            img_io = io.BytesIO(img_bytes)
            filename = f'auto_{uuid.uuid4().hex[:8]}.png'
            setattr(project, fields[i], InMemoryUploadedFile(
                img_io, fields[i], filename, 'image/png', len(img_bytes), None
            ))
        except Exception:
            continue


@login_required
def upload(request):
    """작품 업로드 페이지"""
    if request.method == 'POST':
        form = ProjectUploadForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            project = form.save(commit=False)
            
            # 제작자 결정: 관리자면 폼 선택값 우선, 아니면 현재 사용자
            if not request.user.is_staff or not project.author:
                project.author = request.user
            # 수동 썸네일이 없을 때 자동 생성 썸네일 적용 (최대 3개)
            if not request.FILES.get('thumbnail'):
                import json as _json
                raw = request.POST.get('auto_thumbnail_b64_list', '')
                try:
                    b64_list = _json.loads(raw) if raw else []
                except Exception:
                    b64_list = [request.POST.get('auto_thumbnail_b64', '')]
                _apply_auto_thumbnails(project, b64_list)
            # 관리자는 바로 승인, 학생은 심사 대기
            if request.user.is_staff:
                project.status = 'approved'
            else:
                project.status = 'pending'
            project.save()
            form.save_m2m()  # ManyToMany 필드(categories, tags) 저장을 위해 필구
            if project.status == 'approved':
                messages.success(request, '작품이 등록되었습니다! 🎉')
            else:
                messages.success(request, '작품이 제출되었습니다! 선생님 승인 후 공개됩니다. ⏳')
            return redirect('home')
    else:
        form = ProjectUploadForm(user=request.user)

    return render(request, 'arcade/upload.html', {'form': form})


@login_required
@require_POST
def analyze_zip(request):
    """ZIP 파일을 분석하여 메타데이터(arcade.json) 추출 + 썸네일 자동 생성"""
    zip_file = request.FILES.get('project_zip')
    if not zip_file:
        return JsonResponse({'error': '파일이 없습니다.'}, status=400)

    try:
        zip_bytes = zip_file.read()
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            # arcade.json 또는 arcade_info.json 파일 찾기
            json_path = None
            for name in zf.namelist():
                lower_name = name.lower()
                if lower_name.endswith('arcade.json') or lower_name.endswith('arcade_info.json'):
                    if json_path is None or name.count('/') < json_path.count('/'):
                        json_path = name

            guessed = False
            if not json_path:
                result = guess_project_metadata(zf, zip_file.name)
                guessed = True
            else:
                with zf.open(json_path) as f:
                    data = json.loads(f.read().decode('utf-8'))
                category_names = data.get('categories', [])
                if isinstance(category_names, str):
                    category_names = [category_names]
                matched_category_ids = list(Category.objects.filter(
                    name__in=category_names
                ).values_list('id', flat=True))
                tags_list = data.get('tags', [])
                tags_str = ', '.join(tags_list) if isinstance(tags_list, list) else str(tags_list)
                result = {
                    'title': data.get('title', ''),
                    'description': data.get('description', ''),
                    'tags_str': tags_str,
                    'category_ids': matched_category_ids,
                }

            # 썸네일 자동 생성 (최대 3개)
            tags_set = set(t.strip() for t in result.get('tags_str', '').split(',') if t.strip())
            result['thumbnail_b64_list'] = generate_auto_thumbnails(zf, result.get('title', ''), tags_set)
            # 하위 호환
            result['thumbnail_b64'] = result['thumbnail_b64_list'][0] if result['thumbnail_b64_list'] else ''

            return JsonResponse({'success': True, 'data': result, 'guessed': guessed})

    except Exception as e:
        return JsonResponse({'error': f'ZIP 분석 중 오류 발생: {str(e)}'}, status=500)


def _get_pil_font(size):
    """한글 지원 폰트 탐색 (없으면 기본 폰트)"""
    from PIL import ImageFont
    candidates = [
        # Windows
        'C:/Windows/Fonts/malgun.ttf',
        'C:/Windows/Fonts/malgunbd.ttf',
        'C:/Windows/Fonts/gulim.ttc',
        'C:/Windows/Fonts/arial.ttf',
        # Linux/Mac
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/System/Library/Fonts/AppleSDGothicNeo.ttc',
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def generate_auto_thumbnails(zf, title, tags):
    """
    ZIP 안에서 이미지를 최대 3장 추출하거나, 부족하면 Pillow로 3가지 스타일 썸네일을 생성.
    반환값: base64 PNG 문자열 리스트 (최대 3개, 실패 항목은 제외)
    """
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return []

    THUMB_W, THUMB_H = 480, 270

    # ── 장르별 포인트 색상 ─────────────────────────────────────────────────
    GENRE_COLORS = {
        '슈팅게임': (233, 69, 96),   '플랫포머': (75, 160, 255),
        '퍼즐게임': (160, 100, 255),  '러닝게임': (0, 220, 130),
        '대전게임': (255, 140, 0),    'RPG': (200, 80, 255),
        '아케이드': (0, 210, 200),    '겨울테마': (100, 200, 255),
        'AI/ML': (0, 255, 160),       '퀴즈게임': (255, 200, 0),
        '타워디펜스': (255, 100, 50), '리듬게임': (255, 80, 200),
        'Pygame': (100, 180, 100),    'HTML5캔버스': (255, 165, 0),
    }
    accent = (233, 69, 96)
    for genre, color in GENRE_COLORS.items():
        if genre in tags:
            accent = color
            break
    ar, ag, ab = accent

    # ── 폰트 준비 ─────────────────────────────────────────────────────────
    font_big   = _get_pil_font(40)
    font_mid   = _get_pil_font(22)
    font_tag   = _get_pil_font(13)
    font_small = _get_pil_font(12)
    font_wm    = _get_pil_font(11)

    # ── 태그 우선순위 정렬 ────────────────────────────────────────────────
    priority_order = [
        '슈팅게임', '플랫포머', '퍼즐게임', '러닝게임', '대전게임', 'RPG',
        '아케이드', '겨울테마', 'AI/ML', '퀴즈게임', '타워디펜스', '리듬게임',
        'Pygame', 'HTML5캔버스', '2인용', '스코어경쟁', '키보드컨트롤',
    ]
    show_tags = [t for t in priority_order if t in tags][:4]
    if not show_tags:
        show_tags = sorted(tags)[:4]

    display_title = title if len(title) <= 11 else title[:10] + '…'

    results = []

    # ── ZIP 안 실제 이미지 먼저 최대 3장 추출 ─────────────────────────────
    image_exts = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')
    priority_kw = ['screenshot', 'thumbnail', 'thumb', 'preview', 'cover', 'banner']
    candidates = []
    for name in zf.namelist():
        lower = name.lower()
        base_n = os.path.basename(lower)
        if not lower.endswith(image_exts):
            continue
        score = sum(10 for kw in priority_kw if kw in base_n)
        if lower.count('/') == 0:
            score += 5
        candidates.append((score, name))
    candidates.sort(key=lambda x: -x[0])

    for _, img_name in candidates[:3]:
        try:
            with zf.open(img_name) as f:
                raw = f.read()
            img = Image.open(io.BytesIO(raw)).convert('RGB')
            img.thumbnail((THUMB_W, THUMB_H), Image.LANCZOS)
            canvas = Image.new('RGB', (THUMB_W, THUMB_H), (18, 18, 35))
            canvas.paste(img, ((THUMB_W - img.width) // 2, (THUMB_H - img.height) // 2))
            buf = io.BytesIO()
            canvas.save(buf, format='PNG', optimize=True)
            results.append(base64.b64encode(buf.getvalue()).decode())
        except Exception:
            continue

    # ── 부족한 슬롯은 Pillow 생성으로 채움 ───────────────────────────────
    needed = 3 - len(results)
    if needed <= 0:
        return results[:3]

    def _draw_tag_chips(draw, tags_list, cx_start, cy, font, accent_rgb):
        """태그 칩 row 그리기 (중앙 정렬)"""
        if not tags_list:
            return
        pad_x, chip_h, gap = 12, 22, 7
        widths = []
        for t in tags_list:
            bb = draw.textbbox((0, 0), t, font=font)
            widths.append(bb[2] - bb[0] + pad_x * 2)
        total = sum(widths) + gap * (len(tags_list) - 1)
        x = cx_start - total // 2
        ar2, ag2, ab2 = accent_rgb
        for i, t in enumerate(tags_list):
            w = widths[i]
            draw.rounded_rectangle(
                [(x, cy), (x + w, cy + chip_h)], radius=11,
                fill=(min(ar2 + 40, 255), min(ag2 + 30, 255), min(ab2 + 30, 255)),
            )
            bb = draw.textbbox((0, 0), t, font=font)
            draw.text((x + (w - (bb[2] - bb[0])) // 2, cy + 4), t,
                      font=font, fill=(255, 255, 255))
            x += w + gap

    def _img_to_b64(img):
        buf = io.BytesIO()
        img.save(buf, format='PNG', optimize=True)
        return base64.b64encode(buf.getvalue()).decode()

    def _watermark(draw, accent_rgb):
        draw.text((10, THUMB_H - 20), 'MEDULAB ARCADE', font=font_wm, fill=accent_rgb)

    # ── 스타일 1: 포스터 (어두운 그라디언트 + 중앙 제목 + 태그 칩) ───────
    if needed > 0:
        img = Image.new('RGB', (THUMB_W, THUMB_H))
        draw = ImageDraw.Draw(img)
        for y in range(THUMB_H):
            t = y / THUMB_H
            draw.line([(0, y), (THUMB_W, y)],
                      fill=(int(12 + t * 8), int(12 + t * 6), int(28 + t * 20)))
        # 후광 원
        for cx, cy, rad, ratio in [(390, 55, 85, 0.07), (75, 225, 60, 0.05)]:
            c = (int(ar * ratio + 12), int(ag * ratio + 12), int(ab * ratio + 28))
            for dr in range(rad, 0, -5):
                draw.ellipse([(cx - dr, cy - dr), (cx + dr, cy + dr)], outline=c)
        draw.rectangle([(0, 0), (THUMB_W, 5)], fill=accent)
        # 제목
        bb = draw.textbbox((0, 0), display_title, font=font_big)
        tx = (THUMB_W - (bb[2] - bb[0])) // 2
        draw.text((tx + 2, 95), display_title, font=font_big, fill=(0, 0, 0))
        draw.text((tx, 93), display_title, font=font_big, fill=(255, 255, 255))
        # 태그 칩
        _draw_tag_chips(draw, show_tags[:3], THUMB_W // 2, 152, font_tag, accent)
        draw.rectangle([(0, THUMB_H - 4), (THUMB_W, THUMB_H)], fill=accent)
        _watermark(draw, accent)
        results.append(_img_to_b64(img))
        needed -= 1

    # ── 스타일 2: 스포트라이트 (액센트 방사형 + 큰 이모지/제목 하단) ──────
    if needed > 0:
        img = Image.new('RGB', (THUMB_W, THUMB_H), (10, 10, 22))
        draw = ImageDraw.Draw(img)
        # 중앙 방사형 그라디언트 (동심원으로 근사)
        max_r = int((THUMB_W ** 2 + THUMB_H ** 2) ** 0.5 // 2) + 10
        for r in range(max_r, 0, -4):
            ratio = r / max_r
            bg = (int(ar * (1 - ratio) * 0.45 + 10),
                  int(ag * (1 - ratio) * 0.45 + 10),
                  int(ab * (1 - ratio) * 0.45 + 22))
            draw.ellipse(
                [(THUMB_W // 2 - r, THUMB_H // 2 - r),
                 (THUMB_W // 2 + r, THUMB_H // 2 + r)],
                fill=bg,
            )
        # 제목 하단 좌측
        draw.text((22, THUMB_H - 78), display_title, font=font_big, fill=(255, 255, 255))
        # 장르 태그 한 줄
        genre_tag = show_tags[0] if show_tags else ''
        if genre_tag:
            bb = draw.textbbox((0, 0), genre_tag, font=font_mid)
            draw.rounded_rectangle(
                [(20, THUMB_H - 44), (20 + bb[2] - bb[0] + 20, THUMB_H - 20)],
                radius=10, fill=accent,
            )
            draw.text((30, THUMB_H - 42), genre_tag, font=font_mid, fill=(255, 255, 255))
        # 우측 상단 PLAY 버튼 느낌
        draw.rounded_rectangle([(THUMB_W - 80, 14), (THUMB_W - 14, 44)],
                                radius=15, fill=accent)
        bb = draw.textbbox((0, 0), 'PLAY', font=font_tag)
        draw.text((THUMB_W - 80 + (66 - (bb[2] - bb[0])) // 2, 22),
                  'PLAY', font=font_tag, fill=(255, 255, 255))
        _watermark(draw, accent)
        results.append(_img_to_b64(img))
        needed -= 1

    # ── 스타일 3: 피처 카드 (기능 목록 + 기술 스택) ──────────────────────
    if needed > 0:
        img = Image.new('RGB', (THUMB_W, THUMB_H), (14, 14, 26))
        draw = ImageDraw.Draw(img)
        # 좌측 액센트 세로 바
        draw.rectangle([(0, 0), (5, THUMB_H)], fill=accent)
        # 상단 제목
        draw.text((20, 20), display_title, font=font_mid, fill=(255, 255, 255))
        bb = draw.textbbox((0, 0), display_title, font=font_mid)
        lx = 20 + bb[2] - bb[0] + 10
        draw.line([(lx, 32), (THUMB_W - 20, 32)],
                  fill=(ar // 3, ag // 3, ab // 3), width=1)
        # 특징 목록 (태그 → bullet list)
        bullets = show_tags[:4]
        if not bullets:
            bullets = ['직접 플레이해보세요!']
        for i, b in enumerate(bullets):
            y = 50 + i * 28
            draw.rounded_rectangle([(18, y + 2), (26, y + 14)],
                                    radius=4, fill=accent)
            draw.text((34, y), b, font=font_small, fill=(220, 220, 220))
        # 하단 기술 스택
        tech_tags = [t for t in show_tags if t in ('Pygame', 'HTML5캔버스', 'JavaScript',
                                                     'Python', 'AI/ML', 'CSS3')][:3]
        if tech_tags:
            draw.text((20, THUMB_H - 38), '🛠  ' + '  ·  '.join(tech_tags),
                      font=font_small, fill=(ar, ag, ab))
        draw.rectangle([(0, THUMB_H - 4), (THUMB_W, THUMB_H)], fill=accent)
        _watermark(draw, accent)
        results.append(_img_to_b64(img))

    return results[:3]


# 하위 호환용 단일 반환 래퍼
def generate_auto_thumbnail(zf, title, tags):
    results = generate_auto_thumbnails(zf, title, tags)
    return results[0] if results else ''


def guess_project_metadata(zf, zip_filename):
    """ZIP 파일의 구성과 내용을 정밀 분석하여 풍성한 정보를 추측함"""
    zip_basename = os.path.basename(zip_filename)
    title = os.path.splitext(zip_basename)[0]

    file_list = zf.namelist()
    categories = set()
    tags = set()
    features = []
    controls = []
    tech_stack = []

    # ── 1. 파일명 키워드 분석 (한글·영문 복합 매핑) ───────────────────────
    title_lower = title.lower().replace('_', ' ').replace('-', ' ')
    title_keyword_map = {
        '싸움': ['대전게임', '액션'], '전투': ['대전게임', '액션'],
        '배틀': ['대전게임', '액션'], 'battle': ['대전게임', '액션'],
        '슈팅': ['슈팅게임', '액션'], '총': ['슈팅게임'],
        'shoot': ['슈팅게임'], 'shooter': ['슈팅게임'],
        '달리기': ['러닝게임', '아케이드'], '런': ['러닝게임'],
        'run': ['러닝게임'], 'runner': ['러닝게임'],
        '퍼즐': ['퍼즐게임', '두뇌게임'], 'puzzle': ['퍼즐게임'],
        '점프': ['플랫포머', '점프액션'], 'jump': ['플랫포머'],
        '플랫폼': ['플랫포머'], 'platform': ['플랫포머'],
        '뱀': ['클래식게임', '아케이드'], 'snake': ['클래식게임', '아케이드'],
        '테트리스': ['퍼즐게임', '클래식게임'], 'tetris': ['퍼즐게임', '클래식게임'],
        '블록': ['퍼즐게임', '블록게임'], 'block': ['퍼즐게임', '블록게임'],
        '미로': ['퍼즐게임', '미로탐험'], 'maze': ['퍼즐게임', '미로탐험'],
        '피하기': ['회피게임', '아케이드'], 'dodge': ['회피게임', '아케이드'],
        '눈덩이': ['눈덩이', '겨울테마', '대전게임'],
        '눈싸움': ['눈덩이', '대전게임', '겨울테마'],
        '눈': ['겨울테마'], '겨울': ['겨울테마'],
        '축구': ['스포츠게임', '축구'], '농구': ['스포츠게임', '농구'],
        '야구': ['스포츠게임', '야구'], '스포츠': ['스포츠게임'],
        '자동차': ['레이싱', '자동차'], '레이싱': ['레이싱게임'],
        'racing': ['레이싱게임'], 'car': ['레이싱', '자동차'],
        '우주': ['우주배경', '슈팅게임'], 'space': ['우주배경'],
        'galaxy': ['우주배경', '슈팅게임'],
        '좀비': ['좀비게임', '생존게임'], 'zombie': ['좀비게임', '생존게임'],
        '타워': ['타워디펜스', '전략게임'], 'tower': ['타워디펜스'],
        '카드': ['카드게임', '보드게임'], 'card': ['카드게임'],
        '보드': ['보드게임', '전략게임'],
        '퀴즈': ['퀴즈게임', '교육용'], 'quiz': ['퀴즈게임', '교육용'],
        'rpg': ['RPG', '롤플레잉'], '롤플레잉': ['RPG'],
        '핑퐁': ['탁구게임', '아케이드'], '탁구': ['탁구게임', '아케이드'],
        'pong': ['탁구게임', '아케이드'],
        '벽돌': ['아케이드', '클래식게임'], 'breakout': ['아케이드', '클래식게임'],
        '팩맨': ['클래식게임', '아케이드'], 'pacman': ['클래식게임', '아케이드'],
        '포켓몬': ['수집게임'], '수집': ['수집게임'],
        '방어': ['타워디펜스', '전략게임'], 'defense': ['타워디펜스'],
        '생존': ['생존게임'], 'survive': ['생존게임'], 'survival': ['생존게임'],
        '탐험': ['탐험게임', 'RPG'], 'adventure': ['탐험게임'],
        '음악': ['리듬게임'], '리듬': ['리듬게임'], 'rhythm': ['리듬게임'],
    }
    for keyword, related_tags in title_keyword_map.items():
        if keyword in title_lower or keyword in title:
            for t in related_tags:
                tags.add(t)

    # ── 2. 파일 구성 기반 기술 스택 감지 ─────────────────────────────────
    has_html = any(f.endswith('.html') for f in file_list)
    has_py   = any(f.endswith('.py') for f in file_list)
    has_js   = any(f.endswith('.js') for f in file_list)
    has_css  = any(f.endswith('.css') for f in file_list)
    has_image = any(f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.bmp')) for f in file_list)
    has_sound = any(f.lower().endswith(('.mp3', '.wav', '.ogg', '.flac')) for f in file_list)
    has_json  = any(f.endswith('.json') and 'arcade' not in f.lower() for f in file_list)

    # 카테고리는 이름으로 DB에서 조회 (ID 하드코딩 방지)
    def _cat_id(name):
        try:
            return Category.objects.get(name=name).id
        except Category.DoesNotExist:
            return None

    if has_py:
        cid = _cat_id('Python')
        if cid: categories.add(cid)
        tech_stack.append('Python')
        tags.add('Python')
    if has_html or has_js:
        cid = _cat_id('HTML/JS')
        if cid: categories.add(cid)
        if has_html: tech_stack.append('HTML5')
        if has_js:   tech_stack.append('JavaScript')
    if has_css:
        cid = _cat_id('CSS')
        if cid: categories.add(cid)
        tech_stack.append('CSS3')
    if has_image:
        tags.add('이미지 활용')
    if has_sound:
        tags.add('사운드 포함')
        features.append("배경음악 및 효과음")
    if has_json:
        tags.add('데이터파일')

    # ── 3. Python 소스 정밀 스캔 ──────────────────────────────────────────
    py_files = [f for f in file_list if f.endswith('.py') and '__pycache__' not in f]
    py_files.sort(key=lambda x: (x.count('/'), 'main' not in x.lower(), 'game' not in x.lower()))

    extracted_docstring = ""

    for py_file in py_files[:5]:
        try:
            with zf.open(py_file) as f:
                content = f.read().decode('utf-8', errors='ignore')
            lower = content.lower()

            # 제작자 주석/docstring 추출
            if not extracted_docstring:
                doc = re.search(r'^\s*[\'"]{3}(.*?)[\'"]{3}', content, re.DOTALL)
                if doc:
                    extracted_docstring = doc.group(1).strip()
                else:
                    lines = content.split('\n')
                    block = []
                    for line in lines:
                        stripped = line.strip()
                        if stripped.startswith('#'):
                            block.append(stripped.lstrip('#').strip())
                        elif not stripped:
                            continue
                        else:
                            break
                    if len(block) >= 2:
                        extracted_docstring = '\n'.join(block)

            # ── Pygame 감지 ──
            if 'pygame' in lower:
                cid = _cat_id('게임')
                if cid: categories.add(cid)
                tags.add('Pygame')
                tags.add('게임개발')
                if 'Pygame' not in tech_stack:
                    tech_stack.append('Pygame')

                # 키보드 조작
                keys = []
                if any(k in content for k in ['K_LEFT', 'K_RIGHT', 'K_UP', 'K_DOWN']): keys.append('방향키')
                if 'K_SPACE' in content: keys.append('스페이스바')
                if any(k in content for k in ['K_w', 'K_a', 'K_s', 'K_d', 'K_W', 'K_A', 'K_S', 'K_D']): keys.append('WASD')
                if 'K_RETURN' in content or 'K_KP_ENTER' in content: keys.append('엔터키')
                if any(k in content for k in ['K_z', 'K_x', 'K_c', 'K_Z', 'K_X', 'K_C']): keys.append('Z/X/C키')
                if any(k in content for k in ['K_1', 'K_2', 'K_3', 'K_4']): keys.append('숫자키')
                if keys:
                    controls.append(f"키보드: {', '.join(keys)}")
                    tags.add('키보드컨트롤')

                # 마우스 조작
                if 'mouse.get_pos' in lower or 'mousebuttondown' in lower or 'mousebuttonup' in lower:
                    controls.append("마우스 클릭 / 포인터")
                    tags.add('마우스컨트롤')

                # 게임 기능
                if 'score' in lower or 'point' in lower:
                    features.append("점수 시스템 (스코어보드)")
                    tags.add('스코어경쟁')
                if 'colliderect' in lower or 'spritecollide' in lower or 'collide' in lower:
                    features.append("충돌 감지 & 물리 엔진")
                    tags.add('충돌물리')
                if 'gravity' in lower or 'jump' in lower:
                    features.append("중력 & 점프 물리")
                    tags.add('플랫포머')
                if 'level' in lower:
                    features.append("단계별 레벨 시스템")
                    tags.add('레벨시스템')
                if 'life' in lower or ' hp' in lower or 'health' in lower or 'lives' in lower:
                    features.append("체력(HP) / 목숨 시스템")
                    tags.add('HP시스템')
                if 'enemy' in lower or 'monster' in lower or 'boss' in lower:
                    features.append("적(Enemy) / 몬스터 AI")
                    tags.add('적AI')
                if 'sprite' in lower:
                    features.append("스프라이트 기반 오브젝트")
                if 'animation' in lower or 'frame' in lower:
                    features.append("스프라이트 애니메이션")
                    tags.add('애니메이션')
                if 'mixer' in lower or 'sound' in lower or 'music' in lower:
                    features.append("Pygame 사운드 믹서")
                    tags.add('사운드 포함')

                # FPS 감지
                fps_match = re.search(r'clock\.tick\((\d+)\)', content)
                if fps_match:
                    features.append(f"게임 루프 {fps_match.group(1)} FPS 고정")

                # 장르 정밀 추론
                if any(w in lower for w in ['bullet', 'shoot', 'fire', 'laser', 'missile', 'projectile']):
                    tags.add('슈팅게임')
                if any(w in lower for w in ['gravity', 'jump', 'platform', 'fall']):
                    tags.add('플랫포머')
                if any(w in lower for w in ['puzzle', 'match', 'board', 'tile', 'grid']):
                    tags.add('퍼즐게임')
                if any(w in lower for w in ['snow', 'snowball', 'ice']):
                    tags.add('겨울테마')

                # 2인용 감지
                if any(w in lower for w in ['player1', 'player2', 'player_1', 'player_2', ' p1 ', ' p2 ']):
                    tags.add('2인용')
                    features.append("2인 대전 모드")

            # ── Turtle 감지 ──
            if 'turtle' in lower:
                tags.add('터틀그래픽')
                tags.add('기초코딩')
                if 'Turtle' not in tech_stack: tech_stack.append('Turtle')
                features.append("거북이(Turtle) 그래픽")

            # ── AI/ML 라이브러리 감지 ──
            ml_libs = {'numpy': 'NumPy', 'pandas': 'Pandas', 'tensorflow': 'TensorFlow',
                       'keras': 'Keras', 'sklearn': 'Scikit-learn', 'torch': 'PyTorch',
                       'cv2': 'OpenCV', 'matplotlib': 'Matplotlib'}
            for lib, lib_name in ml_libs.items():
                if lib in lower:
                    if lib_name not in tech_stack: tech_stack.append(lib_name)
                    if lib in ('tensorflow', 'keras', 'torch', 'sklearn'):
                        cid = _cat_id('AI/ML')
                        if cid: categories.add(cid)
                        tags.add('AI/ML')
                    if lib in ('numpy', 'pandas'):
                        tags.add('데이터분석')
                    if lib == 'matplotlib':
                        tags.add('데이터시각화')
                    if lib == 'cv2':
                        tags.add('이미지처리')
                        features.append("OpenCV 이미지 처리")

            # ── 코드 구조 감지 ──
            if 'random' in lower:
                tags.add('랜덤요소')
            if content.count('class ') >= 2:
                tags.add('객체지향')
            if content.count('def ') >= 5:
                tags.add('함수활용')
            if 'threading' in lower or 'multiprocessing' in lower:
                features.append("멀티스레딩")
            if 'socket' in lower or 'network' in lower:
                features.append("네트워크 통신")
                tags.add('네트워크')
            if 'tkinter' in lower:
                tech_stack.append('Tkinter')
                tags.add('GUI앱')
                features.append("Tkinter GUI 인터페이스")
            if 'sqlite' in lower or 'database' in lower or 'db.' in lower:
                features.append("데이터베이스 연동")
                tags.add('DB활용')

        except Exception:
            continue

    # ── 4. HTML / JS 정밀 스캔 ────────────────────────────────────────────
    web_files = [f for f in file_list if f.endswith(('.html', '.js'))]
    web_files.sort(key=lambda x: (x.count('/'), 'index' not in x.lower(), 'main' not in x.lower(), 'game' not in x.lower()))

    for web_file in web_files[:5]:
        try:
            with zf.open(web_file) as f:
                content = f.read().decode('utf-8', errors='ignore')
            lower = content.lower()

            # 제작자 주석 추출
            if not extracted_docstring:
                if web_file.endswith('.html'):
                    doc = re.search(r'<!--\s*(.*?)-->', content[:3000], re.DOTALL)
                    if doc and len(doc.group(1).strip()) > 10:
                        extracted_docstring = doc.group(1).strip()
                elif web_file.endswith('.js'):
                    doc = re.search(r'/\*[\*!]?\s*(.*?)\*/', content[:3000], re.DOTALL)
                    if doc and len(doc.group(1).strip()) > 10:
                        extracted_docstring = doc.group(1).strip()

            # Canvas / WebGL
            if '<canvas' in lower or "createelement('canvas')" in lower or 'createelement("canvas")' in lower:
                cid = _cat_id('게임')
                if cid: categories.add(cid)
                tags.add('HTML5캔버스')
                tags.add('게임개발')
                if 'Canvas API' not in tech_stack: tech_stack.append('Canvas API')
                features.append("HTML5 Canvas 2D 렌더링")
            if 'webgl' in lower or 'three.js' in lower or 'three(' in lower:
                tags.add('WebGL3D')
                if 'Three.js' not in tech_stack: tech_stack.append('Three.js')
                features.append("WebGL / 3D 그래픽")

            # 게임 루프
            if 'requestanimationframe' in lower:
                features.append("게임 루프 (requestAnimationFrame)")
                tags.add('웹애니메이션')

            # 키보드 조작
            keys = []
            if any(w in lower for w in ['arrowleft', 'arrowright', 'arrowup', 'arrowdown']): keys.append('방향키')
            if any(w in lower for w in ['"space"', "'space'", 'keycode===32', 'keycode==32', 'keycode === 32']): keys.append('스페이스바')
            if any(w in lower for w in ['key==="w"', "key==='w'", 'keycode===87', 'keycode==87']): keys.append('WASD')
            if any(w in lower for w in ['key==="enter"', "key==='enter'", 'keycode===13']): keys.append('엔터키')
            if keys:
                controls.append(f"키보드: {', '.join(keys)}")
                tags.add('키보드조작')
            elif any(w in lower for w in ['addeventlistener("keydown"', "addeventlistener('keydown'", 'onkeydown']):
                controls.append("키보드 인터랙션")
                tags.add('키보드조작')

            # 마우스 / 터치
            if any(w in lower for w in ['mousedown', 'mouseup', 'addeventlistener("click"', "addeventlistener('click'"]):
                controls.append("마우스 클릭")
                tags.add('마우스클릭')
            if 'touchstart' in lower or 'touchmove' in lower:
                controls.append("터치스크린")
                tags.add('모바일지원')

            # 점수 / 레벨
            if 'score' in lower:
                features.append("점수 시스템")
                tags.add('스코어경쟁')
            if 'level' in lower:
                features.append("레벨 시스템")
                tags.add('레벨시스템')
            if 'highscore' in lower or 'high_score' in lower or 'best' in lower:
                features.append("최고점수 기록")
            if 'localstorage' in lower:
                features.append("최고점수 저장 (LocalStorage)")
                tags.add('기록저장')

            # 오디오
            if '<audio' in lower or 'new audio(' in lower or 'audiocontext' in lower:
                tags.add('웹사운드')
                features.append("웹 오디오 재생")

            # 체력 / 레이어
            if any(w in lower for w in ['lives', 'health', ' hp', 'lifes']):
                features.append("체력 / 목숨 시스템")
                tags.add('HP시스템')
            if 'enemy' in lower or 'monster' in lower:
                features.append("적(Enemy) 오브젝트")
                tags.add('적AI')

            # 장르 정밀 추론
            if any(w in lower for w in ['bullet', 'shoot', 'fire', 'laser', 'missile']):
                tags.add('슈팅게임')
            if any(w in lower for w in ['gravity', 'jump', 'platform', 'fall']):
                tags.add('플랫포머')
            if any(w in lower for w in ['puzzle', 'match', 'board', 'tile', 'grid']):
                tags.add('퍼즐게임')
            if any(w in lower for w in ['snow', 'snowball', 'ice']):
                tags.add('겨울테마')

            # 2인용
            if any(w in lower for w in ['player1', 'player2', 'p1', 'p2']):
                tags.add('2인용')
                features.append("2인 대전")

            # 기술 감지
            if 'math.random' in lower:
                tags.add('랜덤요소')
            if 'fetch(' in lower or 'xmlhttprequest' in lower or 'axios' in lower:
                features.append("외부 API 통신")
                tags.add('API연동')
            if 'websocket' in lower:
                features.append("WebSocket 실시간 통신")
                tags.add('실시간통신')

        except Exception:
            continue

    # ── 5. 중복 제거 (순서 유지) ──────────────────────────────────────────
    seen = set()
    features   = [x for x in features   if not (x in seen or seen.add(x))]
    seen = set()
    controls   = [x for x in controls   if not (x in seen or seen.add(x))]
    seen = set()
    tech_stack = [x for x in tech_stack if not (x in seen or seen.add(x))]

    # ── 6. 설명 생성 (구조화된 한국어 형식) ──────────────────────────────
    genre_priority = ['슈팅게임', '플랫포머', '퍼즐게임', '러닝게임', '대전게임',
                      '레이싱게임', '보드게임', '카드게임', '퀴즈게임', '타워디펜스',
                      'RPG', '탐험게임', '리듬게임', '생존게임', '클래식게임', '아케이드']
    detected_genre = next((t for t in genre_priority if t in tags), None)
    if detected_genre is None:
        detected_genre = "게임" if (_cat_id('게임') in categories) else "프로그램"

    tech_str = ' · '.join(tech_stack) if tech_stack else '웹 기술'

    desc_parts = []

    # 제작자 노트
    if extracted_docstring:
        clean_doc = re.sub(r'\n{3,}', '\n\n', extracted_docstring.strip())
        desc_parts.append(f"📝 제작자 소개\n{clean_doc}")

    # 본문 소개
    intro = f"📌 작품 소개\n{title}은(는) {tech_str}로 제작된 {detected_genre}입니다."
    if '2인용' in tags:
        intro += "\n두 플레이어가 함께 즐길 수 있는 대전 방식의 게임입니다."
    if '겨울테마' in tags:
        intro += "\n눈과 얼음을 소재로 한 겨울 테마 작품입니다."
    desc_parts.append(intro)

    # 조작법
    if controls:
        ctrl_lines = '\n'.join(f"  • {c}" for c in controls)
        desc_parts.append(f"🕹️ 조작법\n{ctrl_lines}")

    # 주요 기능
    if features:
        feat_lines = '\n'.join(f"  • {f}" for f in features[:7])
        desc_parts.append(f"⭐ 주요 기능\n{feat_lines}")

    # 기술 스택
    if tech_stack:
        desc_parts.append(f"🛠️ 기술 스택\n  {tech_str}")

    desc_parts.append("✨ 직접 실행해보고 의견을 남겨주세요!")
    description = '\n\n'.join(desc_parts)

    # ── 7. 태그 우선순위 정렬 → 상위 10개 선택 ───────────────────────────
    TAG_PRIORITY = [
        # 장르 (가장 중요)
        '슈팅게임', '플랫포머', '퍼즐게임', '러닝게임', '대전게임', '레이싱게임',
        '보드게임', '카드게임', 'RPG', '타워디펜스', '리듬게임', '생존게임',
        '클래식게임', '아케이드', '탐험게임', '퀴즈게임', '회피게임',
        # 특수 테마
        '2인용', '겨울테마', '눈덩이', '우주배경', '좀비게임',
        # 핵심 기술
        'Pygame', 'HTML5캔버스', 'JavaScript', 'Python',
        # 게임 기능
        '스코어경쟁', '레벨시스템', 'HP시스템', '적AI', '충돌물리',
        # 입력
        '키보드컨트롤', '키보드조작', '마우스컨트롤', '마우스클릭', '모바일지원',
        # 기타
        '랜덤요소', '사운드 포함', '이미지 활용', '애니메이션',
        '기록저장', '게임개발', '객체지향', '함수활용',
    ]
    sorted_tags = []
    for p in TAG_PRIORITY:
        if p in tags:
            sorted_tags.append(p)
    for t in sorted(tags):
        if t not in sorted_tags:
            sorted_tags.append(t)

    final_tags = sorted_tags[:10]

    return {
        'title': title,
        'description': description,
        'tags_str': ', '.join(final_tags),
        'category_ids': list(categories),
    }


@login_required
def my_projects(request):
    """내 작품 관리 (선생님은 모든 작품, 학생은 본인 작품)"""
    if request.user.is_staff:
        # 선생님은 모든 작품을 최신순으로 조회
        projects = Project.objects.all().select_related('author').prefetch_related('categories', 'tags').order_by('-created_at')
    else:
        # 학생은 본인이 올린 작품만 조회
        projects = Project.objects.filter(author=request.user).select_related('author').prefetch_related('categories', 'tags').order_by('-created_at')
    
    return render(request, 'arcade/my_projects.html', {
        'projects': projects,
        'is_teacher': request.user.is_staff
    })


@login_required
def approve_project(request, project_id):
    """작품 즉시 승인 (선생님 전용)"""
    if not request.user.is_staff:
        messages.error(request, '작품 승인 권한이 없습니다.')
        return redirect('my_projects')
        
    project = get_object_or_404(Project, pk=project_id)
    project.status = 'approved'
    project.save()
    
    messages.success(request, f'"{project.title}" 작품이 승인되어 아케이드에 공개되었습니다! 🚀')
    return redirect('my_projects')


@require_POST
@login_required
def toggle_like(request, project_id):
    """좋아요 토글 (AJAX)"""
    project = get_object_or_404(Project, pk=project_id)
    like, created = Like.objects.get_or_create(user=request.user, project=project)
    if not created:
        like.delete()
    return JsonResponse({
        'liked': created,
        'count': project.likes.count(),
    })


@require_POST
@login_required
def toggle_bookmark(request, project_id):
    """즐겨찾기 토글 (AJAX)"""
    project = get_object_or_404(Project, pk=project_id)
    bookmark, created = Bookmark.objects.get_or_create(user=request.user, project=project)
    if not created:
        bookmark.delete()
    return JsonResponse({
        'bookmarked': created,
        'count': project.bookmarks.count(),
    })


def check_username(request):
    """아이디(Username) 중복 확인 API (AJAX)"""
    username = request.GET.get('username', '').strip()
    if not username:
        return JsonResponse({'available': False, 'message': '아이디를 입력해주세요.'})
    
    exists = User.objects.filter(username__iexact=username).exists()
    return JsonResponse({
        'available': not exists,
        'message': '이미 사용 중인 아이디입니다.' if exists else '사용 가능한 아이디입니다.'
    })


@login_required
def search_users(request):
    """학생 이름 자동완성을 위한 API"""
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'users': []})
    
    profiles = UserProfile.objects.filter(
        Q(real_name__icontains=q) | Q(user__username__icontains=q)
    ).select_related('user')[:10]
    
    results = []
    for p in profiles:
        name = p.real_name if p.real_name else p.user.username
        if name not in [r['name'] for r in results]: # 중복 방지
            results.append({'id': p.user.id, 'name': name})
            
    return JsonResponse({'users': results})

@login_required
def search_certinfos(request):
    """자격증명 자동완성을 위한 API"""
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'certinfos': []})
    
    certs = CertInfo.objects.filter(name__icontains=q)[:10]
    results = [{'id': c.id, 'name': c.name, 'issuer': c.issuer} for c in certs]
    return JsonResponse({'certinfos': results})

@login_required
def search_competition_types(request):
    """대회종류 자동완성을 위한 API"""
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'competition_types': []})

    competition_types = CompetitionType.objects.filter(name__icontains=q)[:10]
    results = [
        {'id': c.id, 'name': c.name, 'organization': c.organization}
        for c in competition_types
    ]
    return JsonResponse({'competition_types': results})


@login_required
@require_POST
def analyze_award_image(request):
    """상장 이미지를 Gemini Vision으로 분석해 폼 필드값 반환"""
    import base64
    import json as _json
    import os as _os

    try:
        import google.generativeai as genai
    except ImportError:
        return JsonResponse({'error': 'google-generativeai 패키지가 설치되지 않았습니다. pip install google-generativeai를 실행하세요.'}, status=500)

    image_file = request.FILES.get('image')
    if not image_file:
        return JsonResponse({'error': '이미지가 없습니다.'}, status=400)

    image_data = image_file.read()
    mime_type = image_file.content_type or 'image/jpeg'
    b64_data = base64.b64encode(image_data).decode('utf-8')

    # os.environ에서 직접 읽기 (settings 래퍼 문제 우회)
    api_keys = []
    k = _os.environ.get('GEMINI_API_KEY', '')
    if k:
        api_keys.append(k)
    for i in range(2, 21):
        k = _os.environ.get(f'GEMINI_API_KEY_{i}', '')
        if k:
            api_keys.append(k)

    if not api_keys:
        return JsonResponse({'error': 'Gemini API 키가 설정되지 않았습니다. .env 파일에 GEMINI_API_KEY를 추가하세요.'}, status=500)

    prompt = """이 이미지는 대회 수상 상장입니다. 상장에서 다음 항목들을 추출해서 JSON으로만 답변하세요.
JSON 외에 다른 텍스트는 절대 포함하지 마세요.

추출 항목:
- student_name: 수상자 이름 (학생 이름, 없으면 "")
- competition_year: 대회 연도 (4자리 숫자, 없으면 null)
- competition_type: 대회명/대회종류 (예: "제15회 전국 로봇대회", 없으면 "")
- division: 부문 (예: "초등부", "중등부", "SW부문", 없으면 "")
- award_name: 상격 (예: "금상", "은상", "동상", "대상", "최우수상", "우수상", "장려상", 없으면 "")
- organization: 수여기관/주최기관 (없으면 "")
- date_awarded: 수상일자 (YYYY-MM-DD 형식, 없으면 "")

응답 예시:
{"student_name": "홍길동", "competition_year": 2025, "competition_type": "제15회 전국 코딩올림피아드", "division": "초등부", "award_name": "금상", "organization": "교육부", "date_awarded": "2025-11-15"}"""

    last_error = None
    # 모델 우선순위 목록 (할당량 초과 시 다음 모델로 fallback)
    model_names = [
        'gemini-2.5-flash',
        'gemini-2.0-flash-lite',
        'gemini-2.0-flash',
        'gemini-1.5-pro',
    ]

    for api_key in api_keys:
        for model_name in model_names:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(model_name)
                response = model.generate_content([
                    prompt,
                    {'mime_type': mime_type, 'data': b64_data}
                ])
                raw = response.text.strip()
                # ```json ... ``` 코드블록 제거
                if raw.startswith('```'):
                    lines = raw.split('\n')
                    lines = [l for l in lines if not l.startswith('```')]
                    raw = '\n'.join(lines).strip()
                result = _json.loads(raw)
                return JsonResponse({'success': True, 'data': result})
            except Exception as e:
                last_error = str(e)
                # 할당량 초과(429)나 모델 없음(404)이면 다음 모델 시도, 그 외 에러는 다음 키로
                err_str = str(e)
                if '429' in err_str or '404' in err_str or 'not found' in err_str.lower() or 'quota' in err_str.lower():
                    continue
                break  # 다른 에러면 이 키의 나머지 모델 건너뜀

    return JsonResponse({'error': f'분석 실패: {last_error}'}, status=500)


def signup(request):
    """회원가입"""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_active = False
            user.save(update_fields=['is_active'])
            verification = SignupEmailVerification.issue(user)
            confirm_url = request.build_absolute_uri(reverse('confirm_signup_email', args=[verification.token]))
            subject = '[메듀랩] 회원가입 이메일 인증'
            body = (
                f'{user.username}님, 메듀랩 회원가입을 완료하려면 아래 링크를 눌러 주세요.\n\n'
                f'{confirm_url}\n\n'
                '이 링크는 24시간 동안만 유효합니다.'
            )
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@medulab.local')
            try:
                send_mail(subject, body, from_email, [user.email], fail_silently=False)
                messages.success(request, '회원가입 정보가 저장되었습니다. 입력한 이메일 주소로 인증 메일을 보냈습니다. 링크를 눌러 가입을 완료해 주세요.')
            except Exception:
                messages.warning(request, '회원가입 정보는 저장되었지만 인증 메일 발송에 실패했습니다. 이메일 설정 확인 후 다시 시도해 주세요.')
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'arcade/signup.html', {'form': form})


@login_required
def profile_view(request):
    """마이페이지 - 대시보드 및 정보 수정"""
    user = request.user
    profile = user.profile
    
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=profile, user=user)
        if form.is_valid():
            new_email = form.cleaned_data.get('email')
            email_changed = form.email_changed()
            form.save()
            if email_changed:
                change_request = EmailChangeRequest.issue(user, new_email)
                confirm_url = request.build_absolute_uri(reverse('confirm_email_change', args=[change_request.token]))
                subject = '[메듀랩] 이메일 변경 인증'
                body = (
                    f'{user.username}님의 이메일 변경 요청입니다.\n\n'
                    f'아래 링크를 눌러야 새 이메일 주소로 변경됩니다.\n'
                    f'{confirm_url}\n\n'
                    '이 링크는 24시간 동안만 유효합니다.'
                )
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@medulab.local')
                try:
                    send_mail(subject, body, from_email, [new_email], fail_silently=False)
                    messages.success(request, '프로필 정보는 저장되었고, 새 이메일 주소로 인증 메일을 보냈습니다. 링크를 눌러야 이메일이 변경됩니다.')
                except Exception:
                    messages.warning(request, '프로필 정보는 저장되었지만 인증 메일 발송에 실패했습니다. 이메일 설정을 확인한 뒤 다시 시도해 주세요.')
            else:
                messages.success(request, '회원 정보가 성공적으로 수정되었습니다.')
            return redirect('profile')
    else:
        form = UserProfileUpdateForm(instance=profile, user=user)
    
    # 활동 통계 및 내역 조회
    my_projects = Project.objects.filter(author=user).prefetch_related('categories')
    liked_projects = Project.objects.filter(likes__user=user).prefetch_related('author', 'categories')
    bookmarked_projects = Project.objects.filter(bookmarks__user=user).prefetch_related('author', 'categories')
    
    # 받은 총 좋아요/즐겨찾기 수 계산
    total_likes_received = Like.objects.filter(project__author=user).count()
    total_bookmarks_received = Bookmark.objects.filter(project__author=user).count()
    recent_badges = get_recent_user_badges(user, limit=8)
    badge_catalog = get_active_badges_with_user_state(user)
    
    context = {
        'profile': profile,
        'form': form,
        'my_projects': my_projects,
        'liked_projects': liked_projects,
        'bookmarked_projects': bookmarked_projects,
        'total_likes': total_likes_received,
        'total_bookmarks': total_bookmarks_received,
        'badge_count': get_user_badge_count(user),
        'recent_badges': recent_badges,
        'badge_catalog': badge_catalog,
    }
    return render(request, 'arcade/profile.html', context)


def confirm_email_change(request, token):
    change_request = get_object_or_404(EmailChangeRequest, token=token, is_used=False)

    if change_request.is_expired:
        change_request.is_used = True
        change_request.save(update_fields=['is_used'])
        messages.error(request, '이메일 변경 인증 링크가 만료되었습니다. 다시 요청해 주세요.')
        return redirect('profile')

    if User.objects.filter(email__iexact=change_request.new_email).exclude(pk=change_request.user_id).exists():
        change_request.is_used = True
        change_request.save(update_fields=['is_used'])
        messages.error(request, '이미 다른 회원이 사용 중인 이메일 주소입니다.')
        return redirect('profile')

    change_request.user.email = change_request.new_email
    change_request.user.save(update_fields=['email'])
    change_request.is_used = True
    change_request.save(update_fields=['is_used'])
    messages.success(request, '이메일 주소 인증이 완료되었습니다. 새 이메일 주소로 변경되었습니다.')
    return redirect('profile')


def confirm_signup_email(request, token):
    verification = get_object_or_404(SignupEmailVerification, token=token, is_used=False)

    if verification.is_expired:
        verification.is_used = True
        verification.save(update_fields=['is_used'])
        messages.error(request, '회원가입 인증 링크가 만료되었습니다. 다시 가입을 진행해 주세요.')
        return redirect('signup')

    verification.user.is_active = True
    verification.user.save(update_fields=['is_active'])
    verification.is_used = True
    verification.save(update_fields=['is_used'])
    messages.success(request, '이메일 인증이 완료되었습니다. 이제 로그인할 수 있습니다.')
    return redirect('login')


# ────────────────────────────────────────────────
# 회원 관리 (관리자 전용 CRUD)
# ────────────────────────────────────────────────

def staff_check(user):
    return user.is_staff

@login_required
@user_passes_test(staff_check)
def member_list(request):
    """회원 목록 조회"""
    search = request.GET.get('q', '')
    user_type = request.GET.get('type', '')
    
    users = User.objects.all().select_related('profile').order_by('-date_joined')
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search)
        )
    if user_type:
        users = users.filter(profile__user_type=user_type)

    type_filters = [
        {
            'code': code,
            'label': label,
            'active': user_type == code,
        }
        for code, label in UserProfile.USER_TYPE_CHOICES
    ]
        
    context = {
        'users': users,
        'search_query': search,
        'current_type': user_type,
        'user_types': UserProfile.USER_TYPE_CHOICES,
        'type_filters': type_filters,
    }
    return render(request, 'arcade/admin/member_list.html', context)

@login_required
@user_passes_test(staff_check)
def member_create(request):
    """신규 회원 등록"""
    if request.method == 'POST':
        user_form = AdminUserForm(request.POST)
        profile_form = AdminUserProfileForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            # 프로필 정보 업데이트
            profile.user_type = profile_form.cleaned_data['user_type']
            profile.is_approved = profile_form.cleaned_data['is_approved']
            profile.save()
            
            messages.success(request, f'회원 "{user.username}" 계정이 생성되었습니다.')
            return redirect('member_list')
    else:
        user_form = AdminUserForm()
        profile_form = AdminUserProfileForm()
        
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'title': '신규 회원 등록',
    }
    return render(request, 'arcade/admin/member_form.html', context)

@login_required
@user_passes_test(staff_check)
def member_edit(request, user_id):
    """회원 정보 수정"""
    target_user = get_object_or_404(User, pk=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=target_user)
    
    if request.method == 'POST':
        user_form = AdminUserForm(request.POST, instance=target_user)
        profile_form = AdminUserProfileForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, f'회원 "{target_user.username}" 정보가 수정되었습니다.')
            return redirect('member_list')
    else:
        user_form = AdminUserForm(instance=target_user)
        profile_form = AdminUserProfileForm(instance=profile)
        
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'target_user': target_user,
        'title': '회원 정보 수정',
    }
    return render(request, 'arcade/admin/member_form.html', context)


@login_required
@user_passes_test(staff_check)
@require_POST
def member_approve(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=target_user)
    profile.is_approved = True
    profile.approved_at = timezone.now()
    profile.save(update_fields=['is_approved', 'approved_at'])
    messages.success(request, f'회원 "{target_user.username}" 을 승인했습니다.')
    redirect_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('member_list')
    return redirect(redirect_url)

@login_required
@user_passes_test(staff_check)
@require_POST
def member_delete(request, user_id):
    """회원 삭제"""
    target_user = get_object_or_404(User, pk=user_id)
    if target_user == request.user:
        messages.error(request, '본인 계정은 삭제할 수 없습니다.')
    else:
        username = target_user.username
        target_user.delete()
        messages.success(request, f'회원 "{username}" 계정이 삭제되었습니다.')
    return redirect('member_list')


# ────────────────────────────────────────────────
# 배지 관리 (관리자 전용 CRUD)
# ────────────────────────────────────────────────

@login_required
@user_passes_test(staff_check)
@login_required
@user_passes_test(staff_check)
def schedule_admin_list(request):
    """일정 관리 목록"""
    events = ScheduleEvent.objects.select_related().order_by('start_date', 'end_date', 'title')

    # 필터링
    event_type = request.GET.get('event_type', '')
    is_active = request.GET.get('is_active', '')
    search = request.GET.get('q', '')

    if event_type:
        events = events.filter(event_type=event_type)
    if is_active in ('0', '1'):
        events = events.filter(is_active=is_active == '1')
    if search:
        events = events.filter(Q(title__icontains=search) | Q(description__icontains=search))

    context = {
        'events': events,
        'search_query': search,
        'current_event_type': event_type,
        'current_is_active': is_active,
        'event_types': ScheduleEvent.EVENT_TYPE_CHOICES,
        'title': '일정 관리',
    }
    return render(request, 'arcade/admin/schedule_list.html', context)


@login_required
@user_passes_test(staff_check)
def _handle_attachment_uploads(request, event):
    """첨부 파일 업로드 처리"""
    files = request.FILES.getlist('attachments')
    for f in files:
        if f and f.name:
            ScheduleAttachment.objects.create(event=event, file=f)


def schedule_admin_create(request):
    """신규 일정 등록"""
    if request.method == 'POST':
        form = ScheduleEventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save()
            _handle_attachment_uploads(request, event)
            messages.success(request, f'일정 "{event.title}"이 등록되었습니다.')
            return redirect('schedule_admin_list')
    else:
        form = ScheduleEventForm()

    context = {
        'form': form,
        'title': '신규 일정 등록',
    }
    return render(request, 'arcade/admin/schedule_form.html', context)


@login_required
@user_passes_test(staff_check)
def schedule_admin_edit(request, event_id):
    """일정 수정"""
    event = get_object_or_404(ScheduleEvent, pk=event_id)

    if request.method == 'POST':
        form = ScheduleEventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            event = form.save()
            _handle_attachment_uploads(request, event)
            messages.success(request, f'일정 "{event.title}"이 수정되었습니다.')
            return redirect('schedule_admin_list')
    else:
        form = ScheduleEventForm(instance=event)

    context = {
        'form': form,
        'event': event,
        'title': '일정 수정',
    }
    return render(request, 'arcade/admin/schedule_form.html', context)


@login_required
@user_passes_test(staff_check)
@require_POST
def schedule_admin_delete(request, event_id):
    """일정 삭제"""
    event = get_object_or_404(ScheduleEvent, pk=event_id)
    title = event.title
    try:
        event.delete()
        messages.success(request, f'일정 "{title}"이 삭제되었습니다.')
    except DatabaseError:
        messages.error(request, f'일정 "{title}"을 삭제할 수 없습니다.')
    return redirect('schedule_admin_list')


# ────────────────────────────────────────────────
# 학원 시간표 (사용자용 + 관리자 CRUD)
# ────────────────────────────────────────────────

def timetable_view(request):
    """학원 시간표 - 요일별 주간 그리드"""
    GRID_START = 8 * 60   # 08:00
    GRID_END   = 22 * 60  # 22:00
    GRID_H     = 840      # 840px = 14h × 60px

    entries = ScheduleEvent.objects.filter(
        event_type=ScheduleEvent.EVENT_TYPE_ACADEMIC,
        is_active=True
    ).order_by('start_time', 'title')

    DAY_LIST = [
        {'key': '1', 'label': '월'},
        {'key': '2', 'label': '화'},
        {'key': '3', 'label': '수'},
        {'key': '4', 'label': '목'},
        {'key': '5', 'label': '금'},
        {'key': '6', 'label': '토'},
    ]

    COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316', '#ec4899']

    for day in DAY_LIST:
        day['events'] = []

    # 수업별 고정 색상 매핑
    all_ids = list(entries.values_list('id', flat=True))
    color_map = {eid: COLORS[i % len(COLORS)] for i, eid in enumerate(all_ids)}

    for entry in entries:
        if not entry.days_of_week:
            continue
        for day_key in entry.days_of_week.split(','):
            day_key = day_key.strip()
            for day in DAY_LIST:
                if day['key'] == day_key:
                    if entry.start_time and entry.end_time:
                        s = entry.start_time.hour * 60 + entry.start_time.minute
                        e = entry.end_time.hour * 60 + entry.end_time.minute
                        top    = max(0, round((s - GRID_START) * GRID_H / (GRID_END - GRID_START)))
                        height = max(28, round((e - s) * GRID_H / (GRID_END - GRID_START)))
                        day['events'].append({
                            'entry': entry,
                            'top': top,
                            'height': height,
                            'color': color_map[entry.id],
                            'time_str': f"{entry.start_time.strftime('%H:%M')}~{entry.end_time.strftime('%H:%M')}",
                        })

    hour_labels = [
        {'label': f'{h:02d}:00', 'top': round((h - 8) * GRID_H / 14)}
        for h in range(8, 23)
    ]

    context = {
        'days': DAY_LIST,
        'hour_labels': hour_labels,
        'grid_height': GRID_H,
        'total_entries': entries.count(),
        'is_admin': request.user.is_staff,
        'day_choices': [('1','월'),('2','화'),('3','수'),('4','목'),('5','금'),('6','토'),('0','일')],
    }
    return render(request, 'arcade/timetable.html', context)


@login_required
@user_passes_test(staff_check)
def timetable_admin_list(request):
    entries = ScheduleEvent.objects.filter(
        event_type=ScheduleEvent.EVENT_TYPE_ACADEMIC
    ).order_by('start_time', 'title')
    return render(request, 'arcade/admin/timetable_list.html', {'entries': entries})


@login_required
@user_passes_test(staff_check)
def timetable_admin_create(request):
    if request.method == 'POST':
        form = TimetableForm(request.POST)
        if form.is_valid():
            entry = form.save()
            messages.success(request, f'"{entry.title}" 수업이 시간표에 추가되었습니다.')
            return redirect('timetable_admin_list')
    else:
        form = TimetableForm()
    return render(request, 'arcade/admin/timetable_form.html', {'form': form, 'title': '수업 추가'})


@login_required
@user_passes_test(staff_check)
def timetable_admin_edit(request, entry_id):
    entry = get_object_or_404(ScheduleEvent, pk=entry_id, event_type=ScheduleEvent.EVENT_TYPE_ACADEMIC)
    if request.method == 'POST':
        form = TimetableForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{entry.title}" 수업이 수정되었습니다.')
            return redirect('timetable_admin_list')
    else:
        form = TimetableForm(instance=entry)
    return render(request, 'arcade/admin/timetable_form.html', {'form': form, 'entry': entry, 'title': '수업 수정'})


@login_required
@user_passes_test(staff_check)
@require_POST
def timetable_admin_delete(request, entry_id):
    entry = get_object_or_404(ScheduleEvent, pk=entry_id, event_type=ScheduleEvent.EVENT_TYPE_ACADEMIC)
    title = entry.title
    entry.delete()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({'status': 'ok'})
    messages.success(request, f'"{title}" 수업이 삭제되었습니다.')
    return redirect('timetable_admin_list')


@login_required
@user_passes_test(staff_check)
@require_POST
def timetable_admin_api_save(request):
    """시간표 인라인 모달 저장 API"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'error': '잘못된 요청입니다.'}, status=400)

    entry_id    = data.get('id')
    title       = data.get('title', '').strip()
    days_of_week= data.get('days_of_week', '').strip()
    start_time  = data.get('start_time', '').strip()
    end_time    = data.get('end_time', '').strip()
    description = data.get('description', '').strip()
    is_active   = bool(data.get('is_active', True))

    if not title or not days_of_week or not start_time or not end_time:
        return JsonResponse({'status': 'error', 'error': '수업명, 요일, 시간은 필수입니다.'}, status=400)

    try:
        from datetime import time as dtime
        sh, sm = map(int, start_time.split(':'))
        eh, em = map(int, end_time.split(':'))
        s_time = dtime(sh, sm)
        e_time = dtime(eh, em)
        if s_time >= e_time:
            return JsonResponse({'status': 'error', 'error': '종료 시간은 시작 시간보다 늦어야 합니다.'}, status=400)
    except Exception:
        return JsonResponse({'status': 'error', 'error': '시간 형식이 올바르지 않습니다.'}, status=400)

    try:
        if entry_id:
            entry = get_object_or_404(ScheduleEvent, pk=int(entry_id), event_type=ScheduleEvent.EVENT_TYPE_ACADEMIC)
        else:
            entry = ScheduleEvent(event_type=ScheduleEvent.EVENT_TYPE_ACADEMIC)

        entry.title        = title
        entry.days_of_week = days_of_week
        entry.start_time   = s_time
        entry.end_time     = e_time
        entry.description  = description
        entry.is_active    = is_active
        entry.start_date   = None
        entry.end_date     = None
        entry.save()
        return JsonResponse({'status': 'ok', 'id': entry.id})
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)


def badge_list(request):
    """배지 목록 조회"""
    search = request.GET.get('q', '')
    category = request.GET.get('category', '')
    criteria_type = request.GET.get('criteria_type', '')
    is_active = request.GET.get('is_active', '')

    badges = Badge.objects.select_related('related_program').order_by('sort_order', 'name')

    if search:
        badges = badges.filter(
            Q(code__icontains=search) |
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(criteria_type__icontains=search) |
            Q(related_program__name__icontains=search)
        )
    if category:
        badges = badges.filter(category=category)
    if criteria_type:
        badges = badges.filter(criteria_type=criteria_type)
    if is_active in ('0', '1'):
        badges = badges.filter(is_active=is_active == '1')

    context = {
        'badges': badges,
        'search_query': search,
        'current_category': category,
        'current_criteria_type': criteria_type,
        'current_is_active': is_active,
        'categories': Badge.CATEGORY_CHOICES,
        'criteria_types': Badge.objects.exclude(criteria_type='')
        .order_by('criteria_type')
        .values_list('criteria_type', flat=True)
        .distinct(),
        'title': '배지 관리',
    }
    return render(request, 'arcade/admin/badge_list.html', context)


@login_required
@user_passes_test(staff_check)
def badge_create(request):
    """신규 배지 등록"""
    if request.method == 'POST':
        form = BadgeForm(request.POST)
        if form.is_valid():
            badge = form.save()
            messages.success(request, f'배지 "{badge.name}"이 생성되었습니다.')
            return redirect('badge_list')
    else:
        form = BadgeForm()

    context = {
        'form': form,
        'title': '신규 배지 등록',
    }
    return render(request, 'arcade/admin/badge_form.html', context)


@login_required
@user_passes_test(staff_check)
def badge_edit(request, badge_id):
    """배지 정보 수정"""
    badge = get_object_or_404(Badge, pk=badge_id)

    if request.method == 'POST':
        form = BadgeForm(request.POST, instance=badge)
        if form.is_valid():
            badge = form.save()
            messages.success(request, f'배지 "{badge.name}" 정보가 수정되었습니다.')
            return redirect('badge_list')
    else:
        form = BadgeForm(instance=badge)

    context = {
        'form': form,
        'badge': badge,
        'title': '배지 정보 수정',
    }
    return render(request, 'arcade/admin/badge_form.html', context)


@login_required
@user_passes_test(staff_check)
@require_POST
def badge_delete(request, badge_id):
    """배지 삭제"""
    badge = get_object_or_404(Badge, pk=badge_id)
    name = badge.name
    try:
        badge.delete()
    except DatabaseError:
        messages.error(request, f'배지 "{name}"을 삭제할 수 없습니다.')
    else:
        messages.success(request, f'배지 "{name}"이 삭제되었습니다.')
    return redirect('badge_list')


def signup(request):
    """회원가입"""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '회원가입이 완료되었습니다. 이제 로그인할 수 있습니다.')
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'arcade/signup.html', {'form': form})


@login_required
def profile_view(request):
    """마이페이지 - 대시보드 및 정보 수정"""
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=profile, user=user)
        if form.is_valid():
            form.save()
            messages.success(request, '회원 정보가 성공적으로 수정되었습니다.')
            return redirect('profile')
    else:
        form = UserProfileUpdateForm(instance=profile, user=user)

    my_projects = Project.objects.filter(author=user).prefetch_related('categories')
    liked_projects = Project.objects.filter(likes__user=user).prefetch_related('author', 'categories')
    bookmarked_projects = Project.objects.filter(bookmarks__user=user).prefetch_related('author', 'categories')

    total_likes_received = Like.objects.filter(project__author=user).count()
    total_bookmarks_received = Bookmark.objects.filter(project__author=user).count()
    recent_badges = get_recent_user_badges(user, limit=8)
    badge_catalog = get_active_badges_with_user_state(user)

    context = {
        'profile': profile,
        'form': form,
        'my_projects': my_projects,
        'liked_projects': liked_projects,
        'bookmarked_projects': bookmarked_projects,
        'total_likes': total_likes_received,
        'total_bookmarks': total_bookmarks_received,
        'badge_count': get_user_badge_count(user),
        'recent_badges': recent_badges,
        'badge_catalog': badge_catalog,
    }
    return render(request, 'arcade/profile.html', context)

def board_notice(request):
    notices = Notice.objects.all()
    return render(request, 'arcade/board_notice.html', {'notices': notices})

def board_awards(request):
    competition_types = CompetitionType.objects.all().order_by('order', 'name')
    selected_competition_type = request.GET.get('competition_type', '').strip()
    awards = Award.objects.select_related('competition_type').all().order_by('-date_awarded', '-created_at')

    if selected_competition_type:
        awards = awards.filter(competition_type_id=selected_competition_type)

    return render(request, 'arcade/board_awards.html', {
        'awards': awards,
        'competition_types': competition_types,
        'selected_competition_type': selected_competition_type,
    })

def board_cert(request):
    cert_types = CertInfo.objects.all().order_by('order', 'name')
    selected_cert_type = request.GET.get('cert_type', '').strip()
    certs = Certification.objects.select_related('cert_info').all().order_by('-date_acquired', '-created_at')

    if selected_cert_type:
        certs = certs.filter(cert_info_id=selected_cert_type)

    return render(request, 'arcade/board_cert.html', {
        'certs': certs,
        'cert_types': cert_types,
        'selected_cert_type': selected_cert_type,
    })

def board_notice_detail(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    notice.view_count += 1
    notice.save()
    return render(request, 'arcade/board_notice_detail.html', {'notice': notice})

import random

AWARD_MESSAGES = [
    "🎉 자랑스러운 대회 수상을 진심으로 축하합니다! 🎉",
    "🎊 엄청난 노력의 결실! 수상을 축하해요! 🎊",
    "🌟 눈부신 활약으로 이뤄낸 수상을 축하합니다! 🌟",
    "👏 멋진 성과를 이룬 것을 진심으로 축하해요! 👏",
    "✨ 앞으로도 계속될 멋진 도전을 응원합니다! ✨"
]

CERT_MESSAGES = [
    "🎉 자랑스러운 자격 취득을 진심으로 축하합니다! 🎉",
    "🎊 새로운 자격 증명! 한 걸음 더 성장했네요! 🎊",
    "🌟 멋진 도전을 성공으로 이끈 것을 축하해요! 🌟",
    "👏 대단한 성과입니다! 자격 취득을 축하합니다! 👏",
    "✨ 값진 노력으로 얻은 자격증을 축하해요! ✨"
]

def board_awards_detail(request, pk):
    award = get_object_or_404(Award, pk=pk)
    congrats_msg = random.choice(AWARD_MESSAGES)
    return render(request, 'arcade/board_awards_detail.html', {'award': award, 'congrats_msg': congrats_msg})

def board_cert_detail(request, pk):
    cert = get_object_or_404(Certification, pk=pk)
    congrats_msg = random.choice(CERT_MESSAGES)
    return render(request, 'arcade/board_cert_detail.html', {'cert': cert, 'congrats_msg': congrats_msg})


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
            messages.success(request, '대회수상이 저장되었습니다.')
            return redirect('board_awards')
        messages.error(request, '저장하지 못했습니다. 아래 항목을 확인해 주세요.')
    else:
        form = AwardForm()
    return render(request, 'arcade/board_form.html', {'form': form, 'title': '대회수상 글쓰기', 'is_award_form': True})

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
            messages.success(request, '대회수상이 수정되었습니다.')
            return redirect('board_awards_detail', pk=award.pk)
        messages.error(request, '저장하지 못했습니다. 아래 항목을 확인해 주세요.')
    else:
        form = AwardForm(instance=award)
    return render(request, 'arcade/board_form.html', {'form': form, 'title': '대회수상 수정', 'is_award_form': True})

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

# --- 대회종류 (CompetitionType) 게시판 ---
def board_competition_type(request):
    competition_types = CompetitionType.objects.all().order_by('order', 'name')
    return render(request, 'arcade/board_competition_type.html', {'competition_types': competition_types})

def board_competition_type_detail(request, pk):
    competition_type = get_object_or_404(CompetitionType, pk=pk)
    return render(request, 'arcade/board_competition_type_detail.html', {'competition_type': competition_type})

@user_passes_test(lambda u: u.is_staff)
def board_competition_type_create(request):
    from .forms import CompetitionTypeForm
    if request.method == 'POST':
        form = CompetitionTypeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('board_competition_type')
    else:
        form = CompetitionTypeForm()
    return render(request, 'arcade/board_form.html', {'form': form, 'title': '대회종류 글쓰기'})

@user_passes_test(lambda u: u.is_staff)
def board_competition_type_update(request, pk):
    from .forms import CompetitionTypeForm
    competition_type = get_object_or_404(CompetitionType, pk=pk)
    if request.method == 'POST':
        form = CompetitionTypeForm(request.POST, request.FILES, instance=competition_type)
        if form.is_valid():
            form.save()
            return redirect('board_competition_type_detail', pk=competition_type.pk)
    else:
        form = CompetitionTypeForm(instance=competition_type)
    return render(request, 'arcade/board_form.html', {'form': form, 'title': '대회종류 수정'})

@user_passes_test(lambda u: u.is_staff)
def board_competition_type_delete(request, pk):
    competition_type = get_object_or_404(CompetitionType, pk=pk)
    if request.method == 'POST':
        competition_type.delete()
        return redirect('board_competition_type')
    return render(request, 'arcade/board_confirm_delete.html', {'object': competition_type, 'title': '대회종류 삭제', 'cancel_url': reverse('board_competition_type_detail', args=[pk])})


# --- 자격종류 (CertInfo) 게시판 ---
def board_certinfo(request):
    cat_order = Case(
        When(category='ai',           then=Value(0)),
        When(category='block_coding', then=Value(1)),
        When(category='python',       then=Value(2)),
        When(category='robot',        then=Value(3)),
        When(category='doc_work',     then=Value(4)),
        default=Value(9),
        output_field=IntegerField(),
    )
    certinfos = CertInfo.objects.all().annotate(cat_order=cat_order).order_by('cat_order', 'order', 'name')
    grouped_certinfos = OrderedDict()

    for certinfo in certinfos:
        group_name = get_certinfo_group_name(certinfo.name)
        existing = grouped_certinfos.get(group_name)

        if existing is None or (existing.name != group_name and certinfo.name == group_name):
            grouped_certinfos[group_name] = certinfo

    categories = [
        ('all',          '전체'),
        ('ai',           'AI'),
        ('block_coding', '블록코딩'),
        ('python',       '파이썬코딩'),
        ('robot',        '로봇'),
        ('doc_work',     '문서작업'),
    ]
    active_cat = request.GET.get('cat', 'all')
    all_items = list(grouped_certinfos.values())
    if active_cat != 'all':
        all_items = [
            c for c in all_items
            if active_cat in [x.strip() for x in (c.category or '').split(',')]
        ]

    return render(request, 'arcade/board_certinfo.html', {
        'certinfos': all_items,
        'categories': categories,
        'active_cat': active_cat,
    })

def board_certinfo_detail(request, pk):
    certinfo = get_object_or_404(CertInfo, pk=pk)
    return render(request, 'arcade/board_certinfo_detail.html', {'certinfo': certinfo})

@user_passes_test(lambda u: u.is_staff)
def board_certinfo_create(request):
    from .forms import CertInfoForm
    if request.method == 'POST':
        form = CertInfoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('board_certinfo')
    else:
        form = CertInfoForm()
    return render(request, 'arcade/board_certinfo_form.html', {'form': form, 'title': '자격종류 추가'})

@user_passes_test(lambda u: u.is_staff)
def board_certinfo_update(request, pk):
    from .forms import CertInfoForm
    certinfo = get_object_or_404(CertInfo, pk=pk)
    if request.method == 'POST':
        form = CertInfoForm(request.POST, request.FILES, instance=certinfo)
        if form.is_valid():
            form.save()
            return redirect('board_certinfo_detail', pk=certinfo.pk)
    else:
        form = CertInfoForm(instance=certinfo)
    return render(request, 'arcade/board_certinfo_form.html', {'form': form, 'title': '자격종류 수정'})

@user_passes_test(lambda u: u.is_staff)
def board_certinfo_delete(request, pk):
    certinfo = get_object_or_404(CertInfo, pk=pk)
    if request.method == 'POST':
        certinfo.delete()
        return redirect('board_certinfo')
    return render(request, 'arcade/board_confirm_delete.html', {'object': certinfo, 'title': '자격종류 삭제', 'cancel_url': reverse('board_certinfo_detail', args=[pk])})

import json as _json_mod
@user_passes_test(lambda u: u.is_staff)
def board_certinfo_reorder(request):
    if request.method != 'POST':
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['POST'])
    try:
        data = _json_mod.loads(request.body)
        ids = data.get('ids', [])
        for idx, pk in enumerate(ids):
            CertInfo.objects.filter(pk=pk).update(order=idx * 10)
        from django.http import JsonResponse
        return JsonResponse({'ok': True})
    except Exception as e:
        from django.http import JsonResponse
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)


# --- 공모전 (Contest) 게시판 ---
def board_contest(request):
    contests = Contest.objects.filter(is_active=True).order_by('end_date', '-created_at')
    return render(request, 'arcade/board_contest.html', {'contests': contests})

def board_contest_detail(request, pk):
    contest = get_object_or_404(Contest, pk=pk)
    return render(request, 'arcade/board_contest_detail.html', {'contest': contest})

@user_passes_test(lambda u: u.is_staff)
def board_contest_create(request):
    from .forms import ContestForm
    if request.method == 'POST':
        form = ContestForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('board_contest')
    else:
        form = ContestForm()
    return render(request, 'arcade/board_form.html', {'form': form, 'title': '공모전 추가'})

@user_passes_test(lambda u: u.is_staff)
def board_contest_update(request, pk):
    from .forms import ContestForm
    contest = get_object_or_404(Contest, pk=pk)
    if request.method == 'POST':
        form = ContestForm(request.POST, request.FILES, instance=contest)
        if form.is_valid():
            form.save()
            return redirect('board_contest_detail', pk=contest.pk)
    else:
        form = ContestForm(instance=contest)
    return render(request, 'arcade/board_form.html', {'form': form, 'title': '공모전 수정'})

@user_passes_test(lambda u: u.is_staff)
def board_contest_delete(request, pk):
    contest = get_object_or_404(Contest, pk=pk)
    if request.method == 'POST':
        contest.delete()
        return redirect('board_contest')
    return render(request, 'arcade/board_confirm_delete.html', {'object': contest, 'title': '공모전 삭제', 'cancel_url': reverse('board_contest_detail', args=[pk])})


@user_passes_test(lambda u: u.is_staff)
@require_POST
def api_crawl_thinkcontest(request):
    from .management.commands.crawl_contests import Command as CrawlCommand
    try:
        cmd = CrawlCommand()
        added_count = cmd.crawl_and_save()
        return JsonResponse({'status': 'success', 'added_count': added_count})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def my_report(request):
    from django.utils import timezone
    from datetime import timedelta
    from typing_practice.models import TypingScore
    from courses.models import UserProgress
    from .models import Attendance, UserBadge
    from django.db.models import Max, Avg
    from django.db.models.functions import TruncDate

    user = request.user
    profile = user.profile

    # 정보 수정 POST 처리
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=profile, user=user)
        if form.is_valid():
            form.save()
            messages.success(request, '회원 정보가 성공적으로 수정되었습니다.')
            return redirect('my_report')
    else:
        form = UserProfileUpdateForm(instance=profile, user=user)

    today = timezone.localdate()

    # 1. 오늘의 타자 성과 집계
    today_scores = TypingScore.objects.filter(user=request.user, created_at__date=today)
    typing_count = today_scores.count()
    max_speed = today_scores.aggregate(Max('speed'))['speed__max'] or 0
    avg_accuracy = today_scores.aggregate(Avg('accuracy'))['accuracy__avg'] or 0.0
    avg_accuracy = round(avg_accuracy, 1)

    # 2. 오늘의 코딩 학습 성과 집계
    today_progress_qs = UserProgress.objects.filter(
        user=request.user, completed=True, updated_at__date=today
    ).select_related('item__chapter__program')
    coding_count = today_progress_qs.count()

    # 3. 출석 체크 집계 (이번 달)
    current_year = today.year
    current_month = today.month
    attendances = Attendance.objects.filter(user=request.user, date__year=current_year, date__month=current_month)
    attendance_dates = [att.date.day for att in attendances]
    has_attended_today = Attendance.objects.filter(user=request.user, date=today).exists()

    # 달력 생성을 위한 이번 달 날짜 정보
    import calendar
    cal = calendar.Calendar(firstweekday=6) # 일요일 시작
    month_days = cal.monthdayscalendar(current_year, current_month)
    month_name = f"{current_year}년 {current_month}월"

    # 4. 날짜별 타속 기록 - 유형×언어별 분리
    CHART_TYPES = [('word', '단어연습'), ('short', '짧은글'), ('long', '긴글')]
    CHART_LANGS = ['ko', 'en']
    import json as _json

    chart_data_by_type_lang = {}
    for ptype, _ in CHART_TYPES:
        chart_data_by_type_lang[ptype] = {}
        for lang in CHART_LANGS:
            daily = (
                TypingScore.objects.filter(user=request.user, practice_type=ptype, language=lang)
                .annotate(date=TruncDate('created_at'))
                .values('date')
                .annotate(max_speed=Max('speed'), avg_speed=Avg('speed'))
                .order_by('date')
            )
            chart_data_by_type_lang[ptype][lang] = [
                {'label': s['date'].strftime('%m/%d'), 'max': s['max_speed'], 'avg': round(s['avg_speed'], 1)}
                for s in daily
            ]
    chart_data_json = _json.dumps(chart_data_by_type_lang)
    chart_data = chart_data_by_type_lang.get('word', {}).get('ko', [])  # 기존 호환

    # 마지막 연습 유형·언어
    last_score = TypingScore.objects.filter(user=request.user).order_by('-created_at').first()
    last_practice_type = last_score.practice_type if last_score else 'word'
    last_language = last_score.language if last_score else 'ko'
    if last_practice_type not in ('word', 'short', 'long'):
        last_practice_type = 'word'
    if last_language not in ('ko', 'en'):
        last_language = 'ko'

    # 목표 타속 (로드맵 기준) — [lang][type] 3중 구조
    # 한글 로드맵: 단어→짧은글→긴글 순으로 난이도 상승, 긴글은 목표 낮게
    # 영어: 한글의 약 50~60% 수준
    TYPING_TARGET_TABLE = {
        # (age_group): {ko: {word, short, long}, en: {word, short, long}}
        'baby':   {'ko': {'word': 100, 'short':  80, 'long':  None}, 'en': {'word':  50, 'short':  40, 'long': None}},
        'elem12': {'ko': {'word': 200, 'short': 150, 'long':  None}, 'en': {'word': 100, 'short':  80, 'long': None}},
        'elem34': {'ko': {'word': 250, 'short': 200, 'long':  150},  'en': {'word': 130, 'short': 100, 'long':  80}},
        'elem56': {'ko': {'word': 300, 'short': 300, 'long':  250},  'en': {'word': 160, 'short': 150, 'long': 120}},
        'midhigh':{'ko': {'word': 400, 'short': 400, 'long':  350},  'en': {'word': 220, 'short': 200, 'long': 180}},
    }
    typing_targets = {}       # {lang: {type: speed}}
    typing_age_label = ''     # "초5~6 (12~13세)"
    if profile.birth_date:
        age = today.year - profile.birth_date.year - (
            (today.month, today.day) < (profile.birth_date.month, profile.birth_date.day)
        )
        if age <= 7:
            grp, typing_age_label = 'baby',    '유아 (5~7세)'
        elif age <= 9:
            grp, typing_age_label = 'elem12',  '초1~2 (8~9세)'
        elif age <= 11:
            grp, typing_age_label = 'elem34',  '초3~4 (10~11세)'
        elif age <= 13:
            grp, typing_age_label = 'elem56',  '초5~6 (12~13세)'
        else:
            grp, typing_age_label = 'midhigh', '중·고등 (14세+)'
        typing_targets = TYPING_TARGET_TABLE[grp]
    typing_targets_json = _json.dumps(typing_targets)
    typing_target_speed = (typing_targets.get('ko') or {}).get('word')  # 기존 호환

    # 5. 과거 누적 통계
    all_scores = TypingScore.objects.filter(user=user)
    total_typing_count = all_scores.count()
    global_max_speed = all_scores.aggregate(Max('speed'))['speed__max'] or 0
    ko_avg_speed = round(all_scores.filter(language='ko', practice_type='short').aggregate(Avg('speed'))['speed__avg'] or 0)
    en_avg_speed = round(all_scores.filter(language='en', practice_type='short').aggregate(Avg('speed'))['speed__avg'] or 0)

    # 6. 프로필 / 작품 / 배지 통계
    my_projects = Project.objects.filter(author=user)
    total_likes_received = Like.objects.filter(project__author=user).count()
    total_bookmarks_received = Bookmark.objects.filter(project__author=user).count()
    badge_catalog = get_active_badges_with_user_state(user)
    badge_count = get_user_badge_count(user)

    # 7. 자격취득 / 수상이력 (학생 이름 매칭)
    from .models import Certification, Award
    my_certs = []
    my_awards = []
    real_name = profile.real_name if profile.real_name else None
    if real_name:
        my_certs = list(Certification.objects.filter(student_name=real_name).select_related('cert_info').order_by('-date_acquired'))
        my_awards = list(Award.objects.filter(student_name=real_name).select_related('competition_type').order_by('-date_awarded'))

    # 나이 계산
    profile_age = None
    if profile.birth_date:
        born = profile.birth_date
        profile_age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    # 8. 학년별 추천 자격증 (급수별 세분화)
    def age_to_grade_key(age):
        if age is None: return None
        if age <= 7:  return 'kids_5_7'
        if age <= 9:  return 'elem_1_2'
        if age <= 11: return 'elem_3_4'
        if age <= 13: return 'elem_5_6'
        if age <= 19: return 'mid_high'
        return 'adult'

    # 급수별 추천 목록 (certinfo_name = CertInfo.name 매핑용)
    _REC = {
        'kids_5_7': [],
        'elem_1_2': [
            {'name': 'COS Entry 4급',        'category': 'block_coding', 'issuer': 'YBM',          'certinfo_name': 'COS Entry'},
            {'name': 'COS Entry 3급',         'category': 'block_coding', 'issuer': 'YBM',          'certinfo_name': 'COS Entry'},
            {'name': 'KAIT 코딩활용능력 3급', 'category': 'block_coding', 'issuer': 'KAIT',         'certinfo_name': 'KAIT 코딩활용능력'},
        ],
        'elem_3_4': [
            {'name': 'COS Entry 2급',         'category': 'block_coding', 'issuer': 'YBM',          'certinfo_name': 'COS Entry'},
            {'name': 'COS Entry 1급',         'category': 'block_coding', 'issuer': 'YBM',          'certinfo_name': 'COS Entry'},
            {'name': 'KAIT 코딩활용능력 3급', 'category': 'block_coding', 'issuer': 'KAIT',         'certinfo_name': 'KAIT 코딩활용능력'},
            {'name': 'KAIT 코딩활용능력 2급', 'category': 'block_coding', 'issuer': 'KAIT',         'certinfo_name': 'KAIT 코딩활용능력'},
            {'name': 'AICE Future 3급',        'category': 'ai',           'issuer': 'KT·한국경제신문', 'certinfo_name': 'AICE Future'},
            {'name': 'AICE Future 2급',        'category': 'ai',           'issuer': 'KT·한국경제신문', 'certinfo_name': 'AICE Future'},
            {'name': 'ITQ',                    'category': 'doc_work',     'issuer': 'KPC',          'certinfo_name': 'ITQ'},
        ],
        'elem_5_6': [
            {'name': 'COS Entry 1급',          'category': 'block_coding', 'issuer': 'YBM',          'certinfo_name': 'COS Entry'},
            {'name': 'KAIT 코딩활용능력 2급',  'category': 'block_coding', 'issuer': 'KAIT',         'certinfo_name': 'KAIT 코딩활용능력'},
            {'name': 'KAIT 코딩활용능력 1급',  'category': 'python',       'issuer': 'KAIT',         'certinfo_name': 'KAIT 코딩활용능력'},
            {'name': 'COS Pro 3급',            'category': 'python',       'issuer': 'YBM',          'certinfo_name': 'COS Pro'},
            {'name': 'AICE Future 2급',        'category': 'ai',           'issuer': 'KT·한국경제신문', 'certinfo_name': 'AICE Future'},
            {'name': 'AICE Future 1급',        'category': 'ai',           'issuer': 'KT·한국경제신문', 'certinfo_name': 'AICE Future'},
            {'name': 'AICE Junior',            'category': 'ai',           'issuer': 'KT·한국경제신문', 'certinfo_name': 'AICE Junior'},
            {'name': 'ITQ',                    'category': 'doc_work',     'issuer': 'KPC',          'certinfo_name': 'ITQ'},
        ],
        'mid_high': [
            {'name': 'KAIT 코딩활용능력 1급',  'category': 'python',       'issuer': 'KAIT',         'certinfo_name': 'KAIT 코딩활용능력'},
            {'name': 'COS Pro 3급',            'category': 'python',       'issuer': 'YBM',          'certinfo_name': 'COS Pro'},
            {'name': 'COS Pro 2급',            'category': 'python',       'issuer': 'YBM',          'certinfo_name': 'COS Pro'},
            {'name': 'COS Pro 1급',            'category': 'python',       'issuer': 'YBM',          'certinfo_name': 'COS Pro'},
            {'name': 'AICE Junior',            'category': 'ai',           'issuer': 'KT·한국경제신문', 'certinfo_name': 'AICE Junior'},
            {'name': 'AICE Basic',             'category': 'ai',           'issuer': 'KT·한국경제신문', 'certinfo_name': 'AICE Basic'},
            {'name': 'AICE Generative 2급',    'category': 'ai',           'issuer': 'KT·한국경제신문', 'certinfo_name': 'AICE Generative'},
            {'name': 'AICE Generative 1급',    'category': 'ai',           'issuer': 'KT·한국경제신문', 'certinfo_name': 'AICE Generative'},
        ],
        'adult': [
            {'name': 'COS Pro 1급',            'category': 'python',       'issuer': 'YBM',          'certinfo_name': 'COS Pro'},
            {'name': 'AICE Generative 1급',    'category': 'ai',           'issuer': 'KT·한국경제신문', 'certinfo_name': 'AICE Generative'},
            {'name': 'AICE Associate',         'category': 'ai',           'issuer': 'KT·한국경제신문', 'certinfo_name': 'AICE Associate'},
        ],
    }

    student_grade_key = age_to_grade_key(profile_age)
    earned_names = {c.cert_name for c in my_certs}
    certinfo_lookup = {ci.name: ci for ci in CertInfo.objects.filter(category__isnull=False)}

    recommended_certs = []
    if student_grade_key:
        # certinfo_name별 최고 등급만 남김 (목록 순서가 낮→높이므로 덮어쓰기)
        best_per_family = {}
        for rec in _REC.get(student_grade_key, []):
            if rec['name'] not in earned_names:
                best_per_family[rec['certinfo_name']] = rec
        for rec in best_per_family.values():
            ci = certinfo_lookup.get(rec['certinfo_name'])
            recommended_certs.append({
                'name': rec['name'],
                'category': rec['category'],
                'issuer': rec['issuer'],
                'certinfo': ci,
            })

    context = {
        'today': today,
        'typing_count': typing_count,
        'max_speed': max_speed,
        'avg_accuracy': avg_accuracy,
        'coding_count': coding_count,
        'today_progress_list': today_progress_qs,
        'has_attended_today': has_attended_today,
        'attendance_dates': attendance_dates,
        'month_days': month_days,
        'month_name': month_name,
        'chart_data': chart_data,
        'chart_data_json': chart_data_json,
        'last_practice_type': last_practice_type,
        'last_language': last_language,
        'typing_targets_json': typing_targets_json,
        'typing_target_speed': typing_target_speed,
        'typing_age_label': typing_age_label,
        'total_typing_count': total_typing_count,
        'global_max_speed': global_max_speed,
        'ko_avg_speed': ko_avg_speed,
        'en_avg_speed': en_avg_speed,
        # 프로필 통합
        'profile': profile,
        'form': form,
        'my_projects_count': my_projects.count(),
        'total_likes': total_likes_received,
        'total_bookmarks': total_bookmarks_received,
        'badge_catalog': badge_catalog,
        'badge_count': badge_count,
        'profile_age': profile_age,
        'my_certs': my_certs,
        'my_awards': my_awards,
        'cert_count': len(my_certs),
        'award_count': len(my_awards),
        'recommended_certs': recommended_certs,
        'student_grade_key': student_grade_key,
    }
    return render(request, 'arcade/my_report.html', context)


@login_required
@require_POST
def api_submit_attendance(request):
    from django.utils import timezone
    from .models import Attendance
    
    today = timezone.localdate()
    attendance, created = Attendance.objects.get_or_create(user=request.user, date=today)
    
    return JsonResponse({
        'status': 'success',
        'created': created,
        'date': today.strftime('%Y-%m-%d')
    })


@login_required
@user_passes_test(staff_check)
@require_POST
def api_sync_aice_schedule(request):
    """AICE 공식 시험 일정을 크롤링하여 DB에 동기화해 주는 관리자용 API"""
    from django.core.management import call_command
    import io
    
    out = io.StringIO()
    try:
        call_command('sync_aice_schedule', stdout=out, stderr=out)
        output_log = out.getvalue()
        
        import re
        match = re.search(r'새로 등록된 일정:\s*(\d+)개', output_log)
        added_count = int(match.group(1)) if match else 0
        
        return JsonResponse({
            'status': 'success',
            'message': f'AICE 시험 일정 동기화가 완료되었습니다. (새로 추가된 일정: {added_count}개)',
            'log': output_log
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'동기화 작업 중 오류가 발생했습니다: {str(e)}'
        })


@login_required
@require_POST
def api_refresh_session(request):
    """사용자가 세션 연장 버튼을 클릭할 때 호출되어 Django 세션을 갱신함"""
    request.session.modified = True
    return JsonResponse({
        'status': 'success',
        'message': '로그인 세션이 성공적으로 연장되었습니다.'
    })






# ═══════════════════════════════════════════════════════════
# 작품 평가단
# ═══════════════════════════════════════════════════════════

def gallery_admin(request):
    if not request.user.is_staff:
        return redirect('home')
    from .models import GalleryRoom
    rooms = GalleryRoom.objects.prefetch_related('posters').all()
    return render(request, 'arcade/gallery_admin.html', {'rooms': rooms})


def gallery_vote(request):
    return render(request, 'arcade/gallery_vote.html')


@require_POST
def api_gallery_room_create(request):
    if not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': '권한 없음'}, status=403)
    from .models import GalleryRoom, GalleryPoster
    name = request.POST.get('name', '').strip()
    if not name:
        return JsonResponse({'ok': False, 'error': '방 이름을 입력해주세요.'})
    images = request.FILES.getlist('images')
    if not images:
        return JsonResponse({'ok': False, 'error': '포스터 이미지를 하나 이상 업로드해주세요.'})
    room = GalleryRoom.objects.create(name=name)
    for i, img in enumerate(images):
        title = img.name.rsplit('.', 1)[0]
        GalleryPoster.objects.create(room=room, image=img, title=title, order=i)
    return JsonResponse({'ok': True, 'room_id': room.id, 'name': room.name})


@require_POST
def api_gallery_room_delete(request, room_id):
    if not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': '권한 없음'}, status=403)
    from .models import GalleryRoom
    try:
        room = GalleryRoom.objects.get(id=room_id)
        room.delete()
        return JsonResponse({'ok': True})
    except GalleryRoom.DoesNotExist:
        return JsonResponse({'ok': False, 'error': '방을 찾을 수 없습니다.'})


@require_POST
def api_gallery_control(request, room_id):
    if not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': '권한 없음'}, status=403)
    from .models import GalleryRoom
    try:
        room = GalleryRoom.objects.get(id=room_id)
    except GalleryRoom.DoesNotExist:
        return JsonResponse({'ok': False, 'error': '방 없음'})
    action = request.POST.get('action')
    poster_count = room.posters.count()
    if action == 'start':
        if room.status != 'waiting':
            return JsonResponse({'ok': False, 'error': '이미 시작됐습니다.'})
        room.status = 'voting'
        room.current_index = 0
    elif action == 'next':
        if room.status != 'voting':
            return JsonResponse({'ok': False, 'error': '진행 중이 아닙니다.'})
        next_idx = room.current_index + 1
        if next_idx >= poster_count:
            room.status = 'done'
        else:
            room.current_index = next_idx
    elif action == 'end':
        room.status = 'done'
    else:
        return JsonResponse({'ok': False, 'error': '알 수 없는 액션'})
    room.save()
    return JsonResponse({'ok': True, 'status': room.status, 'current_index': room.current_index})


def api_gallery_rooms(request):
    from .models import GalleryRoom
    rooms = GalleryRoom.objects.exclude(status='done').order_by('-created_at')
    return JsonResponse({'rooms': [{'id': r.id, 'name': r.name, 'status': r.status} for r in rooms]})


def api_gallery_room_stats(request, room_id):
    """관리자용: 방 접속자 수 조회"""
    if not request.user.is_staff:
        return JsonResponse({'ok': False}, status=403)
    from .models import GalleryRoom, GalleryMember
    try:
        room = GalleryRoom.objects.get(id=room_id)
    except GalleryRoom.DoesNotExist:
        return JsonResponse({'ok': False})
    members = list(GalleryMember.objects.filter(room=room).values('name', 'last_seen').order_by('last_seen'))
    return JsonResponse({'ok': True, 'member_count': len(members), 'members': members})


@require_POST
def api_gallery_join(request):
    from .models import GalleryRoom, GalleryMember
    data = json.loads(request.body)
    room_id = data.get('room_id')
    voter_name = data.get('name', '').strip()
    if not voter_name:
        return JsonResponse({'ok': False, 'error': '이름을 입력해주세요.'})
    try:
        room = GalleryRoom.objects.get(id=room_id)
    except GalleryRoom.DoesNotExist:
        return JsonResponse({'ok': False, 'error': '방을 찾을 수 없습니다.'})
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    GalleryMember.objects.update_or_create(
        room=room, session_key=session_key,
        defaults={'name': voter_name}
    )
    request.session['gallery_room_id'] = room.id
    request.session['gallery_voter_name'] = voter_name
    request.session.modified = True
    return JsonResponse({'ok': True, 'room_id': room.id, 'room_name': room.name,
                         'session_key': session_key})


def api_gallery_state(request):
    from .models import GalleryRoom, GalleryVote
    from django.db.models import Avg, Count
    room_id = request.GET.get('room_id')
    try:
        room = GalleryRoom.objects.get(id=room_id)
    except GalleryRoom.DoesNotExist:
        return JsonResponse({'ok': False, 'error': '방 없음'})

    session_key = request.session.session_key or ''
    poster_data = None
    my_score = 0  # 0 = 미투표, 1~5 = 별점

    if room.status == 'voting' and room.current_index >= 0:
        posters = list(room.posters.all())
        if room.current_index < len(posters):
            poster = posters[room.current_index]
            my_vote_obj = GalleryVote.objects.filter(
                poster=poster, voter_session=session_key
            ).first()
            my_score = my_vote_obj.score if my_vote_obj else 0
            agg = poster.votes.aggregate(avg=Avg('score'), count=Count('id'))
            poster_data = {
                'id': poster.id,
                'title': poster.title,
                'image_url': poster.image.url,
                'vote_count': agg['count'] or 0,
                'avg_score': round(agg['avg'] or 0, 1),
                'index': room.current_index,
                'total': len(posters),
            }

    results = None
    if room.status == 'done':
        results = []
        for poster in room.posters.all():
            agg = poster.votes.aggregate(avg=Avg('score'), count=Count('id'))
            results.append({
                'id': poster.id,
                'title': poster.title,
                'image_url': poster.image.url,
                'vote_count': agg['count'] or 0,
                'avg_score': round(agg['avg'] or 0, 1),
                'order': poster.order,
            })
        results.sort(key=lambda x: (-x['avg_score'], -x['vote_count']))

    return JsonResponse({
        'ok': True,
        'status': room.status,
        'current_index': room.current_index,
        'poster': poster_data,
        'my_score': my_score,
        'results': results,
    })


@require_POST
def api_gallery_vote(request):
    from .models import GalleryPoster, GalleryVote
    from django.db.models import Avg, Count
    data = json.loads(request.body)
    poster_id = data.get('poster_id')
    score = int(data.get('score', 5))
    if not (1 <= score <= 5):
        score = 5
    voter_name = request.session.get('gallery_voter_name', '')
    session_key = request.session.session_key or ''
    if not session_key or not voter_name:
        return JsonResponse({'ok': False, 'error': '세션 정보가 없습니다. 다시 입장해주세요.'})
    try:
        poster = GalleryPoster.objects.select_related('room').get(id=poster_id)
    except GalleryPoster.DoesNotExist:
        return JsonResponse({'ok': False, 'error': '포스터 없음'})
    if poster.room.status != 'voting':
        return JsonResponse({'ok': False, 'error': '투표 중인 방이 아닙니다.'})
    _, created = GalleryVote.objects.get_or_create(
        poster=poster, voter_session=session_key,
        defaults={'voter_name': voter_name, 'score': score}
    )
    agg = poster.votes.aggregate(avg=Avg('score'), count=Count('id'))
    return JsonResponse({
        'ok': True, 'created': created,
        'vote_count': agg['count'] or 0,
        'avg_score': round(agg['avg'] or 0, 1),
    })
