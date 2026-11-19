"""
email_utils.py — Chambazo SV
Funciones de envío de correo usando Gmail (chambazosv@gmail.com).
"""
import secrets
import threading
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags


def get_from_email():
    f = getattr(settings, 'DEFAULT_FROM_EMAIL', '') or 'Chambazo SV <chambazosv@gmail.com>'
    if '<>' in f or not f.strip():
        return 'Chambazo SV <chambazosv@gmail.com>'
    return f

FROM_EMAIL = get_from_email()


def generar_codigo_6():
    """Genera un código numérico de 6 dígitos."""
    return f"{secrets.randbelow(900000) + 100000}"


def enviar_codigo_verificacion(user, codigo):
    """Envía el código de 6 dígitos para verificar el correo al registrarse."""
    asunto = '✅ Tu código de verificación — Chambazo SV'
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;background:#f8fafc;padding:32px;border-radius:16px;">
      <div style="text-align:center;margin-bottom:24px;">
        <h1 style="color:#064e3b;font-size:2rem;margin:0;">🔧 Chambazo</h1>
        <p style="color:#6b7280;margin:4px 0 0;">La plataforma de chambas de El Salvador</p>
      </div>
      <div style="background:#fff;border-radius:12px;padding:28px;border:1px solid #e2e8f0;">
        <h2 style="color:#0f172a;font-size:1.3rem;margin:0 0 12px;">Hola, {user.first_name or user.username} 👋</h2>
        <p style="color:#475569;line-height:1.6;">Para confirmar tu cuenta en Chambazo, ingresa el siguiente código en la plataforma:</p>
        <div style="text-align:center;margin:28px 0;">
          <div style="font-size:2.8rem;font-weight:900;letter-spacing:10px;color:#064e3b;
                      background:#ecfdf5;border:2px dashed #10b981;border-radius:12px;
                      padding:18px 28px;display:inline-block;">{codigo}</div>
        </div>
        <p style="color:#64748b;font-size:0.88rem;text-align:center;margin:0;">
          ⏱️ Este código expira en <strong>15 minutos</strong>.
        </p>
      </div>
      <p style="color:#94a3b8;font-size:0.8rem;text-align:center;margin-top:20px;">
        Si no creaste una cuenta en Chambazo, ignora este correo.
      </p>
    </div>
    """
    return _enviar_html(asunto, html, [user.email])


def enviar_codigo_2fa(user, codigo):
    """HU059: Envía código de autenticación de dos factores (2FA) con validez de 5 min."""
    asunto = '🔐 Código de Acceso 2FA — Chambazo SV'
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;background:#f8fafc;padding:32px;border-radius:16px;">
      <div style="text-align:center;margin-bottom:24px;">
        <h1 style="color:#064e3b;font-size:2rem;margin:0;">🔧 Chambazo SV</h1>
        <p style="color:#6b7280;margin:4px 0 0;">Verificación de Seguridad en Dos Pasos</p>
      </div>
      <div style="background:#fff;border-radius:12px;padding:28px;border:1px solid #e2e8f0;">
        <h2 style="color:#0f172a;font-size:1.3rem;margin:0 0 12px;">Hola, {user.first_name or user.username} 🛡️</h2>
        <p style="color:#475569;line-height:1.6;">Se solicitó un inicio de sesión seguro con doble factor en tu cuenta de Chambazo. Tu código de verificación es:</p>
        <div style="text-align:center;margin:28px 0;">
          <div style="font-size:2.8rem;font-weight:900;letter-spacing:10px;color:#047857;
                      background:#ecfdf5;border:2px solid #059669;border-radius:12px;
                      padding:18px 28px;display:inline-block;">{codigo}</div>
        </div>
        <p style="color:#64748b;font-size:0.88rem;text-align:center;margin:0;">
          ⏱️ Este código es de un solo uso y expira en <strong>5 minutos</strong>.
        </p>
      </div>
      <p style="color:#94a3b8;font-size:0.8rem;text-align:center;margin-top:20px;">
        Si no intentaste iniciar sesión, cambia tu contraseña inmediatamente.
      </p>
    </div>
    """
    return _enviar_html(asunto, html, [user.email])


def enviar_notif_ticket_soporte(ticket):
    """HU052: Notifica al equipo de Chambazo SV y envía confirmación al usuario que contactó soporte."""
    correo_chambazo = getattr(settings, 'EMAIL_HOST_USER', '') or 'pointsgreen4@gmail.com'

    # 1. Correo interno que recibe el equipo Chambazo SV
    asunto_admin = f'🚨 [Ticket #{ticket.id}] {ticket.asunto} — Prioridad: {ticket.prioridad.upper()}'
    html_admin = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f8fafc;padding:32px;border-radius:16px;">
      <div style="text-align:center;margin-bottom:20px;">
        <h1 style="color:#064e3b;font-size:1.8rem;margin:0;">🔧 Chambazo SV — Soporte</h1>
        <p style="color:#6b7280;margin:4px 0 0;">Nueva solicitud de asistencia recibida</p>
      </div>
      <div style="background:#fff;border-radius:12px;padding:24px;border:1px solid #e2e8f0;margin-bottom:20px;">
        <div style="border-bottom:1px solid #f1f5f9;padding-bottom:12px;margin-bottom:14px;">
          <h2 style="color:#0f172a;font-size:1.1rem;margin:0 0 8px;">Ticket #{ticket.id}: {ticket.asunto}</h2>
          <span style="background:#ecfdf5;color:#047857;font-weight:700;padding:4px 10px;border-radius:20px;font-size:0.78rem;">
            PRIORIDAD: {ticket.prioridad.upper()}
          </span>
        </div>
        <p style="margin:6px 0;color:#334155;font-size:0.9rem;"><strong>Nombre:</strong> {ticket.nombre}</p>
        <p style="margin:6px 0;color:#334155;font-size:0.9rem;"><strong>Correo:</strong> <a href="mailto:{ticket.email}" style="color:#047857;">{ticket.email}</a></p>
        <p style="margin:6px 0;color:#334155;font-size:0.9rem;"><strong>Usuario en plataforma:</strong> {ticket.usuario.username if ticket.usuario else 'Sin cuenta / Visitante'}</p>
        <div style="margin-top:16px;background:#f1f5f9;border-left:4px solid #047857;padding:14px;border-radius:6px;">
          <strong style="color:#0f172a;display:block;margin-bottom:6px;">Mensaje del usuario:</strong>
          <p style="color:#334155;white-space:pre-wrap;line-height:1.6;margin:0;">{ticket.mensaje}</p>
        </div>
      </div>
      <p style="color:#94a3b8;font-size:0.78rem;text-align:center;">
        Responde directamente a: <a href="mailto:{ticket.email}" style="color:#047857;">{ticket.email}</a>
      </p>
    </div>
    """
    _enviar_html(asunto_admin, html_admin, [correo_chambazo])

    # 2. Confirmación al usuario que envió el ticket
    asunto_usuario = f'📨 Recibimos tu mensaje — Ticket #{ticket.id} | Chambazo SV'
    html_usuario = f"""
    <div style="font-family:Arial,sans-serif;max-width:540px;margin:0 auto;background:#f8fafc;padding:32px;border-radius:16px;">
      <div style="text-align:center;margin-bottom:24px;">
        <h1 style="color:#064e3b;font-size:2rem;margin:0;">🔧 Chambazo SV</h1>
        <p style="color:#6b7280;margin:4px 0 0;">Confirmación de recepción</p>
      </div>
      <div style="background:#fff;border-radius:12px;padding:24px;border:1px solid #e2e8f0;">
        <h2 style="color:#0f172a;font-size:1.2rem;margin:0 0 10px;">Hola, {ticket.nombre} 👋</h2>
        <p style="color:#475569;line-height:1.6;">
          Recibimos tu consulta sobre <strong>"{ticket.asunto}"</strong>. Nuestro equipo de soporte revisará tu caso y te responderá a la brevedad posible.
        </p>
        <div style="margin:18px 0;padding:12px 16px;background:#ecfdf5;border-radius:8px;border:1px solid #a7f3d0;text-align:center;">
          <p style="margin:0;color:#065f46;font-size:1rem;font-weight:700;">Número de Ticket: #{ticket.id}</p>
          <p style="margin:4px 0 0;color:#065f46;font-size:0.85rem;">Estado: Recibido — En revisión</p>
        </div>
        <p style="color:#64748b;font-size:0.85rem;margin:0;">
          Si tienes información adicional, responde directamente a este correo.
        </p>
      </div>
    </div>
    """
    return _enviar_html(asunto_usuario, html_usuario, [ticket.email])


def enviar_bienvenida(user):
    """Correo de bienvenida una vez verificada la cuenta."""
    asunto = '🎉 ¡Bienvenido a Chambazo SV!'
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;background:#f8fafc;padding:32px;border-radius:16px;">
      <div style="text-align:center;margin-bottom:24px;">
        <h1 style="color:#064e3b;font-size:2rem;margin:0;">🔧 Chambazo</h1>
        <p style="color:#6b7280;margin:4px 0 0;">La plataforma de chambas de El Salvador</p>
      </div>
      <div style="background:#fff;border-radius:12px;padding:28px;border:1px solid #e2e8f0;">
        <h2 style="color:#0f172a;font-size:1.3rem;margin:0 0 12px;">¡Tu cuenta está activa, {user.first_name or user.username}! 🎊</h2>
        <p style="color:#475569;line-height:1.6;">Ya puedes empezar a usar Chambazo. ¡Encuentra oportunidades de trabajo confiables en El Salvador!</p>
        <div style="margin:24px 0;padding:16px;background:#ecfdf5;border-radius:8px;border-left:4px solid #10b981;">
          <p style="color:#065f46;margin:0;font-weight:600;">✅ Completa tu perfil para destacar entre los demás trabajadores.</p>
        </div>
        <div style="text-align:center;margin-top:24px;">
          <a href="http://chambazo.com" style="background:#064e3b;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:700;font-size:1rem;">Ir a mi Panel →</a>
        </div>
      </div>
      <p style="color:#94a3b8;font-size:0.8rem;text-align:center;margin-top:20px;">
        Chambazo SV · chambazosv@gmail.com
      </p>
    </div>
    """
    return _enviar_html(asunto, html, [user.email])


def enviar_reset_password(user, token, request=None):
    """Envía el enlace para recuperar contraseña."""
    from django.urls import reverse
    link = f"http://127.0.0.1:8000/reset-password/{token}/"
    if request:
        link = request.build_absolute_uri(reverse('reset_password', args=[token]))

    asunto = '🔑 Recupera tu contraseña — Chambazo SV'
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;background:#f8fafc;padding:32px;border-radius:16px;">
      <div style="text-align:center;margin-bottom:24px;">
        <h1 style="color:#064e3b;font-size:2rem;margin:0;">🔧 Chambazo</h1>
        <p style="color:#6b7280;margin:4px 0 0;">La plataforma de chambas de El Salvador</p>
      </div>
      <div style="background:#fff;border-radius:12px;padding:28px;border:1px solid #e2e8f0;">
        <h2 style="color:#0f172a;font-size:1.3rem;margin:0 0 12px;">Hola, {user.first_name or user.username} 👋</h2>
        <p style="color:#475569;line-height:1.6;">Recibimos una solicitud para restablecer la contraseña de tu cuenta.</p>
        <p style="color:#475569;line-height:1.6;">Haz clic en el botón de abajo para crear una nueva contraseña:</p>
        <div style="text-align:center;margin:28px 0;">
          <a href="{link}" style="background:#064e3b;color:#fff;padding:14px 32px;border-radius:8px;
                                   text-decoration:none;font-weight:700;font-size:1rem;display:inline-block;">
            🔑 Restablecer Contraseña
          </a>
        </div>
        <p style="color:#64748b;font-size:0.88rem;text-align:center;margin:0;">
          ⏱️ Este enlace expira en <strong>2 horas</strong>.
        </p>
        <div style="margin-top:20px;padding:12px;background:#fff7ed;border-radius:8px;border-left:4px solid #f59e0b;">
          <p style="color:#92400e;margin:0;font-size:0.85rem;">⚠️ Si no solicitaste este cambio, ignora este correo. Tu contraseña no cambiará.</p>
        </div>
      </div>
    </div>
    """
    return _enviar_html(asunto, html, [user.email])


def enviar_notif_nueva_solicitud(contratista, solicitud):
    """Notifica al contratista que un trabajador aplicó a su trabajo."""
    t = solicitud.trabajo
    w = solicitud.trabajador
    asunto = f'📩 Nueva solicitud para: {t.titulo}'
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;background:#f8fafc;padding:32px;border-radius:16px;">
      <div style="text-align:center;margin-bottom:24px;">
        <h1 style="color:#064e3b;font-size:2rem;margin:0;">🔧 Chambazo</h1>
      </div>
      <div style="background:#fff;border-radius:12px;padding:28px;border:1px solid #e2e8f0;">
        <h2 style="color:#0f172a;font-size:1.2rem;margin:0 0 16px;">¡Tienes una nueva solicitud!</h2>
        <p style="color:#475569;"><strong>{w.get_full_name() or w.username}</strong> aplicó a tu oferta:</p>
        <div style="background:#f0fdf4;border-radius:8px;padding:14px;margin:16px 0;border-left:4px solid #10b981;">
          <p style="margin:0;color:#065f46;font-weight:700;font-size:1.05rem;">{t.titulo}</p>
          <p style="margin:4px 0 0;color:#475569;font-size:0.9rem;">📍 {t.ubicacion} · 💵 ${t.presupuesto}</p>
        </div>
        <div style="text-align:center;margin-top:20px;">
          <a href="http://127.0.0.1:8000/panel-contratista/" style="background:#064e3b;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:700;">Ver solicitud →</a>
        </div>
      </div>
    </div>
    """
    _enviar_html(asunto, html, [contratista.email])


def enviar_notif_estado_solicitud(trabajador, solicitud):
    """Notifica al trabajador el cambio de estado de su solicitud."""
    t = solicitud.trabajo
    estado_labels = {
        'aceptado': ('✅ ¡Solicitud aceptada!', '#065f46', '#ecfdf5'),
        'rechazado': ('❌ Solicitud rechazada', '#991b1b', '#fef2f2'),
        'contratado': ('🏆 ¡Felicidades! Fuiste contratado', '#065f46', '#ecfdf5'),
        'en_revision': ('🔍 Tu solicitud está en revisión', '#1e40af', '#eff6ff'),
    }
    titulo, color, bg = estado_labels.get(solicitud.estado, ('🔄 Actualización de solicitud', '#374151', '#f9fafb'))
    asunto = f'{titulo} — {t.titulo}'
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;background:#f8fafc;padding:32px;border-radius:16px;">
      <div style="text-align:center;margin-bottom:24px;">
        <h1 style="color:#064e3b;font-size:2rem;margin:0;">🔧 Chambazo</h1>
      </div>
      <div style="background:#fff;border-radius:12px;padding:28px;border:1px solid #e2e8f0;">
        <h2 style="color:{color};font-size:1.2rem;margin:0 0 16px;">{titulo}</h2>
        <div style="background:{bg};border-radius:8px;padding:14px;margin:16px 0;">
          <p style="margin:0;color:{color};font-weight:700;">{t.titulo}</p>
          <p style="margin:4px 0 0;color:#475569;font-size:0.9rem;">📍 {t.ubicacion}</p>
        </div>
        <div style="text-align:center;margin-top:20px;">
          <a href="http://127.0.0.1:8000/" style="background:#064e3b;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:700;">Ver en Chambazo →</a>
        </div>
      </div>
    </div>
    """
    _enviar_html(asunto, html, [trabajador.email])


def enviar_notif_trabajo_publicado(trabajo):
    """Notifica al contratista que su trabajo se publicó con éxito."""
    user = trabajo.contratista
    asunto = f'✅ Oferta Publicada: {trabajo.titulo}'
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;background:#f8fafc;padding:32px;border-radius:16px;">
      <div style="text-align:center;margin-bottom:24px;">
        <h1 style="color:#064e3b;font-size:2rem;margin:0;">🔧 Chambazo</h1>
      </div>
      <div style="background:#fff;border-radius:12px;padding:28px;border:1px solid #e2e8f0;">
        <h2 style="color:#0f172a;font-size:1.2rem;margin:0 0 16px;">¡Tu oferta ya está en vivo!</h2>
        <p style="color:#475569;">Hola {user.first_name or user.username}, los trabajadores ya pueden ver tu oferta:</p>
        <div style="background:#f0fdf4;border-radius:8px;padding:14px;margin:16px 0;border-left:4px solid #10b981;">
          <p style="margin:0;color:#065f46;font-weight:700;font-size:1.05rem;">{trabajo.titulo}</p>
        </div>
        <p style="color:#475569;">Te notificaremos en cuanto recibas nuevas aplicaciones.</p>
        <div style="text-align:center;margin-top:20px;">
          <a href="http://127.0.0.1:8000/contratista/candidatos/" style="background:#064e3b;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:700;">Ir a mi Panel →</a>
        </div>
      </div>
    </div>
    """
    return _enviar_html(asunto, html, [user.email])

def enviar_notif_trabajo_completado_exito(solicitud, transaccion):
    """Notifica que el trabajo se finalizó y el pago se liberó, enviando recibo."""
    c = solicitud.trabajo.contratista
    w = solicitud.trabajador
    # Correo para el Trabajador
    asunto_w = f'💸 ¡Pago liberado! Trabajo completado'
    html_w = f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;background:#f8fafc;padding:32px;border-radius:16px;">
      <div style="text-align:center;margin-bottom:24px;"><h1 style="color:#064e3b;font-size:2rem;margin:0;">🔧 Chambazo</h1></div>
      <div style="background:#fff;border-radius:12px;padding:28px;border:1px solid #e2e8f0;">
        <h2 style="color:#0f172a;font-size:1.2rem;">¡Felicidades {w.username}!</h2>
        <p style="color:#475569;">El contratista ha confirmado la finalización del trabajo <strong>{solicitud.trabajo.titulo}</strong>.</p>
        <div style="background:#ecfdf5;border-radius:8px;padding:14px;margin:16px 0;border:left:4px solid #10b981;">
          <p style="margin:0;color:#065f46;font-weight:700;font-size:1.05rem;">Los fondos (${transaccion.monto}) han sido liberados a tu cuenta.</p>
        </div>
      </div>
    </div>
    """
    _enviar_html(asunto_w, html_w, [w.email])

    # Correo para el Contratista
    asunto_c = f'✅ Trabajo Completado y Pagado'
    html_c = f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;background:#f8fafc;padding:32px;border-radius:16px;">
      <div style="text-align:center;margin-bottom:24px;"><h1 style="color:#064e3b;font-size:2rem;margin:0;">🔧 Chambazo</h1></div>
      <div style="background:#fff;border-radius:12px;padding:28px;border:1px solid #e2e8f0;">
        <h2 style="color:#0f172a;font-size:1.2rem;">Trabajo Finalizado</h2>
        <p style="color:#475569;">Has confirmado la entrega de <strong>{solicitud.trabajo.titulo}</strong> y liberado el pago de ${transaccion.monto}.</p>
        <p style="color:#475569;">Puedes descargar el comprobante en PDF desde la plataforma.</p>
      </div>
    </div>
    """
    _enviar_html(asunto_c, html_c, [c.email])


def _enviar_html(asunto, html_content, destinatarios, async_send=True):
    """Helper interno: envía un correo con cuerpo HTML + texto plano de fallback.
    Usa un hilo de fondo (daemon=True) para evitar bloqueos en solicitudes HTTP (DEF-001 / RNF-01).
    """
    texto_plano = strip_tags(html_content)
    def _deliver():
        try:
            msg = EmailMultiAlternatives(
                subject=asunto,
                body=texto_plano,
                from_email=get_from_email(),
                to=destinatarios,
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)
            return True
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"[Chambazo Email] Error al enviar correo a {destinatarios}: {e}")
            return False

    if async_send:
        t = threading.Thread(target=_deliver, daemon=True)
        t.start()
        return True
    return _deliver()
