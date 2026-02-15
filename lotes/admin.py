from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from .models import Manzana, Lote, HistorialLote
from .forms import ImportarLotesForm, ExportarLotesForm
import pandas as pd
from io import BytesIO


@admin.register(Manzana)
class ManzanaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'activo', 'fecha_creacion')
    list_filter = ('activo', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')
    ordering = ('nombre',)
    list_editable = ('activo',)


@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = (
        'numero_lote', 'manzana', 'metros_cuadrados', 'valor_total', 
        'enganche', 'estado', 'activo', 'fecha_creacion'
    )
    list_filter = ('manzana', 'estado', 'activo', 'fecha_creacion')
    search_fields = ('numero_lote', 'manzana__nombre')
    ordering = ('manzana', 'numero_lote')
    list_editable = ('estado', 'activo')
    readonly_fields = ('saldo_financiar', 'fecha_creacion', 'fecha_actualizacion')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('manzana', 'numero_lote', 'metros_cuadrados', 'estado')
        }),
        ('Información Financiera', {
            'fields': ('valor_total', 'enganche', 'costo_instalacion', 'saldo_financiar')
        }),
        ('Financiamiento', {
            'fields': ('plazo_meses', 'cuota_mensual')
        }),
        ('Control', {
            'fields': ('activo', 'fecha_creacion', 'fecha_actualizacion')
        }),
    )
    
    def get_urls(self):
        """Agregar URLs personalizadas para importación y exportación"""
        urls = super().get_urls()
        custom_urls = [
            path('importar/', self.admin_site.admin_view(self.importar_lotes), name='lotes_lote_importar'),
            path('exportar/', self.admin_site.admin_view(self.exportar_lotes), name='lotes_lote_exportar'),
        ]
        return custom_urls + urls
    
    def importar_lotes(self, request):
        """Vista para importar lotes desde Excel"""
        if request.method == 'POST':
            form = ImportarLotesForm(request.POST, request.FILES)
            if form.is_valid():
                resultado = form.procesar_archivo(request)
                if resultado:
                    return redirect('admin:lotes_lote_changelist')
        else:
            form = ImportarLotesForm()
        
        context = {
            'title': 'Importar Lotes desde Excel',
            'form': form,
            'opts': self.model._meta,
        }
        return render(request, 'admin/lotes/lote/importar_lotes.html', context)
    
    def exportar_lotes(self, request):
        """Vista para exportar lotes a Excel"""
        if request.method == 'POST':
            form = ExportarLotesForm(request.POST)
            if form.is_valid():
                return self.generar_archivo_exportacion(request, form.cleaned_data)
        else:
            form = ExportarLotesForm()
        
        context = {
            'title': 'Exportar Lotes a Excel',
            'form': form,
            'opts': self.model._meta,
        }
        return render(request, 'admin/lotes/lote/exportar_lotes.html', context)
    
    def generar_archivo_exportacion(self, request, datos_form):
        """Generar archivo de exportación"""
        # Obtener lotes según filtros
        queryset = Lote.objects.all()
        
        if not datos_form['incluir_inactivos']:
            queryset = queryset.filter(activo=True)
        
        if datos_form['solo_disponibles']:
            queryset = queryset.filter(estado='disponible')
        
        # Preparar datos para exportación
        datos_exportacion = []
        for lote in queryset:
            datos_exportacion.append({
                'manzana': lote.manzana.nombre,
                'numero_lote': lote.numero_lote,
                'metros_cuadrados': float(lote.metros_cuadrados),
                'valor_total': float(lote.valor_total),
                'enganche': float(lote.enganche),
                'costo_instalacion': float(lote.costo_instalacion),
                'plazo_meses': lote.plazo_meses,
                'cuota_mensual': float(lote.cuota_mensual),
                'estado': lote.estado,
                'activo': lote.activo,
                'fecha_creacion': lote.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S'),
                'fecha_actualizacion': lote.fecha_actualizacion.strftime('%Y-%m-%d %H:%M:%S'),
            })
        
        # Crear DataFrame
        df = pd.DataFrame(datos_exportacion)
        
        # Generar archivo
        if datos_form['formato'] == 'xlsx':
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Lotes', index=False)
            output.seek(0)
            
            response = HttpResponse(
                output.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="lotes_exportados_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
            
        else:  # CSV
            output = BytesIO()
            df.to_csv(output, index=False, encoding='utf-8-sig')
            output.seek(0)
            
            response = HttpResponse(output.read(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="lotes_exportados_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        return response
    
    def changelist_view(self, request, extra_context=None):
        """Sobrescribir changelist para agregar botones de importación/exportación"""
        extra_context = extra_context or {}
        extra_context['show_import_export_buttons'] = True
        return super().changelist_view(request, extra_context)


@admin.register(HistorialLote)
class HistorialLoteAdmin(admin.ModelAdmin):
    list_display = ('lote', 'estado_anterior', 'estado_nuevo', 'cambiado_por', 'fecha_cambio')
    list_filter = ('estado_nuevo', 'fecha_cambio')
    search_fields = ('lote__numero_lote', 'lote__manzana__nombre', 'cambiado_por__username')
    ordering = ('-fecha_cambio',)
    readonly_fields = ('fecha_cambio',)
    
    def has_add_permission(self, request):
        return False  # No permitir crear registros manualmente
