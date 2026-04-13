from django.contrib import admin
from .models import ProgramType, LearningProgram, Chapter, Item, LearningEnrollment, UserProgress

class ItemInline(admin.TabularInline):
    model = Item
    extra = 1

class ChapterAdmin(admin.ModelAdmin):
    list_display = ['program', 'number', 'title']
    list_filter = ['program']
    inlines = [ItemInline]

class LearningProgramAdmin(admin.ModelAdmin):
    list_display = ['name', 'program_type', 'is_active', 'created_at']
    list_filter = ['program_type', 'is_active']
    search_fields = ['name', 'description']

admin.site.register(ProgramType)
admin.site.register(LearningProgram, LearningProgramAdmin)
admin.site.register(Chapter, ChapterAdmin)
admin.site.register(Item)
admin.site.register(LearningEnrollment)
admin.site.register(UserProgress)
