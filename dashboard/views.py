# Standard library imports
from datetime import timedelta
from decimal import Decimal

# Django core imports
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import F, Count, Sum, Q
from django.shortcuts import render
from django.utils import timezone
from django.views import View
from django.contrib import messages

# Local application imports
from access_control.models import Role
from access_control.permissions import PermissionManager
from appointment_management.models import Appointment
from consultation_management.models import Consultation

from patient_management.models import Patient, TreatmentPlan
from doctor_management.models import DoctorProfile
from phototherapy_management.models import PhototherapySession
from stock_management.models import StockItem

# Add to imports
from error_handling.views import handler403, handler404, handler500

# Get custom user model
User = get_user_model()

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

class DashboardView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.role:
            return handler403(self.request, exception="No role assigned")
        if not PermissionManager.check_module_access(request.user, 'dashboard'):
            messages.error(request, "You don't have permission to access the dashboard")
            return handler403(request, exception="Access Denied")
        return super().dispatch(request, *args, **kwargs)

    def get_template_name(self):
        return get_template_path('dashboard.html', self.request.user.role, 'dashboard')

    def get_context_for_admin(self):
        # Check if user has admin access
        admin_roles = ['SUPER_ADMIN', 'ADMINISTRATOR', 'MANAGER']
        if not self.request.user.role or self.request.user.role.name not in admin_roles:
            return handler403(self.request, exception="You do not have permission to access the admin dashboard.")
        
        try:
            # Get all staff roles (non-admin roles)
            staff_roles = Role.objects.exclude(name__in=['SUPER_ADMIN', 'ADMIN', 'MANAGER'])
            
            # Calculate total staff
            total_staff = User.objects.filter(role__in=staff_roles).count()
            
            # Calculate new staff percentage (e.g., staff added in the last month)
            one_month_ago = timezone.now() - timedelta(days=30)
            new_staff = User.objects.filter(
                role__in=staff_roles,
                date_joined__gte=one_month_ago
            ).count()
            new_staff_percentage = (new_staff / total_staff) * 100 if total_staff > 0 else 0

            # Calculate total patients
            patient_role = Role.objects.get(name='PATIENT')
            total_patients = User.objects.filter(role=patient_role).count()
            
            # Calculate new patients percentage (e.g., patients added in the last month)
            new_patients = User.objects.filter(date_joined__gte=one_month_ago).count()
            new_patients_percentage = (new_patients / total_patients) * 100 if total_patients > 0 else 0

            # Get today's appointments
            today = timezone.now().date()
            todays_appointments = Appointment.objects.filter(date=today)

            # Calculate weekly phototherapy sessions
            one_week_ago = timezone.now() - timedelta(days=7)
            weekly_phototherapy_sessions = PhototherapySession.objects.filter(session_date__gte=one_week_ago).count()

            # Calculate phototherapy growth (compared to the previous week)
            two_weeks_ago = timezone.now() - timedelta(days=14)
            previous_week_sessions = PhototherapySession.objects.filter(session_date__gte=two_weeks_ago, session_date__lt=one_week_ago).count()
            phototherapy_growth = ((weekly_phototherapy_sessions - previous_week_sessions) / previous_week_sessions * 100) if previous_week_sessions > 0 else 0

            # Calculate demographics
            male_count = User.objects.filter(role=patient_role, gender='M').count()
            female_count = User.objects.filter(role=patient_role, gender='F').count()
            other_count = User.objects.filter(role=patient_role, gender='O').count()

            # Calculate treatment months and progress
            treatment_plans = TreatmentPlan.objects.all()
            treatment_months = [plan.created_date.strftime('%B %Y') for plan in treatment_plans]
            treatment_progress = [plan.medications.count() for plan in treatment_plans]

            # Get low stock items
            low_stock_items = StockItem.objects.filter(current_quantity__lte=F('reorder_point'))

            # Add any other context data needed for the admin dashboard
            context = {
                'total_staff': total_staff,
                'new_staff_percentage': round(new_staff_percentage, 2),
                'total_patients': total_patients,
                'new_patients_percentage': round(new_patients_percentage, 2),
                'todays_appointments': len(todays_appointments),
                'weekly_phototherapy_sessions': weekly_phototherapy_sessions,
                'phototherapy_growth': phototherapy_growth,
                'demographics': {
                    'male': male_count,
                    'female': female_count,
                    'other': other_count,
                },
                'treatment_months': treatment_months,  
                'treatment_progress': treatment_progress,  
                'low_stock_items': low_stock_items,
            }
            return context
        except Exception as e:
            return handler500(self.request, exception=str(e))

    def get_context_for_doctor(self):
        if not self.request.user.role or self.request.user.role.name != 'DOCTOR':
            return handler403(self.request, exception="You do not have permission to access the doctor dashboard.")
        
        today = timezone.now().date()
        one_month_ago = timezone.now() - timedelta(days=30)
        one_week_ago = timezone.now() - timedelta(days=7)
        start_of_month = today.replace(day=1)
        
        try:
            doctor_profile = DoctorProfile.objects.get(user=self.request.user)
            
            # Get patients through consultations
            patient_ids = Consultation.objects.filter(
                doctor=self.request.user
            ).values_list('patient', flat=True).distinct()
            
            total_patients = len(patient_ids)
            
            # Calculate new patients (patients with first consultation in last month)
            new_patient_ids = Consultation.objects.filter(
                doctor=self.request.user,
                created_at__gte=one_month_ago
            ).values_list('patient', flat=True).distinct()
            new_patients = len(new_patient_ids)
            
            new_patients_percentage = (new_patients / total_patients * 100) if total_patients > 0 else 0

            # Get today's appointments
            todays_appointments = Appointment.objects.filter(
                doctor=self.request.user,
                date=today
            ).count()

            # Calculate weekly phototherapy sessions
            weekly_phototherapy_sessions = PhototherapySession.objects.filter(
                plan__patient__in=patient_ids,
                session_date__gte=one_week_ago
            ).count()

            # Calculate previous week's sessions
            previous_week_sessions = PhototherapySession.objects.filter(
                plan__patient__in=patient_ids,
                session_date__gte=timezone.now() - timedelta(days=14),
                session_date__lt=one_week_ago
            ).count()
            
            phototherapy_growth = ((weekly_phototherapy_sessions - previous_week_sessions) / previous_week_sessions * 100) if previous_week_sessions > 0 else 0

            # Calculate monthly revenue from completed appointments
            completed_appointments = Appointment.objects.filter(
                doctor=self.request.user,
                date__gte=start_of_month,
                status='COMPLETED'
            ).count()
            
            monthly_revenue = completed_appointments * doctor_profile.consultation_fee

            # Calculate demographics for doctor's patients
            patients = Patient.objects.filter(id__in=patient_ids)
            demographics = {
                'male': patients.filter(gender='M').count(),
                'female': patients.filter(gender='F').count(),
                'other': patients.filter(gender='O').count(),
            }

            # Get treatment progress data
            treatment_plans = TreatmentPlan.objects.filter(
                created_by=self.request.user
            ).order_by('created_date')
            
            treatment_months = [plan.created_date.strftime('%B %Y') for plan in treatment_plans]
            treatment_progress = [
                (plan.medications.count() / plan.medications.all().count() * 100) 
                if plan.medications.exists() else 0 
                for plan in treatment_plans
            ]

            # Get recent activities (consultations)
            recent_consultations = Consultation.objects.filter(
                doctor=self.request.user
            ).select_related('patient__user').order_by('-created_at')[:5]
            
            recent_activities = [{
                'patient': consultation.patient,
                'appointment_type': consultation.consultation_type,
                'created_at': consultation.created_at
            } for consultation in recent_consultations]

            # Get upcoming appointments
            upcoming_tasks = Appointment.objects.filter(
                doctor=self.request.user,
                date__gt=today,
                status__in=['PENDING', 'SCHEDULED', 'CONFIRMED']
            ).select_related('patient', 'time_slot').order_by('date', 'time_slot__start_time')[:5]

            context = {
                'doctor_profile': doctor_profile,
                'total_patients': total_patients,
                'new_patients_percentage': round(new_patients_percentage, 2),
                'todays_appointments': todays_appointments,
                'weekly_phototherapy_sessions': weekly_phototherapy_sessions,
                'phototherapy_growth': round(phototherapy_growth, 2),
                'monthly_revenue': monthly_revenue,
                'demographics': demographics,
                'treatment_months': treatment_months,
                'treatment_progress': treatment_progress,
                'recent_activities': recent_activities,
                'upcoming_tasks': upcoming_tasks,
            }
        
        except DoctorProfile.DoesNotExist:
            return handler404(self.request, exception="Doctor profile not found")
        except Exception as e:
            return handler500(self.request, exception=str(e))
        return context
        
    def get_context_for_patient(self):
        patient_role = Role.objects.get(name='PATIENT')
        if self.request.user.role != patient_role:
            return handler403(self.request, exception="You do not have permission to access the patient dashboard.")
        
        try:
            patient_profile = self.request.user.patient_profile
            appointments = self.request.user.appointments.all()
            consultations = patient_profile.consultations.all()

            context = {
                'user': self.request.user,
                'patient_profile': patient_profile,
                'appointments': appointments,
                'consultations': consultations,
            }
        except User.patient_profile.RelatedObjectDoesNotExist:
            return handler404(self.request, exception="Patient profile not found")
        except Exception as e:
            return handler500(self.request, exception=str(e))
        return context
        
    def get_context_for_default(self):
        """Default context for other roles with minimal data"""
        return {}
        
    def get(self, request):
        try:
            role_name = request.user.role.name
            
            # Map roles to their context methods
            context_methods = {
                'SUPER_ADMIN': self.get_context_for_admin,
                'ADMIN': self.get_context_for_admin,
                'MANAGER': self.get_context_for_admin,
                'DOCTOR': self.get_context_for_doctor,
                'PATIENT': self.get_context_for_patient
            }
            
            # Get the appropriate context method or use default
            context_method = context_methods.get(role_name, self.get_context_for_default)
            context_result = context_method()
            
            # If the context method returned an HttpResponse (error), return it directly
            if hasattr(context_result, 'status_code'):
                return context_result
                
            return render(request, self.get_template_name(), context_result)
            
        except Exception as e:
            return handler500(self.request, exception=str(e))