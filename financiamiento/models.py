from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from lotes.models import Lote, Manzana


class Financiamiento(models.Model):
    """Modelo para el financiamiento de un lote"""
    lote = models.OneToOneField(Lote, on_delete=models.CASCADE, related_name='financiamiento')
    promitente_comprador = models.CharField(max_length=200, verbose_name="Promitente Comprador")
    
    # Valores financieros
    totalidad = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Totalidad")
    enganche = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Enganche")
    capital_cancelado = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Capital Cancelado")
    interes_cancelado = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Interés Cancelado")
    saldo = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Saldo")
    
    # Plazos y cuotas
    plazo_meses = models.PositiveIntegerField(verbose_name="Plazo en Meses")
    cuota_mensual = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Cuota Mensual")
    cuotas_canceladas = models.PositiveIntegerField(default=0, verbose_name="Cuotas Canceladas")
    cuotas_pendientes = models.PositiveIntegerField(verbose_name="Cuotas Pendientes")
    
    # Fechas importantes
    fecha_inicio_financiamiento = models.DateField(verbose_name="Fecha de Inicio del Financiamiento")
    fecha_vencimiento = models.DateField(verbose_name="Fecha de Vencimiento")
    
    # Estado del financiamiento
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('finalizado', 'Finalizado'),
        ('cancelado', 'Cancelado'),
        ('en_mora', 'En Mora'),
    ]
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo', verbose_name="Estado")
    
    # Campos de auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización")
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='financiamientos_creados')
    actualizado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='financiamientos_actualizados')
    
    class Meta:
        verbose_name = "Financiamiento"
        verbose_name_plural = "Financiamientos"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Financiamiento {self.lote.numero_lote} - {self.promitente_comprador}"
    
    def save(self, *args, **kwargs):
        """Sobrescribir save para calcular automáticamente algunos campos"""
        if not self.pk:  # Si es una nueva creación
            # Solo calcular si los valores necesarios están presentes
            if (self.totalidad is not None and self.enganche is not None and 
                self.plazo_meses is not None and self.fecha_inicio_financiamiento is not None):
                # Calcular saldo inicial
                self.saldo = self.totalidad - self.enganche
                # Calcular cuotas pendientes
                self.cuotas_pendientes = self.plazo_meses
                # Calcular fecha de vencimiento (fecha inicio + plazo en meses)
                from dateutil.relativedelta import relativedelta
                self.fecha_vencimiento = self.fecha_inicio_financiamiento + relativedelta(months=self.plazo_meses)
        
        super().save(*args, **kwargs)
    
    @property
    def saldo_restante(self):
        """Calcular saldo restante"""
        if self.saldo is None or self.capital_cancelado is None:
            return Decimal('0.00')
        return self.saldo - self.capital_cancelado
    
    @property
    def porcentaje_pagado(self):
        """Calcular porcentaje pagado del total"""
        if (self.totalidad is None or self.capital_cancelado is None or 
            self.enganche is None or self.totalidad <= 0):
            return 0
        return ((self.capital_cancelado + self.enganche) / self.totalidad) * 100
    
    @property
    def cuotas_atrasadas(self):
        """Obtener cuotas atrasadas"""
        if not self.pk:  # Si el objeto no está guardado aún
            return 0
        return self.cuotas.filter(estado='atrasada').count()
    
    @property
    def monto_mora_total(self):
        """Calcular monto total de mora"""
        if not self.pk:  # Si el objeto no está guardado aún
            return Decimal('0.00')
        return self.cuotas.filter(estado='atrasada').aggregate(
            total=models.Sum('mora_atraso')
        )['total'] or Decimal('0.00')
    
    def aplicar_pago_capital(self, monto):
        """
        Aplicar un pago a capital y recalcular las cuotas pendientes
        """
        if monto <= 0:
            raise ValueError("El monto del pago a capital debe ser mayor a 0")
        
        if monto > self.saldo_restante:
            raise ValueError("El monto del pago a capital no puede exceder el saldo restante")
        
        # Actualizar capital cancelado
        self.capital_cancelado += monto
        
        # Recalcular cuotas pendientes
        self.recalcular_cuotas_por_pago_capital(monto)
        
        # Verificar si el financiamiento está pagado
        if self.saldo_restante <= 0:
            self.estado = 'finalizado'
            self.cuotas_pendientes = 0
        
        self.save()
        
        return True
    
    def recalcular_cuotas_por_pago_capital(self, monto_pago_capital):
        """
        Recalcular las cuotas pendientes después de un pago a capital
        Usa la fórmula de amortización para recalcular correctamente capital e intereses
        Siempre usa la tasa anual de ConfiguracionGeneral
        """
        from configuracion.models import ConfiguracionGeneral
        
        # Obtener la configuración general
        config = ConfiguracionGeneral.objects.first()
        if not config:
            raise ValueError("No se encontró configuración general. Configure primero la tasa anual.")
        
        # Usar la tasa anual de la configuración y convertir a mensual
        tasa_anual = config.tasa_anual
        if tasa_anual <= 0:
            raise ValueError("La tasa anual debe ser mayor a 0")
        
        # Convertir tasa anual a mensual usando la fórmula correcta
        # tasa_mensual = (1 + tasa_anual)^(1/12) - 1
        tasa_anual_decimal = tasa_anual / Decimal('100')
        tasa_mensual_decimal = (Decimal('1') + tasa_anual_decimal) ** (Decimal('1') / Decimal('12')) - Decimal('1')
        tasa_mensual = tasa_mensual_decimal * Decimal('100')
        
        # Calcular nuevo saldo restante después del pago a capital
        nuevo_saldo = self.saldo_restante - monto_pago_capital
        
        if nuevo_saldo <= 0:
            # Si el saldo es 0 o negativo, todas las cuotas se cancelan
            self.cuotas.filter(estado='pendiente').update(
                estado='cancelada',
                monto_capital=Decimal('0.00'),
                monto_interes=Decimal('0.00'),
                monto_total=Decimal('0.00')
            )
            self.cuotas_pendientes = 0
            return
        
        # Obtener cuotas pendientes ordenadas por fecha de vencimiento
        cuotas_pendientes = self.cuotas.filter(estado='pendiente').order_by('fecha_vencimiento')
        
        if not cuotas_pendientes.exists():
            return
        
        # Calcular nueva cuota mensual usando la fórmula de amortización
        tasa_decimal = tasa_mensual / 100
        num_cuotas_pendientes = cuotas_pendientes.count()
        
        if tasa_decimal > 0:
            # Fórmula de amortización: PMT = PV * (r * (1 + r)^n) / ((1 + r)^n - 1)
            nueva_cuota_mensual = nuevo_saldo * (tasa_decimal * (1 + tasa_decimal)**num_cuotas_pendientes) / ((1 + tasa_decimal)**num_cuotas_pendientes - 1)
        else:
            nueva_cuota_mensual = nuevo_saldo / num_cuotas_pendientes
        
        # Actualizar cuota mensual del financiamiento
        self.cuota_mensual = nueva_cuota_mensual
        
        # Recalcular cada cuota pendiente con el nuevo saldo
        saldo_pendiente = nuevo_saldo
        
        for i, cuota in enumerate(cuotas_pendientes):
            if saldo_pendiente <= 0:
                # Si no hay saldo pendiente, cancelar la cuota
                cuota.estado = 'cancelada'
                cuota.monto_capital = Decimal('0.00')
                cuota.monto_interes = Decimal('0.00')
                cuota.monto_total = Decimal('0.00')
            else:
                # Calcular interés sobre el saldo pendiente
                monto_interes = saldo_pendiente * tasa_decimal
                
                # El capital es la diferencia entre la cuota y el interés
                monto_capital = nueva_cuota_mensual - monto_interes
                
                # Asegurar que el capital no exceda el saldo pendiente
                if monto_capital > saldo_pendiente:
                    monto_capital = saldo_pendiente
                    monto_interes = nueva_cuota_mensual - monto_capital
                
                # Actualizar la cuota
                cuota.monto_capital = monto_capital
                cuota.monto_interes = monto_interes
                cuota.monto_total = nueva_cuota_mensual
                
                # Reducir el saldo pendiente por el capital pagado
                saldo_pendiente -= monto_capital
                
                # Mantener el estado como pendiente
                cuota.estado = 'pendiente'
            
            cuota.save()
        
        # Actualizar el número de cuotas pendientes
        self.cuotas_pendientes = self.cuotas.filter(estado='pendiente').count()
        
        # Verificar si todas las cuotas están pagadas
        if self.cuotas_pendientes == 0:
            self.estado = 'finalizado'


class Cuota(models.Model):
    """Modelo para las cuotas individuales del financiamiento"""
    financiamiento = models.ForeignKey(Financiamiento, on_delete=models.CASCADE, related_name='cuotas')
    numero_cuota = models.PositiveIntegerField(verbose_name="Número de Cuota")
    
    # Valores de la cuota
    monto_capital = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Monto Capital")
    monto_interes = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Monto Interés")
    monto_total = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Monto Total")
    
    # Fechas
    fecha_vencimiento = models.DateField(verbose_name="Fecha de Vencimiento")
    fecha_pago = models.DateField(null=True, blank=True, verbose_name="Fecha de Pago")
    
    # Estado y mora
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('atrasada', 'Atrasada'),
        ('parcial', 'Pago Parcial'),
    ]
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', verbose_name="Estado")
    
    # Campos de mora
    mora_atraso = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Mora por Atraso")
    dias_atraso = models.PositiveIntegerField(default=0, verbose_name="Días de Atraso")
    
    # Campos de auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización")
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cuotas_creadas')
    actualizado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cuotas_actualizadas')
    
    class Meta:
        verbose_name = "Cuota"
        verbose_name_plural = "Cuotas"
        ordering = ['financiamiento', 'numero_cuota']
        unique_together = ['financiamiento', 'numero_cuota']
    
    def __str__(self):
        return f"Cuota {self.numero_cuota} - {self.financiamiento.promitente_comprador}"
    
    def calcular_mora(self):
        """Calcular mora si la cuota está atrasada"""
        from django.utils import timezone
        from datetime import date
        
        if (self.estado == 'pendiente' and self.fecha_vencimiento is not None and 
            self.fecha_vencimiento < date.today() and self.monto_total is not None):
            # Calcular días de atraso
            self.dias_atraso = (date.today() - self.fecha_vencimiento).days
            
            # Obtener configuración de penalización
            try:
                config_financiera = self.financiamiento.lote.manzana.configuracion_financiera
                if config_financiera.aplicar_penalizacion_atrasos:
                    # Calcular mora (porcentaje diario o mensual según configuración)
                    tasa_penalizacion = config_financiera.penalizacion_atraso_porcentaje / 100
                    self.mora_atraso = self.monto_total * tasa_penalizacion * (self.dias_atraso / 30)
                else:
                    self.mora_atraso = Decimal('0.00')
            except:
                # Si no hay configuración, usar 5% mensual por defecto
                self.mora_atraso = self.monto_total * Decimal('0.05') * (self.dias_atraso / 30)
            
            self.estado = 'atrasada'
            self.save()


class Pago(models.Model):
    """Modelo para el historial de pagos realizados"""
    cuota = models.ForeignKey(Cuota, on_delete=models.CASCADE, related_name='pagos')
    financiamiento = models.ForeignKey(Financiamiento, on_delete=models.CASCADE, related_name='pagos')
    
    # Montos del pago
    monto_capital = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Monto Capital")
    monto_interes = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Monto Interés")
    monto_mora = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Monto Mora")
    monto_total = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Monto Total")
    
    # Información del pago
    fecha_pago = models.DateField(verbose_name="Fecha de Pago")
    metodo_pago = models.CharField(max_length=50, verbose_name="Método de Pago")
    referencia_pago = models.CharField(max_length=100, blank=True, null=True, verbose_name="Referencia de Pago")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    
    # Campos de auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='pagos_creados')
    
    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ['-fecha_pago', '-fecha_creacion']
    
    def __str__(self):
        return f"Pago {self.id} - {self.financiamiento.promitente_comprador} - {self.fecha_pago}"
    
    def generar_referencia_automatica(self):
        """Generar referencia automática con formato REF-{numero:03d}-{lote_manzana}"""
        # Obtener el número de recibo (total de pagos + 1)
        total_pagos = Pago.objects.count()
        numero_recibo = total_pagos + 1
        
        # Obtener lote y manzana
        lote = self.financiamiento.lote
        manzana = lote.manzana.nombre if lote.manzana else "X"
        lote_manzana = f"{manzana}{lote.numero_lote}"
        
        # Generar referencia
        referencia = f"REF-{numero_recibo:03d}-{lote_manzana}"
        return referencia
    
    def save(self, *args, **kwargs):
        """Sobrescribir save para actualizar financiamiento y cuota"""
        is_new = self.pk is None
        
        # Generar referencia automática si es nuevo y no tiene referencia
        if is_new and not self.referencia_pago:
            self.referencia_pago = self.generar_referencia_automatica()
        
        super().save(*args, **kwargs)
        
        if is_new:
            # Validar que los montos no sean None
            monto_capital = self.monto_capital or Decimal('0.00')
            monto_interes = self.monto_interes or Decimal('0.00')
            
            # Actualizar cuota
            self.cuota.fecha_pago = self.fecha_pago
            self.cuota.mora_atraso = Decimal('0.00')  # Resetear mora
            self.cuota.dias_atraso = 0
            self.cuota.estado = 'pagada'
            self.cuota.save()
            
            # Actualizar financiamiento
            self.financiamiento.capital_cancelado = (self.financiamiento.capital_cancelado or Decimal('0.00')) + monto_capital
            self.financiamiento.interes_cancelado = (self.financiamiento.interes_cancelado or Decimal('0.00')) + monto_interes
            self.financiamiento.cuotas_canceladas = (self.financiamiento.cuotas_canceladas or 0) + 1
            self.financiamiento.cuotas_pendientes = (self.financiamiento.cuotas_pendientes or 0) - 1
            self.financiamiento.save()
            
            # Verificar si el financiamiento está finalizado
            if self.financiamiento.cuotas_pendientes == 0:
                self.financiamiento.estado = 'finalizado'
                self.financiamiento.save()


class ConfiguracionPago(models.Model):
    """Modelo para configurar las fechas de pago"""
    TIPO_PAGO_CHOICES = [
        ('fin_mes', 'Fin de Mes'),
        ('quincena', 'Quincena'),
        ('especifico', 'Día Específico'),
    ]
    
    tipo_pago = models.CharField(max_length=20, choices=TIPO_PAGO_CHOICES, verbose_name="Tipo de Pago")
    dia_pago = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        verbose_name="Día de Pago",
        help_text="Día del mes para el pago (1-31)"
    )
    descripcion = models.CharField(max_length=200, verbose_name="Descripción")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    
    class Meta:
        verbose_name = "Configuración de Pago"
        verbose_name_plural = "Configuraciones de Pago"
    
    def __str__(self):
        return f"{self.get_tipo_pago_display()} - Día {self.dia_pago}"


class PagoCapital(models.Model):
    """Modelo para registrar pagos adelantados a capital"""
    financiamiento = models.ForeignKey(Financiamiento, on_delete=models.CASCADE, related_name='pagos_capital')
    monto = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Monto del Pago")
    fecha_pago = models.DateField(verbose_name="Fecha de Pago")
    concepto = models.CharField(max_length=200, verbose_name="Concepto", blank=True, null=True)
    referencia_pago = models.CharField(max_length=100, blank=True, null=True, verbose_name="Referencia de Pago")
    
    # Campos de auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='pagos_capital_creados')
    
    class Meta:
        verbose_name = "Pago a Capital"
        verbose_name_plural = "Pagos a Capital"
        ordering = ['-fecha_pago']
    
    def __str__(self):
        return f"Pago Capital {self.financiamiento.lote.numero_lote} - Q{self.monto}"
    
    def save(self, *args, **kwargs):
        """Sobrescribir save para generar referencia automática y aplicar el pago"""
        is_new = self.pk is None
        
        if is_new:
            # Generar referencia automática si no se proporciona
            if not self.referencia_pago:
                self.referencia_pago = self.generar_referencia_automatica()
            
            # Aplicar el pago a capital
            self.financiamiento.aplicar_pago_capital(self.monto)
        
        super().save(*args, **kwargs)
    
    def generar_referencia_automatica(self):
        """Generar referencia automática para el pago a capital"""
        total_pagos_capital = PagoCapital.objects.count()
        numero_recibo = total_pagos_capital + 1
        lote = self.financiamiento.lote
        manzana = lote.manzana.nombre if lote.manzana else "X"
        lote_manzana = f"{manzana}{lote.numero_lote}"
        return f"CAP-{numero_recibo:03d}-{lote_manzana}"
