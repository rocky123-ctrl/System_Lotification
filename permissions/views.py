from rest_framework import status, generics, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from .models import Module, Role, ModulePermission, UserRole, AuditLog
from .serializers import (
    ModuleSerializer, RoleSerializer, ModulePermissionSerializer,
    UserRoleSerializer, UserRoleCreateSerializer, AuditLogSerializer,
    UserPermissionsSerializer, RoleWithPermissionsSerializer,
    ModuleWithPermissionsSerializer
)


class ModuleViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de módulos"""
    queryset = Module.objects.filter(is_active=True)
    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Module.objects.filter(is_active=True)
        name = self.request.query_params.get('name', None)
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset.order_by('order', 'name')

    @action(detail=True, methods=['get'])
    def permissions(self, request, pk=None):
        """Obtener permisos de un módulo específico"""
        module = self.get_object()
        permissions = ModulePermission.objects.filter(module=module, is_active=True)
        serializer = ModulePermissionSerializer(permissions, many=True)
        return Response(serializer.data)


class RoleViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de roles"""
    queryset = Role.objects.filter(is_active=True)
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RoleWithPermissionsSerializer
        return RoleSerializer

    def get_queryset(self):
        queryset = Role.objects.filter(is_active=True)
        name = self.request.query_params.get('name', None)
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset.order_by('name')

    @action(detail=True, methods=['post'])
    def assign_permissions(self, request, pk=None):
        """Asignar permisos a un rol"""
        role = self.get_object()
        permissions_data = request.data.get('permissions', [])
        
        # Eliminar permisos existentes
        ModulePermission.objects.filter(role=role).delete()
        
        # Crear nuevos permisos
        for perm_data in permissions_data:
            ModulePermission.objects.create(
                role=role,
                module_id=perm_data['module_id'],
                permission_type=perm_data['permission_type']
            )
        
        return Response({'message': 'Permisos asignados exitosamente'})

    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """Obtener usuarios con este rol"""
        role = self.get_object()
        user_roles = UserRole.objects.filter(role=role, is_active=True)
        serializer = UserRoleSerializer(user_roles, many=True)
        return Response(serializer.data)


class ModulePermissionViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de permisos de módulos"""
    queryset = ModulePermission.objects.filter(is_active=True)
    serializer_class = ModulePermissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = ModulePermission.objects.filter(is_active=True)
        role_id = self.request.query_params.get('role_id', None)
        module_id = self.request.query_params.get('module_id', None)
        
        if role_id:
            queryset = queryset.filter(role_id=role_id)
        if module_id:
            queryset = queryset.filter(module_id=module_id)
            
        return queryset


class UserRoleViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de roles de usuario"""
    queryset = UserRole.objects.filter(is_active=True)
    serializer_class = UserRoleSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserRoleCreateSerializer
        return UserRoleSerializer

    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)

    def get_queryset(self):
        queryset = UserRole.objects.filter(is_active=True)
        user_id = self.request.query_params.get('user_id', None)
        role_id = self.request.query_params.get('role_id', None)
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if role_id:
            queryset = queryset.filter(role_id=role_id)
            
        return queryset


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para consulta de registros de auditoría"""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = AuditLog.objects.all()
        user_id = self.request.query_params.get('user_id', None)
        action_type = self.request.query_params.get('action', None)
        module_id = self.request.query_params.get('module_id', None)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if action_type:
            queryset = queryset.filter(action=action_type)
        if module_id:
            queryset = queryset.filter(module_id=module_id)
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
            
        return queryset.order_by('-created_at')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_permissions(request, user_id):
    """Obtener permisos de un usuario específico"""
    try:
        user = User.objects.get(id=user_id)
        user_roles = UserRole.objects.filter(user=user, is_active=True)
        
        # Obtener módulos a los que tiene acceso
        modules = set()
        permissions = set()
        
        for user_role in user_roles:
            role_permissions = ModulePermission.objects.filter(
                role=user_role.role,
                is_active=True
            )
            
            for perm in role_permissions:
                modules.add(perm.module)
                permissions.add(f"{perm.module.name}_{perm.permission_type}")
        
        data = {
            'user_id': user_id,
            'modules': ModuleSerializer(list(modules), many=True).data,
            'permissions': list(permissions)
        }
        
        return Response(data)
    except User.DoesNotExist:
        return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_permissions(request):
    """Obtener permisos del usuario autenticado"""
    user = request.user
    user_roles = UserRole.objects.filter(user=user, is_active=True)
    
    # Obtener módulos a los que tiene acceso
    modules = set()
    permissions = set()
    
    for user_role in user_roles:
        role_permissions = ModulePermission.objects.filter(
            role=user_role.role,
            is_active=True
        )
        
        for perm in role_permissions:
            modules.add(perm.module)
            permissions.add(f"{perm.module.name}_{perm.permission_type}")
    
    data = {
        'user_id': user.id,
        'modules': ModuleSerializer(list(modules), many=True).data,
        'permissions': list(permissions)
    }
    
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_permission(request):
    """Verificar si un usuario tiene un permiso específico"""
    module_name = request.data.get('module_name')
    permission_type = request.data.get('permission_type')
    
    if not module_name or not permission_type:
        return Response({'error': 'Se requiere module_name y permission_type'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    user_roles = UserRole.objects.filter(user=user, is_active=True)
    
    has_permission = False
    for user_role in user_roles:
        permission_exists = ModulePermission.objects.filter(
            role=user_role.role,
            module__name=module_name,
            permission_type=permission_type,
            is_active=True
        ).exists()
        
        if permission_exists:
            has_permission = True
            break
    
    return Response({
        'has_permission': has_permission,
        'module_name': module_name,
        'permission_type': permission_type
    })


def log_audit_action(user, action, module=None, description="", request=None):
    """Función helper para registrar acciones de auditoría"""
    ip_address = None
    user_agent = None
    
    if request:
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    AuditLog.objects.create(
        user=user,
        action=action,
        module=module,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent
    )
