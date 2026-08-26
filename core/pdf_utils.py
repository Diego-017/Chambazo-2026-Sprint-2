import os
from django.conf import settings
from django.utils import timezone
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch

def generar_comprobante_pdf(solicitud, transaccion):
    """Genera un recibo en PDF usando ReportLab y lo guarda en MEDIA_ROOT/comprobantes."""
    comprobantes_dir = os.path.join(settings.MEDIA_ROOT, 'comprobantes')
    os.makedirs(comprobantes_dir, exist_ok=True)
    
    filename = f"recibo_chambazo_{transaccion.id}_{solicitud.id}.pdf"
    file_path = os.path.join(comprobantes_dir, filename)
    
    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter
    
    # Header
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(colors.HexColor("#064e3b"))
    c.drawString(1 * inch, height - 1 * inch, "CHAMBAZO SV")
    
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.gray)
    c.drawString(1 * inch, height - 1.3 * inch, "Recibo Oficial de Pago - Sistema Escrow")
    
    # Separator
    c.setStrokeColor(colors.HexColor("#10b981"))
    c.setLineWidth(2)
    c.line(1 * inch, height - 1.5 * inch, width - 1 * inch, height - 1.5 * inch)
    
    # Detalles
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.black)
    c.drawString(1 * inch, height - 2 * inch, "Detalles de la Transacción")
    
    c.setFont("Helvetica", 11)
    y = height - 2.3 * inch
    c.drawString(1 * inch, y, f"ID de Transacción: {transaccion.metodo_pago_simulado}")
    y -= 0.3 * inch
    c.drawString(1 * inch, y, f"Fecha de Liberación: {timezone.localtime(transaccion.actualizado).strftime('%d/%m/%Y %H:%M:%S')}")
    y -= 0.3 * inch
    c.drawString(1 * inch, y, f"Estado: Pagado y Liberado")
    
    # Partes
    y -= 0.6 * inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1 * inch, y, "Partes Involucradas")
    
    c.setFont("Helvetica", 11)
    y -= 0.3 * inch
    c.drawString(1 * inch, y, f"Contratista (Pagador): {solicitud.trabajo.contratista.get_full_name() or solicitud.trabajo.contratista.username}")
    y -= 0.3 * inch
    c.drawString(1 * inch, y, f"Trabajador (Receptor): {solicitud.trabajador.get_full_name() or solicitud.trabajador.username}")
    y -= 0.3 * inch
    c.drawString(1 * inch, y, f"Concepto: {solicitud.trabajo.titulo}")
    
    # Monto
    y -= 0.8 * inch
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor("#064e3b"))
    c.drawString(1 * inch, y, f"Total Pagado: ${transaccion.monto}")
    
    # Footer
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.gray)
    c.drawCentredString(width / 2.0, 1 * inch, "Este comprobante es generado automáticamente por Chambazo SV.")
    c.drawCentredString(width / 2.0, 0.8 * inch, "Gracias por confiar en nuestra plataforma para trabajos seguros.")
    
    c.save()
    
    return f"comprobantes/{filename}"
