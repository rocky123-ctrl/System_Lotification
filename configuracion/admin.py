from django.contrib import admin
from .models import ConfiguracionGeneral, ConfiguracionFinanciera


class ConfiguracionFinancieraInline(admin.StackedInline):
    """Inline para configuración financiera"""
    model = ConfiguracionFinanciera
    extra = 0
    fieldsets = (
        ('Plazos de Financiamiento', {
            'fields': ('plazo_minimo_meses', 'plazo_maximo_meses')
        }),
        ('Porcentajes de Enganche', {
            'fields': ('enganche_minimo_porcentaje', 'enganche_maximo_porcentaje')
        }),
        ('Costos y Configuraciones', {
            'fields': ('costo_instalacion_default', 'permitir_pagos_anticipados')
        }),
        ('Penalizaciones', {
            'fields': ('aplicar_penalizacion_atrasos', 'penalizacion_atraso_porcentaje')
        }),
    )


@admin.register(ConfiguracionGeneral)
class ConfiguracionGeneralAdmin(admin.ModelAdmin):
    list_display = (
        'nombre_lotificacion', 'ubicacion', 'tasa_anual', 'total_lotes', 
        'activo', 'fecha_actualizacion'
    )
    list_filter = ('activo', 'fecha_creacion', 'fecha_actualizacion')
    search_fields = ('nombre_lotificacion', 'ubicacion', 'email')
    ordering = ('-fecha_actualizacion',)
    list_editable = ('activo',)
    readonly_fields = ('tasa_mensual', 'fecha_creacion', 'fecha_actualizacion')
    
    fieldsets = (
        ('Información General', {
            'fields': ('nombre_lotificacion', 'ubicacion', 'descripcion', 'direccion_completa')
        }),
        ('Información de Contacto', {
            'fields': ('telefono', 'email', 'sitio_web')
        }),
        ('Datos del Proyecto', {
            'fields': ('fecha_inicio', 'total_lotes', 'area_total')
        }),
        ('Configuración Financiera', {
            'fields': ('tasa_anual', 'tasa_mensual')
        }),
        ('Archivos', {
            'fields': ('logo',)
        }),
        ('Control', {
            'fields': ('activo', 'fecha_creacion', 'fecha_actualizacion')
        }),
    )
    
    inlines = [ConfiguracionFinancieraInline]
    
    def save_model(self, request, obj, form, change):
        """Sobrescribir save para manejar activación única"""
        if obj.activo:
            # Desactivar todas las demás configuraciones
            ConfiguracionGeneral.objects.exclude(pk=obj.pk).update(activo=False)
        super().save_model(request, obj, form, change)


@admin.register(ConfiguracionFinanciera)
class ConfiguracionFinancieraAdmin(admin.ModelAdmin):
    list_display = (
        'configuracion', 'plazo_minimo_meses', 'plazo_maximo_meses', 
        'enganche_minimo_porcentaje', 'enganche_maximo_porcentaje',
        'fecha_actualizacion'
    )
    list_filter = ('fecha_creacion', 'fecha_actualizacion')
    search_fields = ('configuracion__nombre_lotificacion',)
    ordering = ('-fecha_actualizacion',)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    
    fieldsets = (
        ('Configuración General', {
            'fields': ('configuracion',)
        }),
        ('Plazos de Financiamiento', {
            'fields': ('plazo_minimo_meses', 'plazo_maximo_meses')
        }),
        ('Porcentajes de Enganche', {
            'fields': ('enganche_minimo_porcentaje', 'enganche_maximo_porcentaje')
        }),
        ('Costos', {
            'fields': ('costo_instalacion_default',)
        }),
        ('Configuraciones Adicionales', {
            'fields': ('permitir_pagos_anticipados', 'aplicar_penalizacion_atrasos')
        }),
        ('Penalizaciones', {
            'fields': ('penalizacion_atraso_porcentaje',)
        }),
        ('Control', {
            'fields': ('fecha_creacion', 'fecha_actualizacion')
        }),
    )
    
    def has_add_permission(self, request):
        """Solo permitir crear si no existe configuración financiera"""
        return not ConfiguracionFinanciera.objects.exists()
    
    def get_readonly_fields(self, request, obj=None):
        """Hacer configuracion readonly solo en edición, no en creación"""
        if obj:  # Si es una edición
            return self.readonly_fields + ('configuracion',)
        return self.readonly_fields
    
    def save_model(self, request, obj, form, change):
        """Sobrescribir save para asegurar que configuracion esté asignada"""
        if not change and not obj.configuracion_id:
            # Si es una nueva creación y no tiene configuración asignada
            config_activa = ConfiguracionGeneral.get_configuracion_activa()
            if config_activa:
                obj.configuracion = config_activa
        super().save_model(request, obj, form, change)
