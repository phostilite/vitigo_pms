# views.py

from django.shortcuts import render
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from .models import PhototherapyPlan, PhototherapyType, PhototherapyProtocol, PhototherapySession, PhototherapyDevice
from patient_management.models import Patient

class PhototherapyManagementView(View):
    template_name = 'dashboard/admin/phototherapy_management/phototherapy_dashboard.html'

    def get(self, request):
        try:
            # Fetch all phototherapy types, protocols, and plans
            phototherapy_types = PhototherapyType.objects.all()
            protocols = PhototherapyProtocol.objects.all()
            plans = PhototherapyPlan.objects.all()

            # Fetch sessions and devices
            sessions = PhototherapySession.objects.all()
            devices = PhototherapyDevice.objects.all()

            # Fetch patients
            patients = Patient.objects.all()

            # Calculate statistics
            active_plans = plans.filter(is_active=True).count()
            completed_sessions = sessions.filter(compliance='COMPLETED').count()
            missed_sessions = sessions.filter(compliance='MISSED').count()
            active_devices = devices.filter(is_active=True).count()

            # Pagination for plans
            paginator = Paginator(plans, 10)  # Show 10 plans per page
            page = request.GET.get('page')
            try:
                plans = paginator.page(page)
            except PageNotAnInteger:
                plans = paginator.page(1)
            except EmptyPage:
                plans = paginator.page(paginator.num_pages)

            # Context data to be passed to the template
            context = {
                'phototherapy_types': phototherapy_types,
                'protocols': protocols,
                'phototherapy_plans': plans,
                'sessions': sessions,
                'devices': devices,
                'patients': patients,
                'active_plans': active_plans,
                'completed_sessions': completed_sessions,
                'missed_sessions': missed_sessions,
                'active_devices': active_devices,
                'paginator': paginator,
                'page_obj': plans,
            }

            return render(request, self.template_name, context)

        except Exception as e:
            # Handle any exceptions that occur
            return HttpResponse(f"An error occurred: {str(e)}", status=500)