from django.urls import path
from . import (
    views as v, 
    device_views as dv,
    protocol_views as pv,
    schedule_views as sv,
    report_views as rv,
    rfid_views as rf,
    problem_report_views as pr,
    reminder_views as rm,
    export_views as ev,
    home_views as hv
)
from .export_views import ProtocolExportView

urlpatterns = [
    path('', v.PhototherapyManagementView.as_view(), name='phototherapy_management'),
    path('new-treatment-plan/', v.NewTreatmentPlanView.as_view(), name='new_treatment_plan'),
    path('treatment-plans/', v.TreatmentPlanListView.as_view(), name='treatment_plan_list'),
    path('therapy-types/', v.PhototherapyTypeListView.as_view(), name='therapy_types_dashboard'),
    path('add-therapy-type/', v.AddPhototherapyTypeView.as_view(), name='add_therapy_type'),

    path('devices/', dv.DeviceManagementView.as_view(), name='device_management'),
    path('devices/register/', dv.RegisterDeviceView.as_view(), name='register_device'),
    path('devices/maintenance/schedule/', dv.ScheduleMaintenanceView.as_view(), name='schedule_maintenance'),
    path('devices/edit/<int:device_id>/', dv.EditDeviceView.as_view(), name='edit_device'),

    path('protocols/', pv.ProtocolManagementView.as_view(), name='protocol_management'),
    path('protocols/add/', pv.AddProtocolView.as_view(), name='add_protocol'),
    path('protocols/<int:protocol_id>/edit/', pv.EditProtocolView.as_view(), name='edit_protocol'),
    path('protocols/export/', ProtocolExportView.as_view(), name='export_protocols'),

    path('schedules/', sv.ScheduleManagementView.as_view(), name='schedule_management'),
    path('schedule-session/', sv.ScheduleSessionView.as_view(), name='schedule_session'),
    path('session/<int:session_id>/', sv.SessionDetailView.as_view(), name='session_detail'),
    path('session/<int:session_id>/add-report/', sv.AddSessionReportView.as_view(), name='add_session_report'),
    path('session/<int:session_id>/update-notes/', sv.UpdateSessionNotesView.as_view(), name='update_session_notes'),
    path('session/<int:session_id>/update-rfid/', sv.UpdateRFIDTrackingView.as_view(), name='update_rfid_tracking'),
    path('session/<int:session_id>/update-status/', sv.UpdateSessionStatusView.as_view(), name='update_session_status'),

    path('reports/', rv.ReportManagementView.as_view(), name='report_management'),

    path('rfid-dashboard/', rf.RFIDDashboardView.as_view(), name='rfid_dashboard'),
    path('rfid/issue/', rf.RFIDCardIssueView.as_view(), name='rfid_card_issue'),

    path('report-problem/', pr.ReportProblemView.as_view(), name='report_problem'),

    path('reminders/', rm.PhototherapyRemindersDashboardView.as_view(), name='reminders_dashboard'),
    path('reminders/create/', rm.CreatePhototherapyReminderView.as_view(), name='create_reminder'),
    path('reminders/send/', rm.send_reminder, name='send_reminder'),

    path('export/', ev.PhototherapyDashboardExportView.as_view(), name='phototherapy_export'),

    path('home-therapy/logs/', hv.HomeTherapyLogsView.as_view(), name='home_therapy_logs'),
]