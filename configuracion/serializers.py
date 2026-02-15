from rest_framework import serializers
from .models import ConfiguracionGeneral, ConfiguracionFinanciera


class ConfiguracionGeneralSerializer(serializers.ModelSerializer):
    """Serializer para configuración general"""
    # Campos formateados
    tasa_anual_formateada = serializers.CharField(read_only=True)
    tasa_mensual_formateada = serializers.CharField(read_only=True)
    area_total_formateada = serializers.CharField(read_only=True)
    fecha_inicio_formateada = serializers.CharField(read_only=True)
    
    class Meta:
        model = ConfiguracionGeneral
        fields = '__all__'
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion']


class ConfiguracionGeneralUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar configuración general"""
    
    class Meta:
        model = ConfiguracionGeneral
        fields = [
            'nombre_lotificacion', 'ubicacion', 'descripcion', 'direccion_completa',
            'telefono', 'email', 'sitio_web', 'fecha_inicio', 'total_lotes', 
            'area_total', 'tasa_anual', 'logo', 'activo'
        ]
        read_only_fields = ['tasa_mensual', 'fecha_creacion', 'fecha_actualizacion']


class ConfiguracionGeneralPublicSerializer(serializers.ModelSerializer):
    """Serializer público para mostrar información básica"""
    tasa_anual_formateada = serializers.CharField(read_only=True)
    area_total_formateada = serializers.CharField(read_only=True)
    fecha_inicio_formateada = serializers.CharField(read_only=True)
    
    class Meta:
        model = ConfiguracionGeneral
        fields = [
            'nombre_lotificacion', 'ubicacion', 'descripcion', 'direccion_completa',
            'telefono', 'email', 'sitio_web', 'fecha_inicio_formateada', 
            'total_lotes', 'area_total_formateada', 'tasa_anual_formateada', 'logo'
        ]


class ConfiguracionFinancieraSerializer(serializers.ModelSerializer):
    """Serializer para configuración financiera"""
    
    class Meta:
        model = ConfiguracionFinanciera
        fields = '__all__'
        read_only_fields = ['configuracion', 'fecha_creacion', 'fecha_actualizacion']


class ConfiguracionFinancieraUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar configuración financiera"""
    
    class Meta:
        model = ConfiguracionFinanciera
        fields = [
            'plazo_minimo_meses', 'plazo_maximo_meses', 'enganche_minimo_porcentaje',
            'enganche_maximo_porcentaje', 'costo_instalacion_default',
            'permitir_pagos_anticipados', 'aplicar_penalizacion_atrasos',
            'penalizacion_atraso_porcentaje'
        ]


class ConfiguracionCompletaSerializer(serializers.ModelSerializer):
    """Serializer que incluye configuración general y financiera"""
    configuracion_financiera = ConfiguracionFinancieraSerializer(read_only=True)
    tasa_anual_formateada = serializers.CharField(read_only=True)
    tasa_mensual_formateada = serializers.CharField(read_only=True)
    area_total_formateada = serializers.CharField(read_only=True)
    fecha_inicio_formateada = serializers.CharField(read_only=True)
    
    class Meta:
        model = ConfiguracionGeneral
        fields = '__all__'
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion']


class LogoUploadSerializer(serializers.ModelSerializer):
    """Serializer específico para subir logo"""
    
    class Meta:
        model = ConfiguracionGeneral
        fields = ['logo']


class ConfiguracionResumenSerializer(serializers.Serializer):
    """Serializer para resumen de configuración"""
    nombre_lotificacion = serializers.CharField()
    ubicacion = serializers.CharField()
    total_lotes_configurado = serializers.IntegerField()
    total_lotes_reales = serializers.IntegerField()
    lotes_disponibles = serializers.IntegerField()
    lotes_reservados = serializers.IntegerField()
    lotes_en_proceso = serializers.IntegerField()
    lotes_financiados = serializers.IntegerField()
    lotes_vendidos = serializers.IntegerField()
    lotes_cancelados = serializers.IntegerField()
    tasa_anual = serializers.DecimalField(max_digits=5, decimal_places=2)
    tasa_anual_formateada = serializers.CharField()
    valor_total_inventario = serializers.DecimalField(max_digits=15, decimal_places=2)
    valor_total_reservados = serializers.DecimalField(max_digits=15, decimal_places=2)
    valor_total_en_proceso = serializers.DecimalField(max_digits=15, decimal_places=2)
    valor_total_financiados = serializers.DecimalField(max_digits=15, decimal_places=2)
    valor_total_vendido = serializers.DecimalField(max_digits=15, decimal_places=2)
    fecha_ultima_actualizacion = serializers.DateTimeField()


class ConfiguracionEstadisticasSerializer(serializers.Serializer):
    """Serializer para estadísticas de configuración"""
    total_configuraciones = serializers.IntegerField()
    configuracion_activa = serializers.BooleanField()
    fecha_creacion_configuracion = serializers.DateTimeField()
    fecha_ultima_actualizacion = serializers.DateTimeField()
    tiene_logo = serializers.BooleanField()
    tiene_configuracion_financiera = serializers.BooleanField()
