"""
email_utils.py — Chambazo SV
Funciones de envío de correo usando Gmail (chambazosv@gmail.com).
"""
import random
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags


FROM_EMAIL = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Chambazo SV <chambazosv@gmail.com>')


def generar_codigo_6():
    """Genera un código numérico de 6 dígitos."""
    return str(random.randint(100000, 999999))


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


def _enviar_html(asunto, html_content, destinatarios):
    """Helper interno: envía un correo con cuerpo HTML + texto plano de fallback."""
    texto_plano = strip_tags(html_content)
    try:
        msg = EmailMultiAlternatives(
            subject=asunto,
            body=texto_plano,
            from_email=FROM_EMAIL,
            to=destinatarios,
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        return True
    except Exception as e:
        # Log el error pero no rompe la app
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"[Chambazo Email] Error al enviar correo a {destinatarios}: {e}")
        return False
