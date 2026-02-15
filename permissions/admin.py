from django.contrib import admin
from .models import Module, Role, ModulePermission, UserRole, AuditLog


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('order', 'name')
    list_editable = ('is_active', 'order')


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    list_editable = ('is_active',)


@admin.register(ModulePermission)
class ModulePermissionAdmin(admin.ModelAdmin):
    list_display = ('module', 'role', 'permission_type', 'is_active', 'created_at')
    list_filter = ('module', 'role', 'permission_type', 'is_active', 'created_at')
    search_fields = ('module__name', 'role__name')
    ordering = ('module', 'role', 'permission_type')
    list_editable = ('is_active',)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_active', 'assigned_by', 'assigned_at', 'expires_at')
    list_filter = ('role', 'is_active', 'assigned_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'role__name')
    ordering = ('user', 'role')
    list_editable = ('is_active',)
    readonly_fields = ('assigned_at',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'module', 'ip_address', 'created_at')
    list_filter = ('action', 'module', 'created_at')
    search_fields = ('user__username', 'description', 'ip_address')
    ordering = ('-created_at',)
    readonly_fields = ('user', 'action', 'module', 'description', 'ip_address', 'user_agent', 'created_at')
    list_per_page = 50
