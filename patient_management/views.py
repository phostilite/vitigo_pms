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

class PatientListView(LoginRequiredMixin, View):
    template_name = 'dashboard/admin/patient_management/patient_list.html'

    def get(self, request):
        try:
            if request.user.role not in ['ADMIN', 'DOCTOR', 'NURSE']:
                raise PermissionDenied("You do not have permission to view this page.")

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
            }

            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error retrieving patient list: {str(e)}", exc_info=True)
            return render(request, 'error_handling/500.html', {'error': 'An unexpected error occurred'}, status=500)


class PatientDetailView(LoginRequiredMixin, DetailView):
    template_name = 'dashboard/admin/patient_management/patient_detail.html'
    context_object_name = 'patient'

    def get_object(self):
        try:
            # Get the user first
            try:
                user = get_object_or_404(User, id=self.kwargs.get('user_id'))
            except (ObjectDoesNotExist, ValueError):
                raise Http404("User not found or invalid user ID")
            
            # Check if user is a patient
            try:
                if user.role != 'PATIENT':
                    raise PermissionDenied("This user is not a patient.")
            except AttributeError:
                raise PermissionDenied("Unable to verify user role")
            
            # Get the associated patient profile
            try:
                patient = get_object_or_404(Patient, user=user)
                return patient
            except ObjectDoesNotExist:
                raise Http404("Patient profile not found")
                
        except Exception as e:
            # Log the unexpected error here if you have logging configured
            raise Http404(f"An unexpected error occurred: {str(e)}")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient = self.object
        
        # Get latest vitiligo assessment
        try:
            latest_assessment = VitiligoAssessment.objects.filter(
                patient=patient
            ).order_by('-assessment_date').first()
        except Exception:
            latest_assessment = None
        context['latest_assessment'] = latest_assessment

        # Get active treatment plan
        try:
            active_treatment = TreatmentPlan.objects.filter(
                patient=patient
            ).order_by('-created_date').first()
        except Exception:
            active_treatment = None
        context['active_treatment_plan'] = active_treatment

        # Get current medications
        try:
            current_medications = Medication.objects.filter(
                patient=patient,
                end_date__isnull=True
            ).order_by('-start_date')
        except Exception:
            current_medications = []
        context['current_medications'] = current_medications

        # Get medical history with safe access
        try:
            medical_history = patient.medical_history
        except AttributeError:
            medical_history = None
        context['medical_history'] = medical_history

        # Get vitiligo progression data for chart
        try:
            assessments = VitiligoAssessment.objects.filter(
                patient=patient
            ).order_by('assessment_date')
            assessment_dates = [a.assessment_date.strftime('%Y-%m-%d') for a in assessments]
            vasi_scores = [a.vasi_score for a in assessments]
        except Exception:
            assessment_dates = []
            vasi_scores = []
        
        context['assessment_dates'] = assessment_dates
        context['vasi_scores'] = vasi_scores

        return context