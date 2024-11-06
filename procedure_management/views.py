# views.py
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.views import View
from .models import Procedure, ProcedureType
from django.contrib.auth import get_user_model

User = get_user_model()

def get_template_path(base_template, user_role):
    """
    Resolves template path based on user role.
    """
    # Only roles that should have access to procedure management
    role_template_map = {
        'ADMIN': 'admin',
        'DOCTOR': 'doctor',
        'NURSE': 'nurse',
        'SUPER_ADMIN': 'admin',
        'MANAGER': 'admin'
    }
    
    role_folder = role_template_map.get(user_role)
    if not role_folder:
        return None
    return f'dashboard/{role_folder}/procedure_management/{base_template}'

class ProcedureManagementView(View):
    def get(self, request):
        try:
            user_role = request.user.role  # Assuming role is stored in user model
            template_path = get_template_path('procedure_dashboard.html', user_role)
            
            if not template_path:
                return HttpResponse("Unauthorized access", status=403)

            # Fetch all procedure types and patients for filters
            procedure_types = ProcedureType.objects.all()
            patients = User.objects.filter(role='PATIENT')  # This ensures we only get users with PATIENT role

            # Fetch procedures with optional filtering
            procedures = Procedure.objects.all()
            procedure_type_id = request.GET.get('procedure_type')
            status = request.GET.get('status')
            patient_id = request.GET.get('patient')
            search_query = request.GET.get('search')

            if procedure_type_id:
                procedures = procedures.filter(procedure_type_id=procedure_type_id)
            if status:
                procedures = procedures.filter(status=status)
            if patient_id:
                procedures = procedures.filter(user_id=patient_id)  # Changed from patient_id to user_id
            if search_query:
                procedures = procedures.filter(notes__icontains=search_query)

            # Pagination
            paginator = Paginator(procedures, 10)  # Show 10 procedures per page
            page = request.GET.get('page')
            try:
                procedures = paginator.page(page)
            except PageNotAnInteger:
                procedures = paginator.page(1)
            except EmptyPage:
                procedures = paginator.page(paginator.num_pages)

            # Context data to be passed to the template
            context = {
                'procedure_types': procedure_types,
                'patients': patients,
                'procedures': procedures,
                'total_procedures': Procedure.objects.count(),
                'scheduled_procedures': Procedure.objects.filter(status='SCHEDULED').count(),
                'completed_procedures': Procedure.objects.filter(status='COMPLETED').count(),
                'cancelled_procedures': Procedure.objects.filter(status='CANCELLED').count(),
                'paginator': paginator,
                'page_obj': procedures,
            }

            return render(request, template_path, context)

        except Exception as e:
            # Handle any exceptions that occur
            return HttpResponse(f"An error occurred: {str(e)}", status=500)

class ProcedureDetailView(View):
    def get(self, request, procedure_id):
        try:
            # Check user authorization
            user_role = request.user.role
            template_path = get_template_path('procedure_detail.html', user_role)
            
            if not template_path:
                return HttpResponse("Unauthorized access", status=403)

            # Get procedure with related data
            procedure = get_object_or_404(Procedure.objects.select_related(
                'user',
                'procedure_type',
                'performed_by',
                'consent_form',
                'result'
            ).prefetch_related('images'), id=procedure_id)

            # Validate that the user is actually a patient
            if procedure.user and procedure.user.role != 'PATIENT':
                raise ValueError("Invalid patient assignment")

            context = {
                'procedure': procedure,
                'consent_form': procedure.consent_form if hasattr(procedure, 'consent_form') else None,
                'procedure_result': procedure.result if hasattr(procedure, 'result') else None,
                'images': procedure.images.all(),
                'patient_details': {
                    'name': procedure.user.get_full_name(),
                    'email': procedure.user.email,
                    'gender': procedure.user.gender,
                    'id': procedure.user.id
                } if procedure.user and procedure.user.role == 'PATIENT' else None,
                'performer_details': {
                    'name': procedure.performed_by.get_full_name(),
                    'role': procedure.performed_by.role,
                } if procedure.performed_by else None,
            }

            return render(request, template_path, context)

        except ValueError as e:
            return HttpResponse(f"Invalid procedure data: {str(e)}", status=400)
        except Exception as e:
            return HttpResponse(f"An error occurred: {str(e)}", status=500)

