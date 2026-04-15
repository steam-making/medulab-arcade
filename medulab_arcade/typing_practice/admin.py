from django.contrib import admin
from .models import TypingScore, TypingContent

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
