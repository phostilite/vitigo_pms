# views.py

from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from django.utils import timezone
from django.http import HttpResponse
from .models import ResearchStudy, StudyProtocol, PatientStudyEnrollment, DataCollectionPoint, ResearchData, AnalysisResult, Publication
from django.db.models import Count

def get_template_path(base_template, user_role):
    """
    Resolves template path based on user role.
    """
    role_template_map = {
        'ADMIN': 'admin',
        'DOCTOR': 'doctor',
        'RESEARCHER': 'research',
        'SUPER_ADMIN': 'admin',
        'MANAGER': 'admin',
        'LAB_TECHNICIAN': 'lab'
    }
    
    role_folder = role_template_map.get(user_role)
    if not role_folder:
        return None
    return f'dashboard/{role_folder}/research_management/{base_template}'

class ResearchManagementView(View):
    def get(self, request):
        try:
            user_role = request.user.role
            template_path = get_template_path('research_dashboard.html', user_role)
            
            if not template_path:
                return HttpResponse("Unauthorized access", status=403)

            # Fetch all research studies, study protocols, patient enrollments, data collection points, research data, analysis results, and publications
            research_studies = ResearchStudy.objects.all()
            study_protocols = StudyProtocol.objects.all()
            patient_enrollments = PatientStudyEnrollment.objects.all()
            data_collection_points = DataCollectionPoint.objects.all()
            research_data = ResearchData.objects.all()
            analysis_results = AnalysisResult.objects.all()
            publications = Publication.objects.all()

            # Calculate statistics
            total_studies = research_studies.count()
            total_enrollments = patient_enrollments.count()
            total_data_points = research_data.count()
            total_analysis_results = analysis_results.count()
            total_publications = publications.count()

            # Pagination for research studies
            paginator = Paginator(research_studies, 10)  # Show 10 research studies per page
            page = request.GET.get('page')
            try:
                research_studies = paginator.page(page)
            except PageNotAnInteger:
                research_studies = paginator.page(1)
            except EmptyPage:
                research_studies = paginator.page(paginator.num_pages)

            # Context data to be passed to the template
            context = {
                'research_studies': research_studies,
                'study_protocols': study_protocols,
                'patient_enrollments': patient_enrollments,
                'data_collection_points': data_collection_points,
                'research_data': research_data,
                'analysis_results': analysis_results,
                'publications': publications,
                'total_studies': total_studies,
                'total_enrollments': total_enrollments,
                'total_data_points': total_data_points,
                'total_analysis_results': total_analysis_results,
                'total_publications': total_publications,
                'paginator': paginator,
                'page_obj': research_studies,
            }

            return render(request, template_path, context)

        except Exception as e:
            # Handle any exceptions that occur
            return HttpResponse(f"An error occurred: {str(e)}", status=500)