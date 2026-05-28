from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from clientes.models import Cliente
from lotes.models import Lotificacion, Lote

class ServicioCatalogo(models.Model):
    """
    Catálogo de servicios disponibles por lotificación.
    """
    lotificacion = models.ForeignKey(
        Lotificacion, 
        on_delete=models.CASCADE, 
        related_name='servicios_catalogo',
        verbose_name='Lotificación'
    )
    nombre = models.CharField(max_length=150, verbose_name='Nombre del Servicio')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
    precio_base_defecto = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Precio Base Defecto'
    )
    icono = models.CharField(max_length=50, blank=True, null=True, verbose_name='Icono (String)')
    es_recurrente = models.BooleanField(default=True, verbose_name='Es Recurrente')
    activo = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        verbose_name = 'Servicio de Catálogo'
        verbose_name_plural = 'Servicios de Catálogo'
        db_table = 'servicios_servicio_catalogo'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} - {self.lotificacion.nombre}"


class BilleteraServicio(models.Model):
    """
    Contenedor maestro para los pagos de servicios del cliente.
    """
    cliente = models.OneToOneField(
        Cliente, 
        on_delete=models.CASCADE, 
        related_name='billetera_servicios',
        verbose_name='Cliente'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Billetera de Servicio'
        verbose_name_plural = 'Billeteras de Servicios'
        db_table = 'servicios_billetera'

    def __str__(self):
        return f"Billetera de {self.cliente}"


class ConfiguracionServicioLote(models.Model):
    """
    Configuración personalizada de un servicio para un lote específico.
    """
    lote = models.ForeignKey(
        Lote, 
        on_delete=models.CASCADE, 
        related_name='configuraciones_servicios',
        verbose_name='Lote'
    )
    servicio = models.ForeignKey(
        ServicioCatalogo, 
        on_delete=models.CASCADE, 
        related_name='configuraciones_lotes',
        verbose_name='Servicio'
    )
    precio_personalizado = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.00'))],
        null=True, 
        blank=True,
        verbose_name='Precio Personalizado',
        help_text='Si es nulo, se usará el precio base del catálogo'
    )
    esta_activo = models.BooleanField(default=True, verbose_name='Está Activo')

    class Meta:
        verbose_name = 'Configuración de Servicio por Lote'
        verbose_name_plural = 'Configuraciones de Servicios por Lote'
        db_table = 'servicios_configuracion_lote'
        unique_together = ['lote', 'servicio']

    def __str__(self):
        return f"{self.servicio.nombre} - {self.lote}"

    @property
    def precio_final(self):
        return self.precio_personalizado if self.precio_personalizado is not None else self.servicio.precio_base_defecto


class PagoServicio(models.Model):
    """
    Historial de cobros y pagos de servicios.
    """
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Pagado', 'Pagado'),
        ('Vencido', 'Vencido'),
    ]

    METODO_PAGO_CHOICES = [
        ('Efectivo', 'Efectivo'),
        ('Transferencia', 'Transferencia'),
        ('Depósito', 'Depósito'),
        ('Tarjeta', 'Tarjeta'),
    ]

    lote = models.ForeignKey(
        Lote, 
        on_delete=models.CASCADE, 
        related_name='pagos_servicios',
        verbose_name='Lote'
    )
    servicio = models.ForeignKey(
        ServicioCatalogo, 
        on_delete=models.CASCADE, 
        related_name='pagos',
        verbose_name='Servicio'
    )
    mes_periodo = models.DateField(verbose_name='Mes del Periodo')
    monto_cobrado = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto Cobrado')
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name='Monto Pagado')
    mora_aplicada = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name='Mora Aplicada')
    fecha_limite = models.DateField(verbose_name='Fecha Límite')
    fecha_pago_realizado = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Pago Realizado')
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, default='Efectivo', verbose_name='Método de Pago')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Pendiente', verbose_name='Estado')

    class Meta:
        verbose_name = 'Pago de Servicio'
        verbose_name_plural = 'Pagos de Servicios'
        db_table = 'servicios_pago'
        ordering = ['-mes_periodo', 'lote']

    def __str__(self):
        return f"{self.servicio.nombre} - {self.lote} ({self.mes_periodo})"
