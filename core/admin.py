from django.contrib import admin
from .models import UserProfile, Trabajo, Solicitud, Resena, GaleriaItem, Notificacion, PasswordResetToken

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'rol', 'ubicacion', 'calificacion', 'verificado']
    list_filter = ['rol', 'verificado']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']

@admin.register(Trabajo)
class TrabajoAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'contratista', 'categoria', 'presupuesto', 'es_urgente', 'estado_vacante', 'activo', 'creado']
    list_filter = ['categoria', 'es_urgente', 'activo', 'estado_vacante']
    search_fields = ['titulo', 'descripcion']

@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = ['trabajador', 'trabajo', 'estado', 'rapida', 'creado']
    list_filter = ['estado', 'rapida']

@admin.register(Resena)
class ResenaAdmin(admin.ModelAdmin):
    list_display = ['autor', 'destinatario', 'calificacion', 'creado']

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'tipo', 'titulo', 'leida', 'creado']
    list_filter = ['tipo', 'leida']

admin.site.register(GaleriaItem)
admin.site.register(PasswordResetToken)
