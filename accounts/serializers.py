"""DRF serializers for accounts."""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import JobSeekerProfile

User = get_user_model()


class SeekerProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = JobSeekerProfile
        fields = [
            "id", "email", "username", "full_name", "phone", "profile_photo", "resume",
            "headline", "bio", "location", "website", "linkedin", "github",
            "expected_salary", "experience_years", "skills", "education", "experience",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class UserSerializer(serializers.ModelSerializer):
    seeker_profile = SeekerProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "full_name", "role", "phone",
            "is_active", "is_verified", "created_at", "seeker_profile",
        ]
        read_only_fields = fields


class RegisterSerializer(serializers.Serializer):
    """API registration (mirrors form logic)."""

    ROLE_CHOICES = (("seeker", "Job Seeker"), ("recruiter", "Recruiter"))

    email = serializers.EmailField()
    username = serializers.CharField(min_length=3, max_length=60)
    password = serializers.CharField(min_length=8, write_only=True)
    full_name = serializers.CharField(max_length=120)
    phone = serializers.CharField(max_length=15, required=False, allow_blank=True, default="")
    role = serializers.ChoiceField(choices=ROLE_CHOICES, default="seeker")
    company_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("That username is already taken.")
        return value.lower()

    def create(self, validated):
        from companies.models import Company
        from .models import JobSeekerProfile

        role = User.Role.RECRUITER if validated["role"] == "recruiter" else User.Role.SEEKER
        user = User.objects.create_user(
            email=validated["email"],
            password=validated["password"],
            username=validated["username"],
            full_name=validated["full_name"],
            phone=validated.get("phone", ""),
            role=role,
            is_verified=False,
        )
        if user.is_seeker:
            JobSeekerProfile.objects.create(user=user, full_name=validated["full_name"], phone=validated.get("phone", ""))
        else:
            Company.objects.create(recruiter=user, company_name=validated.get("company_name") or f"{validated['full_name']}'s Company")
        return user


class OTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(min_length=6, max_length=6)
