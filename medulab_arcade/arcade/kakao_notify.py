"""신규 상담 문의 접수 시 관리자 본인의 카카오톡으로 알림을 보내는 유틸리티.

'카카오톡 나에게 보내기'(Kakao Memo API)를 사용한다. 사용 전 관리자가
/admin-services/kakao-notify/connect/ 에서 한번 카카오 로그인 동의를 해줘야
KakaoNotifyToken 이 생성된다. 실패해도 상담 문의 저장 자체는 막지 않는다.
"""
import logging

import requests
from django.conf import settings
from django.utils import timezone

from .models import KakaoNotifyToken

logger = logging.getLogger(__name__)

KAKAO_TOKEN_URL = 'https://kauth.kakao.com/oauth/token'
KAKAO_MEMO_URL = 'https://kapi.kakao.com/v2/api/talk/memo/default/send'


def _refresh_token(token: KakaoNotifyToken) -> bool:
    try:
        resp = requests.post(KAKAO_TOKEN_URL, data={
            'grant_type': 'refresh_token',
            'client_id': settings.KAKAO_CLIENT_ID,
            'client_secret': settings.KAKAO_CLIENT_SECRET,
            'refresh_token': token.refresh_token,
        }, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        logger.exception('카카오 알림 토큰 갱신 실패')
        return False

    token.access_token = data['access_token']
    if data.get('refresh_token'):
        token.refresh_token = data['refresh_token']
    token.expires_at = timezone.now() + timezone.timedelta(seconds=data.get('expires_in', 3600))
    token.save(update_fields=['access_token', 'refresh_token', 'expires_at', 'updated_at'])
    return True


def _get_valid_token():
    token = KakaoNotifyToken.objects.filter(is_active=True).order_by('-updated_at').first()
    if not token:
        return None
    if token.expires_at <= timezone.now() + timezone.timedelta(minutes=2):
        if not _refresh_token(token):
            return None
        token.refresh_from_db()
    return token


def send_kakao_memo_to_me(text: str) -> bool:
    """관리자 본인 카카오톡으로 텍스트 메모를 보낸다. 성공 여부를 반환."""
    token = _get_valid_token()
    if not token:
        logger.warning('카카오 알림 토큰이 없어 알림을 보내지 못했습니다. 관리자 연동이 필요합니다.')
        return False

    template_object = {
        'object_type': 'text',
        'text': text[:200],
        'link': {
            'web_url': getattr(settings, 'SITE_BASE_URL', '') or '',
            'mobile_web_url': getattr(settings, 'SITE_BASE_URL', '') or '',
        },
    }
    try:
        resp = requests.post(
            KAKAO_MEMO_URL,
            headers={'Authorization': f'Bearer {token.access_token}'},
            data={'template_object': __import__('json').dumps(template_object, ensure_ascii=False)},
            timeout=10,
        )
        resp.raise_for_status()
    except Exception:
        logger.exception('카카오 알림 발송 실패')
        return False
    return True


def notify_new_consult_inquiry(inquiry) -> bool:
    """새 상담 문의 접수 시 요약 메시지를 관리자 카카오톡으로 발송."""
    if inquiry.applicant_type == inquiry.APPLICANT_PARENT and inquiry.children_info:
        children = ', '.join(
            f"{c.get('name', '')}({c.get('age', '')})" for c in inquiry.children_info if c.get('name')
        )
        who = f'학부모 - 자녀: {children}' if children else '학부모'
    else:
        age = f' / {inquiry.age_or_grade}' if inquiry.age_or_grade else ''
        who = f'본인 - {inquiry.name}{age}'

    lines = [
        '📥 새 상담 문의가 접수되었습니다.',
        f'신청: {who}',
        f'연락처: {inquiry.phone_number}',
    ]
    if inquiry.finder_track:
        lines.append(f'추천 트랙: {inquiry.finder_track}')
    if inquiry.message:
        lines.append(f'문의내용: {inquiry.message[:80]}')

    return send_kakao_memo_to_me('\n'.join(lines))
