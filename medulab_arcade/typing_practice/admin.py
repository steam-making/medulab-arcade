from django.contrib import admin
from .models import TypingContent, TypingHallOfFame, TypingScore

@admin.register(TypingScore)
class TypingScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'practice_type', 'language', 'score', 'speed', 'accuracy', 'created_at')
    list_filter = ('practice_type', 'language', 'created_at')
    search_fields = ('user__username',)

@admin.register(TypingContent)
class TypingContentAdmin(admin.ModelAdmin):
    list_display = ('content_type', 'language', 'title', 'created_at')
    list_filter = ('content_type', 'language')
    search_fields = ('title', 'text')


@admin.register(TypingHallOfFame)
class TypingHallOfFameAdmin(admin.ModelAdmin):
    list_display = ('practice_type', 'category', 'language', 'user', 'record_value', 'quarter_key', 'updated_at')
    list_filter = ('language', 'practice_type', 'category')
    search_fields = ('user__username', 'quarter_key')
