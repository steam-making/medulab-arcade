from django.contrib import admin
from .models import (
    Chapter,
    Item,
    LearningEnrollment,
    LearningProgram,
    OlympiadAnswerExample,
    OlympiadAnswerSubmission,
    ProgramType,
    UserProgress,
)

class ItemInline(admin.TabularInline):
    model = Item
    extra = 1


class OlympiadAnswerExampleInline(admin.TabularInline):
    model = OlympiadAnswerExample
    extra = 1
    fields = ["image", "caption", "order", "created_at"]
    readonly_fields = ["created_at"]

class ChapterAdmin(admin.ModelAdmin):
    list_display = ['program', 'number', 'title']
    list_filter = ['program']
    inlines = [ItemInline]

class LearningProgramAdmin(admin.ModelAdmin):
    list_display = ['name', 'program_type', 'is_active', 'created_at']
    list_filter = ['program_type', 'is_active']
    search_fields = ['name', 'description']


class ItemAdmin(admin.ModelAdmin):
    list_display = ["chapter", "number", "title", "item_type", "due_date"]
    list_filter = ["item_type", "chapter__program"]
    search_fields = ["title", "key", "chapter__title", "chapter__program__name"]
    inlines = [OlympiadAnswerExampleInline]


class OlympiadAnswerExampleAdmin(admin.ModelAdmin):
    list_display = ["item", "caption", "order", "created_at"]
    list_filter = ["item__chapter__program", "created_at"]
    search_fields = ["item__title", "item__key", "caption"]
    readonly_fields = ["created_at"]


class OlympiadAnswerSubmissionAdmin(admin.ModelAdmin):
    list_display = ["item", "student", "status", "submitted_at", "reviewed_at", "updated_at"]
    list_filter = ["status", "item__chapter__program", "submitted_at", "reviewed_at"]
    search_fields = [
        "item__title",
        "item__key",
        "student__username",
        "student__first_name",
        "student__last_name",
        "ocr_text",
        "edited_text",
        "feedback",
    ]
    readonly_fields = ["submitted_at", "updated_at"]

admin.site.register(ProgramType)
admin.site.register(LearningProgram, LearningProgramAdmin)
admin.site.register(Chapter, ChapterAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(LearningEnrollment)
admin.site.register(UserProgress)
admin.site.register(OlympiadAnswerExample, OlympiadAnswerExampleAdmin)
admin.site.register(OlympiadAnswerSubmission, OlympiadAnswerSubmissionAdmin)
