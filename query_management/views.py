from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views import View
from django.db.models import Count, Q
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from .models import Query, QueryTag, QueryUpdate, QueryAttachment
from .forms import QueryCreateForm
from patient_management.models import Patient
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.shortcuts import redirect
from django.http import JsonResponse
from django.views.generic import View
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from .utils import send_query_notification
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, ExtractHour
from django.db.models import Count, Avg, F, ExpressionWrapper, fields
from datetime import timedelta, datetime
import csv
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from access_control.models import Role

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
        return f'dashboard/{role_folder}/{module}/{base_template}'
    return f'dashboard/{role_folder}/{base_template}'

class QueryManagementView(LoginRequiredMixin, View):
    def get_query_trend_data(self, queryset, days=30):
        """Calculate query volume trend data"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        daily_counts = (queryset
            .filter(created_at__gte=start_date)
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('query_id'))
            .order_by('date'))

        dates = []
        counts = []
        
        current = start_date.date()
        while current <= end_date.date():
            dates.append(current.strftime('%Y-%m-%d'))
            count = next((item['count'] for item in daily_counts if item['date'] == current), 0)
            counts.append(count)
            current += timedelta(days=1)

        return {
            'labels': dates,
            'values': counts
        }

    def get_status_distribution(self, queryset):
        """Calculate query status distribution"""
        status_counts = (queryset
            .values('status')
            .annotate(count=Count('query_id'))
            .order_by('status'))

        status_map = dict(Query.STATUS_CHOICES)
        return {
            'labels': [status_map.get(item['status'], item['status']) for item in status_counts],
            'values': [item['count'] for item in status_counts]
        }

    def get_response_time_data(self, queryset, period='day'):
        """Calculate average response times"""
        if period == 'week':
            trunc_fn = TruncWeek
        elif period == 'month':
            trunc_fn = TruncMonth
        else:  # day
            trunc_fn = TruncDate

        data = (queryset
            .annotate(period=trunc_fn('created_at'))
            .values('period')
            .annotate(avg_time=Avg('response_time'))
            .order_by('period'))
        
        return {
            'labels': [item['period'].strftime('%Y-%m-%d') for item in data],
            'values': [float(item['avg_time'].total_seconds()/3600) if item['avg_time'] else 0 for item in data]
        }

    def get_source_distribution(self, queryset):
        """Calculate query source distribution"""
        source_counts = (queryset
            .values('source')
            .annotate(count=Count('query_id'))
            .order_by('-count'))

        source_map = dict(Query.SOURCE_CHOICES)
        return {
            'labels': [source_map.get(item['source'], item['source']) for item in source_counts],
            'values': [item['count'] for item in source_counts]
        }

    def get_staff_performance(self, queryset, days=30):
        """Calculate staff performance metrics"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        data = (queryset
            .filter(created_at__gte=start_date)
            .values('assigned_to__first_name', 'assigned_to__last_name')
            .annotate(
                total_queries=Count('query_id'),
                resolved_queries=Count('query_id', filter=Q(status='RESOLVED')),
                avg_response_time=Avg('response_time')
            )
            .exclude(assigned_to=None)
            .order_by('-total_queries'))

        return {
            'labels': [f"{item['assigned_to__first_name']} {item['assigned_to__last_name']}" for item in data],
            'total_queries': [item['total_queries'] for item in data],
            'resolved_queries': [item['resolved_queries'] for item in data]
        }

    def get_conversion_metrics(self, queryset):
        """Calculate conversion metrics"""
        total = queryset.count()
        converted = queryset.filter(conversion_status=True).count()
        conversion_rate = (converted / total * 100) if total > 0 else 0

        return {
            'total_converted': converted,
            'total_pending': total - converted,
            'conversion_rate': round(conversion_rate, 1)
        }

    def get(self, request):
        try:
            template_path = get_template_path('query_dashboard.html', request.user.role, 'query_management')
            
            if not template_path:
                return HttpResponse("Unauthorized access", status=403)

            # Get base queryset
            queryset = Query.objects.select_related(
                'user', 
                'assigned_to'
            ).prefetch_related(
                'tags',
                'updates',
                'attachments'
            )
            
            # Get filter parameters
            priority = request.GET.get('priority')
            status = request.GET.get('status')
            source = request.GET.get('source')
            search_query = request.GET.get('search')

            # Apply filters
            if priority:
                queryset = queryset.filter(priority=priority)
            if status:
                queryset = queryset.filter(status=status)
            if source:
                queryset = queryset.filter(source=source)
            
            # Apply search
            if search_query:
                queryset = queryset.filter(
                    Q(subject__icontains=search_query) |
                    Q(description__icontains=search_query) |
                    Q(query_id__icontains=search_query) |
                    Q(user__first_name__icontains=search_query) |
                    Q(user__last_name__icontains=search_query) |
                    Q(contact_email__icontains=search_query) |
                    Q(contact_phone__icontains=search_query)
                )

            # Pagination
            paginator = Paginator(queryset, 10)
            page = request.GET.get('page', 1)
            try:
                queries = paginator.page(page)
            except PageNotAnInteger:
                queries = paginator.page(1)
            except EmptyPage:
                queries = paginator.page(paginator.num_pages)

            # Get choices for dropdowns
            status_choices = Query.STATUS_CHOICES
            source_choices = Query.SOURCE_CHOICES

            # Get available staff members for assignment - Updated to use Role model correctly
            User = get_user_model()
            staff_roles = Role.objects.filter(name__in=['ADMIN', 'DOCTOR', 'NURSE', 'STAFF', 'MANAGER'])
            available_staff = User.objects.filter(
                is_active=True,
                role__in=staff_roles
            ).order_by('first_name')

            # Calculate statistics
            current_date = timezone.now()
            start_of_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            resolved_this_month = Query.objects.filter(resolved_at__gte=start_of_month).count()
            total_queries = Query.objects.count()

            context = {
                'queries': queries,
                'total_queries': total_queries,
                'open_queries': Query.objects.filter(
                    status__in=['NEW', 'IN_PROGRESS', 'WAITING']
                ).count(),
                'resolved_this_month': resolved_this_month,
                'resolution_rate': round((resolved_this_month / total_queries * 100) if total_queries > 0 else 0, 1),
                'status_choices': status_choices,
                'source_choices': source_choices,
                'current_filters': {
                    'priority': priority or '',
                    'status': status or '',
                    'source': source or '',
                    'search': search_query or '',
                },
                'paginator': paginator,
                'page_obj': queries,
                'available_staff': available_staff,
            }

            # Prepare graph data
            context.update({
                'query_trend_data': self.get_query_trend_data(queryset),
                'status_distribution': self.get_status_distribution(queryset),
                'response_time_data': self.get_response_time_data(
                    queryset, 
                    request.GET.get('response_time_period', 'day')
                ),
                'source_distribution': self.get_source_distribution(queryset),
                'staff_performance': self.get_staff_performance(queryset),
                'conversion_metrics': self.get_conversion_metrics(queryset),
                'periods': [
                    ('7', 'Last 7 Days'),
                    ('30', 'Last 30 Days'),
                    ('90', 'Last 90 Days'),
                    ('custom', 'Custom Range'),
                ],
            })

            # Error handling for graph data
            if not any([
                context['query_trend_data']['values'],
                context['status_distribution']['values'],
                context['source_distribution']['values']
            ]):
                messages.info(request, "Not enough data available for some visualizations")

            return render(request, template_path, context)
            
        except Exception as e:
            messages.error(request, f"An error occurred while preparing dashboard data: {str(e)}")
            return render(request, template_path, {
                'error': True,
                'error_message': "Unable to load dashboard data. Please try again later."
            })

class QueryDetailView(LoginRequiredMixin, View):
    def get(self, request, query_id):
        try:
            template_path = get_template_path('query_detail.html', request.user.role, 'query_management')
            
            if not template_path:
                return HttpResponse("Unauthorized access", status=403)

            # Get query with all essential relationships
            query = get_object_or_404(
                Query.objects.select_related(
                    'user',
                    'assigned_to'
                ).prefetch_related(
                    'updates',
                    'attachments',
                    'tags'
                ),
                query_id=query_id
            )

            # Get patient profile if it exists
            patient_profile = None
            if query.user:
                try:
                    patient_profile = Patient.objects.get(user=query.user)
                except Patient.DoesNotExist:
                    pass

            context = {
                'query': query,
                'user_details': {
                    'name': query.user.get_full_name() if query.user else 'Anonymous',
                    'email': query.user.email if query.user else query.contact_email,
                    'role': query.user.role if query.user else None,
                },
                'patient_profile': patient_profile,
                'assigned_to_details': {
                    'name': query.assigned_to.get_full_name() if query.assigned_to else 'Unassigned',
                    'email': query.assigned_to.email if query.assigned_to else None,
                    'role': query.assigned_to.role if query.assigned_to else None,
                },
                'updates': query.updates.all().order_by('-created_at'),
                'attachments': query.attachments.all(),
                'tags': query.tags.all(),
            }

            return render(request, template_path, context)

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return HttpResponse(f"An error occurred: {str(e)}", status=500)


class QueryCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return hasattr(self.request.user, 'role') and self.request.user.role.name in ['ADMIN', 'DOCTOR', 'NURSE', 'STAFF', 'MANAGER']
        
    def get(self, request):
        try:
            template_path = get_template_path('query_create.html', request.user.role, 'query_management')
            
            if not template_path:
                return HttpResponse("Unauthorized access", status=403)
                
            form = QueryCreateForm()
            context = {
                'form': form
            }
            return render(request, template_path, context)
            
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return HttpResponse(f"An error occurred: {str(e)}", status=500)
            
    def post(self, request):
        try:
            form = QueryCreateForm(request.POST)
            if form.is_valid():
                query = form.save(commit=False)
                if not form.cleaned_data.get('user'):
                    query.user = request.user
                query.save()
                form.save_m2m()
                
                # Send notification for new query
                send_query_notification(query, 'created')
                
                messages.success(request, "Query created successfully")
                return redirect('query_management')
                
            # If form invalid, re-render with errors
            template_path = get_template_path('query_create.html', request.user.role, 'query_management')
            return render(request, template_path, {'form': form})
            
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return HttpResponse(f"An error occurred: {str(e)}", status=500)
        

class QueryUpdateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return hasattr(self.request.user, 'role') and self.request.user.role.name in ['ADMIN', 'DOCTOR', 'NURSE', 'STAFF', 'MANAGER']
        
    def get(self, request, query_id):
        try:
            template_path = get_template_path('query_update.html', request.user.role, 'query_management')
            
            if not template_path:
                return HttpResponse("Unauthorized access", status=403)
            
            query = get_object_or_404(Query, query_id=query_id)
            form = QueryCreateForm(instance=query)  # Reuse create form
            
            context = {
                'form': form,
                'query': query
            }
            return render(request, template_path, context)
            
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return HttpResponse(f"An error occurred: {str(e)}", status=500)
            
    def post(self, request, query_id):
        try:
            query = get_object_or_404(Query, query_id=query_id)
            form = QueryCreateForm(request.POST, instance=query)
            
            if form.is_valid():
                query = form.save(commit=False)
                old_status = query.status
                
                # Check if status changed to resolved
                if query.status == 'RESOLVED' and not query.resolved_at:
                    query.resolved_at = timezone.now()
                
                query.save()
                form.save_m2m()
                
                # Notify if status changed
                if old_status != query.status:
                    send_query_notification(
                        query, 
                        'status_updated',
                        old_status=old_status,
                        new_status=query.status
                    )
                
                messages.success(request, "Query updated successfully")
                return redirect('query_detail', query_id=query.query_id)
            
            template_path = get_template_path('query_update.html', request.user.role, 'query_management')
            return render(request, template_path, {'form': form, 'query': query})
            
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return HttpResponse(f"An error occurred: {str(e)}", status=500)
        

class QueryDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return hasattr(self.request.user, 'role') and self.request.user.role.name in ['ADMIN', 'MANAGER']

    def post(self, request, query_id):
        try:
            query = get_object_or_404(Query, query_id=query_id)
            query_number = query.query_id  # Store for message
            query.delete()
            
            messages.success(request, f"Query #{query_number} deleted successfully")
            return redirect('query_management')
            
        except Exception as e:
            messages.error(request, f"Error deleting query: {str(e)}")
            return HttpResponse(f"Error deleting query: {str(e)}", status=500)

class QueryAssignView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return hasattr(self.request.user, 'role') and self.request.user.role.name in ['ADMIN', 'MANAGER']

    def post(self, request, query_id):
        try:
            query = get_object_or_404(Query, query_id=query_id)
            staff_id = request.POST.get('assigned_to')
            
            if staff_id:
                User = get_user_model()
                staff = get_object_or_404(User, id=staff_id)
                previous_assignee = query.assigned_to
                query.assigned_to = staff
                query.save()
                
                # Send notification to newly assigned staff
                send_query_notification(
                    query, 
                    'assigned', 
                    recipient=staff,
                    assigned_by=request.user
                )
                
                # Notify query creator if they exist and are different from the assignee
                if query.user and query.user != staff:
                    send_query_notification(
                        query,
                        'status_updated',
                        recipient=query.user,
                        update_content=f"Query assigned to {staff.get_full_name()}"
                    )
                
                # Notify previous assignee if exists and different from new assignee
                if previous_assignee and previous_assignee != staff:
                    send_query_notification(
                        query,
                        'status_updated',
                        recipient=previous_assignee,
                        update_content=f"Query reassigned to {staff.get_full_name()}"
                    )
                
                # Create a query update to log the assignment
                QueryUpdate.objects.create(
                    query=query,
                    user=request.user,
                    content=f"Query assigned to {staff.get_full_name()}"
                )
                
                messages.success(request, f"Query #{query.query_id} assigned to {staff.get_full_name()}")
            else:
                messages.error(request, "No staff member selected")
                
            return redirect('query_management')
            
        except Exception as e:
            messages.error(request, f"Error assigning query: {str(e)}")
            return redirect('query_management')

class QueryUpdateStatusView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff

    def post(self, request, query_id):
        try:
            query = get_object_or_404(Query, query_id=query_id)
            update_content = request.POST.get('update_content')
            new_status = request.POST.get('new_status')
            
            if update_content:
                # Create query update
                update = QueryUpdate.objects.create(
                    query=query,
                    user=request.user,
                    content=update_content
                )
                
                # Handle file attachments
                files = request.FILES.getlist('attachments')
                for file in files:
                    QueryAttachment.objects.create(
                        query=query,
                        file=file
                    )
                
                # Update query status if provided
                if new_status and new_status != query.status:
                    old_status = query.status
                    query.status = new_status
                    if new_status == 'RESOLVED':
                        query.resolved_at = timezone.now()
                        # Send resolution notification
                        send_query_notification(query, 'resolved')
                    else:
                        # Send status update notification
                        send_query_notification(
                            query, 
                            'status_updated',
                            old_status=old_status,
                            new_status=new_status
                        )
                    query.save()
                
                # Notify query owner about the update
                if query.user and query.user != request.user:
                    send_query_notification(
                        query,
                        'status_updated',
                        recipient=query.user,
                        update_content=update_content
                    )
                
                messages.success(request, f"Update added to Query #{query.query_id}")
                if files:
                    messages.info(request, f"{len(files)} file(s) attached successfully")
            else:
                messages.error(request, "Update content is required")
                
            return redirect('query_detail', query_id=query.query_id)
            
        except Exception as e:
            messages.error(request, f"Error adding update: {str(e)}")
            return redirect('query_detail', query_id=query_id)

class QueryResolveView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff

    def post(self, request, query_id):
        try:
            query = get_object_or_404(Query, query_id=query_id)
            
            # Only allow resolving if query isn't already resolved/closed
            if query.status not in ['RESOLVED', 'CLOSED']:
                query.status = 'RESOLVED'
                query.resolved_at = timezone.now()
                query.save()
                
                # Create a query update to log the resolution
                QueryUpdate.objects.create(
                    query=query,
                    user=request.user,
                    content=f"Query marked as resolved by {request.user.get_full_name()}"
                )
                
                # Send resolution notification
                send_query_notification(
                    query, 
                    'resolved',
                    resolver=request.user.get_full_name()
                )
                
                messages.success(request, f"Query #{query.query_id} has been marked as resolved")
            else:
                messages.warning(request, "Query is already resolved or closed")
                
            return redirect('query_management')
            
        except Exception as e:
            messages.error(request, f"Error resolving query: {str(e)}")
            return redirect('query_management')

class QueryTrendDataView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            days = int(request.GET.get('days', 30))
            queryset = Query.objects.all()
            data = QueryManagementView().get_query_trend_data(queryset, days)
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

class QueryResponseTimeDataView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            period = request.GET.get('period', 'day')
            queryset = Query.objects.all()
            data = QueryManagementView().get_response_time_data(queryset, period)
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

class QueryStaffPerformanceDataView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            days = int(request.GET.get('days', 30))
            queryset = Query.objects.all()
            data = QueryManagementView().get_staff_performance(queryset, days)
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

class QueryExportView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff

    def get(self, request):
        try:
            export_format = request.GET.get('format', 'csv')
            date_range = request.GET.get('date_range')
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')

            # Get queryset based on date range
            try:
                queryset = self.get_filtered_queryset(date_range, start_date, end_date)
            except ValueError as e:
                messages.error(request, str(e))
                return redirect('query_management')

            if export_format == 'csv':
                return self.export_csv(queryset)
            elif export_format == 'pdf':
                return self.export_pdf(queryset)
            else:
                messages.error(request, "Invalid export format")
                return redirect('query_management')
        except Exception as e:
            messages.error(request, f"Export failed: {str(e)}")
            return redirect('query_management')

    def get_filtered_queryset(self, date_range, start_date=None, end_date=None):
        """
        Filter queryset based on date range or custom dates
        """
        queryset = Query.objects.all()

        if date_range == 'custom':
            if not start_date or not end_date:
                raise ValueError("Both start date and end date are required for custom range")
            try:
                # Convert date strings from datepicker format (MM/DD/YYYY) to datetime
                start_datetime = datetime.strptime(start_date, '%m/%d/%Y')
                end_datetime = datetime.strptime(end_date, '%m/%d/%Y')
                
                # Add time to make end_date inclusive
                end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
                
                # Convert to timezone-aware datetime
                start_datetime = timezone.make_aware(start_datetime)
                end_datetime = timezone.make_aware(end_datetime)
                
                if start_datetime > end_datetime:
                    raise ValueError("Start date must be before end date")
                
                queryset = queryset.filter(created_at__range=[start_datetime, end_datetime])
            except ValueError as e:
                raise ValueError(f"Invalid date format: {str(e)}")
        else:
            try:
                days = int(date_range or '30')  # Default to 30 days if not specified
                if days <= 0:
                    raise ValueError("Days must be a positive number")
                    
                end_date = timezone.now()
                start_date = end_date - timedelta(days=days)
                queryset = queryset.filter(created_at__range=[start_date, end_date])
            except ValueError:
                raise ValueError("Invalid date range value")

        return queryset.select_related('user', 'assigned_to')

    def get_user_details(self, user):
        """Helper method to get formatted user details"""
        if not user:
            return "N/A"
        return f"{user.get_full_name()} ({user.email})"

    def format_duration(self, duration):
        """Helper method to format duration"""
        if not duration:
            return "N/A"
        total_seconds = duration.total_seconds()
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        
        parts = []
        if days:
            parts.append(f"{int(days)}d")
        if hours:
            parts.append(f"{int(hours)}h")
        if minutes:
            parts.append(f"{int(minutes)}m")
            
        return " ".join(parts) if parts else "0m"

    def get_duration_in_hours(self, duration):
        """Helper method to get duration in hours for statistics"""
        if not duration:
            return 0
        return duration.total_seconds() / 3600

    def export_csv(self, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="detailed_query_report.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Query ID',
            'Subject',
            'Description',
            'Status',
            'Priority',
            'Source',
            'Query Type',
            'Created At',
            'Updated At',
            'Resolved At',
            'Response Time',
            'Assigned To',
            'User/Contact',
            'Contact Email',
            'Contact Phone',
            'Is Anonymous',
            'Is Patient',
            'Expected Response Date',
            'Follow Up Date',
            'Resolution Summary',
            'Satisfaction Rating',
            'Conversion Status',
            'Tags',
            'Total Updates',
            'Total Attachments'
        ])

        for query in queryset:
            writer.writerow([
                query.query_id,
                query.subject,
                query.description[:100] + '...' if len(query.description) > 100 else query.description,
                query.get_status_display(),
                query.get_priority_display(),
                query.get_source_display(),
                query.get_query_type_display() if query.query_type else 'N/A',
                query.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                query.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                query.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if query.resolved_at else 'N/A',
                self.format_duration(query.response_time),
                self.get_user_details(query.assigned_to),
                self.get_user_details(query.user) if not query.is_anonymous else 'Anonymous',
                query.contact_email or 'N/A',
                query.contact_phone or 'N/A',
                'Yes' if query.is_anonymous else 'No',
                'Yes' if query.is_patient else 'No',
                query.expected_response_date.strftime('%Y-%m-%d %H:%M:%S') if query.expected_response_date else 'N/A',
                query.follow_up_date.strftime('%Y-%m-%d %H:%M:%S') if query.follow_up_date else 'N/A',
                query.resolution_summary or 'N/A',
                f"{query.satisfaction_rating}/5" if query.satisfaction_rating else 'N/A',
                'Converted' if query.conversion_status else 'Not Converted',
                ', '.join(tag.name for tag in query.tags.all()) or 'No Tags',
                query.updates.count(),
                query.attachments.count()
            ])

        return response

    def export_pdf(self, queryset):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="detailed_query_report.pdf"'

        doc = SimpleDocTemplate(response, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        heading_style = styles['Heading2']
        normal_style = styles['Normal']

        # Title
        elements.append(Paragraph('Detailed Query Management Report', title_style))
        elements.append(Spacer(1, 20))

        # Export timestamp
        elements.append(Paragraph(f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
        elements.append(Spacer(1, 20))

        # Statistics summary
        avg_response_time = queryset.filter(response_time__isnull=False).aggregate(Avg('response_time'))['response_time__avg']
        avg_response_hours = self.get_duration_in_hours(avg_response_time) if avg_response_time else 0

        stats = [
            ['Total Queries:', str(queryset.count())],
            ['Open Queries:', str(queryset.filter(status__in=['NEW', 'IN_PROGRESS', 'WAITING']).count())],
            ['Resolved Queries:', str(queryset.filter(status='RESOLVED').count())],
            ['Average Response Time:', f"{avg_response_hours:.1f} hours"]
        ]
        
        stats_table = Table(stats, colWidths=[150, 200])
        stats_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(stats_table)
        elements.append(Spacer(1, 20))

        # Detailed Query List
        elements.append(Paragraph('Detailed Query List', heading_style))
        elements.append(Spacer(1, 10))

        for query in queryset:
            # Query header
            elements.append(Paragraph(f"Query #{query.query_id}: {query.subject}", styles['Heading3']))
            
            # Query details
            details = [
                ['Status:', query.get_status_display(), 'Priority:', query.get_priority_display()],
                ['Created:', query.created_at.strftime('%Y-%m-%d %H:%M:%S'), 'Source:', query.get_source_display()],
                ['Assigned To:', self.get_user_details(query.assigned_to), 'Response Time:', self.format_duration(query.response_time)],
                ['User/Contact:', self.get_user_details(query.user) if not query.is_anonymous else 'Anonymous', 'Type:', query.get_query_type_display() or 'N/A']
            ]
            
            detail_table = Table(details, colWidths=[80, 150, 80, 150])
            detail_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
                ('TEXTCOLOR', (2, 0), (2, -1), colors.grey),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(detail_table)
            elements.append(Spacer(1, 10))

            # Description
            elements.append(Paragraph('Description:', styles['Heading4']))
            elements.append(Paragraph(query.description, normal_style))
            elements.append(Spacer(1, 10))

            # Additional details in a smaller table
            if query.resolution_summary or query.satisfaction_rating or query.tags.exists():
                additional_info = []
                if query.resolution_summary:
                    additional_info.append(['Resolution:', query.resolution_summary])
                if query.satisfaction_rating:
                    additional_info.append(['Satisfaction:', f"{query.satisfaction_rating}/5"])
                if query.tags.exists():
                    additional_info.append(['Tags:', ', '.join(tag.name for tag in query.tags.all())])
                
                add_table = Table(additional_info, colWidths=[80, 380])
                add_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ]))
                elements.append(add_table)

            elements.append(Spacer(1, 20))

        doc.build(elements)
        return response