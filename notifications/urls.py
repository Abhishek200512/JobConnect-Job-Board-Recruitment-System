from django.urls import path
from . import views

urlpatterns = [
    path("", views.notification_list, name="notifications"),
    path("<int:pk>/read/", views.mark_read, name="mark_read"),
    path("read-all/", views.mark_read, name="mark_all_read"),
    path("count/", views.notifications_count, name="notifications_count"),
]
