from decimal import Decimal
from dateutil.relativedelta import relativedelta
from django.utils import timezone
import math

def sincronizar_cuotas(venta):
    """
    Sincroniza y recalcula las cuotas de una venta financiada.
    Si hay cambios en precio, tasa o plazo, actualiza TODAS las cuotas registradas.
    Si se cambia a contado, elimina las cuotas.
    """
    from .models import Cuota, BitacoraCambio

    if venta.tipo_pago != 'FINANCIADO':
        Cuota.objects.filter(venta=venta).delete()
        return

    from dateutil.relativedelta import relativedelta
    from decimal import Decimal
    from django.utils import timezone
    import math

    tasa_anual = float(venta.tasa_interes_anual) / 100.0
    r = round(tasa_anual / 12.0, 12) # Tasa mensual efectiva
    
    total_financiar = float(venta.monto_financiar)
    plazo_meses = venta.plazo_meses

    if r > 0 and plazo_meses > 0:
        numerador = total_financiar * r * math.pow(1 + r, plazo_meses)
        denominador = math.pow(1 + r, plazo_meses) - 1
        cuota_mensual = numerador / denominador
    elif plazo_meses > 0:
        cuota_mensual = total_financiar / plazo_meses
    else:
        cuota_mensual = 0

    monto_cuota_decimal = Decimal(str(round(cuota_mensual, 2)))

    cuotas_totales = venta.cuotas_cobrar.all().order_by('no_cuota')
    conteo_actual = cuotas_totales.count()

    if conteo_actual == 0:
        fecha_vencimiento = timezone.now().date() + relativedelta(months=1)
        for i in range(1, plazo_meses + 1):
            Cuota.objects.create(
                venta=venta,
                no_cuota=i,
                monto_cuota=monto_cuota_decimal,
                fecha_programada=fecha_vencimiento,
                estado='Pendiente'
            )
            fecha_vencimiento += relativedelta(months=1)
    else:
        for c in cuotas_totales:
            c.monto_cuota = monto_cuota_decimal
            c.save()

        if plazo_meses > conteo_actual:
            ultima_cuota = cuotas_totales.last()
            fecha_base = ultima_cuota.fecha_programada if ultima_cuota else timezone.now().date()
            for i in range(conteo_actual + 1, plazo_meses + 1):
                fecha_base += relativedelta(months=1)
                Cuota.objects.create(
                    venta=venta,
                    no_cuota=i,
                    monto_cuota=monto_cuota_decimal,
                    fecha_programada=fecha_base,
                    estado='Pendiente'
                )
        elif plazo_meses < conteo_actual:
            cuotas_a_eliminar = cuotas_totales.filter(no_cuota__gt=plazo_meses)
            cuotas_a_eliminar.delete()

    BitacoraCambio.objects.create(
        venta=venta,
        descripcion=f"Recálculo de cuotas (todas las cuotas). Nuevo monto: Q{monto_cuota_decimal}. Total meses: {plazo_meses}."
    )
