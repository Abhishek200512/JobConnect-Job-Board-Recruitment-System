"""Company views: public directory/details and recruiter profile management."""
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from accounts.utils import role_required, validate_upload
from jobs.models import Job

from .models import Company


def company_list(request):
    qs = Company.objects.annotate(open_jobs=Count("jobs", filter=Q(jobs__status="active")))
    q = request.GET.get("q", "").strip()
    industry = request.GET.get("industry", "").strip()
    if q:
        qs = qs.filter(Q(company_name__icontains=q) | Q(description__icontains=q) | Q(location__icontains=q))
    if industry:
        qs = qs.filter(industry=industry)

    industries = Company.objects.exclude(industry="").values_list("industry", flat=True).distinct().order_by("industry")
    paginator = Paginator(qs.order_by("company_name"), 9)
    page = paginator.get_page(request.GET.get("page"))

    return render(request, "companies/company_list.html", {
        "companies": page.object_list,
        "page_obj": page,
        "total": paginator.count,
        "industries": industries,
        "current_q": q,
        "current_industry": industry,
    })


def company_detail(request, pk):
    company = get_object_or_404(Company, pk=pk)
    jobs = Job.active_jobs().filter(company=company).select_related("category")
    return render(request, "companies/company_detail.html", {"company": company, "jobs": jobs})


@role_required("recruiter")
def company_profile(request):
    company = request.user.companies.first()
    if request.method == "POST":
        if not company:
            company = Company(recruiter=request.user)
        name = request.POST.get("company_name", "").strip()
        if not name:
            messages.error(request, "Company name is required.")
            return redirect("company_profile")

        duplicate = Company.objects.filter(company_name__iexact=name).exclude(pk=company.pk).exists()
        if duplicate:
            messages.error(request, "A company with that name already exists.")
            return redirect("company_profile")

        company.company_name = name
        company.description = request.POST.get("description", "").strip()
        company.website = request.POST.get("website", "").strip()
        company.location = request.POST.get("location", "").strip()
        company.industry = request.POST.get("industry", "").strip()
        company.size = request.POST.get("size", "").strip()

        logo = request.FILES.get("logo")
        if logo:
            ok, err = validate_upload(logo, "image")
            if not ok:
                messages.error(request, err)
                return redirect("company_profile")
            if company.logo:
                company.logo.delete(save=False)
            company.logo = logo

        company.save()
        messages.success(request, "Company profile saved.")
        return redirect("company_profile")

    return render(request, "dashboard/recruiter/company_profile.html", {"company": company})
