from rest_framework import serializers
from .models import Financiamiento, Cuota, Pago, ConfiguracionPago, PagoCapital
from lotes.serializers import LoteSerializer, ManzanaSerializer
from lotes.models import Lote
from decimal import Decimal
from django.db import models


class ConfiguracionPagoSerializer(serializers.ModelSerializer):
    """Serializer para configuración de pagos"""
    
    class Meta:
        model = ConfiguracionPago
        fields = '__all__'


class CuotaSerializer(serializers.ModelSerializer):
    """Serializer para cuotas"""
    financiamiento_id = serializers.IntegerField(write_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    mora_atraso_formateada = serializers.SerializerMethodField()
    
    class Meta:
        model = Cuota
        fields = '__all__'
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion', 'creado_por', 'actualizado_por']
    
    def get_mora_atraso_formateada(self, obj):
        """Formatear mora de atraso"""
        if obj.mora_atraso > 0:
            return f"Q {obj.mora_atraso:,.2f}"
        return "Q 0.00"


class PagoSerializer(serializers.ModelSerializer):
    """Serializer para pagos"""
    cuota_id = serializers.IntegerField(write_only=True)
    financiamiento_id = serializers.IntegerField(write_only=True)
    monto_total_formateado = serializers.SerializerMethodField()
    
    class Meta:
        model = Pago
        fields = '__all__'
        read_only_fields = ['fecha_creacion', 'creado_por']
        extra_kwargs = {
            'referencia_pago': {'required': False, 'allow_blank': True, 'allow_null': True}
        }
    
    def get_monto_total_formateado(self, obj):
        """Formatear monto total"""
        return f"Q {obj.monto_total:,.2f}"
    
    def validate(self, data):
        """Validar que el pago no exceda el monto de la cuota"""
        cuota_id = data.get('cuota_id')
        monto_total = data.get('monto_total')
        
        if cuota_id and monto_total:
            try:
                cuota = Cuota.objects.get(id=cuota_id)
                if monto_total > cuota.monto_total + cuota.mora_atraso:
                    raise serializers.ValidationError(
                        "El monto del pago no puede exceder el monto de la cuota más la mora"
                    )
            except Cuota.DoesNotExist:
                raise serializers.ValidationError(
                    f"La cuota con ID {cuota_id} no existe"
                )
        
        return data


class PagoCapitalSerializer(serializers.ModelSerializer):
    """Serializer para pagos a capital"""
    financiamiento_info = serializers.SerializerMethodField()
    saldo_anterior = serializers.SerializerMethodField()
    saldo_nuevo = serializers.SerializerMethodField()
    
    class Meta:
        model = PagoCapital
        fields = '__all__'
        read_only_fields = ['fecha_creacion', 'creado_por', 'referencia_pago']
        extra_kwargs = {
            'referencia_pago': {'required': False, 'allow_blank': True, 'allow_null': True}
        }
    
    def get_financiamiento_info(self, obj):
        """Obtener información básica del financiamiento"""
        return {
            'id': obj.financiamiento.id,
            'lote_numero': obj.financiamiento.lote.numero_lote,
            'manzana': obj.financiamiento.lote.manzana.nombre if obj.financiamiento.lote.manzana else None,
            'promitente_comprador': obj.financiamiento.promitente_comprador,
            'saldo_restante': obj.financiamiento.saldo_restante,
            'cuotas_pendientes': obj.financiamiento.cuotas_pendientes
        }
    
    def get_saldo_anterior(self, obj):
        """Obtener saldo antes del pago a capital"""
        return obj.financiamiento.saldo_restante + obj.monto
    
    def get_saldo_nuevo(self, obj):
        """Obtener saldo después del pago a capital"""
        return obj.financiamiento.saldo_restante
    
    def validate(self, data):
        """Validar el pago a capital"""
        financiamiento = data.get('financiamiento')
        monto = data.get('monto')
        
        if financiamiento and monto:
            # Verificar que el financiamiento esté activo
            if financiamiento.estado != 'activo':
                raise serializers.ValidationError("Solo se pueden hacer pagos a capital en financiamientos activos")
            
            # Verificar que el monto no exceda el saldo restante
            if monto > financiamiento.saldo_restante:
                raise serializers.ValidationError(f"El monto del pago a capital (Q{monto}) no puede exceder el saldo restante (Q{financiamiento.saldo_restante})")
            
            # Verificar que el monto sea mayor a 0
            if monto <= 0:
                raise serializers.ValidationError("El monto del pago a capital debe ser mayor a 0")
        
        return data


class PagoCapitalCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear pagos a capital"""
    financiamiento_id = serializers.IntegerField(write_only=True)
    financiamiento_info = serializers.SerializerMethodField()
    ahorro_intereses = serializers.SerializerMethodField()
    
    class Meta:
        model = PagoCapital
        fields = ['financiamiento_id', 'monto', 'fecha_pago', 'concepto', 'financiamiento_info', 'ahorro_intereses']
        read_only_fields = ['financiamiento_info', 'ahorro_intereses']
    
    def get_financiamiento_info(self, obj):
        """Obtener información del financiamiento"""
        return {
            'id': obj.financiamiento.id,
            'lote_numero': obj.financiamiento.lote.numero_lote,
            'manzana': obj.financiamiento.lote.manzana.nombre if obj.financiamiento.lote.manzana else None,
            'promitente_comprador': obj.financiamiento.promitente_comprador,
            'saldo_restante': obj.financiamiento.saldo_restante,
            'cuotas_pendientes': obj.financiamiento.cuotas_pendientes,
            'cuota_mensual_actual': obj.financiamiento.cuota_mensual
        }
    
    def get_ahorro_intereses(self, obj):
        """Calcular ahorro estimado en intereses usando la tasa anual de configuración"""
        cuotas_pendientes = obj.financiamiento.cuotas_pendientes
        if cuotas_pendientes > 0:
            from configuracion.models import ConfiguracionGeneral
            config = ConfiguracionGeneral.objects.first()
            if config and config.tasa_anual > 0:
                # Usar la tasa anual de la configuración
                tasa_anual = config.tasa_anual
                # Convertir a mensual para el cálculo
                tasa_anual_decimal = tasa_anual / Decimal('100')
                tasa_mensual_decimal = (Decimal('1') + tasa_anual_decimal) ** (Decimal('1') / Decimal('12')) - Decimal('1')
                tasa_mensual = tasa_mensual_decimal * Decimal('100')
                
                # Cálculo del ahorro estimado
                ahorro_estimado = obj.monto * (tasa_mensual / 100) * cuotas_pendientes / 2
                return ahorro_estimado
            else:
                # Fallback si no hay configuración
                return Decimal('0.00')
        return Decimal('0.00')
    
    def create(self, validated_data):
        """Crear el pago a capital"""
        financiamiento_id = validated_data.pop('financiamiento_id')
        
        try:
            financiamiento = Financiamiento.objects.get(id=financiamiento_id)
        except Financiamiento.DoesNotExist:
            raise serializers.ValidationError(f"El financiamiento con ID {financiamiento_id} no existe")
        
        # Crear el pago a capital
        pago_capital = PagoCapital.objects.create(
            financiamiento=financiamiento,
            **validated_data
        )
        
        return pago_capital


class FinanciamientoSerializer(serializers.ModelSerializer):
    """Serializer para financiamientos"""
    lote_info = serializers.SerializerMethodField()
    pagos_capital = serializers.SerializerMethodField()
    total_pagos_capital = serializers.SerializerMethodField()
    ahorro_intereses_estimado = serializers.SerializerMethodField()
    
    class Meta:
        model = Financiamiento
        fields = '__all__'
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion', 'creado_por', 'actualizado_por']
    
    def get_lote_info(self, obj):
        """Obtener información del lote"""
        return {
            'id': obj.lote.id,
            'numero_lote': obj.lote.numero_lote,
            'manzana': obj.lote.manzana.nombre if obj.lote.manzana else None,
            'metros_cuadrados': obj.lote.metros_cuadrados,
            'valor_total': obj.lote.valor_total
        }
    
    def get_pagos_capital(self, obj):
        """Obtener pagos a capital del financiamiento"""
        pagos = obj.pagos_capital.all()[:5]  # Últimos 5 pagos
        return PagoCapitalSerializer(pagos, many=True).data
    
    def get_total_pagos_capital(self, obj):
        """Obtener total de pagos a capital"""
        return obj.pagos_capital.aggregate(
            total=models.Sum('monto')
        )['total'] or Decimal('0.00')
    
    def get_ahorro_intereses_estimado(self, obj):
        """Calcular ahorro estimado en intereses por pagos a capital usando la tasa anual"""
        total_pagos_capital = self.get_total_pagos_capital(obj)
        if total_pagos_capital > 0:
            cuotas_pendientes = obj.cuotas_pendientes
            from configuracion.models import ConfiguracionGeneral
            config = ConfiguracionGeneral.objects.first()
            if config and config.tasa_anual > 0:
                # Usar la tasa anual de la configuración
                tasa_anual = config.tasa_anual
                # Convertir a mensual para el cálculo
                tasa_anual_decimal = tasa_anual / Decimal('100')
                tasa_mensual_decimal = (Decimal('1') + tasa_anual_decimal) ** (Decimal('1') / Decimal('12')) - Decimal('1')
                tasa_mensual = tasa_mensual_decimal * Decimal('100')
                
                # Cálculo del ahorro estimado
                ahorro_estimado = total_pagos_capital * (tasa_mensual / 100) * cuotas_pendientes / 2
                return ahorro_estimado
            else:
                # Fallback si no hay configuración
                return Decimal('0.00')
        return Decimal('0.00')
    
    def get_totalidad_formateada(self, obj):
        """Formatear totalidad"""
        return f"Q {obj.totalidad:,.2f}"
    
    def get_enganche_formateado(self, obj):
        """Formatear enganche"""
        return f"Q {obj.enganche:,.2f}"
    
    def get_saldo_formateado(self, obj):
        """Formatear saldo"""
        return f"Q {obj.saldo:,.2f}"
    
    def get_cuota_mensual_formateada(self, obj):
        """Formatear cuota mensual"""
        return f"Q {obj.cuota_mensual:,.2f}"
    
    def get_monto_mora_total_formateado(self, obj):
        """Formatear monto total de mora"""
        return f"Q {obj.monto_mora_total:,.2f}"
    
    def validate(self, data):
        """Validar datos del financiamiento"""
        totalidad = data.get('totalidad')
        enganche = data.get('enganche')
        
        if totalidad and enganche:
            if enganche >= totalidad:
                raise serializers.ValidationError(
                    "El enganche no puede ser mayor o igual a la totalidad"
                )
        
        return data


class FinanciamientoCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear financiamientos"""
    lote_id = serializers.IntegerField()
    
    class Meta:
        model = Financiamiento
        fields = [
            'lote_id', 'promitente_comprador', 'totalidad', 'enganche', 
            'plazo_meses', 'cuota_mensual', 'fecha_inicio_financiamiento'
        ]
    
    def create(self, validated_data):
        """Crear financiamiento y generar cuotas automáticamente"""
        from datetime import date, timedelta
        from dateutil.relativedelta import relativedelta
        
        lote_id = validated_data.pop('lote_id')
        lote = Lote.objects.get(id=lote_id)
        
        # Crear financiamiento
        financiamiento = Financiamiento.objects.create(
            lote=lote,
            **validated_data
        )
        
        # Cambiar estado del lote a "financiado"
        lote.estado = 'financiado'
        lote.save()
        
        # Generar cuotas automáticamente
        fecha_inicio = financiamiento.fecha_inicio_financiamiento
        
        # Obtener tasa mensual de la configuración general
        from configuracion.models import ConfiguracionGeneral
        try:
            configuracion = ConfiguracionGeneral.objects.first()
            tasa_mensual = configuracion.tasa_mensual if configuracion else Decimal('1.5')
        except:
            tasa_mensual = Decimal('1.5')  # Tasa por defecto
        
        # Calcular la cuota mensual usando la fórmula de amortización
        # Cuota = P * (r * (1 + r)^n) / ((1 + r)^n - 1)
        # Donde: P = principal, r = tasa mensual, n = número de cuotas
        principal = financiamiento.saldo
        tasa_decimal = tasa_mensual / 100
        num_cuotas = financiamiento.plazo_meses
        
        if tasa_decimal > 0:
            # Fórmula de amortización
            cuota_mensual = principal * (tasa_decimal * (1 + tasa_decimal)**num_cuotas) / ((1 + tasa_decimal)**num_cuotas - 1)
        else:
            # Si tasa es 0, dividir el capital entre las cuotas
            cuota_mensual = principal / num_cuotas
        
        # Actualizar la cuota_mensual en el financiamiento
        financiamiento.cuota_mensual = cuota_mensual
        financiamiento.save()
        
        # Usar tabla de amortización correcta
        saldo_pendiente = principal
        
        for i in range(1, financiamiento.plazo_meses + 1):
            # Calcular fecha de vencimiento (mes siguiente)
            fecha_vencimiento = fecha_inicio + relativedelta(months=i)
            
            # Calcular interés sobre saldo pendiente
            monto_interes = saldo_pendiente * tasa_decimal
            
            # El capital es la cuota menos el interés
            monto_capital = cuota_mensual - monto_interes
            
            # El total es la cuota mensual fija
            monto_total = cuota_mensual
            
            # Actualizar saldo pendiente para próxima iteración
            saldo_pendiente = saldo_pendiente - monto_capital
            
            # Crear cuota
            Cuota.objects.create(
                financiamiento=financiamiento,
                numero_cuota=i,
                monto_capital=monto_capital,
                monto_interes=monto_interes,
                monto_total=monto_total,
                fecha_vencimiento=fecha_vencimiento
            )
        
        return financiamiento


class FinanciamientoListSerializer(serializers.ModelSerializer):
    """Serializer para listar financiamientos"""
    lote_numero = serializers.CharField(source='lote.numero_lote', read_only=True)
    manzana_nombre = serializers.CharField(source='lote.manzana.nombre', read_only=True)
    promitente_comprador = serializers.CharField(max_length=200)
    
    # Campos calculados
    saldo_restante = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    porcentaje_pagado = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    cuotas_atrasadas = serializers.IntegerField(read_only=True)
    monto_mora_total = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = Financiamiento
        fields = [
            'id', 'lote_numero', 'manzana_nombre', 'promitente_comprador',
            'totalidad', 'enganche', 'saldo_restante', 'porcentaje_pagado',
            'cuotas_canceladas', 'cuotas_pendientes', 'cuotas_atrasadas',
            'monto_mora_total', 'estado', 'fecha_inicio_financiamiento',
            'fecha_vencimiento', 'fecha_creacion'
        ]


class FinanciamientoDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalles de financiamiento"""
    lote = LoteSerializer(read_only=True)
    cuotas = CuotaSerializer(many=True, read_only=True)
    pagos = PagoSerializer(many=True, read_only=True)
    
    # Campos calculados
    saldo_restante = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    porcentaje_pagado = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    cuotas_atrasadas = serializers.IntegerField(read_only=True)
    monto_mora_total = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = Financiamiento
        fields = '__all__'


class CuotaDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalles de cuota"""
    financiamiento = FinanciamientoSerializer(read_only=True)
    pagos = PagoSerializer(many=True, read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        model = Cuota
        fields = '__all__'


class PagoDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalles de pago"""
    cuota = CuotaSerializer(read_only=True)
    financiamiento = FinanciamientoSerializer(read_only=True)
    
    class Meta:
        model = Pago
        fields = '__all__'


class FinanciamientoEstadisticasSerializer(serializers.Serializer):
    """Serializer para estadísticas de financiamiento"""
    total_financiamientos = serializers.IntegerField()
    financiamientos_activos = serializers.IntegerField()
    financiamientos_finalizados = serializers.IntegerField()
    financiamientos_en_mora = serializers.IntegerField()
    total_cobrado = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_pendiente = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_mora = serializers.DecimalField(max_digits=15, decimal_places=2)
    cuotas_atrasadas_total = serializers.IntegerField()
