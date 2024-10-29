from django.views.generic import ListView
from django.db.models import Count, Q
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Query, QueryTag

class QueryManagementView(LoginRequiredMixin, ListView):
    model = Query
    template_name = 'dashboard/admin/query_management/query_dashboard.html'
    context_object_name = 'queries'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Query.objects.select_related(
            'patient', 
            'assigned_to'
        ).prefetch_related(
            'tags',
            'updates',
            'attachments'
        )
        
        # Apply filters based on GET parameters
        filters = {}
        
        # Priority filter
        priority = self.request.GET.get('priority')
        if priority:
            filters['priority'] = priority
            
        # Status filter
        status = self.request.GET.get('status')
        if status:
            filters['status'] = status
            
        # Source filter
        source = self.request.GET.get('source')
        if source:
            filters['source'] = source
            
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(subject__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(patient__first_name__icontains=search_query) |
                Q(patient__last_name__icontains=search_query) |
                Q(query_id__icontains=search_query)
            )
            
        return queryset.filter(**filters)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current date for calculations
        current_date = timezone.now()
        start_of_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Add analytics data
        context.update({
            'total_queries': Query.objects.count(),
            'open_queries': Query.objects.filter(
                status__in=['NEW', 'IN_PROGRESS', 'WAITING']
            ).count(),
            
            # Get commonly used tags for filtering
            'common_tags': QueryTag.objects.annotate(
                query_count=Count('query')
            ).order_by('-query_count')[:10],
            
            # Calculate resolution metrics
            'resolved_this_month': Query.objects.filter(
                resolved_at__gte=start_of_month
            ).count(),
            
            # Current filters for template
            'current_filters': {
                'priority': self.request.GET.get('priority', ''),
                'status': self.request.GET.get('status', ''),
                'source': self.request.GET.get('source', ''),
                'search': self.request.GET.get('search', ''),
            },
        })
        
        return context