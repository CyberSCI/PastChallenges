from django.urls import path

from system.views import HealthView, LogsView

urlpatterns = [
    path(r"health/", HealthView.as_view(), name="diagnostics"),
    path(r"logs/", LogsView.as_view(), name="logs"),
]
