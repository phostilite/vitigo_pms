# Standard library imports
import logging

# Django core imports
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Sum, F
from django.shortcuts import render
from django.utils import timezone
from django.views import View

# Local application imports
from access_control.models import Role
from access_control.permissions import PermissionManager
from error_handling.views import handler403, handler404, handler500
from .models import (
    Medication,
    MedicationStock,
    PurchaseOrder,
    Supplier
)

# Configure logging and user model
User = get_user_model()
logger = logging.getLogger(__name__)

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

class PharmacyManagementView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_access(request.user, 'pharmacy_management'):
                messages.error(request, "You don't have permission to access Pharmacy Management")
                return handler403(request, exception="Access denied to pharmacy management")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in pharmacy management dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing pharmacy management")
            return handler500(request, exception=str(e))

    def get(self, request):
        try:
            template_path = get_template_path('pharmacy_dashboard.html', request.user.role, 'pharmacy_management')
            context = self.get_context_data()

            # Pagination for medications
            try:
                page = request.GET.get('page', 1)
                paginator = Paginator(context['medications'], 10)
                context['medications'] = paginator.page(page)
                context['paginator'] = paginator
            except PageNotAnInteger:
                context['medications'] = paginator.page(1)
            except EmptyPage:
                context['medications'] = paginator.page(paginator.num_pages)
            except Exception as e:
                logger.error(f"Pagination error: {str(e)}")
                messages.warning(request, "Error loading page data")

            return render(request, template_path, context)

        except Exception as e:
            logger.error(f"Error in pharmacy management view: {str(e)}")
            messages.error(request, "An error occurred while loading pharmacy data")
            return handler500(request, exception=str(e))

    def get_context_data(self):
        try:
            medications = Medication.objects.select_related(
                'stock'
            ).all()

            purchase_orders = PurchaseOrder.objects.select_related(
                'supplier',
                'created_by'
            ).prefetch_related(
                'items__medication'
            ).filter(status='PENDING')

            context = {
                'medications': medications,
                'suppliers': Supplier.objects.all(),
                'purchase_orders': purchase_orders,
            }

            # Calculate statistics
            now = timezone.now()
            context.update({
                'low_stock_count': MedicationStock.objects.filter(
                    quantity__lte=F('reorder_level')
                ).count(),
                'monthly_revenue': purchase_orders.filter(
                    status='RECEIVED',
                    order_date__month=now.month,
                    order_date__year=now.year
                ).aggregate(total=Sum('total_amount'))['total'] or 0,
                'pending_orders': purchase_orders.count(),
            })

            return context
        except Exception as e:
            logger.error(f"Error getting pharmacy context data: {str(e)}")
            return {}

class MedicationDetailView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_access(request.user, 'pharmacy_management'):
                messages.error(request, "You don't have permission to view medication details")
                return handler403(request, exception="Access denied to medication details")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in medication detail dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing medication details")
            return handler500(request, exception=str(e))

    def get(self, request, medication_id):
        try:
            template_path = get_template_path('medication_detail.html', request.user.role, 'pharmacy_management')
            
            medication = self.get_medication_with_relations(medication_id)
            if not medication:
                messages.error(request, "Medication not found")
                return handler404(request, exception="Medication not found")

            context = self.get_context_data(medication)
            return render(request, template_path, context)

        except Exception as e:
            logger.error(f"Error in medication detail view: {str(e)}")
            messages.error(request, "An error occurred while loading medication details")
            return handler500(request, exception=str(e))

    def get_medication_with_relations(self, medication_id):
        try:
            return Medication.objects.select_related(
                'stock'
            ).prefetch_related(
                'purchaseorderitem_set__purchase_order'  # Added to get purchase history
            ).get(id=medication_id)
        except Medication.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error fetching medication: {str(e)}")
            return None

    def get_context_data(self, medication):
        try:
            return {
                'medication': medication,
                'stock_history': medication.stock,  # Changed from stock_records
                'purchase_history': medication.purchaseorderitem_set.select_related(
                    'purchase_order__supplier'
                ).order_by('-purchase_order__order_date'),
                'current_stock': self.get_current_stock(medication),
                'usage_statistics': self.get_usage_statistics(medication),
            }
        except Exception as e:
            logger.error(f"Error getting medication context data: {str(e)}")
            return {'medication': medication}

    def get_current_stock(self, medication):
        try:
            return MedicationStock.objects.filter(
                medication=medication
            ).aggregate(
                total_quantity=Sum('quantity')
            )['total_quantity'] or 0
        except Exception as e:
            logger.error(f"Error calculating current stock: {str(e)}")
            return 0

    def get_usage_statistics(self, medication):
        try:
            now = timezone.now()
            month_start = now.replace(day=1)
            return {
                'monthly_usage': 0,
                'low_stock_alerts': 1 if medication.stock.quantity <= medication.stock.reorder_level else 0
            }
        except Exception as e:
            logger.error(f"Error calculating usage statistics: {str(e)}")
            return {}