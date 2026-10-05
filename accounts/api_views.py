"""Auth API views (session-authenticated where relevant)."""
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.models import Notification

from .models import OTPVerification, JobSeekerProfile
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    SeekerProfileSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
)
from .utils import send_otp_email

User = get_user_model()


class RegisterAPIView(generics.CreateAPIView):
    """POST /api/auth/register/ — creates a seeker or recruiter (unverified)."""
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        otp = OTPVerification.generate(email=user.email, purpose=OTPVerification.Purpose.VERIFY, user=user)
        send_otp_email(user.email, otp.otp, "verify")
        return Response(
            {"success": True, "message": "Account created. OTP sent to email for verification.", "user_id": user.id},
            status=status.HTTP_201_CREATED,
        )


class OTPRequestAPIView(APIView):
    """POST /api/auth/otp/request/ {"email": "..."} — sends a new verify OTP."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = OTPRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        email = s.validated_data["email"].lower()
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return Response({"success": False, "error": "No account with that email."}, status=404)
        otp = OTPVerification.generate(email=email, purpose=OTPVerification.Purpose.VERIFY, user=user)
        send_otp_email(email, otp.otp, "verify")
        return Response({"success": True, "message": "OTP sent."})


class OTPVerifyAPIView(APIView):
    """POST /api/auth/otp/verify/ {"email": "...", "code": "123456"}"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = OTPVerifySerializer(data=request.data)
        s.is_valid(raise_exception=True)
        email = s.validated_data["email"].lower()
        code = s.validated_data["code"]
        otp = OTPVerification.objects.filter(email__iexact=email, purpose=OTPVerification.Purpose.VERIFY).order_by("-created_at").first()
        user = User.objects.filter(email__iexact=email).first()

        if not otp or not user or not otp.is_valid() or otp.otp != code:
            return Response({"success": False, "error": "Invalid or expired code."}, status=400)

        otp.verified = True
        otp.save(update_fields=["verified"])
        user.is_verified = True
        user.save(update_fields=["is_verified"])
        Notification.notify(user, "Welcome to JobConnect 🎉", "Your email is verified.", url="/dashboard/")
        return Response({"success": True, "message": "Email verified."})


class LoginStatusAPIView(APIView):
    """GET /api/auth/login-status/ — current session user info."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"authenticated": False})
        return Response({"authenticated": True, "user": UserSerializer(request.user).data})


class SeekerListAPIView(generics.ListAPIView):
    """GET /api/users/seekers/?q= — recruiter/admin searchable seeker list."""
    serializer_class = SeekerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not (user.is_recruiter or user.is_admin_role):
            return JobSeekerProfile.objects.none()
        qs = JobSeekerProfile.objects.select_related("user")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(user__full_name__icontains=q) |
                Q(user__email__icontains=q) |
                Q(skills__icontains=q) |
                Q(location__icontains=q)
            )
        return qs
