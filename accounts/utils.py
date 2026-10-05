"""Shared helpers: role-based access decorators, OTP emails, upload validation."""
from functools import wraps
import os

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.conf import settings

from notifications.models import Notification

ALLOWED_RESUME_EXTS = {".pdf", ".doc", ".docx"}
ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

ROLE_HOME = {
    "seeker": "seeker_dashboard",
    "recruiter": "recruiter_dashboard",
    "admin": "admin_dashboard",
}


def role_required(*roles):
    """View decorator: login required + role restriction with friendly message."""

    def decorator(view):
        @wraps(view)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if roles and request.user.role not in roles:
                messages.error(request, "You are not authorized to access that page.")
                return redirect(ROLE_HOME.get(request.user.role, "home"))
            return view(request, *args, **kwargs)

        return _wrapped

    return decorator


def send_otp_email(email, otp, purpose):
    subject = {
        "verify": "JobConnect — Verify your email",
        "reset": "JobConnect — Password reset code",
    }[purpose]
    message = (
        f"Hello,\n\nYour JobConnect verification code is: {otp}\n"
        f"It expires in 10 minutes.\n\nIf you did not request this, you can ignore this email.\n\n— JobConnect Team"
    )
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=True)
    except Exception:
        # Console backend or SMTP hiccup should never break registration UX.
        print(f"[JobConnect OTP] email={email} purpose={purpose} code={otp}")


def validate_upload(file, kind):
    """Validate uploaded file extension & size. Returns (ok, error_message)."""
    limits = {"resume": settings.MAX_RESUME_MB * 1024 * 1024, "image": settings.MAX_IMAGE_MB * 1024 * 1024}
    exts = ALLOWED_RESUME_EXTS if kind == "resume" else ALLOWED_IMAGE_EXTS
    max_bytes = limits[kind]

    ext = os.path.splitext(file.name)[1].lower()
    if ext not in exts:
        allowed = ", ".join(sorted(exts))
        return False, f"Invalid file type “{ext or file.name}”. Allowed: {allowed}"
    if file.size > max_bytes:
        return False, f"File too large ({file.size // 1024} KB). Max {max_bytes // (1024 * 1024)} MB."
    return True, ""
