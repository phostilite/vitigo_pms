# Standard library imports
import logging

# Django core imports
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView
from django.contrib import messages

# Local application imports
from access_control.models import Role
from patient_management.models import Patient
from access_control.permissions import PermissionManager
from error_handling.views import handler403, handler500
from .models import (
    Patient,
    VitiligoAssessment, 
    TreatmentPlan,
    Medication
)

# Configure logging and user model
User = get_user_model()
logger = logging.getLogger(__name__)

def get_template_path(base_template, role, module=''):
    """
    Resolves template path based on user role.
    Now uses the template_folder from Role model.
    """
    if isinstance(role, Role):
        role_folder = role.template_folder
    else:
        # Fallback for any legacy code
        role = Role.objects.get(name=role)
        role_folder = role.template_folder
    
    if module:
        return f'{role_folder}/{module}/{base_template}'
    return f'{role_folder}/{base_template}'

class PatientListView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if not PermissionManager.check_module_access(request.user, 'patient_management'):
            messages.error(request, "You don't have permission to access patient management")
            return handler403(request, exception="Access Denied")
        return super().dispatch(request, *args, **kwargs)

    def get_template_name(self):
        return get_template_path('patient_list.html', self.request.user.role, 'patient_management')

    def get(self, request):
        try:
            patient_role = Role.objects.get(name='PATIENT')
            
            if request.user.role == patient_role:
                messages.error(request, "Patients cannot access this page")
                return handler403(request, exception="Access Denied")

            # Get all patients using the foreign key relationship
            patients = User.objects.filter(role=patient_role)
            
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
            total_patients = User.objects.filter(role=patient_role).count()
            active_patients = User.objects.filter(role=patient_role, is_active=True).count()
            inactive_patients = User.objects.filter(role=patient_role, is_active=False).count()
            
            # Monthly metrics (you might want to adjust this based on your needs)
            new_patients_this_month = User.objects.filter(
                role=patient_role,
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
            
        except Role.DoesNotExist:
            logger.error("Patient role not found in the system")
            messages.error(request, "System configuration error")
            return handler500(request, exception="Patient role not found")
        except Exception as e:
            logger.error(f"Error in PatientListView: {str(e)}", exc_info=True)
            messages.error(request, "An unexpected error occurred while loading patients")
            return handler500(request, exception=e)


class PatientDetailView(LoginRequiredMixin, DetailView):
    def dispatch(self, request, *args, **kwargs):
        if not PermissionManager.check_module_access(request.user, 'patient_management'):
            messages.error(request, "You don't have permission to view patient details")
            return handler403(request, exception="Access Denied")
        return super().dispatch(request, *args, **kwargs)

    def get_template_name(self):
        return get_template_path('patient_detail.html', self.request.user.role, 'patient_management')

    def get_template_names(self):
        return [self.get_template_name()]

    def get_object(self):
        try:
            user = get_object_or_404(User, id=self.kwargs.get('user_id'))
            patient_role = Role.objects.get(name='PATIENT')
            
            # Check using the foreign key relationship
            if user.role != patient_role:
                messages.error(self.request, "Selected user is not a patient")
                raise PermissionDenied("This user is not a patient")

            try:
                return Patient.objects.get(user=user)
            except Patient.DoesNotExist:
                logger.warning(f"No patient profile found for user {user.id}")
                return None

        except Http404:
            logger.error(f"Patient with user_id {self.kwargs.get('user_id')} not found")
            messages.error(self.request, "Patient not found")
            raise
        except Role.DoesNotExist:
            logger.error("Patient role not found in the system")
            messages.error(self.request, "System configuration error")
            raise Http404("Patient role not found")
        except Exception as e:
            logger.error(f"Error in PatientDetailView: {str(e)}", exc_info=True)
            messages.error(self.request, "An unexpected error occurred")
            raise Http404(str(e))

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            context['user_role'] = self.request.user.role
            patient = self.object

            if patient is None:
                context.update({
                    'user': get_object_or_404(User, id=self.kwargs.get('user_id')),
                    'profile_exists': False
                })
                messages.warning(self.request, "Patient profile not found")
                return context

            context['profile_exists'] = True

            # Load related data with error handling
            try:
                context['latest_assessment'] = VitiligoAssessment.objects.filter(
                    patient=patient
                ).order_by('-assessment_date').first()
            except Exception as e:
                logger.error(f"Error loading assessment: {str(e)}")
                messages.warning(self.request, "Could not load latest assessment")
                context['latest_assessment'] = None

            try:
                context['active_treatment_plan'] = TreatmentPlan.objects.filter(
                    patient=patient
                ).order_by('-created_date').first()
            except Exception as e:
                logger.error(f"Error loading treatment plan: {str(e)}")
                messages.warning(self.request, "Could not load active treatment plan")
                context['active_treatment_plan'] = None

            try:
                context['current_medications'] = Medication.objects.filter(
                    patient=patient,
                    end_date__isnull=True
                ).order_by('-start_date')
            except Exception as e:
                logger.error(f"Error loading medications: {str(e)}")
                messages.warning(self.request, "Could not load current medications")
                context['current_medications'] = []

            try:
                context['medical_history'] = patient.medical_history
            except Exception as e:
                logger.error(f"Error loading medical history: {str(e)}")
                messages.warning(self.request, "Could not load medical history")
                context['medical_history'] = None

            return context

        except Exception as e:
            logger.error(f"Error in get_context_data: {str(e)}", exc_info=True)
            messages.error(self.request, "An unexpected error occurred while loading patient data")
            return super().get_context_data(**kwargs)