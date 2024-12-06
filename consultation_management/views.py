# Standard library imports
from django.views.generic import ListView
from django.db.models import Count, Avg, Q
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.detail import DetailView
from django.shortcuts import get_object_or_404
from datetime import timedelta

# Local application imports
from .models import Consultation
from access_control.models import Role
from access_control.permissions import PermissionManager
from error_handling.views import handler403, handler404, handler500

def get_template_path(base_template, role, module=''):
    """
    Resolves template path based on user role.
    """
    if isinstance(role, Role):
        role_folder = role.template_folder
    else:
        try:
            role = Role.objects.get(name=role)
            role_folder = role.template_folder
        except Role.DoesNotExist:
            role_folder = 'default'
    
    if module:
        return f'dashboard/{role_folder}/{module}/{base_template}'
    return f'dashboard/{role_folder}/{base_template}'

class ConsultationManagementView(LoginRequiredMixin, ListView):
    model = Consultation
    context_object_name = 'consultations'
    paginate_by = 10
    
    def dispatch(self, request, *args, **kwargs):
        try:
            # Check module access permission
            if not PermissionManager.check_module_access(request.user, 'consultation_management'):
                messages.error(request, "You don't have permission to access Consultation Management")
                return handler403(request, exception="Access denied to consultation management")

            # Check role-specific requirements
            user = request.user
            if user.role.name == 'DOCTOR' and not hasattr(user, 'doctor_profile'):
                messages.error(request, "Doctor profile not found")
                return handler403(request, exception="Doctor profile not found")
            elif user.role.name == 'PATIENT' and not hasattr(user, 'patient_profile'):
                messages.error(request, "Patient profile not found")
                return handler403(request, exception="Patient profile not found")

            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            messages.error(request, "An error occurred while accessing consultation management")
            return handler500(request, exception=str(e))

    def get_template_names(self):
        return [get_template_path('consultation_dashboard.html', self.request.user.role, 'consultation_management')]

    def get_queryset(self):
        try:
            queryset = super().get_queryset()
            user = self.request.user

            # Filter consultations based on user role
            if user.role.name == 'DOCTOR':
                queryset = queryset.filter(doctor=user)
            elif user.role.name == 'PATIENT':
                queryset = queryset.filter(patient=user)
            
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
                    Q(patient__first_name__icontains=search_query) |
                    Q(patient__last_name__icontains=search_query) |
                    Q(doctor__first_name__icontains=search_query) |
                    Q(doctor__last_name__icontains=search_query) |
                    Q(diagnosis__icontains=search_query)
                )
                
        except Exception as e:
            messages.error(self.request, "Error retrieving consultations")
            return Consultation.objects.none()

        return queryset.select_related(
            'patient',
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
    
    def dispatch(self, request, *args, **kwargs):
        try:
            # Check module access permission
            if not PermissionManager.check_module_access(request.user, 'consultation_management'):
                messages.error(request, "You don't have permission to view consultation details")
                return handler403(request, exception="Access denied to consultation details")

            # Check role-specific requirements
            user = request.user
            if user.role.name == 'DOCTOR' and not hasattr(user, 'doctor_profile'):
                messages.error(request, "Doctor profile not found")
                return handler403(request, exception="Doctor profile not found")
            elif user.role.name == 'PATIENT' and not hasattr(user, 'patient_profile'):
                messages.error(request, "Patient profile not found")
                return handler403(request, exception="Patient profile not found")

            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            messages.error(request, "An error occurred while accessing consultation details")
            return handler500(request, exception=str(e))

    def get_template_names(self):
        return [get_template_path('consultation_detail.html', self.request.user.role, 'consultation_management')]

    def get_object(self, queryset=None):
        try:
            consultation = get_object_or_404(
                Consultation.objects.select_related(
                    'patient',
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
            
            # Check if user has permission to view this consultation
            user = self.request.user
            if user.role.name == 'DOCTOR' and consultation.doctor != user:
                messages.error(self.request, "Not authorized to view this consultation")
                raise PermissionError("Not authorized to view this consultation")
            elif user.role.name == 'PATIENT' and consultation.patient != user:
                messages.error(self.request, "Not authorized to view this consultation")
                raise PermissionError("Not authorized to view this consultation")
                
            return consultation
        except PermissionError as e:
            return handler403(self.request, exception=str(e))
        except Exception as e:
            messages.error(self.request, "Error retrieving consultation details")
            return handler500(self.request, exception=str(e))

    def get_context_data(self, **kwargs):
        try:
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
            
            if consultation.patient and hasattr(consultation.patient, 'patient_profile'):
                # Get patient's medical history and other related data
                patient_profile = consultation.patient.patient_profile
                
                context.update({
                    'medical_history': getattr(patient_profile, 'medical_history', None),
                    'current_medications': patient_profile.medications.filter(end_date__isnull=True),
                    'vitiligo_assessments': patient_profile.vitiligo_assessments.order_by('-assessment_date')[:3],
                    'treatment_plans': patient_profile.treatment_plans.order_by('-created_date')[:1],
                })
                
                # Get previous consultations
                context['previous_consultations'] = Consultation.objects.filter(
                    patient=consultation.patient,
                    date_time__lt=consultation.date_time
                ).order_by('-date_time')[:5]
            
            return context
        except Exception as e:
            messages.error(self.request, "Error loading consultation details")
            return handler500(self.request, exception=str(e))