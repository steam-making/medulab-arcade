# pyright: reportAttributeAccessIssue=false
from django.db.models import Count, F, Q

from courses.models import HomeworkSubmission, LearningProgram, UserProgress
from typing_practice.models import TypingScore

from .models import Badge, UserBadge


DEFAULT_BADGES = [
    {
        'code': 'typing-first-session',
        'name': '첫 타자 도전',
        'description': '타자연습 기록을 처음 저장했어요.',
        'icon': '⌨️',
        'color': '#5aa9ff',
        'category': Badge.CATEGORY_TYPING,
        'criteria_type': 'typing_total_count',
        'criteria_value': 1,
        'sort_order': 10,
    },
    {
        'code': 'typing-accuracy-90',
        'name': '정확도 90%',
        'description': '정확도 90% 이상으로 타자연습을 마쳤어요.',
        'icon': '🎯',
        'color': '#34d399',
        'category': Badge.CATEGORY_TYPING,
        'criteria_type': 'typing_accuracy',
        'criteria_value': 90,
        'sort_order': 20,
    },
    {
        'code': 'typing-speed-250',
        'name': '스피드 업',
        'description': '타속 250 이상을 달성했어요.',
        'icon': '⚡',
        'color': '#a855f7',
        'category': Badge.CATEGORY_TYPING,
        'criteria_type': 'typing_speed',
        'criteria_value': 250,
        'sort_order': 30,
    },
    {
        'code': 'program-first-completion',
        'name': '첫 과정 이수',
        'description': '학습 과정을 처음 끝까지 이수했어요.',
        'icon': '🎓',
        'color': '#f5c451',
        'category': Badge.CATEGORY_LEARNING,
        'criteria_type': 'program_completion_count',
        'criteria_value': 1,
        'sort_order': 40,
    },
    {
        'code': 'program-three-completions',
        'name': '꾸준한 학습자',
        'description': '서로 다른 학습 과정 3개를 이수했어요.',
        'icon': '🚀',
        'color': '#fb7185',
        'category': Badge.CATEGORY_MILESTONE,
        'criteria_type': 'program_completion_count',
        'criteria_value': 3,
        'sort_order': 50,
    },
    {
        'code': 'homework-first-completion',
        'name': '첫 홈플레이 완료',
        'description': '제출한 숙제를 처음 최종 완료했어요.',
        'icon': '📚',
        'color': '#38bdf8',
        'category': Badge.CATEGORY_LEARNING,
        'criteria_type': 'homework_completion_count',
        'criteria_value': 1,
        'sort_order': 60,
    },
    {
        'code': 'homework-three-completions',
        'name': '홈플레이 성실왕',
        'description': '숙제 3개를 최종 완료했어요.',
        'icon': '📝',
        'color': '#22c55e',
        'category': Badge.CATEGORY_MILESTONE,
        'criteria_type': 'homework_completion_count',
        'criteria_value': 3,
        'sort_order': 70,
    },
    {
        'code': 'mission-first-completion',
        'name': '첫 미션 클리어',
        'description': '학습 미션을 처음 완료했어요.',
        'icon': '🧩',
        'color': '#f97316',
        'category': Badge.CATEGORY_LEARNING,
        'criteria_type': 'mission_completion_count',
        'criteria_value': 1,
        'sort_order': 80,
    },
    {
        'code': 'mission-ten-completions',
        'name': '미션 해결사',
        'description': '학습 미션 10개를 완료했어요.',
        'icon': '🛡️',
        'color': '#8b5cf6',
        'category': Badge.CATEGORY_MILESTONE,
        'criteria_type': 'mission_completion_count',
        'criteria_value': 10,
        'sort_order': 90,
    },
]


def ensure_default_badges():
    for definition in DEFAULT_BADGES:
        Badge.objects.get_or_create(code=definition['code'], defaults=definition)


def serialize_badge_catalog_entry(badge, user_badge=None):
    awarded_at = user_badge.awarded_at if user_badge else None
    return {
        'code': badge.code,
        'name': badge.name,
        'description': badge.description,
        'icon': badge.icon,
        'color': badge.color,
        'category': badge.category,
        'criteria_type': badge.criteria_type,
        'criteria_value': badge.criteria_value,
        'related_program_id': badge.related_program_id,
        'sort_order': badge.sort_order,
        'is_earned': user_badge is not None,
        'is_locked': user_badge is None,
        'awarded_at': awarded_at,
    }


def serialize_user_badge(user_badge):
    badge = user_badge.badge
    return {
        'code': badge.code,
        'name': badge.name,
        'description': badge.description,
        'icon': badge.icon,
        'color': badge.color,
        'category': badge.category,
        'awarded_at': user_badge.awarded_at,
    }


def award_badge(user, badge):
    if not badge.is_active:
        return None
    user_badge, created = UserBadge.objects.get_or_create(user=user, badge=badge)
    return user_badge if created else None


def get_recent_user_badges(user, limit=6):
    if not user.is_authenticated:
        return []
    ensure_default_badges()
    return list(
        UserBadge.objects.filter(user=user)
        .select_related('badge')
        .order_by('-awarded_at')[:limit]
    )


def get_active_badges_with_user_state(user):
    if not user.is_authenticated:
        return []
    ensure_default_badges()
    user_badges = {
        user_badge.badge_id: user_badge
        for user_badge in UserBadge.objects.filter(user=user, badge__is_active=True)
    }
    return [
        serialize_badge_catalog_entry(badge, user_badges.get(badge.id))
        for badge in Badge.objects.filter(is_active=True).order_by('sort_order', 'name')
    ]


def get_user_badge_count(user):
    if not user.is_authenticated:
        return 0
    return UserBadge.objects.filter(user=user).count()


def get_program_completion_badge(program):
    badge, _ = Badge.objects.get_or_create(
        code=f'program-complete-{program.id}',
        defaults={
            'name': f'{program.name} 이수',
            'description': f'{program.name} 과정을 모두 완료했어요.',
            'icon': '🏆',
            'color': '#f5c451',
            'category': Badge.CATEGORY_LEARNING,
            'criteria_type': 'program_completion',
            'criteria_value': 1,
            'related_program': program,
            'sort_order': 1000 + program.id,
        },
    )
    return badge


def get_completed_program_ids(user):
    completed = LearningProgram.objects.annotate(
        total_items=Count('chapters__items', distinct=True),
        completed_items=Count(
            'chapters__items__user_progress',
            filter=Q(
                chapters__items__user_progress__user=user,
                chapters__items__user_progress__completed=True,
            ),
            distinct=True,
        ),
    ).filter(total_items__gt=0, completed_items=F('total_items'))
    return list(completed.values_list('id', flat=True))


def award_matching_badges(user, criteria_type, completed_count):
    new_badges = []
    badges = Badge.objects.filter(
        criteria_type=criteria_type,
        criteria_value__lte=completed_count,
        is_active=True,
    )
    for badge in badges:
        awarded = award_badge(user, badge)
        if awarded:
            new_badges.append(serialize_user_badge(awarded))
    return new_badges


def get_completed_homework_count(user):
    return HomeworkSubmission.objects.filter(
        student=user,
        status=HomeworkSubmission.STATUS_COMPLETED,
    ).count()


def evaluate_homework_badges(user):
    ensure_default_badges()
    return award_matching_badges(
        user,
        'homework_completion_count',
        get_completed_homework_count(user),
    )


def get_completed_mission_count(user):
    return UserProgress.objects.filter(user=user, completed=True).count()


def evaluate_mission_badges(user):
    ensure_default_badges()
    return award_matching_badges(
        user,
        'mission_completion_count',
        get_completed_mission_count(user),
    )


def evaluate_typing_badges(user, typing_score):
    ensure_default_badges()

    new_badges = []
    practice_badge, _ = Badge.objects.get_or_create(
        code=f'typing-practice-{typing_score.practice_type}-first',
        defaults={
            'name': f'{typing_score.get_practice_type_display()} 첫 클리어',
            'description': f'{typing_score.get_practice_type_display()} 기록을 처음 저장했어요.',
            'icon': '🥳',
            'color': '#60a5fa',
            'category': Badge.CATEGORY_TYPING,
            'criteria_type': 'typing_practice_first',
            'criteria_value': 1,
            'sort_order': 15,
        },
    )

    new_badges.extend(
        award_matching_badges(
            user,
            'typing_total_count',
            TypingScore.objects.filter(user=user).count(),
        )
    )

    if TypingScore.objects.filter(user=user, practice_type=typing_score.practice_type).count() == 1:
        awarded = award_badge(user, practice_badge)
        if awarded:
            new_badges.append(serialize_user_badge(awarded))

    new_badges.extend(award_matching_badges(user, 'typing_accuracy', typing_score.accuracy))
    new_badges.extend(award_matching_badges(user, 'typing_speed', typing_score.speed))

    return new_badges


def evaluate_program_badges(user, program):
    ensure_default_badges()

    completed_program_ids = get_completed_program_ids(user)
    completed_program_count = len(completed_program_ids)
    if program.id not in completed_program_ids:
        return []

    new_badges = []
    program_badge = get_program_completion_badge(program)
    completion_badges = list(
        Badge.objects.filter(
            criteria_type='program_completion',
            related_program=program,
            is_active=True,
        )
    )
    if (
        program_badge.is_active
        and program_badge.related_program_id == program.id
        and program_badge not in completion_badges
    ):
        completion_badges.append(program_badge)
    for badge in completion_badges:
        awarded = award_badge(user, badge)
        if awarded:
            new_badges.append(serialize_user_badge(awarded))

    new_badges.extend(
        award_matching_badges(user, 'program_completion_count', completed_program_count)
    )

    return new_badges
