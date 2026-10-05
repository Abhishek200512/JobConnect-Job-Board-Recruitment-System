"""DRF serializers for companies."""
from rest_framework import serializers

from .models import Company


class CompanySerializer(serializers.ModelSerializer):
    open_jobs = serializers.IntegerField(read_only=True, default=0)
    recruiter_email = serializers.EmailField(source="recruiter.email", read_only=True)

    class Meta:
        model = Company
        fields = [
            "id", "company_name", "logo", "description", "website", "location",
            "industry", "size", "founded_year", "open_jobs", "recruiter_email",
            "created_at",
        ]
