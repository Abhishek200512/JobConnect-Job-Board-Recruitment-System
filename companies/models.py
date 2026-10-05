"""Company model."""
from django.conf import settings
from django.db import models
import os
import uuid


def company_logo_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"logos/company_{instance.pk or 'new'}_{uuid.uuid4().hex[:8]}{ext}"


class Company(models.Model):
    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="companies"
    )
    company_name = models.CharField(max_length=150, unique=True)
    logo = models.ImageField(upload_to=company_logo_path, null=True, blank=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=120, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    size = models.CharField(max_length=30, blank=True, help_text="e.g. 50-200 employees")
    founded_year = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "companies"
        indexes = [models.Index(fields=["location"]), models.Index(fields=["industry"])]

    def __str__(self):
        return self.company_name
