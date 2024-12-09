from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from access_control.permissions import PermissionManager
from error_handling.views import handler403

from access_control.models import Role

def get_template_path(base_template, role, module='settings'):
    """
    Simple template path resolver based on user role
    """
    if isinstance(role, Role):
        role_folder = role.template_folder
    else:
        role = Role.objects.get(name=role)
        role_folder = role.template_folder
    
    return f'{role_folder}/{module}/{base_template}'

class SettingsManagementView(View):
    def get(self, request):
        try:
            # Check module access permission
            if not PermissionManager.check_module_access(request.user, 'settings'):
                messages.error(request, "You don't have permission to access Settings")
                return handler403(request, exception="Access Denied")

            # Get template path - note the module parameter is now 'settings'
            template_path = get_template_path('settings.html', request.user.role, 'settings')
            
            if not template_path:
                messages.error(request, "Invalid template configuration")
                return handler403(request, exception="Template Configuration Error")

            context = {
                'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            }
            return render(request, template_path, context)

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('dashboard')
