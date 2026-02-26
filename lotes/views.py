from rest_framework import status, generics, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers as drf_serializers
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Count, Avg, Sum
from django.db import transaction
from django.utils import timezone
from django.http import HttpResponse, FileResponse
from decimal import Decimal
import os
import re
import logging
from .models import Lotificacion, Manzana, Lote, HistorialLote
from .serializers import (
    LotificacionSerializer, ManzanaSerializer, LoteSerializer, LoteListSerializer,
    LotePlanoListSerializer,
    LoteCreateSerializer, LoteUpdateSerializer, HistorialLoteSerializer,
    LoteEstadisticasSerializer, LoteFiltroSerializer, LoteReservaSerializer
)

logger = logging.getLogger(__name__)


class LotePagination(PageNumberPagination):
    """Paginación opcional para lotes"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_page_size(self, request):
        """Permitir desactivar paginación con page_size=0"""
        if self.page_size_query_param:
            page_size = request.query_params.get(self.page_size_query_param)
            if page_size == '0':
                return None  # Sin paginación
            if page_size is not None:
                try:
                    return min(int(page_size), self.max_page_size)
                except (KeyError, ValueError):
                    pass
        return self.page_size


class LotificacionViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de lotificaciones"""
    queryset = Lotificacion.objects.all()
    serializer_class = LotificacionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Devolver todas las lotificaciones (activas e inactivas)
        queryset = Lotificacion.objects.all()
        nombre = self.request.query_params.get('nombre', None)
        if nombre:
            queryset = queryset.filter(nombre__icontains=nombre)
        # Ordenar por activo primero (activas primero) y luego por nombre
        return queryset.order_by('-activo', 'nombre')

    def get_serializer_context(self):
        """Agregar request al contexto del serializer para generar URLs absolutas"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def list(self, request, *args, **kwargs):
        """Sobrescribir list para manejar errores mejor"""
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            logger.error(f'Error en list de lotificaciones: {str(e)}', exc_info=True)
            return Response(
                {'error': f'Error al obtener lotificaciones: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_create(self, serializer):
        """Asignar created_by al crear una lotificación"""
        try:
            serializer.save(created_by=self.request.user)
        except Exception as e:
            logger.error(f'Error en perform_create de lotificaciones: {str(e)}', exc_info=True)
            raise

    def perform_update(self, serializer):
        """Asignar updated_by al actualizar una lotificación"""
        try:
            serializer.save(updated_by=self.request.user)
        except Exception as e:
            logger.error(f'Error en perform_update de lotificaciones: {str(e)}', exc_info=True)
            raise

    @action(detail=True, methods=['get'])
    def manzanas(self, request, pk=None):
        """
        Listar manzanas de una lotificación.
        GET /api/lotes/lotificaciones/{id}/manzanas/
        Query: todas=1 para incluir inactivas (para edición en frontend).
        """
        lotificacion = self.get_object()
        todas = request.query_params.get('todas') == '1'
        if todas:
            manzanas = lotificacion.manzanas.all().order_by('id')
        else:
            manzanas = lotificacion.manzanas.filter(activo=True).order_by('nombre')
        serializer = ManzanaSerializer(manzanas, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='plano-svg')
    def plano_svg(self, request, pk=None):
        """
        Servir el archivo SVG del plano de la lotificación.
        GET /api/lotes/lotificaciones/{id}/plano-svg/
        Devuelve el SVG como image/svg+xml para incrustar en el frontend.
        Protegido con IsAuthenticated (JWT).
        """
        lotificacion = self.get_object()
        if not lotificacion.plano_svg:
            return Response(
                {'error': 'Esta lotificación no tiene un plano SVG cargado.'},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            with open(lotificacion.plano_svg.path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            return HttpResponse(content, content_type='image/svg+xml')
        except Exception as e:
            logger.error(f'Error sirviendo plano SVG: {e}', exc_info=True)
            return Response(
                {'error': 'No se pudo leer el archivo del plano.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='lotes')
    def lotes_plano(self, request, pk=None):
        """
        Listar lotes de una lotificación (para plano interactivo).
        GET /api/lotes/lotificaciones/{id}/lotes/
        Filtra por manzana.lotificacion_id. Devuelve id, identificador, estado, activo, manzana.
        """
        lotificacion = self.get_object()
        lotes = Lote.objects.filter(manzana__lotificacion_id=pk, activo=True).select_related('manzana')
        serializer = LotePlanoListSerializer(lotes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path=r'lotes/(?P<identificador>[^/.]+)')
    def lote_por_identificador(self, request, pk=None, identificador=None):
        """
        Detalle de un lote por identificador dentro de la lotificación.
        GET /api/lotes/lotificaciones/{id}/lotes/{identificador}/
        Valida que el lote pertenezca a esa lotificación.
        """
        lotificacion = self.get_object()
        lote = Lote.objects.filter(
            manzana__lotificacion_id=pk,
            identificador=identificador,
            activo=True
        ).select_related('manzana', 'manzana__lotificacion', 'actualizado_por').first()
        if not lote:
            return Response(
                {'error': f'No se encontró un lote con identificador "{identificador}" en esta lotificación.'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = LoteSerializer(lote)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='registrar-lote')
    def registrar_lote(self, request, pk=None):
        """
        Registrar un lote nuevo desde el plano por identificador (ej: MZ03-L07).
        POST /api/lotes/lotificaciones/{id}/registrar-lote/
        Body: { identificador, metros_cuadrados, valor_total, costo_instalacion?, estado? }
        No se envían llaves foráneas ni auditoría: manzana/numero_lote se derivan del identificador.
        """
        lotificacion = self.get_object()
        identificador = (request.data.get('identificador') or '').strip()
        if not identificador:
            return Response(
                {'error': 'El campo "identificador" es obligatorio.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Aceptar formato MZ{manzana}-L{número} (ej: MZ03-L07) o {manzana}-{número} (ej: A-01)
        match = re.match(r'^MZ(.+)-L(.+)$', identificador, re.IGNORECASE)
        if match:
            nombre_manzana = match.group(1).strip()
            numero_lote = match.group(2).strip()
        else:
            match = re.match(r'^(.+)-(.+)$', identificador)
            if not match:
                return Response(
                    {'error': 'Identificador no válido. Use el formato MZ{manzana}-L{número} (ej: MZ03-L07) o {manzana}-{número} (ej: A-01).'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            nombre_manzana = match.group(1).strip()
            numero_lote = match.group(2).strip()
        if not nombre_manzana or not numero_lote:
            return Response(
                {'error': 'Identificador no válido.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        manzana = Manzana.objects.filter(
            lotificacion_id=pk,
            nombre=nombre_manzana,
            activo=True
        ).first()
        if not manzana:
            return Response(
                {'error': f'No existe la manzana "{nombre_manzana}" en esta lotificación.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if Lote.objects.filter(manzana=manzana, numero_lote=numero_lote).exists():
            return Response(
                {'error': f'Ya existe un lote con identificador "{identificador}".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if Lote.objects.filter(identificador=identificador).exists():
            return Response(
                {'error': f'Ya existe un lote con identificador "{identificador}".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        metros_cuadrados = request.data.get('metros_cuadrados')
        valor_total = request.data.get('valor_total')
        if metros_cuadrados is None or valor_total is None:
            return Response(
                {'error': 'Los campos "metros_cuadrados" y "valor_total" son obligatorios.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            metros_cuadrados = Decimal(str(metros_cuadrados))
            valor_total = Decimal(str(valor_total))
        except Exception:
            return Response(
                {'error': 'metros_cuadrados y valor_total deben ser números válidos.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        costo_instalacion = request.data.get('costo_instalacion')
        if costo_instalacion is not None:
            try:
                costo_instalacion = Decimal(str(costo_instalacion))
            except Exception:
                costo_instalacion = Decimal('5000.00')
        else:
            costo_instalacion = Decimal('5000.00')
        estado = (request.data.get('estado') or 'disponible').strip().lower()
        if estado not in dict(Lote.ESTADO_CHOICES):
            estado = 'disponible'
        data = {
            'manzana': manzana.pk,
            'numero_lote': numero_lote,
            'identificador': identificador,
            'metros_cuadrados': metros_cuadrados,
            'valor_total': valor_total,
            'costo_instalacion': costo_instalacion,
            'estado': estado,
        }
        serializer = LoteCreateSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            lote = serializer.save()
            if request.user:
                Lote.objects.filter(pk=lote.pk).update(actualizado_por=request.user)
                lote.refresh_from_db()
        return Response(LoteSerializer(lote).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='subir-plano-svg')
    def subir_plano_svg(self, request, pk=None):
        """
        Subir o reemplazar el plano SVG de una lotificación
        POST /api/lotificaciones/{id}/subir-plano-svg/
        Body: FormData con campo 'plano_svg' (archivo SVG)
        """
        lotificacion = self.get_object()
        
        # Validar que se haya enviado un archivo
        if 'plano_svg' not in request.FILES:
            return Response(
                {'error': 'No se proporcionó ningún archivo. Use el campo "plano_svg".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        archivo = request.FILES['plano_svg']
        
        # Validar que sea un archivo SVG
        if not archivo.name.lower().endswith('.svg'):
            return Response(
                {'error': 'El archivo debe ser un SVG (.svg)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar tamaño (máximo 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if archivo.size > max_size:
            return Response(
                {'error': f'El archivo es demasiado grande. Tamaño máximo: 10MB'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Si ya existe un plano SVG, eliminarlo primero
            if lotificacion.plano_svg:
                # Eliminar archivo físico si existe
                if os.path.isfile(lotificacion.plano_svg.path):
                    os.remove(lotificacion.plano_svg.path)
            
            # Guardar nuevo archivo
            lotificacion.plano_svg = archivo
            lotificacion.plano_svg_nombre = archivo.name
            lotificacion.plano_svg_tamaño = archivo.size
            lotificacion.plano_svg_fecha_subida = timezone.now()
            lotificacion.save()
            
            # Retornar lotificación actualizada
            serializer = LotificacionSerializer(lotificacion, context={'request': request})
            return Response({
                'success': True,
                'message': 'Plano SVG subido exitosamente',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Error al subir el archivo: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['delete'], url_path='eliminar-plano-svg')
    def eliminar_plano_svg(self, request, pk=None):
        """
        Eliminar el plano SVG de una lotificación
        DELETE /api/lotificaciones/{id}/eliminar-plano-svg/
        """
        lotificacion = self.get_object()
        
        if not lotificacion.plano_svg:
            return Response(
                {'error': 'La lotificación no tiene un plano SVG para eliminar'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Eliminar archivo físico si existe
            if os.path.isfile(lotificacion.plano_svg.path):
                os.remove(lotificacion.plano_svg.path)
            
            # Limpiar campos relacionados
            lotificacion.plano_svg.delete(save=False)
            lotificacion.plano_svg_nombre = None
            lotificacion.plano_svg_tamaño = None
            lotificacion.plano_svg_fecha_subida = None
            lotificacion.save()
            
            # Retornar lotificación actualizada
            serializer = LotificacionSerializer(lotificacion, context={'request': request})
            return Response({
                'success': True,
                'message': 'Plano SVG eliminado exitosamente',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Error al eliminar el archivo: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ManzanaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de manzanas"""
    queryset = Manzana.objects.all()
    serializer_class = ManzanaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Para update/retrieve/destroy permitir cualquier manzana (incl. inactivas)
        if self.action in ('retrieve', 'update', 'partial_update', 'destroy'):
            queryset = Manzana.objects.all()
        else:
            queryset = Manzana.objects.filter(activo=True)
        lotificacion_id = self.request.query_params.get('lotificacion', None)
        if lotificacion_id:
            queryset = queryset.filter(lotificacion_id=lotificacion_id)
        nombre = self.request.query_params.get('nombre', None)
        if nombre:
            queryset = queryset.filter(nombre__icontains=nombre)
        return queryset.order_by('lotificacion', 'nombre')

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
    pagination_class = LotePagination

    def get_serializer_class(self):
        if self.action == 'create':
            return LoteCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return LoteUpdateSerializer
        elif self.action == 'list':
            return LoteListSerializer
        return LoteSerializer

    def get_queryset(self):
        queryset = Lote.objects.filter(activo=True).select_related(
            'manzana', 
            'manzana__lotificacion',
            'actualizado_por'
        )
        
        # Filtros
        lotificacion_id = self.request.query_params.get('lotificacion', None)
        manzana_id = self.request.query_params.get('manzana_id', None)
        manzana = self.request.query_params.get('manzana', None)
        estado = self.request.query_params.get('estado', None)
        precio_min = self.request.query_params.get('precio_min', None)
        precio_max = self.request.query_params.get('precio_max', None)
        metros_min = self.request.query_params.get('metros_min', None)
        metros_max = self.request.query_params.get('metros_max', None)
        solo_disponibles = self.request.query_params.get('solo_disponibles', None)
        
        # API 2: Filtrar por lotificación
        if lotificacion_id:
            queryset = queryset.filter(manzana__lotificacion_id=lotificacion_id)
        
        # Filtrar por manzana (ID o nombre)
        if manzana_id:
            queryset = queryset.filter(manzana_id=manzana_id)
        
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
        
        return queryset.order_by('manzana__lotificacion', 'manzana', 'numero_lote')

    def perform_update(self, serializer):
        """
        Actualizar lote con control de concurrencia básico
        API 4: Actualizar estado del lote con control de concurrencia
        """
        instance = serializer.instance
        old_status = instance.estado
        new_status = serializer.validated_data.get('estado', old_status)
        
        # Usar select_for_update para bloqueo de fila en la base de datos
        with transaction.atomic():
            # Bloquear la fila para evitar condiciones de carrera
            lote = Lote.objects.select_for_update().get(pk=instance.pk)
            
            # Verificar versión nuevamente después del bloqueo
            version_enviada = serializer.validated_data.get('version')
            if version_enviada != lote.version:
                raise drf_serializers.ValidationError({
                    'version': 'El lote ha sido modificado por otro usuario. Por favor, recarga los datos.'
                })
            
            # Guardar el lote con usuario para auditoría
            lote = serializer.save(user=self.request.user)
            
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
    
    def perform_create(self, serializer):
        """Crear lote con usuario para auditoría"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'], url_path='por-identificador/(?P<identificador>[^/.]+)')
    def por_identificador(self, request, identificador=None):
        """
        API 3: Obtener detalle de un lote por identificador
        GET /api/lotes/por-identificador/{identificador}/
        """
        try:
            lote = Lote.objects.select_related(
                'manzana', 
                'manzana__lotificacion',
                'actualizado_por'
            ).get(
                identificador=identificador, 
                activo=True
            )
            serializer = LoteSerializer(lote)
            return Response(serializer.data)
        except Lote.DoesNotExist:
            return Response(
                {
                    'error': f'Lote con identificador "{identificador}" no encontrado',
                    'identificador': identificador
                }, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def reservar(self, request, pk=None):
        """
        API 5: Reservar un lote (cambiar estado a RESERVADO si está DISPONIBLE)
        POST /api/lotes/{id}/reservar/
        Body: {"version": 1, "notas": "Opcional"}
        """
        lote = self.get_object()
        serializer = LoteReservaSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        version_enviada = serializer.validated_data.get('version')
        notas = serializer.validated_data.get('notas', '')
        
        # Usar transacción con bloqueo de fila para control de concurrencia
        with transaction.atomic():
            # Bloquear la fila para evitar condiciones de carrera
            lote = Lote.objects.select_for_update().get(pk=lote.pk)
            
            # Verificar versión
            if version_enviada != lote.version:
                return Response(
                    {
                        'error': 'El lote ha sido modificado por otro usuario. Por favor, recarga los datos.',
                        'version_actual': lote.version
                    },
                    status=status.HTTP_409_CONFLICT
                )
            
            # Validar que el lote esté disponible (no RESERVADO ni VENDIDO)
            if lote.estado in ['reservado', 'pagado', 'pagado_y_escriturado']:
                return Response(
                    {
                        'error': f'El lote no puede ser reservado. Estado actual: {lote.get_estado_display()}',
                        'estado_actual': lote.estado,
                        'mensaje': 'Solo se pueden reservar lotes con estado DISPONIBLE'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Cambiar estado a RESERVADO
            estado_anterior = lote.estado
            lote.estado = 'reservado'
            lote.save(user=request.user)  # Guardar con usuario para auditoría
            
            # Registrar en historial
            HistorialLote.objects.create(
                lote=lote,
                estado_anterior=estado_anterior,
                estado_nuevo='reservado',
                cambiado_por=request.user,
                notas=notas or 'Lote reservado'
            )
            
            serializer_response = LoteSerializer(lote)
            return Response({
                'success': True,
                'message': 'Lote reservado exitosamente',
                'data': serializer_response.data
            }, status=status.HTTP_200_OK)

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
            'lotes_pagados': lotes.filter(estado='pagado').count(),
            'lotes_comercial_bodega': lotes.filter(estado='comercial_y_bodega').count(),
            'lotes_financiados': lotes.filter(estado='financiado').count(),
            'lotes_pagado_escriturado': lotes.filter(estado='pagado_y_escriturado').count(),
            'valor_total_inventario': lotes.filter(estado='disponible').aggregate(
                total=Sum('valor_total')
            )['total'] or Decimal('0.00'),
            'valor_total_vendido': lotes.filter(estado__in=['pagado', 'pagado_y_escriturado']).aggregate(
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
