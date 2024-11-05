# views.py

from django.shortcuts import render
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from .models import Medication, MedicationStock, Supplier, PurchaseOrder, Prescription
from django.db.models import Sum, F
from django.utils import timezone

def get_template_path(base_template, user_role):
    """
    Resolves template path based on user role.
    """
    # Updated role mappings for pharmacy management access
    role_template_map = {
        'ADMIN': 'admin',
        'DOCTOR': 'doctor',
        'NURSE': 'nurse',
        'PHARMACIST': 'pharmacy',
        'RECEPTIONIST': 'reception',
        'SUPER_ADMIN': 'admin',
        'MANAGER': 'admin'
    }
    
    role_folder = role_template_map.get(user_role)
    if not role_folder:
        return None
    return f'dashboard/{role_folder}/pharmacy_management/{base_template}'

class PharmacyManagementView(View):
    def get(self, request):
        try:
            user_role = request.user.role  # Assuming role is stored in user model
            template_path = get_template_path('pharmacy_dashboard.html', user_role)
            
            if not template_path:
                return HttpResponse("Unauthorized access", status=403)

            # Fetch all medications, suppliers, and prescriptions
            medications = Medication.objects.all()
            suppliers = Supplier.objects.all()
            prescriptions = Prescription.objects.filter(status='PENDING')
            purchase_orders = PurchaseOrder.objects.filter(status='PENDING')

            # Calculate statistics
            active_prescriptions = prescriptions.count()
            low_stock_count = MedicationStock.objects.filter(quantity__lte=F('reorder_level')).count()
            monthly_revenue = PurchaseOrder.objects.filter(status='RECEIVED', order_date__month=timezone.now().month).aggregate(total=Sum('total_amount'))['total'] or 0
            pending_orders = purchase_orders.count()

            # Pagination for medications
            paginator = Paginator(medications, 10)  # Show 10 medications per page
            page = request.GET.get('page')
            try:
                medications = paginator.page(page)
            except PageNotAnInteger:
                medications = paginator.page(1)
            except EmptyPage:
                medications = paginator.page(paginator.num_pages)

            # Context data to be passed to the template
            context = {
                'medications': medications,
                'suppliers': suppliers,
                'active_prescriptions': active_prescriptions,
                'low_stock_count': low_stock_count,
                'monthly_revenue': round(monthly_revenue, 2),
                'pending_orders': pending_orders,
                'paginator': paginator,
                'page_obj': medications,
            }

            return render(request, template_path, context)

        except Exception as e:
            return HttpResponse(f"An error occurred: {str(e)}", status=500)