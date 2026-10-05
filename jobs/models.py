"""Category and Job models."""
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    icon = models.CharField(max_length=10, blank=True, help_text="Bootstrap icon class or emoji")
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Job(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        CLOSED = "closed", "Closed"
        PENDING = "pending", "Pending Approval"

    class JobType(models.TextChoices):
        FULL_TIME = "full_time", "Full Time"
        PART_TIME = "part_time", "Part Time"
        INTERNSHIP = "internship", "Internship"
        CONTRACT = "contract", "Contract"

    class WorkMode(models.TextChoices):
        REMOTE = "remote", "Remote"
        HYBRID = "hybrid", "Hybrid"
        ONSITE = "onsite", "On-site"

    class Experience(models.TextChoices):
        FRESHER = "fresher", "Fresher"
        JUNIOR = "junior", "Junior (1-3 yrs)"
        MID = "mid", "Mid (3-5 yrs)"
        SENIOR = "senior", "Senior (5-8 yrs)"
        LEAD = "lead", "Lead (8+ yrs)"

    company = models.ForeignKey("companies.Company", on_delete=models.CASCADE, related_name="jobs")
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posted_jobs")

    title = models.CharField(max_length=150, db_index=True)
    slug = models.SlugField(max_length=170, blank=True)
    description = models.TextField()
    responsibilities = models.TextField(blank=True, help_text="One per line")
    qualifications = models.TextField(blank=True, help_text="One per line")
    benefits = models.TextField(blank=True, help_text="One per line")
    skills = models.JSONField(default=list, blank=True)  # ["Python", "SQL", ...]

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="jobs")
    location = models.CharField(max_length=120, db_index=True)
    job_type = models.CharField(max_length=12, choices=JobType.choices, default=JobType.FULL_TIME, db_index=True)
    work_mode = models.CharField(max_length=10, choices=WorkMode.choices, default=WorkMode.ONSITE, db_index=True)
    experience = models.CharField(max_length=10, choices=Experience.choices, default=Experience.FRESHER, db_index=True)

    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    openings = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE, db_index=True)

    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["job_type", "work_mode"]),
        ]

    def __str__(self):
        return f"{self.title} @ {self.company.company_name}"

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE

    @property
    def application_count(self):
        return self.applications.count()

    def salary_display(self):
        def fmt(v):
            v = float(v)
            return f"{v / 100000:.1f}".rstrip("0").rstrip(".") + " LPA" if v >= 100000 else f"{int(v):,}/mo"
        if self.salary_min and self.salary_max:
            return f"₹{fmt(self.salary_min)} – ₹{fmt(self.salary_max)}"
        if self.salary_min or self.salary_max:
            return f"₹{fmt(self.salary_min or self.salary_max)}"
        return "Not disclosed"

    def save(self, *args, **kwargs):
        from django.utils.text import slugify
        import uuid

        if not self.slug:
            base = slugify(self.title)[:140]
            self.slug = f"{base}-{uuid.uuid4().hex[:6]}"
        super().save(*args, **kwargs)

    @classmethod
    def active_jobs(cls):
        return cls.objects.filter(status=cls.Status.ACTIVE)

    def days_since_posted(self):
        return (timezone.now() - self.created_at).days

    def posted_display(self):
        d = self.days_since_posted()
        if d <= 0:
            return "Today"
        if d == 1:
            return "Yesterday"
        return f"{d} days ago"
