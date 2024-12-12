# Standard library imports
import logging

# Django imports
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.generic import View


# Local/application imports
from error_handling.views import handler500
from phototherapy_management.models import (
    PhototherapyPlan,
    PhototherapyProtocol,
    PhototherapyType,
)
from .utils import get_template_path
from .forms import ProtocolForm

# Configure logging
logger = logging.getLogger(__name__)

# Get User model
User = get_user_model()

class ProtocolManagementView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            # Fetch protocols with related data
            protocols = PhototherapyProtocol.objects.select_related(
                'phototherapy_type',
                'created_by'
            ).annotate(
                active_plans=Count('phototherapyplan'),
                avg_improvement=Avg('phototherapyplan__progress_records__improvement_percentage')
            ).order_by('-is_active', 'name')

            # Get protocol statistics
            protocol_stats = {
                'total': protocols.count(),
                'active': protocols.filter(is_active=True).count(),
                'types': PhototherapyType.objects.count(),
                'plans_using_protocols': PhototherapyPlan.objects.filter(
                    protocol__in=protocols,
                    is_active=True
                ).count()
            }

            # Group protocols by type
            protocols_by_type = {}
            for protocol in protocols:
                type_name = protocol.phototherapy_type.name
                if type_name not in protocols_by_type:
                    protocols_by_type[type_name] = []
                protocols_by_type[type_name].append(protocol)

            context = {
                'protocols': protocols,
                'protocols_by_type': protocols_by_type,
                'stats': protocol_stats,
                'phototherapy_types': PhototherapyType.objects.all(),
            }

            template_path = get_template_path(
                'protocol_management.html', 
                request.user.role, 
                'phototherapy_management'
            )
            return render(request, template_path, context)

        except Exception as e:
            logger.error(f"Error in protocol management view: {str(e)}")
            messages.error(request, "An error occurred while loading protocol data")
            return handler500(request, exception=str(e))
        

class AddProtocolView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            form = ProtocolForm()
            context = {
                'form': form,
            }
            template_path = get_template_path(
                'add_protocol.html',
                request.user.role,
                'phototherapy_management'
            )
            return render(request, template_path, context)
        except Exception as e:
            logger.error(f"Error in add protocol view GET: {str(e)}")
            messages.error(request, "An error occurred while loading the form")
            return redirect('protocol_management')

    def post(self, request):
        try:
            form = ProtocolForm(request.POST)
            if form.is_valid():
                protocol = form.save(commit=False)
                protocol.created_by = request.user
                protocol.save()
                
                messages.success(request, f"Protocol '{protocol.name}' created successfully")
                return redirect('protocol_management')
            else:
                context = {'form': form}
                template_path = get_template_path(
                    'add_protocol.html',
                    request.user.role,
                    'phototherapy_management'
                )
                return render(request, template_path, context)

        except Exception as e:
            logger.error(f"Error in add protocol view POST: {str(e)}")
            messages.error(request, "An error occurred while creating the protocol")
            return self.get(request)