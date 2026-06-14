from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg

SKILL_CHOICES = [
    ('electricidad', 'Electricidad'),
    ('plomeria', 'Plomería'),
    ('carpinteria', 'Carpintería'),
    ('pintura', 'Pintura'),
    ('limpieza', 'Limpieza'),
    ('jardineria', 'Jardinería'),
    ('reparaciones', 'Reparaciones'),
    ('instalaciones', 'Instalaciones'),
    ('diseno', 'Diseño'),
    ('acabados', 'Acabados'),
    ('albanileria', 'Albañilería'),
    ('soldadura', 'Soldadura'),
    ('mecanica', 'Mecánica'),
    ('informatica', 'Informática'),
    ('otro', 'Otro'),
]

CATEGORY_CHOICES = [
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
    ('otro', 'Otro'),
]

ESTADO_VACANTE = [
    ('disponible', 'Disponible'),
    ('en_proceso', 'En proceso'),
    ('ocupada', 'Ocupada'),
]

# HU005 / HU006 / HU007 – Registro por rol + Selección de rol
class UserProfile(models.Model):
    ROL_CHOICES = [('trabajador', 'Trabajador'), ('contratista', 'Contratista')]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    rol = models.CharField(max_length=20, choices=ROL_CHOICES)
    telefono = models.CharField(max_length=20, blank=True)
    ubicacion = models.CharField(max_length=100, blank=True)
    lat = models.FloatField(null=True, blank=True)   # HU006 – geolocalización
    lng = models.FloatField(null=True, blank=True)
    descripcion = models.TextField(blank=True)       # HU008 – perfil profesional
    habilidades = models.JSONField(default=list, blank=True)  # HU009 – habilidades
    empresa = models.CharField(max_length=100, blank=True)
    foto = models.ImageField(upload_to='fotos/', null=True, blank=True)  # HU008
    verificado = models.BooleanField(default=False)  # HU007 – usuarios verificados
    calificacion = models.FloatField(default=0.0)
    total_trabajos = models.IntegerField(default=0)
    # HU015 – notificaciones
    notif_email = models.BooleanField(default=True)
    notif_sistema = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.rol})"

    @property
    def nombre_display(self):
        if self.rol == 'contratista' and self.empresa:
            return self.empresa
        return self.user.get_full_name() or self.user.username

    def actualizar_calificacion(self):
        avg = Resena.objects.filter(destinatario=self.user).aggregate(a=Avg('calificacion'))['a']
        if avg:
            self.calificacion = round(avg, 1)
            self.total_trabajos = Solicitud.objects.filter(
                trabajador=self.user, estado='contratado').count()
            self.save(update_fields=['calificacion', 'total_trabajos'])


# HU012 / HU013 / HU014 / HU015 / HU020 – Búsqueda, filtro, detalle, estado
class Trabajo(models.Model):
    ESTADO_VACANTE = [
        ('disponible', 'Disponible'),
        ('en_proceso', 'En proceso'),
        ('ocupada', 'Ocupada'),
    ]
    contratista = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trabajos_publicados')
    titulo = models.CharField(max_length=200)
    categoria = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    descripcion = models.TextField()
    requisitos = models.TextField(blank=True)        # HU014 – detalles completos
    beneficios = models.TextField(blank=True)        # HU014
    ubicacion = models.CharField(max_length=200)
    lat = models.FloatField(null=True, blank=True)   # HU013 – filtro por zona
    lng = models.FloatField(null=True, blank=True)
    presupuesto = models.DecimalField(max_digits=10, decimal_places=2)
    es_urgente = models.BooleanField(default=False)
    estado_vacante = models.CharField(max_length=20, choices=ESTADO_VACANTE, default='disponible')  # HU020
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    habilidades_req = models.JSONField(default=list, blank=True)  # HU014
    vistas = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-creado']

    def __str__(self):
        return self.titulo

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

    def get_estado_badge(self):
        colores = {'disponible': 'success', 'en_proceso': 'warning', 'ocupada': 'danger'}
        return colores.get(self.estado_vacante, 'secondary')


# HU016 / HU017 / HU018 / HU019 – Aplicar, rápida, confirmar, historial
class Solicitud(models.Model):
    STATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_revision', 'En revisión'),
        ('aceptado', 'Aceptado'),
        ('rechazado', 'Rechazado'),
        ('contratado', 'Contratado'),
    ]
    trabajo = models.ForeignKey(Trabajo, on_delete=models.CASCADE, related_name='solicitudes')
    trabajador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='solicitudes')
    estado = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendiente')
    mensaje = models.TextField(blank=True)   # HU016 – mensaje personalizado
    rapida = models.BooleanField(default=False)  # HU017 – aplicación rápida
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('trabajo', 'trabajador')
        ordering = ['-creado']

    def __str__(self):
        return f"{self.trabajador} → {self.trabajo}"

    def get_estado_color(self):
        colores = {
            'pendiente': 'warning', 'en_revision': 'info',
            'aceptado': 'success', 'rechazado': 'danger', 'contratado': 'success'
        }
        return colores.get(self.estado, 'secondary')


# HU007 – Usuarios verificados / calificaciones
class Resena(models.Model):
    trabajo = models.ForeignKey(Trabajo, on_delete=models.CASCADE, related_name='resenas', null=True, blank=True)
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resenas_dadas')
    destinatario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resenas_recibidas')
    calificacion = models.IntegerField(default=5)
    comentario = models.TextField()
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado']

    def __str__(self):
        return f"Reseña de {self.autor} para {self.destinatario}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        try:
            self.destinatario.profile.actualizar_calificacion()
        except Exception:
            pass


# HU008 – Galería de trabajos en perfil
class GaleriaItem(models.Model):
    trabajador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='galeria')
    titulo = models.CharField(max_length=100)
    categoria = models.CharField(max_length=50, blank=True)
    imagen = models.ImageField(upload_to='galeria/', null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado']


# HU015 – Notificaciones del sistema
class Notificacion(models.Model):
    TIPO_CHOICES = [
        ('solicitud', 'Nueva solicitud'),
        ('estado', 'Cambio de estado'),
        ('contratado', 'Contratado'),
        ('resena', 'Nueva reseña'),
        ('sistema', 'Sistema'),
    ]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='sistema')
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    url = models.CharField(max_length=300, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado']

    def __str__(self):
        return f"[{self.tipo}] {self.titulo} → {self.usuario}"


# HU003 – Recuperar contraseña (token)
class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    creado = models.DateTimeField(auto_now_add=True)
    usado = models.BooleanField(default=False)

    def is_valid(self):
        from django.utils import timezone
        from datetime import timedelta
        return not self.usado and (timezone.now() - self.creado) < timedelta(hours=2)
