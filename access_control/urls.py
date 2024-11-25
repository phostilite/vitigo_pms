from django.urls import path
from .views import AccessControlDashboardView, CreateRoleView

urlpatterns = [
    path('dashboard/', AccessControlDashboardView.as_view(), name='access_control_dashboard'),
    path('roles/create/', CreateRoleView.as_view(), name='create_role'),
]
