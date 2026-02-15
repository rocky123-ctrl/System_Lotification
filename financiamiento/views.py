from django.shortcuts import render
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from .models import Financiamiento, Cuota, Pago, ConfiguracionPago, PagoCapital
from .serializers import (
    FinanciamientoSerializer, FinanciamientoCreateSerializer, FinanciamientoListSerializer,
    FinanciamientoDetailSerializer, CuotaSerializer, CuotaDetailSerializer,
    PagoSerializer, PagoDetailSerializer, ConfiguracionPagoSerializer,
    FinanciamientoEstadisticasSerializer, PagoCapitalSerializer, PagoCapitalCreateSerializer
)
from rest_framework import serializers
from django.db import transaction
from configuracion.models import ConfiguracionFinanciera


class PagoCapitalViewSet(viewsets.ModelViewSet):
    """ViewSet para manejar pagos a capital"""
    queryset = PagoCapital.objects.all()
    serializer_class = PagoCapitalSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PagoCapitalCreateSerializer
        return PagoCapitalSerializer
    
    def perform_create(self, serializer):
        """Asignar el usuario que crea el pago"""
        serializer.save(creado_por=self.request.user)
    
    @action(detail=False, methods=['get'])
    def por_financiamiento(self, request):
        """Obtener pagos a capital por financiamiento"""
        financiamiento_id = request.query_params.get('financiamiento_id')
        
        if not financiamiento_id:
            return Response(
                {'error': 'Se requiere financiamiento_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            pagos = PagoCapital.objects.filter(financiamiento_id=financiamiento_id)
            serializer = self.get_serializer(pagos, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Error al obtener pagos: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def resumen_mensual(self, request):
        """Obtener resumen mensual de pagos a capital"""
        try:
            # Obtener parámetros
            año = request.query_params.get('año', timezone.now().year)
            mes = request.query_params.get('mes', timezone.now().month)
            
            # Filtrar pagos del mes
            pagos = PagoCapital.objects.filter(
                fecha_pago__year=año,
                fecha_pago__month=mes
            )
            
            # Calcular estadísticas
            total_pagos = pagos.count()
            monto_total = pagos.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
            
            # Agrupar por financiamiento
            por_financiamiento = pagos.values('financiamiento__lote__numero_lote', 'financiamiento__promitente_comprador').annotate(
                total_pagos=Count('id'),
                monto_total=Sum('monto')
            )
            
            return Response({
                'año': año,
                'mes': mes,
                'total_pagos': total_pagos,
                'monto_total': monto_total,
                'por_financiamiento': por_financiamiento
            })
        except Exception as e:
            return Response(
                {'error': f'Error al obtener resumen: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Obtener estadísticas generales de pagos a capital"""
        try:
            # Estadísticas generales
            total_pagos = PagoCapital.objects.count()
            monto_total = PagoCapital.objects.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
            
            # Pagos del mes actual
            mes_actual = timezone.now().month
            año_actual = timezone.now().year
            pagos_mes = PagoCapital.objects.filter(
                fecha_pago__year=año_actual,
                fecha_pago__month=mes_actual
            )
            total_pagos_mes = pagos_mes.count()
            monto_total_mes = pagos_mes.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
            
            # Promedio por pago
            promedio_pago = monto_total / total_pagos if total_pagos > 0 else Decimal('0.00')
            
            return Response({
                'total_pagos': total_pagos,
                'monto_total': monto_total,
                'promedio_pago': promedio_pago,
                'mes_actual': {
                    'total_pagos': total_pagos_mes,
                    'monto_total': monto_total_mes
                }
            })
        except Exception as e:
            return Response(
                {'error': f'Error al obtener estadísticas: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class FinanciamientoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de financiamientos"""
    queryset = Financiamiento.objects.all()
    serializer_class = FinanciamientoSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return FinanciamientoCreateSerializer
        elif self.action == 'list':
            return FinanciamientoListSerializer
        elif self.action == 'retrieve':
            return FinanciamientoDetailSerializer
        return FinanciamientoSerializer

    def get_queryset(self):
        queryset = Financiamiento.objects.all()
        
        # Filtros
        promitente = self.request.query_params.get('promitente', None)
        estado = self.request.query_params.get('estado', None)
        manzana = self.request.query_params.get('manzana', None)
        en_mora = self.request.query_params.get('en_mora', None)
        
        if promitente:
            queryset = queryset.filter(promitente_comprador__icontains=promitente)
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        if manzana:
            queryset = queryset.filter(lote__manzana__nombre__icontains=manzana)
        
        if en_mora == 'true':
            queryset = queryset.filter(estado='en_mora')
        
        return queryset.order_by('-fecha_creacion')

    def perform_create(self, serializer):
        """Sobrescribir create para asignar usuario"""
        serializer.save(creado_por=self.request.user)

    def perform_update(self, serializer):
        """Sobrescribir update para asignar usuario"""
        serializer.save(actualizado_por=self.request.user)

    @action(detail=False, methods=['get'])
    def activos(self, request):
        """Obtener financiamientos activos"""
        financiamientos = self.get_queryset().filter(estado='activo')
        serializer = self.get_serializer(financiamientos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def en_mora(self, request):
        """Obtener financiamientos en mora"""
        financiamientos = self.get_queryset().filter(estado='en_mora')
        serializer = self.get_serializer(financiamientos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def finalizados(self, request):
        """Obtener financiamientos finalizados"""
        financiamientos = self.get_queryset().filter(estado='finalizado')
        serializer = self.get_serializer(financiamientos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Obtener estadísticas de financiamientos"""
        try:
            total_financiamientos = self.queryset.count()
            activos = self.queryset.filter(estado='activo').count()
            en_mora = self.queryset.filter(estado='en_mora').count()
            finalizados = self.queryset.filter(estado='finalizado').count()
            
            # Montos totales
            monto_total_financiado = self.queryset.aggregate(
                total=Sum('totalidad')
            )['total'] or Decimal('0.00')
            
            monto_total_cobrado = self.queryset.aggregate(
                total=Sum('capital_cancelado')
            )['total'] or Decimal('0.00')
            
            # Pagos a capital
            total_pagos_capital = PagoCapital.objects.aggregate(
                total=Sum('monto')
            )['total'] or Decimal('0.00')
            
            return Response({
                'total_financiamientos': total_financiamientos,
                'activos': activos,
                'en_mora': en_mora,
                'finalizados': finalizados,
                'monto_total_financiado': monto_total_financiado,
                'monto_total_cobrado': monto_total_cobrado,
                'total_pagos_capital': total_pagos_capital,
                'porcentaje_cobrado': (monto_total_cobrado / monto_total_financiado * 100) if monto_total_financiado > 0 else 0
            })
        except Exception as e:
            return Response(
                {'error': f'Error al obtener estadísticas: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def calcular_moras(self, request, pk=None):
        """Calcular moras para un financiamiento específico"""
        financiamiento = self.get_object()
        
        # Calcular moras para todas las cuotas pendientes
        cuotas_pendientes = financiamiento.cuotas.filter(estado='pendiente')
        cuotas_atrasadas = 0
        
        for cuota in cuotas_pendientes:
            cuota.calcular_mora()
            if cuota.estado == 'atrasada':
                cuotas_atrasadas += 1
        
        # Actualizar estado del financiamiento
        if cuotas_atrasadas > 0:
            financiamiento.estado = 'en_mora'
            financiamiento.save()
        
        serializer = self.get_serializer(financiamiento)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def cuotas(self, request, pk=None):
        """Obtener cuotas de un financiamiento"""
        financiamiento = self.get_object()
        cuotas = financiamiento.cuotas.all()
        serializer = CuotaSerializer(cuotas, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def pagos(self, request, pk=None):
        """Obtener pagos de un financiamiento"""
        financiamiento = self.get_object()
        pagos = financiamiento.pagos.all()
        serializer = PagoSerializer(pagos, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def pagos_capital(self, request, pk=None):
        """Obtener pagos a capital de un financiamiento"""
        financiamiento = self.get_object()
        pagos_capital = financiamiento.pagos_capital.all()
        serializer = PagoCapitalSerializer(pagos_capital, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def aplicar_pago_capital(self, request, pk=None):
        """Aplicar un pago a capital a un financiamiento"""
        financiamiento = self.get_object()
        
        try:
            monto = Decimal(request.data.get('monto', 0))
            fecha_pago = request.data.get('fecha_pago', timezone.now().date())
            concepto = request.data.get('concepto', 'Pago a capital')
            
            if monto <= 0:
                return Response(
                    {'error': 'El monto debe ser mayor a 0'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Crear el pago a capital
            pago_capital = PagoCapital.objects.create(
                financiamiento=financiamiento,
                monto=monto,
                fecha_pago=fecha_pago,
                concepto=concepto,
                creado_por=request.user
            )
            
            serializer = PagoCapitalSerializer(pago_capital)
            return Response({
                'mensaje': 'Pago a capital aplicado exitosamente',
                'pago_capital': serializer.data,
                'financiamiento_actualizado': FinanciamientoSerializer(financiamiento).data
            })
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Error al aplicar pago a capital: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def simulacion_pago_capital(self, request, pk=None):
        """Simular el efecto de un pago a capital"""
        financiamiento = self.get_object()
        
        try:
            monto = Decimal(request.query_params.get('monto', 0))
            
            if monto <= 0:
                return Response(
                    {'error': 'El monto debe ser mayor a 0'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if monto > financiamiento.saldo_restante:
                return Response(
                    {'error': 'El monto excede el saldo restante'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Simular el pago a capital
            saldo_anterior = financiamiento.saldo_restante
            saldo_nuevo = saldo_anterior - monto
            cuotas_pendientes = financiamiento.cuotas.filter(estado='pendiente').count()
            
            # Calcular nueva cuota mensual usando la tasa anual de configuración
            from configuracion.models import ConfiguracionGeneral
            config = ConfiguracionGeneral.objects.first()
            if not config:
                return Response(
                    {'error': 'No se encontró configuración general. Configure primero la tasa anual.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Usar la tasa anual de la configuración y convertir a mensual
            tasa_anual = config.tasa_anual
            if tasa_anual <= 0:
                return Response(
                    {'error': 'La tasa anual debe ser mayor a 0'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Convertir tasa anual a mensual usando la fórmula correcta
            # tasa_mensual = (1 + tasa_anual)^(1/12) - 1
            tasa_anual_decimal = tasa_anual / Decimal('100')
            tasa_mensual_decimal = (Decimal('1') + tasa_anual_decimal) ** (Decimal('1') / Decimal('12')) - Decimal('1')
            tasa_mensual = tasa_mensual_decimal * Decimal('100')
            tasa_decimal = tasa_mensual / 100
            
            if tasa_decimal > 0 and cuotas_pendientes > 0:
                nueva_cuota_mensual = saldo_nuevo * (tasa_decimal * (1 + tasa_decimal)**cuotas_pendientes) / ((1 + tasa_decimal)**cuotas_pendientes - 1)
            else:
                nueva_cuota_mensual = saldo_nuevo / cuotas_pendientes if cuotas_pendientes > 0 else 0
            
            # Calcular ahorro estimado
            ahorro_estimado = monto * tasa_decimal * cuotas_pendientes / 2
            
            return Response({
                'monto_pago': monto,
                'saldo_anterior': saldo_anterior,
                'saldo_nuevo': saldo_nuevo,
                'cuota_actual': financiamiento.cuota_mensual,
                'nueva_cuota_mensual': nueva_cuota_mensual,
                'cuotas_pendientes': cuotas_pendientes,
                'ahorro_estimado_intereses': ahorro_estimado,
                'reduccion_cuota': financiamiento.cuota_mensual - nueva_cuota_mensual
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error en simulación: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class CuotaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de cuotas"""
    queryset = Cuota.objects.all()
    serializer_class = CuotaSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CuotaDetailSerializer
        return CuotaSerializer

    def get_queryset(self):
        queryset = Cuota.objects.all()
        
        # Filtros
        financiamiento_id = self.request.query_params.get('financiamiento_id', None)
        estado = self.request.query_params.get('estado', None)
        atrasadas = self.request.query_params.get('atrasadas', None)
        
        if financiamiento_id:
            queryset = queryset.filter(financiamiento_id=financiamiento_id)
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        if atrasadas == 'true':
            queryset = queryset.filter(estado='atrasada')
        
        return queryset.order_by('financiamiento', 'numero_cuota')

    def perform_create(self, serializer):
        """Sobrescribir create para asignar usuario"""
        serializer.save(creado_por=self.request.user)

    def perform_update(self, serializer):
        """Sobrescribir update para asignar usuario"""
        serializer.save(actualizado_por=self.request.user)

    @action(detail=False, methods=['get'])
    def atrasadas(self, request):
        """Obtener cuotas atrasadas"""
        cuotas = self.get_queryset().filter(estado='atrasada')
        serializer = self.get_serializer(cuotas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """Obtener cuotas pendientes"""
        cuotas = self.get_queryset().filter(estado='pendiente')
        serializer = self.get_serializer(cuotas, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def calcular_mora(self, request, pk=None):
        """Calcular mora para una cuota específica"""
        cuota = self.get_object()
        cuota.calcular_mora()
        serializer = self.get_serializer(cuota)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def pagos(self, request, pk=None):
        """Obtener pagos de una cuota"""
        cuota = self.get_object()
        pagos = cuota.pagos.all()
        serializer = PagoSerializer(pagos, many=True)
        return Response(serializer.data)


class PagoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar pagos"""
    queryset = Pago.objects.all()
    serializer_class = PagoSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PagoDetailSerializer
        return PagoSerializer

    def get_queryset(self):
        queryset = Pago.objects.all()
        
        # Filtros
        financiamiento_id = self.request.query_params.get('financiamiento_id', None)
        cuota_id = self.request.query_params.get('cuota_id', None)
        fecha_desde = self.request.query_params.get('fecha_desde', None)
        fecha_hasta = self.request.query_params.get('fecha_hasta', None)
        
        if financiamiento_id:
            queryset = queryset.filter(financiamiento_id=financiamiento_id)
        
        if cuota_id:
            queryset = queryset.filter(cuota_id=cuota_id)
        
        if fecha_desde:
            queryset = queryset.filter(fecha_pago__gte=fecha_desde)
        
        if fecha_hasta:
            queryset = queryset.filter(fecha_pago__lte=fecha_hasta)
        
        return queryset.order_by('-fecha_pago', '-fecha_creacion')

    def perform_create(self, serializer):
        """Sobrescribir create para asignar usuario y validar cuota"""
        cuota_id = serializer.validated_data.get('cuota_id')
        financiamiento_id = serializer.validated_data.get('financiamiento_id')
        
        # Obtener cuota y financiamiento
        cuota = Cuota.objects.get(id=cuota_id)
        financiamiento = Financiamiento.objects.get(id=financiamiento_id)
        
        # Validar que la cuota pertenece al financiamiento
        if cuota.financiamiento_id != financiamiento.id:
            raise serializers.ValidationError("La cuota no pertenece al financiamiento especificado")
        
        serializer.save(creado_por=self.request.user)

    @action(detail=False, methods=['get'])
    def por_fecha(self, request):
        """Obtener pagos por rango de fechas"""
        fecha_desde = request.query_params.get('fecha_desde', None)
        fecha_hasta = request.query_params.get('fecha_hasta', None)
        
        if not fecha_desde or not fecha_hasta:
            return Response(
                {'error': 'Se requieren fecha_desde y fecha_hasta'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        pagos = self.get_queryset().filter(
            fecha_pago__range=[fecha_desde, fecha_hasta]
        )
        serializer = self.get_serializer(pagos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def resumen_mensual(self, request):
        """Obtener resumen de pagos del mes actual"""
        from datetime import datetime
        
        hoy = datetime.now()
        primer_dia_mes = hoy.replace(day=1)
        ultimo_dia_mes = (hoy.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        pagos_mes = self.get_queryset().filter(
            fecha_pago__range=[primer_dia_mes.date(), ultimo_dia_mes.date()]
        )
        
        total_cobrado = pagos_mes.aggregate(
            total=Sum('monto_total')
        )['total'] or Decimal('0.00')
        
        total_capital = pagos_mes.aggregate(
            total=Sum('monto_capital')
        )['total'] or Decimal('0.00')
        
        total_interes = pagos_mes.aggregate(
            total=Sum('monto_interes')
        )['total'] or Decimal('0.00')
        
        total_mora = pagos_mes.aggregate(
            total=Sum('monto_mora')
        )['total'] or Decimal('0.00')
        
        resumen = {
            'mes': hoy.strftime('%B %Y'),
            'total_pagos': pagos_mes.count(),
            'total_cobrado': total_cobrado,
            'total_capital': total_capital,
            'total_interes': total_interes,
            'total_mora': total_mora,
        }
        
        return Response(resumen)

    @action(detail=False, methods=['post'])
    def multiples_pagos(self, request):
        """
        Crear múltiples pagos en una sola petición
        """
        pagos_data = request.data.get('pagos', [])
        
        if not pagos_data:
            return Response(
                {'error': 'Se requiere el campo "pagos" con una lista de pagos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not isinstance(pagos_data, list):
            return Response(
                {'error': 'El campo "pagos" debe ser una lista'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(pagos_data) == 0:
            return Response(
                {'error': 'La lista de pagos no puede estar vacía'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(pagos_data) > 50:  # Límite de seguridad
            return Response(
                {'error': 'No se pueden procesar más de 50 pagos a la vez'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        pagos_creados = []
        errores = []
        
        try:
            with transaction.atomic():
                for i, pago_data in enumerate(pagos_data):
                    try:
                        # Validar datos del pago
                        serializer = self.get_serializer(data=pago_data)
                        if serializer.is_valid():
                            pago = serializer.save()
                            pagos_creados.append({
                                'indice': i,
                                'pago': self.get_serializer(pago).data,
                                'estado': 'creado'
                            })
                        else:
                            errores.append({
                                'indice': i,
                                'error': serializer.errors,
                                'estado': 'error'
                            })
                    except Exception as e:
                        errores.append({
                            'indice': i,
                            'error': str(e),
                            'estado': 'error'
                        })
                
                # Si hay errores, hacer rollback
                if errores:
                    raise Exception("Errores en algunos pagos")
                
                return Response({
                    'mensaje': f'Se crearon {len(pagos_creados)} pagos exitosamente',
                    'pagos_creados': pagos_creados,
                    'total_procesados': len(pagos_data),
                    'exitosos': len(pagos_creados),
                    'errores': len(errores)
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response({
                'error': 'Error al procesar los pagos',
                'mensaje': str(e),
                'pagos_creados': pagos_creados,
                'errores_detallados': errores,
                'total_procesados': len(pagos_data),
                'exitosos': len(pagos_creados),
                'errores': len(errores)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def pagos_por_financiamiento(self, request):
        """
        Crear múltiples pagos para un financiamiento específico
        """
        financiamiento_id = request.data.get('financiamiento_id')
        pagos_data = request.data.get('pagos', [])
        
        if not financiamiento_id:
            return Response(
                {'error': 'Se requiere financiamiento_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not pagos_data:
            return Response(
                {'error': 'Se requiere el campo "pagos" con una lista de pagos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar que el financiamiento existe
        try:
            financiamiento = Financiamiento.objects.get(id=financiamiento_id)
        except Financiamiento.DoesNotExist:
            return Response(
                {'error': f'Financiamiento con ID {financiamiento_id} no existe'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        pagos_creados = []
        errores = []
        
        try:
            with transaction.atomic():
                for i, pago_data in enumerate(pagos_data):
                    try:
                        # Agregar financiamiento_id si no está presente
                        if 'financiamiento_id' not in pago_data:
                            pago_data['financiamiento_id'] = financiamiento_id
                        
                        # Validar que el financiamiento_id coincida
                        if pago_data.get('financiamiento_id') != financiamiento_id:
                            errores.append({
                                'indice': i,
                                'error': 'financiamiento_id no coincide con el especificado',
                                'estado': 'error'
                            })
                            continue
                        
                        serializer = self.get_serializer(data=pago_data)
                        if serializer.is_valid():
                            pago = serializer.save()
                            pagos_creados.append({
                                'indice': i,
                                'pago': self.get_serializer(pago).data,
                                'estado': 'creado'
                            })
                        else:
                            errores.append({
                                'indice': i,
                                'error': serializer.errors,
                                'estado': 'error'
                            })
                    except Exception as e:
                        errores.append({
                            'indice': i,
                            'error': str(e),
                            'estado': 'error'
                        })
                
                # Si hay errores, hacer rollback
                if errores:
                    raise Exception("Errores en algunos pagos")
                
                return Response({
                    'mensaje': f'Se crearon {len(pagos_creados)} pagos para el financiamiento {financiamiento_id}',
                    'financiamiento_id': financiamiento_id,
                    'pagos_creados': pagos_creados,
                    'total_procesados': len(pagos_data),
                    'exitosos': len(pagos_creados),
                    'errores': len(errores)
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response({
                'error': 'Error al procesar los pagos',
                'mensaje': str(e),
                'financiamiento_id': financiamiento_id,
                'pagos_creados': pagos_creados,
                'errores': errores,
                'total_procesados': len(pagos_data),
                'exitosos': len(pagos_creados),
                'errores': len(errores)
            }, status=status.HTTP_400_BAD_REQUEST)


class ConfiguracionPagoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de configuraciones de pago"""
    queryset = ConfiguracionPago.objects.all()
    serializer_class = ConfiguracionPagoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ConfiguracionPago.objects.filter(activo=True).order_by('tipo_pago', 'dia_pago')

    @action(detail=False, methods=['get'])
    def activas(self, request):
        """Obtener configuraciones activas"""
        configuraciones = self.get_queryset()
        serializer = self.get_serializer(configuraciones, many=True)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calcular_moras_generales(request):
    """Calcular moras para todos los financiamientos"""
    try:
        # Obtener todas las cuotas pendientes
        cuotas_pendientes = Cuota.objects.filter(estado='pendiente')
        financiamientos_actualizados = set()
        
        for cuota in cuotas_pendientes:
            estado_anterior = cuota.estado
            cuota.calcular_mora()
            
            if cuota.estado != estado_anterior:
                financiamientos_actualizados.add(cuota.financiamiento.id)
        
        # Actualizar estado de financiamientos
        for financiamiento_id in financiamientos_actualizados:
            financiamiento = Financiamiento.objects.get(id=financiamiento_id)
            if financiamiento.cuotas.filter(estado='atrasada').exists():
                financiamiento.estado = 'en_mora'
                financiamiento.save()
        
        return Response({
            'mensaje': f'Se calcularon moras para {len(cuotas_pendientes)} cuotas',
            'financiamientos_actualizados': len(financiamientos_actualizados)
        })
    
    except Exception as e:
        return Response(
            {'error': f'Error al calcular moras: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reporte_financiamiento(request):
    """Generar reporte de financiamiento"""
    try:
        # Parámetros del reporte
        fecha_desde = request.query_params.get('fecha_desde', None)
        fecha_hasta = request.query_params.get('fecha_hasta', None)
        manzana = request.query_params.get('manzana', None)
        
        # Filtrar financiamientos
        financiamientos = Financiamiento.objects.all()
        
        if fecha_desde:
            financiamientos = financiamientos.filter(fecha_creacion__date__gte=fecha_desde)
        
        if fecha_hasta:
            financiamientos = financiamientos.filter(fecha_creacion__date__lte=fecha_hasta)
        
        if manzana:
            financiamientos = financiamientos.filter(lote__manzana__nombre__icontains=manzana)
        
        # Calcular estadísticas
        total_financiamientos = financiamientos.count()
        total_cobrado = financiamientos.aggregate(
            total=Sum('capital_cancelado') + Sum('enganche')
        )['total'] or Decimal('0.00')
        
        total_pendiente = financiamientos.aggregate(
            total=Sum('saldo') - Sum('capital_cancelado')
        )['total'] or Decimal('0.00')
        
        cuotas_atrasadas = Cuota.objects.filter(
            financiamiento__in=financiamientos,
            estado='atrasada'
        ).count()
        
        reporte = {
            'periodo': {
                'fecha_desde': fecha_desde,
                'fecha_hasta': fecha_hasta
            },
            'filtros': {
                'manzana': manzana
            },
            'estadisticas': {
                'total_financiamientos': total_financiamientos,
                'total_cobrado': total_cobrado,
                'total_pendiente': total_pendiente,
                'cuotas_atrasadas': cuotas_atrasadas
            },
            'financiamientos': FinanciamientoListSerializer(financiamientos, many=True).data
        }
        
        return Response(reporte)
    
    except Exception as e:
        return Response(
            {'error': f'Error al generar reporte: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
