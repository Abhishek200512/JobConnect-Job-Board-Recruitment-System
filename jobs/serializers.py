"""DRF serializers for jobs."""
from rest_framework import serializers

from .models import Job, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "icon", "description"]


class JobListSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.company_name", read_only=True)
    company_logo = serializers.SerializerMethodField()
    category_name = serializers.CharField(source="category.name", read_only=True)
    salary_display = serializers.CharField(read_only=True)
    posted_display = serializers.CharField(read_only=True)
    application_count = serializers.IntegerField(read_only=True)
    url = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            "id", "title", "slug", "company_name", "company_logo", "category_name",
            "location", "job_type", "work_mode", "experience", "salary_display",
            "openings", "skills", "posted_display", "application_count", "views_count",
            "created_at", "url",
        ]

    def get_company_logo(self, obj):
        request = self.context.get("request")
        if obj.company.logo:
            url = obj.company.logo.url
            return request.build_absolute_uri(url) if request else url
        return None

    def get_url(self, obj):
        request = self.context.get("request")
        path = f"/jobs/{obj.pk}/"
        return request.build_absolute_uri(path) if request else path


class JobDetailSerializer(JobListSerializer):
    company_location = serializers.CharField(source="company.location", read_only=True)
    company_website = serializers.CharField(source="company.website", read_only=True)
    description = serializers.CharField()
    responsibilities = serializers.CharField()
    qualifications = serializers.CharField()
    benefits = serializers.CharField()

    class Meta(JobListSerializer.Meta):
        fields = JobListSerializer.Meta.fields + [
            "description", "responsibilities", "qualifications", "benefits",
            "salary_min", "salary_max", "company_location", "company_website",
        ]
