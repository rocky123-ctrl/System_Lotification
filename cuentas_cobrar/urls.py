from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CuotaViewSet, PagoViewSet, BitacoraCambioViewSet

router = DefaultRouter()
router.register(r'cuotas', CuotaViewSet, basename='cuotas-cobrar')
router.register(r'pagos', PagoViewSet, basename='pagos-registrados')
router.register(r'bitacora', BitacoraCambioViewSet, basename='bitacora-cambios')

urlpatterns = [
    path('', include(router.urls)),
]
