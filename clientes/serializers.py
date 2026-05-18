from rest_framework import serializers
from .models import Cliente

class ClienteSerializer(serializers.ModelSerializer):
    dpi = serializers.CharField(required=True, allow_blank=False)
    nit = serializers.CharField(required=True, allow_blank=False)

    class Meta:
        model = Cliente
        fields = [
            'id', 'nombres', 'apellidos', 'dpi', 'nit', 'telefono', 'email', 'direccion', 
            'estado', 'fechaRegistro'
        ]
        read_only_fields = ['id', 'fechaRegistro']
