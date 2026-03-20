from rest_framework import serializers
from .models import Cliente

class ClienteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Cliente
        fields = [
            'id', 'nombres', 'apellidos', 'telefono', 'email', 'direccion', 
            'estado', 'fechaRegistro'
        ]
        read_only_fields = ['id', 'fechaRegistro']
