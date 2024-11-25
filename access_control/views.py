from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse
from .models import Role, Module, ModulePermission
from django.contrib.auth import get_user_model
from django.db.models import Prefetch

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

class CreateRoleView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role.name in ['SUPER_ADMIN', 'ADMIN']

    def get_template_name(self):
        return get_template_path('create_role.html', self.request.user.role, 'access_control')

    def get(self, request):
        context = {
            'modules': Module.objects.filter(is_active=True).order_by('order', 'display_name')
        }
        return render(request, self.get_template_name(), context)

    def post(self, request):
        try:
            # Create new role
            role = Role.objects.create(
                name=request.POST['name'].upper(),
                display_name=request.POST['display_name'],
                template_folder=request.POST['template_folder'],
                description=request.POST['description']
            )

            # Set module permissions
            for module in Module.objects.filter(is_active=True):
                ModulePermission.objects.create(
                    module=module,
                    role=role,
                    can_access=request.POST.get(f'permissions_{module.id}_access') == 'on',
                    can_modify=request.POST.get(f'permissions_{module.id}_modify') == 'on',
                    can_delete=request.POST.get(f'permissions_{module.id}_delete') == 'on'
                )

            messages.success(request, 'Role created successfully.')
            return redirect('access_control_dashboard')
        except Exception as e:
            messages.error(request, f'Error creating role: {str(e)}')
            return redirect('create_role')

class RoleDetailView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role.name in ['SUPER_ADMIN', 'ADMIN']

    def get_template_name(self):
        return get_template_path('role_detail.html', self.request.user.role, 'access_control')

    def get(self, request, role_id):
        try:
            # Optimize queries with select_related and prefetch_related
            role = Role.objects.prefetch_related(
                'users',
                'modulepermission_set__module',
                Prefetch(
                    'users',
                    queryset=get_user_model().objects.select_related('role').order_by('-date_joined')[:5],
                    to_attr='recent_users_list'
                )
            ).get(id=role_id)

            # Get all modules with permissions
            modules_with_permissions = []
            module_permissions = {mp.module_id: mp for mp in role.modulepermission_set.all()}
            
            for module in Module.objects.all():
                perm = module_permissions.get(module.id)
                if perm:
                    modules_with_permissions.append({
                        'module': module,
                        'has_access': perm.can_access,
                        'can_modify': perm.can_modify,
                        'can_delete': perm.can_delete,
                        'last_updated': perm.updated_at
                    })

            # Calculate permission stats
            total_modifiable = len([m for m in modules_with_permissions if m['can_modify']])
            total_deletable = len([m for m in modules_with_permissions if m['can_delete']])
            total_accessible = len([m for m in modules_with_permissions if m['has_access']])

            context = {
                'role': role,
                'modules_with_permissions': modules_with_permissions,
                'total_users': role.users.count(),
                'recent_users': role.recent_users_list,
                'total_modules': total_accessible,
                'total_modifiable': total_modifiable,
                'total_deletable': total_deletable,
            }
            return render(request, self.get_template_name(), context)
            
        except Role.DoesNotExist:
            messages.error(request, 'Role not found.')
            return redirect('access_control_dashboard')

class EditRoleView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role.name in ['SUPER_ADMIN', 'ADMIN']

    def get_template_name(self):
        return get_template_path('edit_role.html', self.request.user.role, 'access_control')

    def get(self, request, role_id):
        try:
            role = Role.objects.prefetch_related('modulepermission_set').get(id=role_id)
            
            # Get modules and attach their permissions
            modules = Module.objects.filter(is_active=True).order_by('order', 'display_name')
            permissions_dict = {
                mp.module_id: mp for mp in role.modulepermission_set.all()
            }
            
            # Attach permissions to each module
            for module in modules:
                module.permission = permissions_dict.get(module.id, ModulePermission(
                    can_access=False,
                    can_modify=False,
                    can_delete=False
                ))
            
            context = {
                'role': role,
                'modules': modules,
            }
            return render(request, self.get_template_name(), context)
        except Role.DoesNotExist:
            messages.error(request, 'Role not found.')
            return redirect('access_control_dashboard')

    def post(self, request, role_id):
        try:
            role = Role.objects.get(id=role_id)
            
            # Update basic role information
            role.display_name = request.POST['display_name']
            role.template_folder = request.POST['template_folder']
            role.description = request.POST['description']
            role.save()

            # Update module permissions
            for module in Module.objects.filter(is_active=True):
                permission, created = ModulePermission.objects.get_or_create(
                    module=module,
                    role=role,
                    defaults={
                        'can_access': False,
                        'can_modify': False,
                        'can_delete': False
                    }
                )
                
                permission.can_access = request.POST.get(f'permissions_{module.id}_access') == 'on'
                permission.can_modify = request.POST.get(f'permissions_{module.id}_modify') == 'on'
                permission.can_delete = request.POST.get(f'permissions_{module.id}_delete') == 'on'
                permission.save()

            messages.success(request, 'Role updated successfully.')
            return redirect('role_detail', role_id=role.id)
            
        except Role.DoesNotExist:
            messages.error(request, 'Role not found.')
        except Exception as e:
            messages.error(request, f'Error updating role: {str(e)}')
        
        return redirect('edit_role', role_id=role_id)

class DeleteRoleView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role.name in ['SUPER_ADMIN', 'ADMIN']

    def post(self, request, role_id):
        try:
            role = Role.objects.get(id=role_id)
            
            # Don't allow deletion of SUPER_ADMIN or ADMIN roles
            if role.name in ['SUPER_ADMIN', 'ADMIN']:
                messages.error(request, 'Cannot delete system roles.')
                return redirect('access_control_dashboard')
            
            # Store role name for success message
            role_name = role.display_name
            
            # Delete the role (this will cascade delete associated permissions)
            role.delete()
            
            messages.success(request, f'Role "{role_name}" has been deleted successfully.')
            
        except Role.DoesNotExist:
            messages.error(request, 'Role not found.')
        except Exception as e:
            messages.error(request, f'Error deleting role: {str(e)}')
        
        return redirect('access_control_dashboard')

class ModuleListView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role.name in ['SUPER_ADMIN', 'ADMIN']

    def get_template_name(self):
        return get_template_path('modules.html', self.request.user.role, 'access_control')

    def get(self, request):
        modules = Module.objects.all().order_by('order', 'display_name')
        context = {
            'modules': modules,
            'total_modules': modules.count(),
            'active_modules': modules.filter(is_active=True).count(),
            'inactive_modules': modules.filter(is_active=False).count(),
        }
        return render(request, self.get_template_name(), context)

class ManageRolesView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role.name in ['SUPER_ADMIN', 'ADMIN']

    def get_template_name(self):
        return get_template_path('manage_roles.html', self.request.user.role, 'access_control')

    def get(self, request):
        context = {
            'roles': Role.objects.prefetch_related('users', 'modulepermission_set').all()
        }
        return render(request, self.get_template_name(), context)

