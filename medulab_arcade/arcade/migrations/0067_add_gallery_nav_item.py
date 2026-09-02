from django.db import migrations
from django.db.models import F


def add_gallery_nav_item(apps, schema_editor):
    NavItem = apps.get_model('arcade', 'NavItem')
    # 학원시간표(order=3) 뒤에 넣기 위해 그 이후 항목들의 order를 한 칸씩 밀기
    NavItem.objects.filter(section='notices', order__gte=4).update(order=F('order') + 1)
    NavItem.objects.create(
        section='notices',
        emoji='📸',
        name='학원갤러리',
        url_name='instagram_gallery',
        url_extra='',
        order=4,
        is_active=True,
        is_accent=False,
        new_tab=False,
    )


def remove_gallery_nav_item(apps, schema_editor):
    NavItem = apps.get_model('arcade', 'NavItem')
    NavItem.objects.filter(section='notices', url_name='instagram_gallery').delete()
    NavItem.objects.filter(section='notices', order__gt=4).update(order=F('order') - 1)


class Migration(migrations.Migration):

    dependencies = [
        ('arcade', '0066_instagramconfig_instagrampost'),
    ]

    operations = [
        migrations.RunPython(add_gallery_nav_item, remove_gallery_nav_item),
    ]
