
def get_dashboard_url(request):
    """
    Returns the appropriate dashboard URL based on user role.
    """
    if not request.user.is_authenticated:
        return {'dashboard_url': '/'}
        
    role_urls = {
        'SUPER_ADMIN': 'admin_dashboard',
        'ADMIN': 'admin_dashboard',
        'MANAGER': 'admin_dashboard',
        'DOCTOR': 'doctor_dashboard',
        'NURSE': 'nurse_dashboard',
        'MEDICAL_ASSISTANT': 'medical_dashboard',
        'RECEPTIONIST': 'reception_dashboard',
        'PHARMACIST': 'pharmacy_dashboard',
        'LAB_TECHNICIAN': 'lab_dashboard',
        'BILLING_STAFF': 'billing_dashboard',
        'INVENTORY_MANAGER': 'inventory_dashboard',
        'HR_STAFF': 'hr_dashboard',
        'SUPPORT_STAFF': 'support_dashboard',
        'SUPPORT_MANAGER': 'support_dashboard',
        'PATIENT': 'patient_dashboard'
    }
    
    if hasattr(request.user, 'role') and request.user.role:
        return {'dashboard_url': role_urls.get(request.user.role.name, '/')}
    return {'dashboard_url': '/'}