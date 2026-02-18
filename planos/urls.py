from django.urls import path
from . import views

app_name = 'planos'

urlpatterns = [
    path('', views.obtener_plano, name='obtener_plano'),
    path('subir/', views.subir_plano, name='subir_plano'),
    path('<int:id>/actualizar/', views.actualizar_plano, name='actualizar_plano'),
    path('<int:id>/archivo/', views.servir_plano, name='servir_plano'),
    path('<int:id>/', views.eliminar_plano, name='eliminar_plano'),
]

