from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Cliente
from .serializers import ClienteSerializer

class ClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para realizar operaciones CRUD completas en la tabla Cliente.
    """
    # Select related porque necesitamos consultar las FKs
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Campos que el usuario puede usar para buscar
    search_fields = ['nombres', 'apellidos', 'email']
    # Permitir ordenamiento por fecha y estado
    ordering_fields = ['fechaRegistro', 'estado', 'nombres']
    # Filtros exactos si es necesario
    filterset_fields = ['estado']

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Endpoint custom /api/clientes/stats/
        Requerido por el frontend en getClientesStats()
        """
        total = self.queryset.count()
        activos = self.queryset.filter(estado='activo').count()
        inactivos = self.queryset.filter(estado='inactivo').count()

        return Response({
            "activos": activos,
            "inactivos": inactivos,
            "total": total
        })

    def destroy(self, request, *args, **kwargs):
        if not (request.user.is_superuser or hasattr(request.user, 'user_roles') and request.user.user_roles.filter(role__name__in=['Superadmin', 'Administrador'], is_active=True).exists()):
            return Response({"detail": "No tienes permiso para eliminar clientes."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['post'], url_path='registrar')
    def registrar(self, request):
        """
        El frontend hace POST a /clientes/registrar/ en lugar de /clientes/ 
        para crear un cliente nuevo. 
        Manejamos este action para empatar con esa llamada.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['delete'])
    def force_delete(self, request, pk=None):
        """
        Elimina físicamente a un cliente y todos sus registros asociados
        (Ventas, Cotizaciones, Servicios, Pagos).
        Libera los lotes asociados dejándolos en estado 'disponible'.
        """
        if not (request.user.is_superuser or hasattr(request.user, 'user_roles') and request.user.user_roles.filter(role__name__in=['Superadmin', 'Administrador'], is_active=True).exists()):
            return Response({"detail": "No tienes permiso para forzar la eliminación de clientes."}, status=status.HTTP_403_FORBIDDEN)
            
        cliente = self.get_object()
        from django.db import transaction
        from ventas.models import Venta, Cotizacion
        from servicios.models import BilleteraServicio, ConfiguracionServicioLote, PagoServicio
        from financiamiento.models import Financiamiento
        from lotes.models import HistorialLote
        import logging

        logger = logging.getLogger(__name__)

        try:
            with transaction.atomic():
                # 1. Obtener todas las ventas del cliente
                ventas = Venta.objects.filter(cliente=cliente)
                
                for venta in ventas:
                    lote = venta.lote
                    
                    # A. Eliminar Configuraciones de Servicios y Pagos de Servicios para el Lote
                    # (Como el lote se libera, se limpia su historial de servicios contratados)
                    ConfiguracionServicioLote.objects.filter(lote=lote).delete()
                    PagoServicio.objects.filter(lote=lote).delete()

                    # B. Eliminar Financiamiento si existe
                    Financiamiento.objects.filter(lote=lote).delete()

                    # C. Liberar el lote y registrar historial
                    estado_anterior = lote.estado_disponibilidad
                    lote.estado_disponibilidad = 'disponible'
                    lote.save()

                    HistorialLote.objects.create(
                        lote=lote,
                        estado_disponibilidad_anterior=estado_anterior,
                        estado_disponibilidad_nuevo='disponible',
                        notas=f"Lote liberado por eliminación forzada del cliente {cliente.nombres} {cliente.apellidos}"
                    )
                
                # 2. Eliminar Billetera de Servicios del Cliente (si existe)
                BilleteraServicio.objects.filter(cliente=cliente).delete()

                # 3. Eliminar Ventas 
                # ( CASCADE eliminará: ventas_cuota, ventas_pago, ventas_historialcambios )
                ventas.delete()

                # 4. Eliminar Cotizaciones
                Cotizacion.objects.filter(cliente=cliente).delete()

                # 5. Eliminar Cliente físicamente
                cliente.delete()

            return Response({"detail": "Cliente y registros eliminados. Lotes liberados exitosamente."}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error en force_delete para cliente {pk}: {str(e)}")
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
