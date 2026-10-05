from django.urls import path
from rest_framework.routers import DefaultRouter  # noqa: F401
from . import api_views

urlpatterns = [
    path("", api_views.JobListAPIView.as_view(), name="api_jobs"),
    path("categories/", api_views.CategoryListAPIView.as_view(), name="api_job_categories"),
    path("<int:pk>/", api_views.JobDetailAPIView.as_view(), name="api_job_detail"),
    path("<int:pk>/save/", api_views.SaveJobAPIView.as_view(), name="api_job_save"),
]
