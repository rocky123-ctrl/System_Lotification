from django.shortcuts import render
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db.models import Q, Count
from .serializers import (
    UserListSerializer, UserDetailSerializer, UserUpdateSerializer,
    UserActivitySerializer, UserSessionSerializer
)
from .models import UserActivity, UserSession


class UserListView(generics.ListAPIView):
    """Lista de usuarios con información básica"""
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = User.objects.filter(is_active=True)
        
        # Filtros
        search = self.request.query_params.get('search', None)
        is_online = self.request.query_params.get('is_online', None)
        
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )
        
        if is_online is not None:
            if is_online.lower() == 'true':
                queryset = queryset.filter(sessions__is_active=True).distinct()
            elif is_online.lower() == 'false':
                queryset = queryset.exclude(sessions__is_active=True)
        
        return queryset.order_by('-date_joined')


class UserDetailView(generics.RetrieveAPIView):
    """Detalles completos de un usuario"""
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]


class UserCreateView(generics.CreateAPIView):
    """Crear nuevo usuario"""
    queryset = User.objects.all()
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAdminUser]


class UserUpdateView(generics.UpdateAPIView):
    """Actualizar usuario"""
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]


class UserDeleteView(generics.DestroyAPIView):
    """Eliminar usuario (desactivar)"""
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserListSerializer
    permission_classes = [IsAdminUser]

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'message': 'Usuario desactivado exitosamente'})


class UserActivityListView(generics.ListAPIView):
    """Lista de actividades de usuario"""
    queryset = UserActivity.objects.all()
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = UserActivity.objects.all()
        user_id = self.request.query_params.get('user_id', None)
        activity_type = self.request.query_params.get('activity_type', None)
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
            
        return queryset.order_by('-created_at')


class UserSessionListView(generics.ListAPIView):
    """Lista de sesiones de usuario"""
    queryset = UserSession.objects.all()
    serializer_class = UserSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = UserSession.objects.all()
        user_id = self.request.query_params.get('user_id', None)
        is_active = self.request.query_params.get('is_active', None)
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if is_active is not None:
            if is_active.lower() == 'true':
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() == 'false':
                queryset = queryset.filter(is_active=False)
                
        return queryset.order_by('-login_time')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_statistics(request, user_id):
    """Obtener estadísticas de un usuario"""
    try:
        user = User.objects.get(id=user_id)
        
        # Estadísticas básicas
        total_activities = user.activities.count()
        total_sessions = user.sessions.count()
        active_sessions = user.sessions.filter(is_active=True).count()
        
        # Actividad por tipo
        activity_types = user.activities.values('activity_type').annotate(
            count=Count('activity_type')
        )
        
        # Últimas actividades
        recent_activities = user.activities.order_by('-created_at')[:10]
        
        # Sesiones recientes
        recent_sessions = user.sessions.order_by('-login_time')[:10]
        
        data = {
            'user_id': user_id,
            'username': user.username,
            'total_activities': total_activities,
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'activity_types': list(activity_types),
            'recent_activities': UserActivitySerializer(recent_activities, many=True).data,
            'recent_sessions': UserSessionSerializer(recent_sessions, many=True).data,
        }
        
        return Response(data)
    except User.DoesNotExist:
        return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def log_user_activity(request):
    """Registrar actividad de usuario"""
    serializer = UserActivitySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_online_users(request):
    """Obtener lista de usuarios en línea"""
    online_users = User.objects.filter(
        sessions__is_active=True
    ).distinct().order_by('username')
    
    serializer = UserListSerializer(online_users, many=True)
    return Response(serializer.data)
