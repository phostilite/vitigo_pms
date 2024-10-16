# website/views.py
import logging
from django.shortcuts import render
from django.views import View
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from user_management.utils import get_client_ip

logger = logging.getLogger(__name__)

class LandingPageView(View):
    @method_decorator(ratelimit(key='ip', rate='10/m', method=['GET']))
    def get(self, request):
        try:
            logger.info(f"Landing page accessed from IP: {get_client_ip(request)}")
            return render(request, 'website/landing_page.html')
        except Exception as e:
            logger.error(f"Error rendering landing page: {str(e)}")
            return render(request, 'error_handling/500.html', status=500)