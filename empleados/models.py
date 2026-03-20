from django.db import models
from django.contrib.auth.models import User

class Empleado(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    correo = models.EmailField(max_length=100, null=True, blank=True)
    dpi = models.CharField(max_length=20, null=True, blank=True)
    direccion = models.TextField(null=True, blank=True)
    fecha_contratacion = models.DateField()
    rol = models.CharField(max_length=20)
    sueldo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    porcentaje_comision = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    estado = models.BooleanField(default=True)
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'empleados_empleado'
        app_label = 'empleados'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.nombre} {self.apellido}".strip()
