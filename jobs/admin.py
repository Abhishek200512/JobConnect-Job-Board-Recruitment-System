from django.contrib import admin
from .models import Category, Job


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "category", "job_type", "work_mode", "status", "created_at")
    list_filter = ("status", "job_type", "work_mode", "category", "experience")
    search_fields = ("title", "company__company_name", "location", "skills")
    date_hierarchy = "created_at"
