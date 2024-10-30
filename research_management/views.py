# views.py

from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from django.utils import timezone
from django.http import HttpResponse
from .models import ResearchStudy, StudyProtocol, PatientStudyEnrollment, DataCollectionPoint, ResearchData, AnalysisResult, Publication
from django.db.models import Count

class ResearchManagementView(View):
    template_name = 'dashboard/admin/research_management/research_dashboard.html'

    def get(self, request):
        try:
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

            return render(request, self.template_name, context)

        except Exception as e:
            # Handle any exceptions that occur
            return HttpResponse(f"An error occurred: {str(e)}", status=500)