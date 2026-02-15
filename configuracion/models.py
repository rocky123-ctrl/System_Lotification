from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class ConfiguracionGeneral(models.Model):
    """
    Modelo para la configuración general de la lotificación
    """
    # Información General
    nombre_lotificacion = models.CharField(
        max_length=200, 
        verbose_name='Nombre de la Lotificación',
        default='Lotificación San Carlos'
    )
    ubicacion = models.CharField(
        max_length=200, 
        verbose_name='Ubicación',
        default='Villa Nueva, Guatemala'
    )
    descripcion = models.TextField(
        verbose_name='Descripción',
        default='Proyecto residencial con lotes de alta calidad en zona privilegiada'
    )
    direccion_completa = models.TextField(
        verbose_name='Dirección Completa',
        default='Km 25 Carretera a El Salvador, Guatemala'
    )
    
    # Información de Contacto
    telefono = models.CharField(
        max_length=20, 
        verbose_name='Teléfono',
        default='+502 2234-5678'
    )
    email = models.EmailField(
        verbose_name='Email',
        default='info@lotificacionsancarlos.com'
    )
    sitio_web = models.URLField(
        verbose_name='Sitio Web',
        default='www.lotificacionsancarlos.com',
        blank=True
    )
    
    # Datos del Proyecto
    fecha_inicio = models.DateField(
        verbose_name='Fecha de Inicio',
        default='2024-01-15'
    )
    total_lotes = models.IntegerField(
        verbose_name='Total de Lotes',
        default=96,
        validators=[MinValueValidator(1)]
    )
    area_total = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name='Área Total (m²)',
        default=15000.00,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Configuración Financiera
    tasa_anual = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        verbose_name='Tasa Anual (%)',
        default=Decimal('12.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('100.00'))
        ],
        help_text='Tasa de interés anual en porcentaje'
    )
    tasa_mensual = models.DecimalField(
        max_digits=5, 
        decimal_places=4, 
        verbose_name='Tasa Mensual (%)',
        default=Decimal('0.9489'),
        validators=[
            MinValueValidator(Decimal('0.0000')),
            MaxValueValidator(Decimal('100.0000'))
        ],
        help_text='Tasa de interés mensual en porcentaje (calculada automáticamente)'
    )
    
    # Archivos
    logo = models.ImageField(
        upload_to='configuracion/logos/',
        verbose_name='Logo de la Empresa',
        blank=True,
        null=True,
        help_text='Logo principal de la lotificación'
    )
    
    # Control
    activo = models.BooleanField(
        default=True, 
        verbose_name='Configuración Activa'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración General'
        verbose_name_plural = 'Configuraciones Generales'
        ordering = ['-fecha_actualizacion']

    def __str__(self):
        return f"Configuración: {self.nombre_lotificacion}"

    def save(self, *args, **kwargs):
        """Sobrescribir save para calcular tasa mensual automáticamente"""
        # Calcular tasa mensual basada en la tasa anual
        if self.tasa_anual > 0:
            # Fórmula: tasa_mensual = (1 + tasa_anual/100)^(1/12) - 1
            tasa_anual_decimal = self.tasa_anual / Decimal('100')
            exponente = Decimal('1') / Decimal('12')
            self.tasa_mensual = ((Decimal('1') + tasa_anual_decimal) ** exponente - Decimal('1')) * Decimal('100')
        
        super().save(*args, **kwargs)

    @property
    def tasa_anual_formateada(self):
        """Retorna la tasa anual formateada"""
        return f"{self.tasa_anual}%"

    @property
    def tasa_mensual_formateada(self):
        """Retorna la tasa mensual formateada"""
        return f"{self.tasa_mensual:.4f}%"

    @property
    def area_total_formateada(self):
        """Retorna el área total formateada"""
        return f"{self.area_total:,.2f} m²"

    @property
    def fecha_inicio_formateada(self):
        """Retorna la fecha de inicio formateada"""
        return self.fecha_inicio.strftime('%d/%m/%Y')

    @classmethod
    def get_configuracion_activa(cls):
        """Obtener la configuración activa"""
        return cls.objects.filter(activo=True).first()

    @classmethod
    def get_or_create_configuracion(cls):
        """Obtener configuración existente o crear una nueva"""
        config = cls.get_configuracion_activa()
        if not config:
            config = cls.objects.create()
        return config


class ConfiguracionFinanciera(models.Model):
    """
    Modelo para configuraciones financieras adicionales
    """
    configuracion = models.OneToOneField(
        ConfiguracionGeneral, 
        on_delete=models.CASCADE, 
        related_name='configuracion_financiera'
    )
    
    # Plazos de financiamiento
    plazo_minimo_meses = models.IntegerField(
        verbose_name='Plazo Mínimo (meses)',
        default=12,
        validators=[MinValueValidator(1)]
    )
    plazo_maximo_meses = models.IntegerField(
        verbose_name='Plazo Máximo (meses)',
        default=60,
        validators=[MinValueValidator(1)]
    )
    
    # Porcentajes de enganche
    enganche_minimo_porcentaje = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        verbose_name='Enganche Mínimo (%)',
        default=Decimal('20.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('100.00'))
        ]
    )
    enganche_maximo_porcentaje = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        verbose_name='Enganche Máximo (%)',
        default=Decimal('50.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('100.00'))
        ]
    )
    
    # Costos adicionales
    costo_instalacion_default = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name='Costo de Instalación por Defecto (Q)',
        default=Decimal('5000.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Configuraciones adicionales
    permitir_pagos_anticipados = models.BooleanField(
        verbose_name='Permitir Pagos Anticipados',
        default=True
    )
    aplicar_penalizacion_atrasos = models.BooleanField(
        verbose_name='Aplicar Penalización por Atrasos',
        default=True
    )
    penalizacion_atraso_porcentaje = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        verbose_name='Penalización por Atraso (%)',
        default=Decimal('5.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('100.00'))
        ]
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración Financiera'
        verbose_name_plural = 'Configuraciones Financieras'

    def __str__(self):
        return f"Configuración Financiera - {self.configuracion.nombre_lotificacion}"

    def save(self, *args, **kwargs):
        """Validaciones adicionales"""
        if self.plazo_minimo_meses >= self.plazo_maximo_meses:
            raise ValueError("El plazo mínimo debe ser menor al plazo máximo")
        
        if self.enganche_minimo_porcentaje >= self.enganche_maximo_porcentaje:
            raise ValueError("El enganche mínimo debe ser menor al enganche máximo")
        
        super().save(*args, **kwargs)
