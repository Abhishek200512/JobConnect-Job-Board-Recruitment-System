from django.urls import path
from . import api_views

urlpatterns = [
    path("", api_views.CompanyListAPIView.as_view(), name="api_companies"),
    path("<int:pk>/", api_views.CompanyDetailAPIView.as_view(), name="api_company_detail"),
]
