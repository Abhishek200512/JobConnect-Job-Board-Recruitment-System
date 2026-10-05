"""Application and SavedJob models."""
from django.conf import settings
from django.db import models
import os
import uuid


def application_resume_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"resumes/app_{instance.applicant_id or 'new'}_{uuid.uuid4().hex[:8]}{ext}"


class Application(models.Model):
    class Status(models.TextChoices):
        APPLIED = "applied", "Applied"
        UNDER_REVIEW = "under_review", "Under Review"
        SHORTLISTED = "shortlisted", "Shortlisted"
        INTERVIEW = "interview", "Interview"
        SELECTED = "selected", "Selected"
        REJECTED = "rejected", "Rejected"

    STATUS_ORDER = ["applied", "under_review", "shortlisted", "interview", "selected"]

    _BADGES = {
        "applied": "badge-soft-secondary",
        "under_review": "badge-soft-info",
        "shortlisted": "badge-soft-warning",
        "interview": "badge-soft-purple",
        "selected": "badge-soft-success",
        "rejected": "badge-soft-danger",
    }

    job = models.ForeignKey("jobs.Job", on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications"
    )
    resume = models.FileField(upload_to=application_resume_path, null=True, blank=True)
    cover_letter = models.TextField(blank=True)
    expected_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notice_period = models.CharField(max_length=50, blank=True)
    additional_info = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.APPLIED, db_index=True)
    recruiter_note = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-applied_at"]
        unique_together = [("job", "applicant")]
        indexes = [models.Index(fields=["status", "applied_at"])]

    def __str__(self):
        return f"{self.applicant.display_name} → {self.job.title}"

    # -- status pipeline ------------------------------------------------
    def next_status(self):
        try:
            i = self.STATUS_ORDER.index(self.status)
        except ValueError:
            return None
        return self.STATUS_ORDER[i + 1] if i + 1 < len(self.STATUS_ORDER) else None

    def status_index(self):
        try:
            return self.STATUS_ORDER.index(self.status)
        except ValueError:
            return -1

    def timeline(self):
        """Ordered pipeline for progress display; rejected flagged separately."""
        return [
            {"key": s, "label": self.Status(s).label, "done": self.status_index() >= i}
            for i, s in enumerate(self.STATUS_ORDER)
        ]

    @property
    def badge_class(self):
        return Application._BADGES.get(self.status, "badge-soft-secondary")

    @staticmethod
    def badge_class_for(status):
        return Application._BADGES.get(status, "badge-soft-secondary")


class SavedJob(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_jobs")
    job = models.ForeignKey("jobs.Job", on_delete=models.CASCADE, related_name="saved_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "job")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} saved {self.job}"
