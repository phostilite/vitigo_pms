from .permissions import PermissionManager

def get_template_path(base_template, user_role):
    """
    Resolves template path based on user role using the permission system.
    """
    permissions = PermissionManager.get_permissions(user_role)
    module_name = base_template.split('/')[0]  # Extract module name from template
    
    if module_name in permissions and permissions[module_name]['can_access']:
        base_path = permissions[module_name]['template_path']
        return base_path.format(role=user_role.lower()) + base_template
    
    return None