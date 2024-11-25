from django.urls import path
from .views import AccessControlDashboardView, CreateRoleView
from . import views

urlpatterns = [
    path('dashboard/', AccessControlDashboardView.as_view(), name='access_control_dashboard'),
    path('roles/create/', CreateRoleView.as_view(), name='create_role'),
    path('role/<int:role_id>/', views.RoleDetailView.as_view(), name='role_detail'),
    path('role/<int:role_id>/edit/', views.EditRoleView.as_view(), name='edit_role'),
    path('role/<int:role_id>/delete/', views.DeleteRoleView.as_view(), name='delete_role'),
]
