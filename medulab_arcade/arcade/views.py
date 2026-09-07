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
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.db import DatabaseError
from django.db.models import Count, Q, Case, When, Value, IntegerField, Sum
from django.contrib.auth import login
from django.contrib import messages
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from .badge_service import get_active_badges_with_user_state, get_recent_user_badges, get_user_badge_count
from .models import Badge, Project, Category, Like, Bookmark, Tag, UserProfile, EmailChangeRequest, SignupEmailVerification, ScheduleAttachment, ScheduleEvent, Notice, Award, Certification, CertInfo, CompetitionType, Contest, SchoolClass, ClassEnrollment, ParentChildLink, TuitionInvoice, ClassAttendance, TuitionBatchPayment, InstagramConfig, InstagramPost
from .forms import ProjectUploadForm, SignUpForm, AdminUserForm, AdminUserProfileForm, BadgeForm, ScheduleEventForm, TimetableForm, UserProfileUpdateForm, MedulabParentUpgradeForm, SocialOnboardingForm, SchoolClassForm
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


def future_career_video(request):
    """AI 미래직업영상 만들기 Web Activity (12차시, 독립형 페이지)"""
    return render(request, 'arcade/tools/future_career_video.html')


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


def carbon_invention(request):
    return render(request, 'arcade/carbon_invention.html')


def problem_finder(request):
    return render(request, 'arcade/problem_finder.html')


def camp_planner(request):
    return render(request, 'arcade/camp_planner.html')

def local_problem_finder(request):
    return render(request, 'arcade/local_problem_finder.html')


def _infer_problem_category(text):
    rules = [
        ('교통', ['교통','버스','주차','도로','신호','보행','자전거','이동','정류장','횡단보도']),
        ('환경', ['환경','쓰레기','공기','수질','미세먼지','오염','녹지','소음','악취']),
        ('안전', ['안전','범죄','사고','위험','화재','재난','침수','가로등','조명']),
        ('복지', ['복지','노인','어르신','장애','아동','청소년','돌봄','고령','독거']),
        ('경제', ['경제','일자리','취업','상권','임대','소상공인','창업','매출','폐업']),
        ('교육', ['교육','학교','학생','학원','방과후','진로','디지털','격차']),
        ('주거', ['주거','주택','아파트','빈집','층간','소음','노후','침수']),
        ('의료', ['의료','병원','건강','응급','진료','약국','복약','정신']),
        ('문화', ['문화','관광','체육','공원','여가','행사','시설','광장']),
    ]
    for cat, keywords in rules:
        if any(kw in text for kw in keywords):
            return cat
    return '기타'


def _get_curated_problems(city, district):
    GWANGJU = {
        '동구': [
            {'title': '충장로·금남로 상권 공동화로 빈 건물이 늘고 있어요', 'category': '경제'},
            {'title': '국립아시아문화전당 주변 주차 공간이 부족해요', 'category': '교통'},
            {'title': '동명동 골목 야간 조명이 부족해서 밤에 무서워요', 'category': '안전'},
            {'title': '노후 주택이 많아 안전 점검이 필요해요', 'category': '주거'},
            {'title': '대인시장 활성화를 위한 청년 창업 지원이 부족해요', 'category': '경제'},
            {'title': '원도심 지역 대중교통 배차 간격이 너무 길어요', 'category': '교통'},
            {'title': '독거 어르신이 많아 복지 사각지대가 생기고 있어요', 'category': '복지'},
            {'title': '하천 수질 오염으로 악취가 발생해요', 'category': '환경'},
        ],
        '서구': [
            {'title': '양동시장 주변 주차 공간이 심각하게 부족해요', 'category': '교통'},
            {'title': '광천동 일대 도로 교통 체증이 매일 발생해요', 'category': '교통'},
            {'title': '노후 주택가 골목에 가로등이 없어 야간 안전 위협이 있어요', 'category': '안전'},
            {'title': '소상공인 온라인 판매 전환 교육·지원이 부족해요', 'category': '경제'},
            {'title': '양동시장 화장실 등 편의시설 환경이 열악해요', 'category': '문화'},
            {'title': '화정동 일대 쓰레기 불법 투기 문제가 심각해요', 'category': '환경'},
            {'title': '청소년 방과후 활동을 위한 공간과 프로그램이 부족해요', 'category': '교육'},
            {'title': '거동이 불편한 어르신의 병원 이동 수단이 없어요', 'category': '복지'},
        ],
        '남구': [
            {'title': '봉선동 교통 체증이 심해 출퇴근이 어려워요', 'category': '교통'},
            {'title': '주거지 인근 불법 쓰레기 투기 문제가 지속돼요', 'category': '환경'},
            {'title': '도심 내 자전거 전용도로가 끊겨 연결이 안 돼요', 'category': '교통'},
            {'title': '노후 주택 밀집 지역 침수 피해 우려가 있어요', 'category': '주거'},
            {'title': '지역 상권 침체로 빈 상가가 증가하고 있어요', 'category': '경제'},
            {'title': '청소년 문화·체육 시설이 부족해요', 'category': '교육'},
            {'title': '독거 어르신 안전 확인 시스템이 부족해요', 'category': '복지'},
            {'title': '주택가 야간 조명이 부족해 범죄 위험이 있어요', 'category': '안전'},
        ],
        '북구': [
            {'title': '첨단지구 출퇴근 시간 교통 혼잡이 심해요', 'category': '교통'},
            {'title': '전통시장 인근 대형마트 쏠림으로 소상공인이 침체됐어요', 'category': '경제'},
            {'title': '재개발 예정 지역 노후 건물 안전 문제가 있어요', 'category': '안전'},
            {'title': '신규 아파트 단지 주변 주차 공간이 부족해요', 'category': '교통'},
            {'title': '미세먼지 고농도 시 야외 활동 안내가 부족해요', 'category': '환경'},
            {'title': '청소년을 위한 방과후 돌봄 시설이 부족해요', 'category': '교육'},
            {'title': '외국인 근로자·다문화 가정 지원 서비스가 부족해요', 'category': '복지'},
            {'title': '버스 정류장 시설이 노후해 비·바람을 피할 수 없어요', 'category': '교통'},
        ],
        '광산구': [
            {'title': '수완지구 주차 공간 부족으로 불법 주차가 많아요', 'category': '교통'},
            {'title': '하남산단 인근 공기 오염과 소음 민원이 많아요', 'category': '환경'},
            {'title': '외국인 밀집 지역 쓰레기 분리수거 안내가 부족해요', 'category': '환경'},
            {'title': '도시 외곽 지역 대중교통 배차가 너무 드물어요', 'category': '교통'},
            {'title': '첨단산단 청년 근로자 주거 지원이 부족해요', 'category': '주거'},
            {'title': '어등산 인근 야간 등산로 안전 시설이 미흡해요', 'category': '안전'},
            {'title': '노인 돌봄 시설 수요 대비 공급이 부족해요', 'category': '복지'},
            {'title': '초등학교 앞 스쿨존 안전 시설 개선이 필요해요', 'category': '안전'},
        ],
    }
    GENERIC_BY_CITY = {
        '서울특별시': [
            {'title': '지하철역 주변 불법 주·정차 문제가 심해요', 'category': '교통'},
            {'title': '골목 보행로가 좁고 위험해 개선이 필요해요', 'category': '안전'},
            {'title': '전통시장 인근 주차 공간이 부족해요', 'category': '교통'},
            {'title': '노후 상가 밀집 지역 도로 포장 상태가 나빠요', 'category': '안전'},
            {'title': '야간 골목길 조명이 부족해 범죄 위험이 있어요', 'category': '안전'},
            {'title': '독거 노인 복지 서비스 신청 경로가 복잡해요', 'category': '복지'},
            {'title': '청년 임대주택 공급이 부족해 이사가 어려워요', 'category': '주거'},
            {'title': '음식물 쓰레기 처리 시설이 부족해요', 'category': '환경'},
        ],
        '부산광역시': [
            {'title': '구도심 지역 빈 건물이 늘어 지역 활력이 떨어지고 있어요', 'category': '경제'},
            {'title': '해안가 주변 불법 주차 문제가 심각해요', 'category': '교통'},
            {'title': '노후 주택 밀집지역 개량 지원이 필요해요', 'category': '주거'},
            {'title': '관광객 급증으로 주민 생활 소음 피해가 커요', 'category': '안전'},
            {'title': '외국인 관광객을 위한 다국어 안내가 부족해요', 'category': '문화'},
            {'title': '노인 인구 급증 대비 돌봄 인력이 부족해요', 'category': '복지'},
            {'title': '고지대 주거지 급경사 도로가 보행 위험 요소에요', 'category': '안전'},
            {'title': '대기 오염으로 호흡기 질환 민원이 많아요', 'category': '환경'},
        ],
    }
    GENERIC = [
        {'title': '대중교통 배차 간격이 길어 대기 시간이 길어요', 'category': '교통'},
        {'title': '야간 골목길 조명 부족으로 안전 우려가 있어요', 'category': '안전'},
        {'title': '불법 쓰레기 투기 문제로 생활 환경이 악화됐어요', 'category': '환경'},
        {'title': '노후 주택 주민을 위한 지원 서비스가 부족해요', 'category': '주거'},
        {'title': '소상공인 지원을 위한 지역 상권 활성화가 필요해요', 'category': '경제'},
        {'title': '청소년을 위한 방과후 프로그램 공간이 부족해요', 'category': '교육'},
        {'title': '독거 어르신 안전 확인 및 복지 서비스가 필요해요', 'category': '복지'},
        {'title': '주차 공간 부족으로 불법 주차 민원이 자주 발생해요', 'category': '교통'},
        {'title': '쓰레기 분리수거 안내 부족으로 오배출이 많아요', 'category': '환경'},
        {'title': '지역 의료 시설 접근성이 낮아 병원까지 멀리 가야 해요', 'category': '의료'},
    ]
    city_name = city or ''
    # 광주전남특별자치도 — 구 이름 앞에 "광주 " 접두어 포함
    if '광주전남' in city_name or '광주' in city_name:
        # district는 "광주 서구" 형식이므로 뒷부분만 추출
        district_key = district.replace('광주 ', '').strip() if district else ''
        # 전남 시/군 큐레이션
        JEONNAM = {
            '목포시': [
                {'title': '구도심 빈 건물 증가로 도시 활력이 떨어지고 있어요', 'category': '경제'},
                {'title': '항구 주변 주차 공간 부족 문제가 심해요', 'category': '교통'},
                {'title': '노후 주택 밀집지역 안전 점검이 필요해요', 'category': '주거'},
                {'title': '해안 관광지 외국어 안내판이 부족해요', 'category': '문화'},
                {'title': '청년 일자리 부족으로 인구 유출이 심각해요', 'category': '경제'},
                {'title': '어르신 복지 시설 접근성이 낮아요', 'category': '복지'},
            ],
            '여수시': [
                {'title': '관광 성수기 교통 혼잡으로 주민 불편이 커요', 'category': '교통'},
                {'title': '해양 쓰레기 문제로 관광지 이미지가 나빠지고 있어요', 'category': '환경'},
                {'title': '야간 관광 인프라가 부족해 방문객이 일찍 떠나요', 'category': '문화'},
                {'title': '어촌 고령화로 지역 공동체가 무너지고 있어요', 'category': '복지'},
                {'title': '석유화학단지 주변 대기 오염 민원이 많아요', 'category': '환경'},
                {'title': '섬 지역 의료 접근성이 매우 낮아요', 'category': '의료'},
            ],
            '순천시': [
                {'title': '생태공원 주변 불법 쓰레기 투기가 심해요', 'category': '환경'},
                {'title': '대중교통 연결이 부족해 농촌 주민 이동이 불편해요', 'category': '교통'},
                {'title': '청년 창업 지원 공간과 프로그램이 부족해요', 'category': '경제'},
                {'title': '노인 인구 증가 대비 돌봄 서비스가 부족해요', 'category': '복지'},
                {'title': '주차 공간 부족으로 도심 혼잡이 심해요', 'category': '교통'},
                {'title': '청소년 문화·여가 시설이 부족해요', 'category': '교육'},
            ],
            '나주시': [
                {'title': '혁신도시 입주 기업 대비 주거·생활 인프라가 부족해요', 'category': '주거'},
                {'title': '농촌 고령화로 영농 인력이 부족해요', 'category': '경제'},
                {'title': '대중교통 연계가 부족해 혁신도시 출퇴근이 불편해요', 'category': '교통'},
                {'title': '청년 유입을 위한 문화·여가 시설이 부족해요', 'category': '문화'},
                {'title': '전통시장 활성화를 위한 지원이 필요해요', 'category': '경제'},
                {'title': '빈집 문제로 구도심 경관이 나빠지고 있어요', 'category': '주거'},
            ],
        }
        problems = GWANGJU.get(district_key, []) or JEONNAM.get(district, [])
        if not problems:
            # 전남 지역이면 전남 공통 + 광주 샘플
            if district and district not in ['동구','서구','남구','북구','광산구',
                                              '광주 동구','광주 서구','광주 남구','광주 북구','광주 광산구']:
                return [
                    {'title': f'{district} 대중교통 배차 간격이 너무 길어요', 'category': '교통'},
                    {'title': f'{district} 고령화로 빈집·빈 상가가 늘어나고 있어요', 'category': '경제'},
                    {'title': f'{district} 청소년·청년을 위한 문화 시설이 부족해요', 'category': '교육'},
                    {'title': f'{district} 노인 돌봄 및 복지 서비스가 부족해요', 'category': '복지'},
                    {'title': f'{district} 주민 생활 불편 민원 처리가 늦어요', 'category': '기타'},
                    {'title': f'{district} 쓰레기 불법 투기 문제가 지속돼요', 'category': '환경'},
                    {'title': f'{district} 지역 경제 활성화를 위한 지원이 필요해요', 'category': '경제'},
                    {'title': f'{district} 응급의료 접근성이 낮아요', 'category': '의료'},
                ]
            # 광주 전체 샘플
            combined = []
            for probs in GWANGJU.values():
                combined.extend(probs[:2])
            return combined[:10]
        return problems
    if city_name in GENERIC_BY_CITY:
        return GENERIC_BY_CITY[city_name]
    return GENERIC


def api_local_problems(request):
    import urllib.request as urllib_req
    import xml.etree.ElementTree as ET
    from urllib.parse import quote as uq
    from datetime import datetime, timedelta
    from email.utils import parsedate

    city = request.GET.get('city', '').strip()
    district = request.GET.get('district', '').strip()
    if not city:
        return JsonResponse({'ok': False, 'error': '지역을 선택해주세요.'})

    try:
        days = int(request.GET.get('days', 90))
        if days not in (7, 30, 90, 180, 365):
            days = 90
    except (ValueError, TypeError):
        days = 90

    cutoff = datetime.now() - timedelta(days=days)
    after_str = cutoff.strftime('%Y-%m-%d')

    location = f"{city} {district}".strip() if district else city
    problems = []

    try:
        for suffix in ['지역문제 불편', '민원 개선 요구']:
            query = f"{location} {suffix} after:{after_str}"
            url = f"https://news.google.com/rss/search?q={uq(query)}&hl=ko&gl=KR&ceid=KR:ko"
            req = urllib_req.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib_req.urlopen(req, timeout=6) as resp:
                content = resp.read()
            root = ET.fromstring(content)
            channel = root.find('channel')
            if channel is None:
                continue
            for item in channel.findall('item')[:8]:
                title = item.findtext('title', '').strip()
                link = item.findtext('link', '').strip()
                source_el = item.find('source')
                source_name = source_el.text.strip() if source_el is not None and source_el.text else ''
                pub_date = item.findtext('pubDate', '').strip()
                # pubDate: "Thu, 15 Aug 2024 12:00:00 GMT" → "2024-08-15"
                date_str = ''
                try:
                    pd = parsedate(pub_date)
                    if pd:
                        article_date = datetime(pd[0], pd[1], pd[2])
                        if article_date < cutoff:
                            continue  # 기간 외 기사 제외
                        date_str = f"{pd[0]}-{pd[1]:02d}-{pd[2]:02d}"
                except Exception:
                    pass
                if ' - ' in title:
                    title = title.rsplit(' - ', 1)[0].strip()
                if not title or len(title) < 8:
                    continue
                if not any(kw in title for kw in [
                    city[:2], district[:2] if len(district) >= 2 else '',
                    '지역', '주민', '시민', '불편', '문제', '개선', '민원', '부족', '위험'
                ]):
                    continue
                problems.append({
                    'title': title,
                    'category': _infer_problem_category(title),
                    'source': source_name,
                    'link': link,
                    'date': date_str,
                })
            if len(problems) >= 8:
                break
        # Deduplicate
        seen, unique = set(), []
        for p in problems:
            key = p['title'][:20]
            if key not in seen:
                seen.add(key)
                unique.append(p)
        problems = unique[:12]
    except Exception:
        pass

    if len(problems) < 4:
        curated = _get_curated_problems(city, district)
        existing_titles = {p['title'][:15] for p in problems}
        for p in curated:
            if p['title'][:15] not in existing_titles and len(problems) < 12:
                problems.append(p)

    return JsonResponse({'ok': True, 'problems': problems, 'location': location})


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
    day_names = ['일', '월', '화', '수', '목', '금', '토']

    def _common_title_prefix(titles):
        word_lists = [t.split(' ') for t in titles]
        prefix = []
        for words in zip(*word_lists):
            if len(set(words)) == 1:
                prefix.append(words[0])
            else:
                break
        return ' '.join(prefix) if prefix else titles[0]

    def _event_time_label(event):
        if event.start_time and event.end_time:
            return f"{event.start_time.strftime('%H:%M')}~{event.end_time.strftime('%H:%M')}"
        return ''

    academic_events_list = []
    for event in events:
        if event.event_type == ScheduleEvent.EVENT_TYPE_ACADEMIC and event.days_of_week:
            academic_events_list.append(event)
            continue

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
        if event.start_date:
            cal_event['start'] = event.start_date.isoformat()
            cal_event['extendedProps']['startDate'] = event.start_date.strftime('%Y.%m.%d %H:%M')
        if event.end_date:
            cal_event['end'] = event.end_date.isoformat()
            cal_event['extendedProps']['endDate'] = event.end_date.strftime('%Y.%m.%d %H:%M')
        else:
            cal_event['extendedProps']['endDate'] = ""
        calendar_events.append(cal_event)

    def _first_word(title):
        return title.split(' ', 1)[0] if title else title

    def _format_grouped_times(times):
        am_parts, pm_parts = [], []
        for t in times:
            h, m = t.hour, t.minute
            if h < 12:
                hh = h if h != 0 else 12
                am_parts.append(f"{hh}:{m:02d}")
            else:
                hh = h - 12 if h > 12 else 12
                pm_parts.append(f"{hh}:{m:02d}")
        parts = []
        if am_parts:
            parts.append('오전 ' + '/'.join(am_parts))
        if pm_parts:
            parts.append('오후 ' + '/'.join(pm_parts))
        return ' '.join(parts)

    # 정규수업은 "같은 요일 + 같은 이름(첫 단어)"을 기준으로 묶는다 (시간은 서로 달라도 됨).
    # 요일마다 묶이는 조합이 다를 수 있으므로, 요일별로 (이름, 수업 id 조합) 시그니처를 구하고
    # 동일한 시그니처를 가진 요일들을 다시 묶어 하나의 캘린더 이벤트로 만든다.
    weekday_events = {}
    for event in academic_events_list:
        for d in (int(x) for x in event.days_of_week.split(',')):
            weekday_events.setdefault(d, []).append(event)

    combo_days = {}   # (name_key, frozenset(event_id, ...)) -> set(weekday, ...)
    combo_events = {}  # frozenset(event_id, ...) -> [event, ...]
    for d, evs in weekday_events.items():
        by_name = {}
        for e in evs:
            by_name.setdefault(_first_word(e.title), []).append(e)
        for name_key, group in by_name.items():
            ids = frozenset(e.id for e in group)
            combo_days.setdefault((name_key, ids), set()).add(d)
            combo_events[ids] = group

    color = SCHEDULE_EVENT_COLORS.get(ScheduleEvent.EVENT_TYPE_ACADEMIC, '#3b82f6')
    for (name_key, ids), days_set in combo_days.items():
        group_events = sorted(combo_events[ids], key=lambda e: (e.start_time is None, e.start_time, e.title))
        days_sorted = sorted(days_set)
        days_str = ', '.join(day_names[d] for d in days_sorted)
        titles = [e.title for e in group_events]
        is_group = len(group_events) > 1
        display_title = _common_title_prefix(titles) if is_group else titles[0]
        distinct_times = sorted({e.start_time for e in group_events if e.start_time})
        time_label = _format_grouped_times(distinct_times)
        end_time = max((e.end_time for e in group_events if e.end_time), default=None)
        earliest_start = distinct_times[0] if distinct_times else None
        time_str = f" {time_label}" if time_label else ''

        cal_event = {
            'id': f"academic-group-{'-'.join(str(i) for i in sorted(ids))}",
            'title': display_title,
            'backgroundColor': color,
            'borderColor': color,
            'textColor': '#ffffff',
            'daysOfWeek': days_sorted,
            'extendedProps': {
                'description': '' if is_group else (group_events[0].description or ''),
                'eventType': ScheduleEvent.EVENT_TYPE_ACADEMIC,
                'eventTypeLabel': group_events[0].get_event_type_display(),
                'imageUrl': '' if is_group else (group_events[0].image.url if group_events[0].image else ''),
                'externalUrl': '' if is_group else (group_events[0].external_url or ''),
                'attachments': [] if is_group else [
                    {'name': a.file.name.split('/')[-1], 'url': a.file.url}
                    for a in group_events[0].attachments.all()
                ],
                'startDate': f"매주 {days_str}요일{time_str}",
                'endDate': '',
                'isGroup': is_group,
                'timeLabel': time_label,
                'groupedItems': [{'title': e.title, 'time': _event_time_label(e)} for e in group_events],
            },
        }
        if not is_group:
            cal_event['id'] = group_events[0].id
        if earliest_start:
            cal_event['startTime'] = earliest_start.strftime('%H:%M:%S')
        if end_time:
            cal_event['endTime'] = end_time.strftime('%H:%M:%S')
        calendar_events.append(cal_event)

    for event in events:
        if getattr(event, 'days_of_week', None):
            days = [int(d) for d in event.days_of_week.split(',')]
            days_str = ', '.join([day_names[d] for d in days])
            event.parsed_days_str = days_str

    # 휴원/공휴일 날짜 목록 (정규수업 숨김 + 달력 셀 빨간 배경 처리용)
    holiday_dates = set()
    for event in events.filter(event_type=ScheduleEvent.EVENT_TYPE_HOLIDAY):
        if not event.start_date:
            continue
        start_d = timezone.localtime(event.start_date).date()
        end_d = timezone.localtime(event.end_date).date() if event.end_date else start_d
        cur = start_d
        while cur <= end_d:
            holiday_dates.add(cur.isoformat())
            cur += timedelta(days=1)

    context = {
        'calendar_events_json': calendar_events,
        'holiday_dates_json': sorted(holiday_dates),
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
    
    qs = CertInfo.objects.filter(name__icontains=q)[:10] if q and q != ' ' else CertInfo.objects.all().order_by('name')[:30]
    results = [{'id': c.id, 'name': c.name, 'issuer': c.issuer, 'grade_info': c.grade_info or []} for c in qs]
    return JsonResponse({'certinfos': results})

@login_required
def search_competition_types(request):
    """대회종류 자동완성을 위한 API"""
    q = request.GET.get('q', '').strip()
    qs = CompetitionType.objects.filter(name__icontains=q).order_by('order', 'name')[:20] if q and q != ' ' else CompetitionType.objects.all().order_by('order', 'name')[:30]
    results = [
        {'id': c.id, 'name': c.name, 'organization': c.organization}
        for c in qs
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
    
    users = User.objects.all().select_related('profile').prefetch_related(
        'child_links__child__profile', 'parent_links__parent__profile',
    ).order_by('-date_joined')
    
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
        
    is_parent_type = profile.user_type in ('parent', 'medulab_parent')
    parent_link = None
    if not is_parent_type:
        parent_link = ParentChildLink.objects.filter(child=target_user).select_related('parent__profile').first()

    child_links = list(ParentChildLink.objects.filter(parent=target_user).select_related('child__profile')) if is_parent_type else []

    # 가입 시 입력한 자녀정보(children_info)와 실제 연결된 계정(ParentChildLink)을
    # 이름 기준으로 최대한 매칭해서 하나의 표로 보여주기 위한 가공
    children_info = profile.children_info or [] if is_parent_type else []
    matched_link_ids = set()
    children_rows = []
    for child in children_info:
        match = None
        child_name = (child.get('name') or '').strip()
        if child_name:
            for link in child_links:
                if link.id in matched_link_ids:
                    continue
                real_name = (link.child.profile.real_name or link.child.username or '').strip()
                if real_name and real_name == child_name:
                    match = link
                    matched_link_ids.add(link.id)
                    break
        children_rows.append({'info': child, 'link': match})
    extra_links = [l for l in child_links if l.id not in matched_link_ids]

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'target_user': target_user,
        'title': '회원 정보 수정',
        'child_links': child_links,
        'children_rows': children_rows,
        'extra_links': extra_links,
        'is_parent_type': is_parent_type,
        'parent_link': parent_link,
    }
    return render(request, 'arcade/admin/member_form.html', context)


@login_required
@user_passes_test(staff_check)
@require_POST
def member_link_child(request, user_id):
    """학부모 계정에 자녀(학생) 계정 연결"""
    parent_user = get_object_or_404(User, pk=user_id)
    child_id = request.POST.get('child_id')
    next_url = request.POST.get('next') or reverse('member_edit', args=[parent_user.id])
    try:
        child_user = User.objects.get(pk=child_id)
    except (User.DoesNotExist, ValueError, TypeError):
        messages.error(request, '연결할 학생 계정을 찾을 수 없습니다.')
        return redirect(next_url)

    if child_user.id == parent_user.id:
        messages.error(request, '같은 계정을 연결할 수 없습니다.')
        return redirect(next_url)

    _, created = ParentChildLink.objects.get_or_create(
        parent=parent_user, child=child_user, defaults={'linked_by': request.user}
    )
    if created:
        messages.success(request, f'"{child_user.profile.real_name or child_user.username}" 계정을 자녀로 연결했습니다.')
    else:
        messages.info(request, '이미 연결된 계정입니다.')
    return redirect(next_url)


@login_required
@user_passes_test(staff_check)
@require_POST
def member_create_child(request, user_id):
    """검색해도 계정이 없는 자녀를 메듀랩 학생 회원으로 새로 생성한 뒤 바로 연결"""
    parent_user = get_object_or_404(User, pk=user_id)
    username = (request.POST.get('username') or '').strip()
    password = request.POST.get('password') or ''
    child_name = (request.POST.get('child_name') or '').strip()
    child_birth_date_raw = (request.POST.get('child_birth_date') or '').strip()

    if not username or not password:
        messages.error(request, '아이디와 비밀번호를 입력해 주세요.')
        return redirect('member_edit', user_id=parent_user.id)

    if User.objects.filter(username=username).exists():
        messages.error(request, f'아이디 "{username}"는 이미 사용 중입니다.')
        return redirect('member_edit', user_id=parent_user.id)

    import datetime
    birth_date = None
    for fmt in ('%Y.%m.%d', '%Y-%m-%d', '%Y%m%d'):
        try:
            birth_date = datetime.datetime.strptime(child_birth_date_raw, fmt).date()
            break
        except ValueError:
            continue

    child_user = User.objects.create_user(username=username, password=password)
    child_profile, _ = UserProfile.objects.get_or_create(user=child_user)
    child_profile.user_type = 'medulab_member'
    child_profile.is_approved = True
    if child_name:
        child_profile.real_name = child_name
    if birth_date:
        child_profile.birth_date = birth_date
    child_profile.save()

    ParentChildLink.objects.get_or_create(
        parent=parent_user, child=child_user, defaults={'linked_by': request.user}
    )
    messages.success(request, f'"{child_name or username}" 학생 계정을 새로 만들어 연결했습니다.')
    return redirect('member_edit', user_id=parent_user.id)


@login_required
@user_passes_test(staff_check)
@require_POST
def member_unlink_child(request, user_id, link_id):
    """학부모-자녀 연결 해제"""
    parent_user = get_object_or_404(User, pk=user_id)
    link = get_object_or_404(ParentChildLink, pk=link_id, parent=parent_user)
    link.delete()
    messages.success(request, '자녀 연결을 해제했습니다.')
    return redirect('member_edit', user_id=parent_user.id)


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
def member_convert_to_inactive(request, user_id):
    """메듀랩 학생 -> 메듀랩 미수강생 원클릭 전환"""
    target_user = get_object_or_404(User, pk=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=target_user)
    if profile.user_type != 'medulab_member':
        messages.error(request, '메듀랩 학생회원만 미수강생으로 전환할 수 있습니다.')
    else:
        profile.user_type = 'medulab_inactive'
        profile.save(update_fields=['user_type'])
        messages.success(request, f'회원 "{target_user.username}" 을 메듀랩 미수강생으로 전환했습니다.')
    redirect_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('member_list')
    return redirect(redirect_url)


@login_required
@user_passes_test(staff_check)
@require_POST
def member_convert_to_active(request, user_id):
    """메듀랩 미수강생 -> 메듀랩 학생 원클릭 전환(수강생 재전환)"""
    target_user = get_object_or_404(User, pk=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=target_user)
    if profile.user_type != 'medulab_inactive':
        messages.error(request, '메듀랩 미수강생만 수강생으로 전환할 수 있습니다.')
    else:
        profile.user_type = 'medulab_member'
        profile.save(update_fields=['user_type'])
        messages.success(request, f'회원 "{target_user.username}" 을 메듀랩 학생으로 전환했습니다.')
    redirect_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('member_list')
    return redirect(redirect_url)


@login_required
@user_passes_test(staff_check)
@require_POST
def member_delete(request, user_id):
    """회원 삭제"""
    target_user = get_object_or_404(User, pk=user_id)
    next_url = request.POST.get('next') or reverse('member_list')
    if target_user == request.user:
        messages.error(request, '본인 계정은 삭제할 수 없습니다.')
    else:
        username = target_user.username
        target_user.delete()
        messages.success(request, f'회원 "{username}" 계정이 삭제되었습니다.')
    return redirect(next_url)


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


def _handle_attachment_uploads(request, event):
    """첨부 파일 업로드 처리"""
    files = request.FILES.getlist('attachments')
    for f in files:
        if f and f.name:
            ScheduleAttachment.objects.create(event=event, file=f)


def _auto_create_competition_type(event):
    """대회 유형 일정 저장 시 competition_base_name 또는 title로 CompetitionType 자동 추가"""
    if event.event_type != ScheduleEvent.EVENT_TYPE_COMPETITION:
        return
    import re
    base = (event.competition_base_name or '').strip()
    if not base:
        # title에서 "제N회 " 패턴 제거하여 기본명 추출
        base = re.sub(r'^제\d+회\s*', '', (event.title or '')).strip()
    if not base:
        return
    CompetitionType.objects.get_or_create(name=base)


@login_required
@user_passes_test(staff_check)
def schedule_admin_create(request):
    """신규 일정 등록"""
    if request.method == 'POST':
        form = ScheduleEventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save()
            _handle_attachment_uploads(request, event)
            _auto_create_competition_type(event)
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
            _auto_create_competition_type(event)
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
# 수업 관리 (관리자 전용 CRUD + 학생 배정)
# ────────────────────────────────────────────────

# (short_label, filter_query, css_class, group_rank) — group_rank도 display_order 오프셋으로 사용되어
# 공개 수업안내 페이지의 정렬(순수 display_order 기준)이 관리자 화면의 그룹 순서와 일치하도록 함
CLASS_PRESET_GROUPS = [
    ('맞춤성장', 'AI로봇코딩 맞춤성장', 'preset-blue', 0),
    ('집중성장', 'AI로봇코딩 집중성장', 'preset-amber', 1),
    ('융합성장', 'AI로봇코딩 융합성장', 'preset-purple', 2),
]
CLASS_OTHER_GROUP_RANK = 3
CLASS_GROUP_ORDER_STEP = 1000


@login_required
@user_passes_test(staff_check)
def class_admin_list(request):
    """수업 관리 목록 (프리셋별 그룹핑 + 그룹 내 드래그 순서 변경)"""
    classes = SchoolClass.objects.select_related('teacher__profile').prefetch_related('enrollments')
    search = request.GET.get('q', '').strip()
    if search:
        classes = classes.filter(name__icontains=search)
    classes_list = list(classes)

    preset_queries = {full_query for _, full_query, _, _ in CLASS_PRESET_GROUPS}
    is_grouped_view = (not search) or (search in preset_queries)

    groups = []
    if is_grouped_view:
        used_ids = set()
        for short_label, full_query, css_class, rank in CLASS_PRESET_GROUPS:
            if search and search != full_query:
                continue
            group_classes = [c for c in classes_list if short_label in c.name]
            if group_classes:
                groups.append({
                    'label': full_query, 'css_class': css_class, 'rank': rank, 'classes': group_classes,
                })
                used_ids.update(c.id for c in group_classes)
        if not search:
            others = [c for c in classes_list if c.id not in used_ids]
            if others:
                groups.append({
                    'label': '기타', 'css_class': '', 'rank': CLASS_OTHER_GROUP_RANK, 'classes': others,
                })
    elif classes_list:
        groups = [{'label': None, 'css_class': '', 'rank': None, 'classes': classes_list}]
    else:
        groups = []

    context = {
        'groups': groups,
        'search_query': search,
        'reorder_enabled': is_grouped_view,
        'title': '수업 관리',
    }
    return render(request, 'arcade/admin/class_list.html', context)


@login_required
@user_passes_test(staff_check)
@require_POST
def class_admin_reorder(request):
    """수업 목록 드래그 앤 드롭 순서 저장 (그룹 내에서만 순서 변경)"""
    try:
        payload = json.loads(request.body)
        ordered_ids = payload.get('order', [])
        group_rank = int(payload.get('group_rank', 0))
    except (json.JSONDecodeError, AttributeError, TypeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'invalid payload'}, status=400)

    base = group_rank * CLASS_GROUP_ORDER_STEP
    classes_by_id = {c.id: c for c in SchoolClass.objects.filter(pk__in=ordered_ids)}
    updated = []
    for index, class_id in enumerate(ordered_ids):
        school_class = classes_by_id.get(int(class_id))
        new_order = base + index
        if school_class and school_class.display_order != new_order:
            school_class.display_order = new_order
            updated.append(school_class)
    if updated:
        SchoolClass.objects.bulk_update(updated, ['display_order'])
    return JsonResponse({'ok': True})


@login_required
@user_passes_test(staff_check)
def class_admin_create(request):
    """신규 수업 등록"""
    if request.method == 'POST':
        form = SchoolClassForm(request.POST)
        if form.is_valid():
            school_class = form.save()
            messages.success(request, f'수업 "{school_class.name}"이 등록되었습니다.')
            return redirect('class_admin_edit', class_id=school_class.pk)
    else:
        form = SchoolClassForm()
    context = {'form': form, 'title': '신규 수업 등록'}
    return render(request, 'arcade/admin/class_form.html', context)


@login_required
@user_passes_test(staff_check)
def class_admin_edit(request, class_id):
    """수업 수정 + 학생 배정 관리"""
    school_class = get_object_or_404(SchoolClass, pk=class_id)
    if request.method == 'POST':
        form = SchoolClassForm(request.POST, instance=school_class)
        if form.is_valid():
            school_class = form.save()
            messages.success(request, f'수업 "{school_class.name}"이 수정되었습니다.')
            return redirect('class_admin_edit', class_id=school_class.pk)
    else:
        form = SchoolClassForm(instance=school_class)

    enrollments = school_class.enrollments.select_related('student__profile').order_by('-enrolled_at')
    invoices = school_class.invoices.select_related('student__profile').order_by('-due_date', '-created_at')[:20]
    context = {
        'form': form,
        'school_class': school_class,
        'enrollments': enrollments,
        'invoices': invoices,
        'title': '수업 수정',
    }
    return render(request, 'arcade/admin/class_form.html', context)


@login_required
@user_passes_test(staff_check)
@require_POST
def class_admin_copy(request, class_id):
    """수업 복사 등록 (학생 배정/연결 일정은 복사하지 않음)"""
    source = get_object_or_404(SchoolClass, pk=class_id)
    copy = SchoolClass.objects.create(
        name=f'{source.name} 사본',
        teacher=source.teacher,
        days_of_week=source.days_of_week,
        duration_minutes=source.duration_minutes,
        start_time=source.start_time,
        end_time=source.end_time,
        regular_fee=source.regular_fee,
        tuition_fee=source.tuition_fee,
        description=source.description,
        is_active=source.is_active,
        show_on_schedule=False,
    )
    messages.success(request, f'수업 "{source.name}"을 복사하여 "{copy.name}"을 등록했습니다.')
    return redirect('class_admin_edit', class_id=copy.pk)


@login_required
@user_passes_test(staff_check)
@require_POST
def class_admin_delete(request, class_id):
    """수업 삭제"""
    school_class = get_object_or_404(SchoolClass, pk=class_id)
    name = school_class.name
    linked_event = school_class.schedule_event
    try:
        school_class.delete()
        if linked_event:
            linked_event.delete()
        messages.success(request, f'수업 "{name}"이 삭제되었습니다.')
    except DatabaseError:
        messages.error(request, f'수업 "{name}"을 삭제할 수 없습니다.')
    return redirect('class_admin_list')


@login_required
@user_passes_test(staff_check)
@require_POST
def class_enroll_student(request, class_id):
    """수업에 학생 배정 (다중 선택)"""
    school_class = get_object_or_404(SchoolClass, pk=class_id)
    student_ids = request.POST.getlist('student_ids')
    next_url = request.POST.get('next') or reverse('class_admin_edit', args=[school_class.pk])
    added = 0
    for sid in student_ids:
        try:
            student = User.objects.get(pk=sid)
        except (User.DoesNotExist, ValueError):
            continue
        enrollment, created = ClassEnrollment.objects.get_or_create(
            school_class=school_class, student=student, defaults={'is_active': True}
        )
        if created:
            added += 1
        elif not enrollment.is_active:
            enrollment.is_active = True
            enrollment.save(update_fields=['is_active'])
            added += 1
    if added:
        messages.success(request, f'{added}명을 "{school_class.name}" 수업에 배정했습니다.')
    else:
        messages.info(request, '새로 배정된 학생이 없습니다.')
    return redirect(next_url)


@login_required
@user_passes_test(staff_check)
@require_POST
def class_unenroll_student(request, class_id, enrollment_id):
    """수업 배정 해제"""
    school_class = get_object_or_404(SchoolClass, pk=class_id)
    enrollment = get_object_or_404(ClassEnrollment, pk=enrollment_id, school_class=school_class)
    enrollment.delete()
    messages.success(request, '수업 배정을 해제했습니다.')
    return redirect('class_admin_edit', class_id=school_class.pk)


def _month_due_date(today=None):
    """당월 마지막 날을 납부 기한으로 사용"""
    import calendar
    from django.utils import timezone
    today = today or timezone.localdate()
    last_day = calendar.monthrange(today.year, today.month)[1]
    return today.replace(day=last_day)


def generate_invoices_for_class(school_class, due_date=None):
    """해당 수업의 활성 배정 학생 전원에게 당월 청구서 생성 (이미 있으면 건너뜀)
    전월 결석 횟수만큼 회당 단가를 차감해 청구 금액을 계산한다."""
    due_date = due_date or _month_due_date()
    period_start = due_date.replace(day=1)
    prev_month_last_day = period_start - timedelta(days=1)
    prev_month_start = prev_month_last_day.replace(day=1)
    per_session = school_class.per_session_fee

    created = 0
    for enrollment in school_class.enrollments.filter(is_active=True).select_related('student'):
        exists = TuitionInvoice.objects.filter(
            student=enrollment.student, school_class=school_class,
            due_date__year=period_start.year, due_date__month=period_start.month,
        ).exists()
        if exists:
            continue

        prev_month_scheduled_dates = _class_session_dates(school_class, prev_month_start.year, prev_month_start.month)
        absence_count = ClassAttendance.objects.filter(
            enrollment=enrollment, is_present=False,
            date__in=prev_month_scheduled_dates,
        ).count()
        deduction = min(per_session * absence_count, school_class.tuition_fee)
        amount = school_class.tuition_fee - deduction

        TuitionInvoice.objects.create(
            student=enrollment.student, school_class=school_class,
            amount=amount, base_amount=school_class.tuition_fee,
            absence_count=absence_count, absence_deduction=deduction,
            due_date=due_date,
        )
        created += 1
    return created


@login_required
@user_passes_test(staff_check)
@require_POST
def class_admin_generate_invoices(request, class_id):
    """이번 달 청구서 일괄 생성"""
    school_class = get_object_or_404(SchoolClass, pk=class_id)
    due_date = _month_due_date()
    created = generate_invoices_for_class(school_class, due_date=due_date)
    period_label = f'{due_date.year}년 {due_date.month}월'
    if created:
        messages.success(request, f'"{school_class.name}" 수업에 {period_label} 청구서 {created}건을 생성했습니다.')
    else:
        messages.info(request, f'이미 {period_label} 청구서가 모두 생성되어 있습니다.')
    return redirect('class_admin_edit', class_id=school_class.pk)


@login_required
@user_passes_test(staff_check)
@require_POST
def tuition_generate_invoices_all(request):
    """모든 활성 수업을 대상으로, 조회 중인 달의 청구서를 한번에 일괄 생성"""
    import calendar
    import datetime

    try:
        year = int(request.POST.get('year'))
        month = int(request.POST.get('month'))
    except (TypeError, ValueError):
        today = timezone.localdate()
        year, month = today.year, today.month

    last_day = calendar.monthrange(year, month)[1]
    due_date = datetime.date(year, month, last_day)

    total_created = 0
    class_count = 0
    for school_class in SchoolClass.objects.filter(is_active=True):
        created = generate_invoices_for_class(school_class, due_date=due_date)
        if created:
            class_count += 1
        total_created += created

    period_label = f'{year}년 {month}월'
    if total_created:
        messages.success(request, f'{period_label} 청구서 {total_created}건을 생성했습니다. ({class_count}개 수업)')
    else:
        messages.info(request, f'{period_label} 청구서가 이미 모두 생성되어 있거나, 배정된 학생이 없습니다.')

    next_url = request.POST.get('next') or reverse('tuition_admin_dashboard')
    return redirect(next_url)


def _class_session_dates(school_class, year, month):
    """수업의 요일 설정에 따라 해당 월의 실제 수업일 목록을 계산"""
    import calendar
    from datetime import date
    if not school_class.days_of_week:
        return []
    code_to_py_weekday = {'0': 6, '1': 0, '2': 1, '3': 2, '4': 3, '5': 4, '6': 5}
    codes = set(school_class.days_of_week.split(','))
    py_days = {code_to_py_weekday[c] for c in codes if c in code_to_py_weekday}
    num_days = calendar.monthrange(year, month)[1]
    return [date(year, month, day) for day in range(1, num_days + 1) if date(year, month, day).weekday() in py_days]


def _prev_next_month(year, month):
    prev_month = month - 1 or 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    return prev_year, prev_month, next_year, next_month


def _month_all_dates(year, month):
    import calendar
    from datetime import date
    num_days = calendar.monthrange(year, month)[1]
    return [date(year, month, day) for day in range(1, num_days + 1)]


@login_required
@user_passes_test(staff_check)
def class_admin_attendance(request, class_id):
    """수업별 출석부 - 한 달 전체 날짜를 보여주되 정규 수업일은 색으로 구분.
    기본 체크 상태는 학생의 자기 출석체크(Attendance) 기록을 따르고, 결석 체크 시 다음 달 청구서에서 자동 차감됨."""
    from .models import Attendance
    school_class = get_object_or_404(SchoolClass, pk=class_id)
    today = timezone.localdate()
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except ValueError:
        year, month = today.year, today.month

    all_dates = _month_all_dates(year, month)
    scheduled_dates = set(_class_session_dates(school_class, year, month))
    enrollments = list(
        school_class.enrollments.filter(is_active=True).select_related('student__profile')
        .order_by('student__profile__real_name', 'student__username')
    )

    if request.method == 'POST':
        for enrollment in enrollments:
            for d in all_dates:
                field_name = f'att_{enrollment.id}_{d.isoformat()}'
                is_present = field_name in request.POST
                ClassAttendance.objects.update_or_create(
                    enrollment=enrollment, date=d,
                    defaults={'is_present': is_present},
                )
        messages.success(request, '출석 정보를 저장했습니다.')
        return redirect(f"{reverse('class_admin_attendance', args=[school_class.id])}?year={year}&month={month}")

    existing = {
        (r.enrollment_id, r.date): r.is_present
        for r in ClassAttendance.objects.filter(enrollment__school_class=school_class, date__year=year, date__month=month)
    }
    student_ids = [e.student_id for e in enrollments]
    self_checkin_dates = set(
        Attendance.objects.filter(
            user_id__in=student_ids, date__year=year, date__month=month,
            attendance_type__in=[Attendance.TYPE_PRESENT, Attendance.TYPE_MAKEUP],
        ).values_list('user_id', 'date')
    )

    rows = []
    for enrollment in enrollments:
        cells = []
        present_count = 0
        for d in all_dates:
            key = (enrollment.id, d)
            if key in existing:
                is_present = existing[key]
            else:
                is_present = (enrollment.student_id, d) in self_checkin_dates
            if is_present:
                present_count += 1
            cells.append({'date': d, 'is_present': is_present, 'is_scheduled': d in scheduled_dates})
        rows.append({'enrollment': enrollment, 'cells': cells, 'present_count': present_count})

    prev_year, prev_month, next_year, next_month = _prev_next_month(year, month)
    context = {
        'school_class': school_class,
        'all_dates': all_dates,
        'scheduled_dates': scheduled_dates,
        'rows': rows,
        'year': year, 'month': month,
        'prev_year': prev_year, 'prev_month': prev_month,
        'next_year': next_year, 'next_month': next_month,
        'title': f'{school_class.name} 출석부',
    }
    return render(request, 'arcade/admin/class_attendance.html', context)


@login_required
@user_passes_test(staff_check)
def tuition_admin_dashboard(request):
    """납부 관리 - 월별 수납/미납 현황 + 학생별 청구 내역"""
    today = timezone.localdate()
    student_id = request.GET.get('student_id')

    if student_id:
        student = get_object_or_404(User, pk=student_id)
        invoices = TuitionInvoice.objects.filter(student=student).select_related('school_class').order_by('-due_date')
        context = {
            'mode': 'student',
            'student': student,
            'invoices': invoices,
            'title': '납부 관리',
        }
        return render(request, 'arcade/admin/tuition_dashboard.html', context)

    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except ValueError:
        year, month = today.year, today.month

    status_filter = request.GET.get('status', '')
    search = request.GET.get('q', '').strip()

    invoices = TuitionInvoice.objects.filter(
        due_date__year=year, due_date__month=month,
    ).select_related('student__profile', 'school_class').order_by('school_class__name', 'student__profile__real_name')
    if status_filter:
        invoices = invoices.filter(status=status_filter)
    if search:
        invoices = invoices.filter(
            Q(student__profile__real_name__icontains=search) | Q(student__username__icontains=search)
        )

    all_month_invoices = TuitionInvoice.objects.filter(due_date__year=year, due_date__month=month)
    total_amount = all_month_invoices.aggregate(Sum('amount'))['amount__sum'] or 0
    paid_amount = all_month_invoices.filter(status=TuitionInvoice.STATUS_PAID).aggregate(Sum('amount'))['amount__sum'] or 0
    unpaid_amount = all_month_invoices.filter(status=TuitionInvoice.STATUS_UNPAID).aggregate(Sum('amount'))['amount__sum'] or 0
    paid_count = all_month_invoices.filter(status=TuitionInvoice.STATUS_PAID).count()
    unpaid_count = all_month_invoices.filter(status=TuitionInvoice.STATUS_UNPAID).count()

    prev_year, prev_month, next_year, next_month = _prev_next_month(year, month)
    context = {
        'mode': 'month',
        'invoices': invoices,
        'year': year, 'month': month,
        'prev_year': prev_year, 'prev_month': prev_month,
        'next_year': next_year, 'next_month': next_month,
        'status_filter': status_filter,
        'search_query': search,
        'total_amount': total_amount,
        'paid_amount': paid_amount,
        'unpaid_amount': unpaid_amount,
        'paid_count': paid_count,
        'unpaid_count': unpaid_count,
        'title': '납부 관리',
    }
    return render(request, 'arcade/admin/tuition_dashboard.html', context)


@login_required
@user_passes_test(staff_check)
def tuition_invoice_edit(request, invoice_id):
    """청구서 금액/기한/상태를 관리자가 직접 수정"""
    invoice = get_object_or_404(TuitionInvoice.objects.select_related('student__profile', 'school_class'), pk=invoice_id)
    next_url = request.POST.get('next') or request.GET.get('next') or reverse('tuition_admin_dashboard')

    if request.method == 'POST':
        try:
            invoice.amount = int(request.POST.get('amount', '').strip())
        except (TypeError, ValueError):
            messages.error(request, '청구 금액을 올바르게 입력해 주세요.')
            return redirect(request.get_full_path())

        due_date_str = request.POST.get('due_date', '').strip()
        if due_date_str:
            try:
                invoice.due_date = timezone.datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, '납부 기한 형식이 올바르지 않습니다.')
                return redirect(request.get_full_path())

        status = request.POST.get('status', '').strip()
        if status in dict(TuitionInvoice.STATUS_CHOICES):
            if status == TuitionInvoice.STATUS_PAID and invoice.status != TuitionInvoice.STATUS_PAID:
                invoice.paid_at = timezone.now()
            elif status != TuitionInvoice.STATUS_PAID:
                invoice.paid_at = None
            invoice.status = status

        invoice.portone_pay_method = request.POST.get('portone_pay_method', '').strip()
        invoice.save()
        messages.success(request, '청구서를 수정했습니다.')
        return redirect(next_url)

    context = {
        'invoice': invoice,
        'next': next_url,
        'title': '청구서 수정',
    }
    return render(request, 'arcade/admin/tuition_invoice_edit.html', context)


@login_required
@user_passes_test(staff_check)
@require_POST
def tuition_invoice_delete(request, invoice_id):
    """청구서 삭제"""
    invoice = get_object_or_404(TuitionInvoice, pk=invoice_id)
    invoice.delete()
    messages.success(request, '청구서를 삭제했습니다.')
    next_url = request.POST.get('next') or reverse('tuition_admin_dashboard')
    return redirect(next_url)


@login_required
@user_passes_test(staff_check)
@require_POST
def tuition_invoice_bulk_action(request):
    """청구서 여러 건을 한번에 삭제하거나 상태를 일괄 변경"""
    next_url = request.POST.get('next') or reverse('tuition_admin_dashboard')
    ids = request.POST.getlist('invoice_ids')
    if not ids:
        messages.error(request, '선택된 청구서가 없습니다.')
        return redirect(next_url)

    invoices = TuitionInvoice.objects.filter(pk__in=ids)
    bulk_action = request.POST.get('bulk_action')

    if bulk_action == 'delete':
        count = invoices.count()
        invoices.delete()
        messages.success(request, f'청구서 {count}건을 삭제했습니다.')
    elif bulk_action == 'status':
        status = request.POST.get('status')
        if status not in dict(TuitionInvoice.STATUS_CHOICES):
            messages.error(request, '상태 값이 올바르지 않습니다.')
            return redirect(next_url)
        count = 0
        for invoice in invoices:
            if status == TuitionInvoice.STATUS_PAID and invoice.status != TuitionInvoice.STATUS_PAID:
                invoice.paid_at = timezone.now()
            elif status != TuitionInvoice.STATUS_PAID:
                invoice.paid_at = None
            invoice.status = status
            invoice.save(update_fields=['status', 'paid_at'])
            count += 1
        status_label = dict(TuitionInvoice.STATUS_CHOICES).get(status, status)
        messages.success(request, f'청구서 {count}건을 "{status_label}"(으)로 변경했습니다.')
    else:
        messages.error(request, '알 수 없는 작업입니다.')

    return redirect(next_url)


@login_required
@user_passes_test(staff_check)
def tuition_invoice_attendance_detail(request, invoice_id):
    """청구서의 전월 출석 근거를 보여주는 모달 내용 (결석 차감 계산에 쓰인 그대로)"""
    invoice = get_object_or_404(
        TuitionInvoice.objects.select_related('student__profile', 'school_class'), pk=invoice_id
    )
    period_start = invoice.due_date.replace(day=1)
    prev_month_last_day = period_start - timedelta(days=1)
    prev_year, prev_month = prev_month_last_day.year, prev_month_last_day.month

    scheduled_dates = _class_session_dates(invoice.school_class, prev_year, prev_month)
    enrollment = ClassEnrollment.objects.filter(school_class=invoice.school_class, student=invoice.student).first()
    present_map = {}
    if enrollment:
        present_map = {
            r.date: r.is_present
            for r in ClassAttendance.objects.filter(enrollment=enrollment, date__in=scheduled_dates)
        }
    cells = [{'date': d, 'is_present': present_map.get(d, True)} for d in scheduled_dates]

    context = {
        'invoice': invoice,
        'prev_year': prev_year, 'prev_month': prev_month,
        'cells': cells,
    }
    return render(request, 'arcade/admin/_invoice_attendance_modal.html', context)


# ────────────────────────────────────────────────
# 학원비 결제 (포트원 V2)
# ────────────────────────────────────────────────

def _portone_method_label(method_obj):
    """포트원 결제 응답의 method 정보를 사람이 읽기 좋은 한글 라벨로 변환"""
    method_obj = method_obj or {}
    method_type = method_obj.get('type', '') or ''

    if 'Card' in method_type:
        card = method_obj.get('card') or {}
        name = card.get('name') or card.get('publisher') or card.get('issuer') or card.get('company')
        return f'신용카드({name})' if name else '신용카드'

    if 'EasyPay' in method_type:
        provider = method_obj.get('provider') or (method_obj.get('easyPayMethod') or {}).get('provider') or ''
        if 'KAKAO' in str(provider).upper():
            return '카카오페이'
        return f'간편결제({provider})' if provider else '간편결제'

    if 'Transfer' in method_type:
        return '실시간 계좌이체'

    if 'VirtualAccount' in method_type:
        return '가상계좌'

    if 'Mobile' in method_type:
        return '휴대폰 소액결제'

    return method_type or '-'


def _tuition_invoice_access_or_404(request, invoice_id):
    """본인 청구서이거나, 연결된 학부모인 경우에만 접근 허용"""
    invoice = get_object_or_404(TuitionInvoice.objects.select_related('school_class', 'student'), pk=invoice_id)
    if invoice.student_id == request.user.id:
        return invoice
    if ParentChildLink.objects.filter(parent=request.user, child_id=invoice.student_id).exists():
        return invoice
    raise Http404('청구서를 찾을 수 없습니다.')


@login_required
def tuition_checkout(request, invoice_id):
    """학원비 결제 화면 (포트원 결제창 호출)"""
    invoice = _tuition_invoice_access_or_404(request, invoice_id)
    if invoice.status == TuitionInvoice.STATUS_PAID:
        messages.info(request, '이미 완납된 청구서입니다.')
        return redirect('my_report')

    context = {
        'invoice': invoice,
        'portone_store_id': settings.PORTONE_STORE_ID,
        'portone_channel_key_card': settings.PORTONE_CHANNEL_KEY_CARD,
        'portone_channel_key_kakaopay': settings.PORTONE_CHANNEL_KEY_KAKAOPAY,
        'portone_customer_email': invoice.student.email or f'{invoice.student.username}@medulab.kr',
        'portone_customer_phone': re.sub(r'\D', '', invoice.student.profile.phone_number or '') or '01000000000',
        'portone_customer_name': invoice.student.profile.real_name or invoice.student.username,
    }
    return render(request, 'arcade/tuition_checkout.html', context)


@login_required
@require_POST
def tuition_verify_payment(request, invoice_id):
    """결제창 완료 콜백 후 서버가 포트원 API로 실제 결제 상태를 재검증"""
    import requests
    invoice = _tuition_invoice_access_or_404(request, invoice_id)

    if invoice.status == TuitionInvoice.STATUS_PAID:
        return JsonResponse({'ok': True, 'already_paid': True})

    if not settings.PORTONE_API_SECRET:
        return JsonResponse({'ok': False, 'error': '결제 연동이 아직 설정되지 않았습니다.'}, status=503)

    try:
        resp = requests.get(
            f'https://api.portone.io/payments/{invoice.portone_payment_id}',
            headers={'Authorization': f'PortOne {settings.PORTONE_API_SECRET}'},
            timeout=10,
        )
    except requests.RequestException:
        return JsonResponse({'ok': False, 'error': '결제 확인 중 오류가 발생했습니다.'}, status=502)

    if resp.status_code != 200:
        return JsonResponse({'ok': False, 'error': '결제 정보를 확인할 수 없습니다.'}, status=502)

    data = resp.json()
    if data.get('status') != 'PAID':
        return JsonResponse({'ok': False, 'error': '결제가 완료되지 않았습니다.'}, status=400)

    paid_amount = (data.get('amount') or {}).get('total')
    if paid_amount != invoice.amount:
        return JsonResponse({'ok': False, 'error': '결제 금액이 청구 금액과 일치하지 않습니다.'}, status=400)

    invoice.status = TuitionInvoice.STATUS_PAID
    invoice.paid_at = timezone.now()
    invoice.portone_pay_method = _portone_method_label(data.get('method'))
    invoice.save(update_fields=['status', 'paid_at', 'portone_pay_method'])
    return JsonResponse({'ok': True})


@login_required
def tuition_batch_checkout(request):
    """학부모가 연결된 모든 자녀의 미납 학원비를 한 번에 결제"""
    child_ids = ParentChildLink.objects.filter(parent=request.user).values_list('child_id', flat=True)
    invoices = list(
        TuitionInvoice.objects.filter(student_id__in=child_ids, status=TuitionInvoice.STATUS_UNPAID)
        .select_related('school_class', 'student__profile').order_by('due_date')
    )
    if not invoices:
        messages.info(request, '미납된 학원비가 없습니다.')
        return redirect('my_report')

    total_amount = sum(inv.amount for inv in invoices)
    current_ids = {inv.id for inv in invoices}

    batch = None
    for candidate in TuitionBatchPayment.objects.filter(payer=request.user, status=TuitionInvoice.STATUS_UNPAID):
        if set(candidate.invoices.values_list('id', flat=True)) == current_ids:
            batch = candidate
            break
    if not batch:
        batch = TuitionBatchPayment.objects.create(payer=request.user, amount=total_amount)
        batch.invoices.set(invoices)

    context = {
        'batch': batch,
        'invoices': invoices,
        'total_amount': total_amount,
        'portone_store_id': settings.PORTONE_STORE_ID,
        'portone_channel_key_card': settings.PORTONE_CHANNEL_KEY_CARD,
        'portone_channel_key_kakaopay': settings.PORTONE_CHANNEL_KEY_KAKAOPAY,
        'portone_customer_email': request.user.email or f'{request.user.username}@medulab.kr',
        'portone_customer_phone': re.sub(r'\D', '', request.user.profile.phone_number or '') or '01000000000',
        'portone_customer_name': request.user.profile.real_name or request.user.username,
    }
    return render(request, 'arcade/tuition_batch_checkout.html', context)


@login_required
@require_POST
def tuition_batch_verify(request, batch_id):
    """일괄결제 완료 콜백 후 서버가 포트원 API로 실제 결제 상태를 재검증"""
    import requests
    batch = get_object_or_404(TuitionBatchPayment, pk=batch_id, payer=request.user)

    if batch.status == TuitionInvoice.STATUS_PAID:
        return JsonResponse({'ok': True, 'already_paid': True})

    if not settings.PORTONE_API_SECRET:
        return JsonResponse({'ok': False, 'error': '결제 연동이 아직 설정되지 않았습니다.'}, status=503)

    try:
        resp = requests.get(
            f'https://api.portone.io/payments/{batch.portone_payment_id}',
            headers={'Authorization': f'PortOne {settings.PORTONE_API_SECRET}'},
            timeout=10,
        )
    except requests.RequestException:
        return JsonResponse({'ok': False, 'error': '결제 확인 중 오류가 발생했습니다.'}, status=502)

    if resp.status_code != 200:
        return JsonResponse({'ok': False, 'error': '결제 정보를 확인할 수 없습니다.'}, status=502)

    data = resp.json()
    if data.get('status') != 'PAID':
        return JsonResponse({'ok': False, 'error': '결제가 완료되지 않았습니다.'}, status=400)

    paid_amount = (data.get('amount') or {}).get('total')
    if paid_amount != batch.amount:
        return JsonResponse({'ok': False, 'error': '결제 금액이 청구 금액과 일치하지 않습니다.'}, status=400)

    method = _portone_method_label(data.get('method'))
    now = timezone.now()
    batch.status = TuitionInvoice.STATUS_PAID
    batch.paid_at = now
    batch.portone_pay_method = method
    batch.save(update_fields=['status', 'paid_at', 'portone_pay_method'])
    batch.invoices.update(status=TuitionInvoice.STATUS_PAID, paid_at=now, portone_pay_method=method)
    return JsonResponse({'ok': True})


@login_required
def parent_payment_history(request):
    """학부모의 연결된 모든 자녀 납부 내역 (읽기 전용)"""
    if request.user.profile.user_type != 'medulab_parent':
        return redirect('my_report')

    links = ParentChildLink.objects.filter(parent=request.user).select_related('child__profile')
    child_ids = [l.child_id for l in links]
    invoices = TuitionInvoice.objects.filter(student_id__in=child_ids).select_related(
        'school_class', 'student__profile'
    ).order_by('-due_date', 'student__profile__real_name')

    unpaid_total = sum(inv.amount for inv in invoices if inv.status == TuitionInvoice.STATUS_UNPAID)
    paid_total = sum(inv.amount for inv in invoices if inv.status == TuitionInvoice.STATUS_PAID)

    context = {
        'links': links,
        'invoices': invoices,
        'unpaid_total': unpaid_total,
        'paid_total': paid_total,
    }
    return render(request, 'arcade/payment_history.html', context)


def _verify_portone_webhook_signature(request):
    """포트원 웹훅은 Svix 표준 서명 방식을 사용 (id.timestamp.body 를 HMAC-SHA256)"""
    import base64
    import hashlib
    import hmac as hmac_lib

    secret = settings.PORTONE_WEBHOOK_SECRET
    webhook_id = request.headers.get('webhook-id', '')
    timestamp = request.headers.get('webhook-timestamp', '')
    signature_header = request.headers.get('webhook-signature', '')
    if not (webhook_id and timestamp and signature_header):
        return False

    secret_bytes = secret[len('whsec_'):] if secret.startswith('whsec_') else secret
    secret_bytes = base64.b64decode(secret_bytes)
    signed_content = f'{webhook_id}.{timestamp}.{request.body.decode("utf-8")}'
    expected = base64.b64encode(
        hmac_lib.new(secret_bytes, signed_content.encode('utf-8'), hashlib.sha256).digest()
    ).decode('utf-8')

    for part in signature_header.split(' '):
        candidate = part.split(',', 1)[-1]
        if hmac_lib.compare_digest(candidate, expected):
            return True
    return False


@csrf_exempt
@require_POST
def tuition_webhook(request):
    """포트원 웹훅 수신 (브라우저 콜백 유실 대비 이중 확인)"""
    import requests

    if settings.PORTONE_WEBHOOK_SECRET:
        if not _verify_portone_webhook_signature(request):
            return JsonResponse({'ok': False, 'error': 'invalid signature'}, status=400)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False}, status=400)

    payment_id = payload.get('data', {}).get('paymentId')
    if not payment_id:
        return JsonResponse({'ok': True})

    target = None
    is_batch = False
    try:
        target = TuitionInvoice.objects.get(portone_payment_id=payment_id)
    except TuitionInvoice.DoesNotExist:
        try:
            target = TuitionBatchPayment.objects.get(portone_payment_id=payment_id)
            is_batch = True
        except TuitionBatchPayment.DoesNotExist:
            return JsonResponse({'ok': True})

    if target.status == TuitionInvoice.STATUS_PAID or not settings.PORTONE_API_SECRET:
        return JsonResponse({'ok': True})

    try:
        resp = requests.get(
            f'https://api.portone.io/payments/{payment_id}',
            headers={'Authorization': f'PortOne {settings.PORTONE_API_SECRET}'},
            timeout=10,
        )
        data = resp.json()
    except requests.RequestException:
        return JsonResponse({'ok': False}, status=502)

    if data.get('status') == 'PAID' and (data.get('amount') or {}).get('total') == target.amount:
        method = _portone_method_label(data.get('method'))
        now = timezone.now()
        target.status = TuitionInvoice.STATUS_PAID
        target.paid_at = now
        target.portone_pay_method = method
        target.save(update_fields=['status', 'paid_at', 'portone_pay_method'])
        if is_batch:
            target.invoices.update(status=TuitionInvoice.STATUS_PAID, paid_at=now, portone_pay_method=method)

    return JsonResponse({'ok': True})


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


def public_class_list(request):
    """공개 수업 소개 페이지 (전자결제 심사용 상품 등록 요건 포함)"""
    classes = SchoolClass.objects.filter(is_active=True)
    return render(request, 'arcade/public_class_list.html', {'classes': classes})


def terms_of_service(request):
    return render(request, 'arcade/terms_of_service.html')


def privacy_policy(request):
    return render(request, 'arcade/privacy_policy.html')


def refund_policy(request):
    return render(request, 'arcade/refund_policy.html')


def consult_inquiry(request):
    """상담 문의 접수 페이지"""
    from .forms import ConsultInquiryForm

    if request.method == 'POST':
        form = ConsultInquiryForm(request.POST)
        if form.is_valid():
            inquiry = form.save(commit=False)
            if request.user.is_authenticated:
                inquiry.user = request.user
            inquiry.save()
            messages.success(request, '상담 문의가 접수되었습니다. 빠른 시일 내에 연락드리겠습니다.')
            return redirect('consult_inquiry')
    else:
        initial = {}
        if request.user.is_authenticated:
            initial['name'] = request.user.profile.real_name
            initial['phone_number'] = request.user.profile.phone_number
        form = ConsultInquiryForm(initial=initial)

    context = {
        'form': form,
        'academy_phone': getattr(settings, 'ACADEMY_PHONE', ''),
        'academy_phone_mobile': getattr(settings, 'ACADEMY_PHONE_MOBILE', ''),
        'academy_kakao_channel_url': getattr(settings, 'ACADEMY_KAKAO_CHANNEL_URL', ''),
    }
    return render(request, 'arcade/consult_inquiry.html', context)


@login_required
@user_passes_test(staff_check)
def consult_inquiry_admin_list(request):
    """상담 문의 관리자 목록"""
    from .models import ConsultInquiry
    inquiries = ConsultInquiry.objects.select_related('user').order_by('-created_at')
    return render(request, 'arcade/admin/consult_inquiry_list.html', {'inquiries': inquiries})


@login_required
@user_passes_test(staff_check)
@require_POST
def consult_inquiry_toggle_handled(request, pk):
    from .models import ConsultInquiry
    inquiry = get_object_or_404(ConsultInquiry, pk=pk)
    inquiry.is_handled = not inquiry.is_handled
    inquiry.save(update_fields=['is_handled'])
    return redirect('consult_inquiry_admin_list')


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
def request_medulab_parent_upgrade(request):
    """'학부모회원' -> '메듀랩 학부모' 전환 신청 (관리자 승인 대기 상태로 전환)"""
    profile = request.user.profile
    if profile.user_type != 'parent':
        messages.error(request, '학부모회원만 메듀랩 학부모로 전환 신청할 수 있습니다.')
        return redirect('profile')

    if request.method == 'POST':
        form = MedulabParentUpgradeForm(request.POST)
        if form.is_valid():
            profile.address = form.cleaned_data['address']
            profile.children_info = form.cleaned_data['children_info']
            profile.user_type = 'medulab_parent'
            profile.is_approved = False
            profile.approved_at = None
            profile.save()
            messages.success(request, '메듀랩 학부모 전환 신청이 접수되었습니다. 관리자 승인 후 적용됩니다.')
            return redirect('profile')
    else:
        import json
        form = MedulabParentUpgradeForm(initial={
            'address': profile.address,
            'children_info': json.dumps(profile.children_info or []),
        })
    return render(request, 'arcade/medulab_parent_upgrade.html', {'form': form})


def social_signup_redirect(request, provider):
    """가입 화면 타일에서 고른 회원 유형을 세션에 담아 소셜 로그인으로 넘긴다.
    (구글/카카오는 회원유형을 모르므로, 로그인 후 온보딩 화면에서 이 값을 초기 선택값으로 사용)"""
    user_type = request.GET.get('user_type', '')
    if user_type in dict(UserProfile.PUBLIC_TYPE_CHOICES):
        request.session['pending_signup_user_type'] = user_type
    if provider not in ('google', 'kakao'):
        return redirect('signup')
    return redirect(f'{provider}_login')


@login_required
def social_onboarding(request):
    """소셜 로그인 최초 가입자의 추가정보 입력 완료 화면"""
    profile = request.user.profile
    if profile.onboarding_complete:
        return redirect('home')

    if request.method == 'POST':
        form = SocialOnboardingForm(request.POST)
        if form.is_valid():
            user_type = form.cleaned_data['user_type']
            profile.real_name = form.cleaned_data['real_name']
            profile.birth_date = form.cleaned_data['birth_date']
            profile.phone_number = form.cleaned_data['phone_number']
            profile.user_type = user_type
            profile.address = form.cleaned_data.get('address', '')
            profile.children_info = form.cleaned_data.get('children_info') or None
            profile.is_approved = user_type in UserProfile.AUTO_APPROVE_TYPES
            profile.onboarding_complete = True
            profile.save()
            messages.success(request, '추가정보 입력이 완료되었습니다.')
            return redirect('home')
    else:
        pending_user_type = request.session.pop('pending_signup_user_type', None)
        initial = {
            'real_name': profile.real_name,
            'phone_number': profile.phone_number,
            'address': profile.address,
        }
        if profile.birth_date:
            initial['birth_date'] = profile.birth_date.strftime('%Y.%m.%d')
        if pending_user_type:
            initial['user_type'] = pending_user_type
        form = SocialOnboardingForm(initial=initial)
    return render(request, 'arcade/social_onboarding.html', {'form': form})


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

    from allauth.socialaccount.models import SocialAccount
    kakao_linked = SocialAccount.objects.filter(user=user, provider='kakao').exists()

    child_links = ParentChildLink.objects.filter(parent=user).select_related('child__profile')

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
        'kakao_linked': kakao_linked,
        'child_links': child_links,
    }
    return render(request, 'arcade/profile.html', context)

INSTAGRAM_GALLERY_PAGE_SIZE = 40

# 캡션/해시태그 키워드로 게시물을 분류하는 필터 카테고리
# (코드, 라벨, 매칭 키워드 목록) — caption에 키워드가 하나라도 포함되면 해당 카테고리로 분류
INSTAGRAM_GALLERY_CATEGORIES = [
    ('ai', 'AI', ['ai', '인공지능']),
    ('robot', '로봇', ['로봇']),
    ('coding', '코딩', ['코딩', '파이썬', 'python', '스크래치', '엔트리']),
    ('cert', '자격증', ['자격증']),
    ('instructor', '지도사', ['지도사']),
    ('special', '특강', ['특강', '3d펜', '드론', '항공', '실험과학', '창의수학', '생명과학']),
]
INSTAGRAM_GALLERY_CATEGORY_MAP = {code: (label, keywords) for code, label, keywords in INSTAGRAM_GALLERY_CATEGORIES}


def _instagram_gallery_queryset(tag):
    qs = InstagramPost.objects.filter(is_excluded=False)
    info = INSTAGRAM_GALLERY_CATEGORY_MAP.get(tag)
    if info:
        _, keywords = info
        keyword_q = Q()
        for kw in keywords:
            keyword_q |= Q(caption__icontains=kw)
        # 관리자가 이 카테고리로 수동 배정한 게시물은 무조건 포함,
        # 그 외엔 수동 배정이 없는(자동 분류) 게시물 중 키워드가 맞는 것만 포함
        qs = qs.filter(Q(manual_category=tag) | (Q(manual_category='') & keyword_q))
    return qs


def _instagram_gallery_page(page_number, tag=None):
    from django.core.paginator import Paginator

    paginator = Paginator(_instagram_gallery_queryset(tag), INSTAGRAM_GALLERY_PAGE_SIZE)
    page_obj = paginator.get_page(page_number)
    for post in page_obj:
        post.children_json = json.dumps(post.carousel_children) if post.carousel_children else ''
    return page_obj


def instagram_gallery(request):
    """학원 인스타그램 갤러리 - 그래프 API로 동기화한 게시물을 보여줌"""
    from .instagram_sync import sync_posts

    config = InstagramConfig.objects.first()
    if config and config.access_token and config.ig_user_id:
        stale = (not config.last_synced_at) or (timezone.now() - config.last_synced_at > timedelta(minutes=30))
        if stale:
            sync_posts()
            config.refresh_from_db()

    tag = request.GET.get('tag', '').strip()
    if tag not in INSTAGRAM_GALLERY_CATEGORY_MAP:
        tag = ''
    page_obj = _instagram_gallery_page(1, tag)

    categories = [
        {'code': code, 'label': label, 'active': code == tag}
        for code, label, _ in INSTAGRAM_GALLERY_CATEGORIES
    ]

    return render(request, 'arcade/instagram_gallery.html', {
        'posts': page_obj,
        'page_obj': page_obj,
        'config': config,
        'categories': categories,
        'current_tag': tag,
    })


def instagram_gallery_more(request):
    """"더보기" 버튼용 다음 페이지 게시물 부분 렌더링"""
    page_number = request.GET.get('page', '2')
    tag = request.GET.get('tag', '').strip()
    if tag not in INSTAGRAM_GALLERY_CATEGORY_MAP:
        tag = ''
    page_obj = _instagram_gallery_page(page_number, tag)
    html = render(request, 'arcade/_instagram_gallery_items.html', {'posts': page_obj}).content.decode('utf-8')
    return JsonResponse({
        'html': html,
        'has_next': page_obj.has_next(),
        'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
    })


@login_required
@user_passes_test(staff_check)
@require_POST
def instagram_post_set_category(request, media_id):
    """관리자가 게시물의 필터 카테고리를 수동으로 재배정 (빈 값이면 자동 분류로 복귀)"""
    post = get_object_or_404(InstagramPost, media_id=media_id)
    category = request.POST.get('category', '').strip()
    if category and category not in INSTAGRAM_GALLERY_CATEGORY_MAP:
        return JsonResponse({'success': False, 'error': '알 수 없는 카테고리입니다.'}, status=400)
    post.manual_category = category
    post.save(update_fields=['manual_category'])
    label = INSTAGRAM_GALLERY_CATEGORY_MAP[category][0] if category else '자동 분류'
    return JsonResponse({'success': True, 'category': category, 'label': label})


@login_required
@user_passes_test(staff_check)
@require_POST
def instagram_post_toggle_exclude(request, media_id):
    """관리자가 게시물을 학원 갤러리 노출에서 제외/포함 토글 (고정 게시물 등)"""
    post = get_object_or_404(InstagramPost, media_id=media_id)
    post.is_excluded = not post.is_excluded
    post.save(update_fields=['is_excluded'])
    return JsonResponse({'success': True, 'is_excluded': post.is_excluded})


@login_required
@user_passes_test(staff_check)
@require_POST
def instagram_gallery_sync(request):
    """학원 갤러리 화면에서 관리자가 바로 누르는 수동 동기화"""
    from .instagram_sync import sync_posts

    result = sync_posts()
    if result.get('success'):
        messages.success(request, f"인스타그램 동기화 완료: {result.get('count', 0)}건")
    else:
        messages.error(request, f"인스타그램 동기화 실패: {result.get('error')}")
    return redirect('instagram_gallery')


@login_required
@user_passes_test(staff_check)
def instagram_admin_config(request):
    """인스타그램 연동 설정 (액세스 토큰/계정 ID) 관리 + 수동 동기화"""
    from .instagram_sync import sync_posts

    config, _ = InstagramConfig.objects.get_or_create(pk=1)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'save':
            config.app_id = request.POST.get('app_id', '').strip()
            config.app_secret = request.POST.get('app_secret', '').strip()
            config.ig_user_id = request.POST.get('ig_user_id', '').strip()
            new_token = request.POST.get('access_token', '').strip()
            if new_token:
                config.access_token = new_token
                config.token_expires_at = None  # 새 토큰이면 만료일 재계산 필요 → 다음 동기화 때 갱신 시도
            config.save()
            messages.success(request, '인스타그램 연동 설정을 저장했습니다.')
        elif action == 'sync':
            result = sync_posts()
            if result.get('success'):
                messages.success(request, f"동기화 완료: {result.get('count', 0)}건 가져왔습니다.")
            else:
                messages.error(request, f"동기화 실패: {result.get('error')}")
        return redirect('instagram_admin_config')

    context = {
        'config': config,
        'post_count': InstagramPost.objects.count(),
    }
    return render(request, 'arcade/admin/instagram_config.html', context)


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
    return render(request, 'arcade/board_form.html', {'form': form, 'title': '자격취득 글쓰기', 'is_cert_form': True})


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
    return render(request, 'arcade/board_form.html', {'form': form, 'title': '자격취득 수정', 'is_cert_form': True})

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
    return render(request, 'arcade/board_certinfo_form.html', {'form': form, 'title': '자격종류 수정', 'certinfo': certinfo})

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


def api_national_ai_schedule(request):
    """전국민 AI 경진대회(aichallenge4all.or.kr) 전체 대회 일정을 대신 가져와 전달
    (해당 사이트는 CORS를 열어두지 않아 브라우저에서 직접 호출이 막혀 있어 서버에서 대신 조회함)"""
    import requests
    from django.core.cache import cache

    data = cache.get('national_ai_schedule')
    if data is None:
        try:
            resp = requests.get('https://aichallenge4all.or.kr/api/competition-schedule', timeout=8)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError):
            return JsonResponse({'success': False, 'error': '전국민 AI 경진대회 사이트에서 일정을 가져오지 못했습니다. 잠시 후 다시 시도해 주세요.'}, status=502)
        cache.set('national_ai_schedule', data, 60 * 15)

    return JsonResponse({'success': True, 'items': data.get('items', [])})

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


def _build_report_context(user):
    """마이 리포트 통계 집계. 본인 조회(my_report)와 학부모의 자녀 조회(child_report)가 공유."""
    from django.utils import timezone
    from datetime import timedelta
    from typing_practice.models import TypingScore
    from courses.models import UserProgress
    from .models import Attendance, UserBadge
    from django.db.models import Max, Avg
    from django.db.models.functions import TruncDate

    profile = user.profile
    today = timezone.localdate()

    # 1. 오늘의 타자 성과 집계
    today_scores = TypingScore.objects.filter(user=user, created_at__date=today)
    typing_count = today_scores.count()
    max_speed = today_scores.aggregate(Max('speed'))['speed__max'] or 0
    avg_accuracy = today_scores.aggregate(Avg('accuracy'))['accuracy__avg'] or 0.0
    avg_accuracy = round(avg_accuracy, 1)

    # 2. 오늘의 코딩 학습 성과 집계
    today_progress_qs = UserProgress.objects.filter(
        user=user, completed=True, updated_at__date=today
    ).select_related('item__chapter__program')
    coding_count = today_progress_qs.count()

    # 3. 출석 체크 집계 (이번 달)
    current_year = today.year
    current_month = today.month
    attendances = Attendance.objects.filter(user=user, date__year=current_year, date__month=current_month)
    attendance_dates = [att.date.day for att in attendances]
    present_days = [att.date.day for att in attendances if att.attendance_type == Attendance.TYPE_PRESENT]
    makeup_days = [att.date.day for att in attendances if att.attendance_type == Attendance.TYPE_MAKEUP]
    access_days = [att.date.day for att in attendances if att.attendance_type == Attendance.TYPE_ACCESS]
    today_attendance = Attendance.objects.filter(user=user, date=today).first()
    has_attended_today = today_attendance is not None
    today_attendance_type_display = today_attendance.get_attendance_type_display() if today_attendance else ''

    # 3-1. 수강 중인 수업 안내 + 달력에 표시할 수업일/공휴일 계산
    enrolled_classes = list(
        ClassEnrollment.objects.filter(student=user, is_active=True)
        .select_related('school_class').order_by('school_class__name')
    )
    class_scheduled_days = set()
    for enrollment in enrolled_classes:
        for d in _class_session_dates(enrollment.school_class, current_year, current_month):
            class_scheduled_days.add(d.day)

    holiday_days_labels = {}
    holiday_events = ScheduleEvent.objects.filter(
        event_type=ScheduleEvent.EVENT_TYPE_HOLIDAY, is_active=True,
    )
    for event in holiday_events:
        if not event.start_date:
            continue
        start_d = timezone.localtime(event.start_date).date()
        end_d = timezone.localtime(event.end_date).date() if event.end_date else start_d
        cur = start_d
        while cur <= end_d:
            if cur.year == current_year and cur.month == current_month:
                holiday_days_labels[cur.day] = event.title
            cur += timedelta(days=1)

    import calendar as _cal
    num_days_in_month = _cal.monthrange(current_year, current_month)[1]
    sunday_days = {day for day in range(1, num_days_in_month + 1) if _cal.weekday(current_year, current_month, day) == 6}
    holiday_days = sunday_days | set(holiday_days_labels.keys())

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
                TypingScore.objects.filter(user=user, practice_type=ptype, language=lang)
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
    last_score = TypingScore.objects.filter(user=user).order_by('-created_at').first()
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
    from .models import Certification, Award, ExamRegistration
    my_certs = []
    my_awards = []
    real_name = profile.real_name if profile.real_name else None
    if real_name:
        my_certs = list(Certification.objects.filter(student_name=real_name).select_related('cert_info').order_by('-date_acquired'))
        my_awards = list(Award.objects.filter(student_name=real_name).select_related('competition_type').order_by('-date_awarded'))

    # 7-1. 대회/자격 접수 이력
    my_exam_registrations = list(
        ExamRegistration.objects.filter(user=user).order_by('-exam_date', '-created_at')[:30]
    )

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

    unpaid_invoices = TuitionInvoice.objects.filter(
        student=user, status=TuitionInvoice.STATUS_UNPAID
    ).select_related('school_class').order_by('due_date')

    context = {
        'today': today,
        'unpaid_invoices': unpaid_invoices,
        'typing_count': typing_count,
        'max_speed': max_speed,
        'avg_accuracy': avg_accuracy,
        'coding_count': coding_count,
        'today_progress_list': today_progress_qs,
        'has_attended_today': has_attended_today,
        'today_attendance_type_display': today_attendance_type_display,
        'attendance_dates': attendance_dates,
        'present_days': present_days,
        'makeup_days': makeup_days,
        'access_days': access_days,
        'enrolled_classes': enrolled_classes,
        'class_scheduled_days': class_scheduled_days,
        'holiday_days': holiday_days,
        'holiday_days_labels': holiday_days_labels,
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
        'my_exam_registrations': my_exam_registrations,
    }
    return context


def _render_staff_student_dashboard(request):
    """관리자(직원)용 메듀랩 학생회원 현황 대시보드 (요약 통계 + 학생 목록)"""
    from django.utils import timezone
    from .models import Attendance, Certification, Award, ExamRegistration

    today = timezone.localdate()
    current_year, current_month = today.year, today.month

    from .models import ParentChildLink

    students = list(
        User.objects.filter(profile__user_type='medulab_member')
        .select_related('profile')
        .prefetch_related('parent_links__parent__profile')
        .order_by('profile__real_name', 'username')
    )
    student_ids = [s.id for s in students]

    today_attended_ids = set(
        Attendance.objects.filter(user_id__in=student_ids, date=today).values_list('user_id', flat=True)
    )
    month_attendance_counts = {}
    for row in (
        Attendance.objects.filter(user_id__in=student_ids, date__year=current_year, date__month=current_month)
        .values('user_id')
        .annotate(cnt=Count('id'))
    ):
        month_attendance_counts[row['user_id']] = row['cnt']

    # 오늘 요일에 배정된 활성 수업이 있는 학생 = 오늘 출석해야 할 학생
    code_for_py_weekday = {0: '1', 1: '2', 2: '3', 3: '4', 4: '5', 5: '6', 6: '0'}
    today_code = code_for_py_weekday[today.weekday()]
    today_scheduled_ids = set()
    today_class_info = {}  # student_id -> (start_time, class_name) — 여러 수업이면 가장 이른 시간
    for enrollment in (
        ClassEnrollment.objects.filter(student_id__in=student_ids, is_active=True)
        .select_related('school_class')
    ):
        codes = enrollment.school_class.days_of_week.split(',') if enrollment.school_class.days_of_week else []
        if today_code in codes:
            sc = enrollment.school_class
            today_scheduled_ids.add(enrollment.student_id)
            existing = today_class_info.get(enrollment.student_id)
            if existing is None or (sc.start_time and sc.start_time < existing[0]):
                today_class_info[enrollment.student_id] = (sc.start_time, sc.name)

    today_classes = list(
        SchoolClass.objects.filter(is_active=True)
        .order_by('start_time', 'name')
    )
    today_classes = [c for c in today_classes if today_code in (c.days_of_week.split(',') if c.days_of_week else [])]

    for s in students:
        s.attended_today = s.id in today_attended_ids
        s.month_attendance_count = month_attendance_counts.get(s.id, 0)
        s.scheduled_today = s.id in today_scheduled_ids
        info = today_class_info.get(s.id)
        s.today_class_name = info[1] if info else ''
        s.today_class_time = info[0] if info else None
        s.parent_link = s.parent_links.all()[0] if s.parent_links.all() else None

    # 수업시간 오름차순(수업 없는 학생은 뒤로) → 이름 오름차순
    students.sort(key=lambda s: (
        s.today_class_time is None,
        s.today_class_time,
        s.profile.real_name or s.username,
    ))

    total_students = len(students)
    today_attended_count = len(today_attended_ids)
    today_scheduled_count = len(today_scheduled_ids)
    pending_approval_count = UserProfile.objects.filter(
        user_type__in=UserProfile.FULL_ACCESS_TYPES, is_approved=False
    ).count()
    all_certs = Certification.objects.select_related('cert_info').order_by('-date_acquired', '-created_at')
    all_awards = Award.objects.select_related('competition_type').order_by('-date_awarded', '-created_at')
    upcoming_exams = (
        ExamRegistration.objects.filter(exam_date__gte=today)
        .select_related('user__profile', 'competition_type', 'cert_info')
        .order_by('exam_date', 'exam_time', '-created_at')
    )

    cert_count_total = all_certs.count()
    award_count_total = all_awards.count()
    upcoming_exam_count = upcoming_exams.count()

    context = {
        'total_students': total_students,
        'today_attended_count': today_attended_count,
        'today_scheduled_count': today_scheduled_count,
        'pending_approval_count': pending_approval_count,
        'cert_count_total': cert_count_total,
        'award_count_total': award_count_total,
        'all_certs': all_certs,
        'all_awards': all_awards,
        'upcoming_exams': upcoming_exams,
        'upcoming_exam_count': upcoming_exam_count,
        'students': students,
        'current_month': current_month,
        'today_classes': today_classes,
    }
    return render(request, 'arcade/admin/staff_student_dashboard.html', context)


@login_required
@user_passes_test(staff_check)
def admin_student_report(request, student_id):
    """관리자가 특정 메듀랩 학생회원의 마이 리포트를 열람"""
    student = get_object_or_404(User, pk=student_id)
    context = _build_report_context(student)
    context['viewing_as_parent'] = True
    context['viewing_as_admin'] = True
    return render(request, 'arcade/my_report.html', context)


@login_required
def my_report(request):
    from .models import ParentChildLink

    user = request.user
    profile = user.profile

    # 관리자(직원) 계정은 본인 통계 대신 메듀랩 학생회원 전체 현황 대시보드를 보여줌
    if user.is_staff:
        return _render_staff_student_dashboard(request)

    # 메듀랩 계열이 아닌 회원(학생/학부모/일반/강사회원)은 아직 정식 학습 데이터가 없으므로
    # 프로그램 안내 + 상담문의 랜딩을 보여줌
    if profile.user_type in ('student', 'parent', 'general', 'teacher'):
        return render(request, 'arcade/parent_landing.html', {
            'academy_phone': getattr(settings, 'ACADEMY_PHONE', ''),
            'academy_kakao_channel_url': getattr(settings, 'ACADEMY_KAKAO_CHANNEL_URL', ''),
        })

    # 메듀랩 학부모는 자기 자신의 학습 통계가 의미 없으므로 연결된 자녀 리포트로 안내
    # (선택 화면 없이 바로 첫 번째 자녀 리포트로 이동, 자녀가 여럿이면 리포트 내 전환 버튼으로 이동)
    if profile.user_type == 'medulab_parent':
        child_links = list(ParentChildLink.objects.filter(parent=user).select_related('child__profile'))
        if child_links:
            return redirect('child_report', child_id=child_links[0].child_id)
        return render(request, 'arcade/parent_report_gate.html', {'child_links': child_links})

    # 정보 수정 POST 처리
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=profile, user=user)
        if form.is_valid():
            form.save()
            messages.success(request, '회원 정보가 성공적으로 수정되었습니다.')
            return redirect('my_report')
    else:
        form = UserProfileUpdateForm(instance=profile, user=user)

    context = _build_report_context(user)
    context['form'] = form
    context['viewing_as_parent'] = False
    return render(request, 'arcade/my_report.html', context)


@login_required
def child_report(request, child_id):
    """학부모가 연결된 자녀의 마이 리포트를 열람"""
    from .models import ParentChildLink
    link = get_object_or_404(ParentChildLink, parent=request.user, child_id=child_id)
    all_links = ParentChildLink.objects.filter(parent=request.user).select_related('child__profile')
    context = _build_report_context(link.child)
    context['viewing_as_parent'] = True
    context['viewed_child_id'] = link.child_id
    context['sibling_links'] = all_links

    # 자녀가 여럿이어도 매번 들어가지 않도록, 연결된 모든 자녀의 미납 학원비를 한 곳에서 확인
    all_child_ids = [l.child_id for l in all_links]
    context['all_children_unpaid_invoices'] = TuitionInvoice.objects.filter(
        student_id__in=all_child_ids, status=TuitionInvoice.STATUS_UNPAID
    ).select_related('school_class', 'student__profile').order_by('due_date')

    return render(request, 'arcade/my_report.html', context)


def _haversine_distance_m(lat1, lon1, lat2, lon2):
    """두 GPS 좌표 사이의 거리(미터)를 계산"""
    import math
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _is_at_academy(lat, lng):
    """학생이 보낸 GPS 좌표가 학원 반경 이내인지 판정 (좌표 미설정/미전송 시 항상 False)"""
    if not (settings.ACADEMY_LATITUDE and settings.ACADEMY_LONGITUDE):
        return False
    if lat is None or lng is None:
        return False
    try:
        distance = _haversine_distance_m(
            float(lat), float(lng),
            float(settings.ACADEMY_LATITUDE), float(settings.ACADEMY_LONGITUDE),
        )
    except (TypeError, ValueError):
        return False
    return distance <= settings.ACADEMY_GEOFENCE_RADIUS_M


def _user_has_class_today(user, today):
    """오늘 요일에 배정된 활성 수업이 하나라도 있으면 정규 수업일로 판단"""
    code_for_py_weekday = {0: '1', 1: '2', 2: '3', 3: '4', 4: '5', 5: '6', 6: '0'}
    code = code_for_py_weekday[today.weekday()]
    for enrollment in ClassEnrollment.objects.filter(student=user, is_active=True).select_related('school_class'):
        codes = enrollment.school_class.days_of_week.split(',') if enrollment.school_class.days_of_week else []
        if code in codes:
            return True
    return False


@login_required
@require_POST
def api_submit_attendance(request):
    from django.utils import timezone
    from .models import Attendance

    today = timezone.localdate()
    try:
        payload = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        payload = {}

    if _is_at_academy(payload.get('lat'), payload.get('lng')):
        attendance_type = Attendance.TYPE_PRESENT if _user_has_class_today(request.user, today) else Attendance.TYPE_MAKEUP
    else:
        attendance_type = Attendance.TYPE_ACCESS

    attendance, created = Attendance.objects.get_or_create(
        user=request.user, date=today,
        defaults={'attendance_type': attendance_type},
    )
    if not created and attendance.attendance_type == Attendance.TYPE_ACCESS and attendance_type != Attendance.TYPE_ACCESS:
        attendance.attendance_type = attendance_type
        attendance.save(update_fields=['attendance_type'])

    return JsonResponse({
        'status': 'success',
        'created': created,
        'date': today.strftime('%Y-%m-%d'),
        'attendance_type': attendance.attendance_type,
        'attendance_type_display': attendance.get_attendance_type_display(),
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
    from .models import GalleryRoom, GalleryPoster, GalleryCriteria
    name = request.POST.get('name', '').strip()
    if not name:
        return JsonResponse({'ok': False, 'error': '방 이름을 입력해주세요.'})
    images = request.FILES.getlist('images')
    if not images:
        return JsonResponse({'ok': False, 'error': '포스터 이미지를 하나 이상 업로드해주세요.'})
    vote_duration = max(0, int(request.POST.get('vote_duration', 0)))
    room = GalleryRoom.objects.create(name=name, vote_duration=vote_duration)
    for i, img in enumerate(images):
        title = img.name.rsplit('.', 1)[0]
        GalleryPoster.objects.create(room=room, image=img, title=title, order=i)
    # 평가항목 저장
    criteria_json = request.POST.get('criteria', '[]')
    try:
        criteria_list = json.loads(criteria_json)
        for i, c in enumerate(criteria_list):
            cname = str(c.get('name', '')).strip()
            if cname:
                GalleryCriteria.objects.create(
                    room=room,
                    name=cname,
                    description=str(c.get('description', '')).strip(),
                    max_score=max(1, min(100, int(c.get('max_score', 20)))),
                    order=i,
                )
    except Exception:
        pass
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
    from django.utils import timezone
    action = request.POST.get('action')
    poster_count = room.posters.count()
    if action == 'start':
        if room.status != 'waiting':
            return JsonResponse({'ok': False, 'error': '이미 시작됐습니다.'})
        room.status = 'voting'
        room.current_index = 0
        room.poster_started_at = timezone.now()
    elif action == 'next':
        if room.status != 'voting':
            return JsonResponse({'ok': False, 'error': '진행 중이 아닙니다.'})
        next_idx = room.current_index + 1
        if next_idx >= poster_count:
            room.status = 'done'
        else:
            room.current_index = next_idx
            room.poster_started_at = timezone.now()
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
    from .models import GalleryRoom, GalleryVote, GalleryCriteria
    from django.db.models import Avg, Count
    room_id = request.GET.get('room_id')
    try:
        room = GalleryRoom.objects.get(id=room_id)
    except GalleryRoom.DoesNotExist:
        return JsonResponse({'ok': False, 'error': '방 없음'})

    session_key = request.session.session_key or ''
    criteria_objs = list(room.criteria.all())
    has_criteria = len(criteria_objs) > 0

    poster_data = None
    my_score = 0
    my_criteria_scores = {}

    if room.status == 'voting' and room.current_index >= 0:
        posters = list(room.posters.all())
        if room.current_index < len(posters):
            poster = posters[room.current_index]

            if has_criteria:
                my_votes = {v.criteria_id: v.score for v in GalleryVote.objects.filter(
                    poster=poster, voter_session=session_key, criteria__isnull=False
                )}
                my_criteria_scores = {str(k): v for k, v in my_votes.items()}
                voted_all = len(my_votes) == len(criteria_objs)
                vote_count = GalleryVote.objects.filter(
                    poster=poster, criteria=criteria_objs[0]
                ).aggregate(count=Count('id'))['count'] if criteria_objs else 0
                # 평균 총점 계산
                total_max = sum(c.max_score for c in criteria_objs)
                avg_scores = []
                for c in criteria_objs:
                    agg = GalleryVote.objects.filter(poster=poster, criteria=c).aggregate(avg=Avg('score'))
                    avg_star = agg['avg'] or 0
                    avg_scores.append({'id': c.id, 'avg_star': round(avg_star, 1)})
                avg_total = round(sum(
                    (a['avg_star'] / 5) * criteria_objs[i].max_score
                    for i, a in enumerate(avg_scores)
                ), 1) if avg_scores else 0
            else:
                my_vote_obj = GalleryVote.objects.filter(
                    poster=poster, voter_session=session_key, criteria__isnull=True
                ).first()
                my_score = my_vote_obj.score if my_vote_obj else 0
                voted_all = my_score > 0
                agg = poster.votes.filter(criteria__isnull=True).aggregate(avg=Avg('score'), count=Count('id'))
                vote_count = agg['count'] or 0
                avg_total = round(agg['avg'] or 0, 1)

            poster_data = {
                'id': poster.id,
                'title': poster.title,
                'image_url': poster.image.url,
                'vote_count': vote_count,
                'avg_score': avg_total,
                'index': room.current_index,
                'total': len(posters),
            }

    results = None
    if room.status == 'done':
        results = []
        for poster in room.posters.all():
            if has_criteria:
                vote_count = GalleryVote.objects.filter(
                    poster=poster, criteria=criteria_objs[0]
                ).aggregate(count=Count('id'))['count'] if criteria_objs else 0
                total = 0.0
                for c in criteria_objs:
                    avg = GalleryVote.objects.filter(poster=poster, criteria=c).aggregate(avg=Avg('score'))['avg'] or 0
                    total += (avg / 5) * c.max_score
            else:
                agg = poster.votes.filter(criteria__isnull=True).aggregate(avg=Avg('score'), count=Count('id'))
                vote_count = agg['count'] or 0
                total = round(agg['avg'] or 0, 1)
            results.append({
                'id': poster.id,
                'title': poster.title,
                'image_url': poster.image.url,
                'vote_count': vote_count,
                'avg_score': round(total, 1),
                'order': poster.order,
            })
        results.sort(key=lambda x: (-x['avg_score'], -x['vote_count']))

    criteria_info = [
        {'id': c.id, 'name': c.name, 'description': c.description, 'max_score': c.max_score}
        for c in criteria_objs
    ]
    max_total_score = sum(c.max_score for c in criteria_objs) if criteria_objs else 5

    # 타이머 정보
    from django.utils import timezone
    poster_started_ts = None
    if room.poster_started_at:
        poster_started_ts = room.poster_started_at.timestamp()

    return JsonResponse({
        'ok': True,
        'status': room.status,
        'current_index': room.current_index,
        'poster': poster_data,
        'my_score': my_score,
        'my_criteria_scores': my_criteria_scores,
        'criteria': criteria_info,
        'results': results,
        'vote_duration': room.vote_duration,
        'poster_started_ts': poster_started_ts,
        'has_criteria': has_criteria,
        'max_total_score': max_total_score,
    })


@require_POST
def api_gallery_vote(request):
    from .models import GalleryPoster, GalleryVote, GalleryCriteria
    from django.db.models import Avg, Count
    data = json.loads(request.body)
    poster_id = data.get('poster_id')
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

    criteria_objs = list(poster.room.criteria.all())
    has_criteria = len(criteria_objs) > 0

    if has_criteria:
        # 평가항목별 별점 저장
        criteria_scores = data.get('criteria_scores', {})
        saved = 0
        for c in criteria_objs:
            raw = criteria_scores.get(str(c.id))
            if raw is None:
                continue
            score = max(1, min(5, int(raw)))
            GalleryVote.objects.update_or_create(
                poster=poster, voter_session=session_key, criteria=c,
                defaults={'voter_name': voter_name, 'score': score}
            )
            saved += 1
        vote_count = GalleryVote.objects.filter(
            poster=poster, criteria=criteria_objs[0]
        ).aggregate(count=Count('id'))['count'] if criteria_objs else 0
        total_max = sum(c.max_score for c in criteria_objs)
        avg_total = 0.0
        for c in criteria_objs:
            avg = GalleryVote.objects.filter(poster=poster, criteria=c).aggregate(avg=Avg('score'))['avg'] or 0
            avg_total += (avg / 5) * c.max_score
        return JsonResponse({
            'ok': True, 'vote_count': vote_count, 'avg_score': round(avg_total, 1),
        })
    else:
        score = int(data.get('score', 5))
        if not (1 <= score <= 5):
            score = 5
        GalleryVote.objects.update_or_create(
            poster=poster, voter_session=session_key, criteria=None,
            defaults={'voter_name': voter_name, 'score': score}
        )
        agg = poster.votes.filter(criteria__isnull=True).aggregate(avg=Avg('score'), count=Count('id'))
        return JsonResponse({
            'ok': True, 'vote_count': agg['count'] or 0,
            'avg_score': round(agg['avg'] or 0, 1),
        })


# ═══════════════════════════════════════════════════════════
# 만족도 조사
# ═══════════════════════════════════════════════════════════

SURVEY_QUESTIONS = [
    {'num': 1, 'text': '탄소중립이 무엇인지 이해하는 데 도움이 되었다.'},
    {'num': 2, 'text': 'AI코디니를 활용한 코딩 활동을 이해할 수 있었다.'},
    {'num': 3, 'text': '음성인식을 활용해 불을 켜고 끄는 활동이 흥미로웠다.'},
    {'num': 4, 'text': '생성형 AI를 활용해 발명품 아이디어를 만드는 활동이 도움이 되었다.'},
    {'num': 5, 'text': '내가 생각한 탄소중립 발명품을 직접 설계해 보는 과정이 재미있었다.'},
    {'num': 6, 'text': '수업의 설명과 활동 난이도는 적절했다.'},
    {'num': 7, 'text': '활동 중 어려움이 있을 때 선생님이나 보조강사의 도움을 받을 수 있었다.'},
    {'num': 8, 'text': '직접 작품을 만들고 발표하는 활동이 좋았다.'},
]

CAMP_SESSIONS = [
    {'num': 1, 'title': '탄소중립 이해하기'},
    {'num': 2, 'title': 'AI코디니 기초 익히기'},
    {'num': 3, 'title': '지니야, 불 켜줘! 만들기'},
    {'num': 4, 'title': 'AI로 발명품 아이디어 설계하기'},
    {'num': 5, 'title': '발명품 포스터 발표'},
]

MOTIVATION_OPTIONS = [
    '🤖 AI·코딩이 궁금해서',
    '🌱 환경·탄소중립에 관심이 있어서',
    '🏆 대회·발명에 도전하고 싶어서',
    '👨‍👩‍👧 부모님 권유로',
    '👫 친구와 함께 참여하려고',
    '🏫 학교에서 신청해서',
]

AI_INTEREST_OPTIONS = [
    '생성형 AI·ChatGPT',
    '코딩·프로그래밍',
    '로봇·교구 활동',
    'AI 그림·웹툰 제작',
    'AI 영상·음악 제작',
    '게임·메타버스',
]

SURVEY_CONFIGS = [
    {'title': 'AI그린탄소중립캠프(12일)', 'slug': 'camp-12', 'total_students': 21},
    {'title': 'AI그린탄소중립캠프(13일)', 'slug': 'camp-13', 'total_students': 22},
]


def _get_survey_sessions(survey):
    return survey.sessions_data if survey.sessions_data else CAMP_SESSIONS


def survey_home(request):
    from .models import SatisfactionSurvey
    for cfg in SURVEY_CONFIGS:
        survey, created = SatisfactionSurvey.objects.get_or_create(
            slug=cfg['slug'],
            defaults={
                'title': cfg['title'],
                'expected_count': cfg.get('total_students', 0),
                'sessions_data': CAMP_SESSIONS,
            }
        )
        if not created:
            changed = False
            if survey.expected_count == 0 and cfg.get('total_students'):
                survey.expected_count = cfg['total_students']
                changed = True
            if not survey.sessions_data:
                survey.sessions_data = CAMP_SESSIONS
                changed = True
            if changed:
                survey.save()
    from django.utils import timezone as tz
    today = tz.localdate()
    surveys = SatisfactionSurvey.objects.filter(is_active=True).order_by('id')
    import json as _json
    surveys_data = []
    for s in surveys:
        surveys_data.append({
            'id': s.id, 'title': s.title, 'slug': s.slug,
            'active_date': s.active_date.strftime('%Y-%m-%d') if s.active_date else '',
            'expected_count': s.expected_count,
            'response_count': s.responses.count(),
            'sessions_data': s.sessions_data or CAMP_SESSIONS,
        })
    return render(request, 'arcade/survey_home.html', {
        'surveys': surveys,
        'surveys_json': _json.dumps(surveys_data),
        'ai_interest_options': AI_INTEREST_OPTIONS,
        'today': today,
    })


def survey_detail(request, slug):
    from .models import SatisfactionSurvey, SatisfactionResponse
    from django.utils import timezone as tz
    survey = get_object_or_404(SatisfactionSurvey, slug=slug)
    sessions = _get_survey_sessions(survey)

    if request.user.is_staff:
        responses = list(survey.responses.all().order_by('created_at'))
        total = len(responses)
        total_students = survey.expected_count
        avg_overall = round(sum(r.overall_score for r in responses) / total, 1) if total else 0
        session_avgs = {}
        for s in sessions:
            scores = [r.session_scores.get(str(s['num'])) for r in responses if r.session_scores.get(str(s['num']))]
            session_avgs[s['num']] = round(sum(scores) / len(scores), 1) if scores else 0
        question_avgs = {}
        for q in SURVEY_QUESTIONS:
            scores = [r.session_scores.get(str(q['num'])) for r in responses if r.session_scores.get(str(q['num']))]
            question_avgs[q['num']] = round(sum(scores) / len(scores), 1) if scores else 0
        attend_counts = {}
        for r in responses:
            k = r.attend_again
            attend_counts[k] = attend_counts.get(k, 0) + 1
        recommend_counts = {}
        for r in responses:
            k = r.recommend
            recommend_counts[k] = recommend_counts.get(k, 0) + 1
        fav_counts = {}
        hard_counts = {}
        ai_interest_counts = {}
        motivation_counts = {}
        for r in responses:
            for n in (r.favorite_sessions or []):
                fav_counts[int(n)] = fav_counts.get(int(n), 0) + 1
            for n in (r.hardest_sessions or []):
                hard_counts[int(n)] = hard_counts.get(int(n), 0) + 1
            for opt in (r.ai_interests or []):
                ai_interest_counts[opt] = ai_interest_counts.get(opt, 0) + 1
            for opt in (r.motivations or []):
                motivation_counts[opt] = motivation_counts.get(opt, 0) + 1
        import json as _json
        responses_json = _json.dumps([
            {'overall_score': r.overall_score, 'session_scores': r.session_scores,
             'favorite_sessions': r.favorite_sessions, 'hardest_sessions': r.hardest_sessions,
             'ai_interests': r.ai_interests or [],
             'grade': r.respondent_grade,
             'good_points': r.good_points or '',
             'bad_points': r.bad_points or ''}
            for r in responses
        ])
        sessions_js = _json.dumps([s['num'] for s in sessions])
        session_avgs_json = _json.dumps(session_avgs)
        fav_counts_json = _json.dumps(fav_counts)
        hard_counts_json = _json.dumps(hard_counts)
        ai_interest_counts_json = _json.dumps(ai_interest_counts)
        ai_interest_options_json = _json.dumps(AI_INTEREST_OPTIONS)
        motivation_counts_json = _json.dumps(motivation_counts)
        motivation_options_json = _json.dumps(MOTIVATION_OPTIONS)
        question_avgs_json = _json.dumps(question_avgs)
        questions_js = _json.dumps([q['num'] for q in SURVEY_QUESTIONS])
        return render(request, 'arcade/survey_results.html', {
            'survey': survey, 'responses': responses, 'total': total,
            'total_students': total_students,
            'avg_overall': avg_overall, 'session_avgs': session_avgs,
            'attend_counts': attend_counts, 'recommend_counts': recommend_counts,
            'fav_counts': fav_counts, 'hard_counts': hard_counts,
            'sessions': sessions,
            'ai_interest_options': AI_INTEREST_OPTIONS,
            'ai_interest_counts': ai_interest_counts,
            'responses_json': responses_json, 'sessions_js': sessions_js,
            'session_avgs_json': session_avgs_json,
            'fav_counts_json': fav_counts_json,
            'hard_counts_json': hard_counts_json,
            'ai_interest_counts_json': ai_interest_counts_json,
            'ai_interest_options_json': ai_interest_options_json,
            'motivation_options': MOTIVATION_OPTIONS,
            'motivation_counts_json': motivation_counts_json,
            'motivation_options_json': motivation_options_json,
            'survey_questions': SURVEY_QUESTIONS,
            'question_avgs_json': question_avgs_json,
            'questions_js': questions_js,
        })

    # 학생: 날짜 체크
    today = tz.localdate()
    if survey.active_date and survey.active_date != today:
        return render(request, 'arcade/survey_form.html', {
            'survey': survey, 'not_today': True,
            'active_date': survey.active_date,
        })

    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    already = SatisfactionResponse.objects.filter(survey=survey, session_key=session_key).exists()
    attend_options = [
        {'value': '꼭 참여하고 싶어요', 'label': '🙋 꼭 참여하고 싶어요!'},
        {'value': '기회가 되면 참여하고 싶어요', 'label': '😊 기회가 되면 참여하고 싶어요'},
        {'value': '잘 모르겠어요', 'label': '🤔 잘 모르겠어요'},
        {'value': '참여하고 싶지 않아요', 'label': '😞 참여하고 싶지 않아요'},
    ]
    recommend_options = [
        {'value': '매우 추천해요', 'label': '🌟 매우 추천해요!'},
        {'value': '추천해요', 'label': '👍 추천해요'},
        {'value': '잘 모르겠어요', 'label': '🤔 잘 모르겠어요'},
        {'value': '추천하지 않아요', 'label': '👎 추천하지 않아요'},
    ]
    return render(request, 'arcade/survey_form.html', {
        'survey': survey, 'sessions': sessions, 'already_submitted': already,
        'survey_questions': SURVEY_QUESTIONS,
        'attend_options': attend_options, 'recommend_options': recommend_options,
        'ai_interest_options': AI_INTEREST_OPTIONS,
        'motivation_options': MOTIVATION_OPTIONS,
    })


@require_POST
def api_survey_submit(request, slug):
    from .models import SatisfactionSurvey, SatisfactionResponse
    from django.utils import timezone as tz
    survey = get_object_or_404(SatisfactionSurvey, slug=slug)
    # 날짜 체크
    if survey.active_date and survey.active_date != tz.localdate():
        return JsonResponse({'ok': False, 'error': '오늘은 만족도 조사 날이 아니에요.'})
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    if SatisfactionResponse.objects.filter(survey=survey, session_key=session_key).exists():
        return JsonResponse({'ok': False, 'error': '이미 참여하셨습니다.'})
    data = json.loads(request.body)
    name = str(data.get('name', '')).strip()
    if not name:
        return JsonResponse({'ok': False, 'error': '이름을 입력해주세요.'})
    school = str(data.get('school', '')).strip()
    grade = str(data.get('grade', '')).strip()
    overall_score = int(data.get('overall_score', 0))
    if not (1 <= overall_score <= 5):
        return JsonResponse({'ok': False, 'error': '전체 만족도를 선택해주세요.'})
    motivations = list(data.get('motivations', []))
    motivation_other = str(data.get('motivation_other', '')).strip()
    if motivation_other:
        motivations.append(f'기타: {motivation_other}')
    session_scores = {str(q['num']): int(data.get(f'session_{q["num"]}', 0))
                      for q in SURVEY_QUESTIONS if data.get(f'session_{q["num"]}')}
    SatisfactionResponse.objects.create(
        survey=survey, respondent_name=name, respondent_school=school, respondent_grade=grade,
        motivations=motivations,
        session_key=session_key,
        overall_score=overall_score, session_scores=session_scores,
        favorite_sessions=data.get('favorite_sessions', []),
        hardest_sessions=data.get('hardest_sessions', []),
        attend_again=str(data.get('attend_again', '')),
        recommend=str(data.get('recommend', '')),
        ai_interests=data.get('ai_interests', []),
        good_points=str(data.get('good_points', '')),
        bad_points=str(data.get('bad_points', '')),
    )
    return JsonResponse({'ok': True})


@require_POST
def api_survey_update(request, slug):
    if not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': '권한 없음'}, status=403)
    from .models import SatisfactionSurvey
    survey = get_object_or_404(SatisfactionSurvey, slug=slug)
    data = json.loads(request.body)
    if 'title' in data:
        survey.title = str(data['title']).strip()
    if 'active_date' in data:
        from datetime import date
        try:
            survey.active_date = date.fromisoformat(data['active_date']) if data['active_date'] else None
        except ValueError:
            return JsonResponse({'ok': False, 'error': '날짜 형식 오류'})
    if 'expected_count' in data:
        survey.expected_count = int(data['expected_count'] or 0)
    if 'sessions_data' in data:
        sessions = data['sessions_data']
        if isinstance(sessions, list):
            survey.sessions_data = [{'num': i + 1, 'title': str(s.get('title', '')).strip()}
                                     for i, s in enumerate(sessions) if str(s.get('title', '')).strip()]
    survey.save()
    return JsonResponse({'ok': True})


@require_POST
def api_survey_clone(request, slug):
    if not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': '권한 없음'}, status=403)
    from .models import SatisfactionSurvey
    import re as _re
    source = get_object_or_404(SatisfactionSurvey, slug=slug)
    data = json.loads(request.body)
    title = str(data.get('title', '')).strip()
    if not title:
        return JsonResponse({'ok': False, 'error': '제목을 입력해주세요.'})
    from datetime import date
    active_date = None
    if data.get('active_date'):
        try:
            active_date = date.fromisoformat(data['active_date'])
        except ValueError:
            return JsonResponse({'ok': False, 'error': '날짜 형식 오류'})
    base_slug = _re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-') or 'survey'
    new_slug = base_slug
    counter = 2
    while SatisfactionSurvey.objects.filter(slug=new_slug).exists():
        new_slug = f'{base_slug}-{counter}'
        counter += 1
    new_survey = SatisfactionSurvey.objects.create(
        title=title, slug=new_slug,
        active_date=active_date,
        expected_count=int(data.get('expected_count') or source.expected_count),
        sessions_data=source.sessions_data or CAMP_SESSIONS,
    )
    return JsonResponse({'ok': True, 'slug': new_survey.slug, 'title': new_survey.title})


@require_POST
def api_survey_reset(request, slug):
    if not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': '권한 없음'}, status=403)
    from .models import SatisfactionSurvey
    survey = get_object_or_404(SatisfactionSurvey, slug=slug)
    deleted, _ = survey.responses.all().delete()
    return JsonResponse({'ok': True, 'deleted': deleted})


@require_POST
def api_survey_create(request):
    if not request.user.is_staff:
        return JsonResponse({'ok': False, 'error': '권한 없음'}, status=403)
    from .models import SatisfactionSurvey
    import re as _re
    from datetime import date
    data = json.loads(request.body)
    title = str(data.get('title', '')).strip()
    if not title:
        return JsonResponse({'ok': False, 'error': '제목을 입력해주세요.'})
    active_date = None
    if data.get('active_date'):
        try:
            active_date = date.fromisoformat(data['active_date'])
        except ValueError:
            return JsonResponse({'ok': False, 'error': '날짜 형식 오류'})
    base_slug = _re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-') or 'survey'
    new_slug = base_slug
    counter = 2
    while SatisfactionSurvey.objects.filter(slug=new_slug).exists():
        new_slug = f'{base_slug}-{counter}'
        counter += 1
    survey = SatisfactionSurvey.objects.create(
        title=title, slug=new_slug,
        active_date=active_date,
        expected_count=int(data.get('expected_count') or 0),
        sessions_data=CAMP_SESSIONS,
    )
    return JsonResponse({'ok': True, 'slug': survey.slug, 'title': survey.title})


# ─── 대회/자격 접수 이력 관리 ─────────────────────────────────────────────────

@login_required
@user_passes_test(lambda u: u.is_staff)
def exam_registration_admin(request):
    from .models import ExamRegistration, CompetitionType, CertInfo
    from django.contrib.auth import get_user_model
    User = get_user_model()

    if request.method == 'POST':
        data = request.POST
        user_ids = data.getlist('user_ids')
        event_type = data.get('event_type', 'cert')
        event_name = data.get('event_name', '').strip()
        exam_date = data.get('exam_date', '').strip()
        exam_time = data.get('exam_time', '').strip() or None
        note = data.get('note', '').strip()
        competition_type_id = data.get('competition_type_id') or None
        cert_info_id = data.get('cert_info_id') or None

        errors = []
        if not user_ids:
            errors.append('회원을 1명 이상 선택해주세요.')
        if not event_name:
            errors.append('대회/자격시험명을 입력해주세요.')
        if not exam_date:
            errors.append('날짜를 입력해주세요.')

        if not errors:
            for uid in user_ids:
                try:
                    u = User.objects.get(pk=uid)
                    ExamRegistration.objects.create(
                        user=u,
                        event_type=event_type,
                        event_name=event_name,
                        exam_date=exam_date,
                        exam_time=exam_time if exam_time else None,
                        note=note,
                        competition_type_id=competition_type_id,
                        cert_info_id=cert_info_id,
                        registered_by=request.user,
                    )
                except User.DoesNotExist:
                    pass
            messages.success(request, f'{len(user_ids)}명 접수 이력이 등록됐습니다.')
            return redirect('exam_registration_admin')
        for e in errors:
            messages.error(request, e)

    # 목록
    qs = ExamRegistration.objects.select_related('user', 'competition_type', 'cert_info', 'registered_by').order_by('-exam_date', '-created_at')

    # 필터
    f_type = request.GET.get('type', '')
    f_user = request.GET.get('user', '').strip()
    f_name = request.GET.get('name', '').strip()
    if f_type:
        qs = qs.filter(event_type=f_type)
    if f_user:
        qs = qs.filter(user__profile__real_name__icontains=f_user) | qs.filter(user__username__icontains=f_user)
    if f_name:
        qs = qs.filter(event_name__icontains=f_name)

    competition_types = CompetitionType.objects.all().order_by('order', 'name')
    cert_infos = CertInfo.objects.all().order_by('name')

    return render(request, 'arcade/exam_registration_admin.html', {
        'registrations': qs[:200],
        'competition_types': competition_types,
        'cert_infos': cert_infos,
        'f_type': f_type,
        'f_user': f_user,
        'f_name': f_name,
    })


@login_required
@user_passes_test(lambda u: u.is_staff)
def exam_registration_delete(request, pk):
    from .models import ExamRegistration
    reg = get_object_or_404(ExamRegistration, pk=pk)
    if request.method == 'POST':
        reg.delete()
        messages.success(request, '삭제됐습니다.')
    return redirect('exam_registration_admin')


@login_required
@user_passes_test(lambda u: u.is_staff)
def api_search_members(request):
    """회원 검색 API (접수 이력 등록용)"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'members': []})
    users = User.objects.filter(
        profile__real_name__icontains=q
    ).select_related('profile')[:20]
    if not users.exists():
        users = User.objects.filter(username__icontains=q).select_related('profile')[:20]
    results = [
        {
            'id': u.pk,
            'username': u.username,
            'real_name': getattr(u.profile, 'real_name', '') or '',
            'display': (getattr(u.profile, 'real_name', '') or u.username),
        }
        for u in users
    ]
    return JsonResponse({'members': results})
