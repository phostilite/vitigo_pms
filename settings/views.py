from django.shortcuts import render
from django.views import View
from django.http import HttpResponse

def get_template_path(base_template, user_role):
    """
    Resolves template path based on user role.
    """
    role_template_map = {
        'ADMIN': 'admin',
        'SUPER_ADMIN': 'admin',
        'MANAGER': 'admin',
        'DOCTOR': 'doctor',
        'SYSTEM_ADMIN': 'admin'
    }
    
    role_folder = role_template_map.get(user_role)
    if not role_folder:
        return None
    return f'dashboard/{role_folder}/settings/{base_template}'

class SettingsManagementView(View):
    def get(self, request):
        try:
            user_role = request.user.role
            template_path = get_template_path('settings.html', user_role)
            
            if not template_path:
                return HttpResponse("Unauthorized access", status=403)

            context = {
                'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            }
            return render(request, template_path, context)

        except Exception as e:
            return HttpResponse(f"An error occurred: {str(e)}", status=500)
