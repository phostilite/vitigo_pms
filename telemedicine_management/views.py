# views.py

from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from django.utils import timezone
from django.http import HttpResponse
from .models import TeleconsultationSession, TeleconsultationPrescription, TeleconsultationFile, TeleconsultationFeedback, TelemedicinevirtualWaitingRoom
from django.db.models import Count

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
        'TELEMEDICINE_STAFF': 'telemedicine'
    }
    
    role_folder = role_template_map.get(user_role)
    if not role_folder:
        return None
    return f'dashboard/{role_folder}/telemedicine_management/{base_template}'

class TelemedicineManagementView(View):
    def get(self, request):
        try:
            user_role = request.user.role
            template_path = get_template_path('telemedicine_dashboard.html', user_role)
            
            if not template_path:
                return HttpResponse("Unauthorized access", status=403)

            # Fetch all teleconsultation sessions, prescriptions, files, feedback, and waiting room entries
            teleconsultations = TeleconsultationSession.objects.all()
            prescriptions = TeleconsultationPrescription.objects.all()
            files = TeleconsultationFile.objects.all()
            feedbacks = TeleconsultationFeedback.objects.all()
            waiting_rooms = TelemedicinevirtualWaitingRoom.objects.all()

            # Calculate statistics
            total_teleconsultations = teleconsultations.count()
            total_prescriptions = prescriptions.count()
            total_files = files.count()
            total_feedbacks = feedbacks.count()
            total_waiting_rooms = waiting_rooms.count()

            # Pagination for teleconsultation sessions
            paginator = Paginator(teleconsultations, 10)  # Show 10 teleconsultations per page
            page = request.GET.get('page')
            try:
                teleconsultations = paginator.page(page)
            except PageNotAnInteger:
                teleconsultations = paginator.page(1)
            except EmptyPage:
                teleconsultations = paginator.page(paginator.num_pages)

            # Context data to be passed to the template
            context = {
                'teleconsultations': teleconsultations,
                'prescriptions': prescriptions,
                'files': files,
                'feedbacks': feedbacks,
                'waiting_rooms': waiting_rooms,
                'total_teleconsultations': total_teleconsultations,
                'total_prescriptions': total_prescriptions,
                'total_files': total_files,
                'total_feedbacks': total_feedbacks,
                'total_waiting_rooms': total_waiting_rooms,
                'paginator': paginator,
                'page_obj': teleconsultations,
            }

            return render(request, template_path, context)

        except Exception as e:
            # Handle any exceptions that occur
            return HttpResponse(f"An error occurred: {str(e)}", status=500)