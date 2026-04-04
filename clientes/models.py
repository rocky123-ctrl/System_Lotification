from django.db import models
# Importaciones lazy para relaciones geográficas

class Cliente(models.Model):
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]

    nombres = models.CharField(max_length=150)
    apellidos = models.CharField(max_length=150)
    dpi = models.CharField(max_length=20, null=True, blank=True)
    nit = models.CharField(max_length=20, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    direccion = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo')
    fechaRegistro = models.DateTimeField(auto_now_add=True)

    # Relaciones Geográficas Temporales Omitidas
    
    class Meta:
        db_table = 'clientes_cliente'
        ordering = ['-fechaRegistro']

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"
