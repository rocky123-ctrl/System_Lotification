from django.contrib import admin
from .models import Plano


@admin.register(Plano)
class PlanoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'fecha_subida', 'activo', 'es_pdf', 'es_imagen']
    list_filter = ['activo', 'fecha_subida']
    search_fields = ['nombre']
    readonly_fields = ['fecha_subida', 'fecha_actualizacion', 'url', 'es_pdf', 'es_imagen']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'archivo', 'activo')
        }),
        ('Información del Archivo', {
            'fields': ('url', 'es_pdf', 'es_imagen')
        }),
        ('Fechas', {
            'fields': ('fecha_subida', 'fecha_actualizacion')
        }),
    )
