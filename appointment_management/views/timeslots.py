from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db import transaction
from django.utils import timezone
from django.shortcuts import redirect
from ..models import DoctorTimeSlot, Center
from access_control.permissions import PermissionManager
from error_handling.views import handler403
from ..utils import get_template_path
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class DoctorTimeSlotManagementView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = DoctorTimeSlot
    context_object_name = 'timeslots'
    paginate_by = 20

    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'appointment_management')

    def dispatch(self, request, *args, **kwargs):
        if not self.test_func():
            messages.error(request, "You don't have permission to manage time slots")
            return handler403(request, exception="Access Denied")
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        return [get_template_path(
            'timeslots/list.html',
            self.request.user.role,
            'appointment_management'
        )]

    def get_queryset(self):
        queryset = DoctorTimeSlot.objects.select_related('doctor', 'center').filter(
            date__gte=timezone.now().date()
        )

        # Apply filters
        doctor_id = self.request.GET.get('doctor')
        center_id = self.request.GET.get('center')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        availability = self.request.GET.get('availability')

        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        if center_id:
            queryset = queryset.filter(center_id=center_id)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        if availability:
            is_available = availability == 'available'
            queryset = queryset.filter(is_available=is_available)

        return queryset.order_by('date', 'start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filters data
        context['doctors'] = User.objects.filter(
            role__name='DOCTOR',
            is_active=True
        ).order_by('first_name')
        
        context['centers'] = Center.objects.filter(
            is_active=True
        ).order_by('name')
        
        # Add selected filter values
        context.update({
            'selected_doctor': self.request.GET.get('doctor', ''),
            'selected_center': self.request.GET.get('center', ''),
            'selected_date_from': self.request.GET.get('date_from', ''),
            'selected_date_to': self.request.GET.get('date_to', ''),
            'selected_availability': self.request.GET.get('availability', ''),
        })
        
        return context

class DoctorTimeSlotCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = DoctorTimeSlot
    fields = ['doctor', 'center', 'date', 'start_time', 'end_time']
    success_url = reverse_lazy('timeslot_management')

    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'appointment_management')

    def form_valid(self, form):
        try:
            with transaction.atomic():
                timeslot = form.save(commit=False)
                timeslot.is_available = True
                timeslot.save()
                messages.success(self.request, "Time slot created successfully")
                return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error creating time slot: {str(e)}")
            messages.error(self.request, f"Error creating time slot: {str(e)}")
            return super().form_invalid(form)

class DoctorTimeSlotUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = DoctorTimeSlot
    fields = ['doctor', 'center', 'date', 'start_time', 'end_time', 'is_available']
    success_url = reverse_lazy('timeslot_management')

    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'appointment_management')

class DoctorTimeSlotDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = DoctorTimeSlot
    success_url = reverse_lazy('timeslot_management')

    def test_func(self):
        return PermissionManager.check_module_delete(self.request.user, 'appointment_management')

    def delete(self, request, *args, **kwargs):
        try:
            timeslot = self.get_object()
            if timeslot.date >= timezone.now().date():
                messages.error(request, "Cannot delete future time slots")
                return redirect('timeslot_management')
            messages.success(request, "Time slot deleted successfully")
            return super().delete(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error deleting time slot: {str(e)}")
            messages.error(request, f"Error deleting time slot: {str(e)}")
            return redirect('timeslot_management')
