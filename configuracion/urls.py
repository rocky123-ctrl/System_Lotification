from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'configuracion'

router = DefaultRouter()
router.register(r'general', views.ConfiguracionGeneralViewSet)
router.register(r'financiera', views.ConfiguracionFinancieraViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('publica/', views.configuracion_publica, name='configuracion_publica'),
    path('inicializar/', views.inicializar_configuracion, name='inicializar_configuracion'),
]
