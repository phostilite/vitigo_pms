from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
from django.views import View
from django.db.models import Q

from access_control.permissions import PermissionManager
from error_handling.views import handler403, handler500
from ..models import AssetAudit
from ..utils import get_template_path

import logging
logger = logging.getLogger(__name__)

class TotalAuditsView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'asset_management')

    def dispatch(self, request, *args, **kwargs):
        if not self.test_func():
            messages.error(request, "You don't have permission to view audits")
            return handler403(request, exception="Access Denied")
        return super().dispatch(request, *args, **kwargs)

    def get_template_name(self):
        return get_template_path('audits/total_audits.html', self.request.user.role, 'asset_management')

    def get(self, request):
        try:
            # Get filter parameters
            search_query = request.GET.get('search', '')
            status = request.GET.get('status', '')
            date_from = request.GET.get('date_from', '')
            date_to = request.GET.get('date_to', '')

            # Base queryset
            audits = AssetAudit.objects.select_related('asset').order_by('-audit_date')

            # Apply filters
            if search_query:
                audits = audits.filter(
                    Q(asset__name__icontains=search_query) |
                    Q(asset__asset_id__icontains=search_query) |
                    Q(conducted_by__icontains=search_query)
                )
            if status:
                audits = audits.filter(status=status)
            if date_from:
                audits = audits.filter(audit_date__gte=date_from)
            if date_to:
                audits = audits.filter(audit_date__lte=date_to)

            # Pagination
            page = request.GET.get('page', 1)
            paginator = Paginator(audits, 10)
            try:
                audits = paginator.page(page)
            except PageNotAnInteger:
                audits = paginator.page(1)
            except EmptyPage:
                audits = paginator.page(paginator.num_pages)

            context = {
                'audits': audits,
                'search_query': search_query,
                'selected_status': status,
                'date_from': date_from,
                'date_to': date_to,
                'status_choices': AssetAudit.STATUS_CHOICES,
                'has_filters': bool(search_query or status or date_from or date_to),
                'user_role': request.user.role.name if request.user.role else None,
                'module_name': 'Asset Management',
                'page_title': 'Asset Audits'
            }

            return render(request, self.get_template_name(), context)
        except Exception as e:
            logger.error(f"Error in total audits view: {str(e)}")
            messages.error(request, "An error occurred while loading asset audits")
            return handler500(request, exception=str(e))
