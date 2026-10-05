from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, JobSeekerProfile, OTPVerification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("-created_at",)
    list_display = ("email", "username", "role", "is_active", "is_verified", "created_at")
    list_filter = ("role", "is_active", "is_verified")
    search_fields = ("email", "username", "full_name")
    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Profile", {"fields": ("full_name", "role", "phone")}),
        ("Status", {"fields": ("is_active", "is_verified", "is_staff", "is_superuser")}),
        ("Dates", {"fields": ("last_login", "created_at")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "username", "role", "password1", "password2")}),
    )
    readonly_fields = ("last_login", "created_at")


@admin.register(JobSeekerProfile)
class SeekerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "location", "experience_years", "updated_at")
    search_fields = ("user__email", "user__full_name", "location")


@admin.register(OTPVerification)
class OTPAdmin(admin.ModelAdmin):
    list_display = ("email", "purpose", "verified", "expires_at", "created_at")
    list_filter = ("purpose", "verified")
