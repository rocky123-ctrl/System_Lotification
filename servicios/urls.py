from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ServicioCatalogoViewSet, 
    BilleteraServicioViewSet, 
    ConfiguracionServicioLoteViewSet, 
    PagoServicioViewSet
)

router = DefaultRouter()
router.register(r'catalogo', ServicioCatalogoViewSet)
router.register(r'billeteras', BilleteraServicioViewSet)
router.register(r'configuraciones', ConfiguracionServicioLoteViewSet)
router.register(r'pagos', PagoServicioViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
