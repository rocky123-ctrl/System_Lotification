from celery import shared_task
from django.utils import timezone
from django.db import transaction
from .models import ConfiguracionServicioLote, PagoServicio
from datetime import date
import logging

logger = logging.getLogger(__name__)

@shared_task
def generar_cobros_mensuales():
    """
    Recorre todos los lotes con ConfiguracionServicioLote activo y genera 
    los registros en PagoServicio para el mes actual.
    """
    hoy = timezone.now().date()
    primer_dia_mes = hoy.replace(day=1)
    
    # Obtener todas las configuraciones activas
    configuraciones = ConfiguracionServicioLote.objects.filter(
        esta_activo=True,
        servicio__activo=True
    ).select_related('lote', 'servicio')
    
    count = 0
    for config in configuraciones:
        # Obtener el cliente asociado al lote a través de la Venta más reciente
        venta_activa = config.lote.ventas.first()
        if venta_activa and venta_activa.cliente.estado == 'inactivo':
            # Si el cliente está inactivo, pausar la generación de cobros
            continue

        # Verificar si ya existe un pago para este lote, servicio y mes
        if not PagoServicio.objects.filter(
            lote=config.lote,
            servicio=config.servicio,
            mes_periodo=primer_dia_mes
        ).exists():
            with transaction.atomic():
                PagoServicio.objects.create(
                    lote=config.lote,
                    servicio=config.servicio,
                    mes_periodo=primer_dia_mes,
                    monto_cobrado=config.precio_final,
                    fecha_limite=primer_dia_mes.replace(day=15) # Ejemplo: vence el 15
                )
                count += 1
    
    logger.info(f"Se generaron {count} cobros de servicios para el periodo {primer_dia_mes}")
    return count


@shared_task
def actualizar_estados_vencidos():
    """
    Actualiza el estado de los pagos pendientes a 'Vencido' si la fecha límite ya pasó.
    
    Sugerencia Redis: Se podría usar Redis para cachear los IDs de pagos que están por vencer
    y enviar notificaciones proactivas, o usar un Lock distribuido de Redis para asegurar
    que esta tarea no se solape en entornos multi-worker.
    """
    hoy = timezone.now().date()
    
    actualizados = PagoServicio.objects.filter(
        estado='Pendiente',
        fecha_limite__lt=hoy
    ).update(estado='Vencido')
    
    logger.info(f"Se actualizaron {actualizados} pagos a estado 'Vencido'")
    return actualizados
