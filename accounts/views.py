"""Authentication & account views."""
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from applications.models import Application, SavedJob
from companies.models import Company
from jobs.models import Job, Category
from notifications.models import Notification

from .models import User, JobSeekerProfile, OTPVerification
from .utils import role_required, send_otp_email, validate_upload, ROLE_HOME


# ---------------------------------------------------------------------------
# Registration (seeker & recruiter) with email OTP
# ---------------------------------------------------------------------------
def register(request):
    if request.user.is_authenticated:
        return redirect(ROLE_HOME.get(request.user.role, "home"))

    if request.method == "POST":
        role = request.POST.get("role", "seeker")
        full_name = request.POST.get("full_name", "").strip()
        username = request.POST.get("username", "").strip().lower()
        email = request.POST.get("email", "").strip().lower()
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")
        company_name = request.POST.get("company_name", "").strip()

        ctx = {"form": request.POST, "role": role}

        if not all([full_name, username, email, password]):
            return render(request, "accounts/register.html", {**ctx, "error": "All required fields must be filled."})
        try:
            validate_email(email)
        except ValidationError:
            return render(request, "accounts/register.html", {**ctx, "error": "Please enter a valid email address."})
        if len(password) < 8:
            return render(request, "accounts/register.html", {**ctx, "error": "Password must be at least 8 characters."})
        if password != password2:
            return render(request, "accounts/register.html", {**ctx, "error": "Passwords do not match."})
        if User.objects.filter(email__iexact=email).exists():
            return render(request, "accounts/register.html", {**ctx, "error": "An account with this email already exists."})
        if User.objects.filter(username__iexact=username).exists():
            return render(request, "accounts/register.html", {**ctx, "error": "That username is already taken."})

        user = User.objects.create_user(
            email=email, password=password, username=username,
            full_name=full_name, phone=phone,
            role=User.Role.RECRUITER if role == "recruiter" else User.Role.SEEKER,
            is_active=True, is_verified=False,
        )
        if user.is_seeker:
            JobSeekerProfile.objects.create(user=user, full_name=full_name, phone=phone)
        else:
            Company.objects.create(recruiter=user, company_name=company_name or f"{full_name}'s Company")

        otp = OTPVerification.generate(email=email, purpose=OTPVerification.Purpose.VERIFY, user=user)
        send_otp_email(email, otp.otp, "verify")

        request.session["pending_verify_email"] = email
        messages.success(request, "Account created! We sent a 6-digit verification code to your email.")
        return redirect("verify_otp")

    return render(request, "accounts/register.html")


def verify_otp(request):
    """Verify the 6-digit code sent to the user's email."""
    email = request.session.get("pending_verify_email")
    if not email:
        messages.info(request, "No pending verification. Please register or login.")
        return redirect("login")

    pending = User.objects.filter(email__iexact=email, is_verified=False).first()
    if request.method == "POST":
        code = "".join(request.POST.get(f"otp{i}", "") for i in range(1, 7)).strip()
        otp = OTPVerification.objects.filter(email__iexact=email, purpose=OTPVerification.Purpose.VERIFY).order_by("-created_at").first()

        if not pending:
            messages.error(request, "Account not found.")
            return redirect("register")
        if not otp or not otp.is_valid():
            messages.error(request, "Invalid or expired code. Please request a new one.")
            return redirect("verify_otp")
        if otp.otp != code:
            otp.attempts += 1
            otp.save(update_fields=["attempts"])
            messages.error(request, f"Incorrect code. {max(0, 5 - otp.attempts)} attempts remaining.")
            return redirect("verify_otp")

        otp.verified = True
        otp.save(update_fields=["verified"])
        pending.is_verified = True
        pending.save(update_fields=["is_verified"])
        Notification.notify(
            pending, "Welcome to JobConnect 🎉",
            "Your email is verified. Complete your profile to get the best matches.",
            url="/dashboard/",
        )
        request.session.pop("pending_verify_email", None)
        login(request, pending)
        messages.success(request, "Email verified — welcome aboard!")
        return redirect(ROLE_HOME.get(pending.role, "home"))

    return render(request, "accounts/verify_otp.html", {"email": email})


def resend_otp(request):
    email = request.session.get("pending_verify_email")
    if email:
        otp = OTPVerification.generate(email=email, purpose=OTPVerification.Purpose.VERIFY)
        send_otp_email(email, otp.otp, "verify")
        messages.success(request, "A new verification code was sent.")
    return redirect("verify_otp")


# ---------------------------------------------------------------------------
# Login / logout
# ---------------------------------------------------------------------------
def login_view(request):
    if request.user.is_authenticated:
        return redirect(ROLE_HOME.get(request.user.role, "home"))

    if request.method == "POST":
        identifier = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        user = User.objects.filter(email__iexact=identifier).first() or User.objects.filter(username__iexact=identifier).first()

        if user and user.check_password(password):
            if not user.is_active:
                return render(request, "accounts/login.html", {"error": "Your account has been deactivated. Contact support."})
            if not user.is_verified:
                request.session["pending_verify_email"] = user.email
                otp = OTPVerification.generate(email=user.email, purpose=OTPVerification.Purpose.VERIFY, user=user)
                send_otp_email(user.email, otp.otp, "verify")
                messages.info(request, "Please verify your email first — we sent you a fresh code.")
                return redirect("verify_otp")

            login(request, user)
            messages.success(request, f"Welcome back, {user.display_name}!")
            nxt = request.GET.get("next") or request.POST.get("next")
            return redirect(nxt or ROLE_HOME.get(user.role, "home"))

        return render(request, "accounts/login.html", {"error": "Invalid email or password."})

    return render(request, "accounts/login.html")


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("home")


# ---------------------------------------------------------------------------
# Forgot / reset password (OTP-based)
# ---------------------------------------------------------------------------
def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return render(request, "accounts/forgot_password.html", {"error": "No account found with that email."})
        otp = OTPVerification.generate(email=email, purpose=OTPVerification.Purpose.RESET, user=user)
        send_otp_email(email, otp.otp, "reset")
        request.session["reset_email"] = email
        messages.success(request, "Password reset code sent to your email.")
        return redirect("reset_password")
    return render(request, "accounts/forgot_password.html")


def reset_password(request):
    email = request.session.get("reset_email")
    if not email:
        messages.info(request, "Please start the password reset process again.")
        return redirect("forgot_password")

    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        p1 = request.POST.get("password", "")
        p2 = request.POST.get("password2", "")
        otp = OTPVerification.objects.filter(email__iexact=email, purpose=OTPVerification.Purpose.RESET).order_by("-created_at").first()

        if not otp or not otp.is_valid() or otp.otp != code:
            return render(request, "accounts/reset_password.html", {"error": "Invalid or expired code."})
        if len(p1) < 8:
            return render(request, "accounts/reset_password.html", {"error": "Password must be at least 8 characters."})
        if p1 != p2:
            return render(request, "accounts/reset_password.html", {"error": "Passwords do not match."})

        user = User.objects.filter(email__iexact=email).first()
        user.set_password(p1)
        user.is_verified = True
        user.save()
        otp.verified = True
        otp.save()
        request.session.pop("reset_email", None)
        messages.success(request, "Password updated — you can login now.")
        return redirect("login")

    return render(request, "accounts/reset_password.html", {"email": email})


# ---------------------------------------------------------------------------
# Seeker profile management
# ---------------------------------------------------------------------------
def _handle_photo(form_files, profile):
    photo = form_files.get("photo")
    if not photo:
        return True
    ok, err = validate_upload(photo, "image")
    if not ok:
        return err
    if profile.profile_photo:
        profile.profile_photo.delete(save=False)
    profile.profile_photo = photo
    return True


def _handle_resume(form_files, profile):
    resume = form_files.get("resume")
    if not resume:
        return True
    ok, err = validate_upload(resume, "resume")
    if not ok:
        return err
    if profile.resume:
        profile.resume.delete(save=False)
    profile.resume = resume
    return True


def _parse_json_field(raw, expect_list=True):
    import json

    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except (ValueError, TypeError):
        return []


@login_required
def profile_view(request):
    if not request.user.is_seeker:
        return redirect(ROLE_HOME.get(request.user.role, "home"))
    profile, _ = JobSeekerProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        location = request.POST.get("location", "").strip()
        headline = request.POST.get("headline", "").strip()
        bio = request.POST.get("bio", "").strip()
        website = request.POST.get("website", "").strip()
        linkedin = request.POST.get("linkedin", "").strip()
        github = request.POST.get("github", "").strip()
        exp_years = request.POST.get("experience_years", "0") or "0"

        if not full_name:
            messages.error(request, "Full name is required.")
            return redirect("profile")

        user = request.user
        user.full_name, user.phone = full_name, phone
        user.save(update_fields=["full_name", "phone"])

        profile.full_name, profile.phone = full_name, phone
        profile.location, profile.headline, profile.bio = location, headline, bio
        profile.website, profile.linkedin, profile.github = website, linkedin, github
        try:
            profile.experience_years = max(0, int(exp_years))
        except ValueError:
            profile.experience_years = 0

        photo_result = _handle_photo(request.FILES, profile)
        if photo_result is not True:
            messages.error(request, photo_result)
            return redirect("profile")
        resume_result = _handle_resume(request.FILES, profile)
        if resume_result is not True:
            messages.error(request, resume_result)
            return redirect("profile")

        profile.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("profile")

    return render(request, "dashboard/seeker/profile.html", {"profile": profile})


@login_required
@role_required("seeker")
def skills_education_view(request):
    """Skills / education / experience management (JSON-backed sections)."""
    profile, _ = JobSeekerProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        section = request.POST.get("section")
        if section == "skills":
            skills = [s.strip() for s in request.POST.get("skills", "").split(",") if s.strip()]
            profile.skills = skills[:30]
            profile.save(update_fields=["skills"])
            messages.success(request, "Skills updated.")
        elif section == "education":
            entries = _parse_json_field(request.POST.get("education_json", ""))
            profile.education = entries[:10]
            profile.save(update_fields=["education"])
            messages.success(request, "Education updated.")
        elif section == "experience":
            entries = _parse_json_field(request.POST.get("experience_json", ""))
            profile.experience = entries[:10]
            profile.save(update_fields=["experience"])
            messages.success(request, "Experience updated.")
        return redirect("profile_sections")

    return render(request, "dashboard/seeker/sections.html", {"profile": profile})


@login_required
@role_required("seeker")
def seeker_settings(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "change_password":
            p1, p2 = request.POST.get("password", ""), request.POST.get("password2", "")
            if len(p1) < 8:
                messages.error(request, "New password must be at least 8 characters.")
            elif p1 != p2:
                messages.error(request, "Passwords do not match.")
            else:
                request.user.set_password(p1)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, "Password changed.")
        return redirect("seeker_settings")

    return render(request, "dashboard/seeker/settings.html")


def public_profile(request, pk):
    """Recruiter-visible seeker profile."""
    seeker = get_object_or_404(User, pk=pk, role=User.Role.SEEKER)
    profile = JobSeekerProfile.objects.filter(user=seeker).first()
    return render(request, "dashboard/seeker/public_profile.html", {"seeker": seeker, "profile": profile})
