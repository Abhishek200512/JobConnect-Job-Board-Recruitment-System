"""JobConnect root URL configuration."""
from django.contrib import admin as django_admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("django-admin/", django_admin.site.urls),

    path("", include("dashboard.urls")),
    path("accounts/", include("accounts.urls")),
    path("jobs/", include("jobs.urls")),
    path("companies/", include("companies.urls")),
    path("applications/", include("applications.urls")),
    path("notifications/", include("notifications.urls")),

    # REST API
    path("api/", include("dashboard.api_index_urls")),
    path("api/auth/", include("accounts.api_urls")),
    path("api/users/", include("accounts.api_user_urls")),
    path("api/jobs/", include("jobs.api_urls")),
    path("api/companies/", include("companies.api_urls")),
    path("api/applications/", include("applications.api_urls")),
    path("api/notifications/", include("notifications.api_urls")),
    path("api/analytics/", include("dashboard.api_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = "dashboard.views.error_404"
handler500 = "dashboard.views.error_500"
