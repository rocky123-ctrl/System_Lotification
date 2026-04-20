from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone

class Cuota(models.Model):
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Pagado', 'Pagado'),
        ('Vencido', 'Vencido'),
    ]

    venta = models.ForeignKey('ventas.Venta', on_delete=models.CASCADE, related_name='cuotas_cobrar')
    no_cuota = models.PositiveIntegerField(verbose_name="No. Cuota")
    fecha_vencimiento = models.DateField(verbose_name="Fecha de Vencimiento")
    monto_base = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto Base (Capital)")
    interes_monto = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Monto Interés")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Pendiente')

    class Meta:
        verbose_name = "Cuota"
        verbose_name_plural = "Cuotas"
        ordering = ['venta', 'no_cuota']
        app_label = 'cuentas_cobrar'

    def __str__(self):
        return f"Cuota {self.no_cuota} - {self.venta.lote.numero_lote}"

    def calcular_mora(self, porcentaje_diario=Decimal('0.05')):
        """
        Calcula el monto de mora si la cuota está vencida.
        Retorna el monto extra (mora).
        """
        if self.estado != 'Pagado' and self.fecha_vencimiento < timezone.now().date():
            dias_atraso = (timezone.now().date() - self.fecha_vencimiento).days
            monto_mora = self.monto_base * (porcentaje_diario / Decimal('100')) * Decimal(dias_atraso)
            return monto_mora.quantize(Decimal('0.01'))
        return Decimal('0.00')

class Pago(models.Model):
    METODO_PAGO_CHOICES = [
        ('Efectivo', 'Efectivo'),
        ('Transferencia', 'Transferencia'),
        ('Depósito', 'Depósito'),
    ]

    cuota = models.ForeignKey(Cuota, on_delete=models.CASCADE, related_name='pagos_registrados')
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto Pagado")
    monto_mora = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Monto Mora")
    fecha_pago = models.DateTimeField(default=timezone.now, verbose_name="Fecha de Pago")
    metodo_pago = models.CharField(max_length=50, choices=METODO_PAGO_CHOICES, verbose_name="Método de Pago")
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Admin/Usuario que cobró")

    class Meta:
        verbose_name = "Pago Realizado"
        verbose_name_plural = "Pagos Realizados"
        app_label = 'cuentas_cobrar'

    def __str__(self):
        return f"Pago {self.id} - Cuota {self.cuota.no_cuota}"

    def save(self, *args, **kwargs):
        # Al guardar el pago total, marcar la cuota como pagada
        super().save(*args, **kwargs)
        # Verificamos si el monto pagado cubre la cuota
        # En este sistema simplificado asumimos pago total para cambiar el estado
        self.cuota.estado = 'Pagado'
        self.cuota.save()

class BitacoraCambio(models.Model):
    venta = models.ForeignKey('ventas.Venta', on_delete=models.CASCADE, related_name='bitacora_cambios')
    fecha = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField(verbose_name="Descripción del Cambio")

    class Meta:
        verbose_name = "Bitácora de Cambio"
        verbose_name_plural = "Bitácoras de Cambios"
        app_label = 'cuentas_cobrar'

    def __str__(self):
        return f"Cambio en Venta {self.venta.id} - {self.fecha.date()}"
