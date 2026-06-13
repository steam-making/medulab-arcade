from django import forms
from django.contrib import admin
from django.utils import timezone
from .models import Badge, Bookmark, Category, Like, Project, ScheduleAttachment, ScheduleEvent, UserBadge, UserProfile, Notice, Award, Certification


BADGE_CRITERIA_HELP = (
    '지원 조건: typing_total_count(누적 타자 기록 수), typing_accuracy(정확도 이상), '
    'typing_speed(타속 이상), typing_practice_first(유형별 첫 기록), '
    'program_completion(연결 과정 이수), program_completion_count(서로 다른 과정 이수 수), '
    'homework_completion_count(완료 숙제 수), mission_completion_count(완료 미션 수)'
)


class BadgeAdminForm(forms.ModelForm):
    class Meta:
        model = Badge
        fields = '__all__'
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['criteria_type'].help_text = BADGE_CRITERIA_HELP
        self.fields['criteria_value'].help_text = '조건 달성 기준값입니다. 예: 정확도 90, 타속 250, 이수 과정 3개.'
        self.fields['related_program'].help_text = 'program_completion 조건일 때 연결할 과정을 선택합니다.'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'order')
    list_editable = ('order',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'author_display_name', 'get_categories', 'status', 'is_featured', 'play_count', 'created_at')
    list_filter = ('status', 'categories', 'is_featured')
    list_editable = ('status', 'is_featured')
    search_fields = ('title', 'author_display_name', 'description')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('play_count', 'project_path')
    actions = ['approve_projects', 'reject_projects']

    @admin.display(description='카테고리')
    def get_categories(self, obj):
        return ", ".join([c.name for c in obj.categories.all()])

    @admin.action(description='선택한 작품 승인')
    def approve_projects(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, f'{queryset.count()}개 작품이 승인되었습니다.')

    @admin.action(description='선택한 작품 반려')
    def reject_projects(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f'{queryset.count()}개 작품이 반려되었습니다.')


@admin.register(ScheduleEvent)
class ScheduleEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'start_date', 'end_date', 'is_active')
    list_filter = ('event_type', 'is_active', 'start_date')
    list_editable = ('is_active',)
    search_fields = ('title', 'description')
    ordering = ('start_date', 'end_date', 'title')


@admin.register(ScheduleAttachment)
class ScheduleAttachmentAdmin(admin.ModelAdmin):
    list_display = ('event', 'file', 'uploaded_at')
    list_filter = ('event',)


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'created_at')


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'created_at')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'is_approved', 'approved_at', 'created_at')
    list_filter = ('user_type', 'is_approved')
    list_editable = ('is_approved',)
    search_fields = ('user__username', 'user__email')
    actions = ['approve_members', 'reject_members']

    @admin.action(description='✅ 선택한 회원 승인')
    def approve_members(self, request, queryset):
        queryset.update(is_approved=True, approved_at=timezone.now())
        self.message_user(request, f'{queryset.count()}명의 회원이 승인되었습니다.')

    @admin.action(description='❌ 선택한 회원 승인 취소')
    def reject_members(self, request, queryset):
        queryset.update(is_approved=False, approved_at=None)
        self.message_user(request, f'{queryset.count()}명의 회원이 승인 취소되었습니다.')


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    form = BadgeAdminForm
    list_display = (
        'code',
        'name',
        'icon',
        'color',
        'category',
        'criteria_type',
        'criteria_value',
        'related_program',
        'is_active',
        'sort_order',
        'description_preview',
    )
    list_display_links = ('code',)
    list_editable = (
        'name',
        'icon',
        'color',
        'category',
        'criteria_type',
        'criteria_value',
        'related_program',
        'is_active',
        'sort_order',
    )
    list_filter = ('category', 'criteria_type', 'is_active', 'related_program')
    search_fields = ('name', 'code', 'description', 'criteria_type', 'related_program__name')
    autocomplete_fields = ('related_program',)
    list_select_related = ('related_program',)
    list_per_page = 50
    fieldsets = (
        ('기본 정보', {
            'fields': ('code', 'name', 'description', 'icon', 'color', 'category', 'is_active', 'sort_order'),
            'description': '배지에 표시되는 이름, 설명, 아이콘, 색상과 노출 상태를 관리합니다.',
        }),
        ('획득 조건', {
            'fields': ('criteria_type', 'criteria_value', 'related_program'),
            'description': BADGE_CRITERIA_HELP,
        }),
    )

    @admin.display(description='설명')
    def description_preview(self, obj):
        return obj.description[:40] + ('...' if len(obj.description) > 40 else '')


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'awarded_at')
    list_filter = ('badge__category', 'awarded_at')
    search_fields = ('user__username', 'badge__name', 'badge__code')

@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at', 'view_count', 'is_pinned')
    list_filter = ('is_pinned', 'created_at')
    search_fields = ('title', 'content')
    list_editable = ('is_pinned',)

@admin.register(Award)
class AwardAdmin(admin.ModelAdmin):
    list_display = ('title', 'student_name', 'competition_name', 'organization', 'award_name', 'date_awarded')
    list_filter = ('date_awarded',)
    search_fields = ('student_name', 'competition_name', 'award_name', 'organization', 'title')

@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'student_name', 'cert_name', 'issuer', 'date_acquired')
    list_filter = ('date_acquired',)
    search_fields = ('student_name', 'cert_name', 'issuer', 'title')

