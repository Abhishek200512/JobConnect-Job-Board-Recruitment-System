"""Custom User model, email OTP verification and job-seeker profile."""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid
import os


def seeker_photo_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"photos/seeker_{instance.user_id}_{uuid.uuid4().hex[:8]}{ext}"


def seeker_resume_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"resumes/seeker_{instance.user_id}_{uuid.uuid4().hex[:8]}{ext}"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("role", User.Role.ADMIN)
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("is_verified", True)
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    """Single user table for all three roles."""

    class Role(models.TextChoices):
        SEEKER = "seeker", "Job Seeker"
        RECRUITER = "recruiter", "Recruiter"
        ADMIN = "admin", "Admin"

    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(max_length=60, unique=True)
    full_name = models.CharField(max_length=120, blank=True)
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.SEEKER, db_index=True)
    phone = models.CharField(max_length=15, blank=True)

    is_active = models.BooleanField(default=True, db_index=True)
    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        indexes = [
            models.Index(fields=["role", "is_active"]),
        ]

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    # ------------------------------------------------------------------
    @property
    def is_seeker(self):
        return self.role == self.Role.SEEKER

    @property
    def is_recruiter(self):
        return self.role == self.Role.RECRUITER

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    @property
    def display_name(self):
        return self.full_name or self.username

    def get_short_name(self):
        return self.display_name


class OTPVerification(models.Model):
    """Email OTP for account verification and password reset."""

    class Purpose(models.TextChoices):
        VERIFY = "verify", "Account verification"
        RESET = "reset", "Password reset"

    email = models.EmailField(db_index=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name="otps")
    otp = models.CharField(max_length=6)
    purpose = models.CharField(max_length=10, choices=Purpose.choices, default=Purpose.VERIFY)
    expires_at = models.DateTimeField()
    verified = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["email", "purpose"])]

    def __str__(self):
        return f"OTP for {self.email} ({self.purpose})"

    @classmethod
    def generate(cls, email, purpose, user=None):
        """Create a fresh OTP, invalidating older ones for the same email/purpose."""
        import secrets

        cls.objects.filter(email__iexact=email, purpose=purpose, verified=False).delete()
        return cls.objects.create(
            email=email.lower(),
            user=user,
            otp=f"{secrets.randbelow(10 ** 6):06d}",
            purpose=purpose,
            expires_at=timezone.now() + timedelta(minutes=10),
        )

    def is_valid(self):
        return (not self.verified) and self.attempts < 5 and timezone.now() <= self.expires_at


class JobSeekerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="seeker_profile")
    full_name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    profile_photo = models.ImageField(upload_to=seeker_photo_path, null=True, blank=True)
    resume = models.FileField(upload_to=seeker_resume_path, null=True, blank=True)
    headline = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=120, blank=True)
    website = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    github = models.URLField(blank=True)
    expected_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    experience_years = models.PositiveSmallIntegerField(default=0)
    skills = models.JSONField(default=list, blank=True)          # ["Python", "Django", ...]
    education = models.JSONField(default=list, blank=True)       # [{degree, institution, year}]
    experience = models.JSONField(default=list, blank=True)      # [{title, company, duration}]
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.display_name}"
