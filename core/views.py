import json
import random
import string
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from django.conf import settings

from .models import (
    UserProfile, Trabajo, Solicitud, Notificacion,
    Resena, GaleriaItem, Mensaje, PasswordResetToken,
    TrabajoGuardado, Logro, LogroObtenido, AceptacionTerminos,
    EmailVerificationToken,
    SKILL_CHOICES, SKILL_ICONS, SKILL_COLORS
)
from .forms import (
    LoginForm, RegistroStep2Form, RegistroStep3Form,
    TrabajoForm, EditarPerfilForm, ResenaForm, GaleriaItemForm,
    PagoTarjetaForm, MensajeChatForm
)


# ── Helpers ────────────────────────────────────────────────────────────────────
def ctx_base(request):
    ctx = {'GOOGLE_MAPS_KEY': settings.GOOGLE_MAPS_API_KEY}
    if request.user.is_authenticated:
        ctx['notif_count'] = Notificacion.objects.filter(usuario=request.user, leida=False).count()
        if request.user.profile.rol == 'trabajador':
            ctx['urgentes_count'] = Trabajo.objects.filter(activo=True, es_urgente=True).count()
            ctx['solicitudes_pend_count'] = Solicitud.objects.filter(
                trabajador=request.user, estado__in=['pendiente', 'en_revision']).count()
    return ctx


def crear_notif(usuario, tipo, titulo, mensaje, url=''):
    Notificacion.objects.create(usuario=usuario, tipo=tipo, titulo=titulo, mensaje=mensaje, url=url)


def verificar_logros(user):
    """Revisa y otorga logros automáticamente según el progreso del usuario."""
    profile = user.profile
    contratados = Solicitud.objects.filter(trabajador=user, estado='contratado').count()
    seguidos = 0
    ultimas = list(Solicitud.objects.filter(trabajador=user).order_by('-actualizado')[:10])
    for s in ultimas:
        if s.estado in ('aceptado', 'contratado'):
            seguidos += 1
        else:
            break

    condiciones = {
        'primer_trabajo': contratados >= 1,
        'superestrella': profile.calificacion >= 4.5 and contratados >= 3,
        'en_racha': seguidos >= 3,
        'verificado': profile.verificado,
        'pro_worker': contratados >= 25,
        'top_chambazo': contratados >= 50,
    }
    for codigo, cumplido in condiciones.items():
        if cumplido:
            logro = Logro.objects.filter(codigo=codigo).first()
            if logro and not LogroObtenido.objects.filter(usuario=user, logro=logro).exists():
                LogroObtenido.objects.create(usuario=user, logro=logro)
                crear_notif(user, 'sistema', f'🏆 ¡Logro desbloqueado: {logro.nombre}!',
                            logro.descripcion, '/logros/')


# ── Auth ───────────────────────────────────────────────────────────────────────
def home(request):
    # Ya no redirigimos automáticamente. La landing page será lo primero que vean.
    return render(request, 'core/landing.html')


def login_view(request):
    error = None
    stats_landing = {
        'trabajadores': UserProfile.objects.filter(rol='trabajador').count() or 500,
        'empleadores': UserProfile.objects.filter(rol='contratista').count() or 200,
        'promedio': 4.8,
    }
    if request.method == 'POST':
        form = LoginForm(request.POST)
        rol_login = request.POST.get('rol_login', 'trabajador')
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                user_obj = User.objects.get(email=email)
                user = authenticate(request, username=user_obj.username, password=password)
                if user:
                    login(request, user)
                    rol = getattr(user.profile, 'rol', 'trabajador')
                    return redirect('panel_contratista' if rol == 'contratista' else 'home_trabajador')
                else:
                    error = 'Contraseña incorrecta.'
            except User.DoesNotExist:
                error = 'No existe una cuenta con ese correo.'
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form, 'error': error, 'stats_landing': stats_landing})


def logout_view(request):
    logout(request)
    return redirect('home')


def recuperar_password(request):
    msg = None
    error = None
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        try:
            user = User.objects.get(email=email)
            # Invalida tokens anteriores
            PasswordResetToken.objects.filter(user=user, usado=False).update(usado=True)
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=40))
            PasswordResetToken.objects.create(user=user, token=token)
            # Enviar email real
            from .email_utils import enviar_reset_password
            enviado = enviar_reset_password(user, token, request)
            if enviado:
                msg = '✅ Te enviamos un enlace a tu correo. Revisa tu bandeja de entrada (y spam).'
            else:
                msg = '⚠️ Hubo un error enviando el correo. Intenta de nuevo más tarde.'
        except User.DoesNotExist:
            # Por seguridad, no revelamos si el correo existe o no
            msg = '✅ Si ese correo está registrado, recibirás instrucciones en breve.'
    return render(request, 'core/recuperar_password.html', {'msg': msg, 'error': error})


def reset_password(request, token):
    prt = get_object_or_404(PasswordResetToken, token=token)
    if not prt.is_valid():
        messages.error(request, 'El enlace expiró o ya fue usado.')
        return redirect('login')
    if request.method == 'POST':
        pw = request.POST.get('password', '')
        if len(pw) >= 6:
            prt.user.set_password(pw)
            prt.user.save()
            prt.usado = True
            prt.save()
            messages.success(request, '¡Contraseña actualizada!')
            return redirect('login')
    return render(request, 'core/reset_password.html', {'token': token})


# ── Registro 3 pasos ──────────────────────────────────────────────────────────
def registro_step1(request):
    if request.method == 'POST':
        rol = request.POST.get('rol', 'trabajador')
        request.session['registro_rol'] = rol
        return redirect('registro_step2')
    return render(request, 'core/registro_step1.html')


def registro_step2(request):
    rol = request.session.get('registro_rol', 'trabajador')
    if request.method == 'POST':
        form = RegistroStep2Form(request.POST, rol=rol)
        if form.is_valid():
            request.session['registro_data'] = {
                'nombre': form.cleaned_data.get('nombre', ''),
                'empresa': form.cleaned_data.get('empresa', ''),
                'email': form.cleaned_data['email'],
                'password': form.cleaned_data['password'],
                'telefono': form.cleaned_data.get('telefono', ''),
                'ubicacion': form.cleaned_data.get('ubicacion', ''),
            }
            return redirect('registro_step3')
    else:
        form = RegistroStep2Form(rol=rol)
    return render(request, 'core/registro_step2.html', {'form': form, 'rol': rol})


def registro_step3(request):
    rol = request.session.get('registro_rol', 'trabajador')
    data = request.session.get('registro_data', {})
    if not data:
        return redirect('registro_step1')
    if request.method == 'POST':
        form = RegistroStep3Form(request.POST, rol=rol)
        if form.is_valid():
            username = data['email'].split('@')[0]
            base = username
            i = 1
            while User.objects.filter(username=username).exists():
                username = f"{base}{i}"; i += 1
            nombre_completo = data.get('nombre', '').strip()
            partes = nombre_completo.split(' ', 1)
            first_name = partes[0] if partes else ''
            last_name = partes[1] if len(partes) > 1 else ''
            # Crear usuario desactivado hasta que verifique su correo
            user = User.objects.create_user(
                username=username, email=data['email'], password=data['password'],
                first_name=first_name, last_name=last_name,
                is_active=False,   # ← inactivo hasta verificación
            )
            habilidades = request.POST.getlist('habilidades') if rol == 'trabajador' else []
            UserProfile.objects.create(
                user=user, rol=rol,
                telefono=data.get('telefono', ''), ubicacion=data.get('ubicacion', ''),
                empresa=data.get('empresa', ''), habilidades=habilidades,
            )
            AceptacionTerminos.objects.create(usuario=user, aceptado=True)
            # Generar y enviar código de 6 dígitos
            from .email_utils import generar_codigo_6, enviar_codigo_verificacion
            codigo = generar_codigo_6()
            EmailVerificationToken.objects.create(user=user, token=codigo)
            enviar_codigo_verificacion(user, codigo)
            # Guardar user_id en sesión para la pantalla de verificación
            request.session['verificacion_user_id'] = user.pk
            request.session['verificacion_email'] = user.email
            return redirect('verificar_email')
    else:
        form = RegistroStep3Form(rol=rol)
    return render(request, 'core/registro_step3.html',
                  {'form': form, 'rol': rol, 'skills': SKILL_CHOICES})


def verificar_email(request):
    """Pantalla donde el usuario ingresa el código de 6 dígitos enviado a su correo."""
    user_id = request.session.get('verificacion_user_id')
    email = request.session.get('verificacion_email', '')
    if not user_id:
        return redirect('registro_step1')

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return redirect('registro_step1')

    error = None
    if request.method == 'POST':
        accion = request.POST.get('accion', 'verificar')

        if accion == 'reenviar':
            # Invalida anteriores y genera nuevo código
            EmailVerificationToken.objects.filter(user=user, usado=False).update(usado=True)
            from .email_utils import generar_codigo_6, enviar_codigo_verificacion
            codigo = generar_codigo_6()
            EmailVerificationToken.objects.create(user=user, token=codigo)
            enviado = enviar_codigo_verificacion(user, codigo)
            if enviado:
                messages.success(request, '✅ Nuevo código enviado. Revisa tu bandeja de entrada.')
            else:
                messages.error(request, '⚠️ Error al reenviar. Intenta de nuevo.')
            return redirect('verificar_email')

        codigo_ingresado = request.POST.get('codigo', '').strip()
        token_obj = EmailVerificationToken.objects.filter(
            user=user, token=codigo_ingresado, usado=False
        ).last()

        if token_obj and token_obj.is_valid():
            # Marcar token como usado y activar el usuario
            token_obj.usado = True
            token_obj.save()
            user.is_active = True
            user.save()
            # Limpiar sesión de verificación
            request.session.pop('verificacion_user_id', None)
            request.session.pop('verificacion_email', None)
            # Enviar correo de bienvenida
            from .email_utils import enviar_bienvenida
            enviar_bienvenida(user)
            # Iniciar sesión
            login(request, user)
            messages.success(request, f'¡Bienvenido a Chambazo, {user.first_name or user.username}! 🎉')
            return redirect('panel_contratista' if user.profile.rol == 'contratista' else 'home_trabajador')
        elif token_obj and not token_obj.is_valid():
            error = '⏱️ El código expiró. Solicita uno nuevo.'
        else:
            error = '❌ Código incorrecto. Verifica e inténtalo de nuevo.'

    return render(request, 'core/verificar_email.html', {'email': email, 'error': error})



# ── Buscar empleos (Home Trabajador) ────────────────────────────────────────────
@login_required
def home_trabajador(request):
    qs = Trabajo.objects.filter(activo=True).select_related('contratista__profile')
    q = request.GET.get('q', '')
    categoria = request.GET.get('categoria', '')
    urgente = request.GET.get('urgente', '')

    if q:
        qs = qs.filter(Q(titulo__icontains=q) | Q(descripcion__icontains=q) | Q(ubicacion__icontains=q))
    if categoria:
        qs = qs.filter(categoria=categoria)
    if urgente:
        qs = qs.filter(es_urgente=True)

    profile = request.user.profile
    guardado_ids = set(TrabajoGuardado.objects.filter(usuario=request.user).values_list('trabajo_id', flat=True))
    trabajos_list = []
    for t in qs[:60]:
        t.match = profile.match_score(t)
        t.esta_guardado = t.pk in guardado_ids
        trabajos_list.append(t)

    mis_sols = Solicitud.objects.filter(trabajador=request.user)
    stats = {
        'completados': mis_sols.filter(estado='contratado').count(),
        'calificacion': profile.calificacion,
        'ganado_mes': _ganado_este_mes(request.user),
    }
    ctx = ctx_base(request)
    ctx.update({'trabajos': trabajos_list, 'stats': stats, 'active': 'buscar', 'skills': SKILL_CHOICES})
    return render(request, 'core/home_trabajador.html', ctx)


def _ganado_este_mes(user):
    hoy = timezone.now()
    total = Solicitud.objects.filter(
        trabajador=user, estado='contratado',
        actualizado__year=hoy.year, actualizado__month=hoy.month
    ).aggregate(s=Sum('trabajo__presupuesto'))['s']
    return total or 0


# ── Trabajo detalle ────────────────────────────────────────────────────────────
def trabajo_detalle(request, pk):
    trabajo = get_object_or_404(Trabajo, pk=pk, activo=True)
    Trabajo.objects.filter(pk=pk).update(vistas=trabajo.vistas + 1)

    ya_aplico = False
    solicitud_estado = ''
    match_score = 0
    esta_guardado = False

    if request.user.is_authenticated:
        sol = Solicitud.objects.filter(trabajo=trabajo, trabajador=request.user).first()
        if sol:
            ya_aplico = True
            solicitud_estado = sol.get_estado_display()
        try:
            match_score = request.user.profile.match_score(trabajo)
            esta_guardado = TrabajoGuardado.objects.filter(usuario=request.user, trabajo=trabajo).exists()
        except Exception:
            pass

    ctx = ctx_base(request)
    ctx.update({
        'trabajo': trabajo, 'ya_aplico': ya_aplico, 'solicitud_estado': solicitud_estado,
        'match_score': match_score, 'esta_guardado': esta_guardado, 'active': 'buscar',
    })
    return render(request, 'core/trabajo_detalle.html', ctx)


@login_required
def toggle_guardado(request, pk):
    trabajo = get_object_or_404(Trabajo, pk=pk)
    obj, created = TrabajoGuardado.objects.get_or_create(usuario=request.user, trabajo=trabajo)
    if not created:
        obj.delete()
        messages.info(request, 'Quitado de guardados.')
    else:
        messages.success(request, '❤️ Guardado.')
    nxt = request.POST.get('next') or request.GET.get('next') or 'home_trabajador'
    return redirect(nxt)


@login_required
def guardados(request):
    items = TrabajoGuardado.objects.filter(usuario=request.user).select_related('trabajo__contratista__profile')
    profile = request.user.profile
    trabajos = []
    for g in items:
        t = g.trabajo
        t.match = profile.match_score(t)
        trabajos.append(t)
    ctx = ctx_base(request)
    ctx.update({'trabajos': trabajos, 'active': 'guardados'})
    return render(request, 'core/guardados.html', ctx)


# ── Aplicar ────────────────────────────────────────────────────────────────────
@login_required
def aplicar_trabajo(request, pk):
    trabajo = get_object_or_404(Trabajo, pk=pk, activo=True)
    if Solicitud.objects.filter(trabajo=trabajo, trabajador=request.user).exists():
        messages.warning(request, 'Ya aplicaste a este trabajo.')
        return redirect('trabajo_detalle', pk=pk)

    match_score = request.user.profile.match_score(trabajo)

    if request.method == 'POST':
        mensaje = request.POST.get('mensaje', '')
        tarifa = request.POST.get('tarifa_propuesta') or None
        solicitud = Solicitud.objects.create(
            trabajo=trabajo, trabajador=request.user, mensaje=mensaje,
            tarifa_propuesta=Decimal(tarifa) if tarifa else None,
            pagado=False, total_a_pagar=Decimal('1.50')
        )
        return redirect('pagar_solicitud', pk=solicitud.pk)

    ctx = ctx_base(request)
    ctx.update({'trabajo': trabajo, 'match_score': match_score, 'active': 'buscar'})
    return render(request, 'core/aplicar_trabajo.html', ctx)

@login_required
def pagar_solicitud(request, pk):
    solicitud = get_object_or_404(Solicitud, pk=pk, trabajador=request.user)
    if solicitud.pagado:
        return redirect('solicitud_enviada', pk=solicitud.trabajo.pk)

    if request.method == 'POST':
        form = PagoTarjetaForm(request.POST)
        if form.is_valid():
            # Simular pago
            import uuid
            solicitud.pagado = True
            solicitud.metodo_pago_id = str(uuid.uuid4()).split('-')[0].upper()
            solicitud.save()
            crear_notif(solicitud.trabajo.contratista, 'solicitud', f'Nueva solicitud — {solicitud.trabajo.titulo}',
                        f'{request.user.get_full_name() or request.user.username} aplicó a tu vacante.',
                        f'/contratista/trabajo/{solicitud.trabajo.pk}/candidatos/')
            return redirect('solicitud_enviada', pk=solicitud.trabajo.pk)
    else:
        form = PagoTarjetaForm()
    
    ctx = ctx_base(request)
    ctx.update({'solicitud': solicitud, 'form': form, 'active': 'buscar'})
    return render(request, 'core/pagar_solicitud.html', ctx)


@login_required
def solicitud_enviada(request, pk):
    trabajo = get_object_or_404(Trabajo, pk=pk)
    ctx = ctx_base(request)
    ctx['trabajo'] = trabajo
    return render(request, 'core/solicitud_enviada.html', ctx)


@login_required
def aplicar_rapido(request, pk):
    trabajo = get_object_or_404(Trabajo, pk=pk, activo=True)
    if Solicitud.objects.filter(trabajo=trabajo, trabajador=request.user).exists():
        messages.warning(request, 'Ya aplicaste a este trabajo.')
        return redirect('trabajo_detalle', pk=pk)
    solicitud = Solicitud.objects.create(trabajo=trabajo, trabajador=request.user, rapida=True, pagado=False, total_a_pagar=Decimal('1.50'))
    return redirect('pagar_solicitud', pk=solicitud.pk)


# ── Mis solicitudes (tabla) ─────────────────────────────────────────────────────
@login_required
def mis_solicitudes(request):
    qs = Solicitud.objects.filter(trabajador=request.user).select_related('trabajo__contratista__profile')
    estado = request.GET.get('estado', '')
    if estado:
        qs = qs.filter(estado=estado)
    ctx = ctx_base(request)
    ctx.update({'solicitudes': qs, 'active': 'solicitudes'})
    return render(request, 'core/mis_solicitudes.html', ctx)


# ── Trabajos urgentes ──────────────────────────────────────────────────────────
@login_required
def trabajos_urgentes(request):
    trabajos = Trabajo.objects.filter(activo=True, es_urgente=True).select_related('contratista__profile')
    ctx = ctx_base(request)
    ctx.update({'trabajos': trabajos, 'active': 'urgentes'})
    return render(request, 'core/trabajos_urgentes.html', ctx)


# ── Mensajes (lista + chat WhatsApp style) ──────────────────────────────────────
@login_required
def mensajes(request, sol_pk=None):
    # conversaciones = solicitudes aceptadas, contratadas, en progreso o con mensajes previos
    if request.user.profile.rol == 'trabajador':
        conv_qs = Solicitud.objects.filter(
            trabajador=request.user
        ).filter(
            Q(estado__in=['aceptado', 'contratado', 'en_progreso', 'completado']) | Q(mensajes__isnull=False)
        ).distinct().select_related('trabajo__contratista__profile')
    else:
        conv_qs = Solicitud.objects.filter(
            trabajo__contratista=request.user
        ).filter(
            Q(estado__in=['aceptado', 'contratado', 'en_progreso', 'completado']) | Q(mensajes__isnull=False)
        ).distinct().select_related('trabajador__profile', 'trabajo')

    conversaciones = []
    for sol in conv_qs:
        otro = sol.trabajo.contratista if request.user == sol.trabajador else sol.trabajador
        ultimo = sol.mensajes.last()
        resumen_ultimo = 'Inicia la conversación'
        if ultimo:
            if ultimo.texto:
                resumen_ultimo = ultimo.texto[:35]
            elif ultimo.audio:
                resumen_ultimo = '🎤 Nota de voz'
            elif ultimo.adjunto:
                resumen_ultimo = '📎 Archivo adjunto'
            elif ultimo.lat and ultimo.lng:
                resumen_ultimo = '📍 Ubicación'

        conversaciones.append({
            'sol': sol, 'otro': otro,
            'ultimo_msg': resumen_ultimo,
            'ultimo_fecha': ultimo.creado if ultimo else sol.creado,
            'no_leidos': sol.mensajes.filter(leido=False).exclude(autor=request.user).count(),
        })
    conversaciones.sort(key=lambda c: c['ultimo_fecha'], reverse=True)

    sol_activa = None
    otro_user = None
    msgs = []
    if sol_pk:
        sol_activa = get_object_or_404(Solicitud, pk=sol_pk)
        if request.user not in [sol_activa.trabajador, sol_activa.trabajo.contratista]:
            messages.error(request, 'No tienes acceso a este chat.')
            return redirect('mensajes')
        otro_user = sol_activa.trabajo.contratista if request.user == sol_activa.trabajador else sol_activa.trabajador
        
        if request.method == 'POST':
            texto = request.POST.get('texto', '').strip()
            adjunto = request.FILES.get('adjunto')
            audio = request.FILES.get('audio')
            lat_str = request.POST.get('lat', '')
            lng_str = request.POST.get('lng', '')
            ubicacion_nombre = request.POST.get('ubicacion_nombre', '').strip()

            lat = float(lat_str) if lat_str else None
            lng = float(lng_str) if lng_str else None

            if texto or adjunto or audio or (lat and lng):
                msg_obj = Mensaje.objects.create(
                    solicitud=sol_activa,
                    autor=request.user,
                    texto=texto,
                    adjunto=adjunto,
                    audio=audio,
                    lat=lat,
                    lng=lng,
                    ubicacion_nombre=ubicacion_nombre,
                    estado_entrega='entregado'
                )
                preview_txt = texto or ('[Audio]' if audio else ('[Archivo]' if adjunto else '[Ubicación]'))
                crear_notif(otro_user, 'sistema', f'💬 Mensaje de {request.user.profile.nombre_display}',
                            preview_txt[:100], f'/mensajes/{sol_pk}/')
            return redirect('mensajes_chat', sol_pk=sol_pk)

        msgs = sol_activa.mensajes.all()
        # Marcar los mensajes del otro usuario como leídos (doble check azul)
        sol_activa.mensajes.filter(leido=False).exclude(autor=request.user).update(
            leido=True, estado_entrega='leido'
        )

    active = 'mensajes'
    ctx = ctx_base(request)
    ctx.update({'conversaciones': conversaciones, 'sol_activa': sol_activa,
                'otro_user': otro_user, 'mensajes_list': msgs, 'active': active})
    template = 'core/mensajes_contratista.html' if request.user.profile.rol == 'contratista' else 'core/mensajes.html'
    return render(request, template, ctx)



# ── Ganancias (solo trabajador) ─────────────────────────────────────────────────
@login_required
def ganancias(request):
    contratados = Solicitud.objects.filter(trabajador=request.user, estado='contratado').select_related('trabajo')
    total_mes = _ganado_este_mes(request.user)

    # Ingresos por semana (últimas 5 semanas)
    hoy = timezone.now()
    semanas = []
    for i in range(4, -1, -1):
        inicio = hoy - timezone.timedelta(days=hoy.weekday() + 7 * i)
        fin = inicio + timezone.timedelta(days=6)
        monto = contratados.filter(actualizado__date__gte=inicio.date(), actualizado__date__lte=fin.date()) \
            .aggregate(s=Sum('trabajo__presupuesto'))['s'] or 0
        semanas.append({'label': f"S{4-i+1} {inicio.strftime('%b')}", 'monto': float(monto)})

    mejor_semana = max(semanas, key=lambda s: s['monto']) if semanas else {'monto': 0, 'label': '—'}
    max_monto = max([s['monto'] for s in semanas] + [1])
    for s in semanas:
        s['pct'] = int((s['monto'] / max_monto) * 100) if max_monto else 0

    total_trabajos = contratados.count()
    prom = (total_mes / total_trabajos) if total_trabajos else 0

    ultimos_pagos = contratados.order_by('-actualizado')[:6]

    ctx = ctx_base(request)
    ctx.update({
        'total_mes': total_mes, 'mejor_semana': mejor_semana, 'total_trabajos': total_trabajos,
        'prom_trabajo': round(prom, 2), 'semanas': semanas, 'ultimos_pagos': ultimos_pagos,
        'active': 'ganancias',
    })
    return render(request, 'core/ganancias.html', ctx)


# ── Logros ─────────────────────────────────────────────────────────────────────
@login_required
def logros(request):
    verificar_logros(request.user)
    todos = Logro.objects.all()
    obtenidos_ids = set(LogroObtenido.objects.filter(usuario=request.user).values_list('logro_id', flat=True))
    puntos_totales = Logro.objects.filter(id__in=obtenidos_ids).aggregate(s=Sum('puntos'))['s'] or 0
    puntos_max = todos.aggregate(s=Sum('puntos'))['s'] or 1

    lista = []
    for l in todos:
        lista.append({'logro': l, 'desbloqueado': l.id in obtenidos_ids})

    nivel_pct = int((puntos_totales / puntos_max) * 100) if puntos_max else 0
    ctx = ctx_base(request)
    ctx.update({
        'lista_logros': lista, 'puntos_totales': puntos_totales,
        'desbloqueados': len(obtenidos_ids), 'total_logros': todos.count(),
        'nivel_pct': nivel_pct, 'puntos_faltan': max(puntos_max - puntos_totales, 0),
        'active': 'logros',
    })
    return render(request, 'core/logros.html', ctx)


# ── Panel contratista ──────────────────────────────────────────────────────────
@login_required
def panel_contratista(request):
    if request.user.profile.rol != 'contratista':
        return redirect('home_trabajador')
    trabajos = Trabajo.objects.filter(contratista=request.user)
    stats = {
        'activas': trabajos.filter(activo=True).count(),
        'candidatos': Solicitud.objects.filter(trabajo__contratista=request.user).count(),
        'tarifa_prom': trabajos.aggregate(a=Avg('presupuesto'))['a'] or 0,
        'reputacion': request.user.profile.calificacion or 0,
    }
    ctx = ctx_base(request)
    ctx.update({'trabajos': trabajos[:8], 'stats': stats, 'active': 'panel'})
    return render(request, 'core/panel_contratista.html', ctx)


# ── Publicar / Editar trabajo ──────────────────────────────────────────────────
@login_required
def publicar_trabajo(request):
    if request.user.profile.rol != 'contratista':
        return redirect('home_trabajador')
    if request.method == 'POST':
        form = TrabajoForm(request.POST)
        if form.is_valid():
            trabajo = form.save(commit=False)
            trabajo.contratista = request.user
            trabajo.habilidades_req = request.POST.getlist('habilidades_req')
            lat = request.POST.get('lat', ''); lng = request.POST.get('lng', '')
            if lat and lng:
                try:
                    trabajo.lat = float(lat); trabajo.lng = float(lng)
                except ValueError:
                    pass
            trabajo.calcular_tarifas()
            trabajo.save()
            messages.info(request, 'Paso 2: Confirma el pago de la tarifa de publicación para activar tu vacante.')
            return redirect('pagar_trabajo', pk=trabajo.pk)
    else:
        form = TrabajoForm()
    ctx = ctx_base(request)
    ctx.update({'form': form, 'skills': SKILL_CHOICES, 'titulo_pagina': 'Publicar trabajo',
                'btn_label': 'Continuar al pago', 'active': 'publicar'})
    return render(request, 'core/publicar_trabajo.html', ctx)


@login_required
def pagar_trabajo(request, pk):
    trabajo = get_object_or_404(Trabajo, pk=pk, contratista=request.user)
    trabajo.calcular_tarifas()

    if request.method == 'POST':
        form = PagoTarjetaForm(request.POST)
        if form.is_valid():
            card_num = form.cleaned_data['numero_tarjeta'].replace(' ', '')
            last4 = card_num[-4:] if len(card_num) >= 4 else '4242'
            trabajo.metodo_pago_id = f"CHZ-CARD-*{last4}-{random.randint(1000, 9999)}"
            trabajo.pagado = True
            trabajo.fecha_pago = timezone.now()
            trabajo.activo = True
            trabajo.save()

            crear_notif(
                request.user, 'sistema',
                f'💳 Pago confirmado (${trabajo.total_a_pagar} USD)',
                f'Tu oferta "{trabajo.titulo}" ha sido activada y ya está disponible para los trabajadores. Comprobante: {trabajo.metodo_pago_id}',
                f'/trabajo/{trabajo.pk}/'
            )
            from .email_utils import enviar_notif_trabajo_publicado
            enviar_notif_trabajo_publicado(trabajo)
            messages.success(request, f'✅ ¡Pago de ${trabajo.total_a_pagar} USD aprobado con éxito! Tu vacante ya está activa.')
            return redirect('candidatos', pk=trabajo.pk)
        else:
            messages.error(request, 'Por favor verifica los datos de tu tarjeta.')
    else:
        form = PagoTarjetaForm()

    ctx = ctx_base(request)
    ctx.update({
        'trabajo': trabajo,
        'form': form,
        'active': 'publicar'
    })
    return render(request, 'core/pagar_trabajo.html', ctx)


@login_required
def editar_trabajo(request, pk):
    trabajo = get_object_or_404(Trabajo, pk=pk, contratista=request.user)
    if request.method == 'POST':
        form = TrabajoForm(request.POST, instance=trabajo)
        if form.is_valid():
            t = form.save(commit=False)
            t.habilidades_req = request.POST.getlist('habilidades_req')
            lat = request.POST.get('lat', ''); lng = request.POST.get('lng', '')
            if lat and lng:
                try:
                    t.lat = float(lat); t.lng = float(lng)
                except ValueError:
                    pass
            t.calcular_tarifas()
            t.save()
            messages.success(request, '✅ Vacante actualizada.')
            return redirect('panel_contratista')
    else:
        form = TrabajoForm(instance=trabajo)
    ctx = ctx_base(request)
    ctx.update({'form': form, 'skills': SKILL_CHOICES, 'titulo_pagina': 'Editar trabajo',
                'btn_label': 'Guardar cambios', 'active': 'publicar'})
    return render(request, 'core/publicar_trabajo.html', ctx)


# ── Candidatos ─────────────────────────────────────────────────────────────────
@login_required
def candidatos_general(request):
    """Lista consolidada de candidatos de TODAS las vacantes del contratista."""
    trabajos_ids = Trabajo.objects.filter(contratista=request.user).values_list('id', flat=True)
    qs = Solicitud.objects.filter(trabajo_id__in=trabajos_ids).select_related('trabajador__profile', 'trabajo')
    estado = request.GET.get('estado', '')
    if estado:
        qs = qs.filter(estado=estado)
    trabajos = Trabajo.objects.filter(contratista=request.user, activo=True)
    ctx = ctx_base(request)
    ctx.update({'solicitudes': qs, 'trabajo': None, 'trabajos_propios': trabajos, 'active': 'candidatos'})
    return render(request, 'core/candidatos.html', ctx)


@login_required
def candidatos(request, pk):
    trabajo = get_object_or_404(Trabajo, pk=pk, contratista=request.user)
    qs = Solicitud.objects.filter(trabajo=trabajo).select_related('trabajador__profile')
    estado = request.GET.get('estado', '')
    if estado:
        qs = qs.filter(estado=estado)
    ctx = ctx_base(request)
    ctx.update({'trabajo': trabajo, 'solicitudes': qs, 'active': 'candidatos'})
    return render(request, 'core/candidatos.html', ctx)


@login_required
def cambiar_estado_solicitud(request, sol_pk, nuevo_estado):
    # Puede ser cambiado por el contratista o en caso de avance a en_progreso/completado también por el trabajador asignado
    sol = get_object_or_404(Solicitud, pk=sol_pk)
    if sol.trabajo.contratista != request.user and sol.trabajador != request.user:
        messages.error(request, 'No tienes permiso para modificar esta solicitud.')
        return redirect('home')

    estados_validos = ['pendiente', 'en_revision', 'aceptado', 'rechazado', 'contratado', 'en_progreso', 'completado']
    if nuevo_estado in estados_validos:
        sol.estado = nuevo_estado
        sol.save()
        labels = {
            'aceptado': '✅ Aceptado', 'rechazado': '❌ Rechazado',
            'contratado': '🏆 Contratado', 'en_revision': '🔍 En revisión',
            'en_progreso': '⚡ En progreso', 'completado': '✨ Trabajo Completado'
        }
        destinatario = sol.trabajador if request.user == sol.trabajo.contratista else sol.trabajo.contratista
        url_destino = f'/resena/crear/{sol.pk}/' if nuevo_estado == 'completado' else '/solicitudes/'
        
        crear_notif(destinatario, 'contratado' if nuevo_estado in ('contratado', 'completado') else 'estado',
                    f'{labels.get(nuevo_estado, nuevo_estado)} — {sol.trabajo.titulo}',
                    f'El estado del trabajo fue actualizado a: {sol.get_estado_display()}.', url_destino)
        
        if nuevo_estado in ('contratado', 'completado'):
            sol.trabajo.estado_vacante = 'ocupada'
            sol.trabajo.save(update_fields=['estado_vacante'])
            verificar_logros(sol.trabajador)
        messages.success(request, f'Estado actualizado a: {sol.get_estado_display()}')

    nxt = request.GET.get('next')
    if nxt:
        return redirect(nxt)
    if request.user == sol.trabajo.contratista:
        return redirect('candidatos', pk=sol.trabajo.pk)
    return redirect('mis_solicitudes')


# ── Calificaciones y Reseñas ───────────────────────────────────────────────────
@login_required
def crear_resena_solicitud(request, sol_pk):
    sol = get_object_or_404(Solicitud, pk=sol_pk)
    if request.user != sol.trabajo.contratista and request.user != sol.trabajador:
        messages.error(request, 'Solo los participantes del trabajo pueden dejar una reseña.')
        return redirect('home')

    destinatario = sol.trabajador if request.user == sol.trabajo.contratista else sol.trabajo.contratista

    # Verificar si ya existe reseña
    if Resena.objects.filter(solicitud=sol, autor=request.user).exists():
        messages.info(request, 'Ya has calificado este trabajo previamente.')
        return redirect('perfil_publico', user_pk=destinatario.pk)

    if request.method == 'POST':
        form = ResenaForm(request.POST)
        if form.is_valid():
            resena = form.save(commit=False)
            resena.trabajo = sol.trabajo
            resena.solicitud = sol
            resena.autor = request.user
            resena.destinatario = destinatario
            resena.etiquetas = request.POST.get('etiquetas', '')
            resena.save()

            crear_notif(destinatario, 'resena',
                        f'⭐ ¡Nueva calificación recibida de {request.user.profile.nombre_display}!',
                        f'Recibiste una puntuación de {resena.calificacion}★ en "{sol.trabajo.titulo}".',
                        f'/perfil/{destinatario.pk}/')

            verificar_logros(destinatario)
            messages.success(request, '✅ ¡Calificación y reseña publicada exitosamente!')
            return redirect('perfil_publico', user_pk=destinatario.pk)
    else:
        form = ResenaForm()

    ctx = ctx_base(request)
    
    if request.user.profile.rol == 'contratista':
        tags = [
            ('Puntualidad', 'Puntualidad'),
            ('Calidad de trabajo', 'Calidad de trabajo'),
            ('Excelente comunicación', 'Excelente comunicación'),
            ('Profesionalismo', 'Profesionalismo'),
            ('Rápido y eficiente', 'Rápido y eficiente'),
        ]
    else:
        tags = [
            ('Pago oportuno', 'Pago oportuno'),
            ('Trato respetuoso', 'Trato respetuoso'),
            ('Instrucciones claras', 'Instrucciones claras'),
            ('Excelentes herramientas', 'Excelentes herramientas'),
            ('Buen ambiente', 'Buen ambiente'),
        ]

    ctx.update({
        'form': form,
        'solicitud': sol,
        'destinatario': destinatario,
        'etiquetas_opciones': tags,
        'active': 'resena'
    })
    return render(request, 'core/crear_resena.html', ctx)


# ── Comprobante de Contratación Digital ─────────────────────────────────────────
@login_required
def comprobante_contrato(request, sol_pk):
    sol = get_object_or_404(Solicitud, pk=sol_pk)
    if not (request.user == sol.trabajo.contratista or request.user == sol.trabajador or request.user.is_staff):
        messages.error(request, 'Acceso denegado a este comprobante.')
        return redirect('home')

    ctx = ctx_base(request)
    ctx.update({'solicitud': sol, 'active': 'contrato'})
    return render(request, 'core/comprobante_contrato.html', ctx)


# ── Portafolio y Galería (Trabajador) ───────────────────────────────────────────
@login_required
def galeria_gestionar(request):
    if request.method == 'POST':
        form = GaleriaItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.usuario = request.user
            item.save()
            messages.success(request, '✅ Foto agregada a la galería exitosamente.')
            return redirect('galeria_gestionar')
    else:
        form = GaleriaItemForm()

    items = GaleriaItem.objects.filter(usuario=request.user)
    ctx = ctx_base(request)
    ctx.update({'form': form, 'items': items, 'active': 'portafolio'})
    return render(request, 'core/galeria_gestionar.html', ctx)


@login_required
def galeria_eliminar(request, pk):
    item = get_object_or_404(GaleriaItem, pk=pk, usuario=request.user)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Imagen eliminada de la galería.')
    return redirect('galeria_gestionar')



# ── Buscar trabajadores (contratista) ───────────────────────────────────────────
@login_required
def buscar_trabajadores(request):
    if request.user.profile.rol != 'contratista':
        return redirect('home_trabajador')
    qs = UserProfile.objects.filter(rol='trabajador').select_related('user')
    q = request.GET.get('q', '')
    if q:
        qs = qs.filter(Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q)
                       | Q(habilidades__icontains=q))
    trabajadores = list(qs[:40])
    ctx = ctx_base(request)
    ctx.update({'trabajadores': trabajadores, 'skills': SKILL_CHOICES, 'active': 'buscar_trab'})
    return render(request, 'core/buscar_trabajadores.html', ctx)


@login_required
def invitar_trabajador(request, user_pk):
    trabajador = get_object_or_404(User, pk=user_pk)
    crear_notif(trabajador, 'sistema', f'Invitación de {request.user.profile.nombre_display}',
                f'{request.user.profile.nombre_display} te invitó a postular a una de sus vacantes.',
                '/inicio/')
    messages.success(request, f'Invitación enviada a {trabajador.get_full_name() or trabajador.username}.')
    return redirect('buscar_trabajadores')


# ── Estadísticas (contratista) ──────────────────────────────────────────────────
@login_required
def estadisticas(request):
    trabajos = Trabajo.objects.filter(contratista=request.user)
    vistas_totales = trabajos.aggregate(s=Sum('vistas'))['s'] or 0
    postulaciones = Solicitud.objects.filter(trabajo__contratista=request.user).count()
    tasa_conv = round((postulaciones / vistas_totales) * 100, 1) if vistas_totales else 0
    tarifa_prom = trabajos.aggregate(a=Avg('presupuesto'))['a'] or 0

    # Por categoría
    cat_counts = trabajos.values('categoria').annotate(c=Count('id')).order_by('-c')
    total_cat = sum(c['c'] for c in cat_counts) or 1
    colores = ['#1FA35A', '#3b82f6', '#F2B90D', '#8b5cf6', '#e5484d']
    por_categoria = []
    for i, c in enumerate(cat_counts[:5]):
        por_categoria.append({
            'nombre': dict(SKILL_CHOICES).get(c['categoria'], c['categoria']),
            'pct': round(c['c'] / total_cat * 100),
            'color': colores[i % len(colores)],
        })

    # Vistas vs aplicaciones últimos 7 días
    dias = []
    hoy = timezone.now().date()
    for i in range(6, -1, -1):
        d = hoy - timezone.timedelta(days=i)
        dias.append({'label': d.strftime('%a')[:3].capitalize(), 'vistas': random.randint(5, 30),
                     'aplicaciones': random.randint(1, 12)})

    ctx = ctx_base(request)
    ctx.update({
        'vistas_totales': vistas_totales, 'postulaciones': postulaciones,
        'tasa_conv': tasa_conv, 'tarifa_prom': round(tarifa_prom, 2),
        'por_categoria': por_categoria, 'dias': dias, 'active': 'stats',
    })
    return render(request, 'core/estadisticas.html', ctx)


# ── Mi empresa ───────────────────────────────────────────────────────────────
@login_required
def mi_empresa(request):
    profile = request.user.profile
    trabajos = Trabajo.objects.filter(contratista=request.user)
    contratados = Solicitud.objects.filter(trabajo__contratista=request.user, estado='contratado').count()
    total_pub = trabajos.count()
    tasa_exito = round((contratados / total_pub) * 100) if total_pub else 0
    anos_plataforma = max((timezone.now() - request.user.date_joined).days // 365, 0)
    ctx = ctx_base(request)
    ctx.update({
        'profile': profile, 'total_pub': total_pub, 'contratados': contratados,
        'tasa_exito': tasa_exito, 'anos_plataforma': anos_plataforma or 1, 'active': 'empresa',
    })
    return render(request, 'core/mi_empresa.html', ctx)


# ── Términos y Política ─────────────────────────────────────────────────────────
def terminos_condiciones(request):
    ctx = ctx_base(request)
    if request.user.is_authenticated and request.method == 'POST':
        AceptacionTerminos.objects.update_or_create(
            usuario=request.user, defaults={'aceptado': True})
        messages.success(request, 'Términos aceptados.')
        return redirect('home')
    return render(request, 'core/terminos_condiciones.html', ctx)


def politica_privacidad(request):
    ctx = ctx_base(request)
    if request.user.is_authenticated and request.method == 'POST':
        messages.success(request, 'Política de privacidad aceptada.')
        return redirect('mi_empresa' if request.user.profile.rol == 'contratista' else 'perfil_trabajador')
    return render(request, 'core/politica_privacidad.html', ctx)


# ── Perfiles ───────────────────────────────────────────────────────────────────
@login_required
def perfil_trabajador(request):
    profile = request.user.profile
    verificar_logros(request.user)
    mis_sols = Solicitud.objects.filter(trabajador=request.user)
    stats = {
        'completados': mis_sols.filter(estado='contratado').count(),
        'calificacion': profile.calificacion,
        'ganado_mes': _ganado_este_mes(request.user),
    }
    resenas = Resena.objects.filter(destinatario=request.user)[:5]
    obtenidos = LogroObtenido.objects.filter(usuario=request.user).select_related('logro')[:4]
    ctx = ctx_base(request)
    ctx.update({'profile': profile, 'stats': stats, 'resenas': resenas,
                'logros_obtenidos': obtenidos, 'active': 'perfil'})
    return render(request, 'core/perfil_trabajador.html', ctx)


@login_required
def perfil_contratista(request):
    return redirect('mi_empresa')


@login_required
def perfil_publico(request, user_pk):
    user_obj = get_object_or_404(User, pk=user_pk)
    profile = user_obj.profile
    resenas = Resena.objects.filter(destinatario=user_obj)[:10]
    mis_sols = Solicitud.objects.filter(trabajador=user_obj)
    stats = {'aplicaciones': mis_sols.count(), 'contratados': mis_sols.filter(estado='contratado').count()}
    ctx = ctx_base(request)
    ctx.update({'profile': profile, 'resenas': resenas, 'stats': stats, 'user_obj': user_obj})
    return render(request, 'core/perfil_publico.html', ctx)


@login_required
def editar_perfil(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, request.FILES, instance=profile, rol=profile.rol)
        if form.is_valid():
            p = form.save(commit=False)
            if profile.rol == 'trabajador':
                p.habilidades = request.POST.getlist('habilidades')
            nombre = request.POST.get('nombre', '').strip()
            if nombre:
                partes = nombre.split(' ', 1)
                request.user.first_name = partes[0]
                request.user.last_name = partes[1] if len(partes) > 1 else ''
                request.user.save(update_fields=['first_name', 'last_name'])
            p.save()
            messages.success(request, '✅ Perfil actualizado.')
            return redirect('perfil_trabajador' if profile.rol == 'trabajador' else 'mi_empresa')
    else:
        form = EditarPerfilForm(instance=profile, rol=profile.rol,
                                initial={'nombre': request.user.get_full_name()})
    ctx = ctx_base(request)
    ctx.update({'form': form, 'profile': profile, 'skills': SKILL_CHOICES, 'active': 'perfil'})
    return render(request, 'core/editar_perfil.html', ctx)


@login_required
def toggle_disponibilidad(request):
    if request.method == 'POST':
        p = request.user.profile
        p.disponible = not p.disponible
        p.save(update_fields=['disponible'])
        messages.success(request, f'Ahora estás {"disponible" if p.disponible else "no disponible"}.')
    return redirect('perfil_trabajador')


# ── Notificaciones ─────────────────────────────────────────────────────────────
@login_required
def notificaciones(request):
    if request.GET.get('marcar_todas'):
        Notificacion.objects.filter(usuario=request.user, leida=False).update(leida=True)
        messages.success(request, 'Todas marcadas como leídas.')
    notifs = Notificacion.objects.filter(usuario=request.user)[:40]
    ctx = ctx_base(request)
    ctx.update({'notificaciones': notifs, 'active': 'notif'})
    return render(request, 'core/notificaciones.html', ctx)


@login_required
def marcar_notif_leida(request, pk):
    n = get_object_or_404(Notificacion, pk=pk, usuario=request.user)
    n.leida = True; n.save()
    if n.url:
        return redirect(n.url)
    return redirect('notificaciones')


# ── Asistente IA ─────────────────────────────────────────────────────────────
@login_required
def asistente(request):
    ctx = ctx_base(request)
    ctx['active'] = 'asistente'
    return render(request, 'core/asistente.html', ctx)


def _generar_respuesta_asistente(request, texto):
    """Motor de generación de respuestas contextual (basado en reglas + datos reales de BD).
    No depende de servicios externos: funciona 100% localmente con la información
    real del usuario y de la plataforma."""
    texto_l = texto.lower().strip()
    user = request.user
    profile = user.profile
    rol = profile.rol

    def contiene(*palabras):
        return any(p in texto_l for p in palabras)

    # ── TRABAJADOR ──────────────────────────────────────────────────────────
    if rol == 'trabajador':
        if contiene('mejor pagado', 'mejor pagados', 'mejor pagados', 'mas paga', 'más paga', 'mejor pagan', 'salario', 'cuanto pagan', 'cuánto pagan', 'mejores trabajos'):
            top = Trabajo.objects.filter(activo=True).order_by('-presupuesto')[:3]
            if top:
                lista = '\n'.join([f"• **{t.titulo}** — ${t.presupuesto} ({t.ubicacion})" for t in top])
                return (f"Estos son los trabajos mejor pagados disponibles ahora mismo:\n\n{lista}\n\n"
                        f"¿Quieres que te muestre más detalles de alguno o filtre por tu categoría de habilidad?")
            return "Ahora mismo no hay vacantes activas, pero revisa la sección 'Buscar empleos' regularmente — se publican nuevas todos los días."

        if 'perfil' in texto_l and contiene('mejor', 'completa', 'incompleto', 'falta'):
            faltantes = []
            if not user.get_full_name(): faltantes.append('tu nombre completo')
            if not profile.telefono: faltantes.append('tu teléfono')
            if not profile.ubicacion: faltantes.append('tu ubicación')
            if not profile.descripcion: faltantes.append('una descripción sobre ti')
            if not profile.foto: faltantes.append('una foto de perfil')
            if not profile.habilidades: faltantes.append('tus habilidades')
            pct = profile.completitud_perfil
            if faltantes:
                items = ', '.join(faltantes)
                return (f"Tu perfil está al **{pct}%** de completitud. Te recomiendo agregar: {items}. "
                        f"Un perfil completo recibe hasta 3 veces más solicitudes aceptadas por los empleadores. "
                        f"Puedes editarlo desde 'Mi perfil' → 'Editar'.")
            return f"¡Tu perfil ya está al {pct}%! Está muy completo. Sigue así, eso ayuda mucho a que los empleadores confíen en ti."

        if contiene('entrevista', 'preparar', 'consejo', 'consejos', 'tips'):
            return ("Aquí van algunos consejos para destacar:\n\n"
                    "1. **Responde rápido** — los empleadores prefieren candidatos que contestan en minutos.\n"
                    "2. **Sé específico** en tu mensaje de aplicación: menciona experiencia concreta.\n"
                    "3. **Llega puntual** si es un trabajo presencial urgente.\n"
                    "4. **Pide reseñas** después de cada trabajo — tu calificación importa mucho.\n\n"
                    "¿Quieres que revise tu perfil para ver qué más puedes mejorar?")

        if contiene('tendencia', 'demanda', 'que habilidad', 'qué habilidad', 'habilidades piden'):
            top_cat = Trabajo.objects.filter(activo=True).values('categoria').annotate(c=Count('id')).order_by('-c')[:3]
            if top_cat:
                nombres = [dict(SKILL_CHOICES).get(c['categoria'], c['categoria']) for c in top_cat]
                return (f"Las habilidades más solicitadas en este momento en Chambazo son: "
                        f"**{', '.join(nombres)}**. Si tienes experiencia en alguna, actualiza tu perfil para aparecer en más búsquedas.")
            return "Aún no hay suficientes datos de demanda, pero electricidad, plomería y limpieza suelen ser las más solicitadas en El Salvador."

        if contiene('como funciona el pago', 'cómo funciona el pago', 'pago seguro', 'funciona el pago'):
            return ("Chambazo protege tu pago: cuando un empleador te contrata, el monto queda reservado. "
                    "Al completar y confirmar el trabajo, el pago se libera a tu cuenta. Puedes ver tu historial completo en 'Ganancias'.")

        if contiene('gano', 'ganancia', 'cuanto he ganado', 'cuánto he ganado', 'dinero'):
            total = _ganado_este_mes(user)
            completados = Solicitud.objects.filter(trabajador=user, estado='contratado').count()
            return (f"Este mes has ganado **${total}** en Chambazo, con **{completados}** trabajo{'s' if completados != 1 else ''} completado{'s' if completados != 1 else ''} en total. "
                    f"Puedes ver el detalle completo en la sección 'Ganancias'.")

        if contiene('urgente', 'urgentes', 'inmediato', 'ya mismo'):
            n = Trabajo.objects.filter(activo=True, es_urgente=True).count()
            return (f"Ahora mismo hay **{n}** trabajo{'s' if n != 1 else ''} urgente{'s' if n != 1 else ''} publicados. "
                    f"Los urgentes pagan rápido pero requieren respuesta inmediata. Revisa la sección 'Urgentes' en el menú.")

        if contiene('solicitud', 'aplique', 'apliqué', 'postulacion', 'postulación', 'estado de mi'):
            pend = Solicitud.objects.filter(trabajador=user, estado__in=['pendiente', 'en_revision']).count()
            acept = Solicitud.objects.filter(trabajador=user, estado__in=['aceptado', 'contratado']).count()
            return (f"Tienes **{pend}** solicitud{'es' if pend != 1 else ''} en revisión y **{acept}** aceptada{'s' if acept != 1 else ''}. "
                    f"Puedes ver el detalle completo con línea de tiempo en 'Mis solicitudes'.")

        if contiene('como me califica', 'cómo me califica', 'calificacion', 'calificación', 'estrellas'):
            return (f"Tu calificación actual es **{profile.calificacion} ★** basada en {profile.total_trabajos} trabajos. "
                    f"Los empleadores te califican después de cada trabajo completado según calidad, puntualidad y comunicación.")

        if contiene('logro', 'insignia', 'puntos', 'nivel'):
            obtenidos = LogroObtenido.objects.filter(usuario=user).count()
            return (f"Llevas **{obtenidos}** logros desbloqueados. Sigue completando trabajos, manteniendo buena calificación "
                    f"y respondiendo rápido para desbloquear más insignias. Revisa tu progreso en 'Logros'.")

        if contiene('hola', 'buenas', 'que tal', 'qué tal', 'ayuda'):
            return (f"¡Hola {user.first_name or user.username}! 👋 Puedo ayudarte con: encontrar trabajos, mejorar tu perfil, "
                    f"consejos para aplicar, o revisar tus ganancias y solicitudes. ¿Qué necesitas?")

    # ── CONTRATISTA ──────────────────────────────────────────────────────────
    else:
        if contiene('redactar', 'descripcion de vacante', 'descripción de vacante', 'como publico', 'cómo publico'):
            return ("Para una vacante atractiva incluye: 1) título claro y específico, "
                    "2) descripción detallada del trabajo y materiales disponibles, "
                    "3) presupuesto justo para la zona, 4) requisitos concretos. "
                    "Ve a 'Publicar trabajo' en el menú y te guío en cada campo.")

        if contiene('candidato ideal', 'encontrar candidato', 'mejor candidato', 'como encuentro', 'cómo encuentro', 'encontrar el candidato'):
            n = UserProfile.objects.filter(rol='trabajador', disponible=True).count()
            return (f"Hay **{n}** trabajadores disponibles ahora mismo en la plataforma. "
                    f"Te recomiendo revisar el % de compatibilidad en cada candidato — indica qué tan bien coinciden sus "
                    f"habilidades con lo que pediste. También puedes usar 'Buscar trabajadores' para invitar directamente a perfiles calificados.")

        if contiene('retener', 'talento', 'fidelizar'):
            return ("Para retener buen talento: paga a tiempo, califica con honestidad, da retroalimentación clara "
                    "y ofrece trabajo recurrente a quienes tengan buen desempeño. Los trabajadores con buenas experiencias "
                    "suelen aceptar más rápido tus próximas vacantes.")

        if contiene('cuanto deberia pagar', 'cuánto debería pagar', 'tarifa', 'salario', 'cuanto pagar'):
            prom = Trabajo.objects.filter(activo=True).aggregate(a=Avg('presupuesto'))['a'] or 0
            return (f"La tarifa promedio actual en la plataforma es de **${prom:.2f}** por trabajo. "
                    f"Varía según categoría, urgencia y duración — los trabajos urgentes suelen pagar 15-20% más.")

        if contiene('estadistica', 'estadística', 'rendimiento', 'como van mis vacantes', 'cómo van mis vacantes'):
            trabajos = Trabajo.objects.filter(contratista=user)
            vistas = trabajos.aggregate(s=Sum('vistas'))['s'] or 0
            postul = Solicitud.objects.filter(trabajo__contratista=user).count()
            return (f"Tus vacantes han recibido **{vistas}** vistas y **{postul}** postulaciones en total. "
                    f"Revisa el detalle completo con gráficas en la sección 'Estadísticas'.")

        if contiene('candidatos pendientes', 'quien aplico', 'quién aplicó', 'solicitudes recibidas'):
            n = Solicitud.objects.filter(trabajo__contratista=user, estado='pendiente').count()
            return (f"Tienes **{n}** solicitud{'es' if n != 1 else ''} pendiente{'s' if n != 1 else ''} de revisar. "
                    f"Ve a 'Candidatos' para verlas y responder.")

        if contiene('hola', 'buenas', 'que tal', 'qué tal', 'ayuda'):
            return (f"¡Hola {user.first_name or profile.empresa}! 👋 Puedo ayudarte a redactar vacantes, encontrar candidatos, "
                    f"revisar tus estadísticas o darte consejos de contratación. ¿En qué te ayudo?")

    # ── Respuesta genérica de respaldo (siempre contextual, nunca vacía) ────
    fallback_trabajador = [
        "Puedo ayudarte a encontrar trabajos que coincidan con tus habilidades, mejorar tu perfil, "
        "o resolver dudas sobre pagos y calificaciones. ¿Sobre qué tema quieres saber más?",
        "Cuéntame si necesitas ayuda para: buscar trabajo, revisar el estado de tus solicitudes, "
        "entender cómo funciona el pago, o mejorar tu perfil para conseguir más oportunidades.",
    ]
    fallback_contratista = [
        "Puedo ayudarte a redactar una vacante atractiva, encontrar el candidato ideal, "
        "o entender tus estadísticas de reclutamiento. ¿Qué necesitas?",
        "Cuéntame si quieres ayuda para: publicar una vacante, revisar candidatos, "
        "o conocer las tarifas promedio del mercado en El Salvador.",
    ]
    import random as _r
    return _r.choice(fallback_trabajador if rol == 'trabajador' else fallback_contratista)


@login_required
def asistente_responder(request):
    """Endpoint que genera una respuesta del asistente (server-side, sin dependencias externas)."""
    from django.http import JsonResponse
    if request.method != 'POST':
        return JsonResponse({'error': 'method'}, status=405)
    texto = request.POST.get('mensaje', '').strip()
    if not texto:
        return JsonResponse({'respuesta': 'Escribe tu pregunta y con gusto te ayudo.'})
    respuesta = _generar_respuesta_asistente(request, texto)
    return JsonResponse({'respuesta': respuesta})


# ── NUEVO: GESTIÓN DE ESCROW Y EVIDENCIAS DE TRABAJO ───────────────────────────
from .models import TransaccionEscrow, EvidenciaTrabajo
import uuid

@login_required
def depositar_escrow(request, sol_pk):
    """Vista para que el contratista deposite fondos en Escrow y contrate formalmente."""
    solicitud = get_object_or_404(Solicitud, pk=sol_pk, trabajo__contratista=request.user)
    
    # Validar que esté en un estado contratable
    if solicitud.estado not in ['aceptado', 'pendiente', 'en_revision']:
        messages.error(request, 'Esta solicitud ya está procesada o no es válida.')
        return redirect('candidatos', pk=solicitud.trabajo.pk)

    if request.method == 'POST':
        tarjeta = request.POST.get('tarjeta', '').replace(' ', '')
        if not tarjeta:
            messages.error(request, 'Ingresa una tarjeta válida.')
            return redirect('depositar_escrow', sol_pk=sol_pk)

        # Simular transacción exitosa
        monto = solicitud.tarifa_propuesta if solicitud.tarifa_propuesta else solicitud.trabajo.presupuesto
        last4 = tarjeta[-4:] if len(tarjeta) >= 4 else 'XXXX'
        tx_id = f"CHZ-ESCROW-{uuid.uuid4().hex[:8].upper()}"

        TransaccionEscrow.objects.create(
            solicitud=solicitud,
            monto=monto,
            estado='retenido',
            metodo_pago_simulado=f"****{last4} - {tx_id}"
        )
        
        # Cambiar estado a contratado
        solicitud.estado = 'contratado'
        solicitud.save()
        
        solicitud.trabajo.estado_vacante = 'ocupada'
        solicitud.trabajo.save(update_fields=['estado_vacante'])

        # Notificar al trabajador
        from .email_utils import enviar_notif_estado_solicitud
        enviar_notif_estado_solicitud(solicitud.trabajador, solicitud)

        messages.success(request, f'✅ Fondos retenidos en Escrow. Has contratado a {solicitud.trabajador.first_name or solicitud.trabajador.username}.')
        return redirect('gestionar_trabajo', sol_pk=sol_pk)

    ctx = ctx_base(request)
    ctx['solicitud'] = solicitud
    ctx['active'] = 'candidatos'
    return render(request, 'core/depositar_escrow.html', ctx)


@login_required
def gestionar_trabajo(request, sol_pk):
    """Consola para ver el estado del Escrow y subir evidencias fotográficas."""
    solicitud = get_object_or_404(Solicitud, pk=sol_pk)
    # Validar acceso
    if request.user != solicitud.trabajo.contratista and request.user != solicitud.trabajador:
        messages.error(request, 'No tienes permiso para ver este trabajo.')
        return redirect('home')

    if request.method == 'POST':
        imagen = request.FILES.get('imagen')
        descripcion = request.POST.get('descripcion', '')
        if imagen:
            EvidenciaTrabajo.objects.create(
                solicitud=solicitud,
                subido_por=request.user,
                tipo='contratista' if request.user == solicitud.trabajo.contratista else 'trabajador',
                imagen=imagen,
                descripcion=descripcion
            )
            messages.success(request, '📸 Evidencia subida correctamente.')
        return redirect('gestionar_trabajo', sol_pk=sol_pk)

    escrow = getattr(solicitud, 'escrow', None)
    evidencias = solicitud.evidencias.all()

    ctx = ctx_base(request)
    ctx.update({
        'solicitud': solicitud,
        'escrow': escrow,
        'evidencias': evidencias,
        'active': 'candidatos' if request.user == solicitud.trabajo.contratista else 'solicitudes'
    })
    return render(request, 'core/gestionar_trabajo.html', ctx)


@login_required
def liberar_fondos_escrow(request, sol_pk):
    """El contratista aprueba la finalización del trabajo y libera el pago."""
    solicitud = get_object_or_404(Solicitud, pk=sol_pk, trabajo__contratista=request.user)
    if not hasattr(solicitud, 'escrow') or solicitud.escrow.estado != 'retenido':
        messages.error(request, 'Esta transacción no está retenida en Escrow.')
        return redirect('gestionar_trabajo', sol_pk=sol_pk)

    if request.method == 'POST':
        escrow = solicitud.escrow
        escrow.estado = 'liberado'
        escrow.save()

        solicitud.estado = 'completado'
        solicitud.save()

        # Generar comprobante
        from .pdf_utils import generar_comprobante_pdf
        pdf_path = generar_comprobante_pdf(solicitud, escrow)
        if pdf_path:
            escrow.comprobante_pdf.name = pdf_path
            escrow.save()

        # Notificar por correo
        from .email_utils import enviar_notif_trabajo_completado_exito
        enviar_notif_trabajo_completado_exito(solicitud, escrow)

        crear_notif(
            solicitud.trabajador, 'sistema',
            '💸 Fondos Liberados & Califica a tu Contratista',
            f'El pago de ${escrow.monto} ha sido liberado. ¡Haz clic para dejar una reseña sobre tu experiencia con {request.user.profile.nombre_display}!',
            f'/resena/crear/{solicitud.pk}/'
        )

        messages.success(request, '✨ Trabajo completado y fondos liberados. ¡No olvides dejar tu reseña!')
        return redirect('crear_resena_solicitud', sol_pk=sol_pk)

    return redirect('gestionar_trabajo', sol_pk=sol_pk)


@login_required
def descargar_comprobante_pdf(request, pk):
    """Descarga el comprobante PDF de una transacción en Escrow."""
    escrow = get_object_or_404(TransaccionEscrow, pk=pk)
    solicitud = escrow.solicitud
    if request.user != solicitud.trabajo.contratista and request.user != solicitud.trabajador:
        messages.error(request, 'No autorizado.')
        return redirect('home')

    if not escrow.comprobante_pdf:
        messages.error(request, 'El comprobante aún no ha sido generado.')
        return redirect('gestionar_trabajo', sol_pk=solicitud.pk)

    from django.http import HttpResponse, Http404
    from django.conf import settings
    import os
    file_path = os.path.join(settings.MEDIA_ROOT, escrow.comprobante_pdf.name)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/pdf")
            response['Content-Disposition'] = f'inline; filename="Chambazo_Recibo_{escrow.id}.pdf"'
            return response
    raise Http404("Comprobante no encontrado")


# ── NUEVO: CONTRATO DIGITAL ───────────────────────────────────────────────────
from .models import ContratoDigital

@login_required
def crear_contrato_digital(request, sol_pk):
    """El contratista define el alcance, firma digitalmente e inicia la contratación."""
    solicitud = get_object_or_404(Solicitud, pk=sol_pk, trabajo__contratista=request.user)
    
    if solicitud.estado not in ['aceptado', 'pendiente', 'en_revision']:
        messages.error(request, 'Esta solicitud ya no se puede contratar.')
        return redirect('candidatos', pk=solicitud.trabajo.pk)

    if request.method == 'POST':
        alcance = request.POST.get('alcance_trabajo')
        plazo = request.POST.get('plazo_entrega')
        firma = request.POST.get('firma_contratista')
        
        monto = solicitud.tarifa_propuesta if solicitud.tarifa_propuesta else solicitud.trabajo.presupuesto
        
        # Eliminar si existe previo por si acaso
        ContratoDigital.objects.filter(solicitud=solicitud).delete()
        
        contrato = ContratoDigital.objects.create(
            solicitud=solicitud,
            alcance_trabajo=alcance,
            plazo_entrega=plazo,
            costo_total=monto,
            firma_contratista=firma,
            firmado_contratista_at=timezone.now(),
            estado='pendiente'
        )
        
        messages.info(request, '📝 Contrato digital firmado. Ahora procede al depósito en Escrow para activarlo.')
        return redirect('depositar_escrow', sol_pk=solicitud.pk)

    ctx = ctx_base(request)
    ctx['solicitud'] = solicitud
    ctx['active'] = 'candidatos'
    return render(request, 'core/crear_contrato.html', ctx)


@login_required
def firmar_contrato(request, sol_pk):
    """El trabajador visualiza las condiciones del contrato redactado y firma digitalmente."""
    solicitud = get_object_or_404(Solicitud, pk=sol_pk, trabajador=request.user)
    contrato = get_object_or_404(ContratoDigital, solicitud=solicitud)

    if request.method == 'POST':
        firma = request.POST.get('firma_trabajador')
        contrato.firma_trabajador = firma
        contrato.firmado_trabajador_at = timezone.now()
        contrato.estado = 'vigente'
        contrato.save()
        
        # Notificar al contratista que el contrato está activo
        crear_notif(
            solicitud.trabajo.contratista, 'sistema',
            '✍️ Contrato Digital Firmado',
            f'{request.user.profile.nombre_display} ha firmado el contrato digital para "{solicitud.trabajo.titulo}". El trabajo ya está vigente.',
            f'/solicitud/{solicitud.pk}/gestionar/'
        )
        
        messages.success(request, '📝 ¡Has firmado el contrato digital! El trabajo está ahora activo.')
        return redirect('gestionar_trabajo', sol_pk=solicitud.pk)

    ctx = ctx_base(request)
    ctx['contrato'] = contrato
    ctx['active'] = 'solicitudes'
    return render(request, 'core/firmar_contrato.html', ctx)

