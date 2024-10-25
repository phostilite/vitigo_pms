from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from patient_management.models import Patient   
import logging
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

User = get_user_model()

logger = logging.getLogger(__name__)

class PatientListView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            if request.user.role not in ['ADMIN', 'DOCTOR', 'NURSE']:
                raise PermissionDenied("You do not have permission to view this page.")
            
            # Determine the template based on the user role
            role_template_map = {
                'ADMIN': 'dashboard/admin/patient_management.html/patient_list.html',
                'DOCTOR': 'dashboard/doctor/patient_management.html/patient_list.html',
                'NURSE': 'dashboard/nurse/patient_management.html/patient_list.html'
            }
            template = role_template_map.get(request.user.role)
            
            patients = User.objects.filter(role='PATIENT', is_active=True)
            return render(request, template, {'patients': patients})
        
        except PermissionDenied as e:
            logger.warning(f"Permission denied for user {request.user.email}: {str(e)}")
            return render(request, 'error_handling/403.html', {'error': str(e)}, status=403)
        
        except Exception as e:
            logger.error(f"Error retrieving patient list: {str(e)}", exc_info=True)
            return render(request, 'error_handling/500.html', {'error': 'An unexpected error occurred'}, status=500)


class PatientDetailView(LoginRequiredMixin, View):
    def get(self, request, patient_id):
        try:
            if request.user.role not in ['ADMIN', 'DOCTOR', 'NURSE']:
                raise PermissionDenied("You do not have permission to view this page.")
                
            patient = get_object_or_404(Patient.objects.select_related(
                'user',
                'medical_history'
            ).prefetch_related(
                'medications',
                'vitiligo_assessments',
                'treatment_plans',
                'treatment_plans__medications'
            ), id=patient_id)
            
            latest_assessment = patient.vitiligo_assessments.order_by('-assessment_date').first()
            latest_treatment = patient.treatment_plans.order_by('-created_date').first()
            
            context = {
                'patient': patient,
                'latest_assessment': latest_assessment,
                'latest_treatment': latest_treatment,
            }
            
            return render(request, 'dashboard/admin/patient_management.html/patient_detail.html', context)
            
        except PermissionDenied as e:
            logger.warning(f"Permission denied for user {request.user.email}: {str(e)}")
            return render(request, 'error_handling/403.html', {'error': str(e)}, status=403)
        except Exception as e:
            logger.error(f"Error retrieving patient details: {str(e)}", exc_info=True)
            return render(request, 'error_handling/500.html', {'error': 'An unexpected error occurred'}, status=500)