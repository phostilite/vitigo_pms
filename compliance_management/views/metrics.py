# Standard Library imports
import logging
from datetime import datetime, timedelta

# Django imports
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

# Local/Relative imports
from access_control.utils import PermissionManager
from error_handling.views import handler403, handler500, handler401
from ..models import ComplianceMetric
from ..utils import get_template_path

# Configure logging
logger = logging.getLogger(__name__)

class ComplianceMetricListView(LoginRequiredMixin, ListView):
    """View for listing compliance metrics"""
    model = ComplianceMetric
    context_object_name = 'metrics'
    paginate_by = 10
    
    def get_template_names(self):
        try:
            return [get_template_path(
                'metrics/metric_list.html',
                self.request.user.role,
                'compliance_management'
            )]
        except Exception as e:
            logger.error(f"Template retrieval error: {str(e)}")
            return handler500(self.request, exception="Error loading metrics template")

    def get_queryset(self):
        queryset = ComplianceMetric.objects.select_related('patient', 'evaluated_by')
        
        # Apply filters
        metric_type = self.request.GET.get('metric_type')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        search = self.request.GET.get('search')

        if metric_type:
            queryset = queryset.filter(metric_type=metric_type)
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(evaluation_date__gte=date_from)
            except ValueError:
                pass
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(evaluation_date__lte=date_to)
            except ValueError:
                pass
        if search:
            queryset = queryset.filter(
                Q(patient__first_name__icontains=search) |
                Q(patient__last_name__icontains=search)
            )

        return queryset.order_by('-evaluation_date')

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            context.update({
                'metric_type_choices': ComplianceMetric.metric_type.field.choices,
                'current_filters': {
                    'metric_type': self.request.GET.get('metric_type', ''),
                    'date_from': self.request.GET.get('date_from', ''),
                    'date_to': self.request.GET.get('date_to', ''),
                    'search': self.request.GET.get('search', '')
                },
                'low_compliance_count': self.model.objects.filter(
                    compliance_score__lt=60
                ).count(),
                'recent_evaluations': self.model.objects.filter(
                    evaluation_date__gte=timezone.now().date() - timedelta(days=7)
                ).count()
            })
            return context
        except Exception as e:
            logger.error(f"Error in metrics list context: {str(e)}")
            return {}

class ComplianceMetricDetailView(LoginRequiredMixin, DetailView):
    """View for displaying metric details"""
    model = ComplianceMetric
    context_object_name = 'metric'
    
    def get_template_names(self):
        try:
            return [get_template_path(
                'metrics/metric_detail.html',
                self.request.user.role,
                'compliance_management'
            )]
        except Exception as e:
            logger.error(f"Template retrieval error: {str(e)}")
            return handler500(self.request, exception="Error loading metric detail template")

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            metric = self.get_object()
            
            # Get historical metrics for the same type
            historical_metrics = self.model.objects.filter(
                patient=metric.patient,
                metric_type=metric.metric_type,
                evaluation_date__lt=metric.evaluation_date
            ).order_by('-evaluation_date')[:5]

            # Get related issues
            related_issues = metric.patient.compliance_issues.filter(
                created_at__range=[
                    metric.evaluation_period_start,
                    metric.evaluation_period_end
                ]
            ).order_by('-created_at')

            context.update({
                'historical_metrics': historical_metrics,
                'related_issues': related_issues,
                'improvement': self._calculate_improvement(metric, historical_metrics.first())
            })
            return context
        except Exception as e:
            logger.error(f"Error in metric detail context: {str(e)}")
            return {}

    def _calculate_improvement(self, current_metric, previous_metric):
        """Calculate improvement percentage from previous metric"""
        if not previous_metric:
            return None
        
        difference = current_metric.compliance_score - previous_metric.compliance_score
        return {
            'value': difference,
            'is_positive': difference > 0
        }