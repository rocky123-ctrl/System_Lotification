from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count
from django.utils import timezone
from decimal import Decimal
from .models import ConfiguracionGeneral, ConfiguracionFinanciera
from .serializers import (
    ConfiguracionGeneralSerializer, ConfiguracionGeneralUpdateSerializer,
    ConfiguracionGeneralPublicSerializer, ConfiguracionFinancieraSerializer,
    ConfiguracionFinancieraUpdateSerializer, ConfiguracionCompletaSerializer,
    LogoUploadSerializer, ConfiguracionResumenSerializer, ConfiguracionEstadisticasSerializer
)


class ConfiguracionGeneralViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de configuración general"""
    queryset = ConfiguracionGeneral.objects.all()
    serializer_class = ConfiguracionGeneralSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return ConfiguracionGeneralUpdateSerializer
        elif self.action == 'public':
            return ConfiguracionGeneralPublicSerializer
        elif self.action == 'completa':
            return ConfiguracionCompletaSerializer
        return ConfiguracionGeneralSerializer

    def get_queryset(self):
        return ConfiguracionGeneral.objects.all().order_by('-fecha_actualizacion')

    @action(detail=False, methods=['get'])
    def activa(self, request):
        """Obtener la configuración activa"""
        config = ConfiguracionGeneral.get_configuracion_activa()
        if config:
            serializer = self.get_serializer(config)
            return Response(serializer.data)
        return Response(
            {'error': 'No hay configuración activa'}, 
            status=status.HTTP_404_NOT_FOUND
        )

    @action(detail=False, methods=['get'])
    def public(self, request):
        """Obtener información pública de la configuración"""
        config = ConfiguracionGeneral.get_configuracion_activa()
        if config:
            serializer = ConfiguracionGeneralPublicSerializer(config)
            return Response(serializer.data)
        return Response(
            {'error': 'No hay configuración activa'}, 
            status=status.HTTP_404_NOT_FOUND
        )

    @action(detail=False, methods=['get'])
    def completa(self, request):
        """Obtener configuración completa con datos financieros"""
        config = ConfiguracionGeneral.get_configuracion_activa()
        if config:
            serializer = ConfiguracionCompletaSerializer(config)
            return Response(serializer.data)
        return Response(
            {'error': 'No hay configuración activa'}, 
            status=status.HTTP_404_NOT_FOUND
        )

    @action(detail=False, methods=['get'])
    def resumen(self, request):
        """Obtener resumen de configuración con estadísticas"""
        config = ConfiguracionGeneral.get_configuracion_activa()
        if not config:
            return Response(
                {'error': 'No hay configuración activa'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Importar aquí para evitar importación circular
        from lotes.models import Lote
        
        # Obtener estadísticas de lotes
        lotes = Lote.objects.filter(activo=True)
        total_lotes_reales = lotes.count()
        
        # Contar por estado
        lotes_disponibles = lotes.filter(estado='disponible').count()
        lotes_reservados = lotes.filter(estado='reservado').count()
        lotes_en_proceso = lotes.filter(estado='en_proceso').count()
        lotes_financiados = lotes.filter(estado='financiado').count()
        lotes_vendidos = lotes.filter(estado='vendido').count()
        lotes_cancelados = lotes.filter(estado='cancelado').count()
        
        # Calcular valores totales
        valor_total_inventario = lotes.filter(estado='disponible').aggregate(
            total=Sum('valor_total')
        )['total'] or Decimal('0.00')
        
        valor_total_reservados = lotes.filter(estado='reservado').aggregate(
            total=Sum('valor_total')
        )['total'] or Decimal('0.00')
        
        valor_total_en_proceso = lotes.filter(estado='en_proceso').aggregate(
            total=Sum('valor_total')
        )['total'] or Decimal('0.00')
        
        valor_total_financiados = lotes.filter(estado='financiado').aggregate(
            total=Sum('valor_total')
        )['total'] or Decimal('0.00')
        
        valor_total_vendido = lotes.filter(estado='vendido').aggregate(
            total=Sum('valor_total')
        )['total'] or Decimal('0.00')
        
        resumen_data = {
            'nombre_lotificacion': config.nombre_lotificacion,
            'ubicacion': config.ubicacion,
            'total_lotes_configurado': config.total_lotes,
            'total_lotes_reales': total_lotes_reales,
            'lotes_disponibles': lotes_disponibles,
            'lotes_reservados': lotes_reservados,
            'lotes_en_proceso': lotes_en_proceso,
            'lotes_financiados': lotes_financiados,
            'lotes_vendidos': lotes_vendidos,
            'lotes_cancelados': lotes_cancelados,
            'tasa_anual': config.tasa_anual,
            'tasa_anual_formateada': config.tasa_anual_formateada,
            'valor_total_inventario': valor_total_inventario,
            'valor_total_reservados': valor_total_reservados,
            'valor_total_en_proceso': valor_total_en_proceso,
            'valor_total_financiados': valor_total_financiados,
            'valor_total_vendido': valor_total_vendido,
            'fecha_ultima_actualizacion': config.fecha_actualizacion,
        }
        
        serializer = ConfiguracionResumenSerializer(resumen_data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Obtener estadísticas de configuración"""
        total_configuraciones = ConfiguracionGeneral.objects.count()
        config_activa = ConfiguracionGeneral.get_configuracion_activa()
        
        stats = {
            'total_configuraciones': total_configuraciones,
            'configuracion_activa': config_activa is not None,
            'fecha_creacion_configuracion': config_activa.fecha_creacion if config_activa else None,
            'fecha_ultima_actualizacion': config_activa.fecha_actualizacion if config_activa else None,
            'tiene_logo': config_activa.logo is not None if config_activa else False,
            'tiene_configuracion_financiera': hasattr(config_activa, 'configuracion_financiera') if config_activa else False,
        }
        
        serializer = ConfiguracionEstadisticasSerializer(stats)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def activar(self, request, pk=None):
        """Activar una configuración específica"""
        config = self.get_object()
        
        # Desactivar todas las configuraciones
        ConfiguracionGeneral.objects.update(activo=False)
        
        # Activar la configuración seleccionada
        config.activo = True
        config.save()
        
        serializer = self.get_serializer(config)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def subir_logo(self, request, pk=None):
        """Subir logo para una configuración"""
        config = self.get_object()
        serializer = LogoUploadSerializer(config, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        """Sobrescribir create para manejar configuración única"""
        # Si es la primera configuración, activarla automáticamente
        if not ConfiguracionGeneral.objects.exists():
            serializer.save(activo=True)
        else:
            serializer.save()


class ConfiguracionFinancieraViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de configuración financiera"""
    queryset = ConfiguracionFinanciera.objects.all()
    serializer_class = ConfiguracionFinancieraSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return ConfiguracionFinancieraUpdateSerializer
        return ConfiguracionFinancieraSerializer

    @action(detail=False, methods=['get'])
    def activa(self, request):
        """Obtener configuración financiera activa"""
        config_general = ConfiguracionGeneral.get_configuracion_activa()
        if not config_general:
            return Response(
                {'error': 'No hay configuración general activa'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            config_financiera = config_general.configuracion_financiera
            serializer = self.get_serializer(config_financiera)
            return Response(serializer.data)
        except ConfiguracionFinanciera.DoesNotExist:
            return Response(
                {'error': 'No hay configuración financiera para la configuración activa'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def crear_para_activa(self, request):
        """Crear configuración financiera para la configuración activa"""
        config_general = ConfiguracionGeneral.get_configuracion_activa()
        if not config_general:
            return Response(
                {'error': 'No hay configuración general activa'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar si ya existe configuración financiera
        if hasattr(config_general, 'configuracion_financiera'):
            return Response(
                {'error': 'Ya existe configuración financiera para la configuración activa'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(configuracion=config_general)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def configuracion_publica(request):
    """Endpoint público para obtener información básica de la lotificación"""
    config = ConfiguracionGeneral.get_configuracion_activa()
    if config:
        serializer = ConfiguracionGeneralPublicSerializer(config)
        return Response(serializer.data)
    return Response(
        {'error': 'No hay configuración disponible'}, 
        status=status.HTTP_404_NOT_FOUND
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def inicializar_configuracion(request):
    """Inicializar configuración por defecto"""
    try:
        # Crear configuración general
        config_general = ConfiguracionGeneral.get_or_create_configuracion()
        
        # Crear configuración financiera si no existe
        if not hasattr(config_general, 'configuracion_financiera'):
            ConfiguracionFinanciera.objects.create(configuracion=config_general)
        
        serializer = ConfiguracionCompletaSerializer(config_general)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response(
            {'error': f'Error al inicializar configuración: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
