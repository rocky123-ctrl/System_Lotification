from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Empleado
from .serializers import EmpleadoSerializer

from rest_framework.pagination import PageNumberPagination

class EmpleadoPagination(PageNumberPagination):
    page_size = 8
    page_size_query_param = 'page_size'
    max_page_size = 100

class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.all()
    serializer_class = EmpleadoSerializer
    pagination_class = EmpleadoPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    search_fields = ['nombre', 'apellido', 'correo', 'dpi']
    ordering_fields = ['fecha_creacion', 'estado', 'nombre']
    filterset_fields = ['estado', 'rol']

    def get_queryset(self):
        # Filtrar por rol y excluir superusuarios. Usar select_related para optimizar.
        return Empleado.objects.select_related('usuario').filter(
            rol__in=['Administrador', 'Vendedor']
        ).exclude(
            usuario__is_superuser=True
        )

    def perform_destroy(self, instance):
        user = instance.usuario
        instance.delete()
        if user:
            user.delete()
