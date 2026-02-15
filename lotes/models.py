from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Manzana(models.Model):
    """
    Modelo para representar manzanas/bloques
    """
    nombre = models.CharField(max_length=10, unique=True, verbose_name='Nombre de Manzana')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Manzana'
        verbose_name_plural = 'Manzanas'
        ordering = ['nombre']

    def __str__(self):
        return f"Manzana {self.nombre}"


class Lote(models.Model):
    """
    Modelo para representar lotes disponibles para venta
    """
    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('reservado', 'Reservado'),
        ('vendido', 'Vendido'),
        ('en_proceso', 'En Proceso de Venta'),
        ('financiado', 'Financiado'),
        ('cancelado', 'Cancelado'),
    ]

    # Información básica
    manzana = models.ForeignKey(Manzana, on_delete=models.CASCADE, related_name='lotes', verbose_name='Manzana')
    numero_lote = models.CharField(max_length=10, verbose_name='Número de Lote')
    metros_cuadrados = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Metros Cuadrados'
    )
    
    # Información financiera
    valor_total = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Valor Total (Q)'
    )
    enganche = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Enganche (Q)'
    )
    costo_instalacion = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('5000.00'),
        verbose_name='Instalación (Q)'
    )
    
    # Información de financiamiento
    plazo_meses = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Plazo (meses)'
    )
    cuota_mensual = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Cuota Mensual (Q)'
    )
    
    # Estado y control
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='disponible',
        verbose_name='Estado del Lote'
    )
    activo = models.BooleanField(default=True, verbose_name='Activo')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Lote'
        verbose_name_plural = 'Lotes'
        unique_together = ['manzana', 'numero_lote']
        ordering = ['manzana', 'numero_lote']

    def __str__(self):
        return f"Lote {self.numero_lote} - Manzana {self.manzana.nombre}"

    @property
    def saldo_financiar(self):
        """Calcula el saldo a financiar"""
        if self.valor_total is None or self.enganche is None or self.costo_instalacion is None:
            return Decimal('0.00')
        return self.valor_total - self.enganche - self.costo_instalacion

    @property
    def valor_total_formateado(self):
        """Retorna el valor total formateado"""
        if self.valor_total is None:
            return "Q 0.00"
        return f"Q {self.valor_total:,.2f}"

    @property
    def enganche_formateado(self):
        """Retorna el enganche formateado"""
        if self.enganche is None:
            return "Q 0.00"
        return f"Q {self.enganche:,.2f}"

    @property
    def costo_instalacion_formateado(self):
        """Retorna el costo de instalación formateado"""
        if self.costo_instalacion is None:
            return "Q 0.00"
        return f"Q {self.costo_instalacion:,.2f}"

    @property
    def saldo_financiar_formateado(self):
        """Retorna el saldo a financiar formateado"""
        if self.saldo_financiar is None:
            return "Q 0.00"
        return f"Q {self.saldo_financiar:,.2f}"

    @property
    def cuota_mensual_formateada(self):
        """Retorna la cuota mensual formateada"""
        if self.cuota_mensual is None:
            return "Q 0.00"
        return f"Q {self.cuota_mensual:,.2f}"

    @property
    def metros_cuadrados_formateados(self):
        """Retorna los metros cuadrados formateados"""
        if self.metros_cuadrados is None:
            return "0 m²"
        return f"{self.metros_cuadrados} m²"

    def save(self, *args, **kwargs):
        """Sobrescribir save para validaciones adicionales"""
        # Solo validar si todos los valores están presentes
        if (self.valor_total is not None and self.enganche is not None and 
            self.costo_instalacion is not None):
            
            # Validar que el enganche no sea mayor al valor total
            if self.enganche >= self.valor_total:
                raise ValueError("El enganche no puede ser mayor o igual al valor total")
            
            # Validar que el saldo a financiar sea positivo
            if self.saldo_financiar <= 0:
                raise ValueError("El saldo a financiar debe ser mayor a 0")
        
        super().save(*args, **kwargs)


class HistorialLote(models.Model):
    """
    Modelo para registrar el historial de cambios de estado de los lotes
    """
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='historial', verbose_name='Lote')
    estado_anterior = models.CharField(max_length=20, verbose_name='Estado Anterior')
    estado_nuevo = models.CharField(max_length=20, verbose_name='Nuevo Estado')
    cambiado_por = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, verbose_name='Cambiado por')
    notas = models.TextField(blank=True, null=True, verbose_name='Notas')
    fecha_cambio = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Cambio')

    class Meta:
        verbose_name = 'Historial de Lote'
        verbose_name_plural = 'Historial de Lotes'
        ordering = ['-fecha_cambio']

    def __str__(self):
        return f"Lote {self.lote.numero_lote} - {self.estado_anterior} → {self.estado_nuevo}"
