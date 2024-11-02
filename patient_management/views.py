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