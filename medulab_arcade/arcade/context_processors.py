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
