# views.py

from django.shortcuts import render
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from .models import LabTest, LabOrder, LabOrderItem, LabResult
from django.db.models import Sum, F
from django.utils import timezone
from access_control.models import Role

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
        return f'dashboard/{role_folder}/{module}/{base_template}'
    return f'dashboard/{role_folder}/{base_template}'

class LabManagementView(View):
    def get(self, request):
        try:
            template_path = get_template_path('lab_dashboard.html', request.user.role, 'lab_management')
            
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