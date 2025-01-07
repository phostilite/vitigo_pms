import logging
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import render, redirect
from django.views import View

from ..models import PerformanceReview, Employee
from access_control.permissions import PermissionManager
from error_handling.views import handler403, handler500
from hr_management.utils import get_template_path
from ..forms import PerformanceReviewForm

# Initialize logger
logger = logging.getLogger(__name__)

class PerformanceListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = PerformanceReview
    context_object_name = 'reviews'
    paginate_by = 10

    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'hr_management')

    def get_template_name(self):
        return get_template_path('performance/review_list.html', self.request.user.role, 'hr_management')

    def dispatch(self, request, *args, **kwargs):
        try:
            if not self.test_func():
                messages.error(request, "You don't have permission to access Performance Reviews")
                return handler403(request, exception="Access Denied")
            
            template_path = self.get_template_name()
            if not template_path:
                return handler403(request, exception="Unauthorized access")
            
            self.template_name = template_path
            return super().dispatch(request, *args, **kwargs)
            
        except Exception as e:
            logger.exception(f"Error in PerformanceListView dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing performance reviews.")
            return handler500(request, exception=str(e))

    def get_queryset(self):
        try:
            queryset = PerformanceReview.objects.select_related('employee', 'reviewer').all()
            
            # Apply search filter
            search_query = self.request.GET.get('search', '')
            if search_query:
                queryset = queryset.filter(
                    Q(employee__user__first_name__icontains=search_query) |
                    Q(employee__user__last_name__icontains=search_query) |
                    Q(employee__employee_id__icontains=search_query)
                )

            # Apply status filter
            status_filter = self.request.GET.get('status', '')
            if status_filter:
                queryset = queryset.filter(status=status_filter)

            # Apply date range filter
            date_filter = self.request.GET.get('date_range', '')
            if date_filter == 'upcoming':
                queryset = queryset.filter(review_date__gte=timezone.now().date())
            elif date_filter == 'past':
                queryset = queryset.filter(review_date__lt=timezone.now().date())

            return queryset.order_by('-review_date')
            
        except Exception as e:
            logger.error(f"Error in get_queryset: {str(e)}")
            messages.error(self.request, "Error retrieving performance reviews.")
            return PerformanceReview.objects.none()

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            context.update({
                'page_title': 'Performance Reviews',
                'module_name': 'HR Management',
                'status_filter': self.request.GET.get('status', ''),
                'date_range': self.request.GET.get('date_range', ''),
                'search_query': self.request.GET.get('search', ''),
                'status_choices': PerformanceReview._meta.get_field('status').choices,
                'upcoming_reviews_count': PerformanceReview.objects.filter(
                    review_date__gte=timezone.now().date()
                ).count(),
                'user_role': self.request.user.role.name if self.request.user.role else None,
            })
            return context
            
        except Exception as e:
            logger.error(f"Error in get_context_data: {str(e)}")
            messages.error(self.request, "Error loading page data.")
            return {}

    def get(self, request, *args, **kwargs):
        try:
            template_path = self.get_template_name()
            if not template_path:
                return handler403(request, exception="Unauthorized access")
                
            return super().get(request, *args, **kwargs)
            
        except Exception as e:
            logger.exception(f"Error in PerformanceListView get: {str(e)}")
            messages.error(request, "An error occurred while loading performance reviews.")
            return handler500(request, exception=str(e))

class PerformanceReviewCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'hr_management')

    def get_template_name(self):
        return get_template_path('performance/review_create.html', self.request.user.role, 'hr_management')

    def get(self, request):
        try:
            form = PerformanceReviewForm()
            return render(request, self.get_template_name(), {
                'form': form,
                'page_title': 'Create Performance Review'
            })
        except Exception as e:
            logger.error(f"Error in PerformanceReviewCreateView GET: {str(e)}")
            messages.error(request, "Error loading performance review form")
            return redirect('performance_reviews')

    def post(self, request):
        try:
            form = PerformanceReviewForm(request.POST)
            if form.is_valid():
                review = form.save(commit=False)
                review.reviewer = request.user
                review.status = 'DRAFT'
                review.save()
                
                messages.success(request, "Performance review created successfully")
                return redirect('performance_reviews')
            
            return render(request, self.get_template_name(), {
                'form': form,
                'page_title': 'Create Performance Review'
            })
            
        except Exception as e:
            logger.error(f"Error in PerformanceReviewCreateView POST: {str(e)}")
            messages.error(request, "Error creating performance review")
            return redirect('performance_reviews')
