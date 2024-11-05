# views.py

from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from django.db.models import Sum, F, Count
from django.http import HttpResponse
from django.utils import timezone
from .models import ItemCategory, StockItem, StockMovement

def get_template_path(base_template, user_role):
    """
    Resolves template path based on user role.
    """
    role_template_map = {
        'ADMIN': 'admin',
        'STORE_MANAGER': 'store',
        'STORE_KEEPER': 'store',
        'SUPER_ADMIN': 'admin',
        'DOCTOR': 'doctor',
        'MANAGER': 'admin',
        'PHARMACIST': 'pharmacy',
        'INVENTORY_STAFF': 'store'
    }
    
    role_folder = role_template_map.get(user_role)
    if not role_folder:
        return None
    return f'dashboard/{role_folder}/stock_management/{base_template}'

class StockManagementView(View):
    def get(self, request):
        try:
            user_role = request.user.role
            template_path = get_template_path('stock_dashboard.html', user_role)
            
            if not template_path:
                return HttpResponse("Unauthorized access", status=403)

            # Fetch all stock items, categories, and stock movements
            stock_items = StockItem.objects.all()
            categories = ItemCategory.objects.all()
            stock_movements = StockMovement.objects.all()

            # Calculate statistics
            total_items = stock_items.count()
            low_stock_count = stock_items.filter(current_quantity__lte=F('reorder_point')).count()
            total_stock_value = stock_items.aggregate(total_value=Sum(F('current_quantity') * F('unit_price')))['total_value'] or 0
            total_stock_value = round(total_stock_value, 2)
            monthly_transactions = stock_movements.filter(date__gte=timezone.now().replace(day=1)).count()

            # Pagination for stock items
            paginator = Paginator(stock_items, 10)  # Show 10 stock items per page
            page = request.GET.get('page')
            try:
                stock_items = paginator.page(page)
            except PageNotAnInteger:
                stock_items = paginator.page(1)
            except EmptyPage:
                stock_items = paginator.page(paginator.num_pages)

            # Context data to be passed to the template
            context = {
                'items': stock_items,
                'categories': categories,
                'total_items': total_items,
                'low_stock_count': low_stock_count,
                'total_stock_value': total_stock_value,
                'monthly_transactions': monthly_transactions,
                'paginator': paginator,
                'page_obj': stock_items,
            }

            return render(request, template_path, context)

        except Exception as e:
            # Handle any exceptions that occur
            return HttpResponse(f"An error occurred: {str(e)}", status=500)