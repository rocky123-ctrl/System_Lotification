from reportlab.lib.pagesizes import HALF_LETTER, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import io
import os

def generar_pdf_recibo(cuota, pago):
    buffer = io.BytesIO()
    # Media Carta en Horizontal (Landscape)
    pagesize = landscape(HALF_LETTER)
    c = canvas.Canvas(buffer, pagesize=pagesize)
    width, height = pagesize
    
    lotificacion = cuota.venta.lote.manzana.lotificacion
    
    # --- Logotipo ---
    if lotificacion.logo and os.path.exists(lotificacion.logo.path):
        try:
            # Dibujar logo en la parte superior izquierda
            # Ajustamos posición para que no choque con el texto
            c.drawImage(lotificacion.logo.path, 50, height - 65, width=90, height=45, preserveAspectRatio=True, mask='auto')
        except:
            pass

    # --- Encabezado ---
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width/2 + 20, height - 45, "RECIBO DE PAGO")
    
    c.setFont("Helvetica", 10)
    c.drawRightString(width - 50, height - 45, f"Fecha: {pago.fecha_pago.strftime('%d/%m/%Y %H:%M')}")
    
    # Recibo No movido para no chocar con la línea
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, height - 75, f"Recibo No: #{pago.id}")
    
    c.setLineWidth(1)
    c.line(50, height - 80, width - 50, height - 80)
    
    # --- Datos del Cliente y Lote ---
    # Bajamos el inicio para dar aire
    y = height - 115
    
    c.setFont("Helvetica-Bold", 11)
    c.drawString(70, y, "CLIENTE:")
    c.setFont("Helvetica", 11)
    c.drawString(170, y, f"{cuota.venta.cliente.nombres} {cuota.venta.cliente.apellidos}")
    
    y -= 22
    c.setFont("Helvetica-Bold", 11)
    c.drawString(70, y, "LOTE:")
    c.setFont("Helvetica", 11)
    c.drawString(170, y, f"Lote {cuota.venta.lote.numero_lote} - Manzana {cuota.venta.lote.manzana.nombre}")
    
    y -= 22
    c.setFont("Helvetica-Bold", 11)
    c.drawString(70, y, "PROYECTO:")
    c.setFont("Helvetica", 11)
    c.drawString(170, y, f"{lotificacion.nombre}")
    
    y -= 22
    c.setFont("Helvetica-Bold", 11)
    c.drawString(70, y, "CONCEPTO:")
    c.setFont("Helvetica", 11)
    c.drawString(170, y, f"Pago de Cuota No. {cuota.no_cuota}")
    
    # --- Separador Central ---
    y -= 30
    c.setDash(1, 2)
    c.line(70, y, width - 70, y)
    c.setDash() 
    
    # --- Detalle de montos ---
    y -= 30
    c.setFont("Helvetica", 11)
    c.drawString(100, y, "Monto Base de Cuota:")
    c.drawRightString(width - 100, y, f"Q {pago.monto_base:,.2f}")
    
    y -= 18
    c.drawString(100, y, "Mora / Recargos:")
    c.drawRightString(width - 100, y, f"Q {pago.monto_mora:,.2f}")
    
    # Línea de suma
    y -= 10
    c.setLineWidth(1)
    c.line(width - 180, y, width - 100, y)
    
    # TOTAL
    y -= 25
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, y, "TOTAL PAGADO:")
    total = pago.monto_base + pago.monto_mora
    c.drawRightString(width - 100, y, f"Q {total:,.2f}")
    
    # --- Información de Pago ---
    # Movido a la izquierda para no chocar con la firma
    y_pago = 60
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(70, y_pago, f"Forma de Pago: {pago.metodo_pago}")
    if pago.referencia:
        c.drawString(70, y_pago - 12, f"Referencia: {pago.referencia}")
    
    # --- Firma ---
    # Movida a la derecha y ajustada para no superponerse
    y_firma = 60
    c.setLineWidth(0.5)
    c.line(width - 250, y_firma, width - 70, y_firma)
    c.setFont("Helvetica", 10)
    c.drawCentredString(width - 160, y_firma - 15, "Firma Autorizada / Sello")
    
    # --- Pie de página ---
    c.setFont("Helvetica", 8)
    c.drawCentredString(width/2, 20, "Este documento es un comprobante de pago oficial.")
    
    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer
