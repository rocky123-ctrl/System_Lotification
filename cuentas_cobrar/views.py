from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Cuota, Pago, BitacoraCambio
from .serializers import CuotaSerializer, PagoSerializer, BitacoraCambioSerializer

class CuotaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para listar y gestionar cuotas.
    Permite filtrar por cliente_id para ver las deudas de un cliente específico.
    """
    queryset = Cuota.objects.all().select_related('venta', 'venta__cliente', 'venta__lote')
    serializer_class = CuotaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        cliente_id = self.request.query_params.get('cliente_id')
        venta_id = self.request.query_params.get('venta_id')
        
        if cliente_id:
            queryset = queryset.filter(venta__cliente_id=cliente_id)
        
        if venta_id:
            queryset = queryset.filter(venta_id=venta_id)
            
        return queryset.order_by('no_cuota')

class PagoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para registrar pagos de cuotas.
    Asigna automáticamente el usuario (Admin) que realiza la transacción.
    """
    queryset = Pago.objects.all()
    serializer_class = PagoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Asignar el usuario logueado como el admin que registra el cobro
        serializer.save(usuario=self.request.user)

class BitacoraCambioViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Historial de cambios auditoría de las ventas y sus cuotas.
    """
    queryset = BitacoraCambio.objects.all()
    serializer_class = BitacoraCambioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        venta_id = self.request.query_params.get('venta_id')
        if venta_id:
            queryset = queryset.filter(venta_id=venta_id)
        return queryset.order_by('-fecha')
