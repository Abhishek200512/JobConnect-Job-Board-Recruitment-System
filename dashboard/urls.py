from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),

    path("dashboard/", views.seeker_dashboard, name="seeker_dashboard"),
    path("recruiter/", views.recruiter_dashboard, name="recruiter_dashboard"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),

    path("manage/users/", views.admin_users, name="admin_users"),
    path("manage/users/<int:pk>/toggle/", views.admin_toggle_user, name="admin_toggle_user"),
    path("manage/companies/", views.admin_companies, name="admin_companies"),
    path("manage/companies/<int:pk>/delete/", views.admin_delete_company, name="admin_delete_company"),
    path("manage/jobs/", views.admin_jobs, name="admin_jobs"),
    path("manage/jobs/<int:pk>/toggle/", views.admin_toggle_job, name="admin_toggle_job"),
    path("manage/jobs/<int:pk>/delete/", views.admin_delete_job, name="admin_delete_job"),
    path("manage/applications/", views.admin_applications, name="admin_applications"),
    path("reports/", views.admin_reports, name="admin_reports"),
]
