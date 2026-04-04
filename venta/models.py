from django.db import models

class Venta(models.Model):
    TIPO_VENTA_CHOICES = [
        ('contado', 'Contado'),
        ('financiado', 'Financiado'),
    ]

    ESTADO_CHOICES = [
        ('activa', 'Activa'),
        ('anulada', 'Anulada'),
    ]

    lote = models.ForeignKey(
        'lotes.Lote', 
        on_delete=models.PROTECT, 
        related_name='ventas',
        verbose_name='Lote'
    )
    cliente = models.ForeignKey(
        'clientes.Cliente', 
        on_delete=models.PROTECT, 
        related_name='ventas',
        verbose_name='Cliente'
    )
    vendedor = models.ForeignKey(
        'empleados.Empleado', 
        on_delete=models.PROTECT, 
        related_name='ventas',
        verbose_name='Vendedor',
        null=True,
        blank=True
    )
    
    fecha_venta = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Venta')
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Precio de Venta (Q)')
    
    tipo_venta = models.CharField(
        max_length=20, 
        choices=TIPO_VENTA_CHOICES, 
        default='contado',
        verbose_name='Tipo de Venta'
    )
    
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='activa',
        verbose_name='Estado de la Venta'
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-fecha_venta']
        db_table = 'ventas_venta'

    def __str__(self):
        return f"Venta {self.tipo_venta} - Lote {self.lote.numero_lote} a {self.cliente.nombres}"
