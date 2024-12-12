from django.urls import path
from . import (
    views as v, 
    device_views as dv,
    protocol_views as pv,
    schedule_views as sv,
)

urlpatterns = [
    path('', v.PhototherapyManagementView.as_view(), name='phototherapy_management'),

    path('devices/', dv.DeviceManagementView.as_view(), name='device_management'),

    path('protocols/', pv.ProtocolManagementView.as_view(), name='protocol_management'),

    path('schedules/', sv.ScheduleManagementView.as_view(), name='schedule_management'),
]