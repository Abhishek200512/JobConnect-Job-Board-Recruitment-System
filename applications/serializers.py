"""DRF serializers for applications."""
from rest_framework import serializers

from jobs.serializers import JobListSerializer

from .models import Application, SavedJob


class ApplicationCreateSerializer(serializers.ModelSerializer):
    job = serializers.PrimaryKeyRelatedField(queryset=JobListSerializer.Meta.model.objects.all())

    class Meta:
        model = Application
        fields = ["job", "resume", "cover_letter", "expected_salary", "notice_period", "additional_info"]

    def validate_job(self, job):
        if job.status != job.Status.ACTIVE:
            raise serializers.ValidationError("This job is not accepting applications.")
        if Application.objects.filter(job=job, applicant=self.context["request"].user).exists():
            raise serializers.ValidationError("You have already applied to this job.")
        return job


class ApplicationListSerializer(serializers.ModelSerializer):
    job = JobListSerializer(read_only=True)
    applicant_name = serializers.CharField(source="applicant.display_name", read_only=True)
    applicant_email = serializers.EmailField(source="applicant.email", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    badge_class = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = [
            "id", "job", "applicant", "applicant_name", "applicant_email",
            "cover_letter", "expected_salary", "notice_period", "additional_info",
            "status", "status_display", "badge_class", "recruiter_note",
            "applied_at", "updated_at",
        ]
        read_only_fields = fields

    def get_badge_class(self, obj):
        return obj.badge_class_for(obj.status)


class ApplicationStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Application.Status.choices)
    note = serializers.CharField(required=False, allow_blank=True, default="")
