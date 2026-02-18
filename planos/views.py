from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404, JsonResponse
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.http import require_http_methods
from .models import Plano
from .serializers import PlanoSerializer, PlanoUploadSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_plano(request):
    """
    Obtener el plano actual activo
    GET /api/planos/
    """
    try:
        plano = Plano.objects.filter(activo=True).first()
        if plano:
            serializer = PlanoSerializer(plano, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {'mensaje': 'No hay planos disponibles'},
                status=status.HTTP_404_NOT_FOUND
            )
    except Exception as e:
        return Response(
            {'error': f'Error al obtener el plano: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def subir_plano(request):
    """
    Subir un nuevo plano
    POST /api/planos/subir/
    """
    try:
        serializer = PlanoUploadSerializer(data=request.data)
        if serializer.is_valid():
            plano = serializer.save()
            response_serializer = PlanoSerializer(plano, context={'request': request})
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
    except Exception as e:
        return Response(
            {'error': f'Error al subir el plano: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def actualizar_plano(request, id):
    """
    Actualizar un plano existente
    POST /api/planos/{id}/actualizar/
    """
    try:
        plano = get_object_or_404(Plano, id=id, activo=True)
        serializer = PlanoUploadSerializer(plano, data=request.data, partial=True)
        if serializer.is_valid():
            plano_actualizado = serializer.save()
            response_serializer = PlanoSerializer(plano_actualizado, context={'request': request})
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
    except Plano.DoesNotExist:
        return Response(
            {'error': 'Plano no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Error al actualizar el plano: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def eliminar_plano(request, id):
    """
    Eliminar un plano
    DELETE /api/planos/{id}/
    """
    try:
        plano = get_object_or_404(Plano, id=id)
        
        # Eliminar el archivo físico si existe
        if plano.archivo:
            plano.archivo.delete(save=False)
        
        # Eliminar el registro de la base de datos
        plano.delete()
        
        return Response(
            {'mensaje': 'Plano eliminado correctamente'},
            status=status.HTTP_200_OK
        )
    except Plano.DoesNotExist:
        return Response(
            {'error': 'Plano no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Error al eliminar el plano: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@xframe_options_exempt  # Permite mostrar el PDF en iframes desde cualquier origen
def servir_plano(request, id):
    """
    Servir el archivo del plano directamente
    GET /api/planos/{id}/archivo/
    Esta vista permite mostrar el PDF en iframes sin restricciones de X-Frame-Options
    """
    # Verificar autenticación usando JWT de DRF
    from rest_framework_simplejwt.authentication import JWTAuthentication
    
    # Intentar autenticar con JWT
    jwt_auth = JWTAuthentication()
    try:
        user, token = jwt_auth.authenticate(request)
        if user:
            request.user = user
        elif not request.user.is_authenticated:
            return JsonResponse(
                {'error': 'No autenticado'},
                status=401
            )
    except Exception:
        if not request.user.is_authenticated:
            return JsonResponse(
                {'error': 'No autenticado'},
                status=401
            )
    
    try:
        plano = get_object_or_404(Plano, id=id, activo=True)
        
        if not plano.archivo:
            raise Http404("El plano no tiene archivo asociado")
        
        # Determinar el content type
        if plano.es_pdf:
            content_type = 'application/pdf'
        elif plano.es_imagen:
            ext = plano.archivo.name.split('.')[-1].lower()
            content_type_map = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'webp': 'image/webp'
            }
            content_type = content_type_map.get(ext, 'application/octet-stream')
        else:
            content_type = 'application/octet-stream'
        
        # Servir el archivo con los headers apropiados
        response = FileResponse(
            plano.archivo.open('rb'),
            content_type=content_type
        )
        response['Content-Disposition'] = f'inline; filename="{plano.nombre}"'
        # Permitir que se muestre en iframes desde cualquier origen
        response['X-Frame-Options'] = 'ALLOWALL'
        
        return response
    except Plano.DoesNotExist:
        raise Http404("Plano no encontrado")
    except Exception as e:
        raise Http404(f"Error al servir el plano: {str(e)}")
