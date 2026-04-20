from decimal import Decimal
from dateutil.relativedelta import relativedelta
from django.utils import timezone
import math

def sincronizar_cuotas(venta):
    """
    Sincroniza y recalcula las cuotas de una venta financiada.
    Si hay cambios en precio, tasa o plazo, recalcula solo las NO pagadas.
    """
    if venta.tipo_pago != 'FINANCIADO':
        # Si ya no es financiado, opcionalmente podrías borrar cuotas no pagadas
        # Pero nos enfocamos en el flujo financiado
        return

    from .models import Cuota, BitacoraCambio

    # 1. Obtener cuotas actuales
    cuotas_totales = venta.cuotas_cobrar.all().order_by('no_cuota')
    cuotas_pagadas = cuotas_totales.filter(estado='Pagado')
    cuotas_pendientes = cuotas_totales.exclude(estado='Pagado')

    conteo_pagadas = cuotas_pagadas.count()
    capital_pagado = sum(c.monto_base for c in cuotas_pagadas)

    # 2. Calcular Nuevo Saldo a Financiar
    # Saldo = Valor Lote (Nuevo) - Enganche - Descuento - Lo ya pagado de capital
    nuevo_saldo_financiar = (venta.valor_lote - venta.enganche - venta.descuento) - capital_pagado
    
    if nuevo_saldo_financiar < 0:
        nuevo_saldo_financiar = Decimal('0.00')

    # 3. Meses/Cuotas Restantes
    # Plazo total - lo ya pagado
    meses_restantes = venta.plazo_meses - conteo_pagadas

    if meses_restantes < 0:
        meses_restantes = 0

    # 4. Ajustar Estructura de Cuotas (Crear o Eliminar Pendientes)
    conteo_pendientes = cuotas_pendientes.count()
    
    # Si el plazo se acorta y hay más pendientes de las permitidas
    if conteo_pendientes > meses_restantes:
        cuotas_a_eliminar = cuotas_pendientes.order_by('-no_cuota')[:(conteo_pendientes - meses_restantes)]
        for c in cuotas_a_eliminar:
            c.delete()
    # Si el plazo se alarga y faltan cuotas
    elif conteo_pendientes < meses_restantes:
        ultima_cuota = cuotas_totales.last()
        num_inicio = ultima_cuota.no_cuota + 1 if ultima_cuota else 1
        fecha_base = ultima_cuota.fecha_vencimiento if ultima_cuota else venta.fecha_creacion.date()
        
        for i in range(num_inicio, venta.plazo_meses + 1):
            nueva_fecha = fecha_base + relativedelta(months=(i - (num_inicio - 1)))
            Cuota.objects.create(
                venta=venta,
                no_cuota=i,
                fecha_vencimiento=nueva_fecha,
                monto_base=Decimal('0.00'), # Se actualizará en el paso 5
                estado='Pendiente'
            )

    # 5. Volver a obtener las pendientes tras el ajuste de estructura
    cuotas_pendientes = venta.cuotas_cobrar.exclude(estado='Pagado').order_by('no_cuota')
    
    # 6. Recalcular Montos (Amortización simple o francesa sugerida por tasa de interés)
    # PMT = PV * (r * (1 + r)^n) / ((1 + r)^n - 1)
    if meses_restantes > 0 and nuevo_saldo_financiar > 0:
        tasa_anual = float(venta.tasa_interes_anual) / 100.0
        r = math.pow(1 + tasa_anual, 1/12) - 1 # Tasa mensual efectiva
        
        if r > 0:
            numerador = float(nuevo_saldo_financiar) * r * math.pow(1 + r, meses_restantes)
            denominador = math.pow(1 + r, meses_restantes) - 1
            cuota_total_mensual = numerador / denominador
        else:
            cuota_total_mensual = float(nuevo_saldo_financiar) / meses_restantes
            
        # Distribución en las cuotas pendientes
        saldo_insoluto = float(nuevo_saldo_financiar)
        for c in cuotas_pendientes:
            interes_de_mes = saldo_insoluto * r
            capital_de_mes = cuota_total_mensual - interes_de_mes
            
            # Ajuste de valores finales
            c.monto_base = Decimal(str(round(capital_de_mes, 2)))
            c.interes_monto = Decimal(str(round(interes_de_mes, 2)))
            c.save()
            
            saldo_insoluto -= capital_de_mes
    
    # 7. Bitácora del Cambio
    BitacoraCambio.objects.create(
        venta=venta,
        descripcion=f"Recálculo de cuotas finalizado. Nuevo saldo a financiar: Q{nuevo_saldo_financiar}. Cuotas restantes: {meses_restantes}."
    )
