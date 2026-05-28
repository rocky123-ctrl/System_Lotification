from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone

class Cuota(models.Model):
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Pagado', 'Pagado'),
        ('Vencido', 'Vencido'),
        ('Revertido', 'Revertido'),
    ]

    venta = models.ForeignKey('ventas.Venta', on_delete=models.CASCADE, related_name='cuotas_cobrar')
    no_cuota = models.PositiveIntegerField(verbose_name="No. Cuota", default=1)
    fecha_programada = models.DateField(verbose_name="Fecha Programada", default=timezone.now)
    monto_cuota = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto Cuota", default=Decimal('0.00'))
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Pendiente')

    class Meta:
        db_table = 'ventas_cuota'
        verbose_name = "Cuota"
        verbose_name_plural = "Cuotas"
        ordering = ['venta', 'no_cuota']
        indexes = [
            models.Index(fields=['venta', 'no_cuota']),
            models.Index(fields=['estado', 'fecha_programada']),
        ]

    def __str__(self):
        return f"Cuota {self.no_cuota} - {self.venta.lote.numero_lote}"

class Pago(models.Model):
    METODO_PAGO_CHOICES = [
        ('Efectivo', 'Efectivo'),
        ('Tarjeta', 'Tarjeta'),
        ('Transferencia', 'Transferencia'),
        ('Depósito', 'Depósito'),
    ]

    cuota = models.ForeignKey(Cuota, on_delete=models.CASCADE, related_name='pagos_registrados')
    monto_base = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto Base", default=Decimal('0.00'))
    monto_mora = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Monto Mora")
    fecha_pago = models.DateTimeField(default=timezone.now, verbose_name="Fecha de Pago")
    metodo_pago = models.CharField(max_length=50, choices=METODO_PAGO_CHOICES, verbose_name="Método de Pago", default='Efectivo')
    referencia = models.CharField(max_length=100, blank=True, null=True, verbose_name="Referencia de Pago")
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuario que cobró", null=True, blank=True)
    activo = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        db_table = 'ventas_pago'
        verbose_name = "Pago Realizado"
        verbose_name_plural = "Pagos Realizados"

    def __str__(self):
        return f"Pago {self.id} - Cuota {self.cuota.no_cuota}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Al guardar un nuevo pago, actualizar cuota y venta
        if is_new and self.activo:
            self.cuota.estado = 'Pagado'
            self.cuota.save()
            
            # Recalcular totales en la venta
            self.cuota.venta.actualizar_totales()

class BitacoraCambio(models.Model):
    venta = models.ForeignKey('ventas.Venta', on_delete=models.CASCADE, related_name='bitacora_cambios')
    fecha = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField(verbose_name="Descripción del Cambio", default='')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Usuario")

    class Meta:
        db_table = 'ventas_historialcambios'
        verbose_name = "Historial de Cambio"
        verbose_name_plural = "Historial de Cambios"
        ordering = ['-fecha']

    def __str__(self):
        return f"Cambio en Venta {self.venta.id} - {self.fecha.date()}"
