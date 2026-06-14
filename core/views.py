import secrets
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Avg
from django.utils import timezone
from django.http import JsonResponse
from .models import (UserProfile, Trabajo, Solicitud, Resena, GaleriaItem,
                     Notificacion, PasswordResetToken, SKILL_CHOICES)
from .forms import (LoginForm, RegistroTrabajadorForm, RegistroContratistaForm,
                    HabilidadesForm, DescripcionEmpresaForm, RecuperarPasswordForm,
                    NuevaPasswordForm, PerfilForm, HabilidadesUpdateForm,
                    BuscarOfertasForm, SolicitudForm, TrabajoForm, ResenaForm)

# ─── helpers ──────────────────────────────────────────────────────────────────
def crear_notificacion(usuario, tipo, titulo, mensaje, url=''):
    Notificacion.objects.create(usuario=usuario, tipo=tipo, titulo=titulo,
                                 mensaje=mensaje, url=url)

def notif_count(request):
    if request.user.is_authenticated:
        return Notificacion.objects.filter(usuario=request.user, leida=False).count()
    return 0

# ─── HU002 – Inicio de sesión ─────────────────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = LoginForm()
    error = None
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            rol = request.POST.get('rol_login', 'trabajador')
            try:
                user_obj = User.objects.get(email=email)
                user = authenticate(request, username=user_obj.username, password=password)
                if user:
                    if hasattr(user, 'profile') and user.profile.rol == rol:
                        login(request, user)
                        return redirect('home')
                    else:
                        error = 'El rol seleccionado no corresponde a tu cuenta.'
                else:
                    error = 'Correo o contraseña incorrectos.'
            except User.DoesNotExist:
                error = 'No existe una cuenta con ese correo.'
    return render(request, 'core/login.html', {'form': form, 'error': error})

# ─── HU004 – Cerrar sesión ────────────────────────────────────────────────────
def logout_view(request):
    logout(request)
    return redirect('login')

# ─── HU003 – Recuperar contraseña ────────────────────────────────────────────
def recuperar_password(request):
    if request.method == 'POST':
        form = RecuperarPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                token = secrets.token_urlsafe(32)
                PasswordResetToken.objects.create(user=user, token=token)
                # En producción se enviaría por email; mostramos el link directamente
                reset_url = request.build_absolute_uri(f'/reset-password/{token}/')
                messages.success(request,
                    f'Enlace de recuperación generado. En producción se enviaría a {email}. '
                    f'Link de prueba: {reset_url}')
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, 'No existe una cuenta con ese correo.')
    else:
        form = RecuperarPasswordForm()
    return render(request, 'core/recuperar_password.html', {'form': form})

def reset_password(request, token):
    reset = get_object_or_404(PasswordResetToken, token=token)
    if not reset.is_valid():
        messages.error(request, 'El enlace expiró o ya fue utilizado.')
        return redirect('recuperar_password')
    if request.method == 'POST':
        form = NuevaPasswordForm(request.POST)
        if form.is_valid():
            reset.user.set_password(form.cleaned_data['password'])
            reset.user.save()
            reset.usado = True
            reset.save()
            messages.success(request, '¡Contraseña actualizada exitosamente!')
            return redirect('login')
    else:
        form = NuevaPasswordForm()
    return render(request, 'core/reset_password.html', {'form': form, 'token': token})

# ─── HU007 / HU005 / HU006 – Registro con selección de rol ──────────────────
def registro_step1(request):
    if request.method == 'POST':
        rol = request.POST.get('rol')
        if rol in ['trabajador', 'contratista']:
            request.session['reg_rol'] = rol
            return redirect('registro_step2')
    return render(request, 'core/registro_step1.html')

def registro_step2(request):
    rol = request.session.get('reg_rol')
    if not rol:
        return redirect('registro_step1')
    FormClass = RegistroTrabajadorForm if rol == 'trabajador' else RegistroContratistaForm
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            request.session['reg_data'] = form.cleaned_data
            return redirect('registro_step3')
    else:
        form = FormClass()
    return render(request, 'core/registro_step2.html', {'form': form, 'rol': rol})

def registro_step3(request):
    rol = request.session.get('reg_rol')
    reg_data = request.session.get('reg_data')
    if not rol or not reg_data:
        return redirect('registro_step1')
    FormClass = HabilidadesForm if rol == 'trabajador' else DescripcionEmpresaForm
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            # Construir username único
            base = reg_data['email'].split('@')[0]
            username, i = base, 1
            while User.objects.filter(username=username).exists():
                username = f"{base}{i}"; i += 1
            # Nombre completo
            nombre_parts = reg_data.get('nombre', '').split(' ', 1)
            user = User.objects.create_user(
                username=username, email=reg_data['email'],
                password=reg_data['password'],
                first_name=nombre_parts[0],
                last_name=nombre_parts[1] if len(nombre_parts) > 1 else '')
            kwargs = dict(user=user, rol=rol,
                          telefono=reg_data.get('telefono', ''),
                          ubicacion=reg_data.get('ubicacion', ''))
            if rol == 'trabajador':
                kwargs['habilidades'] = list(form.cleaned_data.get('habilidades', []))
            else:
                kwargs['empresa'] = reg_data.get('empresa', '')
                kwargs['descripcion'] = form.cleaned_data.get('descripcion', '')
            UserProfile.objects.create(**kwargs)
            # Limpiar sesión
            for k in ('reg_rol', 'reg_data'):
                request.session.pop(k, None)
            login(request, user)
            return redirect('home')
    else:
        form = FormClass()
    return render(request, 'core/registro_step3.html',
                  {'form': form, 'rol': rol, 'skills': SKILL_CHOICES})

# ─── HOME (despacha por rol) ──────────────────────────────────────────────────
@login_required
def home(request):
    if request.user.profile.rol == 'contratista':
        return redirect('panel_contratista')
    return redirect('home_trabajador')

# ─── HU012 / HU013 / HU014 – Buscar / Filtrar / Ver ofertas ──────────────────
@login_required
def home_trabajador(request):
    form = BuscarOfertasForm(request.GET or None)
    trabajos = Trabajo.objects.filter(activo=True).select_related('contratista__profile')
    if form.is_valid():
        q = form.cleaned_data.get('q')
        cat = form.cleaned_data.get('categoria')
        ubi = form.cleaned_data.get('ubicacion')
        pmin = form.cleaned_data.get('precio_min')
        pmax = form.cleaned_data.get('precio_max')
        solo_disp = form.cleaned_data.get('solo_disponibles')
        if q:
            trabajos = trabajos.filter(
                Q(titulo__icontains=q) | Q(descripcion__icontains=q) |
                Q(categoria__icontains=q))
        if cat:
            trabajos = trabajos.filter(categoria=cat)
        if ubi:
            trabajos = trabajos.filter(ubicacion__icontains=ubi)
        if pmin is not None:
            trabajos = trabajos.filter(presupuesto__gte=pmin)
        if pmax is not None:
            trabajos = trabajos.filter(presupuesto__lte=pmax)
        if solo_disp:
            trabajos = trabajos.filter(estado_vacante='disponible')

    # HU014 – mostrar según habilidades del perfil primero
    profile = request.user.profile
    habs = profile.habilidades or []
    if habs:
        match = trabajos.filter(habilidades_req__overlap=habs) if hasattr(trabajos.query, 'compiler') else trabajos
        # fallback simple: filter in Python
        match_ids = [t.pk for t in trabajos if any(h in (t.habilidades_req or []) for h in habs)]
        otros_ids = [t.pk for t in trabajos if t.pk not in match_ids]
        from itertools import chain
        trabajos_list = list(Trabajo.objects.filter(pk__in=match_ids).filter(activo=True)) + \
                        list(Trabajo.objects.filter(pk__in=otros_ids).filter(activo=True))
    else:
        trabajos_list = list(trabajos)

    stats = {
        'trabajos_hoy': Trabajo.objects.filter(activo=True, creado__date=timezone.now().date()).count(),
        'total_trabajadores': UserProfile.objects.filter(rol='trabajador').count(),
        'calificacion': Resena.objects.aggregate(avg=Avg('calificacion'))['avg'] or 4.8,
    }
    return render(request, 'core/home_trabajador.html', {
        'trabajos': trabajos_list, 'form': form, 'stats': stats,
        'skills': SKILL_CHOICES, 'notif_count': notif_count(request),
    })

# ─── HU015 – Ver detalles de oferta ──────────────────────────────────────────
@login_required
def trabajo_detalle(request, pk):
    trabajo = get_object_or_404(Trabajo, pk=pk)
    # Incrementar vistas
    Trabajo.objects.filter(pk=pk).update(vistas=trabajo.vistas + 1)
    trabajo.refresh_from_db()
    ya_aplico = False
    mi_solicitud = None
    if request.user.profile.rol == 'trabajador':
        mi_solicitud = Solicitud.objects.filter(trabajo=trabajo, trabajador=request.user).first()
        ya_aplico = mi_solicitud is not None
    resenas = Resena.objects.filter(trabajo=trabajo).select_related('autor')
    return render(request, 'core/trabajo_detalle.html', {
        'trabajo': trabajo, 'ya_aplico': ya_aplico,
        'mi_solicitud': mi_solicitud, 'resenas': resenas,
        'notif_count': notif_count(request),
    })

# ─── HU016 – Aplicar a una vacante ───────────────────────────────────────────
@login_required
def aplicar_trabajo(request, pk):
    if request.user.profile.rol != 'trabajador':
        return redirect('home')
    trabajo = get_object_or_404(Trabajo, pk=pk, activo=True)
    if trabajo.estado_vacante == 'ocupada':
        messages.error(request, 'Esta vacante ya está ocupada.')
        return redirect('trabajo_detalle', pk=pk)
    if Solicitud.objects.filter(trabajo=trabajo, trabajador=request.user).exists():
        messages.info(request, 'Ya aplicaste a este trabajo.')
        return redirect('trabajo_detalle', pk=pk)

    if request.method == 'POST':
        form = SolicitudForm(request.POST)
        if form.is_valid():
            sol = form.save(commit=False)
            sol.trabajo = trabajo
            sol.trabajador = request.user
            sol.save()
            # HU020 – actualizar estado vacante si tiene suficientes candidatos
            if trabajo.solicitudes.count() >= 3 and trabajo.estado_vacante == 'disponible':
                Trabajo.objects.filter(pk=pk).update(estado_vacante='en_proceso')
            # HU015 – notificar al contratista
            crear_notificacion(trabajo.contratista, 'solicitud',
                f'Nueva postulación: {trabajo.titulo}',
                f'{request.user.get_full_name()} aplicó a tu vacante.',
                f'/contratista/trabajo/{pk}/candidatos/')
            return render(request, 'core/solicitud_enviada.html',
                          {'trabajo': trabajo, 'solicitud': sol})
    else:
        form = SolicitudForm()
    return render(request, 'core/aplicar_trabajo.html', {'trabajo': trabajo, 'form': form})

# ─── HU017 – Aplicación rápida ───────────────────────────────────────────────
@login_required
def aplicar_rapido(request, pk):
    if request.user.profile.rol != 'trabajador':
        return redirect('home')
    trabajo = get_object_or_404(Trabajo, pk=pk, activo=True)
    if trabajo.estado_vacante == 'ocupada':
        messages.error(request, 'Esta vacante ya está ocupada.')
        return redirect('trabajo_detalle', pk=pk)
    sol, created = Solicitud.objects.get_or_create(
        trabajo=trabajo, trabajador=request.user,
        defaults={'rapida': True})
    if created:
        crear_notificacion(trabajo.contratista, 'solicitud',
            f'Postulación rápida: {trabajo.titulo}',
            f'{request.user.get_full_name()} aplicó rápidamente a tu vacante.',
            f'/contratista/trabajo/{pk}/candidatos/')
        return render(request, 'core/solicitud_enviada.html',
                      {'trabajo': trabajo, 'solicitud': sol})
    messages.info(request, 'Ya aplicaste a este trabajo.')
    return redirect('trabajo_detalle', pk=pk)

# ─── HU018/HU019 – Confirmar / Historial de postulaciones ────────────────────
@login_required
def mis_solicitudes(request):
    if request.user.profile.rol != 'trabajador':
        return redirect('home')
    solicitudes = Solicitud.objects.filter(
        trabajador=request.user).select_related('trabajo__contratista__profile')
    return render(request, 'core/mis_solicitudes.html',
                  {'solicitudes': solicitudes, 'notif_count': notif_count(request)})

# ─── HU011 – Visualizar perfil ───────────────────────────────────────────────
@login_required
def perfil_trabajador(request):
    profile = request.user.profile
    profile.actualizar_calificacion()
    resenas = Resena.objects.filter(destinatario=request.user)
    galeria = GaleriaItem.objects.filter(trabajador=request.user)
    return render(request, 'core/perfil_trabajador.html', {
        'profile': profile, 'resenas': resenas, 'galeria': galeria,
        'notif_count': notif_count(request),
    })

# ─── HU008 / HU010 – Crear / Actualizar perfil ───────────────────────────────
@login_required
def editar_perfil(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES, instance=profile)
        hab_form = HabilidadesUpdateForm(request.POST)
        if form.is_valid() and hab_form.is_valid():
            # Nombre y apellido
            request.user.first_name = request.POST.get('first_name', '')
            request.user.last_name = request.POST.get('last_name', '')
            request.user.save()
            pf = form.save(commit=False)
            if profile.rol == 'trabajador':
                pf.habilidades = list(hab_form.cleaned_data.get('habilidades', []))
            pf.save()
            messages.success(request, '¡Perfil actualizado exitosamente!')
            return redirect('perfil_trabajador' if profile.rol == 'trabajador' else 'perfil_contratista')
    else:
        form = PerfilForm(instance=profile,
                          initial={'first_name': request.user.first_name,
                                   'last_name': request.user.last_name})
        hab_form = HabilidadesUpdateForm(initial={'habilidades': profile.habilidades})
    return render(request, 'core/editar_perfil.html',
                  {'form': form, 'hab_form': hab_form,
                   'profile': profile, 'skills': SKILL_CHOICES})

# ─── HU015 – Notificaciones ──────────────────────────────────────────────────
@login_required
def notificaciones(request):
    notifs = Notificacion.objects.filter(usuario=request.user)
    Notificacion.objects.filter(usuario=request.user, leida=False).update(leida=True)
    return render(request, 'core/notificaciones.html',
                  {'notifs': notifs, 'notif_count': 0})

@login_required
def marcar_notif_leida(request, pk):
    n = get_object_or_404(Notificacion, pk=pk, usuario=request.user)
    n.leida = True; n.save()
    return JsonResponse({'ok': True})

# ─── Trabajos urgentes ────────────────────────────────────────────────────────
@login_required
def trabajos_urgentes(request):
    trabajos = Trabajo.objects.filter(activo=True, es_urgente=True)
    return render(request, 'core/trabajos_urgentes.html',
                  {'trabajos': trabajos, 'notif_count': notif_count(request)})

# ─── PANEL CONTRATISTA ────────────────────────────────────────────────────────
@login_required
def panel_contratista(request):
    if request.user.profile.rol != 'contratista':
        return redirect('home_trabajador')
    trabajos = Trabajo.objects.filter(contratista=request.user)
    stats = {
        'activas': trabajos.filter(activo=True).count(),
        'candidatos': Solicitud.objects.filter(trabajo__contratista=request.user).count(),
        'reputacion': Resena.objects.filter(destinatario=request.user)
                      .aggregate(avg=Avg('calificacion'))['avg'] or 0,
    }
    return render(request, 'core/panel_contratista.html', {
        'trabajos': trabajos, 'stats': stats,
        'notif_count': notif_count(request),
    })

@login_required
def publicar_trabajo(request):
    if request.user.profile.rol != 'contratista':
        return redirect('home')
    if request.method == 'POST':
        form = TrabajoForm(request.POST)
        if form.is_valid():
            trabajo = form.save(commit=False)
            trabajo.contratista = request.user
            trabajo.save()
            messages.success(request, '¡Trabajo publicado exitosamente!')
            return redirect('panel_contratista')
    else:
        form = TrabajoForm()
    return render(request, 'core/publicar_trabajo.html', {'form': form})

@login_required
def editar_trabajo(request, pk):
    trabajo = get_object_or_404(Trabajo, pk=pk, contratista=request.user)
    if request.method == 'POST':
        form = TrabajoForm(request.POST, instance=trabajo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Trabajo actualizado.')
            return redirect('panel_contratista')
    else:
        form = TrabajoForm(instance=trabajo)
    return render(request, 'core/publicar_trabajo.html', {'form': form, 'editar': True, 'trabajo': trabajo})

@login_required
def candidatos(request, trabajo_pk):
    trabajo = get_object_or_404(Trabajo, pk=trabajo_pk, contratista=request.user)
    solicitudes = Solicitud.objects.filter(trabajo=trabajo).select_related('trabajador__profile')
    return render(request, 'core/candidatos.html',
                  {'trabajo': trabajo, 'solicitudes': solicitudes})

@login_required
def cambiar_estado_solicitud(request, sol_pk, nuevo_estado):
    sol = get_object_or_404(Solicitud, pk=sol_pk, trabajo__contratista=request.user)
    estados_validos = [s[0] for s in Solicitud.STATUS_CHOICES]
    if nuevo_estado not in estados_validos:
        messages.error(request, 'Estado inválido.')
        return redirect('candidatos', trabajo_pk=sol.trabajo.pk)
    sol.estado = nuevo_estado
    sol.save()
    # HU020 – si se contrata, marcar vacante ocupada
    if nuevo_estado == 'contratado':
        Trabajo.objects.filter(pk=sol.trabajo.pk).update(estado_vacante='ocupada')
    # HU015 – notificar trabajador
    msgs_estado = {
        'aceptado': '¡Tu solicitud fue aceptada!',
        'rechazado': 'Tu solicitud no fue seleccionada en esta ocasión.',
        'contratado': '¡Felicidades! Fuiste contratado.',
        'en_revision': 'Tu solicitud está siendo revisada.',
    }
    crear_notificacion(sol.trabajador, 'estado',
        f'Estado actualizado: {sol.trabajo.titulo}',
        msgs_estado.get(nuevo_estado, 'Tu solicitud fue actualizada.'),
        '/solicitudes/')
    messages.success(request, f'Estado cambiado a {nuevo_estado}.')
    return redirect('candidatos', trabajo_pk=sol.trabajo.pk)

@login_required
def perfil_contratista(request):
    profile = request.user.profile
    trabajos_count = Trabajo.objects.filter(contratista=request.user).count()
    completados = Solicitud.objects.filter(trabajo__contratista=request.user, estado='contratado').count()
    return render(request, 'core/perfil_contratista.html', {
        'profile': profile, 'trabajos_count': trabajos_count, 'completados': completados,
        'notif_count': notif_count(request),
    })

# ─── Perfil público de un trabajador ─────────────────────────────────────────
@login_required
def perfil_publico(request, user_pk):
    usuario = get_object_or_404(User, pk=user_pk)
    profile = get_object_or_404(UserProfile, user=usuario)
    resenas = Resena.objects.filter(destinatario=usuario)
    galeria = GaleriaItem.objects.filter(trabajador=usuario)
    # Reseña de este contratista
    puedo_calificar = (request.user.profile.rol == 'contratista' and
        Solicitud.objects.filter(trabajo__contratista=request.user,
                                  trabajador=usuario, estado='contratado').exists())
    if request.method == 'POST' and puedo_calificar:
        form = ResenaForm(request.POST)
        if form.is_valid():
            r = form.save(commit=False)
            r.autor = request.user
            r.destinatario = usuario
            r.save()
            messages.success(request, 'Reseña enviada.')
            return redirect('perfil_publico', user_pk=user_pk)
    else:
        form = ResenaForm()
    return render(request, 'core/perfil_publico.html', {
        'perfil_user': usuario, 'profile': profile,
        'resenas': resenas, 'galeria': galeria,
        'puedo_calificar': puedo_calificar, 'form': form,
        'notif_count': notif_count(request),
    })

# ─── Asistente ────────────────────────────────────────────────────────────────
@login_required
def asistente(request):
    return render(request, 'core/asistente.html', {'notif_count': notif_count(request)})
