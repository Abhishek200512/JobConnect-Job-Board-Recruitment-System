"""Public home pages and role dashboards with Chart.js analytics."""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from datetime import date
from django.views.decorators.http import require_POST


def _json_err(message, status=400):
    return JsonResponse({"success": False, "error": message}, status=status)


def admin_json_action(view):
    """POST-only admin JSON action with auth checks returning JSON errors."""

    @wraps(view)
    @require_POST
    @login_required
    def _wrapped(request, *args, **kwargs):
        if request.user.role != "admin":
            return _json_err("Unauthorized", status=403)
        return view(request, *args, **kwargs)

    return _wrapped

from accounts.models import User, JobSeekerProfile
from accounts.utils import role_required
from applications.models import Application, SavedJob
from companies.models import Company
from jobs.models import Job, Category
from notifications.models import Notification

from .models import ContactMessage


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------
def home(request):
    jobs = Job.active_jobs().select_related("company", "category")
    context = {
        "featured_jobs": jobs.order_by("-created_at")[:6],
        "categories": Category.objects.all()[:8],
        "top_companies": Company.objects.annotate(n=Count("jobs", filter=Q(jobs__status="active"))).order_by("-n")[:8],
        "stats": {
            "jobs": jobs.count(),
            "companies": Company.objects.count(),
            "seekers": User.objects.filter(role=User.Role.SEEKER).count(),
            "hired": Application.objects.filter(status=Application.Status.SELECTED).count(),
        },
    }
    return render(request, "dashboard/home.html", context)


def about(request):
    return render(request, "dashboard/about.html")


def contact(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        subject = request.POST.get("subject", "").strip()
        message = request.POST.get("message", "").strip()
        if not all([name, email, subject, message]):
            messages.error(request, "All fields are required.")
        else:
            ContactMessage.objects.create(name=name, email=email, subject=subject, message=message)
            messages.success(request, "Thanks for reaching out! Our team will get back to you soon.")
            return redirect("contact")
    return render(request, "dashboard/contact.html")


def job_seeker_landing(request):
    return redirect("job_list")


def error_404(request, exception=None):
    return render(request, "dashboard/404.html", status=404)


def error_500(request):
    return render(request, "dashboard/404.html", {"is_500": True}, status=500)


# ---------------------------------------------------------------------------
# Job seeker dashboard
# ---------------------------------------------------------------------------
@role_required("seeker")
def seeker_dashboard(request):
    apps = Application.objects.filter(applicant=request.user).select_related("job", "job__company")
    counts = {
        "applied": apps.count(),
        "saved": SavedJob.objects.filter(user=request.user).count(),
        "under_review": apps.filter(status=Application.Status.UNDER_REVIEW).count(),
        "shortlisted": apps.filter(status=Application.Status.SHORTLISTED).count(),
        "interviews": apps.filter(status=Application.Status.INTERVIEW).count(),
        "selected": apps.filter(status=Application.Status.SELECTED).count(),
    }

    # Last 6 months activity
    months, applied_series, status_series = [], [], []
    today = date.today()
    for i in range(5, -1, -1):
        m = (today.month - i - 1) % 12 + 1
        y = today.year + (today.month - i - 1) // 12
        start = date(y, m, 1)
        months.append(start.strftime("%b"))
        applied_series.append(apps.filter(applied_at__year=y, applied_at__month=m).count())
        selected_qs = apps.filter(status=Application.Status.SELECTED, updated_at__year=y, updated_at__month=m)
        status_series.append(selected_qs.count())

    return render(request, "dashboard/seeker/dashboard.html", {
        "counts": counts,
        "recent_applications": apps[:6],
        "chart": {"labels": months, "applied": applied_series, "selected": status_series},
        "recommended_jobs": Job.active_jobs().select_related("company")[:5],
    })


# ---------------------------------------------------------------------------
# Recruiter dashboard
# ---------------------------------------------------------------------------
@role_required("recruiter")
def recruiter_dashboard(request):
    jobs = Job.objects.filter(posted_by=request.user)
    apps = Application.objects.filter(job__posted_by=request.user).select_related("job", "applicant", "job__company")

    counts = {
        "total_jobs": jobs.count(),
        "active_jobs": jobs.filter(status=Job.Status.ACTIVE).count(),
        "applicants": apps.count(),
        "shortlisted": apps.filter(status=Application.Status.SHORTLISTED).count(),
        "interviews": apps.filter(status=Application.Status.INTERVIEW).count(),
        "selected": apps.filter(status=Application.Status.SELECTED).count(),
    }

    # Applications per month (last 6)
    today = date.today()
    months, app_series = [], []
    for i in range(5, -1, -1):
        m = (today.month - i - 1) % 12 + 1
        y = today.year + (today.month - i - 1) // 12
        months.append(date(y, m, 1).strftime("%b"))
        app_series.append(apps.filter(applied_at__year=y, applied_at__month=m).count())

    # Jobs by category
    by_cat = jobs.values("category__name").annotate(n=Count("id")).order_by("-n")[:8]
    # Status distribution
    by_status = apps.values("status").annotate(n=Count("id"))

    recent = apps.order_by("-applied_at")[:6]
    return render(request, "dashboard/recruiter/dashboard.html", {
        "counts": counts,
        "recent_applications": recent,
        "my_jobs": jobs.order_by("-created_at")[:5],
        "chart": {
            "months": months,
            "applications": app_series,
            "categories": [r["category__name"] or "Other" for r in by_cat],
            "category_counts": [r["n"] for r in by_cat],
            "status_labels": [Application.Status(s["status"]).label for s in by_status],
            "status_counts": [s["n"] for s in by_status],
        },
    })


# ---------------------------------------------------------------------------
# Admin dashboard
# ---------------------------------------------------------------------------
@role_required("admin")
def admin_dashboard(request):
    users = User.objects.all()
    jobs = Job.objects.all()
    apps = Application.objects.all()

    counts = {
        "users": users.count(),
        "seekers": users.filter(role=User.Role.SEEKER).count(),
        "recruiters": users.filter(role=User.Role.RECRUITER).count(),
        "companies": Company.objects.count(),
        "jobs": jobs.count(),
        "active_jobs": jobs.filter(status=Job.Status.ACTIVE).count(),
        "applications": apps.count(),
        "selected": apps.filter(status=Application.Status.SELECTED).count(),
    }

    today = date.today()
    months, reg_series, jobs_series, apps_series = [], [], [], []
    for i in range(5, -1, -1):
        m = (today.month - i - 1) % 12 + 1
        y = today.year + (today.month - i - 1) // 12
        months.append(date(y, m, 1).strftime("%b"))
        reg_series.append(users.filter(created_at__year=y, created_at__month=m).count())
        jobs_series.append(jobs.filter(created_at__year=y, created_at__month=m).count())
        apps_series.append(apps.filter(applied_at__year=y, applied_at__month=m).count())

    by_cat = jobs.values("category__name").annotate(n=Count("id")).order_by("-n")[:8]
    by_status = apps.values("status").annotate(n=Count("id"))

    return render(request, "dashboard/admin/dashboard.html", {
        "counts": counts,
        "recent_users": users.order_by("-created_at")[:6],
        "recent_applications": apps.select_related("job", "applicant")[:6],
        "chart": {
            "months": months,
            "registrations": reg_series,
            "jobs_created": jobs_series,
            "applications": apps_series,
            "categories": [r["category__name"] or "Other" for r in by_cat],
            "category_counts": [r["n"] for r in by_cat],
            "status_labels": [Application.Status(s["status"]).label for s in by_status],
            "status_counts": [s["n"] for s in by_status],
        },
    })


# ---------------------------------------------------------------------------
# Admin management pages
# ---------------------------------------------------------------------------
@role_required("admin")
def admin_users(request):
    role = request.GET.get("role", "")
    q = request.GET.get("q", "").strip()
    users = User.objects.all().order_by("-created_at")
    if role:
        users = users.filter(role=role)
    if q:
        users = users.filter(Q(email__icontains=q) | Q(username__icontains=q) | Q(full_name__icontains=q))
    return render(request, "dashboard/admin/users.html", {
        "users": users, "roles": User.Role.choices, "current_role": role, "current_q": q,
    })


@admin_json_action
def admin_toggle_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user.is_superuser:
        return _json_err("Cannot deactivate a superuser.")
    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])
    return JsonResponse({"success": True, "is_active": user.is_active,
                         "message": f"{user.email} {'activated' if user.is_active else 'deactivated'}."})


@role_required("admin")
def admin_companies(request):
    q = request.GET.get("q", "").strip()
    companies = Company.objects.all().order_by("company_name")
    if q:
        companies = companies.filter(Q(company_name__icontains=q) | Q(industry__icontains=q) | Q(location__icontains=q))
    return render(request, "dashboard/admin/companies.html", {"companies": companies, "current_q": q})


@admin_json_action
def admin_delete_company(request, pk):
    company = get_object_or_404(Company, pk=pk)
    name = company.company_name
    company.delete()
    return JsonResponse({"success": True, "message": f"Company “{name}” deleted."})


@role_required("admin")
def admin_jobs(request):
    status = request.GET.get("status", "")
    q = request.GET.get("q", "").strip()
    jobs = Job.objects.select_related("company", "category").order_by("-created_at")
    if status:
        jobs = jobs.filter(status=status)
    if q:
        jobs = jobs.filter(Q(title__icontains=q) | Q(company__company_name__icontains=q))
    return render(request, "dashboard/admin/jobs.html", {
        "jobs": jobs, "statuses": Job.Status.choices, "current_status": status, "current_q": q,
    })


@admin_json_action
def admin_toggle_job(request, pk):
    job = get_object_or_404(Job, pk=pk)
    job.status = Job.Status.INACTIVE if job.status == Job.Status.ACTIVE else Job.Status.ACTIVE
    job.save(update_fields=["status"])
    return JsonResponse({"success": True, "status": job.status,
                         "message": f"Job “{job.title}” is now {job.get_status_display().lower()}."})


@admin_json_action
def admin_delete_job(request, pk):
    job = get_object_or_404(Job, pk=pk)
    title = job.title
    job.delete()
    return JsonResponse({"success": True, "message": f"Job “{title}” deleted."})


@role_required("admin")
def admin_applications(request):
    status = request.GET.get("status", "")
    q = request.GET.get("q", "").strip()
    apps = Application.objects.select_related("job", "applicant", "job__company").order_by("-applied_at")
    if status:
        apps = apps.filter(status=status)
    if q:
        apps = apps.filter(Q(applicant__email__icontains=q) | Q(job__title__icontains=q))
    return render(request, "dashboard/admin/applications.html", {
        "applications": apps, "statuses": Application.Status.choices, "current_status": status, "current_q": q,
    })


@role_required("admin")
def admin_reports(request):
    """Monthly series built with month/year filtering (no SQL tz conversion —
    MariaDB servers without timezone tables would fail on TruncMonth)."""
    jobs_by_cat = list(Job.objects.values("category__name").annotate(n=Count("id")).order_by("-n")[:10])

    today = date.today()
    apps_by_month = []
    for i in range(5, -1, -1):
        m = (today.month - i - 1) % 12 + 1
        y = today.year + (today.month - i - 1) // 12
        n = Application.objects.filter(applied_at__year=y, applied_at__month=m).count()
        apps_by_month.append({"label": date(y, m, 1).strftime("%b %y"), "n": n})

    by_status = list(Application.objects.values("status").annotate(n=Count("id")))
    top_companies = list(Company.objects.annotate(n=Count("jobs")).order_by("-n")[:8])
    return render(request, "dashboard/admin/reports.html", {
        "jobs_by_cat": jobs_by_cat,
        "apps_by_month": apps_by_month,
        "by_status": by_status,
        "status_labels": [Application.Status(s["status"]).label for s in by_status],
        "top_companies": top_companies,
    })
