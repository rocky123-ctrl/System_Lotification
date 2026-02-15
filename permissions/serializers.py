from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import Module, Role, ModulePermission, UserRole, AuditLog


class ModuleSerializer(serializers.ModelSerializer):
    """Serializer para módulos"""
    
    class Meta:
        model = Module
        fields = '__all__'


class RoleSerializer(serializers.ModelSerializer):
    """Serializer para roles"""
    
    class Meta:
        model = Role
        fields = '__all__'


class ModulePermissionSerializer(serializers.ModelSerializer):
    """Serializer para permisos de módulos"""
    module_name = serializers.CharField(source='module.name', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    permission_type_display = serializers.CharField(source='get_permission_type_display', read_only=True)
    
    class Meta:
        model = ModulePermission
        fields = '__all__'


class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer para roles de usuario"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.SerializerMethodField()
    role_name = serializers.CharField(source='role.name', read_only=True)
    assigned_by_username = serializers.CharField(source='assigned_by.username', read_only=True)
    
    class Meta:
        model = UserRole
        fields = '__all__'
    
    def get_user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()


class UserRoleCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear roles de usuario"""
    
    class Meta:
        model = UserRole
        fields = ['user', 'role', 'expires_at']


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer para registros de auditoría"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    module_name = serializers.CharField(source='module.name', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = '__all__'
        read_only_fields = ['user', 'ip_address', 'user_agent', 'created_at']


class UserPermissionsSerializer(serializers.Serializer):
    """Serializer para obtener permisos de un usuario"""
    user_id = serializers.IntegerField()
    modules = ModuleSerializer(many=True, read_only=True)
    permissions = serializers.ListField(child=serializers.CharField(), read_only=True)


class RoleWithPermissionsSerializer(serializers.ModelSerializer):
    """Serializer para roles con sus permisos"""
    permissions = ModulePermissionSerializer(source='module_permissions', many=True, read_only=True)
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = '__all__'
    
    def get_user_count(self, obj):
        return obj.user_roles.filter(is_active=True).count()


class ModuleWithPermissionsSerializer(serializers.ModelSerializer):
    """Serializer para módulos con sus permisos"""
    permissions = ModulePermissionSerializer(source='permissions', many=True, read_only=True)
    
    class Meta:
        model = Module
        fields = '__all__'
