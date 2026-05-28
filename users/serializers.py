from rest_framework import serializers
from django.contrib.auth.models import User
from authentication.serializers import UserSerializer, UserUpdateSerializer


class UserListSerializer(serializers.ModelSerializer):
    """Serializer para listar usuarios con información básica"""
    full_name = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()
    last_activity = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name',
                 'is_active', 'date_joined', 'is_online', 'last_activity', 'phone', 'address']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
    
    def get_is_online(self, obj):
        return False
    
    def get_last_activity(self, obj):
        return None
    
    def get_phone(self, obj):
        if hasattr(obj, 'profile') and obj.profile:
            return obj.profile.phone or ''
        return ''
    
    def get_address(self, obj):
        if hasattr(obj, 'profile') and obj.profile:
            return obj.profile.address or ''
        return ''


class UserDetailSerializer(UserSerializer):
    """Serializer para detalles completos de usuario"""
    
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields
