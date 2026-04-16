from django.contrib import admin
from django.utils import timezone
from .models import Project, Category, Like, Bookmark, UserProfile


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

    def get_categories(self, obj):
        return ", ".join([c.name for c in obj.categories.all()])
    get_categories.short_description = '카테고리'

    def approve_projects(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, f'{queryset.count()}개 작품이 승인되었습니다.')
    approve_projects.short_description = '선택한 작품 승인'

    def reject_projects(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f'{queryset.count()}개 작품이 반려되었습니다.')
    reject_projects.short_description = '선택한 작품 반려'


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

    def approve_members(self, request, queryset):
        queryset.update(is_approved=True, approved_at=timezone.now())
        self.message_user(request, f'{queryset.count()}명의 회원이 승인되었습니다.')
    approve_members.short_description = '✅ 선택한 회원 승인'

    def reject_members(self, request, queryset):
        queryset.update(is_approved=False, approved_at=None)
        self.message_user(request, f'{queryset.count()}명의 회원이 승인 취소되었습니다.')
    reject_members.short_description = '❌ 선택한 회원 승인 취소'
