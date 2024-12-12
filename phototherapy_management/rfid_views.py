# phototherapy_management/views.py

# Standard library imports
import logging

# Third-party imports
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone
from django.views import View

# Local application imports
from .models import PatientRFIDCard, PhototherapyPlan, PhototherapySession
from .utils import get_template_path
from error_handling.views import handler500

# Logger configuration
logger = logging.getLogger(__name__)
User = get_user_model()

class RFIDDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            # Get current datetime for comparisons
            now = timezone.now()

            # Get all RFID cards with related data
            rfid_cards = PatientRFIDCard.objects.select_related(
                'patient'
            ).annotate(
                sessions_count=Count('patient__phototherapy_plans__sessions',
                    filter=Q(patient__phototherapy_plans__sessions__status='COMPLETED')),
                active_plans=Count('patient__phototherapy_plans',
                    filter=Q(patient__phototherapy_plans__is_active=True))
            ).order_by('-is_active', '-assigned_date')

            # Calculate statistics
            card_stats = {
                'total': rfid_cards.count(),
                'active': rfid_cards.filter(is_active=True, expires_at__gt=now).count(),
                'expiring_soon': rfid_cards.filter(
                    is_active=True,
                    expires_at__range=[now, now + timezone.timedelta(days=30)]
                ).count(),
                'expired': rfid_cards.filter(expires_at__lte=now).count(),
            }

            # Get recent activities
            recent_sessions = PhototherapySession.objects.select_related(
                'plan__patient'
            ).filter(
                rfid_entry_time__isnull=False
            ).order_by('-rfid_entry_time')[:10]

            context = {
                'rfid_cards': rfid_cards,
                'stats': card_stats,
                'recent_sessions': recent_sessions,
            }

            template_path = get_template_path(
                'rfid_dashboard.html',
                request.user.role,
                'phototherapy_management'
            )
            return render(request, template_path, context)

        except Exception as e:
            logger.error(f"Error in RFID dashboard view: {str(e)}")
            messages.error(request, "An error occurred while loading RFID card data")
            return handler500(request, exception=str(e))