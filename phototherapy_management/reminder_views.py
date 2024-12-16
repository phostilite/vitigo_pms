# Standard library imports
import logging

# Django imports
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.generic import View, ListView, CreateView
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

# Local/application imports
from error_handling.views import handler500, handler403
from access_control.permissions import PermissionManager
from phototherapy_management.models import (
    PhototherapyReminder, PhototherapyPlan
)
from .forms import PhototherapyReminderForm
from .utils import get_template_path

# Configure logging
logger = logging.getLogger(__name__)

# Get User model
User = get_user_model()

logger = logging.getLogger(__name__)

class PhototherapyRemindersDashboardView(LoginRequiredMixin, ListView):
    model = PhototherapyReminder
    context_object_name = 'reminders'
    paginate_by = 10
    
    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_access(request.user, 'phototherapy_management'):
                logger.warning(f"Access denied to phototherapy reminders for user {request.user.id}")
                messages.error(request, "You don't have permission to access Phototherapy Reminders")
                return handler403(request, exception="Access Denied")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in phototherapy reminders dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing the page")
            return redirect('dashboard')

    def get_queryset(self):
        try:
            return PhototherapyReminder.objects.filter(
                status='PENDING',
                scheduled_datetime__gte=timezone.now()
            ).select_related('plan', 'plan__patient').order_by('scheduled_datetime')
        except Exception as e:
            logger.error(f"Error getting reminders queryset: {str(e)}")
            return PhototherapyReminder.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['pending_reminders'] = self.get_queryset().count()
            context['today_reminders'] = self.get_queryset().filter(
                scheduled_datetime__date=timezone.now().date()
            ).count()
            context['section'] = 'reminders'
        except Exception as e:
            logger.error(f"Error getting context data: {str(e)}")
            context['error'] = "Unable to load complete data"
        return context

    def get_template_names(self):
        try:
            return [get_template_path(
                'phototherapy_reminders_dashboard.html',
                self.request.user.role,
                'phototherapy_management'
            )]
        except Exception as e:
            logger.error(f"Error getting template: {str(e)}")
            return ['phototherapy_management/default_phototherapy_reminders_dashboard.html']
        


class CreatePhototherapyReminderView(LoginRequiredMixin, CreateView):
    model = PhototherapyReminder
    form_class = PhototherapyReminderForm
    success_url = reverse_lazy('reminders_dashboard')
    
    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_access(request.user, 'phototherapy_management'):
                logger.warning(f"Access denied to create reminder for user {request.user.id}")
                messages.error(request, "You don't have permission to create reminders")
                return handler403(request, exception="Access Denied")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in create reminder dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing the page")
            return redirect('dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['active_plans'] = PhototherapyPlan.objects.filter(
                is_active=True
            ).select_related('patient')
            context['title'] = 'Create New Reminder'
            context['submit_text'] = 'Create Reminder'
        except Exception as e:
            logger.error(f"Error getting context data: {str(e)}")
            context['error'] = "Unable to load complete data"
        return context

    def get_template_names(self):
        try:
            return [get_template_path(
                'create_reminder.html',
                self.request.user.role,
                'phototherapy_management'
            )]
        except Exception as e:
            logger.error(f"Error getting template: {str(e)}")
            return ['phototherapy_management/default_create_reminder.html']

    def form_valid(self, form):
        try:
            form.instance.created_by = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, "Reminder created successfully")
            return response
        except Exception as e:
            logger.error(f"Error saving reminder: {str(e)}")
            messages.error(self.request, "Failed to create reminder")
            return self.form_invalid(form)

@login_required
@require_POST
def send_reminder(request):
    reminder_id = request.POST.get('reminder_id')
    send_email = request.POST.get('send_email') == 'on'
    send_sms = request.POST.get('send_sms') == 'on'

    try:
        reminder = PhototherapyReminder.objects.get(id=reminder_id, status='PENDING')
        
        if send_email:
            # Prepare email content
            html_message = render_to_string('emails/phototherapy/reminder.html', {
                'reminder': reminder
            })
            
            # Send email
            send_mail(
                subject='Phototherapy Reminder',
                message=reminder.message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[reminder.plan.patient.email],
                fail_silently=False,
            )

        if send_sms:
            # Implement SMS sending logic here
            pass

        # Update reminder status
        reminder.status = 'SENT'
        reminder.sent_at = timezone.now()
        reminder.save()

        messages.success(request, 'Reminder sent successfully!')
    except PhototherapyReminder.DoesNotExist:
        messages.error(request, 'Reminder not found or already sent.')
    except Exception as e:
        messages.error(request, f'Failed to send reminder: {str(e)}')

    return redirect('reminders_dashboard')