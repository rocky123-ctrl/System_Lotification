from django.contrib import admin
from .models import Financiamiento, Cuota, Pago, ConfiguracionPago, PagoCapital


class CuotaInline(admin.TabularInline):
    model = Cuota
    extra = 0
    readonly_fields = ['numero_cuota', 'monto_capital', 'monto_interes', 'monto_total', 'fecha_vencimiento']
    fields = ['numero_cuota', 'monto_capital', 'monto_interes', 'monto_total', 'fecha_vencimiento', 'estado']


class PagoInline(admin.TabularInline):
    model = Pago
    extra = 0
    readonly_fields = ['fecha_creacion', 'creado_por']
    fields = ['cuota', 'monto_capital', 'monto_interes', 'monto_mora', 'monto_total', 'fecha_pago', 'metodo_pago', 'referencia_pago']


class PagoCapitalInline(admin.TabularInline):
    model = PagoCapital
    extra = 0
    readonly_fields = ['fecha_creacion', 'creado_por', 'referencia_pago']
    fields = ['monto', 'fecha_pago', 'concepto', 'referencia_pago']


@admin.register(Financiamiento)
class FinanciamientoAdmin(admin.ModelAdmin):
    list_display = ['lote', 'promitente_comprador', 'totalidad', 'saldo_restante', 'cuotas_pendientes', 'estado', 'fecha_inicio_financiamiento']
    list_filter = ['estado', 'fecha_inicio_financiamiento', 'fecha_vencimiento']
    search_fields = ['promitente_comprador', 'lote__numero_lote', 'lote__manzana__nombre']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion', 'creado_por', 'actualizado_por', 'saldo_restante', 'porcentaje_pagado']
    inlines = [CuotaInline, PagoInline, PagoCapitalInline]
    
    fieldsets = (
        ('Información del Lote', {
            'fields': ('lote', 'promitente_comprador')
        }),
        ('Valores Financieros', {
            'fields': ('totalidad', 'enganche', 'capital_cancelado', 'interes_cancelado', 'saldo')
        }),
        ('Plazos y Cuotas', {
            'fields': ('plazo_meses', 'cuota_mensual', 'cuotas_canceladas', 'cuotas_pendientes')
        }),
        ('Fechas', {
            'fields': ('fecha_inicio_financiamiento', 'fecha_vencimiento')
        }),
        ('Estado', {
            'fields': ('estado',)
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_actualizacion', 'creado_por', 'actualizado_por'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Cuota)
class CuotaAdmin(admin.ModelAdmin):
    list_display = ['financiamiento', 'numero_cuota', 'monto_total', 'fecha_vencimiento', 'estado', 'mora_atraso']
    list_filter = ['estado', 'fecha_vencimiento', 'fecha_pago']
    search_fields = ['financiamiento__promitente_comprador', 'financiamiento__lote__numero_lote']
    readonly_fields = ['financiamiento', 'numero_cuota', 'monto_capital', 'monto_interes', 'monto_total', 'fecha_vencimiento']
    
    actions = ['calcular_moras']
    
    def calcular_moras(self, request, queryset):
        """Acción para calcular moras de las cuotas seleccionadas"""
        cuotas_actualizadas = 0
        for cuota in queryset:
            if cuota.estado == 'pendiente':
                cuota.calcular_mora()
                cuota.save()
                cuotas_actualizadas += 1
        
        self.message_user(request, f'Se calcularon las moras de {cuotas_actualizadas} cuotas.')
    
    calcular_moras.short_description = "Calcular moras de las cuotas seleccionadas"


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ['financiamiento', 'cuota', 'monto_total', 'fecha_pago', 'metodo_pago', 'referencia_pago']
    list_filter = ['fecha_pago', 'metodo_pago']
    search_fields = ['financiamiento__promitente_comprador', 'financiamiento__lote__numero_lote', 'referencia_pago']
    readonly_fields = ['fecha_creacion', 'creado_por']


@admin.register(PagoCapital)
class PagoCapitalAdmin(admin.ModelAdmin):
    list_display = ['financiamiento', 'monto', 'fecha_pago', 'concepto', 'referencia_pago', 'fecha_creacion']
    list_filter = ['fecha_pago', 'fecha_creacion']
    search_fields = ['financiamiento__promitente_comprador', 'financiamiento__lote__numero_lote', 'referencia_pago', 'concepto']
    readonly_fields = ['fecha_creacion', 'creado_por', 'referencia_pago']
    
    fieldsets = (
        ('Información del Pago', {
            'fields': ('financiamiento', 'monto', 'fecha_pago', 'concepto')
        }),
        ('Referencia', {
            'fields': ('referencia_pago',)
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'creado_por'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Sobrescribir save_model para asignar el usuario creador"""
        if not change:  # Si es una nueva creación
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(ConfiguracionPago)
class ConfiguracionPagoAdmin(admin.ModelAdmin):
    list_display = ['tipo_pago', 'dia_pago', 'activo']
    list_filter = ['tipo_pago', 'activo']
    search_fields = ['tipo_pago']
