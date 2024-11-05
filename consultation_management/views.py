from django.views.generic import ListView
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta
from .models import Consultation
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.detail import DetailView
from django.shortcuts import get_object_or_404

def get_template_path(base_template, user_role):
    """
    Resolves template path based on user role.
    Example: For 'consultation_dashboard.html' and role 'DOCTOR', 
    returns 'dashboard/doctor/consultation_management/consultation_dashboard.html'
    """
    role_template_map = {
        'ADMIN': 'admin',
        'DOCTOR': 'doctor',
        'NURSE': 'nurse',
        'RECEPTIONIST': 'receptionist',
        'PHARMACIST': 'pharmacist',
        'LAB_TECHNICIAN': 'lab',
    }
    
    role_folder = role_template_map.get(user_role, 'admin') 
    return f'dashboard/{role_folder}/consultation_management/{base_template}'

class ConsultationManagementView(LoginRequiredMixin, ListView):
    model = Consultation
    context_object_name = 'consultations'
    paginate_by = 10
    
    def get_template_names(self):
        user_role = self.request.user.role  # Assuming user role is stored in user model
        return [get_template_path('consultation_dashboard.html', user_role)]

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
    

class ConsultationDetailView(LoginRequiredMixin, DetailView):
    model = Consultation
    context_object_name = 'consultation'
    
    def get_template_names(self):
        user_role = self.request.user.role
        return [get_template_path('consultation_detail.html', user_role)]

    def get_object(self, queryset=None):
        # Get consultation with all related data
        consultation = get_object_or_404(
            Consultation.objects.select_related(
                'patient__user',
                'doctor',
                'doctor__doctor_profile',  # Add this line
                'treatment_instruction',
                'follow_up_plan'
            ).prefetch_related(
                'prescriptions__medication',
                'attachments'
            ),
            pk=self.kwargs['pk']
        )
        return consultation

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        consultation = self.object
        
        # Add doctor details
        context['doctor_details'] = {
            'name': consultation.doctor.get_full_name(),
            'specializations': consultation.doctor.doctor_profile.specializations.all(),
            'qualification': consultation.doctor.doctor_profile.qualification,
            'experience': consultation.doctor.doctor_profile.experience,
            'registration_number': consultation.doctor.doctor_profile.registration_number
        }
        
        # Calculate consultation duration
        if consultation.date_time:
            next_consultation = Consultation.objects.filter(
                date_time__gt=consultation.date_time,
                patient=consultation.patient
            ).order_by('date_time').first()
            
            if next_consultation:
                duration = next_consultation.date_time - consultation.date_time
                context['consultation_duration'] = duration.seconds // 60  # in minutes

        # Get patient's medical history
        context['medical_history'] = consultation.patient.medical_history
        
        # Get previous consultations
        context['previous_consultations'] = Consultation.objects.filter(
            patient=consultation.patient,
            date_time__lt=consultation.date_time
        ).order_by('-date_time')[:5]
        
        # Get patient's current medications
        context['current_medications'] = consultation.patient.medications.filter(
            end_date__isnull=True
        )
        
        # Get vitiligo assessments
        context['vitiligo_assessments'] = consultation.patient.vitiligo_assessments.order_by(
            '-assessment_date'
        )[:3]
        
        # Get treatment plan
        context['treatment_plans'] = consultation.patient.treatment_plans.order_by(
            '-created_date'
        )[:1]
        
        return context