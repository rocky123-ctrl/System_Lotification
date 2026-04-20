from rest_framework import serializers
from .models import Venta, LiquidacionComision, Cotizacion
from decimal import Decimal

class VentaSerializer(serializers.ModelSerializer):
    vendedor_nombre = serializers.SerializerMethodField()
    cliente_nombre = serializers.SerializerMethodField()
    lote_numero = serializers.ReadOnlyField(source='lote.numero_lote')
    lote_manzana = serializers.ReadOnlyField(source='lote.manzana.nombre')
    lotificacion_nombre = serializers.ReadOnlyField(source='lote.manzana.lotificacion.nombre')
    lotificacion_id = serializers.ReadOnlyField(source='lote.manzana.lotificacion_id')
    plano_svg_id = serializers.ReadOnlyField(source='lote.plano_svg_id')
    lote_identificador = serializers.ReadOnlyField(source='lote.identificador')
    lote_costo_instalacion = serializers.ReadOnlyField(source='lote.costo_instalacion')
    lote_valor_total = serializers.ReadOnlyField(source='lote.valor_total')

    class Meta:
        model = Venta
        fields = '__all__'
        read_only_fields = [
            'valor_lote', 
            'monto_financiar', 
            'total_pagar_contado', 
            'vendedor', 
            'comision_monto'
        ]

    def get_vendedor_nombre(self, obj):
        if obj.vendedor:
            return f"{obj.vendedor.first_name} {obj.vendedor.last_name}".strip() or obj.vendedor.username
        return "N/A"

    def get_cliente_nombre(self, obj):
        if obj.cliente:
            return f"{obj.cliente.nombres} {obj.cliente.apellidos}".strip()
        return "N/A"

    def validate(self, data):
        # El frontend puede indicar si se incluye o no el costo de instalación
        # Ahora usamos el campo acepta_instalacion del modelo
        acepta_instalacion = data.get('acepta_instalacion', False)
        
        # Tomamos el valor real del lote desde la base de datos
        lote = data.get('lote')
        if lote:
            if acepta_instalacion:
                data['valor_lote'] = lote.valor_total
            else:
                data['valor_lote'] = lote.valor_total - lote.costo_instalacion
        
        valor_lote = data.get('valor_lote', Decimal('0.00'))
        enganche = data.get('enganche', Decimal('0.00'))
        descuento = data.get('descuento', Decimal('0.00'))
        tipo_pago = data.get('tipo_pago')
        plazo = data.get('plazo_meses', 0)
        
        monto_calculado = valor_lote - enganche - descuento
        
        if monto_calculado < 0:
            raise serializers.ValidationError("El enganche y descuento superan el valor del lote.")
        
        if tipo_pago == 'FINANCIADO':
            if plazo <= 0:
                raise serializers.ValidationError({"plazo_meses": "El plazo debe ser mayor a 0 para ventas financiadas."})
        elif tipo_pago == 'CONTADO':
            # Si es Al Contado, el backend ignora plazo e interés
            data['plazo_meses'] = 0
            data['tasa_interes_anual'] = 0
            
        return data

class LiquidacionComisionSerializer(serializers.ModelSerializer):
    vendedor_nombre = serializers.SerializerMethodField()
    fecha_venta = serializers.ReadOnlyField(source='venta.fecha_creacion')
    lote_numero = serializers.ReadOnlyField(source='venta.lote.numero_lote')

    class Meta:
        model = LiquidacionComision
        fields = [
            'id', 'venta', 'vendedor', 'vendedor_nombre', 
            'fecha_venta', 'lote_numero', 'monto_pagado', 
            'fecha_pago', 'es_pago_inmediato', 'referencia_pago', 
            'estado_pago', 'fecha_creacion'
        ]
        read_only_fields = ['id', 'venta', 'vendedor', 'monto_pagado', 'fecha_creacion', 'estado_pago']

    def get_vendedor_nombre(self, obj):
        if hasattr(obj.vendedor, 'empleado') and obj.vendedor.empleado:
            return f"{obj.vendedor.empleado.nombre} {obj.vendedor.empleado.apellido or ''}".strip()
        return f"{obj.vendedor.first_name} {obj.vendedor.last_name}".strip() or obj.vendedor.username

import math

class CotizacionSerializer(serializers.ModelSerializer):
    vendedor_nombre = serializers.SerializerMethodField()
    cliente_nombre = serializers.SerializerMethodField()
    lote_numero = serializers.ReadOnlyField(source='lote.numero_lote')
    lote_manzana = serializers.ReadOnlyField(source='lote.manzana.nombre')
    lotificacion_nombre = serializers.ReadOnlyField(source='lote.manzana.lotificacion.nombre')
    cuota_mensual_estimada = serializers.SerializerMethodField()

    class Meta:
        model = Cotizacion
        fields = '__all__'
        read_only_fields = [
            'valor_lote', 
            'monto_financiar', 
            'total_pagar_contado', 
            'vendedor'
        ]

    def get_vendedor_nombre(self, obj):
        if obj.vendedor:
            return f"{obj.vendedor.first_name} {obj.vendedor.last_name}".strip() or obj.vendedor.username
        return "N/A"

    def get_cliente_nombre(self, obj):
        if obj.cliente:
            return f"{obj.cliente.nombres} {obj.cliente.apellidos}".strip()
        elif obj.nombre_prospecto:
            return obj.nombre_prospecto
        return "N/A"

    def get_cuota_mensual_estimada(self, obj):
        if obj.tipo_pago != 'FINANCIADO' or not obj.monto_financiar or obj.plazo_meses <= 0:
            return 0.0

        tasa_anual_decimal = float(obj.tasa_interes_anual) / 100.0
        tasa_mensual_efectiva = math.pow(1 + tasa_anual_decimal, 1 / 12) - 1
        vf_float = float(obj.monto_financiar)

        if tasa_mensual_efectiva > 0:
            numerador = vf_float * tasa_mensual_efectiva * math.pow(1 + tasa_mensual_efectiva, obj.plazo_meses)
            denominador = math.pow(1 + tasa_mensual_efectiva, obj.plazo_meses) - 1
            return round(numerador / denominador, 2)
        else:
            return round(vf_float / obj.plazo_meses, 2)

    def validate(self, data):
        acepta_instalacion = data.get('acepta_instalacion', False)
        lote = data.get('lote')
        if lote:
            if acepta_instalacion:
                data['valor_lote'] = lote.valor_total
            else:
                data['valor_lote'] = lote.valor_total - lote.costo_instalacion
        
        valor_lote = data.get('valor_lote', Decimal('0.00'))
        enganche = data.get('enganche', Decimal('0.00'))
        descuento = data.get('descuento', Decimal('0.00'))
        tipo_pago = data.get('tipo_pago')
        plazo = data.get('plazo_meses', 0)
        
        monto_calculado = valor_lote - enganche - descuento
        
        if monto_calculado < 0:
            raise serializers.ValidationError("El enganche y descuento superan el valor del lote.")
        
        if tipo_pago == 'FINANCIADO':
            if plazo <= 0:
                raise serializers.ValidationError({"plazo_meses": "El plazo debe ser mayor a 0 para cotizaciones financiadas."})
        elif tipo_pago == 'CONTADO':
            data['plazo_meses'] = 0
            data['tasa_interes_anual'] = 0
            
        return data
