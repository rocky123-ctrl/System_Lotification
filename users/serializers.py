from rest_framework import serializers
from django.contrib.auth.models import User
from authentication.serializers import UserSerializer, UserUpdateSerializer
from .models import UserActivity, UserSession


class UserActivitySerializer(serializers.ModelSerializer):
    """Serializer para actividades de usuario"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserActivity
        fields = '__all__'
        read_only_fields = ['user', 'ip_address', 'user_agent', 'created_at']


class UserSessionSerializer(serializers.ModelSerializer):
    """Serializer para sesiones de usuario"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserSession
        fields = '__all__'
        read_only_fields = ['user', 'ip_address', 'user_agent', 'login_time']


class UserListSerializer(serializers.ModelSerializer):
    """Serializer para listar usuarios con información básica"""
    full_name = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()
    last_activity = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name', 
                 'is_active', 'date_joined', 'is_online', 'last_activity']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
    
    def get_is_online(self, obj):
        # Verificar si el usuario tiene sesiones activas
        return obj.sessions.filter(is_active=True).exists()
    
    def get_last_activity(self, obj):
        # Obtener la última actividad del usuario
        last_activity = obj.activities.first()
        return last_activity.created_at if last_activity else None


class UserDetailSerializer(UserSerializer):
    """Serializer para detalles completos de usuario"""
    activities = UserActivitySerializer(many=True, read_only=True)
    sessions = UserSessionSerializer(many=True, read_only=True)
    activity_count = serializers.SerializerMethodField()
    session_count = serializers.SerializerMethodField()
    
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['activities', 'sessions', 'activity_count', 'session_count']
    
    def get_activity_count(self, obj):
        return obj.activities.count()
    
    def get_session_count(self, obj):
        return obj.sessions.count()
