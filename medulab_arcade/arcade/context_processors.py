from django.core.cache import cache


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
