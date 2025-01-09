from django.urls import path
from .views import (
    dashboard as dashboard_views,
    schedules as schedule_views
)

app_name = 'compliance_management'

urlpatterns = [
    path('dashboard/', dashboard_views.ComplianceManagementDashboardView.as_view(), name='compliance_dashboard'),
    
    path('schedules/', schedule_views.ComplianceScheduleListView.as_view(), name='schedule_list'),
]