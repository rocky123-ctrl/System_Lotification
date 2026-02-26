from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import Lote, Manzana
from decimal import Decimal
import pandas as pd
import io


class ImportarLotesForm(forms.Form):
    """Formulario para importar lotes desde Excel"""
    archivo_excel = forms.FileField(
        label='Archivo Excel (.xlsx)',
        help_text='Selecciona un archivo Excel con los datos de los lotes',
        widget=forms.FileInput(attrs={
            'accept': '.xlsx,.xls',
            'class': 'form-control'
        })
    )
    
    # Opciones de importación
    crear_manzanas = forms.BooleanField(
        label='Crear manzanas automáticamente',
        required=False,
        initial=True,
        help_text='Si está marcado, creará las manzanas que no existan'
    )
    
    sobrescribir_existentes = forms.BooleanField(
        label='Sobrescribir lotes existentes',
        required=False,
        initial=False,
        help_text='Si está marcado, actualizará lotes que ya existan (basado en manzana y número de lote)'
    )
    
    def clean_archivo_excel(self):
        """Validar el archivo Excel"""
        archivo = self.cleaned_data.get('archivo_excel')
        
        if not archivo:
            raise ValidationError('Debe seleccionar un archivo')
        
        # Verificar extensión
        if not archivo.name.endswith(('.xlsx', '.xls')):
            raise ValidationError('El archivo debe ser un Excel (.xlsx o .xls)')
        
        # Verificar tamaño (máximo 10MB)
        if archivo.size > 10 * 1024 * 1024:
            raise ValidationError('El archivo no puede ser mayor a 10MB')
        
        try:
            # Intentar leer el archivo
            df = pd.read_excel(archivo)
            
            # Verificar columnas requeridas
            columnas_requeridas = [
                'manzana', 'numero_lote', 'metros_cuadrados', 
                'valor_total'
            ]
            
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
            if columnas_faltantes:
                raise ValidationError(
                    f'El archivo debe contener las siguientes columnas: {", ".join(columnas_faltantes)}'
                )
            
            # Verificar que no esté vacío
            if df.empty:
                raise ValidationError('El archivo está vacío')
            
            # Verificar que tenga datos válidos
            if len(df) > 1000:
                raise ValidationError('El archivo no puede contener más de 1000 lotes')
            
            return archivo
            
        except Exception as e:
            raise ValidationError(f'Error al leer el archivo: {str(e)}')
    
    def procesar_archivo(self, request):
        """Procesar el archivo Excel e importar los lotes"""
        archivo = self.cleaned_data['archivo_excel']
        crear_manzanas = self.cleaned_data['crear_manzanas']
        sobrescribir_existentes = self.cleaned_data['sobrescribir_existentes']
        
        try:
            # Leer el archivo Excel
            df = pd.read_excel(archivo)
            
            # Contadores para el reporte
            lotes_creados = 0
            lotes_actualizados = 0
            lotes_omitidos = 0
            errores = []
            
            # Procesar cada fila
            for index, row in df.iterrows():
                try:
                    # Obtener o crear manzana
                    nombre_manzana = str(row['manzana']).strip()
                    manzana, manzana_creada = Manzana.objects.get_or_create(
                        nombre=nombre_manzana,
                        defaults={
                            'descripcion': f'Manzana {nombre_manzana}',
                            'activo': True
                        }
                    )
                    
                    # Buscar lote existente
                    numero_lote = str(row['numero_lote']).strip()
                    lote_existente = Lote.objects.filter(
                        manzana=manzana,
                        numero_lote=numero_lote
                    ).first()
                    
                    # Preparar datos del lote
                    datos_lote = {
                        'manzana': manzana,
                        'numero_lote': numero_lote,
                        'metros_cuadrados': Decimal(str(row['metros_cuadrados'])),
                        'valor_total': Decimal(str(row['valor_total'])),
                        'estado': 'disponible',
                        'activo': True
                    }
                    
                    # Agregar campos opcionales si existen
                    if 'costo_instalacion' in row and pd.notna(row['costo_instalacion']):
                        datos_lote['costo_instalacion'] = Decimal(str(row['costo_instalacion']))
                    
                    if 'estado' in row and pd.notna(row['estado']):
                        estado = str(row['estado']).strip().lower()
                        if estado in ['disponible', 'reservado', 'pagado', 'comercial_y_bodega', 'financiado', 'pagado_y_escriturado']:
                            datos_lote['estado'] = estado
                    
                    # Crear o actualizar lote
                    if lote_existente and sobrescribir_existentes:
                        # Actualizar lote existente
                        for campo, valor in datos_lote.items():
                            setattr(lote_existente, campo, valor)
                        lote_existente.save()
                        lotes_actualizados += 1
                        
                    elif lote_existente and not sobrescribir_existentes:
                        # Omitir lote existente
                        lotes_omitidos += 1
                        
                    else:
                        # Crear nuevo lote
                        Lote.objects.create(**datos_lote)
                        lotes_creados += 1
                        
                except Exception as e:
                    errores.append(f"Fila {index + 2}: {str(e)}")
                    continue
            
            # Mostrar mensajes de resultado
            if lotes_creados > 0:
                messages.success(
                    request, 
                    f'✅ Se crearon {lotes_creados} lotes exitosamente'
                )
            
            if lotes_actualizados > 0:
                messages.warning(
                    request, 
                    f'🔄 Se actualizaron {lotes_actualizados} lotes existentes'
                )
            
            if lotes_omitidos > 0:
                messages.info(
                    request, 
                    f'⏭️ Se omitieron {lotes_omitidos} lotes existentes (no sobrescribir)'
                )
            
            if errores:
                for error in errores[:10]:  # Mostrar solo los primeros 10 errores
                    messages.error(request, error)
                if len(errores) > 10:
                    messages.error(
                        request, 
                        f'... y {len(errores) - 10} errores más'
                    )
            
            return {
                'creados': lotes_creados,
                'actualizados': lotes_actualizados,
                'omitidos': lotes_omitidos,
                'errores': len(errores)
            }
            
        except Exception as e:
            messages.error(request, f'❌ Error al procesar el archivo: {str(e)}')
            return None


class ExportarLotesForm(forms.Form):
    """Formulario para exportar lotes a Excel"""
    formato = forms.ChoiceField(
        choices=[
            ('xlsx', 'Excel (.xlsx)'),
            ('csv', 'CSV (.csv)')
        ],
        initial='xlsx',
        label='Formato de exportación'
    )
    
    incluir_inactivos = forms.BooleanField(
        label='Incluir lotes inactivos',
        required=False,
        initial=False
    )
    
    solo_disponibles = forms.BooleanField(
        label='Solo lotes disponibles',
        required=False,
        initial=False
    )
