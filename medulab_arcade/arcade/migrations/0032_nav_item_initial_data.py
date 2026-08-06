from django.db import migrations


NOTICES = [
    ('📢', '공지사항',       'board_notice',          '', False, False, 1),
    ('📅', '학원일정',       'schedule',              '', False, False, 2),
    ('🗓️', '학원시간표',    'timetable',             '', False, False, 3),
    ('✨', '추천 공모전',    'board_contest',         '', False, False, 4),
    ('🏆', '대회수상',       'board_awards',          '', False, False, 5),
    ('🏁', '대회종류',       'board_competition_type','', False, False, 6),
    ('🏅', '자격취득',       'board_cert',            '', False, False, 7),
    ('🎖️', '자격종류',      'board_certinfo',        '', False, False, 8),
]

LEARNING = [
    ('📚', '교육프로그램',       'student_course_list', '',        False, False, 1),
    ('🗺️', '프로그램 로드맵',   'program_roadmap',     '',        False, False, 2),
    ('🔍', '프로그램 찾기',      'program_finder',      '',        False, False, 3),
    ('🎨', '학생 작품 갤러리',   'home',                '#works',  False, False, 4),
    ('✨', 'AI 프롬프트 생성기', 'ai_prompts',          '',        True,  False, 5),
    ('⭐', 'AI 즐겨찾기',        'ai_favorites',        '',        False, False, 6),
    ('🔑', '로그인 도우미',      'login_helper',        '',        False, False, 7),
]


def populate_nav_items(apps, schema_editor):
    NavItem = apps.get_model('arcade', 'NavItem')
    for emoji, name, url_name, url_extra, is_accent, new_tab, order in NOTICES:
        NavItem.objects.create(
            section='notices', emoji=emoji, name=name,
            url_name=url_name, url_extra=url_extra,
            is_accent=is_accent, new_tab=new_tab, order=order,
        )
    for emoji, name, url_name, url_extra, is_accent, new_tab, order in LEARNING:
        NavItem.objects.create(
            section='learning', emoji=emoji, name=name,
            url_name=url_name, url_extra=url_extra,
            is_accent=is_accent, new_tab=new_tab, order=order,
        )


def remove_nav_items(apps, schema_editor):
    NavItem = apps.get_model('arcade', 'NavItem')
    NavItem.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('arcade', '0031_nav_item'),
    ]

    operations = [
        migrations.RunPython(populate_nav_items, remove_nav_items),
    ]
