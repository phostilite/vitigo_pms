# views.py

from django.shortcuts import render
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from .models import Medication, MedicationStock, Supplier, PurchaseOrder, Prescription
from django.db.models import Sum, F
from django.utils import timezone

class PharmacyManagementView(View):
    template_name = 'dashboard/admin/pharmacy_management/pharmacy_dashboard.html'

    def get(self, request):
        try:
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

            return render(request, self.template_name, context)

        except Exception as e:
            # Handle any exceptions that occur
            return HttpResponse(f"An error occurred: {str(e)}", status=500)