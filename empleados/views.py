from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Empleado
from .serializers import EmpleadoSerializer

class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.all()
    serializer_class = EmpleadoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    search_fields = ['nombre', 'apellido', 'correo', 'dpi']
    ordering_fields = ['fecha_creacion', 'estado', 'nombre']
    filterset_fields = ['estado', 'rol']

    def perform_destroy(self, instance):
        user = instance.usuario
        instance.delete()
        if user:
            user.delete()
