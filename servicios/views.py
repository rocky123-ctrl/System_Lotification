from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.utils import timezone
from datetime import datetime, date
import calendar

from .models import ServicioCatalogo, BilleteraServicio, ConfiguracionServicioLote, PagoServicio
from .serializers import (
    ServicioCatalogoSerializer, 
    BilleteraServicioSerializer, 
    ConfiguracionServicioLoteSerializer, 
    PagoServicioSerializer
)
from ventas.models import Venta

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ServicioCatalogoViewSet(viewsets.ModelViewSet):
    queryset = ServicioCatalogo.objects.all()
    serializer_class = ServicioCatalogoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['lotificacion_id', 'activo']


class BilleteraServicioViewSet(viewsets.ModelViewSet):
    queryset = BilleteraServicio.objects.all()
    serializer_class = BilleteraServicioSerializer

    def destroy(self, request, *args, **kwargs):
        billetera = self.get_object()
        cliente = billetera.cliente
        
        # Encontrar los lotes del cliente
        from ventas.models import Venta
        from lotes.models import Lote
        lotes_cliente = Lote.objects.filter(ventas__cliente=cliente)

        with transaction.atomic():
            # Eliminar en cascada las configuraciones y pagos
            ConfiguracionServicioLote.objects.filter(lote__in=lotes_cliente).delete()
            PagoServicio.objects.filter(lote__in=lotes_cliente).delete()
            # Eliminar la billetera misma
            billetera.delete()
            
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def lots_status(self, request, pk=None):
        """
        Devuelve todos los lotes asociados al cliente con sus respectivos estados de cuenta de servicios.
        """
        billetera = self.get_object()
        cliente = billetera.cliente
        
        # Obtener ventas (lotes) del cliente con estados específicos
        ventas = Venta.objects.filter(
            cliente=cliente,
            lote__estado_disponibilidad__in=['financiado', 'pagado', 'escriturado']
        ).select_related('lote', 'lote__manzana', 'lote__manzana__lotificacion')
        
        data = []
        for venta in ventas:
            lote = venta.lote
            # Obtener configuraciones de servicios para este lote
            configuraciones_all = ConfiguracionServicioLote.objects.filter(lote=lote)
            servicios_activos = [c for c in configuraciones_all if c.esta_activo]
            
            # Obtener resumen de cobros pendientes y vencidos
            cobros_activos = PagoServicio.objects.filter(lote=lote).exclude(estado='Pagado')
            saldo_pendiente = sum(p.monto_cobrado - p.monto_pagado for p in cobros_activos)
            
            data.append({
                'lote_id': lote.id,
                'numero_lote': lote.numero_lote,
                'manzana': lote.manzana.nombre,
                'lotificacion': lote.manzana.lotificacion.nombre,
                'lotificacion_id': lote.manzana.lotificacion.id,
                'estado_lote': lote.estado_disponibilidad,
                'servicios_activos': ConfiguracionServicioLoteSerializer(servicios_activos, many=True).data,
                'configuraciones': ConfiguracionServicioLoteSerializer(configuraciones_all, many=True).data,
                'saldo_pendiente': float(saldo_pendiente),
                'count_pendientes': cobros_activos.count()
            })
            
        return Response(data)


class ConfiguracionServicioLoteViewSet(viewsets.ModelViewSet):
    queryset = ConfiguracionServicioLote.objects.all()
    serializer_class = ConfiguracionServicioLoteSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['lote_id', 'servicio_id', 'esta_activo']

    def perform_create(self, serializer):
        config = serializer.save()
        self._generar_pago_inicial(config)

    def perform_update(self, serializer):
        config = serializer.save()
        if config.esta_activo:
            self._generar_pago_inicial(config)
        else:
            # Requerimiento: Si se desactiva el servicio, quitar cobros pendientes (no vencidos)
            PagoServicio.objects.filter(
                lote=config.lote,
                servicio=config.servicio,
                estado='Pendiente'
            ).delete()

    def _generar_pago_inicial(self, config):
        """Genera un registro de pago pendiente para el mes actual si no existe."""
        if not config.esta_activo:
            return

        today = date.today()
        # Primer día del mes actual para el periodo
        periodo = today.replace(day=1)
        
        # Verificar si ya existe un pago para este lote, servicio y periodo
        exists = PagoServicio.objects.filter(
            lote=config.lote,
            servicio=config.servicio,
            mes_periodo=periodo
        ).exists()

        if not exists:
            # Calcular fin de mes para fecha límite
            last_day = calendar.monthrange(today.year, today.month)[1]
            fecha_limite = today.replace(day=last_day)
            
            PagoServicio.objects.create(
                lote=config.lote,
                servicio=config.servicio,
                mes_periodo=periodo,
                monto_cobrado=config.precio_personalizado or config.servicio.precio_base_defecto,
                fecha_limite=fecha_limite,
                estado='Pendiente'
            )


class PagoServicioViewSet(viewsets.ModelViewSet):
    queryset = PagoServicio.objects.all()
    serializer_class = PagoServicioSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['lote_id', 'servicio_id', 'estado', 'mes_periodo']

    def get_queryset(self):
        queryset = super().get_queryset()
        exclude_estado = self.request.query_params.get('exclude_estado', None)
        if exclude_estado:
            estados = [e.strip() for e in exclude_estado.split(',')]
            queryset = queryset.exclude(estado__in=estados)
        return queryset

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Si se está intentando pagar
        nuevo_estado = request.data.get('estado')
        if nuevo_estado == 'Pagado' and instance.estado != 'Pagado':
            monto_pagar = float(request.data.get('monto_pagado', 0))
            monto_cobrado = float(instance.monto_cobrado)
            mora = float(request.data.get('mora_aplicada', 0))
            
            total_esperado = monto_cobrado + mora
            
            if abs(monto_pagar - total_esperado) > 0.01:
                return Response(
                    {"detail": f"El monto pagado (Q{monto_pagar:.2f}) debe ser exactamente igual al total cobrado más mora (Q{total_esperado:.2f})."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Si pasa la validación, setear fecha de pago
            request.data['fecha_pago_realizado'] = timezone.now().isoformat()

        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def recibo(self, request, pk=None):
        """Genera un comprobante de pago de servicio en PDF."""
        from .utils import generar_pdf_recibo_servicio
        from django.http import FileResponse
        
        pago = self.get_object()
        if pago.estado != 'Pagado':
            return Response(
                {"error": "Solo se puede generar recibo para pagos completados."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        buffer = generar_pdf_recibo_servicio(pago)
        filename = f"Recibo_Servicio_{pago.lote.numero_lote}_{pago.servicio.nombre}_{pago.mes_periodo}.pdf"
        
        return FileResponse(buffer, as_attachment=False, filename=filename, content_type='application/pdf')
