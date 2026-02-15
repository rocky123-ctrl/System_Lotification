from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'financiamiento'

router = DefaultRouter()
router.register(r'financiamientos', views.FinanciamientoViewSet)
router.register(r'cuotas', views.CuotaViewSet)
router.register(r'pagos', views.PagoViewSet)
router.register(r'configuracion-pago', views.ConfiguracionPagoViewSet)
router.register(r'pagos-capital', views.PagoCapitalViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
    # Endpoints adicionales
    path('calcular-moras-generales/', views.calcular_moras_generales, name='calcular_moras_generales'),
    path('reporte-financiamiento/', views.reporte_financiamiento, name='reporte_financiamiento'),
]
