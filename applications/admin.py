from django.contrib import admin
from .models import Application, SavedJob


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("job", "applicant", "status", "applied_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("job__title", "applicant__email", "applicant__full_name")


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ("user", "job", "created_at")
