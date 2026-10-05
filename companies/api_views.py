"""Companies API: /api/companies/."""
from django.db.models import Count, Q
from rest_framework import generics, permissions

from .models import Company
from .serializers import CompanySerializer


class CompanyListAPIView(generics.ListAPIView):
    """GET /api/companies/?q=&industry="""
    serializer_class = CompanySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Company.objects.annotate(open_jobs=Count("jobs", filter=Q(jobs__status="active")))
        q = self.request.GET.get("q", "").strip()
        industry = self.request.GET.get("industry", "").strip()
        if q:
            qs = qs.filter(company_name__icontains=q)
        if industry:
            qs = qs.filter(industry=industry)
        return qs.order_by("company_name")


class CompanyDetailAPIView(generics.RetrieveAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [permissions.AllowAny]
