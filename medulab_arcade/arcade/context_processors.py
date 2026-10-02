from django.conf import settings
from django.core.cache import cache


def academy_info(request):
    return {
        'ACADEMY_CEO_NAME': getattr(settings, 'ACADEMY_CEO_NAME', ''),
        'ACADEMY_BIZ_NUMBER': getattr(settings, 'ACADEMY_BIZ_NUMBER', ''),
        'ACADEMY_ADDRESS': getattr(settings, 'ACADEMY_ADDRESS', ''),
        'ACADEMY_PHONE': getattr(settings, 'ACADEMY_PHONE', ''),
        'ACADEMY_PHONE_MOBILE': getattr(settings, 'ACADEMY_PHONE_MOBILE', ''),
    }


def checkin_modal(request):
    """메듀랩 학생이 오늘 출석 기록(출석/보강/접속 중 아무거나)을 아직 남기지 않았다면,
    확인할 때(또는 X로 로그아웃할 때)까지 모든 페이지에서 '학원입니까?' 모달을 계속 띄운다.
    새로고침으로 건너뛸 수 없도록, 세션 플래그가 아니라 매 요청마다 DB 상태를 직접 확인한다."""
    if not request.user.is_authenticated or request.user.is_staff:
        return {'show_checkin_modal': False}

    profile = getattr(request.user, 'profile', None)
    if not profile or profile.user_type != 'medulab_member':
        return {'show_checkin_modal': False}

    from django.utils import timezone
    from .models import Attendance, ClassEnrollment

    today = timezone.localdate()
    if Attendance.objects.filter(user=request.user, date=today).exists():
        return {'show_checkin_modal': False}

    code_for_py_weekday = {0: '1', 1: '2', 2: '3', 3: '4', 4: '5', 5: '6', 6: '0'}
    code = code_for_py_weekday[today.weekday()]

    today_class = None
    for enrollment in ClassEnrollment.objects.filter(
        student=request.user, is_active=True
    ).select_related('school_class'):
        sc = enrollment.school_class
        codes = sc.days_of_week.split(',') if sc.days_of_week else []
        if code in codes:
            if today_class is None or (sc.start_time and sc.start_time < today_class.start_time):
                today_class = sc

    return {
        'show_checkin_modal': True,
        'checkin_today_class': today_class,
    }


def nav_items(request):
    items = cache.get('nav_items_qs')
    if items is None:
        from .models import NavItem
        items = list(NavItem.objects.filter(is_active=True))
        cache.set('nav_items_qs', items, 300)
    notices = [i for i in items if i.section == 'notices']
    learning = [i for i in items if i.section == 'learning']
    return {
        'nav_notices': notices,
        'nav_learning': learning,
    }
