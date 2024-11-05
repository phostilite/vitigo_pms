# views.py
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.views import View
from .models import Procedure, ProcedureType, Patient

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
            patients = Patient.objects.all()

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
                procedures = procedures.filter(patient_id=patient_id)
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