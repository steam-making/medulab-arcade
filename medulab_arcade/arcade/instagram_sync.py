"""인스타그램 게시물 동기화 + 액세스 토큰 자동 갱신.

두 가지 발급 방식의 토큰을 모두 지원한다:
- "Instagram API with Instagram Login"으로 발급한 토큰(보통 IGAA로 시작) →
  graph.instagram.com 사용, 앱 시크릿 없이 ig_refresh_token으로 자체 갱신
- 페이스북 페이지에 연결해 발급한 구버전 토큰(보통 EAA로 시작) →
  graph.facebook.com 사용, 앱 ID/시크릿으로 fb_exchange_token 갱신
"""
from datetime import timedelta

import requests
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import InstagramConfig, InstagramPost

API_VERSION = 'v21.0'
IG_LOGIN_API_BASE = 'https://graph.instagram.com'
FACEBOOK_API_BASE = f'https://graph.facebook.com/{API_VERSION}'
REQUEST_TIMEOUT = 10


def get_config():
    config, _ = InstagramConfig.objects.get_or_create(pk=1)
    return config


def _is_ig_login_token(token):
    return token.startswith('IGAA')


def refresh_token_if_needed(config):
    """장기 토큰 만료 7일 전이면 미리 갱신."""
    if not config.access_token:
        return config
    if config.token_expires_at and (config.token_expires_at - timezone.now()) > timedelta(days=7):
        return config

    try:
        if _is_ig_login_token(config.access_token):
            resp = requests.get(f'{IG_LOGIN_API_BASE}/refresh_access_token', params={
                'grant_type': 'ig_refresh_token',
                'access_token': config.access_token,
            }, timeout=REQUEST_TIMEOUT)
        elif config.app_id and config.app_secret:
            resp = requests.get(f'{FACEBOOK_API_BASE}/oauth/access_token', params={
                'grant_type': 'fb_exchange_token',
                'client_id': config.app_id,
                'client_secret': config.app_secret,
                'fb_exchange_token': config.access_token,
            }, timeout=REQUEST_TIMEOUT)
        else:
            return config

        data = resp.json()
        if 'access_token' in data:
            config.access_token = data['access_token']
            expires_in = data.get('expires_in', 60 * 24 * 3600)
            config.token_expires_at = timezone.now() + timedelta(seconds=expires_in)
            config.save(update_fields=['access_token', 'token_expires_at'])
    except requests.RequestException:
        pass  # 갱신 실패해도 기존 토큰으로 계속 시도
    return config


def sync_posts(limit=500):
    """인스타그램 게시물을 가져와 InstagramPost에 upsert."""
    config = get_config()
    if not config.access_token or not config.ig_user_id:
        return {'success': False, 'error': '액세스 토큰 또는 계정 ID가 설정되지 않았습니다.'}

    config = refresh_token_if_needed(config)
    api_base = IG_LOGIN_API_BASE if _is_ig_login_token(config.access_token) else FACEBOOK_API_BASE

    url = f'{api_base}/{config.ig_user_id}/media'
    params = {
        'fields': (
            'id,caption,media_type,media_url,permalink,thumbnail_url,timestamp,'
            'children{media_type,media_url,thumbnail_url}'
        ),
        'access_token': config.access_token,
        'limit': min(limit, 100),
    }
    fetched = 0
    try:
        while url and fetched < limit:
            resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            data = resp.json()
            if 'error' in data:
                message = data['error'].get('message', '알 수 없는 오류')
                config.last_sync_error = message[:300]
                config.save(update_fields=['last_sync_error'])
                return {'success': False, 'error': message}

            for item in data.get('data', []):
                children = None
                if item.get('media_type') == 'CAROUSEL_ALBUM' and item.get('children', {}).get('data'):
                    children = [
                        {
                            'media_type': child.get('media_type', ''),
                            'media_url': child.get('media_url', ''),
                            'thumbnail_url': child.get('thumbnail_url', ''),
                        }
                        for child in item['children']['data']
                    ]
                InstagramPost.objects.update_or_create(
                    media_id=item['id'],
                    defaults={
                        'media_type': item.get('media_type', ''),
                        'media_url': item.get('media_url', ''),
                        'thumbnail_url': item.get('thumbnail_url', ''),
                        'permalink': item.get('permalink', ''),
                        'caption': item.get('caption', ''),
                        'carousel_children': children,
                        'posted_at': parse_datetime(item['timestamp']) if item.get('timestamp') else None,
                    }
                )
                fetched += 1

            url = data.get('paging', {}).get('next')
            params = None  # next 링크에 이미 access_token 등 파라미터 포함됨
    except requests.RequestException as e:
        config.last_sync_error = str(e)[:300]
        config.save(update_fields=['last_sync_error'])
        return {'success': False, 'error': str(e)}

    config.last_synced_at = timezone.now()
    config.last_sync_error = ''
    config.save(update_fields=['last_synced_at', 'last_sync_error'])
    return {'success': True, 'count': fetched}


def _graph_error_message(data):
    err = data.get('error') or {}
    message = err.get('error_user_msg') or err.get('message') or '알 수 없는 오류'
    if 'permission' in message.lower() or err.get('code') == 200:
        message += ' (토큰에 게시(instagram_content_publish) 권한이 없을 수 있습니다. Meta 콘솔에서 권한을 포함해 토큰을 재발급해 주세요.)'
    return message


def _create_container(api_base, ig_user_id, access_token, **fields):
    params = {'access_token': access_token, **fields}
    resp = requests.post(f'{api_base}/{ig_user_id}/media', data=params, timeout=30)
    data = resp.json()
    if 'error' in data:
        return None, _graph_error_message(data)
    return data.get('id'), None


def _publish_container(api_base, ig_user_id, access_token, creation_id):
    resp = requests.post(f'{api_base}/{ig_user_id}/media_publish', data={
        'access_token': access_token,
        'creation_id': creation_id,
    }, timeout=30)
    data = resp.json()
    if 'error' in data:
        return None, _graph_error_message(data)
    return data.get('id'), None


def _get_permalink(api_base, media_id, access_token):
    try:
        resp = requests.get(f'{api_base}/{media_id}', params={
            'fields': 'permalink',
            'access_token': access_token,
        }, timeout=10)
        return resp.json().get('permalink', '')
    except requests.RequestException:
        return ''


def _publish_ready(config):
    if not config.access_token or not config.ig_user_id:
        return False, '액세스 토큰 또는 계정 ID가 설정되지 않았습니다. /admin-services/instagram/ 에서 먼저 연동해 주세요.'
    return True, None


def publish_single_image(image_public_url, caption):
    """이미지 1장 게시. 반환: {success, media_id, permalink, error}"""
    config = refresh_token_if_needed(get_config())
    ok, err = _publish_ready(config)
    if not ok:
        return {'success': False, 'error': err}
    api_base = IG_LOGIN_API_BASE if _is_ig_login_token(config.access_token) else FACEBOOK_API_BASE

    creation_id, err = _create_container(api_base, config.ig_user_id, config.access_token,
                                          image_url=image_public_url, caption=caption)
    if err:
        return {'success': False, 'error': err}

    media_id, err = _publish_container(api_base, config.ig_user_id, config.access_token, creation_id)
    if err:
        return {'success': False, 'error': err}

    permalink = _get_permalink(api_base, media_id, config.access_token)
    return {'success': True, 'media_id': media_id, 'permalink': permalink}


def publish_carousel(image_public_urls, caption):
    """이미지 여러 장을 캐러셀로 게시. 반환: {success, media_id, permalink, error}"""
    config = refresh_token_if_needed(get_config())
    ok, err = _publish_ready(config)
    if not ok:
        return {'success': False, 'error': err}
    api_base = IG_LOGIN_API_BASE if _is_ig_login_token(config.access_token) else FACEBOOK_API_BASE

    child_ids = []
    for url in image_public_urls:
        child_id, err = _create_container(api_base, config.ig_user_id, config.access_token,
                                           image_url=url, is_carousel_item='true')
        if err:
            return {'success': False, 'error': err}
        child_ids.append(child_id)

    creation_id, err = _create_container(
        api_base, config.ig_user_id, config.access_token,
        media_type='CAROUSEL', caption=caption, children=','.join(child_ids),
    )
    if err:
        return {'success': False, 'error': err}

    media_id, err = _publish_container(api_base, config.ig_user_id, config.access_token, creation_id)
    if err:
        return {'success': False, 'error': err}

    permalink = _get_permalink(api_base, media_id, config.access_token)
    return {'success': True, 'media_id': media_id, 'permalink': permalink}


def publish_video(video_public_url, caption, max_wait_seconds=60):
    """영상 1개 게시(REELS). 업로드 처리 완료까지 폴링 후 게시. 반환: {success, media_id, permalink, error}"""
    import time

    config = refresh_token_if_needed(get_config())
    ok, err = _publish_ready(config)
    if not ok:
        return {'success': False, 'error': err}
    api_base = IG_LOGIN_API_BASE if _is_ig_login_token(config.access_token) else FACEBOOK_API_BASE

    creation_id, err = _create_container(api_base, config.ig_user_id, config.access_token,
                                          media_type='REELS', video_url=video_public_url, caption=caption)
    if err:
        return {'success': False, 'error': err}

    waited = 0
    while waited < max_wait_seconds:
        try:
            resp = requests.get(f'{api_base}/{creation_id}', params={
                'fields': 'status_code',
                'access_token': config.access_token,
            }, timeout=10)
            status = resp.json().get('status_code')
        except requests.RequestException:
            status = None
        if status == 'FINISHED':
            break
        if status == 'ERROR':
            return {'success': False, 'error': '인스타그램에서 영상 처리 중 오류가 발생했습니다.'}
        time.sleep(3)
        waited += 3
    else:
        return {'success': False, 'error': '영상 처리가 제한 시간 내에 끝나지 않았습니다. 잠시 후 다시 시도해 주세요.'}

    media_id, err = _publish_container(api_base, config.ig_user_id, config.access_token, creation_id)
    if err:
        return {'success': False, 'error': err}

    permalink = _get_permalink(api_base, media_id, config.access_token)
    return {'success': True, 'media_id': media_id, 'permalink': permalink}
