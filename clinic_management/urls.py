# URLs configuration (add to urls.py)
from django.urls import path
from . import views

app_name = 'clinic_management'

urlpatterns = [
    path('', views.ClinicManagementDashboardView.as_view(), name='clinic_dashboard'),
    
    path('active_visits/', views.ActiveVisitsView.as_view(), name='active_visits'),

    path('active_checklists/', views.ActiveChecklistsView.as_view(), name='active_checklists'),

    path('visit_status_config/', views.VisitStatusConfigView.as_view(), name='visit_status_config'),

    path('completed_visits_report/', views.CompletedVisitsReportView.as_view(), name='completed_visits_report'),

    path('new_visit/', views.NewVisitView.as_view(), name='new_visit'),

    path('all_visits/', views.AllVisitsView.as_view(), name='all_visits'),

    path('visit_logs/', views.VisitLogsView.as_view(), name='visit_logs'),
    path('analytics/', views.VisitAnalyticsView.as_view(), name='visit_analytics'),
    path('checklist/new/', views.NewChecklistView.as_view(), name='new_checklist'),
    path('checklist/manage/', views.ManageChecklistsView.as_view(), name='manage_checklists'),
]
