import random
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg
from django.conf import settings

SKILL_CHOICES = [
    ('electricidad', 'Electricidad'),
    ('plomeria', 'Plomería'),
    ('carpinteria', 'Carpintería'),
    ('pintura', 'Pintura'),
    ('limpieza', 'Limpieza'),
    ('jardineria', 'Jardinería'),
    ('reparaciones', 'Reparaciones'),
    ('instalaciones', 'Instalaciones'),
    ('albanileria', 'Albañilería'),
    ('soldadura', 'Soldadura'),
    ('mecanica', 'Mecánica'),
    ('informatica', 'Informática'),
    ('diseno', 'Diseño'),
    ('acabados', 'Acabados'),
    ('otro', 'Otro'),
]

CATEGORY_CHOICES = SKILL_CHOICES  # mismas categorías

ESTADO_VACANTE = [
    ('disponible', 'Disponible'),
    ('en_proceso', 'En proceso'),
    ('ocupada', 'Ocupada'),
]

SKILL_ICONS = {
    'electricidad': '⚡', 'plomeria': '🔧', 'carpinteria': '🪚',
    'pintura': '🎨', 'limpieza': '🧹', 'jardineria': '🌿',
    'reparaciones': '🔨', 'instalaciones': '🔩', 'albanileria': '🏗️',
    'soldadura': '🔥', 'mecanica': '🚗', 'informatica': '💻',
    'diseno': '✏️', 'acabados': '🏠', 'otro': '⭐',
}

SKILL_COLORS = {
    'electricidad': '#fef3c7', 'plomeria': '#dbeafe', 'carpinteria': '#fce7f3',
    'pintura': '#ede9fe', 'limpieza': '#d1fae5', 'jardineria': '#dcfce7',
    'reparaciones': '#fee2e2', 'instalaciones': '#e0f2fe', 'albanileria': '#fef9c3',
    'soldadura': '#ffedd5', 'mecanica': '#f3f4f6', 'informatica': '#eff6ff',
    'diseno': '#fdf4ff', 'acabados': '#f0fdf4', 'otro': '#f8fafc',
}


def random_sv_location():
    """Devuelve una ubicación aleatoria de El Salvador"""
    locs = getattr(settings, 'SV_LOCATIONS', [])
    if locs:
        return random.choice(locs)
    return {"nombre": "San Salvador", "lat": 13.6929, "lng": -89.2182}


# ── UserProfile ────────────────────────────────────────────────────────────────
class UserProfile(models.Model):
    ROL_CHOICES = [('trabajador', 'Trabajador'), ('contratista', 'Contratista')]
    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    rol         = models.CharField(max_length=20, choices=ROL_CHOICES)
    telefono    = models.CharField(max_length=20, blank=True)
    ubicacion   = models.CharField(max_length=100, blank=True)
    lat         = models.FloatField(null=True, blank=True)
    lng         = models.FloatField(null=True, blank=True)
    descripcion = models.TextField(blank=True)
    habilidades = models.JSONField(default=list, blank=True)
    empresa     = models.CharField(max_length=100, blank=True)
    foto        = models.ImageField(upload_to='fotos/', null=True, blank=True)
    verificado  = models.BooleanField(default=False)
    calificacion= models.FloatField(default=0.0)
    total_trabajos = models.IntegerField(default=0)
    notif_email = models.BooleanField(default=True)
    notif_sistema = models.BooleanField(default=True)
    # Sprint 2
    disponible  = models.BooleanField(default=True)   # activo para contratar
    tarifa_hora = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    experiencia_anos = models.PositiveIntegerField(default=0)
    portfolio_url = models.URLField(blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.rol})"

    @property
    def nombre_display(self):
        if self.rol == 'contratista' and self.empresa:
            return self.empresa
        return self.user.get_full_name() or self.user.username

    @property
    def completitud_perfil(self):
        """Porcentaje de completitud del perfil"""
        campos = [
            bool(self.user.get_full_name()),
            bool(self.telefono),
            bool(self.ubicacion),
            bool(self.descripcion),
            bool(self.foto),
            bool(self.habilidades),
        ]
        return int(sum(campos) / len(campos) * 100)

    @property
    def estrellas(self):
        """Devuelve string de estrellas llenas/vacías"""
        cal = round(self.calificacion)
        return '★' * cal + '☆' * (5 - cal)

    def match_score(self, trabajo):
        """% de compatibilidad con un trabajo (0-100)"""
        if not self.habilidades or not trabajo.habilidades_req:
            return 0
        mias = set(self.habilidades)
        req  = set(trabajo.habilidades_req)
        if not req:
            return 0
        return int(len(mias & req) / len(req) * 100)

    def actualizar_calificacion(self):
        avg = Resena.objects.filter(destinatario=self.user).aggregate(a=Avg('calificacion'))['a']
        if avg:
            self.calificacion = round(avg, 1)
            self.total_trabajos = Solicitud.objects.filter(
                trabajador=self.user, estado='contratado').count()
            self.save(update_fields=['calificacion', 'total_trabajos'])


# ── Trabajo ────────────────────────────────────────────────────────────────────
class Trabajo(models.Model):
    ESTADO_VACANTE = [
        ('disponible', 'Disponible'),
        ('en_proceso', 'En proceso'),
        ('ocupada', 'Ocupada'),
    ]
    contratista   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trabajos_publicados')
    titulo        = models.CharField(max_length=200)
    categoria     = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    descripcion   = models.TextField()
    requisitos    = models.TextField(blank=True)
    beneficios    = models.TextField(blank=True)
    ubicacion     = models.CharField(max_length=200)
    lat           = models.FloatField(null=True, blank=True)
    lng           = models.FloatField(null=True, blank=True)
    presupuesto   = models.DecimalField(max_digits=10, decimal_places=2)
    es_urgente    = models.BooleanField(default=False)
    estado_vacante= models.CharField(max_length=20, choices=ESTADO_VACANTE, default='disponible')
    activo        = models.BooleanField(default=True)
    creado        = models.DateTimeField(auto_now_add=True)
    actualizado   = models.DateTimeField(auto_now=True)
    habilidades_req = models.JSONField(default=list, blank=True)
    vistas        = models.PositiveIntegerField(default=0)
    # Sprint 2
    modalidad     = models.CharField(max_length=20, choices=[
        ('presencial','Presencial'), ('remoto','Remoto'), ('hibrido','Híbrido')
    ], default='presencial')
    duracion      = models.CharField(max_length=100, blank=True,
                                     help_text='Ej: 3 días, 1 semana')
    verificacion_requerida = models.BooleanField(default=False)
    pagado        = models.BooleanField(default=False)
    fecha_pago    = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-creado']

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        # Si no tiene coordenadas, asignar una ubicación aleatoria de El Salvador
        if not self.lat or not self.lng:
            loc = random_sv_location()
            if not self.lat:
                self.lat = loc['lat'] + random.uniform(-0.05, 0.05)
            if not self.lng:
                self.lng = loc['lng'] + random.uniform(-0.05, 0.05)
            if not self.ubicacion:
                self.ubicacion = loc['nombre']
        super().save(*args, **kwargs)

    @property
    def tiempo_relativo(self):
        from django.utils import timezone
        diff = timezone.now() - self.creado
        if diff.days > 0:
            return f"Hace {diff.days} día{'s' if diff.days > 1 else ''}"
        hours = diff.seconds // 3600
        if hours > 0:
            return f"Hace {hours} hora{'s' if hours > 1 else ''}"
        mins = diff.seconds // 60
        return f"Hace {mins} minutos"

    @property
    def candidatos_count(self):
        return self.solicitudes.count()

    @property
    def icono_categoria(self):
        return SKILL_ICONS.get(self.categoria, '⭐')

    @property
    def color_categoria(self):
        return SKILL_COLORS.get(self.categoria, '#f8fafc')

    def get_estado_badge(self):
        colores = {'disponible': 'success', 'en_proceso': 'warning', 'ocupada': 'danger'}
        return colores.get(self.estado_vacante, 'secondary')


# ── Solicitud ──────────────────────────────────────────────────────────────────
class Solicitud(models.Model):
    STATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_revision', 'En revisión'),
        ('aceptado', 'Aceptado'),
        ('rechazado', 'Rechazado'),
        ('contratado', 'Contratado'),
        ('en_progreso', 'En progreso'),
        ('completado', 'Completado'),
    ]
    trabajo   = models.ForeignKey(Trabajo, on_delete=models.CASCADE, related_name='solicitudes')
    trabajador= models.ForeignKey(User, on_delete=models.CASCADE, related_name='solicitudes')
    estado    = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendiente')
    mensaje   = models.TextField(blank=True)
    rapida    = models.BooleanField(default=False)
    tarifa_propuesta = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    creado    = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('trabajo', 'trabajador')
        ordering = ['-creado']

    def __str__(self):
        return f"{self.trabajador} → {self.trabajo}"

    def get_estado_color(self):
        colores = {
            'pendiente': 'warning', 'en_revision': 'info',
            'aceptado': 'success', 'rechazado': 'danger',
            'contratado': 'success', 'en_progreso': 'primary',
            'completado': 'info'
        }
        return colores.get(self.estado, 'secondary')

    @property
    def estado_label(self):
        return dict(self.STATUS_CHOICES).get(self.estado, self.estado)

    @property
    def estado_icon(self):
        icons = {
            'pendiente': '⏳', 'en_revision': '🔍',
            'aceptado': '✅', 'rechazado': '❌',
            'contratado': '🏆', 'en_progreso': '⚡',
            'completado': '✨'
        }
        return icons.get(self.estado, '📋')


# ── Resena ─────────────────────────────────────────────────────────────────────
class Resena(models.Model):
    trabajo     = models.ForeignKey(Trabajo, on_delete=models.CASCADE, related_name='resenas', null=True, blank=True)
    solicitud   = models.ForeignKey(Solicitud, on_delete=models.SET_NULL, null=True, blank=True, related_name='resenas')
    autor       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resenas_dadas')
    destinatario= models.ForeignKey(User, on_delete=models.CASCADE, related_name='resenas_recibidas')
    calificacion= models.IntegerField(default=5)
    comentario  = models.TextField()
    etiquetas   = models.CharField(max_length=255, blank=True, help_text="Etiquetas separadas por comas")
    creado      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado']

    def __str__(self):
        return f"Reseña de {self.autor} para {self.destinatario} ({self.calificacion}★)"

    @property
    def estrellas(self):
        return '★' * self.calificacion + '☆' * (5 - self.calificacion)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        try:
            self.destinatario.profile.actualizar_calificacion()
        except Exception:
            pass


# ── GaleriaItem ────────────────────────────────────────────────────────────────
class GaleriaItem(models.Model):
    trabajador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='galeria')
    titulo     = models.CharField(max_length=100)
    descripcion= models.TextField(blank=True)
    categoria  = models.CharField(max_length=50, blank=True)
    imagen     = models.ImageField(upload_to='galeria/', null=True, blank=True)
    creado     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado']


# ── Notificacion ───────────────────────────────────────────────────────────────
class Notificacion(models.Model):
    TIPO_CHOICES = [
        ('solicitud', 'Nueva solicitud'),
        ('estado', 'Cambio de estado'),
        ('contratado', 'Contratado'),
        ('resena', 'Nueva reseña'),
        ('sistema', 'Sistema'),
        ('match', 'Nuevo match'),
    ]
    TIPO_ICONS = {
        'solicitud': '📩', 'estado': '🔄', 'contratado': '🏆',
        'resena': '⭐', 'sistema': '🔔', 'match': '🎯',
    }
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones')
    tipo    = models.CharField(max_length=20, choices=TIPO_CHOICES, default='sistema')
    titulo  = models.CharField(max_length=200)
    mensaje = models.TextField()
    leida   = models.BooleanField(default=False)
    url     = models.CharField(max_length=300, blank=True)
    creado  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado']

    def __str__(self):
        return f"[{self.tipo}] {self.titulo} → {self.usuario}"

    @property
    def icono(self):
        return self.TIPO_ICONS.get(self.tipo, '🔔')


# ── Mensaje (Chat básico Sprint 2) ─────────────────────────────────────────────
class Mensaje(models.Model):
    solicitud = models.ForeignKey(Solicitud, on_delete=models.CASCADE, related_name='mensajes')
    autor     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mensajes_enviados')
    texto     = models.TextField()
    leido     = models.BooleanField(default=False)
    creado    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['creado']

    def __str__(self):
        return f"{self.autor} → {self.solicitud} : {self.texto[:40]}"


# ── PasswordResetToken ─────────────────────────────────────────────────────────
class PasswordResetToken(models.Model):
    user   = models.ForeignKey(User, on_delete=models.CASCADE)
    token  = models.CharField(max_length=100, unique=True)
    creado = models.DateTimeField(auto_now_add=True)
    usado  = models.BooleanField(default=False)

    def is_valid(self):
        from django.utils import timezone
        from datetime import timedelta
        return not self.usado and (timezone.now() - self.creado) < timedelta(hours=2)


# ── TrabajoGuardado (Guardados) ─────────────────────────────────────────────────
class TrabajoGuardado(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='guardados')
    trabajo = models.ForeignKey(Trabajo, on_delete=models.CASCADE, related_name='guardado_por')
    creado  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'trabajo')
        ordering = ['-creado']


# ── Logros (gamificación) ───────────────────────────────────────────────────────
class Logro(models.Model):
    codigo      = models.CharField(max_length=40, unique=True)
    nombre      = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=200)
    icono       = models.CharField(max_length=10, default='🏆')
    puntos      = models.PositiveIntegerField(default=100)
    meta        = models.PositiveIntegerField(default=1, help_text='Cantidad requerida para desbloquear')
    orden       = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden']

    def __str__(self):
        return self.nombre


class LogroObtenido(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='logros_obtenidos')
    logro   = models.ForeignKey(Logro, on_delete=models.CASCADE)
    creado  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'logro')


# ── Aceptación de Términos y Condiciones ────────────────────────────────────────
class AceptacionTerminos(models.Model):
    usuario  = models.OneToOneField(User, on_delete=models.CASCADE, related_name='aceptacion_terminos')
    version  = models.CharField(max_length=20, default='2026.1')
    aceptado = models.BooleanField(default=False)
    fecha    = models.DateTimeField(auto_now=True)
