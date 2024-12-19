# Standard library imports
import logging

# Django core imports
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Sum, F
from django.db import models
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views import View
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView

# Local application imports
from access_control.models import Role
from access_control.permissions import PermissionManager
from error_handling.views import handler403, handler404, handler500
from .models import (
    Medication,
    MedicationStock,
    PurchaseOrder,
    Supplier,
    PurchaseOrderItem,
    StockAdjustment
)
from django.forms import formset_factory
from .forms import MedicationForm, StockAdjustmentForm

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

            now = timezone.now()
            month_start = now.replace(day=1)

            # Enhanced analytics
            monthly_revenue = PurchaseOrder.objects.filter(
                status='RECEIVED',
                order_date__gte=month_start,
                order_date__lte=now
            ).aggregate(total=Sum('total_amount'))['total'] or 0

            previous_month = (month_start - timezone.timedelta(days=1)).replace(day=1)
            previous_revenue = PurchaseOrder.objects.filter(
                status='RECEIVED',
                order_date__gte=previous_month,
                order_date__lte=month_start
            ).aggregate(total=Sum('total_amount'))['total'] or 0

            # Calculate revenue growth percentage
            if previous_revenue > 0:
                revenue_growth = ((monthly_revenue - previous_revenue) / previous_revenue) * 100
            else:
                revenue_growth = 0

            context = {
                'medications': medications,
                'suppliers': Supplier.objects.all(),
                'purchase_orders': purchase_orders,
                'low_stock_count': MedicationStock.objects.filter(
                    quantity__lte=F('reorder_level')
                ).count(),
                'monthly_revenue': monthly_revenue,
                'revenue_growth': revenue_growth,
                'total_medications': medications.count(),
                'pending_orders': purchase_orders.count(),
                'recent_transactions': PurchaseOrder.objects.select_related(
                    'supplier'
                ).order_by('-order_date')[:5],
                'stock_alerts': self.get_stock_alerts(),
            }

            return context
        except Exception as e:
            logger.error(f"Error getting pharmacy context data: {str(e)}")
            return {}

    def get_stock_alerts(self):
        return MedicationStock.objects.select_related('medication').filter(
            quantity__lte=F('reorder_level')
        ).order_by(
            'quantity'
        )[:5]

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

class PurchaseOrderCreateView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if not PermissionManager.check_module_access(request.user, 'pharmacy_management'):
            messages.error(request, "You don't have permission to create purchase orders")
            return handler403(request, exception="Access denied to purchase order creation")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        try:
            template_path = get_template_path('purchase_order_form.html', request.user.role, 'pharmacy_management')
            context = {
            }
            return render(request, template_path, context)
        except Exception as e:
            logger.error(f"Error loading purchase order form: {str(e)}")
            messages.error(request, "Error loading purchase order form")
            return handler500(request, exception=str(e))

class MedicationCreateView(LoginRequiredMixin, CreateView):
    form_class = MedicationForm
    success_url = reverse_lazy('pharmacy_management')

    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_access(request.user, 'pharmacy_management'):
                messages.error(request, "You don't have permission to add medications")
                return handler403(request, exception="Access denied to medication creation")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in medication creation dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing medication creation")
            return handler500(request, exception=str(e))

    def get_template_names(self):
        return [get_template_path('add_medication.html', self.request.user.role, 'pharmacy_management')]

    def form_valid(self, form):
        try:
            medication = form.save(commit=False)
            medication.save()
            
            # Create initial stock record
            MedicationStock.objects.create(
                medication=medication,
                quantity=form.cleaned_data['initial_stock'],
                reorder_level=form.cleaned_data['reorder_level']
            )
            
            messages.success(self.request, f"Medication '{medication.name}' added successfully")
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error saving medication: {str(e)}")
            messages.error(self.request, "Error saving medication")
            return self.form_invalid(form)

class StockAdjustmentView(LoginRequiredMixin, CreateView):
    form_class = StockAdjustmentForm
    success_url = reverse_lazy('pharmacy_management')

    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_access(request.user, 'pharmacy_management'):
                messages.error(request, "You don't have permission to adjust stock")
                return handler403(request, exception="Access denied to stock adjustment")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in stock adjustment dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing stock adjustment")
            return handler500(request, exception=str(e))

    def get_template_names(self):
        return [get_template_path('stock_adjustment.html', self.request.user.role, 'pharmacy_management')]

    def form_valid(self, form):
        try:
            form.instance.adjusted_by = self.request.user
            adjustment = form.save()
            
            # Add success message with details
            messages.success(
                self.request,
                f"Stock adjusted successfully: {adjustment.get_adjustment_type_display()} "
                f"of {abs(adjustment.quantity)} units for {adjustment.medication.name}"
            )
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error saving stock adjustment: {str(e)}")
            messages.error(self.request, "Error adjusting stock")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_adjustments'] = StockAdjustment.objects.select_related(
            'medication', 'adjusted_by'
        ).order_by('-adjusted_at')[:5]
        return context

class LowStockItemsView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_access(request.user, 'pharmacy_management'):
                messages.error(request, "You don't have permission to view low stock items")
                return handler403(request, exception="Access denied to low stock items")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in low stock items dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing low stock items")
            return handler500(request, exception=str(e))

    def get(self, request):
        try:
            template_path = get_template_path('low_stock_items.html', request.user.role, 'pharmacy_management')
            context = self.get_context_data()

            try:
                page = request.GET.get('page', 1)
                paginator = Paginator(context['medications'], 10)
                context['medications'] = paginator.page(page)
                context['paginator'] = paginator
            except (PageNotAnInteger, EmptyPage) as e:
                logger.error(f"Pagination error: {str(e)}")
                messages.warning(request, "Error loading page data")
                context['medications'] = []

            return render(request, template_path, context)
        except Exception as e:
            logger.error(f"Error in low stock items view: {str(e)}")
            messages.error(request, "An error occurred while loading low stock items")
            return handler500(request, exception=str(e))

    def get_context_data(self):
        try:
            medications = MedicationStock.objects.select_related(
                'medication'
            ).filter(
                quantity__lte=F('reorder_level')
            ).order_by(
                'quantity'
            )

            return {
                'medications': medications,
                'total_low_stock': medications.count(),
                'critical_items': medications.filter(quantity=0).count(),
                'total_value': sum(
                    med.medication.price * med.quantity 
                    for med in medications
                ),
            }
        except Exception as e:
            logger.error(f"Error getting low stock context data: {str(e)}")
            return {}

class AllMedicationsView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_access(request.user, 'pharmacy_management'):
                messages.error(request, "You don't have permission to view medications")
                return handler403(request, exception="Access denied to medications list")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in medications list dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing medications list")
            return handler500(request, exception=str(e))

    def get(self, request):
        try:
            template_path = get_template_path('all_medications.html', request.user.role, 'pharmacy_management')
            context = self.get_context_data(request)
            return render(request, template_path, context)
        except Exception as e:
            logger.error(f"Error in medications list view: {str(e)}")
            messages.error(request, "An error occurred while loading medications list")
            return handler500(request, exception=str(e))

    def get_context_data(self, request):
        try:
            # Get filter parameters
            search_query = request.GET.get('search', '')
            medication_type = request.GET.get('type', '')
            status = request.GET.get('status', '')

            # Base queryset with explicit ordering
            medications = Medication.objects.select_related('stock').all().order_by('name', 'id')

            # Apply filters
            if search_query:
                medications = medications.filter(
                    models.Q(name__icontains=search_query) |
                    models.Q(generic_name__icontains=search_query) |
                    models.Q(manufacturer__icontains=search_query)
                )

            if medication_type:
                medications = medications.filter(requires_prescription=(medication_type == 'PRESCRIPTION'))

            if status:
                if status == 'LOW_STOCK':
                    medications = medications.filter(stock__quantity__lte=F('stock__reorder_level'))
                elif status == 'OUT_OF_STOCK':
                    medications = medications.filter(stock__quantity=0)

            # Get counts before pagination
            total_count = medications.count()
            active_count = medications.filter(is_active=True).count()
            low_stock_count = medications.filter(stock__quantity__lte=F('stock__reorder_level')).count()

            # Pagination
            page = request.GET.get('page', 1)
            paginator = Paginator(medications, 10)
            try:
                paginated_medications = paginator.page(page)
            except (PageNotAnInteger, EmptyPage):
                paginated_medications = paginator.page(1)

            return {
                'medications': paginated_medications,
                'paginator': paginator,
                'total_count': total_count,
                'active_count': active_count,
                'low_stock_count': low_stock_count,
                'filters': {
                    'search': search_query,
                    'type': medication_type,
                    'status': status
                }
            }
        except Exception as e:
            logger.error(f"Error getting medications context data: {str(e)}")
            return {}