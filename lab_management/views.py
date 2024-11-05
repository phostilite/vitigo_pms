# views.py

from django.shortcuts import render
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from .models import LabTest, LabOrder, LabOrderItem, LabResult
from django.db.models import Sum, F
from django.utils import timezone

def get_template_path(base_template, user_role):
    """
    Resolves template path based on user role.
    Example: For 'lab_dashboard.html' and role 'DOCTOR', 
    returns 'dashboard/accountant/lab_management/lab_dashboard.html'
    """
    # Updated role mappings for lab management access
    role_template_map = {
        'ADMIN': 'admin',
        'DOCTOR': 'doctor',
        'NURSE': 'nurse',
        'LAB_TECHNICIAN': 'lab',
        'TECHNICIAN': 'technician',
        'LAB_MANAGER': 'lab',
        'PATHOLOGIST': 'lab'
    }
    
    role_folder = role_template_map.get(user_role)
    if not role_folder:
        return None
    return f'dashboard/{role_folder}/lab_management/{base_template}'

class LabManagementView(View):
    def get(self, request):
        try:
            # Get user role from request
            user_role = request.user.role  # Assuming role is stored in user model

            # Get template path based on user role
            template_path = get_template_path('lab_dashboard.html', user_role)
            if not template_path:
                return HttpResponse("Unauthorized access", status=403)

            # Fetch all lab orders and related data
            lab_orders = LabOrder.objects.all()
            lab_results = LabResult.objects.all()

            # Calculate statistics
            pending_tests = lab_orders.filter(status='ORDERED').count()
            critical_results = lab_results.filter(status='CRITICAL').count()
            completed_tests = lab_orders.filter(status='COMPLETED').count()
            monthly_revenue = LabOrderItem.objects.filter(
                lab_order__status='COMPLETED',
                lab_order__order_date__month=timezone.now().month
            ).aggregate(total=Sum('price'))['total'] or 0
            monthly_revenue = round(monthly_revenue, 2)

            # Pagination for lab orders
            paginator = Paginator(lab_orders, 10)  # Show 10 lab orders per page
            page = request.GET.get('page')
            try:
                lab_orders = paginator.page(page)
            except PageNotAnInteger:
                lab_orders = paginator.page(1)
            except EmptyPage:
                lab_orders = paginator.page(paginator.num_pages)

            # Context data to be passed to the template
            context = {
                'lab_orders': lab_orders,
                'pending_tests': pending_tests,
                'critical_results': critical_results,
                'completed_tests': completed_tests,
                'monthly_revenue': monthly_revenue,
                'paginator': paginator,
                'page_obj': lab_orders,
            }

            return render(request, template_path, context)

        except Exception as e:
            # Handle any exceptions that occur
            return HttpResponse(f"An error occurred: {str(e)}", status=500)