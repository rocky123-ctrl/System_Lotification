from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VentaViewSet, 
    LiquidacionComisionViewSet, 
    CotizacionViewSet
)

router = DefaultRouter()
router.register(r'liquidaciones', LiquidacionComisionViewSet, basename='liquidaciones')
router.register(r'cotizaciones', CotizacionViewSet, basename='cotizaciones')
router.register(r'', VentaViewSet, basename='ventas')

urlpatterns = [
    path('', include(router.urls)),
]
