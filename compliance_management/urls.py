from django.urls import path
from .views import ComplianceManagementDashboardView

app_name = 'compliance_management'

urlpatterns = [
    path('dashboard/', ComplianceManagementDashboardView.as_view(), name='compliance_dashboard'),
]