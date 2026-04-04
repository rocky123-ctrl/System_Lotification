from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import os


def plano_svg_upload_path(instance, filename):
    """Generar ruta para guardar el SVG del plano"""
    # Guardar en: lotificaciones/{lotificacion_id}/plano.svg
    return f'lotificaciones/{instance.id}/plano.svg'


class Lotificacion(models.Model):
    """
    Modelo para representar una lotificación
    """
    nombre = models.CharField(max_length=200, unique=True, verbose_name='Nombre de la Lotificación')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
    ubicacion = models.CharField(max_length=200, blank=True, null=True, verbose_name='Ubicación')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Campos de estadísticas
    total_manzanas = models.IntegerField(
        default=0,
        verbose_name='Total de Manzanas',
        help_text='Número total de manzanas en la lotificación'
    )
    total_lotes = models.IntegerField(
        default=0,
        verbose_name='Total de Lotes',
        help_text='Número total de lotes en la lotificación'
    )
    area_total_m2 = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name='Área Total (m²)',
        help_text='Área total de la lotificación en metros cuadrados'
    )
    
    # Campos de auditoría
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Fecha de Actualización')
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lotificaciones_creadas',
        verbose_name='Creado por'
    )
    updated_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lotificaciones_actualizadas',
        verbose_name='Actualizado por'
    )
    
    # Campo para el plano SVG (relación 1:1)
    plano_svg = models.FileField(
        upload_to=plano_svg_upload_path,
        blank=True,
        null=True,
        verbose_name='Plano SVG',
        help_text='Archivo SVG del plano de la lotificación'
    )
    plano_svg_nombre = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Nombre del Archivo SVG',
        help_text='Nombre original del archivo SVG'
    )
    plano_svg_tamaño = models.BigIntegerField(
        blank=True,
        null=True,
        verbose_name='Tamaño del Archivo (bytes)',
        help_text='Tamaño del archivo SVG en bytes'
    )
    plano_svg_fecha_subida = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de Subida del Plano',
        help_text='Fecha en que se subió el plano SVG'
    )

    class Meta:
        verbose_name = 'Lotificación'
        verbose_name_plural = 'Lotificaciones'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Manzana(models.Model):
    """
    Modelo para representar manzanas/bloques
    """
    lotificacion = models.ForeignKey(
        Lotificacion, 
        on_delete=models.CASCADE, 
        related_name='manzanas', 
        verbose_name='Lotificación'
    )
    nombre = models.CharField(max_length=10, verbose_name='Nombre de Manzana')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Manzana'
        verbose_name_plural = 'Manzanas'
        unique_together = ['lotificacion', 'nombre']
        ordering = ['lotificacion', 'nombre']
        indexes = [
            models.Index(fields=['lotificacion', 'nombre'], name='lotes_manzana_lotif_idx'),
        ]

    def __str__(self):
        return f"Manzana {self.nombre} - {self.lotificacion.nombre}"


class Lote(models.Model):
    """
    Modelo para representar lotes disponibles para venta
    """
    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('reservado', 'Reservado'),
        ('pagado', 'Pagado'),
        ('comercial_y_bodega', 'Comercial y Bodega'),
        ('financiado', 'Financiado'),
        ('pagado_y_escriturado', 'Pagado y Escriturado'),
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
    costo_instalacion = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('5000.00'),
        verbose_name='Instalación (Q)'
    )
    
    # Identificador único para SVG (ej: "MZ03-L07")
    identificador = models.CharField(
        max_length=150, 
        unique=True,
        null=True,
        blank=True,
        verbose_name='Identificador SVG',
        help_text='Identificador único que coincide con el id del path en el SVG (ej: MZ03-L07)'
    )
    
    # Override de SVG ID para vinculaciones manuales
    plano_svg_id = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        db_index=True,
        verbose_name='Plano SVG ID (Override)',
        help_text='ID textual exacto del SVG para sobreescribir la vinculacion dinamica'
    )
    
    # Estado y control
    estado = models.CharField(
        max_length=25, 
        choices=ESTADO_CHOICES, 
        default='disponible',
        verbose_name='Estado del Lote'
    )
    
    # Campo para control de concurrencia básico
    version = models.IntegerField(default=0, verbose_name='Versión')
    
    # Auditoría básica
    actualizado_por = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='lotes_actualizados',
        verbose_name='Actualizado por'
    )
    
    activo = models.BooleanField(default=True, verbose_name='Activo')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Lote'
        verbose_name_plural = 'Lotes'
        unique_together = ['manzana', 'numero_lote']
        ordering = ['manzana', 'numero_lote']
        indexes = [
            models.Index(fields=['identificador'], name='lotes_identificador_idx'),
            models.Index(fields=['plano_svg_id'], name='lotes_plano_svg_id_idx'),
            models.Index(fields=['manzana', 'estado'], name='lotes_manzana_estado_idx'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['manzana', 'plano_svg_id'],
                name='unique_plano_svg_per_manzana'
            )
        ]

    def __str__(self):
        return f"Lote {self.numero_lote} - Manzana {self.manzana.nombre}"

    @property
    def saldo_financiar(self):
        """Calcula el saldo a financiar (valor total menos costo de instalación)"""
        if self.valor_total is None or self.costo_instalacion is None:
            return Decimal('0.00')
        return self.valor_total - self.costo_instalacion

    @property
    def valor_total_formateado(self):
        """Retorna el valor total formateado"""
        if self.valor_total is None:
            return "Q 0.00"
        return f"Q {self.valor_total:,.2f}"

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
    def metros_cuadrados_formateados(self):
        """Retorna los metros cuadrados formateados"""
        if self.metros_cuadrados is None:
            return "0 m²"
        return f"{self.metros_cuadrados} m²"

    def save(self, *args, **kwargs):
        """Sobrescribir save para validaciones adicionales y auditoría.

        No se auto-genera identificador aquí: los lotes creados manualmente (sin plano)
        deben mantener identificador=NULL para poder aparecer en "lotes sin identificar"
        y luego relacionarse con un path del SVG. El identificador se asigna al
        registrar desde el plano (registrar_lote) o al relacionar un lote existente.
        """
        # Obtener usuario del contexto si está disponible
        user = kwargs.pop('user', None)
        if user:
            # Verificar si el usuario tiene el atributo is_authenticated (puede ser un objeto User o None)
            if hasattr(user, 'is_authenticated') and user.is_authenticated:
                self.actualizado_por = user
            elif not hasattr(user, 'is_authenticated'):
                # Si es un objeto User sin is_authenticated, asignarlo directamente
                self.actualizado_por = user
        
        # Solo validar si todos los valores están presentes
        if self.valor_total is not None and self.costo_instalacion is not None:
            if self.saldo_financiar <= 0:
                raise ValueError("El saldo a financiar debe ser mayor a 0")
        
        # Incrementar versión en cada actualización
        if self.pk:
            self.version += 1
        
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
