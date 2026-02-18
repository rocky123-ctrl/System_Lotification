from rest_framework import serializers
from .models import Plano
import os


class PlanoSerializer(serializers.ModelSerializer):
    """Serializer para planos"""
    url = serializers.SerializerMethodField()
    es_pdf = serializers.BooleanField(read_only=True)
    es_imagen = serializers.BooleanField(read_only=True)
    fecha_subida = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S', read_only=True)

    class Meta:
        model = Plano
        fields = ['id', 'url', 'nombre', 'fecha_subida', 'es_pdf', 'es_imagen']
        read_only_fields = ['id', 'fecha_subida', 'url', 'es_pdf', 'es_imagen']

    def get_url(self, obj):
        """Obtiene la URL completa del archivo usando la vista especial que permite iframes"""
        if obj.archivo:
            request = self.context.get('request')
            if request:
                # Usar la vista especial que permite mostrar en iframes
                from django.urls import reverse
                url = reverse('planos:servir_plano', args=[obj.id])
                return request.build_absolute_uri(url)
            # Fallback a la URL directa si no hay request
            return obj.archivo.url
        return None


class PlanoUploadSerializer(serializers.ModelSerializer):
    """Serializer para subir planos"""
    plano = serializers.FileField(write_only=True, required=True)
    nombre = serializers.CharField(required=True, max_length=255)

    class Meta:
        model = Plano
        fields = ['plano', 'nombre']

    def validate_plano(self, value):
        """Validar el archivo subido"""
        # Validar tamaño (máximo 50MB)
        max_size = 50 * 1024 * 1024  # 50MB en bytes
        if value.size > max_size:
            raise serializers.ValidationError(
                f'El archivo es demasiado grande. Tamaño máximo: 50MB'
            )

        # Validar extensión
        extensiones_permitidas = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.webp']
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in extensiones_permitidas:
            raise serializers.ValidationError(
                f'Formato no permitido. Formatos permitidos: {", ".join(extensiones_permitidas)}'
            )

        return value

    def create(self, validated_data):
        """Crear un nuevo plano"""
        # Desactivar planos anteriores si existe uno activo
        Plano.objects.filter(activo=True).update(activo=False)
        
        # Crear nuevo plano
        archivo = validated_data.pop('plano')
        nombre = validated_data.pop('nombre')
        
        plano = Plano.objects.create(
            archivo=archivo,
            nombre=nombre,
            activo=True
        )
        
        return plano

    def update(self, instance, validated_data):
        """Actualizar un plano existente"""
        if 'plano' in validated_data:
            # Eliminar archivo anterior si existe
            if instance.archivo:
                instance.archivo.delete(save=False)
            
            instance.archivo = validated_data.pop('plano')
        
        if 'nombre' in validated_data:
            instance.nombre = validated_data.pop('nombre')
        
        instance.save()
        return instance

