from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
from django.db.models import Count, Q
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Query, QueryTag

def get_template_path(base_template, user_role):
    """
    Resolves template path based on user role.
    """
    role_template_map = {
        'ADMIN': 'admin',
        'DOCTOR': 'doctor',
        'NURSE': 'nurse',
        'SUPER_ADMIN': 'admin',
        'MANAGER': 'admin',
        'RECEPTIONIST': 'reception',
        'STAFF': 'staff'
    }
    
    role_folder = role_template_map.get(user_role)
    if not role_folder:
        return None
    return f'dashboard/{role_folder}/query_management/{base_template}'

class QueryManagementView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            user_role = request.user.role
            template_path = get_template_path('query_dashboard.html', user_role)
            
            if not template_path:
                return HttpResponse("Unauthorized access", status=403)

            # Get base queryset with all relations
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
            for param in ['priority', 'status', 'source']:
                if request.GET.get(param):
                    filters[param] = request.GET.get(param)
                    
            # Apply filters to queryset
            filtered_queries = queryset.filter(**filters)
            
            # Search functionality
            search_query = request.GET.get('search')
            if search_query:
                filtered_queries = filtered_queries.filter(
                    Q(subject__icontains=search_query) |
                    Q(description__icontains=search_query) |
                    Q(patient__first_name__icontains=search_query) |
                    Q(patient__last_name__icontains=search_query) |
                    Q(query_id__icontains=search_query)
                )

            # Pagination
            paginator = Paginator(filtered_queries, 10)
            page = request.GET.get('page')
            try:
                queries = paginator.page(page)
            except PageNotAnInteger:
                queries = paginator.page(1)
            except EmptyPage:
                queries = paginator.page(paginator.num_pages)

            # Get current date for calculations
            current_date = timezone.now()
            start_of_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            # Context data
            context = {
                'queries': queries,
                'total_queries': Query.objects.count(),
                'open_queries': Query.objects.filter(
                    status__in=['NEW', 'IN_PROGRESS', 'WAITING']
                ).count(),
                'common_tags': QueryTag.objects.annotate(
                    query_count=Count('query')
                ).order_by('-query_count')[:10],
                'resolved_this_month': Query.objects.filter(
                    resolved_at__gte=start_of_month
                ).count(),
                'current_filters': {
                    'priority': request.GET.get('priority', ''),
                    'status': request.GET.get('status', ''),
                    'source': request.GET.get('source', ''),
                    'search': request.GET.get('search', ''),
                },
                'paginator': paginator,
                'page_obj': queries,
            }

            return render(request, template_path, context)

        except Exception as e:
            return HttpResponse(f"An error occurred: {str(e)}", status=500)
