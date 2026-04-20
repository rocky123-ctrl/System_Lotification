from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
import math

from .models import Venta, LiquidacionComision, Cotizacion
from .serializers import VentaSerializer, LiquidacionComisionSerializer, CotizacionSerializer

from django.db.models import Sum, Q
from django.http import HttpResponse
from django.utils import timezone
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from rest_framework.pagination import PageNumberPagination
from dateutil.relativedelta import relativedelta

class VentasPagination(PageNumberPagination):
    page_size = 8
    page_size_query_param = 'page_size'
    max_page_size = 100

class VentaViewSet(viewsets.ModelViewSet):
    """
    ModelViewSet para procesar ventas de Lotes hechas por Clientes.
    Permite operaciones CRUD y expone un endpoint de cálculo avanzado.
    """
    queryset = Venta.objects.all()
    serializer_class = VentaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = VentasPagination

    def get_queryset(self):
        user = self.request.user
        all_sales = self.request.query_params.get('all') == 'true'
        
        # Un Superadmin puede ver todas las ventas si usa el parámetro 'all'
        is_super = user.is_superuser or (
            hasattr(user, 'user_roles') and 
            user.user_roles.filter(role__name='Superadmin', is_active=True).exists()
        )

        if is_super and all_sales:
            queryset = Venta.objects.all().select_related('cliente', 'lote', 'vendedor')
        else:
            # Usuarios normales solo ven sus ventas
            queryset = Venta.objects.filter(vendedor=user).select_related('cliente', 'lote', 'vendedor')

        # Filtros
        anio = self.request.query_params.get('anio')
        mes = self.request.query_params.get('mes')
        search = self.request.query_params.get('search')
        lotificacion = self.request.query_params.get('lotificacion')

        if anio:
            queryset = queryset.filter(fecha_creacion__year=anio)
        if mes:
            queryset = queryset.filter(fecha_creacion__month=mes)
        if lotificacion:
            queryset = queryset.filter(lote__manzana__lotificacion_id=lotificacion)
        if search:
            queryset = queryset.filter(
                Q(cliente__nombres__icontains=search) |
                Q(cliente__apellidos__icontains=search) |
                Q(lote__numero_lote__icontains=search)
            )

        return queryset.order_by('-fecha_creacion')

    def perform_create(self, serializer):
        # Asignar automáticamente el vendedor como el usuario activo
        serializer.save(vendedor=self.request.user)

    def perform_destroy(self, instance):
        """
        Al eliminar una venta, debemos devolver el lote a 'disponible'
        y limpiar cualquier financiamiento activo si existiera.
        """
        from django.db import transaction
        from lotes.models import HistorialLote
        from financiamiento.models import Financiamiento
        
        with transaction.atomic():
            lote = instance.lote
            estado_anterior = lote.estado_disponibilidad
            
            # 1. Liberar el lote
            lote.estado_disponibilidad = 'disponible'
            lote.save()
            
            # 2. Registrar en historial
            HistorialLote.objects.create(
                lote=lote,
                estado_disponibilidad_anterior=estado_anterior,
                estado_disponibilidad_nuevo='disponible',
                notas=f"Venta ID {instance.id} eliminada por {self.request.user.username}. Lote liberado."
            )
            
            # 3. Eliminar financiamiento si existe para este lote
            # (El modelo Financiamiento tiene OneToOne con Lote y on_delete=CASCADE lo borrará si borramos lote, 
            # pero aquí borramos la Venta, así que debemos borrar el Financiamiento manualmente)
            Financiamiento.objects.filter(lote=lote).delete()
            
            # 4. Eliminar la venta
            instance.delete()

    @action(detail=False, methods=['get'])
    def resumen(self, request):
        """
        Devuelve totales de ventas y comisiones para el usuario activo
        basado en los filtros aplicados.
        """
        queryset = self.filter_queryset(self.get_queryset())
        totales = queryset.aggregate(
            total_ventas=Sum('valor_lote'),
            total_comisiones=Sum('comision_monto')
        )
        return Response({
            'total_ventas': totales['total_ventas'] or 0,
            'total_comisiones': totales['total_comisiones'] or 0,
            'conteo': queryset.count()
        })

    @action(detail=False, methods=['post'])
    def calcular(self, request):
        """
        Calcula amortización y desglose financiero de una venta
        en tiempo real desde el Backend.
        """
        try:
            valor_lote = Decimal(str(request.data.get('valor_lote', 0)))
            enganche = Decimal(str(request.data.get('enganche', 0)))
            descuento = Decimal(str(request.data.get('descuento', 0)))
            tipo_pago = str(request.data.get('tipo_pago', 'contado')).lower()
            plazo_meses = int(request.data.get('plazo_meses', 0))
            tasa_interes = float(request.data.get('tasa_interes', 0))

            valor_con_descuento = max(Decimal('0'), valor_lote - descuento)
            valor_financiar = max(Decimal('0'), valor_con_descuento - enganche)

            # Tasa Efectiva Mensual = (1 + Tasa Anual Decimal)^(1/12) - 1
            tasa_anual_decimal = tasa_interes / 100.0
            tasa_mensual_efectiva = math.pow(1 + tasa_anual_decimal, 1 / 12) - 1
            tasa_mensual_efectiva_porcentaje = tasa_mensual_efectiva * 100

            cuota_final = 0.0

            if tipo_pago == 'financiado' and plazo_meses > 0 and float(valor_financiar) > 0:
                vf_float = float(valor_financiar)
                if tasa_mensual_efectiva > 0:
                    numerador = vf_float * tasa_mensual_efectiva * math.pow(1 + tasa_mensual_efectiva, plazo_meses)
                    denominador = math.pow(1 + tasa_mensual_efectiva, plazo_meses) - 1
                    cuota_final = numerador / denominador
                else:
                    cuota_final = vf_float / plazo_meses

            total_pagar_hoy = float(enganche + valor_financiar) if tipo_pago == 'contado' else float(enganche)

            return Response({
                'valor_lote': float(valor_lote),
                'valor_con_descuento': float(valor_con_descuento),
                'valor_financiar': float(valor_financiar),
                'tasa_anual': tasa_interes,
                'tasa_mensual_efectiva_porcentaje': tasa_mensual_efectiva_porcentaje,
                'plazo_meses': plazo_meses,
                'cuota_final_mensual': cuota_final,
                'total_pagar_hoy': total_pagar_hoy
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class LiquidacionComisionViewSet(viewsets.ModelViewSet):
    queryset = LiquidacionComision.objects.all()
    serializer_class = LiquidacionComisionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = LiquidacionComision.objects.select_related('venta', 'vendedor', 'vendedor__empleado', 'venta__lote')
        
        # Filtros
        anio = self.request.query_params.get('anio')
        mes = self.request.query_params.get('mes')
        search = self.request.query_params.get('search')
        estado = self.request.query_params.get('estado')

        if anio:
            queryset = queryset.filter(venta__fecha_creacion__year=anio)
        if mes:
            queryset = queryset.filter(venta__fecha_creacion__month=mes)
        if estado:
            queryset = queryset.filter(estado_pago=estado)
        if search:
            queryset = queryset.filter(
                Q(vendedor__first_name__icontains=search) |
                Q(vendedor__last_name__icontains=search) |
                Q(vendedor__username__icontains=search) |
                Q(vendedor__empleado__nombre__icontains=search) |
                Q(vendedor__empleado__apellido__icontains=search)
            )

        return queryset.order_by('-fecha_creacion')

    @action(detail=True, methods=['post'])
    def pagar_ahora(self, request, pk=None):
        instance = self.get_object()
        if instance.estado_pago == 'PAGADO':
            return Response({'error': 'Esta liquidación ya ha sido pagada.'}, status=status.HTTP_400_BAD_REQUEST)
        
        referencia = request.data.get('referencia_pago')
        
        instance.estado_pago = 'PAGADO'
        instance.fecha_pago = timezone.now().date()
        instance.es_pago_inmediato = True
        instance.referencia_pago = referencia
        instance.save()
        
        return Response(self.get_serializer(instance).data)

    @action(detail=False, methods=['get'])
    def exportar_excel(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Liquidaciones"

        # Encabezados
        headers = ["Vendedor", "Folio Venta", "Valor Lote", "Monto Comisión", "Fecha Venta", "Fecha Pago Real", "Estado"]
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num, value=header)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')

        # Datos
        for row_num, liq in enumerate(queryset, 2):
            vendedor = liq.vendedor_nombre if hasattr(liq, 'vendedor_nombre') else liq.vendedor.username
            if not vendedor: # Si falla el SerializerMethodField en crudo
                 vendedor = f"{liq.vendedor.first_name} {liq.vendedor.last_name}".strip() or liq.vendedor.username

            ws.cell(row=row_num, column=1, value=vendedor)
            ws.cell(row=row_num, column=2, value=f"V-{liq.venta.id}")
            ws.cell(row=row_num, column=3, value=float(liq.venta.valor_lote))
            ws.cell(row=row_num, column=4, value=float(liq.monto_pagado))
            ws.cell(row=row_num, column=5, value=liq.venta.fecha_creacion.strftime('%Y-%m-%d'))
            ws.cell(row=row_num, column=6, value=liq.fecha_pago.strftime('%Y-%m-%d') if liq.fecha_pago else "PENDIENTE")
            ws.cell(row=row_num, column=7, value=liq.estado_pago)

        # Ajustar ancho de columnas
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column].width = adjusted_width

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=planillas_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        wb.save(response)
        return response

class CotizacionesPagination(PageNumberPagination):
    page_size = 8
    page_size_query_param = 'page_size'
    max_page_size = 100

class CotizacionViewSet(viewsets.ModelViewSet):
    queryset = Cotizacion.objects.all()
    serializer_class = CotizacionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CotizacionesPagination

    def get_queryset(self):
        user = self.request.user
        all_cotizaciones = self.request.query_params.get('all') == 'true'
        
        is_super = user.is_superuser or (
            hasattr(user, 'user_roles') and 
            user.user_roles.filter(role__name='Superadmin', is_active=True).exists()
        )

        if is_super and all_cotizaciones:
            queryset = Cotizacion.objects.all().select_related('cliente', 'lote', 'vendedor')
        else:
            queryset = Cotizacion.objects.filter(vendedor=user).select_related('cliente', 'lote', 'vendedor')

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(cliente__nombres__icontains=search) |
                Q(cliente__apellidos__icontains=search) |
                Q(nombre_prospecto__icontains=search) |
                Q(lote__numero_lote__icontains=search)
            )

        return queryset.order_by('-fecha_creacion')

    def perform_create(self, serializer):
        serializer.save(vendedor=self.request.user)

    @action(detail=True, methods=['post'])
    def convertir_a_venta(self, request, pk=None):
        cotizacion = self.get_object()

        if cotizacion.fecha_vencimiento < timezone.now().date():
            return Response({'error': 'La cotización ha vencido.'}, status=status.HTTP_400_BAD_REQUEST)

        if not cotizacion.cliente:
            return Response({'error': 'La cotización no tiene un cliente asociado para crear la venta. Asigne un cliente primero.'}, status=status.HTTP_400_BAD_REQUEST)

        # Usar transacciones atómicas para cambiar estado
        from django.db import transaction
        with transaction.atomic():
            # Verificamos lote y solicitamos bloqueo (si el user cambia concurrentemente, se evita conflicto, aunque simple fetch works for now)
            if cotizacion.lote.estado_disponibilidad != 'disponible':
                return Response({'error': f'El lote {cotizacion.lote.numero_lote} ya no está disponible.'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                nueva_venta = Venta(
                    cliente=cotizacion.cliente,
                    lote=cotizacion.lote,
                    valor_lote=cotizacion.valor_lote,
                    enganche=cotizacion.enganche,
                    descuento=cotizacion.descuento,
                    monto_financiar=cotizacion.monto_financiar,
                    tasa_interes_anual=cotizacion.tasa_interes_anual,
                    total_pagar_contado=cotizacion.total_pagar_contado,
                    tipo_pago=cotizacion.tipo_pago,
                    forma_pago=cotizacion.forma_pago,
                    acepta_instalacion=cotizacion.acepta_instalacion,
                    plazo_meses=cotizacion.plazo_meses,
                    vendedor=cotizacion.vendedor
                )
                nueva_venta.save()
                return Response({'mensaje': 'Venta creada exitosamente', 'venta_id': nueva_venta.id}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def exportar_excel(self, request, pk=None):
        cotizacion = self.get_object()
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"Cotizacion_{cotizacion.id}"

        # Estilos
        title_font = Font(bold=True, size=14)
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
        border_side = Side(style='thin')
        border = Border(left=border_side, right=border_side, top=border_side, bottom=border_side)

        # Encabezado General
        ws.merge_cells('A1:E1')
        ws['A1'] = "COTIZACIÓN DE LOTE"
        ws['A1'].font = title_font
        ws['A1'].alignment = Alignment(horizontal='center')

        # Información del Cliente y Vencimiento
        ws['A3'] = "Cliente/Prospecto:"
        ws['B3'] = f"{cotizacion.cliente.nombres} {cotizacion.cliente.apellidos}" if cotizacion.cliente else (cotizacion.nombre_prospecto or "Prospecto")
        ws['A4'] = "Teléfono:"
        ws['B4'] = (cotizacion.cliente.telefono if cotizacion.cliente else cotizacion.telefono_prospecto) or "N/A"
        ws['A5'] = "Fecha Vencimiento:"
        ws['B5'] = cotizacion.fecha_vencimiento.strftime('%d/%m/%Y')
        ws['A6'] = "Vendedor:"
        ws['B6'] = f"{cotizacion.vendedor.get_full_name() or cotizacion.vendedor.username}"

        # Información del Lote
        ws['D3'] = "Lote:"
        ws['E3'] = cotizacion.lote.numero_lote
        ws['D4'] = "Manzana:"
        ws['E4'] = cotizacion.lote.manzana.nombre
        ws['D5'] = "Área:"
        ws['E5'] = f"{cotizacion.lote.metros_cuadrados} m²"
        ws['D6'] = "Proyecto:"
        ws['E6'] = cotizacion.lote.manzana.lotificacion.nombre

        # Detalles Financieros
        ws['A8'] = "DETALLES FINANCIEROS"
        ws['A8'].font = Font(bold=True)
        
        ws['A9'] = "Valor del Lote:"
        ws['B9'] = float(cotizacion.valor_lote)
        ws['B9'].number_format = '\"Q\" #,##0.00'
        ws['A10'] = "Enganche:"
        ws['B10'] = float(cotizacion.enganche)
        ws['B10'].number_format = '\"Q\" #,##0.00'
        ws['A11'] = "Descuento:"
        ws['B11'] = float(cotizacion.descuento)
        ws['B11'].number_format = '\"Q\" #,##0.00'
        ws['A12'] = "Monto a Financiar:"
        ws['B12'] = float(cotizacion.monto_financiar or 0)
        ws['B12'].number_format = '\"Q\" #,##0.00'
        
        ws['D9'] = "Tipo de Pago:"
        ws['E9'] = cotizacion.tipo_pago
        ws['D10'] = "Forma de Pago:"
        ws['E10'] = cotizacion.forma_pago
        ws['D11'] = "Plazo (Meses):"
        ws['E11'] = cotizacion.plazo_meses
        ws['D12'] = "Tasa Interés Anual:"
        ws['E12'] = f"{cotizacion.tasa_interes_anual}%"

        # Cálculos de Interés Mensual y Cuota
        tasa_anual_decimal = float(cotizacion.tasa_interes_anual) / 100.0
        tasa_mensual_efectiva = math.pow(1 + tasa_anual_decimal, 1 / 12) - 1
        
        ws['D13'] = "Tasa Mensual EF.:"
        ws['E13'] = f"{round(tasa_mensual_efectiva * 100, 4)}%"

        # Amortización si es Financiado
        if cotizacion.tipo_pago == 'FINANCIADO' and cotizacion.plazo_meses > 0:
            row = 16
            ws.merge_cells(f'A{row}:F{row}')
            ws[f'A{row}'] = "TABLA DE AMORTIZACIÓN ESTIMADA"
            ws[f'A{row}'].font = Font(bold=True)
            ws[f'A{row}'].alignment = Alignment(horizontal='center')
            
            row += 1
            headers = ["No.", "Fecha Est.", "Interés", "Capital", "Total Cuota", "Saldo"]
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=row, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center')
                cell.border = border
            
            row += 1
            saldo_insoluto = float(cotizacion.monto_financiar)
            fecha_vencimiento = timezone.now().date() + relativedelta(months=1)
            
            # Calcular cuota nivelada
            if tasa_mensual_efectiva > 0:
                numerador = saldo_insoluto * tasa_mensual_efectiva * math.pow(1 + tasa_mensual_efectiva, cotizacion.plazo_meses)
                denominador = math.pow(1 + tasa_mensual_efectiva, cotizacion.plazo_meses) - 1
                cuota_mensual = numerador / denominador
            else:
                cuota_mensual = saldo_insoluto / cotizacion.plazo_meses

            for i in range(1, cotizacion.plazo_meses + 1):
                interes_cuota = saldo_insoluto * tasa_mensual_efectiva
                capital_cuota = cuota_mensual - interes_cuota
                
                if i == cotizacion.plazo_meses:
                    capital_cuota = saldo_insoluto
                    cuota_mensual = capital_cuota + interes_cuota
                
                saldo_insoluto -= capital_cuota
                
                ws.cell(row=row, column=1, value=i).border = border
                ws.cell(row=row, column=2, value=fecha_vencimiento.strftime('%d/%m/%Y')).border = border
                
                c_interes = ws.cell(row=row, column=3, value=round(interes_cuota, 2))
                c_interes.number_format = '\"Q\" #,##0.00'
                c_interes.border = border
                
                c_capital = ws.cell(row=row, column=4, value=round(capital_cuota, 2))
                c_capital.number_format = '\"Q\" #,##0.00'
                c_capital.border = border
                
                c_total = ws.cell(row=row, column=5, value=round(cuota_mensual, 2))
                c_total.number_format = '\"Q\" #,##0.00'
                c_total.border = border
                
                c_saldo = ws.cell(row=row, column=6, value=max(0, round(saldo_insoluto, 2)))
                c_saldo.number_format = '\"Q\" #,##0.00'
                c_saldo.border = border
                
                fecha_vencimiento += relativedelta(months=1)
                row += 1

        # Ajustar columnas
        for col in ws.columns:
            max_length = 0
            # Usar el índice de columna y convertirlo a letra para evitar errores con MergedCells
            column_letter = get_column_letter(col[0].column)
            for cell in col:
                try:
                    if cell.value and len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except: pass
            ws.column_dimensions[column_letter].width = max_length + 5

        user_filename = request.query_params.get('filename', f"cotizacion_{cotizacion.id}")
        if not user_filename.endswith('.xlsx'):
            user_filename += '.xlsx'

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{user_filename}"'
        wb.save(response)
        return response
