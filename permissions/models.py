from django.db import models
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType


class Module(models.Model):
    """
    Modelo para representar módulos del sistema
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)
    url = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Módulo'
        verbose_name_plural = 'Módulos'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Role(models.Model):
    """
    Modelo para roles personalizados
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        ordering = ['name']

    def __str__(self):
        return self.name


class ModulePermission(models.Model):
    """
    Modelo para permisos específicos de módulos
    """
    PERMISSION_CHOICES = [
        ('view', 'Ver'),
        ('create', 'Crear'),
        ('edit', 'Editar'),
        ('delete', 'Eliminar'),
        ('export', 'Exportar'),
        ('import', 'Importar'),
    ]

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='permissions')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='module_permissions')
    permission_type = models.CharField(max_length=20, choices=PERMISSION_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Permiso de Módulo'
        verbose_name_plural = 'Permisos de Módulos'
        unique_together = ['module', 'role', 'permission_type']
        ordering = ['module', 'role', 'permission_type']

    def __str__(self):
        return f"{self.role.name} - {self.module.name} - {self.get_permission_type_display()}"


class UserRole(models.Model):
    """
    Modelo para asignar roles a usuarios
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_roles')
    is_active = models.BooleanField(default=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_roles')
    assigned_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Rol de Usuario'
        verbose_name_plural = 'Roles de Usuarios'
        unique_together = ['user', 'role']
        ordering = ['user', 'role']

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"


class AuditLog(models.Model):
    """
    Modelo para registrar auditoría de acciones
    """
    ACTION_CHOICES = [
        ('login', 'Inicio de sesión'),
        ('logout', 'Cierre de sesión'),
        ('create', 'Crear'),
        ('update', 'Actualizar'),
        ('delete', 'Eliminar'),
        ('view', 'Ver'),
        ('export', 'Exportar'),
        ('import', 'Importar'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    module = models.ForeignKey(Module, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Registros de Auditoría'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username if self.user else 'Sistema'} - {self.get_action_display()} - {self.created_at}"
