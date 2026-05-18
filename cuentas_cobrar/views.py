from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db import transaction
from django.utils import timezone
from .models import Cuota, Pago, BitacoraCambio
from .serializers import CuotaSerializer, PagoSerializer, BitacoraCambioSerializer

from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class CuotaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para listar y gestionar cuotas.
    Permite filtrar por cliente_id para ver las deudas de un cliente específico.
    """
    queryset = Cuota.objects.all().select_related('venta', 'venta__cliente', 'venta__lote')
    serializer_class = CuotaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        cliente_id = self.request.query_params.get('cliente_id')
        venta_id = self.request.query_params.get('venta_id')
        
        if cliente_id:
            queryset = queryset.filter(venta__cliente_id=cliente_id)
        
        if venta_id:
            queryset = queryset.filter(venta_id=venta_id)
            
        anio = self.request.query_params.get('anio')
        mes = self.request.query_params.get('mes')
        
        if anio and anio != 'all':
            queryset = queryset.filter(fecha_programada__year=anio)
        if mes and mes != 'all':
            queryset = queryset.filter(fecha_programada__month=mes)
            
        return queryset.order_by('no_cuota')

    @action(detail=True, methods=['get'])
    def recibo(self, request, pk=None):
        """
        Genera un comprobante de pago en PDF (tamaño media carta).
        """
        from .utils import generar_pdf_recibo
        from django.http import FileResponse
        
        cuota = self.get_object()
        # Obtener el último pago activo para esta cuota
        pago = cuota.pagos_registrados.filter(activo=True).last()
        
        if not pago:
            return Response(
                {"error": "No se encontró un pago activo para esta cuota. No se puede generar el recibo."}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        buffer = generar_pdf_recibo(cuota, pago)
        filename = f"Recibo_Lote_{cuota.venta.lote.numero_lote}_Cuota_{cuota.no_cuota}.pdf"
        
        return FileResponse(buffer, as_attachment=False, filename=filename, content_type='application/pdf')

class PagoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para registrar pagos de cuotas.
    Asigna automáticamente el usuario que realiza la transacción.
    """
    queryset = Pago.objects.all()
    serializer_class = PagoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        with transaction.atomic():
            pago = serializer.save(usuario=self.request.user)
            # Registrar en bitácora
            BitacoraCambio.objects.create(
                venta=pago.cuota.venta,
                descripcion=f"Pago registrado para la cuota {pago.cuota.no_cuota}. Monto Base: Q{pago.monto_base}. Mora: Q{pago.monto_mora}.",
                usuario=self.request.user
            )

    @action(detail=True, methods=['post'])
    def anular(self, request, pk=None):
        """
        Anula un pago (Soft Delete) y revierte el estado de la cuota.
        """
        pago = self.get_object()
        if not pago.activo:
            return Response({"error": "El pago ya se encuentra anulado."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            pago.activo = False
            pago.save()

            cuota = pago.cuota
            
            # Revertir estado de la cuota
            # Si hoy es mayor a la fecha programada, es Vencido, sino Pendiente
            if cuota.fecha_programada < timezone.now().date():
                cuota.estado = 'Vencido'
            else:
                cuota.estado = 'Pendiente'
            cuota.save()

            # Registrar en la bitácora
            motivo = request.data.get('motivo', 'Anulación de pago por error.')
            BitacoraCambio.objects.create(
                venta=cuota.venta,
                descripcion=f"Pago de la cuota {cuota.no_cuota} ANULADO. Motivo: {motivo}.",
                usuario=self.request.user
            )

            # Recalcular totales en la venta
            cuota.venta.actualizar_totales()

        return Response({"mensaje": "Pago anulado correctamente.", "cuota_estado": cuota.estado})

class BitacoraCambioViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Historial de cambios auditoría de las ventas y sus cuotas.
    """
    queryset = BitacoraCambio.objects.all()
    serializer_class = BitacoraCambioSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        venta_id = self.request.query_params.get('venta_id')
        if venta_id:
            queryset = queryset.filter(venta_id=venta_id)
            
        anio = self.request.query_params.get('anio')
        mes = self.request.query_params.get('mes')
        
        if anio and anio != 'all':
            queryset = queryset.filter(fecha__year=anio)
        if mes and mes != 'all':
            queryset = queryset.filter(fecha__month=mes)
            
        return queryset.order_by('-fecha')
