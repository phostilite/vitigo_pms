from django.core.cache import cache
from .models import ModulePermission

class PermissionManager:
    CACHE_KEY = "module_permissions_{role}"
    CACHE_TIMEOUT = 3600  # 1 hour

    @classmethod
    def get_permissions(cls, role):
        cache_key = cls.CACHE_KEY.format(role=role)
        permissions = cache.get(cache_key)
        
        if permissions is None:
            permissions = ModulePermission.objects.filter(
                role__name=role,
                module__is_active=True
            ).select_related('module')
            
            # Convert to dictionary for faster lookup
            permissions_dict = {
                perm.module.name: {
                    'can_access': perm.can_access,
                    'can_modify': perm.can_modify,
                    'template_path': perm.module.base_template_path
                } for perm in permissions
            }
            
            cache.set(cache_key, permissions_dict, cls.CACHE_TIMEOUT)
            return permissions_dict
            
        return permissions

    @classmethod
    def invalidate_cache(cls, role):
        cache_key = cls.CACHE_KEY.format(role=role)
        cache.delete(cache_key)