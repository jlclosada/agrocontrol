from django.contrib import admin

from apps.tasks.models import Task, TaskActivity


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        "title", "status", "priority", "category", "due_date", "cooperative",
    ]
    list_filter = ["cooperative", "status", "priority", "category", "due_date"]
    search_fields = ["title", "description"]
    filter_horizontal = ["assignees"]


@admin.register(TaskActivity)
class TaskActivityAdmin(admin.ModelAdmin):
    list_display = ["task", "action", "field", "actor", "created_at"]
    list_filter = ["action", "created_at"]
    search_fields = ["task__title", "from_value", "to_value", "note"]
    readonly_fields = [
        "task", "actor", "action", "field", "from_value", "to_value",
        "note", "created_at",
    ]

