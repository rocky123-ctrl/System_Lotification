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
    lote_estado_disponibilidad = serializers.ReadOnlyField(source='lote.estado_disponibilidad')

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
        acepta_instalacion = data.get('acepta_instalacion', self.instance.acepta_instalacion if self.instance else False)
        
        lote = data.get('lote', self.instance.lote if self.instance else None)
        if lote:
            data['valor_lote'] = lote.valor_total
        
        valor_lote = data.get('valor_lote', self.instance.valor_lote if self.instance else Decimal('0.00'))
        costo_instalacion = lote.costo_instalacion if (lote and acepta_instalacion) else Decimal('0.00')
        enganche = data.get('enganche', self.instance.enganche if self.instance else Decimal('0.00'))
        descuento = data.get('descuento', self.instance.descuento if self.instance else Decimal('0.00'))
        tipo_pago = data.get('tipo_pago', self.instance.tipo_pago if self.instance else None)
        plazo = data.get('plazo_meses', self.instance.plazo_meses if self.instance else 0)
        tasa = data.get('tasa_interes_anual', self.instance.tasa_interes_anual if self.instance else 0)
        
        monto_maximo = valor_lote + costo_instalacion
        
        if (enganche + descuento) > monto_maximo:
            raise serializers.ValidationError("El pago inicial y el descuento superan el valor del lote (incluyendo instalación si aplica).")
        
        if tipo_pago == 'CONTADO':
            if (enganche + descuento) != monto_maximo:
                raise serializers.ValidationError("En una venta al contado, el monto pagado más el descuento debe ser exactamente igual al valor total del lote.")
            data['plazo_meses'] = 0
            data['tasa_interes_anual'] = 0
        elif tipo_pago == 'FINANCIADO':
            if enganche <= 0:
                raise serializers.ValidationError({"enganche": "El enganche debe ser mayor a 0 para ventas financiadas."})
            if plazo <= 0:
                raise serializers.ValidationError({"plazo_meses": "El plazo en meses debe ser mayor a 0 para ventas financiadas."})
            if tasa <= 0:
                raise serializers.ValidationError({"tasa_interes_anual": "La tasa de interés debe ser mayor a 0 para ventas financiadas."})
            
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
        acepta_instalacion = data.get('acepta_instalacion', self.instance.acepta_instalacion if self.instance else False)
        
        lote = data.get('lote', self.instance.lote if self.instance else None)
        if lote:
            data['valor_lote'] = lote.valor_total
        
        valor_lote = data.get('valor_lote', self.instance.valor_lote if self.instance else Decimal('0.00'))
        costo_instalacion = lote.costo_instalacion if (lote and acepta_instalacion) else Decimal('0.00')
        enganche = data.get('enganche', self.instance.enganche if self.instance else Decimal('0.00'))
        descuento = data.get('descuento', self.instance.descuento if self.instance else Decimal('0.00'))
        tipo_pago = data.get('tipo_pago', self.instance.tipo_pago if self.instance else None)
        plazo = data.get('plazo_meses', self.instance.plazo_meses if self.instance else 0)
        tasa = data.get('tasa_interes_anual', self.instance.tasa_interes_anual if self.instance else 0)
        
        monto_maximo = valor_lote + costo_instalacion
        
        if (enganche + descuento) > monto_maximo:
            raise serializers.ValidationError("El pago inicial y el descuento superan el valor del lote (incluyendo instalación si aplica).")
        
        if tipo_pago == 'CONTADO':
            if (enganche + descuento) != monto_maximo:
                raise serializers.ValidationError("En una venta al contado, el monto pagado más el descuento debe ser exactamente igual al valor total del lote.")
            data['plazo_meses'] = 0
            data['tasa_interes_anual'] = 0
        elif tipo_pago == 'FINANCIADO':
            if enganche <= 0:
                raise serializers.ValidationError({"enganche": "El enganche debe ser mayor a 0 para ventas financiadas."})
            if plazo <= 0:
                raise serializers.ValidationError({"plazo_meses": "El plazo en meses debe ser mayor a 0 para ventas financiadas."})
            if tasa <= 0:
                raise serializers.ValidationError({"tasa_interes_anual": "La tasa de interés debe ser mayor a 0 para ventas financiadas."})
            
        return data

