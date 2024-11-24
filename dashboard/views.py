from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from patient_management.models import Patient, TreatmentPlan
from django.utils import timezone
from datetime import timedelta
from appointment_management.models import Appointment
from phototherapy_management.models import PhototherapySession
from django.contrib.auth import get_user_model
from stock_management.models import StockItem
from django.db.models import F, Count, Sum, Q
from decimal import Decimal
from doctor_management.models import DoctorProfile
from consultation_management.models import Consultation
from access_control.models import Role

User = get_user_model()

def get_template_path(base_template, role):
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
    
    return f'dashboard/{role_folder}/{base_template}'

@login_required
def patient_dashboard(request):
    patient_role = Role.objects.get(name='PATIENT')
    if request.user.role != patient_role:
        raise PermissionDenied("You do not have permission to access the patient dashboard.")
    
    try:
        patient_profile = request.user.patient_profile
        appointments = request.user.appointments.all()
        consultations = patient_profile.consultations.all()

        context = {
            'user': request.user,
            'patient_profile': patient_profile,
            'appointments': appointments,
            'consultations': consultations,
        }
    except User.patient_profile.RelatedObjectDoesNotExist:
        context = {
            'user': request.user,
            'error_message': "Your patient profile is not created yet. Please create it yourself or contact support.",
        }
    
    template_name = get_template_path('dashboard.html', request.user.role)
    return render(request, template_name, context)

@login_required
def admin_dashboard(request):
    # Check if user has admin access
    admin_roles = ['SUPER_ADMIN', 'ADMIN', 'MANAGER']
    if not request.user.role or request.user.role.name not in admin_roles:
        raise PermissionDenied("You do not have permission to access the admin dashboard.")
    
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
    
    template_name = get_template_path('dashboard.html', request.user.role)
    return render(request, template_name, context)

@login_required
def doctor_dashboard(request):
    if not request.user.role or request.user.role.name != 'DOCTOR':
        raise PermissionDenied("You do not have permission to access the doctor dashboard.")
    
    today = timezone.now().date()
    one_month_ago = timezone.now() - timedelta(days=30)
    one_week_ago = timezone.now() - timedelta(days=7)
    start_of_month = today.replace(day=1)
    
    try:
        doctor_profile = DoctorProfile.objects.get(user=request.user)
        
        # Get patients through consultations
        patient_ids = Consultation.objects.filter(
            doctor=request.user
        ).values_list('patient', flat=True).distinct()
        
        total_patients = len(patient_ids)
        
        # Calculate new patients (patients with first consultation in last month)
        new_patient_ids = Consultation.objects.filter(
            doctor=request.user,
            created_at__gte=one_month_ago
        ).values_list('patient', flat=True).distinct()
        new_patients = len(new_patient_ids)
        
        new_patients_percentage = (new_patients / total_patients * 100) if total_patients > 0 else 0

        # Get today's appointments
        todays_appointments = Appointment.objects.filter(
            doctor=request.user,
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
            doctor=request.user,
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
            created_by=request.user
        ).order_by('created_date')
        
        treatment_months = [plan.created_date.strftime('%B %Y') for plan in treatment_plans]
        treatment_progress = [
            (plan.medications.count() / plan.medications.all().count() * 100) 
            if plan.medications.exists() else 0 
            for plan in treatment_plans
        ]

        # Get recent activities (consultations)
        recent_consultations = Consultation.objects.filter(
            doctor=request.user
        ).select_related('patient__user').order_by('-created_at')[:5]
        
        recent_activities = [{
            'patient': consultation.patient,
            'appointment_type': consultation.consultation_type,
            'created_at': consultation.created_at
        } for consultation in recent_consultations]

        # Get upcoming appointments
        upcoming_tasks = Appointment.objects.filter(
            doctor=request.user,
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
        context = {
            'error_message': "Your doctor profile is not set up. Please contact the administrator."
        }
    
    template_name = get_template_path('dashboard.html', request.user.role)
    return render(request, template_name, context)

@login_required
def nurse_dashboard(request):
    if not request.user.role or request.user.role.name != 'NURSE':
        raise PermissionDenied("You do not have permission to access the nurse dashboard.")
    
    context = {}
    template_name = get_template_path('dashboard.html', request.user.role)
    return render(request, template_name, context)

@login_required
def medical_dashboard(request):
    if not request.user.role or request.user.role.name != 'MEDICAL_ASSISTANT':
        raise PermissionDenied("You do not have permission to access the medical dashboard.")
    
    context = {}
    template_name = get_template_path('dashboard.html', request.user.role)
    return render(request, template_name, context)

@login_required
def reception_dashboard(request):
    if not request.user.role or request.user.role.name != 'RECEPTIONIST':
        raise PermissionDenied("You do not have permission to access the reception dashboard.")
    
    context = {}
    template_name = get_template_path('dashboard.html', request.user.role)
    return render(request, template_name, context)

@login_required
def pharmacy_dashboard(request):
    if not request.user.role or request.user.role.name != 'PHARMACIST':
        raise PermissionDenied("You do not have permission to access the pharmacy dashboard.")
    
    context = {}
    template_name = get_template_path('dashboard.html', request.user.role)
    return render(request, template_name, context)

@login_required
def lab_dashboard(request):
    if not request.user.role or request.user.role.name != 'LAB_TECHNICIAN':
        raise PermissionDenied("You do not have permission to access the lab dashboard.")
    
    context = {}
    template_name = get_template_path('dashboard.html', request.user.role)
    return render(request, template_name, context)

@login_required
def billing_dashboard(request):
    if not request.user.role or request.user.role.name != 'BILLING_STAFF':
        raise PermissionDenied("You do not have permission to access the billing dashboard.")
    
    context = {}
    template_name = get_template_path('dashboard.html', request.user.role)
    return render(request, template_name, context)

@login_required
def inventory_dashboard(request):
    if not request.user.role or request.user.role.name != 'INVENTORY_MANAGER':
        raise PermissionDenied("You do not have permission to access the inventory dashboard.")
    
    context = {}
    template_name = get_template_path('dashboard.html', request.user.role)
    return render(request, template_name, context)

@login_required
def hr_dashboard(request):
    if not request.user.role or request.user.role.name != 'HR_STAFF':
        raise PermissionDenied("You do not have permission to access the HR dashboard.")
    
    context = {}
    template_name = get_template_path('dashboard.html', request.user.role)
    return render(request, template_name, context)

@login_required
def support_dashboard(request):
    if not request.user.role or request.user.role.name not in ['SUPPORT_MANAGER', 'SUPPORT_STAFF']:
        raise PermissionDenied("You do not have permission to access the support dashboard.")
    
    context = {}
    template_name = get_template_path('dashboard.html', request.user.role)
    return render(request, template_name, context)