"""Application views for seekers and recruiters."""
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, FileResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST, require_GET

from accounts.utils import role_required, validate_upload
from jobs.models import Job
from notifications.models import Notification

from .models import Application, SavedJob


# ---------------------------------------------------------------------------
# Job seeker
# ---------------------------------------------------------------------------
@role_required("seeker")
def apply_job(request, pk):
    job = get_object_or_404(Job, pk=pk, status=Job.Status.ACTIVE)

    if Application.objects.filter(job=job, applicant=request.user).exists():
        messages.info(request, "You have already applied to this job.")
        return redirect("job_detail", pk=job.pk)

    profile = getattr(request.user, "seeker_profile", None)

    if request.method == "POST":
        cover_letter = request.POST.get("cover_letter", "").strip()
        expected_salary = request.POST.get("expected_salary") or None
        notice_period = request.POST.get("notice_period", "").strip()
        additional_info = request.POST.get("additional_info", "").strip()
        resume = request.FILES.get("resume")

        if resume is None and (not profile or not profile.resume):
            messages.error(request, "Please upload a resume (or add one to your profile first).")
            return redirect("apply_job", pk=job.pk)
        if resume is not None:
            ok, err = validate_upload(resume, "resume")
            if not ok:
                messages.error(request, err)
                return redirect("apply_job", pk=job.pk)

        Application.objects.create(
            job=job,
            applicant=request.user,
            resume=resume or None,
            cover_letter=cover_letter,
            expected_salary=expected_salary or None,
            notice_period=notice_period,
            additional_info=additional_info,
        )
        # Notify recruiter
        Notification.notify(
            job.posted_by,
            "New application received",
            f"{request.user.display_name} applied for {job.title}.",
            url=f"/applications/manage/{job.pk}/",
        )
        messages.success(request, "Application submitted successfully! Track its status from your dashboard.")
        return redirect("applied_jobs")

    return render(request, "applications/apply.html", {"job": job, "profile": profile})


@role_required("seeker")
def applied_jobs(request):
    apps = Application.objects.filter(applicant=request.user).select_related("job", "job__company")
    status_filter = request.GET.get("status", "")
    if status_filter:
        apps = apps.filter(status=status_filter)
    return render(request, "dashboard/seeker/applied_jobs.html", {
        "applications": apps,
        "statuses": Application.Status.choices,
        "current_status": status_filter,
    })


@role_required("seeker")
def saved_jobs(request):
    saved = SavedJob.objects.filter(user=request.user).select_related("job", "job__company", "job__category")
    return render(request, "dashboard/seeker/saved_jobs.html", {"saved_jobs": saved})


@require_POST
def withdraw_application(request, pk):
    if not request.user.is_authenticated or not request.user.is_seeker:
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)
    app = get_object_or_404(Application, pk=pk, applicant=request.user)
    if app.status not in (Application.Status.APPLIED, Application.Status.UNDER_REVIEW):
        return JsonResponse({"success": False, "error": "Application can no longer be withdrawn."}, status=400)
    app.delete()
    return JsonResponse({"success": True, "message": "Application withdrawn."})


# ---------------------------------------------------------------------------
# Recruiter
# ---------------------------------------------------------------------------
@role_required("recruiter")
def applicants(request):
    """All applicants across the recruiter's jobs, with filters."""
    apps = Application.objects.filter(job__posted_by=request.user).select_related("job", "job__company", "applicant")
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    job_id = request.GET.get("job", "")

    if q:
        apps = apps.filter(
            Q(applicant__full_name__icontains=q) |
            Q(applicant__username__icontains=q) |
            Q(applicant__email__icontains=q) |
            Q(applicant__seeker_profile__skills__icontains=q)
        )
    if status:
        apps = apps.filter(status=status)
    if job_id:
        apps = apps.filter(job_id=job_id)

    my_jobs = Job.objects.filter(posted_by=request.user)
    return render(request, "dashboard/recruiter/applicants.html", {
        "applications": apps,
        "my_jobs": my_jobs,
        "statuses": Application.Status.choices,
        "current_q": q,
        "current_status": status,
        "current_job": job_id,
    })


@role_required("recruiter")
def job_applicants(request, pk):
    """Applicants for one specific job."""
    job = get_object_or_404(Job, pk=pk, posted_by=request.user)
    apps = Application.objects.filter(job=job).select_related("applicant")
    return render(request, "dashboard/recruiter/applicants.html", {
        "applications": apps,
        "job": job,
        "my_jobs": Job.objects.filter(posted_by=request.user),
        "statuses": Application.Status.choices,
        "current_job": str(job.pk),
    })


@require_POST
def update_status(request, pk):
    """Recruiter changes application status + notifies the applicant."""
    if not request.user.is_authenticated or not request.user.is_recruiter:
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    app = get_object_or_404(Application.objects.select_related("job", "job__company"), pk=pk, job__posted_by=request.user)
    new_status = request.POST.get("status", "")
    note = request.POST.get("note", "").strip()

    valid = [s[0] for s in Application.Status.choices]
    if new_status not in valid:
        return JsonResponse({"success": False, "error": "Invalid status."}, status=400)

    old = app.get_status_display()
    app.status = new_status
    if note:
        app.recruiter_note = note
    app.save()

    labels = dict(Application.Status.choices)
    title_map = {
        "shortlisted": "You're shortlisted! 🎉",
        "interview": "Interview invitation 📅",
        "selected": "Congratulations — Selected! 🎊",
        "rejected": "Application update",
        "under_review": "Application under review",
        "applied": "Application update",
    }
    msg = f"Your application for {app.job.title} at {app.job.company.company_name} moved from “{old}” to “{labels[new_status]}”."
    if note:
        msg += f" Note from recruiter: {note}"
    Notification.notify(app.applicant, title_map.get(new_status, "Application update"), msg, url="/applications/applied/")

    return JsonResponse({"success": True, "status": new_status, "status_display": labels[new_status], "message": f"Status updated to {labels[new_status]}."})


@require_POST
def send_interview_invite(request, pk):
    """Shortcut: mark Interview + include date/time details in the notification."""
    if not request.user.is_authenticated or not request.user.is_recruiter:
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    app = get_object_or_404(Application, pk=pk, job__posted_by=request.user)
    details = request.POST.get("details", "").strip() or "Interview details will be shared shortly."
    app.status = Application.Status.INTERVIEW
    app.recruiter_note = details
    app.save()

    Notification.notify(
        app.applicant,
        "Interview invitation 📅",
        f"Interview for {app.job.title} at {app.job.company.company_name}: {details}",
        url="/applications/applied/",
    )
    return JsonResponse({"success": True, "message": "Interview invitation sent."})


@require_GET
def download_resume(request, pk):
    """Serve the applicant's resume file after an authorization check."""
    if not request.user.is_authenticated or not request.user.is_recruiter:
        raise Http404()
    app = get_object_or_404(Application, pk=pk, job__posted_by=request.user)
    target = app.resume or getattr(app.applicant.seeker_profile, "resume", None)
    if not target:
        raise Http404("Resume not found.")
    return FileResponse(target.open("rb"), as_attachment=True)
