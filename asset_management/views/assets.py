# Standard library imports
import logging
from datetime import timedelta

# Django imports
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q, Sum
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# Local imports
from access_control.permissions import PermissionManager
from error_handling.views import handler403, handler500
from ..models import Asset, AssetCategory
from ..forms import AssetForm
from ..utils import get_template_path

# Initialize logger
logger = logging.getLogger(__name__)


class TotalAssetsView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'asset_management')

    def get_template_name(self):
        return get_template_path('assets/total_assets.html', self.request.user.role, 'asset_management')

    def get(self, request):
        try:
            # Get filter parameters
            search_query = request.GET.get('search', '')
            category = request.GET.get('category', '')
            status = request.GET.get('status', '')
            condition = request.GET.get('condition', '')

            # Base queryset
            assets = Asset.objects.select_related('category').filter(is_active=True)

            # Apply filters
            if search_query:
                assets = assets.filter(
                    Q(name__icontains=search_query) |
                    Q(asset_id__icontains=search_query) |
                    Q(manufacturer__icontains=search_query)
                )
            if category:
                assets = assets.filter(category_id=category)
            if status:
                assets = assets.filter(status=status)
            if condition:
                assets = assets.filter(condition=condition)

            # Pagination
            page = request.GET.get('page', 1)
            paginator = Paginator(assets, 10)  # Show 10 assets per page
            try:
                assets = paginator.page(page)
            except PageNotAnInteger:
                assets = paginator.page(1)
            except EmptyPage:
                assets = paginator.page(paginator.num_pages)

            # Get filter options
            categories = AssetCategory.objects.filter(is_active=True)
            status_choices = Asset.STATUS_CHOICES
            condition_choices = Asset.CONDITION_CHOICES

            context = {
                'assets': assets,
                'categories': categories,
                'status_choices': status_choices,
                'condition_choices': condition_choices,
                'search_query': search_query,
                'selected_category': category,
                'selected_status': status,
                'selected_condition': condition,
                'has_filters': bool(search_query or category or status or condition),
            }

            return render(request, self.get_template_name(), context)
        except Exception as e:
            logger.error(f"Error in total assets view: {str(e)}")
            messages.error(request, "An error occurred while loading the assets")
            return redirect('asset_dashboard')
        

class AddAssetView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        """Check if user has permission to add assets"""
        return PermissionManager.check_module_modify(self.request.user, 'asset_management')

    def dispatch(self, request, *args, **kwargs):
        """Handle unauthorized access"""
        try:
            if not self.test_func():
                messages.error(request, "You don't have permission to add assets")
                return handler403(request, exception="Access Denied")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in add asset dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing the page")
            return redirect('asset_dashboard')

    def get_template_name(self):
        """Get appropriate template based on user role"""
        try:
            return get_template_path('assets/add_asset.html', self.request.user.role, 'asset_management')
        except Exception as e:
            logger.error(f"Error getting template path: {str(e)}")
            return None

    def get(self, request):
        try:
            form = AssetForm()
            return render(request, self.get_template_name(), {'form': form})
        except Exception as e:
            logger.error(f"Error in add asset view: {str(e)}")
            messages.error(request, "An error occurred while loading the form")
            return redirect('asset_dashboard')

    def post(self, request):
        try:
            form = AssetForm(request.POST, request.FILES)
            if form.is_valid():
                asset = form.save()
                messages.success(request, f"Asset {asset.name} was created successfully")
                return redirect('asset_dashboard')
            return render(request, self.get_template_name(), {'form': form})
        except Exception as e:
            logger.error(f"Error saving asset: {str(e)}")
            messages.error(request, "An error occurred while saving the asset")
            return render(request, self.get_template_name(), {'form': form})