from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from patient_management.models import Patient
from django.utils import timezone
from datetime import timedelta
from appointment_management.models import Appointment
from phototherapy_management.models import PhototherapySession
from django.contrib.auth import get_user_model
from stock_management.models import StockItem
from django.db.models import F

User = get_user_model()

@login_required
def dashboard_router(request):
    user = request.user
    if user.role == 'PATIENT':
        return patient_dashboard(request)
    elif user.role == 'ADMIN':
        return admin_dashboard(request)
    elif user.is_staff:
        return staff_dashboard(request)
    else:
        raise PermissionDenied("You do not have permission to access any dashboard.")

@login_required
def patient_dashboard(request):
    if request.user.role != 'PATIENT':
        raise PermissionDenied("You do not have permission to access the patient dashboard.")
    # Add any context data needed for the patient dashboard
    context = {}
    return render(request, 'dashboard/patient/patient_dashboard.html', context)

@login_required
def admin_dashboard(request):
    if request.user.role != 'ADMIN':
        raise PermissionDenied("You do not have permission to access the admin dashboard.")
    
    # Calculate total patients
    total_patients = User.objects.filter(role='PATIENT').count()
    
    # Calculate new patients percentage (e.g., patients added in the last month)
    one_month_ago = timezone.now() - timedelta(days=30)
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
    male_count = User.objects.filter(role='PATIENT', gender='M').count()
    female_count = User.objects.filter(role='PATIENT', gender='F').count()
    other_count = User.objects.filter(role='PATIENT', gender='O').count()

    # Get low stock items
    low_stock_items = StockItem.objects.filter(current_quantity__lte=F('reorder_point'))

    # Add any other context data needed for the admin dashboard
    context = {
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
        'low_stock_items': low_stock_items,
    }
    
    return render(request, 'dashboard/admin/admin_dashboard.html', context)

@login_required
def staff_dashboard(request):
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to access the staff dashboard.")
    # Add any context data needed for the staff dashboard
    context = {}
    return render(request, 'dashboard/staff/staff_dashboard.html', context)