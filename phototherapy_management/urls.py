from django.urls import path
from . import (
    views as v, 
    device_views as dv,
    protocol_views as pv,
    schedule_views as sv,
    report_views as rv,
    rfid_views as rf
)

urlpatterns = [
    path('', v.PhototherapyManagementView.as_view(), name='phototherapy_management'),

    path('devices/', dv.DeviceManagementView.as_view(), name='device_management'),
    path('devices/register/', dv.RegisterDeviceView.as_view(), name='register_device'),
    path('devices/maintenance/schedule/', dv.ScheduleMaintenanceView.as_view(), name='schedule_maintenance'),


    path('protocols/', pv.ProtocolManagementView.as_view(), name='protocol_management'),
    path('protocols/add/', pv.AddProtocolView.as_view(), name='add_protocol'),
    path('protocols/<int:protocol_id>/edit/', pv.EditProtocolView.as_view(), name='edit_protocol'),

    path('schedules/', sv.ScheduleManagementView.as_view(), name='schedule_management'),

    path('reports/', rv.ReportManagementView.as_view(), name='report_management'),

    path('rfid-dashboard/', rf.RFIDDashboardView.as_view(), name='rfid_dashboard'),
    path('rfid/issue/', rf.RFIDCardIssueView.as_view(), name='rfid_card_issue'),
]