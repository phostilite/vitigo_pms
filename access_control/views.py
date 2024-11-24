from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import UserPassesTestMixin
from .models import Role, Module, ModulePermission

def get_template_path(base_template, role, module=''):
    """
    Resolves template path based on user role.
    Now uses the template_folder from Role model.
    """
    if isinstance(role, Role):
        role_folder = role.template_folder
    else:
        # Fallback for any legacy code
        role = Role.objects.get(name=role)
        role_folder = role.template_folder
    
    if module:
        return f'dashboard/{role_folder}/{module}/{base_template}'
    return f'dashboard/{role_folder}/{base_template}'

class AccessControlDashboardView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role.name in ['SUPER_ADMIN', 'ADMIN']

    def get_template_name(self):
        return get_template_path('dashboard.html', self.request.user.role, 'access_control')

    def get(self, request):
        context = {
            'total_roles': Role.objects.count(),
            'total_modules': Module.objects.filter(is_active=True).count(),
            'total_permissions': ModulePermission.objects.count(),
            'roles': Role.objects.prefetch_related('users', 'modulepermission_set').all(),
            'recent_activities': self.get_recent_activities(),
        }
        return render(request, self.get_template_name(), context)
    
    def get_recent_activities(self):
        # Implement logic to fetch recent permission changes or role assignments
        # This is a placeholder that you can implement based on your needs
        return []
