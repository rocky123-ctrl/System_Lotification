from rest_framework import serializers
from .models import Lotificacion, Manzana, Lote, HistorialLote


class LotificacionSerializer(serializers.ModelSerializer):
    """Serializer para lotificaciones"""
    plano_svg_url = serializers.SerializerMethodField()
    tiene_plano_svg = serializers.SerializerMethodField()
    created_by_nombre = serializers.SerializerMethodField()
    updated_by_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = Lotificacion
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'fecha_creacion', 'fecha_actualizacion']
    
    def get_created_by_nombre(self, obj):
        """Retornar nombre del usuario que creó la lotificación"""
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None
    
    def get_updated_by_nombre(self, obj):
        """Retornar nombre del usuario que actualizó la lotificación"""
        if obj.updated_by:
            return obj.updated_by.get_full_name() or obj.updated_by.username
        return None
    
    def get_plano_svg_url(self, obj):
        """Retornar URL completa del plano SVG si existe"""
        if obj.plano_svg:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.plano_svg.url)
            return obj.plano_svg.url
        return None
    
    def get_tiene_plano_svg(self, obj):
        """Indicar si la lotificación tiene un plano SVG"""
        return bool(obj.plano_svg)


class ManzanaSerializer(serializers.ModelSerializer):
    """Serializer para manzanas"""
    lotificacion_nombre = serializers.CharField(source='lotificacion.nombre', read_only=True)
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
    """Serializer para lotes con respuestas JSON limpias"""
    manzana_nombre = serializers.CharField(source='manzana.nombre', read_only=True)
    lotificacion_nombre = serializers.CharField(source='manzana.lotificacion.nombre', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    saldo_financiar = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    actualizado_por_nombre = serializers.CharField(source='actualizado_por.get_full_name', read_only=True)
    
    # Campos formateados
    valor_total_formateado = serializers.CharField(read_only=True)
    costo_instalacion_formateado = serializers.CharField(read_only=True)
    saldo_financiar_formateado = serializers.CharField(read_only=True)
    metros_cuadrados_formateados = serializers.CharField(read_only=True)
    
    class Meta:
        model = Lote
        fields = '__all__'


class LoteListSerializer(serializers.ModelSerializer):
    """Serializer para listar lotes con información básica"""
    manzana_nombre = serializers.CharField(source='manzana.nombre', read_only=True)
    lotificacion_nombre = serializers.CharField(source='manzana.lotificacion.nombre', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    saldo_financiar = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    actualizado_por_nombre = serializers.SerializerMethodField()

    # Campos formateados para la tabla
    valor_total_formateado = serializers.CharField(read_only=True)
    costo_instalacion_formateado = serializers.CharField(read_only=True)
    saldo_financiar_formateado = serializers.CharField(read_only=True)
    metros_cuadrados_formateados = serializers.CharField(read_only=True)

    def get_actualizado_por_nombre(self, obj):
        if obj.actualizado_por:
            return obj.actualizado_por.get_full_name() or obj.actualizado_por.username
        return None

    class Meta:
        model = Lote
        fields = [
            'id', 'identificador', 'manzana', 'manzana_nombre', 'lotificacion_nombre', 
            'numero_lote', 'metros_cuadrados', 'metros_cuadrados_formateados', 
            'valor_total', 'valor_total_formateado', 
            'costo_instalacion', 'costo_instalacion_formateado', 'saldo_financiar', 
            'saldo_financiar_formateado', 'estado', 'estado_display', 'version', 
            'actualizado_por', 'actualizado_por_nombre', 'activo', 
            'fecha_creacion', 'fecha_actualizacion'
        ]


class LotePlanoListSerializer(serializers.ModelSerializer):
    """Serializer ligero para plano interactivo: listar lotes por identificador y estado."""
    manzana_nombre = serializers.CharField(source='manzana.nombre', read_only=True)

    class Meta:
        model = Lote
        fields = ['id', 'identificador', 'estado', 'activo', 'manzana', 'manzana_nombre']


class LoteCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear lotes"""
    
    class Meta:
        model = Lote
        fields = [
            'manzana', 'numero_lote', 'identificador', 'metros_cuadrados', 'valor_total', 
            'costo_instalacion', 'estado'
        ]
    
    def validate(self, attrs):
        valor_total = attrs.get('valor_total', 0)
        costo_instalacion = attrs.get('costo_instalacion', 0)
        if valor_total is not None and costo_instalacion is not None:
            saldo = valor_total - costo_instalacion
            if saldo <= 0:
                raise serializers.ValidationError("El saldo a financiar debe ser mayor a 0")
        return attrs


class LoteUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar lotes con control de concurrencia. Permite editar también manzana y numero_lote (no identificador)."""
    version = serializers.IntegerField(required=True)
    manzana = serializers.PrimaryKeyRelatedField(queryset=Manzana.objects.all(), required=False)
    numero_lote = serializers.CharField(max_length=10, required=False)

    class Meta:
        model = Lote
        fields = [
            'manzana', 'numero_lote', 'metros_cuadrados', 'valor_total', 'costo_instalacion',
            'estado', 'activo', 'version'
        ]

    def validate(self, attrs):
        instance = self.instance
        if instance:
            version_enviada = attrs.get('version')
            if version_enviada != instance.version:
                raise serializers.ValidationError({
                    'version': 'El lote ha sido modificado por otro usuario. Por favor, recarga los datos.'
                })
            # Si se cambia manzana, debe ser de la misma lotificación que la actual
            manzana = attrs.get('manzana') or instance.manzana
            if manzana and instance.manzana_id and manzana.lotificacion_id != instance.manzana.lotificacion_id:
                raise serializers.ValidationError({
                    'manzana': 'La manzana debe pertenecer a la misma lotificación del lote.'
                })
        valor_total = attrs.get('valor_total', instance.valor_total if instance else None)
        costo_instalacion = attrs.get('costo_instalacion', instance.costo_instalacion if instance else None)
        if valor_total is not None and costo_instalacion is not None:
            saldo = valor_total - costo_instalacion
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


class LoteReservaSerializer(serializers.Serializer):
    """Serializer para reservar un lote"""
    version = serializers.IntegerField(required=True)
    notas = serializers.CharField(required=False, allow_blank=True)
