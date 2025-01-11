from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
import logging

from access_control.utils import PermissionManager
from error_handling.views import handler403, handler500, handler401
from ..models import (
    Procedure, ProcedureType, ProcedureCategory,
    ProcedurePrerequisite, ProcedureInstruction
)
from ..utils import get_template_path

logger = logging.getLogger(__name__)

class ProcedureListView(LoginRequiredMixin, ListView):
    model = Procedure
    context_object_name = 'procedures'
    paginate_by = 10
    
    def get_template_names(self):
        try:
            return [get_template_path(
                'procedures/list.html',
                self.request.user.role,
                'procedure_management'
            )]
        except Exception as e:
            logger.error(f"Template retrieval error: {str(e)}")
            return handler500(self.request, "Error loading procedure list template")

    def get_queryset(self):
        queryset = Procedure.objects.select_related(
            'procedure_type',
            'patient',
            'primary_doctor',
            'appointment'
        ).order_by('-scheduled_date', '-scheduled_time')

        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(procedure_type__name__icontains=search_query) |
                Q(patient__first_name__icontains=search_query) |
                Q(patient__last_name__icontains=search_query) |
                Q(primary_doctor__first_name__icontains=search_query) |
                Q(primary_doctor__last_name__icontains=search_query) |
                Q(status__icontains=search_query)
            )

        # Status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status.upper())

        # Date range filter
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(scheduled_date__range=[start_date, end_date])

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            # Add filters data
            context.update({
                'procedure_types': ProcedureType.objects.all(),
                'procedure_categories': ProcedureCategory.objects.all(),
                'status_choices': Procedure.STATUS_CHOICES,
                'current_filters': {
                    'search': self.request.GET.get('search', ''),
                    'status': self.request.GET.get('status', ''),
                    'start_date': self.request.GET.get('start_date', ''),
                    'end_date': self.request.GET.get('end_date', ''),
                },
                'total_procedures': self.get_queryset().count(),
                'today_procedures': self.get_queryset().filter(
                    scheduled_date=timezone.now().date()
                ).count(),
            })
        except Exception as e:
            logger.error(f"Context data error: {str(e)}")
            context['error_message'] = "Error loading procedure data"

        return context

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return handler401(request, "Authentication required")
            
        try:
            if not PermissionManager.check_module_access(request.user, 'procedure_management'):
                logger.warning(f"Access denied for user {request.user} to procedure list")
                return handler403(request, "Access denied to procedure list")

            request.session['last_procedure_action'] = 'view_procedure_list'
            request.session['procedure_access_time'] = timezone.now().isoformat()
            
            return super().dispatch(request, *args, **kwargs)
            
        except Exception as e:
            logger.error(f"Dispatch error: {str(e)}", exc_info=True)
            return handler500(request, "Error accessing procedure list")