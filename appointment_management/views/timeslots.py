from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.db import transaction
from django.utils import timezone
from django.shortcuts import redirect
from ..models import DoctorTimeSlot, Center
from access_control.permissions import PermissionManager
from error_handling.views import handler403
from ..utils import get_template_path
from ..forms import DoctorTimeSlotForm
from django.contrib.auth import get_user_model
import logging
from django.db.models import Count, Q

User = get_user_model()
logger = logging.getLogger(__name__)

class DoctorTimeSlotDashboardView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    context_object_name = 'doctors'
    
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'appointment_management')

    def dispatch(self, request, *args, **kwargs):
        if not self.test_func():
            messages.error(request, "You don't have permission to manage doctor time slots")
            return handler403(request, exception="Access Denied")
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        return [get_template_path(
            'timeslots/dashboard.html',
            self.request.user.role,
            'appointment_management'
        )]
    
    def get_queryset(self):
        return User.objects.filter(
            role__name='DOCTOR',
            is_active=True
        ).annotate(
            total_slots=Count('time_slots'),
            available_slots=Count('time_slots', filter=Q(time_slots__is_available=True)),
            booked_slots=Count('time_slots', filter=Q(time_slots__is_available=False))
        ).order_by('first_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['centers'] = Center.objects.filter(is_active=True)
        return context

class DoctorTimeSlotsView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    context_object_name = 'doctor'
    model = User

    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'appointment_management')

    def dispatch(self, request, *args, **kwargs):
        if not self.test_func():
            messages.error(request, "You don't have permission to view doctor time slots")
            return handler403(request, exception="Access Denied")
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        return [get_template_path(
            'timeslots/doctor_slots.html',
            self.request.user.role,
            'appointment_management'
        )]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            # Get filter parameters
            center_id = self.request.GET.get('center')
            date = self.request.GET.get('date', timezone.now().date())
            
            # Base queryset with efficient joins
            slots = DoctorTimeSlot.objects.select_related('center').filter(
                doctor=self.object,
                date__gte=timezone.now().date()
            ).order_by('date', 'start_time')
            
            # Apply filters
            if center_id:
                slots = slots.filter(center_id=center_id)
            if date:
                slots = slots.filter(date=date)
            
            # Group slots by date for better organization
            slots_by_date = {}
            for slot in slots:
                if slot.date not in slots_by_date:
                    slots_by_date[slot.date] = {
                        'total': 0,
                        'available': 0,
                        'slots': []
                    }
                
                slots_by_date[slot.date]['slots'].append(slot)
                slots_by_date[slot.date]['total'] += 1
                if slot.is_available:
                    slots_by_date[slot.date]['available'] += 1
            
            context.update({
                'slots_by_date': slots_by_date,
                'centers': Center.objects.filter(is_active=True),
                'selected_center': center_id,
                'selected_date': date,
                'page_title': f"Time Slots - Dr. {self.object.get_full_name()}",
                'total_slots': sum(data['total'] for data in slots_by_date.values()),
                'available_slots': sum(data['available'] for data in slots_by_date.values())
            })
            
        except Exception as e:
            logger.error(f"Error fetching doctor time slots: {str(e)}")
            messages.error(self.request, "Error loading time slots")
            context.update({
                'error': True,
                'slots_by_date': {},
                'centers': Center.objects.filter(is_active=True)
            })
        
        return context

class DoctorTimeSlotCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = DoctorTimeSlot
    form_class = DoctorTimeSlotForm
    success_url = reverse_lazy('timeslot_dashboard')

    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'appointment_management')

    def dispatch(self, request, *args, **kwargs):
        if not self.test_func():
            messages.error(request, "You don't have permission to create time slots")
            return handler403(request, exception="Access Denied")
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        return [get_template_path(
            'timeslots/create.html',
            self.request.user.role,
            'appointment_management'
        )]

    def form_valid(self, form):
        try:
            with transaction.atomic():
                self.object = form.save()
                messages.success(self.request, "Time slot created successfully")
                return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error creating time slot: {str(e)}")
            messages.error(self.request, f"Error creating time slot: {str(e)}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Create Time Slot"
        return context

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
