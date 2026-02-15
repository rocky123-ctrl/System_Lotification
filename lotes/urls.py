from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'lotes'

router = DefaultRouter()
router.register(r'manzanas', views.ManzanaViewSet)
router.register(r'lotes', views.LoteViewSet)
router.register(r'historial', views.HistorialLoteViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('lotes-disponibles-count/', views.lotes_disponibles_count, name='lotes_disponibles_count'),
    path('filtrar-lotes/', views.filtrar_lotes, name='filtrar_lotes'),
]
