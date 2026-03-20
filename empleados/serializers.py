from rest_framework import serializers
from django.contrib.auth.models import User
from django.db import transaction
from permissions.models import Role, UserRole
from .models import Empleado

class EmpleadoSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Empleado
        fields = '__all__'
        read_only_fields = ['id', 'fecha_creacion', 'usuario']

    def validate(self, data):
        # Validar contraseñas
        if 'password' in data:
            if data['password'] != data.get('confirm_password'):
                raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})
        return data

    @transaction.atomic
    def create(self, validated_data):
        username = validated_data.pop('username', None)
        password = validated_data.pop('password', None)
        validated_data.pop('confirm_password', None)
        
        user = None
        if username and password:
            if User.objects.filter(username=username).exists():
                raise serializers.ValidationError({"username": "Este nombre de usuario ya está en uso."})
            user = User.objects.create_user(username=username, password=password, email=validated_data.get('correo', ''))
            
            # Asignar rol al usuario
            rol_name = validated_data.get('rol')
            if rol_name:
                try:
                    role = Role.objects.get(name=rol_name)
                    UserRole.objects.create(user=user, role=role)
                except Role.DoesNotExist:
                    pass

        validated_data['usuario'] = user
        return super().create(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        username = validated_data.pop('username', None)
        password = validated_data.pop('password', None)
        validated_data.pop('confirm_password', None)
        
        user = instance.usuario
        
        if username and user and username != user.username:
             if User.objects.filter(username=username).exclude(id=user.id).exists():
                 raise serializers.ValidationError({"username": "Este nombre de usuario ya está en uso."})
             user.username = username
             user.save()
             
        if password and user:
            user.set_password(password)
            user.save()
            
        if not user and username and password:
            if User.objects.filter(username=username).exists():
                raise serializers.ValidationError({"username": "Este nombre de usuario ya está en uso."})
            user = User.objects.create_user(username=username, password=password, email=validated_data.get('correo', ''))
            instance.usuario = user
            instance.save()
            
        new_rol = validated_data.get('rol')
        if new_rol and new_rol != instance.rol and user:
             try:
                 role = Role.objects.get(name=new_rol)
                 UserRole.objects.filter(user=user).delete()
                 UserRole.objects.create(user=user, role=role)
             except Role.DoesNotExist:
                 pass

        return super().update(instance, validated_data)
