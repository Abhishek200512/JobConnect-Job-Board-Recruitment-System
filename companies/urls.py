from django.urls import path
from . import views

urlpatterns = [
    path("", views.company_list, name="company_list"),
    path("profile/", views.company_profile, name="company_profile"),
    path("<int:pk>/", views.company_detail, name="company_detail"),
]
