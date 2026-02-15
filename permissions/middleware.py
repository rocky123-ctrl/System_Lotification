from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.urls import resolve
from .models import AuditLog, Module, ModulePermission, UserRole
from .views import log_audit_action
import json


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware para registrar automáticamente las acciones de los usuarios
    """
    
    def process_request(self, request):
        # Solo registrar para usuarios autenticados
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Obtener información de la URL
            resolved = resolve(request.path_info)
            view_name = resolved.view_name
            url_name = resolved.url_name
            
            # Determinar la acción basada en el método HTTP
            action_map = {
                'GET': 'view',
                'POST': 'create',
                'PUT': 'update',
                'PATCH': 'update',
                'DELETE': 'delete',
            }
            
            action = action_map.get(request.method, 'view')
            
            # Intentar encontrar el módulo correspondiente
            module = None
            try:
                # Buscar módulo por URL pattern
                module = Module.objects.filter(url__icontains=url_name).first()
                if not module:
                    # Buscar por nombre de la app
                    app_name = resolved.app_name
                    if app_name:
                        module = Module.objects.filter(name__icontains=app_name).first()
            except:
                pass
            
            # Crear descripción
            description = f"{request.method} {request.path}"
            
            # Registrar la acción
            log_audit_action(
                user=request.user,
                action=action,
                module=module,
                description=description,
                request=request
            )


class PermissionMiddleware(MiddlewareMixin):
    """
    Middleware para verificar permisos en tiempo real
    """
    
    def process_request(self, request):
        # Solo verificar para usuarios autenticados
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None
        
        # Obtener información de la URL
        resolved = resolve(request.path_info)
        view_name = resolved.view_name
        url_name = resolved.url_name
        
        # Determinar el tipo de permiso basado en el método HTTP
        permission_map = {
            'GET': 'view',
            'POST': 'create',
            'PUT': 'edit',
            'PATCH': 'edit',
            'DELETE': 'delete',
        }
        
        permission_type = permission_map.get(request.method, 'view')
        
        # Intentar encontrar el módulo correspondiente
        module = None
        try:
            module = Module.objects.filter(url__icontains=url_name).first()
            if not module:
                app_name = resolved.app_name
                if app_name:
                    module = Module.objects.filter(name__icontains=app_name).first()
        except:
            pass
        
        if module:
            # Verificar si el usuario tiene el permiso necesario
            user_roles = UserRole.objects.filter(user=request.user, is_active=True)
            has_permission = False
            
            for user_role in user_roles:
                permission_exists = ModulePermission.objects.filter(
                    role=user_role.role,
                    module=module,
                    permission_type=permission_type,
                    is_active=True
                ).exists()
                
                if permission_exists:
                    has_permission = True
                    break
            
            # Si no tiene permiso, devolver error
            if not has_permission:
                return JsonResponse({
                    'error': 'No tienes permisos para realizar esta acción',
                    'module': module.name,
                    'permission_required': permission_type
                }, status=403)
        
        return None
