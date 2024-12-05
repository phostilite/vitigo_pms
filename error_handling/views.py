# error_handling/views.py

from django.shortcuts import render
from django.http import HttpRequest
from .models import ErrorLog
import traceback
import json

def log_error(request: HttpRequest, status_code: int, exception: Exception = None):
    """Helper function to log errors to database"""
    error_level = 'ERROR' if status_code >= 500 else 'WARNING'
    
    error_data = {
        'headers': dict(request.headers),
        'method': request.method,
        'path': request.path,
    }
    
    if hasattr(request, 'user'):
        user = request.user if request.user.is_authenticated else None
    else:
        user = None

    ErrorLog.objects.create(
        level=error_level,
        message=str(exception) if exception else f"HTTP {status_code}",
        traceback=traceback.format_exc() if exception else None,
        user=user,
        url=request.build_absolute_uri(),
        method=request.method,
        data=error_data
    )

def handler400(request: HttpRequest, exception=None):
    log_error(request, 400, exception)
    return render(request, 'error_handling/400.html', status=400)

def handler403(request: HttpRequest, exception=None):
    log_error(request, 403, exception)
    return render(request, 'error_handling/403.html', status=403)

def handler404(request: HttpRequest, exception=None):
    log_error(request, 404, exception)
    return render(request, 'error_handling/404.html', status=404)

def handler500(request: HttpRequest, exception=None):
    """
    500 error handler.
    Templates should have a context.
    """
    log_error(request, 500, exception)
    context = {'error': str(exception) if exception else "Internal Server Error"}
    return render(request, 'error_handling/500.html', context, status=500)