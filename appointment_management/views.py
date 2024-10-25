from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from .models import Appointment
from django.db.models import Q
from collections import defaultdict

class AppointmentDashboardView(LoginRequiredMixin, ListView):
    model = Appointment
    template_name = 'dashboard/admin/appointment_management/appointment_dashboard.html'
    context_object_name = 'appointments'
    paginate_by = 10

    def get_queryset(self):
        queryset = Appointment.objects.all().order_by('-date', '-time_slot__start_time')
        
        # Apply filters if any
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(patient__first_name__icontains=search_query) |
                Q(patient__last_name__icontains=search_query) |
                Q(doctor__first_name__icontains=search_query) |
                Q(doctor__last_name__icontains=search_query)
            )
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        
        # Get appointment statistics
        context['total_appointments'] = Appointment.objects.count()
        context['today_appointments'] = Appointment.objects.filter(date=today).count()
        context['pending_appointments'] = Appointment.objects.filter(status='PENDING').count()
        context['completed_appointments'] = Appointment.objects.filter(status='COMPLETED').count()
        
        # Get appointments by status for chart
        status_counts = (Appointment.objects.values('status')
                        .annotate(count=Count('id'))
                        .order_by('status'))
        context['status_data'] = list(status_counts)
        
        # Get appointments by priority
        priority_counts = (Appointment.objects.values('priority')
                          .annotate(count=Count('id'))
                          .order_by('priority'))
        context['priority_data'] = list(priority_counts)
        
        # Get upcoming appointments for the next 7 days
        next_week = today + timedelta(days=7)
        context['upcoming_appointments'] = (
            Appointment.objects.filter(date__range=[today, next_week])
            .order_by('date', 'time_slot__start_time')[:5]
        )
        
        # Get daily appointment counts for the last 30 days
        last_month = today - timedelta(days=30)
        daily_appointments = Appointment.objects.filter(date__gte=last_month).values('date')
        
        # Manually aggregate daily counts
        daily_counts = defaultdict(int)
        for appt in daily_appointments:
            date_key = appt['date']
            daily_counts[date_key] += 1

        context['daily_appointment_data'] = [
            {'day': day, 'count': count} for day, count in sorted(daily_counts.items())
        ]
        
        return context

class AppointmentDetailView(LoginRequiredMixin, DetailView):
    model = Appointment
    template_name = 'dashboard/admin/appointment_management/appointment_detail.html'
    context_object_name = 'appointment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        appointment = self.get_object()
        
        # Add related appointments for the same patient
        context['related_appointments'] = (
            Appointment.objects.filter(patient=appointment.patient)
            .exclude(id=appointment.id)
            .order_by('-date')[:5]
        )
        
        return context
