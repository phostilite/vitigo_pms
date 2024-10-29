from django.views.generic import ListView
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta
from .models import Consultation
from django.db.models import Q

class ConsultationManagementView(ListView):
    model = Consultation
    template_name = 'dashboard/admin/consultation_management/consultation_dashboard.html'
    context_object_name = 'consultations'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply filters from URL parameters
        consultation_type = self.request.GET.get('type')
        if consultation_type:
            queryset = queryset.filter(consultation_type=consultation_type)
            
        date_filter = self.request.GET.get('date')
        if date_filter:
            queryset = queryset.filter(date_time__date=date_filter)
            
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(patient__user__first_name__icontains=search_query) |
                Q(patient__user__last_name__icontains=search_query) |
                Q(doctor__first_name__icontains=search_query) |
                Q(doctor__last_name__icontains=search_query) |
                Q(diagnosis__icontains=search_query)
            )
            
        return queryset.select_related(
            'patient__user',
            'doctor',
            'treatment_instruction',
            'follow_up_plan'
        ).prefetch_related(
            'prescriptions',
            'attachments'
        ).order_by('-date_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current date and time
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        seven_days_future = now + timedelta(days=7)
        
        # Calculate metrics
        context.update({
            # Total consultations this month
            'total_consultations': Consultation.objects.filter(
                date_time__month=now.month,
                date_time__year=now.year
            ).count(),
            
            # Upcoming follow-ups in next 7 days
            'upcoming_followups': Consultation.objects.filter(
                follow_up_date__range=[now.date(), seven_days_future.date()]
            ).count(),
            
            # Monthly growth calculation
            'monthly_growth': self.calculate_monthly_growth(),
            
            # Consultation type distribution
            'consultation_types': Consultation.objects.values(
                'consultation_type'
            ).annotate(
                count=Count('id')
            ),
            
            # Filter options for template
            'consultation_type_choices': Consultation.CONSULTATION_TYPE_CHOICES,
        })
        
        return context
    
    def calculate_monthly_growth(self):
        """Calculate the growth in consultations compared to previous month"""
        now = timezone.now()
        this_month = Consultation.objects.filter(
            date_time__month=now.month,
            date_time__year=now.year
        ).count()
        
        # Get previous month's count
        if now.month == 1:
            prev_month = Consultation.objects.filter(
                date_time__month=12,
                date_time__year=now.year-1
            ).count()
        else:
            prev_month = Consultation.objects.filter(
                date_time__month=now.month-1,
                date_time__year=now.year
            ).count()
        
        if prev_month == 0:
            return 0
        
        return ((this_month - prev_month) / prev_month) * 100