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

urlpatterns = [
    path('', v.PhototherapyManagementView.as_view(), name='phototherapy_management'),
    path('new-treatment-plan/', v.NewTreatmentPlanView.as_view(), name='new_treatment_plan'),
    path('treatment-plans/', v.TreatmentPlanListView.as_view(), name='treatment_plan_list'),
    path('therapy-types/', v.PhototherapyTypeListView.as_view(), name='therapy_types_dashboard'),
    path('add-therapy-type/', v.AddPhototherapyTypeView.as_view(), name='add_therapy_type'),
    path('therapy-types/<int:pk>/edit/', v.EditPhototherapyTypeView.as_view(), name='edit_therapy_type'),
    path('therapy-types/<int:pk>/delete/', v.DeletePhototherapyTypeView.as_view(), name='delete_therapy_type'),
    path('therapy-type/<int:type_id>/details/', 
         v.get_therapy_type_details, 
         name='therapy_type_details'),
    path('treatment-plans/export/', ev.TreatmentPlanExportView.as_view(), name='export_treatment_plans'),
    path('treatment-plans/<int:pk>/', v.TreatmentPlanDetailView.as_view(), name='treatment_plan_detail'),
    path('treatment-plans/<int:pk>/activate/', v.ActivateTreatmentPlanView.as_view(), name='activate_treatment_plan'),
    path('treatment-plans/<int:pk>/deactivate/', v.DeactivateTreatmentPlanView.as_view(), name='deactivate_treatment_plan'),
    path('treatment-plans/<int:pk>/edit/', v.EditTreatmentPlanView.as_view(), name='edit_treatment_plan'),

    path('devices/', dv.DeviceManagementView.as_view(), name='device_management'),
    path('devices/register/', dv.RegisterDeviceView.as_view(), name='register_device'),
    path('devices/export/', ev.DeviceDataExportView.as_view(), name='export_device_data'),  
    path('devices/maintenance/schedule/', dv.ScheduleMaintenanceView.as_view(), name='schedule_maintenance'),
    path('devices/edit/<int:device_id>/', dv.EditDeviceView.as_view(), name='edit_device'),
    path('devices/<int:pk>/delete/', dv.DeleteDeviceView.as_view(), name='delete_device'),
    path('device/<int:device_id>/details/', 
         v.get_device_details, 
         name='device_details'),

    path('protocols/', pv.ProtocolManagementView.as_view(), name='protocol_management'),
    path('protocols/add/', pv.AddProtocolView.as_view(), name='add_protocol'),
    path('protocols/<int:protocol_id>/edit/', pv.EditProtocolView.as_view(), name='edit_protocol'),
    path('protocols/export/', ev.ProtocolExportView.as_view(), name='export_protocols'),
    path('protocols/<int:protocol_id>/', pv.ProtocolDetailView.as_view(), name='protocol_detail'),
    path('protocols/<int:protocol_id>/activate/', pv.ActivateProtocolView.as_view(), name='activate_protocol'),
    path('protocols/<int:protocol_id>/deactivate/', pv.DeactivateProtocolView.as_view(), name='deactivate_protocol'),
    path('protocol/<int:protocol_id>/details/', v.get_protocol_details, name='protocol_details'),

    path('schedules/', sv.ScheduleManagementView.as_view(), name='schedule_management'),
    path('schedule-session/', sv.ScheduleSessionView.as_view(), name='schedule_session'),
    path('session/<int:session_id>/', sv.SessionDetailView.as_view(), name='session_detail'),
    path('session/<int:session_id>/add-report/', sv.AddSessionReportView.as_view(), name='add_session_report'),
    path('session/<int:session_id>/update-notes/', sv.UpdateSessionNotesView.as_view(), name='update_session_notes'),
    path('session/<int:session_id>/update-rfid/', sv.UpdateRFIDTrackingView.as_view(), name='update_rfid_tracking'),
    path('session/<int:session_id>/update-status/', sv.UpdateSessionStatusView.as_view(), name='update_session_status'),

    path('reports/', rv.ReportManagementView.as_view(), name='report_management'),
    path('reports/export/', ev.ReportExportView.as_view(), name='export_reports'),  

    path('rfid-dashboard/', rf.RFIDDashboardView.as_view(), name='rfid_dashboard'),
    path('rfid/issue/', rf.RFIDCardIssueView.as_view(), name='rfid_card_issue'),
    path('rfid/<int:pk>/edit/', rf.RFIDCardEditView.as_view(), name='edit_rfid_card'),
    path('rfid/export/', ev.RFIDCardExportView.as_view(), name='export_rfid_cards'),

    path('report-problem/', pr.ReportProblemView.as_view(), name='report_problem'),

    path('reminders/', rm.PhototherapyRemindersDashboardView.as_view(), name='reminders_dashboard'),
    path('reminders/create/', rm.CreatePhototherapyReminderView.as_view(), name='create_reminder'),
    path('reminders/send/', rm.send_reminder, name='send_reminder'),
    path('reminders/send-all/', rm.SendAllRemindersView.as_view(), name='send_all_reminders'),
    path('reminders/<int:reminder_id>/edit/', rm.edit_reminder, name='edit_reminder'),
    path('reminders/<int:pk>/delete/', rm.DeleteReminderView.as_view(), name='delete_reminder'),

    path('export/', ev.PhototherapyDashboardExportView.as_view(), name='phototherapy_export'),

    path('home-therapy/logs/', hv.HomeTherapyLogsView.as_view(), name='home_therapy_logs'),

    path('treatment-plan/<int:plan_id>/details/', 
         v.get_treatment_plan_details, 
         name='treatment_plan_details'),

    path('patient/<int:patient_id>/details/', 
         v.get_patient_details, 
         name='patient_details'),
]