from django.db import migrations


def rename_favorites(apps, schema_editor):
    NavItem = apps.get_model('arcade', 'NavItem')
    NavItem.objects.filter(name='AI 즐겨찾기').update(name='즐겨찾기')


def revert_rename(apps, schema_editor):
    NavItem = apps.get_model('arcade', 'NavItem')
    NavItem.objects.filter(name='즐겨찾기').update(name='AI 즐겨찾기')


class Migration(migrations.Migration):
    dependencies = [
        ('arcade', '0032_nav_item_initial_data'),
    ]

    operations = [
        migrations.RunPython(rename_favorites, revert_rename),
    ]
