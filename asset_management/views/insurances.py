from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
from django.views import View
from django.db.models import Q
from django.utils import timezone

from access_control.permissions import PermissionManager
from error_handling.views import handler403, handler500
from ..models import InsurancePolicy
from ..utils import get_template_path

import logging
logger = logging.getLogger(__name__)

class TotalInsurancesView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'asset_management')

    def dispatch(self, request, *args, **kwargs):
        if not self.test_func():
            messages.error(request, "You don't have permission to view insurances")
            return handler403(request, exception="Access Denied")
        return super().dispatch(request, *args, **kwargs)

    def get_template_name(self):
        return get_template_path('insurances/total_insurances.html', self.request.user.role, 'asset_management')

    def get(self, request):
        try:
            # Get filter parameters
            search_query = request.GET.get('search', '')
            status = request.GET.get('status', '')
            date_from = request.GET.get('date_from', '')
            date_to = request.GET.get('date_to', '')

            # Base queryset
            insurances = InsurancePolicy.objects.select_related('asset').order_by('-start_date')

            # Apply filters
            if search_query:
                insurances = insurances.filter(
                    Q(asset__name__icontains=search_query) |
                    Q(policy_number__icontains=search_query) |
                    Q(provider__icontains=search_query)
                )
            if status:
                insurances = insurances.filter(status=status)
            if date_from:
                insurances = insurances.filter(start_date__gte=date_from)
            if date_to:
                insurances = insurances.filter(end_date__lte=date_to)

            # Update expired policies
            current_date = timezone.now().date()
            expired_policies = insurances.filter(
                end_date__lt=current_date,
                status='ACTIVE'
            )
            expired_policies.update(status='EXPIRED')

            # Pagination
            page = request.GET.get('page', 1)
            paginator = Paginator(insurances, 10)
            try:
                insurances = paginator.page(page)
            except PageNotAnInteger:
                insurances = paginator.page(1)
            except EmptyPage:
                insurances = paginator.page(paginator.num_pages)

            context = {
                'insurances': insurances,
                'search_query': search_query,
                'selected_status': status,
                'date_from': date_from,
                'date_to': date_to,
                'status_choices': InsurancePolicy.STATUS_CHOICES,
                'has_filters': bool(search_query or status or date_from or date_to),
                'user_role': request.user.role.name if request.user.role else None,
                'module_name': 'Asset Management',
                'page_title': 'Insurance Policies'
            }

            return render(request, self.get_template_name(), context)
        except Exception as e:
            logger.error(f"Error in total insurances view: {str(e)}")
            messages.error(request, "An error occurred while loading insurance policies")
            return handler500(request, exception=str(e))
