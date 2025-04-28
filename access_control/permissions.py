from rest_framework import permissions

class IsAdministrator(permissions.BasePermission):
    """
    Permiso que solo permite a los administradores realizar la acción.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Los superusuarios y staff siempre tienen permiso
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Verificar si el usuario tiene un perfil con rol de Administrador
        if hasattr(request.user, 'profile') and request.user.profile.role:
            return request.user.profile.role.name == 'Administrator'
        
        return False

class IsSecurityPersonnel(permissions.BasePermission):
    """
    Permiso que permite a personal de seguridad realizar la acción.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Los superusuarios y staff siempre tienen permiso
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Verificar si el usuario tiene un perfil con rol de Seguridad
        if hasattr(request.user, 'profile') and request.user.profile.role:
            return request.user.profile.role.name in ['Security', 'Security Supervisor']
        
        return False

class IsReceptionist(permissions.BasePermission):
    """
    Permiso que permite a los recepcionistas realizar la acción.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Los superusuarios y staff siempre tienen permiso
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Verificar si el usuario tiene un perfil con rol de Recepcionista
        if hasattr(request.user, 'profile') and request.user.profile.role:
            return request.user.profile.role.name == 'Receptionist'
        
        return False

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permiso que permite a los propietarios de un objeto o administradores realizar la acción.
    """
    def has_object_permission(self, request, view, obj):
        # Los superusuarios y staff siempre tienen permiso
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Verificar si el usuario tiene un perfil con rol de Administrador
        if hasattr(request.user, 'profile') and request.user.profile.role:
            if request.user.profile.role.name == 'Administrator':
                return True
        
        # Verificar si el usuario es el propietario
        # Esto depende del modelo, así que hay que implementarlo según el caso
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'host'):
            return obj.host == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False