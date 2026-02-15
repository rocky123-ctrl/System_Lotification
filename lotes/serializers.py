from rest_framework import serializers
from .models import Manzana, Lote, HistorialLote


class ManzanaSerializer(serializers.ModelSerializer):
    """Serializer para manzanas"""
    total_lotes = serializers.SerializerMethodField()
    lotes_disponibles = serializers.SerializerMethodField()
    
    class Meta:
        model = Manzana
        fields = '__all__'
    
    def get_total_lotes(self, obj):
        return obj.lotes.count()
    
    def get_lotes_disponibles(self, obj):
        return obj.lotes.filter(estado='disponible', activo=True).count()


class LoteSerializer(serializers.ModelSerializer):
    """Serializer para lotes"""
    manzana_nombre = serializers.CharField(source='manzana.nombre', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    saldo_financiar = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    # Campos formateados
    valor_total_formateado = serializers.CharField(read_only=True)
    enganche_formateado = serializers.CharField(read_only=True)
    costo_instalacion_formateado = serializers.CharField(read_only=True)
    saldo_financiar_formateado = serializers.CharField(read_only=True)
    cuota_mensual_formateada = serializers.CharField(read_only=True)
    metros_cuadrados_formateados = serializers.CharField(read_only=True)
    
    class Meta:
        model = Lote
        fields = '__all__'


class LoteListSerializer(serializers.ModelSerializer):
    """Serializer para listar lotes con información básica"""
    manzana_nombre = serializers.CharField(source='manzana.nombre', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    saldo_financiar = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    # Campos formateados para la tabla
    valor_total_formateado = serializers.CharField(read_only=True)
    enganche_formateado = serializers.CharField(read_only=True)
    costo_instalacion_formateado = serializers.CharField(read_only=True)
    saldo_financiar_formateado = serializers.CharField(read_only=True)
    cuota_mensual_formateada = serializers.CharField(read_only=True)
    metros_cuadrados_formateados = serializers.CharField(read_only=True)
    
    class Meta:
        model = Lote
        fields = [
            'id', 'manzana', 'manzana_nombre', 'numero_lote', 'metros_cuadrados', 
            'metros_cuadrados_formateados', 'valor_total', 'valor_total_formateado',
            'enganche', 'enganche_formateado', 'costo_instalacion', 'costo_instalacion_formateado',
            'saldo_financiar', 'saldo_financiar_formateado', 'plazo_meses', 
            'cuota_mensual', 'cuota_mensual_formateada', 'estado', 'estado_display',
            'activo', 'fecha_creacion', 'fecha_actualizacion'
        ]


class LoteCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear lotes"""
    
    class Meta:
        model = Lote
        fields = [
            'manzana', 'numero_lote', 'metros_cuadrados', 'valor_total', 
            'enganche', 'costo_instalacion', 'plazo_meses', 'cuota_mensual', 'estado'
        ]
    
    def validate(self, attrs):
        # Validar que el enganche no sea mayor al valor total
        if attrs.get('enganche', 0) >= attrs.get('valor_total', 0):
            raise serializers.ValidationError("El enganche no puede ser mayor o igual al valor total")
        
        # Validar que el saldo a financiar sea positivo
        saldo = attrs.get('valor_total', 0) - attrs.get('enganche', 0) - attrs.get('costo_instalacion', 0)
        if saldo <= 0:
            raise serializers.ValidationError("El saldo a financiar debe ser mayor a 0")
        
        return attrs


class LoteUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar lotes"""
    
    class Meta:
        model = Lote
        fields = [
            'metros_cuadrados', 'valor_total', 'enganche', 'costo_instalacion', 
            'plazo_meses', 'cuota_mensual', 'estado', 'activo'
        ]
    
    def validate(self, attrs):
        # Obtener valores actuales si no se proporcionan
        instance = self.instance
        valor_total = attrs.get('valor_total', instance.valor_total if instance else 0)
        enganche = attrs.get('enganche', instance.enganche if instance else 0)
        costo_instalacion = attrs.get('costo_instalacion', instance.costo_instalacion if instance else 0)
        
        # Validar que el enganche no sea mayor al valor total
        if enganche >= valor_total:
            raise serializers.ValidationError("El enganche no puede ser mayor o igual al valor total")
        
        # Validar que el saldo a financiar sea positivo
        saldo = valor_total - enganche - costo_instalacion
        if saldo <= 0:
            raise serializers.ValidationError("El saldo a financiar debe ser mayor a 0")
        
        return attrs


class HistorialLoteSerializer(serializers.ModelSerializer):
    """Serializer para historial de lotes"""
    lote_numero = serializers.CharField(source='lote.numero_lote', read_only=True)
    manzana_nombre = serializers.CharField(source='lote.manzana.nombre', read_only=True)
    cambiado_por_nombre = serializers.CharField(source='cambiado_por.get_full_name', read_only=True)
    
    class Meta:
        model = HistorialLote
        fields = '__all__'
        read_only_fields = ['fecha_cambio']


class LoteEstadisticasSerializer(serializers.Serializer):
    """Serializer para estadísticas de lotes"""
    total_lotes = serializers.IntegerField()
    lotes_disponibles = serializers.IntegerField()
    lotes_reservados = serializers.IntegerField()
    lotes_vendidos = serializers.IntegerField()
    lotes_en_proceso = serializers.IntegerField()
    lotes_cancelados = serializers.IntegerField()
    valor_total_inventario = serializers.DecimalField(max_digits=15, decimal_places=2)
    valor_total_vendido = serializers.DecimalField(max_digits=15, decimal_places=2)
    promedio_metros_cuadrados = serializers.DecimalField(max_digits=8, decimal_places=2)
    promedio_valor_lote = serializers.DecimalField(max_digits=12, decimal_places=2)


class LoteFiltroSerializer(serializers.Serializer):
    """Serializer para filtros de lotes"""
    manzana = serializers.CharField(required=False)
    estado = serializers.CharField(required=False)
    precio_min = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    precio_max = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    metros_min = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)
    metros_max = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)
    solo_disponibles = serializers.BooleanField(default=False)
