from django.urls import path
from .views import (
    dashboard as dashboard_views,
    schedules as schedule_views,
    issues as issue_views,
    metrics as metrics_views
)

app_name = 'compliance_management'

urlpatterns = [
    path('dashboard/', dashboard_views.ComplianceManagementDashboardView.as_view(), name='compliance_dashboard'),
    path('schedules/', schedule_views.ComplianceScheduleListView.as_view(), name='schedule_list'),
    path('schedules/<int:pk>/', schedule_views.ComplianceScheduleDetailView.as_view(), name='schedule_detail'),
    path('schedules/<int:pk>/edit/', schedule_views.ComplianceScheduleUpdateView.as_view(), name='schedule_edit'),
    path('schedules/<int:pk>/delete/', schedule_views.ComplianceScheduleDeleteView.as_view(), name='schedule_delete'),
    
    # Issue Management URLs
    path('issues/', issue_views.ComplianceIssueListView.as_view(), name='issue_list'),
    path('issues/create/', issue_views.ComplianceIssueCreateView.as_view(), name='issue_create'),
    path('issues/<int:pk>/', issue_views.ComplianceIssueDetailView.as_view(), name='issue_detail'),
    path('issues/<int:pk>/edit/', issue_views.ComplianceIssueUpdateView.as_view(), name='issue_edit'),
    path('issues/<int:pk>/delete/', issue_views.ComplianceIssueDeleteView.as_view(), name='issue_delete'),

    # Metrics Management URLs
    path('metrics/', metrics_views.ComplianceMetricListView.as_view(), name='metric_list'),
    path('metrics/create/', metrics_views.ComplianceMetricCreateView.as_view(), name='metric_create'),
    path('metrics/<int:pk>/', metrics_views.ComplianceMetricDetailView.as_view(), name='metric_detail'),
]