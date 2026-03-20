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
