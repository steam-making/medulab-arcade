"""인스타그램 그래프 API 연동: 게시물 동기화 + 장기 액세스 토큰 자동 갱신."""
from datetime import timedelta

import requests
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import InstagramConfig, InstagramPost

GRAPH_API_VERSION = 'v21.0'
GRAPH_API_BASE = f'https://graph.facebook.com/{GRAPH_API_VERSION}'
REQUEST_TIMEOUT = 10


def get_config():
    config, _ = InstagramConfig.objects.get_or_create(pk=1)
    return config


def refresh_token_if_needed(config):
    """장기 토큰 만료 7일 전이면 미리 갱신 (fb_exchange_token)."""
    if not config.access_token or not config.app_id or not config.app_secret:
        return config
    if config.token_expires_at and (config.token_expires_at - timezone.now()) > timedelta(days=7):
        return config

    try:
        resp = requests.get(f'{GRAPH_API_BASE}/oauth/access_token', params={
            'grant_type': 'fb_exchange_token',
            'client_id': config.app_id,
            'client_secret': config.app_secret,
            'fb_exchange_token': config.access_token,
        }, timeout=REQUEST_TIMEOUT)
        data = resp.json()
        if 'access_token' in data:
            config.access_token = data['access_token']
            expires_in = data.get('expires_in', 60 * 24 * 3600)
            config.token_expires_at = timezone.now() + timedelta(seconds=expires_in)
            config.save(update_fields=['access_token', 'token_expires_at'])
    except requests.RequestException:
        pass  # 갱신 실패해도 기존 토큰으로 계속 시도
    return config


def sync_posts(limit=60):
    """인스타그램 게시물을 가져와 InstagramPost에 upsert."""
    config = get_config()
    if not config.access_token or not config.ig_user_id:
        return {'success': False, 'error': '액세스 토큰 또는 계정 ID가 설정되지 않았습니다.'}

    config = refresh_token_if_needed(config)

    url = f'{GRAPH_API_BASE}/{config.ig_user_id}/media'
    params = {
        'fields': 'id,caption,media_type,media_url,permalink,thumbnail_url,timestamp',
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
                InstagramPost.objects.update_or_create(
                    media_id=item['id'],
                    defaults={
                        'media_type': item.get('media_type', ''),
                        'media_url': item.get('media_url', ''),
                        'thumbnail_url': item.get('thumbnail_url', ''),
                        'permalink': item.get('permalink', ''),
                        'caption': item.get('caption', ''),
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
