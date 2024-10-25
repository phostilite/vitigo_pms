from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

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
    # Add any context data needed for the admin dashboard
    context = {}
    return render(request, 'dashboard/admin/admin_dashboard.html', context)

@login_required
def staff_dashboard(request):
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to access the staff dashboard.")
    # Add any context data needed for the staff dashboard
    context = {}
    return render(request, 'dashboard/staff/staff_dashboard.html', context)