from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views import View
from django.db.models import Count, Q
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from .models import Query, QueryTag, QueryUpdate
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

            # Get available staff members for assignment
            User = get_user_model()
            available_staff = User.objects.filter(
                is_active=True,
                role__in=['ADMIN', 'DOCTOR', 'NURSE', 'STAFF', 'MANAGER']
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

            return render(request, template_path, context)
            
        except Exception as e:
            return HttpResponse(f"An error occurred: {str(e)}", status=500)

class QueryDetailView(LoginRequiredMixin, View):
    def get(self, request, query_id):
        try:
            user_role = request.user.role
            template_path = get_template_path('query_detail.html', user_role)
            
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
        return self.request.user.is_staff
        
    def get(self, request):
        try:
            user_role = request.user.role
            template_path = get_template_path('query_create.html', user_role)
            
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
                form.save_m2m()  # Save many-to-many relationships
                messages.success(request, "Query created successfully")
                return redirect('query_management')
                
            # If form invalid, re-render with errors
            template_path = get_template_path('query_create.html', request.user.role)
            return render(request, template_path, {'form': form})
            
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return HttpResponse(f"An error occurred: {str(e)}", status=500)
        

class QueryUpdateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff
        
    def get(self, request, query_id):
        try:
            user_role = request.user.role
            template_path = get_template_path('query_update.html', user_role)
            
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
                # Check if status changed to resolved
                if query.status == 'RESOLVED' and not query.resolved_at:
                    query.resolved_at = timezone.now()
                query.save()
                form.save_m2m()
                messages.success(request, "Query updated successfully")
                return redirect('query_detail', query_id=query.query_id)
                
            template_path = get_template_path('query_update.html', request.user.role)
            return render(request, template_path, {'form': form, 'query': query})
            
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return HttpResponse(f"An error occurred: {str(e)}", status=500)
        

class QueryDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff

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
        return self.request.user.is_staff

    def post(self, request, query_id):
        try:
            query = get_object_or_404(Query, query_id=query_id)
            staff_id = request.POST.get('assigned_to')
            
            if staff_id:
                User = get_user_model()
                staff = get_object_or_404(User, id=staff_id)
                query.assigned_to = staff
                query.save()
                
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
                QueryUpdate.objects.create(
                    query=query,
                    user=request.user,
                    content=update_content
                )
                
                # Update query status if provided
                if new_status and new_status != query.status:
                    query.status = new_status
                    if new_status == 'RESOLVED':
                        query.resolved_at = timezone.now()
                    query.save()
                
                messages.success(request, f"Update added to Query #{query.query_id}")
            else:
                messages.error(request, "Update content is required")
                
            return redirect('query_management')
            
        except Exception as e:
            messages.error(request, f"Error adding update: {str(e)}")
            return redirect('query_management')

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
                
                messages.success(request, f"Query #{query.query_id} has been marked as resolved")
            else:
                messages.warning(request, "Query is already resolved or closed")
                
            return redirect('query_management')
            
        except Exception as e:
            messages.error(request, f"Error resolving query: {str(e)}")
            return redirect('query_management')