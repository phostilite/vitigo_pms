# Django imports 
import logging
from datetime import datetime
from django.utils import timezone  

# Standard library imports
from django.views.generic import ListView, View, DetailView, CreateView, UpdateView
from django.db.models import Count, Avg, Q, FloatField
from django.db.models.functions import Cast
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from datetime import timedelta
from django.db import transaction
from django.urls import reverse_lazy
from django.http import Http404
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.http import HttpResponse
from django.contrib.auth.mixins import UserPassesTestMixin
import csv
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

# Local application imports
from .models import (
    Consultation, DoctorPrivateNotes, ConsultationType,
    ConsultationPriority, PaymentStatus, Prescription, PrescriptionTemplate, ConsultationFeedback, StaffInstruction, TemplateItem, PrescriptionItem
)
from .forms import ConsultationForm
from access_control.models import Role
from access_control.permissions import PermissionManager
from stock_management.models import StockItem
from pharmacy_management.models import Medication
from error_handling.views import handler403, handler404, handler500


logger = logging.getLogger(__name__)
User = get_user_model()

def get_template_path(base_template, role, module='consultation_management'):
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
        return f'{role_folder}/{module}/{base_template}'
    return f'{role_folder}/{base_template}'

class ConsultationDashboardView(LoginRequiredMixin, ListView):
    model = Consultation
    context_object_name = 'consultations'
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        if not PermissionManager.check_module_access(request.user, 'consultation_management'):
            messages.error(request, "You don't have permission to access Consultations")
            return handler403(request, exception="Access Denied")
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        return [get_template_path('consultation_dashboard.html', self.request.user.role, 'consultation_management')]

    def get_queryset(self):
        queryset = Consultation.objects.select_related('patient', 'doctor').all()
        
        # Get filter parameters
        consultation_type = self.request.GET.get('consultation_type')
        status = self.request.GET.get('status')
        date_range = self.request.GET.get('date_range')
        search = self.request.GET.get('search')
        doctor = self.request.GET.get('doctor')

        # Apply consultation type filter
        if consultation_type:
            queryset = queryset.filter(consultation_type=consultation_type)

        # Apply status filter
        if status:
            queryset = queryset.filter(status=status)

        # Apply date range filter
        if date_range:
            today = timezone.now()
            if date_range == '7':
                date_threshold = today - timedelta(days=7)
            elif date_range == '30':
                date_threshold = today - timedelta(days=30)
            elif date_range == '90':
                date_threshold = today - timedelta(days=90)
            queryset = queryset.filter(scheduled_datetime__gte=date_threshold)

        # Apply doctor filter
        if doctor:
            queryset = queryset.filter(doctor_id=doctor)

        # Apply search filter
        if search:
            queryset = queryset.filter(
                Q(patient__first_name__icontains=search) |
                Q(patient__last_name__icontains=search) |
                Q(doctor__first_name__icontains=search) |
                Q(doctor__last_name__icontains=search) |
                Q(diagnosis__icontains=search) |
                Q(chief_complaint__icontains=search)
            )

        return queryset.order_by('-scheduled_datetime')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter choices to context
        context.update({
            'consultation_types': ConsultationType.choices,
            'status_choices': [
                ('SCHEDULED', 'Scheduled'),
                ('IN_PROGRESS', 'In Progress'),
                ('COMPLETED', 'Completed'),
                ('CANCELLED', 'Cancelled'),
                ('NO_SHOW', 'No Show')
            ],
            'doctors': User.objects.filter(role__name='DOCTOR'),
            'current_filters': {
                'consultation_type': self.request.GET.get('consultation_type', ''),
                'status': self.request.GET.get('status', ''),
                'date_range': self.request.GET.get('date_range', ''),
                'doctor': self.request.GET.get('doctor', ''),
                'search': self.request.GET.get('search', ''),
            }
        })
        
        today = timezone.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Calculate total consultations this month
        context['total_consultations'] = Consultation.objects.filter(
            scheduled_datetime__gte=start_of_month,
            scheduled_datetime__lte=today
        ).count()

        # Calculate upcoming follow-ups (next 7 days)
        next_week = today + timedelta(days=7)
        context['upcoming_followups'] = Consultation.objects.filter(
            follow_up_date__gte=today,
            follow_up_date__lte=next_week
        ).count()

        # Calculate average consultation duration (last 30 days)
        last_month = today - timedelta(days=30)
        completed_consultations = Consultation.objects.filter(
            status='COMPLETED',
            actual_end_time__gte=last_month
        ).exclude(actual_start_time=None)
        
        total_duration = timedelta()
        consultation_count = 0
        
        for consultation in completed_consultations:
            if consultation.actual_end_time and consultation.actual_start_time:
                duration = consultation.actual_end_time - consultation.actual_start_time
                total_duration += duration
                consultation_count += 1
        
        if consultation_count > 0:
            avg_minutes = total_duration.total_seconds() / (consultation_count * 60)
            context['avg_duration'] = round(avg_minutes)
        else:
            context['avg_duration'] = 0

        # Calculate patient satisfaction metrics from feedback
        last_month = today - timedelta(days=30)
        feedback_metrics = ConsultationFeedback.objects.filter(
            created_at__gte=last_month,
            consultation__status='COMPLETED'
        ).aggregate(
            avg_rating=Avg('rating'),
            avg_service=Avg('service_quality'),
            avg_communication=Avg('doctor_communication'),
            total_feedbacks=Count('id'),
            recommendation_rate=Avg(Cast('would_recommend', FloatField())) * 100
        )
        
        context.update({
            'patient_satisfaction': round(feedback_metrics['avg_rating'] or 0, 1),
            'total_ratings': feedback_metrics['total_feedbacks'],
            'satisfaction_metrics': {
                'service': round(feedback_metrics['avg_service'] or 0, 1),
                'communication': round(feedback_metrics['avg_communication'] or 0, 1),
                'recommendation_rate': round(feedback_metrics['recommendation_rate'] or 0)
            }
        })

        # Calculate month-over-month growth
        previous_month = start_of_month - timedelta(days=1)
        previous_month_start = previous_month.replace(day=1)
        
        current_month_count = context['total_consultations']
        previous_month_count = Consultation.objects.filter(
            scheduled_datetime__gte=previous_month_start,
            scheduled_datetime__lte=previous_month
        ).count()
        
        if previous_month_count > 0:
            context['consultation_growth'] = round(
                ((current_month_count - previous_month_count) / previous_month_count) * 100
            )
        else:
            context['consultation_growth'] = 0
            
        return context
    

class ConsultationCreateView(LoginRequiredMixin, CreateView):
    model = Consultation
    form_class = ConsultationForm
    success_url = reverse_lazy('consultation_dashboard')
    
    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_modify(request.user, 'consultation_management'):
                logger.warning(
                    f"Access denied to consultation creation for user {request.user.id}"
                )
                messages.error(request, "You don't have permission to access Consultations")
                return handler403(request, exception="Access Denied")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in consultation dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing the page")
            return redirect('dashboard')

    def get_template_names(self):
        try:
            return [get_template_path(
                'consultation_create.html',
                self.request.user.role,
                'consultation_management'
            )]
        except Exception as e:
            logger.error(f"Error getting template: {str(e)}")
            return ['consultation_management/default_consultation_create.html']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        try:
            kwargs['user'] = self.request.user
        except Exception as e:
            logger.error(f"Error setting form kwargs: {str(e)}")
        return kwargs

    def form_valid(self, form):
        try:
            # Set defaults for required fields
            consultation = form.save(commit=False)
            
            # Set the doctor if not already set
            if not consultation.doctor:
                consultation.doctor = self.request.user
            
            # Updated datetime validation
            if consultation.scheduled_datetime <= timezone.now():
                form.add_error('scheduled_datetime', 'Consultation must be scheduled for a future time')
                return self.form_invalid(form)
            
            # Save the consultation
            consultation.save()
            
            # Create private notes
            try:
                DoctorPrivateNotes.objects.create(consultation=consultation)
            except Exception as e:
                logger.warning(f"Error creating private notes: {str(e)}")
                # Continue execution as this is not critical
            
            messages.success(self.request, "Consultation created successfully")
            logger.info(f"Consultation {consultation.id} created by user {self.request.user.id}")
            
            return super().form_valid(form)
            
        except ValidationError as e:
            logger.error(f"Validation error in consultation creation: {str(e)}")
            messages.error(self.request, str(e))
            return self.form_invalid(form)
        except Exception as e:
            logger.error(f"Error creating consultation: {str(e)}")
            messages.error(self.request, "An error occurred while creating the consultation")
            return self.form_invalid(form)

    def form_invalid(self, form):
        try:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(self.request, f"{field}: {error}")
            logger.warning(
                f"Invalid consultation form submission by user {self.request.user.id}: {form.errors}"
            )
            return super().form_invalid(form)
        except Exception as e:
            logger.error(f"Error handling invalid form: {str(e)}")
            messages.error(self.request, "An error occurred while processing your request")
            return redirect('consultation_dashboard')

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            context.update({
                'consultation_types': ConsultationType.choices,
                'priority_levels': ConsultationPriority.choices,
                'payment_statuses': PaymentStatus.choices,
                'page_title': 'Create New Consultation',
                'submit_text': 'Schedule Consultation'
            })
            return context
        except Exception as e:
            logger.error(f"Error getting context data: {str(e)}")
            return {'error': 'Error loading page data'}
        

class ConsultationDetailView(LoginRequiredMixin, DetailView):
    model = Consultation
    context_object_name = 'consultation'
    
    def dispatch(self, request, *args, **kwargs):
        try:
            if not PermissionManager.check_module_access(request.user, 'consultation_management'):
                logger.warning(f"Access denied to consultation details for user {request.user.id}")
                messages.error(request, "You don't have permission to view consultation details")
                return handler403(request, exception="Access Denied")
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in consultation detail dispatch: {str(e)}")
            messages.error(request, "An error occurred while accessing the consultation details")
            return redirect('dashboard')

    def get_template_names(self):
        try:
            return [get_template_path(
                'consultation_detail.html',
                self.request.user.role,
                'consultation_management'
            )]
        except Exception as e:
            logger.error(f"Error getting template: {str(e)}")
            return ['consultation_management/default_consultation_detail.html']

    def get_object(self, queryset=None):
        try:
            return Consultation.objects.select_related(
                'patient',
                'doctor',
                'private_notes',
                'treatment_plan',
                'staff_instructions'
            ).prefetch_related(
                'prescriptions__items__medication',
                'phototherapy_sessions',
                'attachments'
            ).get(pk=self.kwargs['pk'])
        except Consultation.DoesNotExist:
            logger.warning(f"Consultation {self.kwargs['pk']} not found")
            raise Http404("Consultation not found")
        except Exception as e:
            logger.error(f"Error retrieving consultation: {str(e)}")
            raise

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            consultation = self.object
            
            # Base consultation information
            context['page_title'] = f'Consultation Details - {consultation.patient.get_full_name()}'
            
            # Get previous consultations
            try:
                context['previous_consultations'] = Consultation.objects.filter(
                    patient=consultation.patient,
                    scheduled_datetime__lt=consultation.scheduled_datetime
                ).order_by('-scheduled_datetime')[:5]
            except Exception as e:
                logger.warning(f"Error fetching previous consultations: {str(e)}")
                context['previous_consultations'] = []
            
            # Get prescriptions with stock information
            try:
                prescriptions = consultation.prescriptions.prefetch_related(
                    'items__medication',
                    'items__stock_item'
                ).all()
                context['prescriptions'] = prescriptions
                
                # Get previous consultations' prescriptions for templates
                previous_prescriptions = Prescription.objects.filter(
                    consultation__patient=consultation.patient,
                    consultation__scheduled_datetime__lt=consultation.scheduled_datetime
                ).prefetch_related('items__medication')[:5]
                context['previous_prescriptions'] = previous_prescriptions
                
                # Get prescription templates
                context['prescription_templates'] = PrescriptionTemplate.objects.filter(
                    Q(doctor=consultation.doctor) | Q(is_global=True)
                )
            except Exception as e:
                logger.warning(f"Error fetching prescriptions data: {str(e)}")
                context['prescriptions'] = None
                context['prescription_error'] = "Unable to load prescriptions"
            
            # Get treatment plan details with costing
            try:
                if hasattr(consultation, 'treatment_plan'):
                    context['treatment_plan_items'] = consultation.treatment_plan.items.all()
                    context['treatment_plan_cost'] = consultation.treatment_plan.total_cost
                    context['payment_status'] = consultation.treatment_plan.get_payment_status_display()
            except Exception as e:
                logger.warning(f"Error fetching treatment plan: {str(e)}")
                context['treatment_plan_items'] = None
                context['treatment_plan_error'] = "Unable to load treatment plan"
            
            # Get phototherapy sessions
            try:
                context['phototherapy_sessions'] = consultation.phototherapy_sessions.select_related(
                    'phototherapy_session'
                ).all()
            except Exception as e:
                logger.warning(f"Error fetching phototherapy sessions: {str(e)}")
                context['phototherapy_sessions'] = None
                context['phototherapy_error'] = "Unable to load phototherapy sessions"
            
            # Get consultation history timeline
            try:
                context['consultation_history'] = self._get_consultation_history(consultation)
            except Exception as e:
                logger.warning(f"Error generating consultation history: {str(e)}")
                context['consultation_history'] = None
            
            # Add permissions context
            context['can_edit'] = PermissionManager.check_module_modify(
                self.request.user, 
                'consultation_management'
            )
            context['can_delete'] = PermissionManager.check_module_delete(
                self.request.user, 
                'consultation_management'
            )
            context['is_doctor'] = self.request.user.role.name == 'DOCTOR'
            
            # Add consultation priority choices for staff instructions form
            context['consultation_priority_choices'] = ConsultationPriority.choices

            # Add all active medications for prescription creation
            context['medications'] = Medication.objects.filter(is_active=True).order_by('name')
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting consultation detail context: {str(e)}")
            messages.error(self.request, "Error loading consultation details")
            return {'error': 'Error loading consultation data'}

    def _get_consultation_history(self, consultation):
        """Generate a timeline of consultation events"""
        try:
            history = []
            
            # Add creation event
            history.append({
                'timestamp': consultation.created_at,
                'description': f'Consultation scheduled by {consultation.created_by.get_full_name() if consultation.created_by else "System"}'
            })
            
            # Add status changes
            if consultation.actual_start_time:
                history.append({
                    'timestamp': consultation.actual_start_time,
                    'description': 'Consultation started'
                })
            
            if consultation.actual_end_time:
                history.append({
                    'timestamp': consultation.actual_end_time,
                    'description': 'Consultation completed'
                })
            
            # Add prescription events
            for prescription in consultation.prescriptions.all():
                history.append({
                    'timestamp': prescription.created_at,
                    'description': 'Prescription added'
                })
            
            # Add treatment plan events
            if hasattr(consultation, 'treatment_plan'):
                history.append({
                    'timestamp': consultation.treatment_plan.created_at,
                    'description': 'Treatment plan created'
                })
            
            # Sort by timestamp
            history.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return history
        except Exception as e:
            logger.error(f"Error generating consultation history: {str(e)}")
            return []
        

class ConsultationDeleteView(LoginRequiredMixin, View):
    def post(self, request, consultation_id):  # Changed from pk to consultation_id
        if not PermissionManager.check_module_delete(request.user, 'consultation_management'):
            messages.error(request, "You don't have permission to delete consultations")
            return handler403(request, exception="Access Denied")

        try:
            consultation = get_object_or_404(Consultation, id=consultation_id)
            
            # Check if consultation is in the past
            if consultation.scheduled_datetime <= timezone.now():
                messages.error(request, "Cannot delete past consultations")
                return redirect('consultation_dashboard')
                
            consultation.delete()
            messages.success(request, "Consultation deleted successfully")
            return redirect('consultation_dashboard')
        except Exception as e:
            logger.error(f"Error deleting consultation {consultation_id}: {str(e)}")
            messages.error(request, "Error deleting consultation")
            return redirect('consultation_dashboard')

class ConsultationStatusUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        try:
            consultation = get_object_or_404(Consultation, pk=pk)
            new_status = request.POST.get('status')
            
            # Get choices from model directly
            valid_statuses = [status[0] for status in Consultation.STATUS_CHOICES]
            
            if not new_status or new_status not in valid_statuses:
                messages.error(request, "Invalid status provided")
                return redirect('consultation_detail', pk=pk)

            # Additional validation for status transitions
            current_status = consultation.status
            valid_transition = True
            
            if new_status == 'IN_PROGRESS' and current_status != 'SCHEDULED':
                valid_transition = False
            elif new_status == 'COMPLETED' and current_status != 'IN_PROGRESS':
                valid_transition = False
            elif new_status == 'CANCELLED' and current_status in ['COMPLETED', 'CANCELLED']:
                valid_transition = False

            if not valid_transition:
                messages.error(request, f"Cannot change status from {current_status} to {new_status}")
                return redirect('consultation_detail', pk=pk)

            # Update status and timestamps
            consultation.status = new_status
            if new_status == 'IN_PROGRESS':
                consultation.actual_start_time = timezone.now()
            elif new_status == 'COMPLETED':
                consultation.actual_end_time = timezone.now()

            consultation.save()
            messages.success(request, f"Consultation status updated to {consultation.get_status_display()}")
            
            return redirect('consultation_detail', pk=pk)

        except Exception as e:

            logger.error(f"Error updating consultation status: {str(e)}")
            messages.error(request, "An error occurred while updating the consultation status")
            return redirect('consultation_detail', pk=pk)
        

class StaffInstructionsUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        try:
            consultation = get_object_or_404(Consultation, pk=pk)
            
            if not PermissionManager.check_module_modify(request.user, 'consultation_management'):
                messages.error(request, "You don't have permission to modify staff instructions")
                return redirect('consultation_detail', pk=pk)
            
            # Validate priority
            priority = request.POST.get('priority')
            if priority not in dict(ConsultationPriority.choices):
                messages.error(request, "Invalid priority level")
                return redirect('consultation_detail', pk=pk)
            
            # Get or create staff instructions
            staff_instructions, created = StaffInstruction.objects.get_or_create(
                consultation=consultation
            )
            
            # Update all fields
            staff_instructions.pre_consultation = request.POST.get('pre_consultation', '')
            staff_instructions.during_consultation = request.POST.get('during_consultation', '')
            staff_instructions.post_consultation = request.POST.get('post_consultation', '')
            staff_instructions.priority = priority
            
            # Save changes
            staff_instructions.save()
            
            messages.success(request, "Staff instructions updated successfully")
            logger.info(f"Staff instructions updated for consultation {pk} by user {request.user.id}")
            
        except Exception as e:
            logger.error(f"Error updating staff instructions: {str(e)}")
            messages.error(request, "An error occurred while updating staff instructions")
        
        return redirect('consultation_detail', pk=pk)

class PrescriptionDashboardView(LoginRequiredMixin, ListView):
    model = Prescription
    context_object_name = 'prescriptions'
    paginate_by = 10

    def get_template_names(self):
        return [get_template_path('prescription_dashboard.html', self.request.user.role)]

    def get_queryset(self):
        queryset = Prescription.objects.select_related(
            'consultation__patient', 
            'consultation__doctor'
        ).prefetch_related('items__medication')
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(consultation__patient__first_name__icontains=search) |
                Q(consultation__patient__last_name__icontains=search) |
                Q(items__medication__name__icontains=search)
            ).distinct()
            
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now()
        last_month = today - timedelta(days=30)
        
        # Get templates
        templates = PrescriptionTemplate.objects.filter(
            Q(doctor=self.request.user) | Q(is_global=True)
        )
        
        # Analytics data
        context.update({
            'templates': templates,
            'total_templates': templates.count(),
            'active_templates': templates.filter(is_active=True).count(),
            'total_prescriptions': Prescription.objects.count(),
            'recent_prescriptions': Prescription.objects.filter(
                created_at__gte=today - timedelta(days=7)
            ).count()
        })
        
        # Add medications list for template creation
        context['medications'] = Medication.objects.filter(is_active=True)
        
        return context

class PrescriptionTemplateCreateView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            if not PermissionManager.check_module_modify(request.user, 'consultation_management'):
                messages.error(request, "You don't have permission to create prescription templates")
                return redirect('prescription_dashboard')

            # Extract basic information
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            is_active = request.POST.get('is_active') == 'on'
            is_global = request.POST.get('is_global') == 'on'

            # Validate required fields
            if not name:
                messages.error(request, "Template name is required")
                return redirect('prescription_dashboard')

            # Create the template
            with transaction.atomic():
                template = PrescriptionTemplate.objects.create(
                    name=name,
                    description=description,
                    doctor=request.user,
                    is_active=is_active,
                    is_global=is_global
                )

                # Process medications
                medications = request.POST.getlist('medications[]')
                dosages = request.POST.getlist('dosages[]')
                frequencies = request.POST.getlist('frequencies[]')
                durations = request.POST.getlist('durations[]')

                # Create template items
                for i in range(len(medications)):
                    if medications[i]:  # Only create if medication is selected
                        TemplateItem.objects.create(
                            template=template,
                            medication_id=medications[i],
                            dosage=dosages[i],
                            frequency=frequencies[i],
                            duration=durations[i],
                            order=i
                        )

            messages.success(request, "Prescription template created successfully")
            logger.info(f"Prescription template '{name}' created by user {request.user.id}")
            
        except Exception as e:
            logger.error(f"Error creating prescription template: {str(e)}")
            messages.error(request, "An error occurred while creating the template")

        return redirect('prescription_dashboard')


class PrescriptionTemplateEditView(LoginRequiredMixin, View):
    def get(self, request, pk):
        try:
            template = get_object_or_404(PrescriptionTemplate, pk=pk)
            data = {
                'template': {
                    'id': template.id,
                    'name': template.name,
                    'description': template.description,
                    'is_active': template.is_active,
                    'is_global': template.is_global,
                    'items': list(template.items.values(
                        'id',
                        'medication_id',
                        'dosage',
                        'frequency',
                        'duration',
                        'order'
                    ))
                }
            }
            return JsonResponse(data)
        except Exception as e:
            logger.error(f"Error fetching template data: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)

    def post(self, request, pk):
        try:
            if not PermissionManager.check_module_modify(request.user, 'consultation_management'):
                return JsonResponse({
                    'error': "You don't have permission to modify prescription templates"
                }, status=403)

            template = get_object_or_404(PrescriptionTemplate, pk=pk)

            with transaction.atomic():
                # Update basic information
                template.name = request.POST.get('name')
                template.description = request.POST.get('description', '')
                template.is_active = request.POST.get('is_active') == 'on'
                template.is_global = request.POST.get('is_global') == 'on'
                template.save()

                # Delete existing items
                template.items.all().delete()

                # Add new items
                medications = request.POST.getlist('medications[]')
                dosages = request.POST.getlist('dosages[]')
                frequencies = request.POST.getlist('frequencies[]')
                durations = request.POST.getlist('durations[]')

                for i in range(len(medications)):
                    if medications[i]:
                        TemplateItem.objects.create(
                            template=template,
                            medication_id=medications[i],
                            dosage=dosages[i],
                            frequency=frequencies[i],
                            duration=durations[i],
                            order=i
                        )

            messages.success(request, "Prescription template updated successfully")
            return redirect('prescription_dashboard')

        except Exception as e:
            logger.error(f"Error updating prescription template: {str(e)}")
            messages.error(request, "An error occurred while updating the template")
            return redirect('prescription_dashboard')

class PrescriptionTemplateDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        try:
            if not PermissionManager.check_module_delete(request.user, 'consultation_management'):
                messages.error(request, "You don't have permission to delete prescription templates")
                return redirect('prescription_dashboard')

            template = get_object_or_404(PrescriptionTemplate, pk=pk)
            
            # Additional validation if needed (e.g., only owner can delete)
            if not template.is_global and template.doctor != request.user:
                messages.error(request, "You can only delete your own templates")
                return redirect('prescription_dashboard')

            template_name = template.name
            template.delete()
            
            messages.success(request, f"Template '{template_name}' deleted successfully")
            logger.info(f"Prescription template {pk} deleted by user {request.user.id}")
            
        except Exception as e:
            logger.error(f"Error deleting prescription template: {str(e)}")
            messages.error(request, "An error occurred while deleting the template")
            
        return redirect('prescription_dashboard')


class ConsultationExportView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return PermissionManager.check_module_access(self.request.user, 'consultation_management')

    def get_filtered_queryset(self):
        """Get filtered queryset based on request parameters"""
        try:
            queryset = Consultation.objects.select_related('patient', 'doctor').all()
            date_range = self.request.GET.get('date_range')
            start_date = self.request.GET.get('start_date')
            end_date = self.request.GET.get('end_date')

            if date_range == 'custom' and start_date and end_date:
                try:
                    start_datetime = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
                    end_datetime = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d'))
                    end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
                    queryset = queryset.filter(scheduled_datetime__range=[start_datetime, end_datetime])
                except ValueError:
                    raise ValueError("Invalid date format")
            elif date_range:
                try:
                    days = int(date_range)
                    end_date = timezone.now()
                    start_date = end_date - timedelta(days=days)
                    queryset = queryset.filter(scheduled_datetime__range=[start_date, end_date])
                except ValueError:
                    raise ValueError("Invalid date range value")

            return queryset.order_by('-scheduled_datetime')

        except Exception as e:
            logger.error(f"Error filtering consultations: {str(e)}")
            raise

    def export_csv(self, queryset):
        try:
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="consultations_export.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'Consultation ID',
                'Patient Name',
                'Patient ID',
                'Doctor Name',
                'Type',
                'Status',
                'Scheduled Date',
                'Start Time',
                'End Time',
                'Duration (min)',
                'Chief Complaint',
                'Diagnosis',
                'Prescription Count',
                'Follow-up Date'
            ])

            for consultation in queryset:
                writer.writerow([
                    consultation.id,
                    consultation.patient.get_full_name(),
                    consultation.patient.id,
                    f"Dr. {consultation.doctor.get_full_name()}",
                    consultation.get_consultation_type_display(),
                    consultation.get_status_display(),
                    consultation.scheduled_datetime.strftime('%Y-%m-%d'),
                    consultation.actual_start_time.strftime('%H:%M') if consultation.actual_start_time else 'N/A',
                    consultation.actual_end_time.strftime('%H:%M') if consultation.actual_end_time else 'N/A',
                    consultation.duration_minutes,
                    consultation.chief_complaint,
                    consultation.diagnosis,
                    consultation.prescriptions.count(),
                    consultation.follow_up_date.strftime('%Y-%m-%d') if consultation.follow_up_date else 'N/A'
                ])

            return response
            
        except Exception as e:
            logger.error(f"Error exporting CSV: {str(e)}")
            raise

    def export_pdf(self, queryset):
        try:
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="consultations_export.pdf"'

            doc = SimpleDocTemplate(response, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()

            # Title
            elements.append(Paragraph('Consultation Report', styles['Heading1']))
            elements.append(Spacer(1, 20))

            # Date Range Info
            date_range = self.request.GET.get('date_range')
            if date_range == 'custom':
                date_info = f"Custom Range: {self.request.GET.get('start_date')} to {self.request.GET.get('end_date')}"
            else:
                date_info = f"Last {date_range} days"
            elements.append(Paragraph(f"Period: {date_info}", styles['Normal']))
            elements.append(Paragraph(f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
            elements.append(Spacer(1, 20))

            # Summary Statistics
            stats = [
                ['Total Consultations:', str(queryset.count())],
                ['Completed:', str(queryset.filter(status='COMPLETED').count())],
                ['Scheduled:', str(queryset.filter(status='SCHEDULED').count())],
                ['In Progress:', str(queryset.filter(status='IN_PROGRESS').count())]
            ]

            stats_table = Table(stats, colWidths=[120, 100])
            stats_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ]))
            elements.append(stats_table)
            elements.append(Spacer(1, 20))

            # Main Consultations Table
            data = [[
                'Patient',
                'Doctor',
                'Type',
                'Status',
                'Date',
                'Duration'
            ]]

            for consultation in queryset:
                data.append([
                    consultation.patient.get_full_name(),
                    f"Dr. {consultation.doctor.get_full_name()}",
                    consultation.get_consultation_type_display(),
                    consultation.get_status_display(),
                    consultation.scheduled_datetime.strftime('%Y-%m-%d'),
                    f"{consultation.duration_minutes} min"
                ])

            table = Table(data, repeatRows=1)
            table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ]))

            elements.append(table)
            doc.build(elements)
            return response

        except Exception as e:
            logger.error(f"Error exporting PDF: {str(e)}")
            raise

    def get(self, request):
        try:
            # Get filtered queryset
            queryset = self.get_filtered_queryset()
            
            # Get export format
            export_format = request.GET.get('format', 'csv').lower()
            
            if export_format == 'csv':
                return self.export_csv(queryset)
            elif export_format == 'pdf':
                return self.export_pdf(queryset)
            else:
                messages.error(request, "Invalid export format specified")
                return redirect('consultation_dashboard')
                
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('consultation_dashboard')
        except Exception as e:
            logger.error(f"Export error: {str(e)}")
            messages.error(request, "An error occurred during export")
            return redirect('consultation_dashboard')

class PrescriptionCreateView(LoginRequiredMixin, View):
    def post(self, request, consultation_id):
        try:
            consultation = get_object_or_404(Consultation, id=consultation_id)
            
            if not PermissionManager.check_module_modify(request.user, 'consultation_management'):
                messages.error(request, "You don't have permission to create prescriptions")
                return redirect('consultation_detail', pk=consultation_id)

            with transaction.atomic():
                # Create prescription
                prescription = Prescription.objects.create(
                    consultation=consultation,
                    notes=request.POST.get('notes', '')
                )

                # Process medication items
                medications = request.POST.getlist('medications[]')
                dosages = request.POST.getlist('dosages[]')
                frequencies = request.POST.getlist('frequencies[]')
                durations = request.POST.getlist('durations[]')

                for i in range(len(medications)):
                    if medications[i]:  # Only create if medication is selected
                        medication_id = medications[i]
                        
                        # Find stock item for this medication, if available
                        stock_item = None
                        try:
                            stock_item = StockItem.objects.filter(
                                name=Medication.objects.get(id=medication_id).name,
                                current_quantity__gt=0
                            ).first()
                        except Exception as e:
                            logger.warning(f"Could not find stock item for medication {medication_id}: {str(e)}")

                        PrescriptionItem.objects.create(
                            prescription=prescription,
                            medication_id=medication_id,
                            stock_item=stock_item,  # Can be None if not in stock
                            dosage=dosages[i],
                            frequency=frequencies[i],
                            duration=durations[i],
                            quantity_prescribed=1,  # Default value
                            order=i
                        )

                messages.success(request, "Prescription created successfully")
                logger.info(f"Prescription created for consultation {consultation_id} by user {request.user.id}")

            return redirect('consultation_detail', pk=consultation_id)

        except Exception as e:
            logger.error(f"Error creating prescription: {str(e)}")
            messages.error(request, "An error occurred while creating the prescription")
            return redirect('consultation_detail', pk=consultation_id)

class UsePrescriptionTemplateView(LoginRequiredMixin, View):
    def post(self, request, consultation_id, template_id):
        try:
            consultation = get_object_or_404(Consultation, id=consultation_id)
            template = get_object_or_404(PrescriptionTemplate, id=template_id)
            
            if not PermissionManager.check_module_modify(request.user, 'consultation_management'):
                messages.error(request, "You don't have permission to create prescriptions")
                return redirect('consultation_detail', pk=consultation_id)

            with transaction.atomic():
                # Create prescription from template
                prescription = Prescription.objects.create(
                    consultation=consultation,
                    template_used=template,
                    notes=f"Created from template: {template.name}"
                )

                # Create prescription items from template items
                for template_item in template.items.all():
                    # Check if medication is in stock (optional)
                    stock_item = None
                    try:
                        stock_item = StockItem.objects.filter(
                            name=template_item.medication.name,
                            current_quantity__gt=0
                        ).first()
                    except Exception as e:
                        logger.warning(f"Could not find stock item for medication {template_item.medication.id}: {str(e)}")

                    PrescriptionItem.objects.create(
                        prescription=prescription,
                        medication=template_item.medication,
                        stock_item=stock_item,
                        dosage=template_item.dosage,
                        frequency=template_item.frequency,
                        duration=template_item.duration,
                        instructions=template_item.instructions,
                        quantity_prescribed=1,
                        order=template_item.order
                    )

                messages.success(request, f"Prescription created from template '{template.name}'")
                logger.info(f"Prescription created from template {template.id} for consultation {consultation_id}")

            return redirect('consultation_detail', pk=consultation_id)

        except Exception as e:
            logger.error(f"Error creating prescription from template: {str(e)}")
            messages.error(request, "An error occurred while creating the prescription")
            return redirect('consultation_detail', pk=consultation_id)

class PrescriptionEditView(LoginRequiredMixin, View):
    def get(self, request, consultation_id, prescription_id):
        try:
            consultation = get_object_or_404(Consultation, id=consultation_id)
            prescription = get_object_or_404(Prescription, id=prescription_id, consultation=consultation)
            
            data = {
                'prescription': {
                    'id': prescription.id,
                    'notes': prescription.notes,
                    'items': list(prescription.items.values(
                        'id',
                        'medication_id',
                        'dosage',
                        'frequency',
                        'duration',
                        'instructions',
                        'quantity_prescribed',
                        'order'
                    ))
                }
            }
            return JsonResponse(data)
        except Exception as e:
            logger.error(f"Error fetching prescription data: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)

    def post(self, request, consultation_id, prescription_id):
        try:
            consultation = get_object_or_404(Consultation, id=consultation_id)
            prescription = get_object_or_404(Prescription, id=prescription_id, consultation=consultation)
            
            if not PermissionManager.check_module_modify(request.user, 'consultation_management'):
                messages.error(request, "You don't have permission to edit prescriptions")
                return redirect('consultation_detail', pk=consultation_id)

            with transaction.atomic():
                # Update prescription notes
                prescription.notes = request.POST.get('notes', '')
                prescription.save()

                # Delete existing items and create new ones
                prescription.items.all().delete()

                # Process medication items
                medications = request.POST.getlist('medications[]')
                dosages = request.POST.getlist('dosages[]')
                frequencies = request.POST.getlist('frequencies[]')
                durations = request.POST.getlist('durations[]')

                for i in range(len(medications)):
                    if medications[i]:
                        medication_id = medications[i]
                        
                        # Find stock item for this medication, if available
                        stock_item = None
                        try:
                            stock_item = StockItem.objects.filter(
                                name=Medication.objects.get(id=medication_id).name,
                                current_quantity__gt=0
                            ).first()
                        except Exception as e:
                            logger.warning(f"Could not find stock item for medication {medication_id}: {str(e)}")

                        PrescriptionItem.objects.create(
                            prescription=prescription,
                            medication_id=medication_id,
                            stock_item=stock_item,
                            dosage=dosages[i],
                            frequency=frequencies[i],
                            duration=durations[i],
                            quantity_prescribed=1,
                            order=i
                        )

                messages.success(request, "Prescription updated successfully")
                logger.info(f"Prescription {prescription_id} updated for consultation {consultation_id}")

            return redirect('consultation_detail', pk=consultation_id)

        except Exception as e:
            logger.error(f"Error updating prescription: {str(e)}")
            messages.error(request, "An error occurred while updating the prescription")
            return redirect('consultation_detail', pk=consultation_id)

class PrescriptionDeleteView(LoginRequiredMixin, View):
    def post(self, request, consultation_id, prescription_id):
        try:
            consultation = get_object_or_404(Consultation, id=consultation_id)
            prescription = get_object_or_404(Prescription, id=prescription_id, consultation=consultation)
            
            if not PermissionManager.check_module_delete(request.user, 'consultation_management'):
                messages.error(request, "You don't have permission to delete prescriptions")
                return redirect('consultation_detail', pk=consultation_id)

            with transaction.atomic():
                prescription.delete()
                messages.success(request, "Prescription deleted successfully")
                logger.info(f"Prescription {prescription_id} deleted from consultation {consultation_id}")

            return redirect('consultation_detail', pk=consultation_id)

        except Exception as e:
            logger.error(f"Error deleting prescription: {str(e)}")
            messages.error(request, "An error occurred while deleting the prescription")
            return redirect('consultation_detail', pk=consultation_id)