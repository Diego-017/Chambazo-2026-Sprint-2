from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('recuperar-password/', views.recuperar_password, name='recuperar_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    # Registro (HU001/HU005/HU006/HU007)
    path('registro/', views.registro_step1, name='registro_step1'),
    path('registro/paso2/', views.registro_step2, name='registro_step2'),
    path('registro/paso3/', views.registro_step3, name='registro_step3'),
    # Home
    path('', views.home, name='home'),
    path('inicio/', views.home_trabajador, name='home_trabajador'),
    # Trabajos (HU012-HU020)
    path('trabajo/<int:pk>/', views.trabajo_detalle, name='trabajo_detalle'),
    path('trabajo/<int:pk>/aplicar/', views.aplicar_trabajo, name='aplicar_trabajo'),
    path('trabajo/<int:pk>/aplicar-rapido/', views.aplicar_rapido, name='aplicar_rapido'),
    path('trabajos/urgentes/', views.trabajos_urgentes, name='trabajos_urgentes'),
    # Solicitudes (HU018/HU019)
    path('solicitudes/', views.mis_solicitudes, name='mis_solicitudes'),
    # Perfil (HU008/HU010/HU011)
    path('perfil/', views.perfil_trabajador, name='perfil_trabajador'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('perfil/<int:user_pk>/', views.perfil_publico, name='perfil_publico'),
    # Notificaciones (HU015)
    path('notificaciones/', views.notificaciones, name='notificaciones'),
    path('notificaciones/<int:pk>/leer/', views.marcar_notif_leida, name='marcar_notif_leida'),
    # Contratista
    path('contratista/', views.panel_contratista, name='panel_contratista'),
    path('contratista/publicar/', views.publicar_trabajo, name='publicar_trabajo'),
    path('contratista/trabajo/<int:pk>/editar/', views.editar_trabajo, name='editar_trabajo'),
    path('contratista/trabajo/<int:trabajo_pk>/candidatos/', views.candidatos, name='candidatos'),
    path('contratista/solicitud/<int:sol_pk>/estado/<str:nuevo_estado>/',
         views.cambiar_estado_solicitud, name='cambiar_estado_solicitud'),
    path('contratista/perfil/', views.perfil_contratista, name='perfil_contratista'),
    path('contratista/perfil/editar/', views.editar_perfil, name='editar_perfil_contratista'),
    # Asistente
    path('asistente/', views.asistente, name='asistente'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
