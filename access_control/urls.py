from django.urls import path
from .views import AccessControlDashboardView

urlpatterns = [
    path('dashboard/', AccessControlDashboardView.as_view(), name='access_control_dashboard'),
]
