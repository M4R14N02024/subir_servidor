# decorators.py

from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from functools import wraps

def check_group_permissions(view_func=None, groups=None, require_all=False):
    """
    Decorador mejorado para verificar permisos de grupo.
    
    Args:
        view_func: La vista a decorar
        groups: Lista de grupos permitidos
        require_all: Si es True, el usuario debe pertenecer a todos los grupos
    """
    if view_func is None:
        return lambda v: check_group_permissions(v, groups=groups, require_all=require_all)
    
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Superusuarios siempre tienen acceso total
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
            
        if not groups:
            return view_func(request, *args, **kwargs)
            
        user_groups = request.user.groups.values_list('name', flat=True)
        
        if require_all:
            has_permission = all(group in user_groups for group in groups)
        else:
            has_permission = any(group in user_groups for group in groups)
            
        if not has_permission:
            raise PermissionDenied("No tienes permisos suficientes para acceder a esta función.")
            
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view

def admin_required(view_func):
    """Solo administradores tienen acceso"""
    return check_group_permissions(view_func, groups=['Administradores'])

def admin_or_special_required(view_func):
    """Administradores o empleados especiales tienen acceso"""
    return check_group_permissions(
        view_func, 
        groups=['Administradores', 'Empleados Especiales']
    )

def any_employee_required(view_func):
    """Cualquier empleado tiene acceso"""
    return check_group_permissions(
        view_func,
        groups=['Administradores', 'Empleados Especiales', 'Empleados Regulares']
    )

def special_employee_required(view_func):
    """Solo empleados especiales tienen acceso"""
    return check_group_permissions(
        view_func,
        groups=['Empleados Especiales']
    )

# Decoradores específicos para funcionalidades
def can_manage_employees(view_func):
    """Verifica si el usuario puede gestionar empleados"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.has_perm('app.gestionar_empleados'):
            raise PermissionDenied("No tienes permiso para gestionar empleados.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def can_view_reports(view_func):
    """Verifica si el usuario puede ver reportes"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.has_perm('app.ver_reportes'):
            raise PermissionDenied("No tienes permiso para ver reportes.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view