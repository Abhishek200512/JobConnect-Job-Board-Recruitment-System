"""Job browsing and recruiter job management views."""
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.http import require_POST

from accounts.utils import role_required
from applications.models import Application, SavedJob
from companies.models import Company
from notifications.models import Notification

from .models import Job, Category
from .forms import JobForm

JOB_TYPES = Job.JobType
WORK_MODES = Job.WorkMode
EXPERIENCES = Job.Experience


def _filtered_jobs(request):
    """Shared query builder for HTML and JSON job lists (all filters + sorting)."""
    GET = request.GET
    qs = Job.active_jobs().select_related("company", "category")

    keyword = GET.get("keyword", "").strip()
    if keyword:
        qs = qs.filter(
            Q(title__icontains=keyword) |
            Q(skills__icontains=keyword) |
            Q(description__icontains=keyword) |
            Q(company__company_name__icontains=keyword)
        )

    location = GET.get("location", "").strip()
    if location and location.lower() != "all":
        qs = qs.filter(location__icontains=location)

    category = GET.get("category", "")
    if category:
        qs = qs.filter(category__slug=category)

    job_type = GET.get("job_type", "")
    if job_type:
        qs = qs.filter(job_type=job_type)

    work_mode = GET.get("work_mode", "")
    if work_mode:
        qs = qs.filter(work_mode=work_mode)

    experience = GET.get("experience", "")
    if experience:
        qs = qs.filter(experience=experience)

    company = GET.get("company", "")
    if company:
        qs = qs.filter(company_id=company)

    salary_min = GET.get("min_salary", "")
    if salary_min:
        try:
            qs = qs.filter(salary_max__gte=float(salary_min))
        except ValueError:
            pass

    salary_max = GET.get("max_salary", "")
    if salary_max:
        try:
            qs = qs.filter(salary_min__lte=float(salary_max))
        except ValueError:
            pass

    posted_within = GET.get("posted_within", "")
    if posted_within:
        try:
            days = int(posted_within)
            qs = qs.filter(created_at__gte=timezone.now() - timedelta(days=days))
        except (ValueError, TypeError):
            pass

    allowed_orders = {
        "-created_at": "-created_at",
        "created_at": "created_at",
        "-salary_max": "-salary_max",
        "salary_min": "salary_min",
    }
    ordering = GET.get("ordering", "-created_at")
    return qs.order_by(allowed_orders.get(ordering, "-created_at"))


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------
def job_list(request):
    qs = _filtered_jobs(request)
    paginator = Paginator(qs, 9)
    page = paginator.get_page(request.GET.get("page"))

    saved_ids = []
    if request.user.is_authenticated and request.user.is_seeker:
        saved_ids = list(SavedJob.objects.filter(user=request.user, job__in=page.object_list).values_list("job_id", flat=True))

    return render(request, "jobs/job_list.html", {
        "page_obj": page,
        "jobs": page.object_list,
        "saved_ids": saved_ids,
        "categories": Category.objects.all(),
        "companies": Company.objects.order_by("company_name"),
        "total_results": paginator.count,
        "job_types": JOB_TYPES.choices,
        "work_modes": WORK_MODES.choices,
        "experiences": EXPERIENCES.choices,
        "current_filters": request.GET,
    })


def jobs_ajax(request):
    """AJAX endpoint returning job cards + pagination as rendered HTML."""
    qs = _filtered_jobs(request)
    paginator = Paginator(qs, 9)
    page = paginator.get_page(request.GET.get("page"))

    from django.template.loader import render_to_string
    html = render_to_string("jobs/_job_cards.html", {"jobs": page.object_list, "page_obj": page}, request=request)
    saved_ids = []
    if request.user.is_authenticated and request.user.is_seeker:
        saved_ids = sorted(SavedJob.objects.filter(user=request.user, job__in=page.object_list).values_list("job_id", flat=True))
    return JsonResponse({
        "success": True,
        "html": html,
        "total": paginator.count,
        "num_pages": paginator.num_pages,
        "page": page.number,
        "saved_ids": saved_ids,
    })


def job_detail(request, pk):
    job = get_object_or_404(Job.objects.select_related("company", "category"), pk=pk, status=Job.Status.ACTIVE)
    job.views_count += 1
    job.save(update_fields=["views_count"])
    similar = Job.active_jobs().filter(category=job.category).exclude(pk=job.pk).select_related("company")[:4]
    has_applied = has_saved = False
    if request.user.is_authenticated and request.user.is_seeker:
        has_applied = Application.objects.filter(job=job, applicant=request.user).exists()
        has_saved = SavedJob.objects.filter(job=job, user=request.user).exists()

    return render(request, "jobs/job_detail.html", {
        "job": job,
        "similar_jobs": similar,
        "has_applied": has_applied,
        "has_saved": has_saved,
    })


# ---------------------------------------------------------------------------
# Save / unsave job (AJAX)
# ---------------------------------------------------------------------------
@require_POST
def toggle_save_job(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "login_required", "redirect": "/accounts/login/"}, status=401)
    if not request.user.is_seeker:
        return JsonResponse({"success": False, "error": "Only job seekers can save jobs."}, status=403)

    job = get_object_or_404(Job, pk=pk, status=Job.Status.ACTIVE)
    saved, created = SavedJob.objects.get_or_create(user=request.user, job=job)
    if not created:
        saved.delete()
        return JsonResponse({"success": True, "saved": False, "message": "Removed from saved jobs."})
    return JsonResponse({"success": True, "saved": True, "message": "Job saved!"})


# ---------------------------------------------------------------------------
# Recruiter job CRUD
# ---------------------------------------------------------------------------
@role_required("recruiter")
def manage_jobs(request):
    jobs = Job.objects.filter(posted_by=request.user).select_related("company", "category")
    q = request.GET.get("q", "").strip()
    if q:
        jobs = jobs.filter(Q(title__icontains=q) | Q(location__icontains=q))
    status = request.GET.get("status", "")
    if status:
        jobs = jobs.filter(status=status)

    return render(request, "dashboard/recruiter/manage_jobs.html", {
        "jobs": jobs,
        "statuses": Job.Status.choices,
    })


@role_required("recruiter")
def post_job(request):
    company = request.user.companies.first()
    if not company:
        messages.warning(request, "Please complete your company profile before posting a job.")
        return redirect("company_profile")

    if request.method == "POST":
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.company = company
            job.posted_by = request.user
            job.save()
            messages.success(request, f"Job “{job.title}” posted successfully.")
            return redirect("manage_jobs")
    else:
        form = JobForm()
    return render(request, "dashboard/recruiter/post_job.html", {"form": form, "company": company})


@role_required("recruiter")
def edit_job(request, pk):
    job = get_object_or_404(Job, pk=pk, posted_by=request.user)
    if request.method == "POST":
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, "Job updated successfully.")
            return redirect("manage_jobs")
    else:
        form = JobForm(instance=job)
    return render(request, "dashboard/recruiter/post_job.html", {"form": form, "company": job.company, "edit": True, "job": job})


@require_POST
def delete_job(request, pk):
    if not request.user.is_authenticated or not request.user.is_recruiter:
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)
    job = get_object_or_404(Job, pk=pk, posted_by=request.user)
    job.delete()
    return JsonResponse({"success": True, "message": "Job deleted."})


@require_POST
def toggle_job_status(request, pk):
    if not request.user.is_authenticated or not request.user.is_recruiter:
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)
    job = get_object_or_404(Job, pk=pk, posted_by=request.user)
    job.status = Job.Status.INACTIVE if job.status == Job.Status.ACTIVE else Job.Status.ACTIVE
    job.save(update_fields=["status"])
    return JsonResponse({"success": True, "status": job.status, "message": f"Job is now {job.get_status_display().lower()}."})
