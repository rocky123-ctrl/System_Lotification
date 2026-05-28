from django.shortcuts import render
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db.models import Q, Count
from .serializers import (
    UserListSerializer, UserDetailSerializer, UserUpdateSerializer
)


class UserListView(generics.ListAPIView):
    """Lista de usuarios con información básica"""
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = User.objects.filter(is_active=True)
        
        # Filtrar por rol (ej: role=Vendedor para listar solo vendedores)
        role = self.request.query_params.get('role', None)
        if role:
            queryset = queryset.filter(
                user_roles__role__name__iexact=role.strip(),
                user_roles__is_active=True
            ).distinct()
        
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
        
        return queryset.select_related('profile').order_by('-date_joined')


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

