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
]
