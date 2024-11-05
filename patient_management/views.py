from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
import logging
from patient_management.models import Patient
from django.utils import timezone
from django.views.generic import DetailView
from .models import Patient, VitiligoAssessment, TreatmentPlan, Medication
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist

User = get_user_model()
logger = logging.getLogger(__name__)

def get_template_path(base_template, user_role):
    """
    Resolves template path based on user role.
    Example: For 'patient_list.html' and role 'DOCTOR', 
    returns 'dashboard/doctor/patient_management/patient_list.html'
    """
    role_template_map = {
        'ADMIN': 'admin',
        'DOCTOR': 'doctor',
        'NURSE': 'nurse',
        'RECEPTIONIST': 'receptionist',
        'PHARMACIST': 'pharmacist',
        'LAB_TECHNICIAN': 'lab',
    }
    
    role_folder = role_template_map.get(user_role, 'admin')  # default to admin if role not found
    return f'dashboard/{role_folder}/patient_management/{base_template}'

class PatientListView(LoginRequiredMixin, View):
    def get_template_name(self):
        return get_template_path('patient_list.html', self.request.user.role)

    def get(self, request):
        try:
            if request.user.role == 'PATIENT':
                raise PermissionDenied("Patients cannot access this page.")

            # Get all patients with optional filtering
            patients = User.objects.filter(role='PATIENT')
            
            # Apply filters
            status = request.GET.get('status')
            search_query = request.GET.get('search')

            if status:
                patients = patients.filter(is_active=(status == 'active'))
            
            if search_query:
                patients = patients.filter(
                    Q(first_name__icontains=search_query) |
                    Q(last_name__icontains=search_query) |
                    Q(email__icontains=search_query)
                )

            # Pagination
            paginator = Paginator(patients, 10)  # Show 10 patients per page
            page = request.GET.get('page')
            try:
                patients = paginator.page(page)
            except PageNotAnInteger:
                patients = paginator.page(1)
            except EmptyPage:
                patients = paginator.page(paginator.num_pages)

            # Get metrics
            total_patients = User.objects.filter(role='PATIENT').count()
            active_patients = User.objects.filter(role='PATIENT', is_active=True).count()
            inactive_patients = User.objects.filter(role='PATIENT', is_active=False).count()
            
            # Monthly metrics (you might want to adjust this based on your needs)
            new_patients_this_month = User.objects.filter(
                role='PATIENT',
                date_joined__month=timezone.now().month
            ).count()

            context = {
                'patients': patients,
                'total_patients': total_patients,
                'active_patients': active_patients,
                'inactive_patients': inactive_patients,
                'new_patients_this_month': new_patients_this_month,
                'paginator': paginator,
                'page_obj': patients,
                'user_role': request.user.role,  # Add user role to context
            }

            return render(request, self.get_template_name(), context)
            
        except Exception as e:
            logger.error(f"Error retrieving patient list: {str(e)}", exc_info=True)
            return render(request, 'error_handling/500.html', {'error': 'An unexpected error occurred'}, status=500)


class PatientDetailView(LoginRequiredMixin, DetailView):
    context_object_name = 'patient'
    
    def get_template_name(self):
        return get_template_path('patient_detail.html', self.request.user.role)

    def get_template_names(self):
        return [self.get_template_name()]

    def get_object(self):
        try:
            user = get_object_or_404(User, id=self.kwargs.get('user_id'))
            
            if user.role != 'PATIENT':
                raise PermissionDenied("This user is not a patient.")
            
            # Instead of get_object_or_404, use get() with a try-except block
            try:
                patient = Patient.objects.get(user=user)
                return patient
            except Patient.DoesNotExist:
                # Return None if no patient profile exists
                return None
                
        except Exception as e:
            logger.error(f"Error in PatientDetailView: {str(e)}")
            raise Http404(f"An unexpected error occurred: {str(e)}")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_role'] = self.request.user.role  # Add user role to context
        patient = self.object
        
        # If patient profile doesn't exist, return basic user info only
        if patient is None:
            context['user'] = get_object_or_404(User, id=self.kwargs.get('user_id'))
            context['profile_exists'] = False
            return context
            
        context['profile_exists'] = True
        
        # Only fetch related data if patient profile exists
        try:
            context['latest_assessment'] = VitiligoAssessment.objects.filter(
                patient=patient
            ).order_by('-assessment_date').first()
        except Exception:
            context['latest_assessment'] = None

        try:
            context['active_treatment_plan'] = TreatmentPlan.objects.filter(
                patient=patient
            ).order_by('-created_date').first()
        except Exception:
            context['active_treatment_plan'] = None

        try:
            context['current_medications'] = Medication.objects.filter(
                patient=patient,
                end_date__isnull=True
            ).order_by('-start_date')
        except Exception:
            context['current_medications'] = []

        try:
            context['medical_history'] = patient.medical_history
        except Exception:
            context['medical_history'] = None

        return context