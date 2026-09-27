import os
from django.conf import settings
from django.utils import timezone
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader

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


NIVEL_EDUCATIVO_LABELS = dict([
    ('primaria', 'Educación Primaria (1° a 6° grado)'),
    ('basica', 'Educación Básica / Tercer Ciclo (7° a 9° grado)'),
    ('media', 'Bachillerato / Educación Media'),
    ('tecnico', 'Técnico Vocacional'),
    ('universitario_curso', 'Universitario (en curso)'),
    ('universitario', 'Universitario Graduado'),
    ('postgrado', 'Postgrado / Maestría'),
])


MESES_ES = {1:'enero',2:'febrero',3:'marzo',4:'abril',5:'mayo',6:'junio',
            7:'julio',8:'agosto',9:'septiembre',10:'octubre',11:'noviembre',12:'diciembre'}


def generar_cv_pdf(profile, user):
    """Genera un Currículum Vitae en PDF a partir de los datos del UserProfile (diseño de dos columnas)."""
    from .models import Solicitud, SKILL_CHOICES

    cvs_dir = os.path.join(settings.MEDIA_ROOT, 'cvs_generados')
    os.makedirs(cvs_dir, exist_ok=True)

    filename = f"cv_{user.username}_{int(timezone.now().timestamp())}.pdf"
    file_path = os.path.join(cvs_dir, filename)

    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter

    NAVY = colors.HexColor("#0f172a")
    GREEN = colors.HexColor("#1FA35A")
    GREEN_LIGHT = colors.HexColor("#EAFAF0")
    GRAY_TXT = colors.HexColor("#4b5768")
    DARK_TXT = colors.HexColor("#1f2937")
    MUTED = colors.HexColor("#8a94a3")
    WHITE = colors.white

    header_h = 1.55 * inch
    sidebar_w = 2.35 * inch
    pad = 0.28 * inch
    bottom_margin = 0.55 * inch

    def texto_wrap(texto, x, y_pos, max_width_pt, font="Helvetica", size=9.5, leading=0.16, color=DARK_TXT):
        """Envuelve texto a un ancho en puntos (no caracteres) y devuelve la nueva Y."""
        c.setFont(font, size)
        c.setFillColor(color)
        palabras = texto.split()
        linea = ""
        for palabra in palabras:
            prueba = f"{linea} {palabra}".strip()
            if c.stringWidth(prueba, font, size) <= max_width_pt:
                linea = prueba
            else:
                c.drawString(x, y_pos, linea)
                y_pos -= leading * inch
                linea = palabra
        if linea:
            c.drawString(x, y_pos, linea)
            y_pos -= leading * inch
        return y_pos

    def titulo_seccion(texto, x, y_pos, color=NAVY, size=11.5):
        c.setFont("Helvetica-Bold", size)
        c.setFillColor(color)
        c.drawString(x, y_pos, texto.upper())
        y_pos -= 0.07 * inch
        c.setStrokeColor(GREEN)
        c.setLineWidth(1.4)
        c.line(x, y_pos, x + 0.35 * inch, y_pos)
        return y_pos - 0.2 * inch

    def draw_pills(items, x0, y_pos, max_width_pt, bg, txt_color, font_size=8, pill_h=0.24*inch, gap=5):
        """Dibuja 'píldoras' que se van envolviendo dentro de max_width_pt. Devuelve la Y final."""
        cx = x0
        for item in items:
            c.setFont("Helvetica", font_size)
            w = c.stringWidth(item, "Helvetica", font_size) + 14
            if cx + w > x0 + max_width_pt:
                cx = x0
                y_pos -= pill_h + gap
            c.setFillColor(bg)
            c.roundRect(cx, y_pos - pill_h, w, pill_h, pill_h / 2, stroke=0, fill=1)
            c.setFillColor(txt_color)
            c.drawCentredString(cx + w / 2, y_pos - pill_h + 6.5, item)
            cx += w + gap
        return y_pos - pill_h - gap

    # ══════════════ BANDA SUPERIOR (nombre + contacto) ══════════════
    c.setFillColor(NAVY)
    c.rect(0, height - header_h, width, header_h, stroke=0, fill=1)

    # Foto de perfil (si tiene), esquina superior derecha de la banda
    text_right_limit = width - 0.6 * inch
    if profile.foto:
        try:
            foto_size = 0.85 * inch
            foto_x = width - 0.55 * inch - foto_size
            foto_y = height - header_h + (header_h - foto_size) / 2
            img = ImageReader(profile.foto.path)
            c.saveState()
            path_clip = c.beginPath()
            path_clip.circle(foto_x + foto_size / 2, foto_y + foto_size / 2, foto_size / 2)
            c.clipPath(path_clip, stroke=0, fill=0)
            c.drawImage(img, foto_x, foto_y, width=foto_size, height=foto_size, mask='auto', preserveAspectRatio=True)
            c.restoreState()
            text_right_limit = foto_x - 0.25 * inch
        except Exception:
            pass

    nombre_completo = user.get_full_name() or user.username
    yb = height - 0.62 * inch
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(WHITE)
    c.drawString(0.6 * inch, yb, nombre_completo)
    yb -= 0.28 * inch
    c.setFont("Helvetica", 11)
    c.setFillColor(GREEN)
    c.drawString(0.6 * inch, yb, "Currículum Vitae — Generado en Chambazo")
    yb -= 0.24 * inch
    contacto_partes = [p for p in [profile.telefono, user.email, profile.ubicacion] if p]
    if contacto_partes:
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#cbd5e1"))
        c.drawString(0.6 * inch, yb, "  ·  ".join(contacto_partes))
        yb -= 0.22 * inch
    if profile.calificacion and profile.total_trabajos:
        c.setFont("Helvetica-Bold", 9.5)
        c.setFillColor(colors.HexColor("#F2B90D"))
        c.drawString(0.6 * inch, yb, f"★ {profile.calificacion:.1f}/5.0")
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#cbd5e1"))
        c.drawString(0.6 * inch + 0.75 * inch, yb, f"({profile.total_trabajos} trabajos completados en Chambazo)")

    # ══════════════ BARRA LATERAL (izquierda) ══════════════
    body_top = height - header_h
    c.setFillColor(GREEN_LIGHT)
    c.rect(0, 0, sidebar_w, body_top, stroke=0, fill=1)

    sx = pad
    sy = body_top - 0.35 * inch
    sw = sidebar_w - 2 * pad

    if profile.habilidades:
        skill_labels = dict(SKILL_CHOICES)
        sy = titulo_seccion("Habilidades", sx, sy, size=10.5)
        sy = draw_pills([skill_labels.get(h, h) for h in profile.habilidades], sx, sy, sw,
                         bg=colors.white, txt_color=colors.HexColor("#0d7a41"))
        sy -= 0.18 * inch

    if profile.idiomas:
        sy = titulo_seccion("Idiomas", sx, sy, size=10.5)
        items = [f"{i.get('nombre','')} · {i.get('nivel','')}" for i in profile.idiomas if i.get('nombre')]
        sy = draw_pills(items, sx, sy, sw, bg=colors.white, txt_color=colors.HexColor("#0d7a41"))
        sy -= 0.18 * inch

    disp = profile.disponibilidad_horario or {}
    if disp.get('dias') or disp.get('franja'):
        sy = titulo_seccion("Disponibilidad", sx, sy, size=10.5)
        dias_map = {'lun':'Lun','mar':'Mar','mie':'Mié','jue':'Jue','vie':'Vie','sab':'Sáb','dom':'Dom'}
        dias_txt = " · ".join(dias_map.get(d, d) for d in disp.get('dias', []))
        franja_map = {'manana':'Mañana','tarde':'Tarde','noche':'Noche','completo':'Tiempo completo'}
        franja_txt = franja_map.get(disp.get('franja', ''), disp.get('franja', ''))
        if dias_txt:
            sy = texto_wrap(dias_txt, sx, sy, sw, size=9, color=GRAY_TXT)
        if franja_txt:
            sy = texto_wrap(franja_txt, sx, sy, sw, size=9, color=GRAY_TXT)
        sy -= 0.1 * inch

    if profile.nivel_educativo:
        sy = titulo_seccion("Educación", sx, sy, size=10.5)
        sy = texto_wrap(NIVEL_EDUCATIVO_LABELS.get(profile.nivel_educativo, profile.nivel_educativo), sx, sy, sw, size=9, color=GRAY_TXT)
        sy -= 0.1 * inch

    if profile.portfolio_url:
        sy = titulo_seccion("Portafolio", sx, sy, size=10.5)
        sy = texto_wrap(profile.portfolio_url, sx, sy, sw, size=8.5, color=GREEN)

    # ══════════════ COLUMNA PRINCIPAL (derecha) ══════════════
    mx = sidebar_w + pad
    mw = width - mx - 0.55 * inch
    my = body_top - 0.4 * inch

    if profile.descripcion:
        my = titulo_seccion("Perfil", mx, my)
        my = texto_wrap(profile.descripcion, mx, my, mw)
        my -= 0.16 * inch

    trabajos_completados = (Solicitud.objects
        .filter(trabajador=user, estado='completado')
        .select_related('trabajo', 'trabajo__contratista__profile')
        .order_by('-actualizado')[:6])
    if trabajos_completados:
        my = titulo_seccion("Experiencia en Chambazo (verificada)", mx, my)
        for sol in trabajos_completados:
            contratista_profile = getattr(sol.trabajo.contratista, 'profile', None)
            nombre_empleador = (contratista_profile.nombre_display if contratista_profile and hasattr(contratista_profile, 'nombre_display')
                                 else sol.trabajo.contratista.get_full_name() or sol.trabajo.contratista.username)
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(DARK_TXT)
            c.drawString(mx, my, sol.trabajo.titulo)
            c.setFont("Helvetica", 8.5)
            c.setFillColor(MUTED)
            c.drawRightString(mx + mw, my, f"{MESES_ES[sol.actualizado.month]} {sol.actualizado.year}")
            my -= 0.17 * inch
            my = texto_wrap(f"Contratado por {nombre_empleador}", mx, my, mw, size=9, leading=0.16, color=GRAY_TXT)
            my -= 0.06 * inch
        my -= 0.1 * inch

    if profile.certificaciones:
        my = titulo_seccion("Certificaciones y diplomas", mx, my)
        my = texto_wrap(profile.certificaciones, mx, my, mw)
        my -= 0.16 * inch

    if profile.referencias_personales:
        my = titulo_seccion("Referencias personales", mx, my)
        for ref in profile.referencias_personales:
            if ref.get('nombre'):
                my = texto_wrap(f"{ref.get('nombre')} — {ref.get('telefono', '')}", mx, my, mw)
        my -= 0.1 * inch

    # Footer
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.gray)
    c.drawCentredString(width / 2.0, 0.35 * inch, "Generado automáticamente por Chambazo SV — chambazo.sv")

    c.save()
    return f"cvs_generados/{filename}"