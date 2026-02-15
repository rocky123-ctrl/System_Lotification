from rest_framework import status, generics, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from decimal import Decimal
from .models import Manzana, Lote, HistorialLote
from .serializers import (
    ManzanaSerializer, LoteSerializer, LoteListSerializer, LoteCreateSerializer,
    LoteUpdateSerializer, HistorialLoteSerializer, LoteEstadisticasSerializer,
    LoteFiltroSerializer
)


class ManzanaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de manzanas"""
    queryset = Manzana.objects.filter(activo=True)
    serializer_class = ManzanaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Manzana.objects.filter(activo=True)
        nombre = self.request.query_params.get('nombre', None)
        if nombre:
            queryset = queryset.filter(nombre__icontains=nombre)
        return queryset.order_by('nombre')

    @action(detail=True, methods=['get'])
    def lotes(self, request, pk=None):
        """Obtener lotes de una manzana específica"""
        manzana = self.get_object()
        lotes = manzana.lotes.filter(activo=True)
        serializer = LoteListSerializer(lotes, many=True)
        return Response(serializer.data)


class LoteViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de lotes"""
    queryset = Lote.objects.filter(activo=True)
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return LoteCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return LoteUpdateSerializer
        elif self.action == 'list':
            return LoteListSerializer
        return LoteSerializer

    def get_queryset(self):
        queryset = Lote.objects.filter(activo=True)
        
        # Filtros
        manzana = self.request.query_params.get('manzana', None)
        estado = self.request.query_params.get('estado', None)
        precio_min = self.request.query_params.get('precio_min', None)
        precio_max = self.request.query_params.get('precio_max', None)
        metros_min = self.request.query_params.get('metros_min', None)
        metros_max = self.request.query_params.get('metros_max', None)
        solo_disponibles = self.request.query_params.get('solo_disponibles', None)
        
        if manzana:
            queryset = queryset.filter(manzana__nombre__icontains=manzana)
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        if precio_min:
            queryset = queryset.filter(valor_total__gte=precio_min)
        
        if precio_max:
            queryset = queryset.filter(valor_total__lte=precio_max)
        
        if metros_min:
            queryset = queryset.filter(metros_cuadrados__gte=metros_min)
        
        if metros_max:
            queryset = queryset.filter(metros_cuadrados__lte=metros_max)
        
        if solo_disponibles:
            queryset = queryset.filter(estado='disponible')
        
        return queryset.order_by('manzana', 'numero_lote')

    def perform_update(self, serializer):
        """Registrar cambio de estado en el historial"""
        instance = serializer.instance
        old_status = instance.estado
        new_status = serializer.validated_data.get('estado', old_status)
        
        # Guardar el lote
        lote = serializer.save()
        
        # Registrar cambio de estado si cambió
        if old_status != new_status:
            HistorialLote.objects.create(
                lote=lote,
                estado_anterior=old_status,
                estado_nuevo=new_status,
                cambiado_por=self.request.user,
                notas=f"Estado cambiado de {old_status} a {new_status}"
            )
        
        return lote

    @action(detail=True, methods=['get'])
    def historial(self, request, pk=None):
        """Obtener historial de un lote"""
        lote = self.get_object()
        historial = lote.historial.all()
        serializer = HistorialLoteSerializer(historial, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        """Cambiar estado de un lote con notas"""
        lote = self.get_object()
        nuevo_estado = request.data.get('estado')
        notas = request.data.get('notas', '')
        
        if not nuevo_estado:
            return Response(
                {'error': 'El campo estado es requerido'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if nuevo_estado not in dict(Lote.ESTADO_CHOICES):
            return Response(
                {'error': 'Estado no válido'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        estado_anterior = lote.estado
        lote.estado = nuevo_estado
        lote.save()
        
        # Registrar en historial
        HistorialLote.objects.create(
            lote=lote,
            estado_anterior=estado_anterior,
            estado_nuevo=nuevo_estado,
            cambiado_por=request.user,
            notas=notas
        )
        
        serializer = LoteSerializer(lote)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def disponibles(self, request):
        """Obtener solo lotes disponibles"""
        lotes = self.get_queryset().filter(estado='disponible')
        serializer = LoteListSerializer(lotes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Obtener estadísticas de lotes"""
        lotes = Lote.objects.filter(activo=True)
        
        stats = {
            'total_lotes': lotes.count(),
            'lotes_disponibles': lotes.filter(estado='disponible').count(),
            'lotes_reservados': lotes.filter(estado='reservado').count(),
            'lotes_vendidos': lotes.filter(estado='vendido').count(),
            'lotes_en_proceso': lotes.filter(estado='en_proceso').count(),
            'lotes_cancelados': lotes.filter(estado='cancelado').count(),
            'valor_total_inventario': lotes.filter(estado='disponible').aggregate(
                total=Sum('valor_total')
            )['total'] or Decimal('0.00'),
            'valor_total_vendido': lotes.filter(estado='vendido').aggregate(
                total=Sum('valor_total')
            )['total'] or Decimal('0.00'),
            'promedio_metros_cuadrados': lotes.aggregate(
                promedio=Avg('metros_cuadrados')
            )['promedio'] or Decimal('0.00'),
            'promedio_valor_lote': lotes.aggregate(
                promedio=Avg('valor_total')
            )['promedio'] or Decimal('0.00'),
        }
        
        serializer = LoteEstadisticasSerializer(stats)
        return Response(serializer.data)


class HistorialLoteViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para consulta de historial de lotes"""
    queryset = HistorialLote.objects.all()
    serializer_class = HistorialLoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = HistorialLote.objects.all()
        lote_id = self.request.query_params.get('lote_id', None)
        estado = self.request.query_params.get('estado', None)
        fecha_desde = self.request.query_params.get('fecha_desde', None)
        fecha_hasta = self.request.query_params.get('fecha_hasta', None)
        
        if lote_id:
            queryset = queryset.filter(lote_id=lote_id)
        
        if estado:
            queryset = queryset.filter(estado_nuevo=estado)
        
        if fecha_desde:
            queryset = queryset.filter(fecha_cambio__gte=fecha_desde)
        
        if fecha_hasta:
            queryset = queryset.filter(fecha_cambio__lte=fecha_hasta)
        
        return queryset.order_by('-fecha_cambio')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lotes_disponibles_count(request):
    """Obtener conteo de lotes disponibles"""
    count = Lote.objects.filter(estado='disponible', activo=True).count()
    return Response({'lotes_disponibles': count})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def filtrar_lotes(request):
    """Filtrar lotes con múltiples criterios"""
    serializer = LoteFiltroSerializer(data=request.data)
    if serializer.is_valid():
        queryset = Lote.objects.filter(activo=True)
        data = serializer.validated_data
        
        if data.get('manzana'):
            queryset = queryset.filter(manzana__nombre__icontains=data['manzana'])
        
        if data.get('estado'):
            queryset = queryset.filter(estado=data['estado'])
        
        if data.get('precio_min'):
            queryset = queryset.filter(valor_total__gte=data['precio_min'])
        
        if data.get('precio_max'):
            queryset = queryset.filter(valor_total__lte=data['precio_max'])
        
        if data.get('metros_min'):
            queryset = queryset.filter(metros_cuadrados__gte=data['metros_min'])
        
        if data.get('metros_max'):
            queryset = queryset.filter(metros_cuadrados__lte=data['metros_max'])
        
        if data.get('solo_disponibles'):
            queryset = queryset.filter(estado='disponible')
        
        serializer_result = LoteListSerializer(queryset, many=True)
        return Response(serializer_result.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
