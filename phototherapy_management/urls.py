from django.urls import path
from . import views, device_views

urlpatterns = [
    path('', views.PhototherapyManagementView.as_view(), name='phototherapy_management'),

    path('devices/', device_views.DeviceManagementView.as_view(), name='device_management'),
]