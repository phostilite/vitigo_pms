# Standard library imports
import logging
from datetime import timedelta

# Django imports
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.utils import timezone
from django.views.generic import View
from django.contrib.auth import get_user_model

# Local/application imports
from error_handling.views import handler500
from phototherapy_management.models import DeviceMaintenance, PhototherapyDevice
from .utils import get_template_path

# Configure logger  
logger = logging.getLogger(__name__)

# Get user model
User = get_user_model()

class DeviceManagementView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            # Fetch devices with related data
            devices = PhototherapyDevice.objects.select_related(
                'phototherapy_type'
            ).prefetch_related(
                'maintenance_records'
            ).order_by('-is_active', 'name')

            # Calculate maintenance statistics
            maintenance_needed = devices.filter(
                next_maintenance_date__lte=timezone.now().date()
            ).count()

            maintenance_records = DeviceMaintenance.objects.select_related(
                'device'
            ).order_by('-maintenance_date')[:5]  # Get 5 most recent records

            # Group devices by type
            devices_by_type = {}
            for device in devices:
                type_name = device.phototherapy_type.name
                if type_name not in devices_by_type:
                    devices_by_type[type_name] = []
                devices_by_type[type_name].append(device)

            context = {
                'devices': devices,
                'devices_by_type': devices_by_type,
                'total_devices': devices.count(),
                'active_devices': devices.filter(is_active=True).count(),
                'maintenance_needed': maintenance_needed,
                'recent_maintenance': maintenance_records,
            }

            template_path = get_template_path('device_management.html', request.user.role, 'phototherapy_management')
            return render(request, template_path, context)

        except Exception as e:
            logger.error(f"Error in device management view: {str(e)}")
            messages.error(request, "An error occurred while loading device data")
            return handler500(request, exception=str(e))