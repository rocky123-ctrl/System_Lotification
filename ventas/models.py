from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal

class Venta(models.Model):
    TIPO_PAGO_CHOICES = [
        ('CONTADO', 'Contado'),
        ('FINANCIADO', 'Financiado'),
    ]

    FORMA_PAGO_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('TARJETA', 'Tarjeta'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('DEPOSITO', 'Depósito'),
    ]

    ESTADO_VENTA_CHOICES = [
        ('GENERADA', 'Generada'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    ]

    cliente = models.ForeignKey(
        'clientes.Cliente', 
        on_delete=models.PROTECT, 
        related_name='ventas',
        verbose_name='Cliente'
    )
    lote = models.ForeignKey(
        'lotes.Lote', 
        on_delete=models.PROTECT, 
        related_name='ventas',
        verbose_name='Lote'
    )

    valor_lote = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Valor del Lote')
    enganche = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Enganche')
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Descuento')
    monto_financiar = models.DecimalField(max_digits=12, decimal_places=2, blank=True, verbose_name='Monto a Financiar')
    tasa_interes_anual = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Tasa de Interés Anual (%)')
    total_pagar_contado = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name='Total a Pagar Contado')
    
    tipo_pago = models.CharField(max_length=20, choices=TIPO_PAGO_CHOICES, default='FINANCIADO', verbose_name='Tipo de Pago')
    forma_pago = models.CharField(max_length=20, choices=FORMA_PAGO_CHOICES, default='EFECTIVO', verbose_name='Forma de Pago')
    acepta_instalacion = models.BooleanField(default=False, verbose_name='Acepta Instalación')
    plazo_meses = models.IntegerField(default=0, verbose_name='Plazo en Meses')
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_VENTA_CHOICES, 
        default='GENERADA',
        verbose_name='Estado de la Venta'
    )

    vendedor = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        related_name='ventas_realizadas',
        null=True,
        blank=True,
        verbose_name='Vendedor'
    )
    comision_monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Monto de Comisión'
    )

    # Campos calculados para optimización (Evita JOINs pesados)
    total_pagado_calculado = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Total Pagado')
    saldo_pendiente_calculado = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Saldo Pendiente')
    cuotas_vencidas_calculado = models.IntegerField(default=0, verbose_name='Cuotas Vencidas')

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        db_table = 'ventas_venta'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Venta {self.tipo_pago} - Lote {self.lote.numero_lote} a {self.cliente.nombres}"

    def clean(self):
        # Validar si el lote ya no está disponible antes de crear
        if not self.pk:
            if self.lote.estado_disponibilidad != 'disponible':
                raise ValidationError(f"El lote {self.lote.numero_lote} no está disponible para venta. Estado actual: {self.lote.get_estado_disponibilidad_display()}")

        # Re-calcular monto a financiar (Verdad lógica en el servidor)
        # Se incluye el costo de instalación si se aceptó y se resta el descuento
        costo_instalacion = self.lote.costo_instalacion if self.acepta_instalacion else Decimal('0.00')
        self.valor_lote = (self.lote.valor_total + costo_instalacion) - self.descuento
        monto_calculado = self.valor_lote - self.enganche
        
        if self.tipo_pago == 'FINANCIADO':
            if self.plazo_meses <= 0:
                raise ValidationError("Para ventas financiadas, el plazo en meses debe ser mayor a 0.")
            self.monto_financiar = max(Decimal('0.00'), monto_calculado)
            self.total_pagar_contado = Decimal('0.00')
        else:
            # Si es Al Contado, reseteamos plazo e interés
            self.monto_financiar = Decimal('0.00')
            self.plazo_meses = 0
            self.tasa_interes_anual = 0
            self.total_pagar_contado = max(Decimal('0.00'), self.valor_lote)

        super().clean()

    def save(self, *args, **kwargs):
        from django.db import transaction
        self.clean()
        
        is_new = self.pk is None
        
        # Calcular comisión si hay vendedor y es una venta nueva
        if is_new and self.vendedor:
            # Regla de Negocio: Vendedores que son Admins (Staff/Superuser) no cobran comisión.
            if self.vendedor.is_staff or self.vendedor.is_superuser:
                self.comision_monto = Decimal('0.00')
            else:
                from empleados.models import Empleado
                # Primero intentamos obtener el empleado asociado al usuario
                empleado = Empleado.objects.filter(usuario=self.vendedor).first()
                if empleado and empleado.porcentaje_comision:
                    # Comision = Valor Promesa * (Porcentaje / 100)
                    base_comision = self.valor_lote
                    self.comision_monto = base_comision * (empleado.porcentaje_comision / Decimal('100.00'))

        with transaction.atomic():
            super().save(*args, **kwargs)
 
            if is_new:
                # Cambiar el estado del lote automáticamente de forma atómica
                nuevo_estado = 'pagado' if self.tipo_pago == 'CONTADO' else 'financiado'
                
                estado_anterior = self.lote.estado_disponibilidad
                self.lote.estado_disponibilidad = nuevo_estado
                self.lote.save()
                
                # Registrar en historial
                from lotes.models import HistorialLote
                HistorialLote.objects.create(
                    lote=self.lote,
                    estado_disponibilidad_anterior=estado_anterior,
                    estado_disponibilidad_nuevo=nuevo_estado,
                    notas=f"Venta registrada ({self.tipo_pago})"
                )
                
                # Crear liquidacion de comision
                if float(self.comision_monto) > 0 and self.vendedor:
                    LiquidacionComision.objects.create(
                        venta=self,
                        vendedor=self.vendedor,
                        monto_pagado=self.comision_monto,
                        estado_pago='PENDIENTE'
                    )

                # Generar el plan de financiamiento y cuotas en el módulo de financiamiento si aplica
                if self.tipo_pago == 'FINANCIADO':
                    self.crear_plan_financiamiento()
            
            # Sincronización de cuotas: debe ejecutarse tanto al crear como al editar.
            from cuentas_cobrar.logic import sincronizar_cuotas
            sincronizar_cuotas(self)
            self.actualizar_totales()
            
            # Asegurarnos que el estado del lote coincida (útil para ediciones)
            if not is_new and self.lote.estado_disponibilidad != 'escriturado':
                estado_esperado_lote = 'pagado' if self.tipo_pago == 'CONTADO' else 'financiado'
                if self.lote.estado_disponibilidad != estado_esperado_lote:
                    self.lote.estado_disponibilidad = estado_esperado_lote
                    self.lote.save()

    def actualizar_totales(self):
        from cuentas_cobrar.models import Cuota
        from django.utils import timezone
        
        # Calcular total pagado (basado en cuotas pagadas o pagos activos)
        cuotas = self.cuotas_cobrar.all()
        pagadas = cuotas.filter(estado='Pagado')
        
        total_pagado = sum(c.monto_cuota for c in pagadas)
        saldo_pendiente = self.monto_financiar - total_pagado
        
        cuotas_vencidas = cuotas.filter(
            estado='Pendiente', 
            fecha_programada__lt=timezone.now().date()
        ).count()
        
        self.total_pagado_calculado = total_pagado
        self.saldo_pendiente_calculado = max(Decimal('0.00'), saldo_pendiente)
        self.cuotas_vencidas_calculado = cuotas_vencidas
        
        estado_nuevo = self.estado
        if self.estado != 'CANCELADA':
            if self.tipo_pago == 'FINANCIADO':
                if cuotas.count() > 0 and pagadas.count() == cuotas.count():
                    estado_nuevo = 'COMPLETADA'
                else:
                    estado_nuevo = 'GENERADA'
            elif self.tipo_pago == 'CONTADO':
                estado_nuevo = 'COMPLETADA'
                
        self.estado = estado_nuevo

        # Evitamos el loop infinito usando update_fields si es posible, o save sin logic pesado
        Venta.objects.filter(pk=self.pk).update(
            total_pagado_calculado=self.total_pagado_calculado,
            saldo_pendiente_calculado=self.saldo_pendiente_calculado,
            cuotas_vencidas_calculado=self.cuotas_vencidas_calculado,
            estado=self.estado
        )

    def crear_plan_financiamiento(self):
        """Genera el financiamiento y las cuotas iniciales"""
        from financiamiento.models import Financiamiento, Cuota
        from dateutil.relativedelta import relativedelta
        from django.utils import timezone
        import math

        # Tasa efectiva mensual
        tasa_anual_decimal = float(self.tasa_interes_anual) / 100.0
        tasa_mensual_efectiva = math.pow(1 + tasa_anual_decimal, 1 / 12) - 1
        
        cuota_mensual = 0
        if self.plazo_meses > 0 and float(self.monto_financiar) > 0:
            if tasa_mensual_efectiva > 0:
                numerador = float(self.monto_financiar) * tasa_mensual_efectiva * math.pow(1 + tasa_mensual_efectiva, self.plazo_meses)
                denominador = math.pow(1 + tasa_mensual_efectiva, self.plazo_meses) - 1
                cuota_mensual = numerador / denominador
            else:
                cuota_mensual = float(self.monto_financiar) / self.plazo_meses

        financiamiento = Financiamiento.objects.create(
            lote=self.lote,
            promitente_comprador=f"{self.cliente.nombres} {self.cliente.apellidos}",
            totalidad=self.valor_lote,
            enganche=self.enganche,
            saldo=self.monto_financiar,
            plazo_meses=self.plazo_meses,
            cuota_mensual=Decimal(str(round(cuota_mensual, 2))),
            cuotas_pendientes=self.plazo_meses,
            fecha_inicio_financiamiento=timezone.now().date(),
            estado='activo'
        )

        # Generar cuotas
        saldo_insoluto = float(self.monto_financiar)
        fecha_vencimiento = timezone.now().date() + relativedelta(months=1)

        for i in range(1, self.plazo_meses + 1):
            interes_cuota = saldo_insoluto * tasa_mensual_efectiva
            capital_cuota = cuota_mensual - interes_cuota
            
            # Ajuste de última cuota
            if i == self.plazo_meses:
                capital_cuota = saldo_insoluto
                cuota_mensual = capital_cuota + interes_cuota

            Cuota.objects.create(
                financiamiento=financiamiento,
                numero_cuota=i,
                monto_capital=Decimal(str(round(capital_cuota, 2))),
                monto_interes=Decimal(str(round(interes_cuota, 2))),
                monto_total=Decimal(str(round(cuota_mensual, 2))),
                fecha_vencimiento=fecha_vencimiento,
                estado='pendiente'
            )
            
            saldo_insoluto -= capital_cuota
            fecha_vencimiento += relativedelta(months=1)

class LiquidacionComision(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('PAGADO', 'Pagado'),
    ]

    venta = models.OneToOneField(Venta, on_delete=models.CASCADE, related_name='liquidacion_comision')
    vendedor = models.ForeignKey('auth.User', on_delete=models.PROTECT, related_name='liquidaciones')
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Monto de Comisión')
    fecha_pago = models.DateField(null=True, blank=True, verbose_name='Fecha de Pago')
    es_pago_inmediato = models.BooleanField(default=False, verbose_name='Es Pago Inmediato')
    referencia_pago = models.CharField(max_length=100, null=True, blank=True, verbose_name='Referencia de Pago')
    estado_pago = models.CharField(max_length=20, default='PENDIENTE', choices=ESTADO_CHOICES)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ventas_liquidacion'
        verbose_name = 'Liquidación de Comisión'
        verbose_name_plural = 'Liquidaciones de Comisiones'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Liquidación {self.estado_pago} - Venta {self.venta.id} - Vendedor {self.vendedor.username}"

class Cotizacion(models.Model):
    TIPO_PAGO_CHOICES = Venta.TIPO_PAGO_CHOICES
    FORMA_PAGO_CHOICES = Venta.FORMA_PAGO_CHOICES

    cliente = models.ForeignKey(
        'clientes.Cliente', 
        on_delete=models.SET_NULL, 
        related_name='cotizaciones',
        null=True,
        blank=True,
        verbose_name='Cliente'
    )
    nombre_prospecto = models.CharField(max_length=150, null=True, blank=True, verbose_name='Nombre del Prospecto')
    telefono_prospecto = models.CharField(max_length=20, null=True, blank=True, verbose_name='Teléfono del Prospecto')
    
    lote = models.ForeignKey(
        'lotes.Lote', 
        on_delete=models.PROTECT, 
        related_name='cotizaciones',
        verbose_name='Lote'
    )

    valor_lote = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Valor del Lote')
    enganche = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Enganche')
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Descuento')
    monto_financiar = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name='Monto a Financiar')
    tasa_interes_anual = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Tasa de Interés Anual (%)')
    total_pagar_contado = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name='Total a Pagar Contado')
    
    tipo_pago = models.CharField(max_length=20, choices=TIPO_PAGO_CHOICES, default='FINANCIADO', verbose_name='Tipo de Pago')
    forma_pago = models.CharField(max_length=20, choices=FORMA_PAGO_CHOICES, default='EFECTIVO', verbose_name='Forma de Pago')
    acepta_instalacion = models.BooleanField(default=False, verbose_name='Acepta Instalación')
    plazo_meses = models.IntegerField(default=0, verbose_name='Plazo en Meses')

    vendedor = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        related_name='cotizaciones_realizadas',
        null=True,
        blank=True,
        verbose_name='Vendedor'
    )

    ESTADO_COTIZACION_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('ACEPTADA', 'Aceptada'),
        ('RECHAZADA', 'Rechazada'),
        ('VENCIDA', 'Vencida'),
    ]

    fecha_vencimiento = models.DateField(verbose_name='Fecha de Vencimiento')
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_COTIZACION_CHOICES, 
        default='PENDIENTE',
        verbose_name='Estado'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cotización'
        verbose_name_plural = 'Cotizaciones'
        db_table = 'ventas_cotizacion'
        ordering = ['-fecha_creacion']

    def __str__(self):
        cliente_nombre = self.cliente.nombres if self.cliente else self.nombre_prospecto
        return f"Cotización Lote {self.lote.numero_lote} - {cliente_nombre}"

    @property
    def es_vencida(self):
        from django.utils import timezone
        return self.fecha_vencimiento < timezone.now().date()

    def clean(self):
        if not self.cliente and not self.nombre_prospecto:
            raise ValidationError("Debe especificar un cliente registrado o un nombre de prospecto.")

        costo_instalacion = self.lote.costo_instalacion if self.acepta_instalacion else Decimal('0.00')
        self.valor_lote = (self.lote.valor_total + costo_instalacion) - self.descuento
        monto_calculado = self.valor_lote - self.enganche
        
        if self.tipo_pago == 'FINANCIADO':
            if self.plazo_meses <= 0:
                raise ValidationError("Para cotizaciones financiadas, el plazo en meses debe ser mayor a 0.")
            self.monto_financiar = max(Decimal('0.00'), monto_calculado)
            self.total_pagar_contado = Decimal('0.00')
        else:
            self.monto_financiar = Decimal('0.00')
            self.plazo_meses = 0
            self.tasa_interes_anual = 0
            self.total_pagar_contado = max(Decimal('0.00'), self.valor_lote)

        super().clean()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


