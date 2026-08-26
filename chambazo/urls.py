from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from core import views, api_views

# Router de la API RESTful
router = DefaultRouter()
router.register(r'trabajos', api_views.TrabajoViewSet, basename='api_trabajo')
router.register(r'perfiles', api_views.UserProfileViewSet, basename='api_perfil')
router.register(r'solicitudes', api_views.SolicitudViewSet, basename='api_solicitud')
router.register(r'resenas', api_views.ResenaViewSet, basename='api_resena')
router.register(r'galeria', api_views.GaleriaItemViewSet, basename='api_galeria')

urlpatterns = [
    path('admin/', admin.site.urls),
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('recuperar-password/', views.recuperar_password, name='recuperar_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    # Registro
    path('registro/', views.registro_step1, name='registro_step1'),
    path('registro/paso2/', views.registro_step2, name='registro_step2'),
    path('registro/paso3/', views.registro_step3, name='registro_step3'),
    path('registro/verificar-email/', views.verificar_email, name='verificar_email'),
    # Home / trabajador
    path('', views.home, name='home'),
    path('inicio/', views.home_trabajador, name='home_trabajador'),
    path('trabajo/<int:pk>/', views.trabajo_detalle, name='trabajo_detalle'),
    path('trabajo/<int:pk>/aplicar/', views.aplicar_trabajo, name='aplicar_trabajo'),
    path('trabajo/<int:pk>/aplicar-rapido/', views.aplicar_rapido, name='aplicar_rapido'),
    path('solicitud/<int:pk>/pagar/', views.pagar_solicitud, name='pagar_solicitud'),
    # Escrow y Gestión del Trabajo Activo
    path('solicitud/<int:sol_pk>/escrow/', views.depositar_escrow, name='depositar_escrow'),
    path('solicitud/<int:sol_pk>/gestionar/', views.gestionar_trabajo, name='gestionar_trabajo'),
    path('solicitud/<int:sol_pk>/liberar-pago/', views.liberar_fondos_escrow, name='liberar_fondos_escrow'),
    path('escrow/<int:pk>/pdf/', views.descargar_comprobante_pdf, name='descargar_comprobante_pdf'),
    path('trabajo/<int:pk>/enviada/', views.solicitud_enviada, name='solicitud_enviada'),
    path('trabajo/<int:pk>/guardar/', views.toggle_guardado, name='toggle_guardado'),
    path('trabajos/urgentes/', views.trabajos_urgentes, name='trabajos_urgentes'),
    path('guardados/', views.guardados, name='guardados'),
    path('solicitudes/', views.mis_solicitudes, name='mis_solicitudes'),
    path('ganancias/', views.ganancias, name='ganancias'),
    path('logros/', views.logros, name='logros'),
    # Mensajes (compartido)
    path('mensajes/', views.mensajes, name='mensajes'),
    path('mensajes/<int:sol_pk>/', views.mensajes, name='mensajes_chat'),
    # Perfil trabajador
    path('perfil/', views.perfil_trabajador, name='perfil_trabajador'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('perfil/<int:user_pk>/', views.perfil_publico, name='perfil_publico'),
    path('perfil/disponibilidad/', views.toggle_disponibilidad, name='toggle_disponibilidad'),
    # Portafolio / Galería
    path('portafolio/', views.galeria_gestionar, name='galeria_gestionar'),
    path('portafolio/<int:pk>/eliminar/', views.galeria_eliminar, name='galeria_eliminar'),
    # Reseñas y Contratos
    path('resena/crear/<int:sol_pk>/', views.crear_resena_solicitud, name='crear_resena_solicitud'),
    path('contrato/<int:sol_pk>/', views.comprobante_contrato, name='comprobante_contrato'),
    # Notificaciones (compartido)
    path('notificaciones/', views.notificaciones, name='notificaciones'),
    path('notificaciones/<int:pk>/leer/', views.marcar_notif_leida, name='marcar_notif_leida'),
    # Contratista
    path('contratista/', views.panel_contratista, name='panel_contratista'),
    path('contratista/publicar/', views.publicar_trabajo, name='publicar_trabajo'),
    path('contratista/trabajo/<int:pk>/pagar/', views.pagar_trabajo, name='pagar_trabajo'),
    path('contratista/trabajo/<int:pk>/editar/', views.editar_trabajo, name='editar_trabajo'),
    path('contratista/trabajo/<int:pk>/candidatos/', views.candidatos, name='candidatos'),
    path('contratista/candidatos/', views.candidatos_general, name='candidatos_general'),
    path('contratista/solicitud/<int:sol_pk>/estado/<str:nuevo_estado>/',
         views.cambiar_estado_solicitud, name='cambiar_estado_solicitud'),
    path('contratista/buscar-trabajadores/', views.buscar_trabajadores, name='buscar_trabajadores'),
    path('contratista/invitar/<int:user_pk>/', views.invitar_trabajador, name='invitar_trabajador'),
    path('contratista/estadisticas/', views.estadisticas, name='estadisticas'),
    path('contratista/mi-empresa/', views.mi_empresa, name='mi_empresa'),
    path('contratista/perfil/', views.perfil_contratista, name='perfil_contratista'),
    # Legal
    path('terminos/', views.terminos_condiciones, name='terminos_condiciones'),
    path('privacidad/', views.politica_privacidad, name='politica_privacidad'),
    # Asistente
    path('asistente/', views.asistente, name='asistente'),
    path('asistente/responder/', views.asistente_responder, name='asistente_responder'),
    # API RESTful v1
    path('api/v1/', include(router.urls)),
    path('api/v1/stats/', api_views.PlataformaStatsAPIView.as_view(), name='api_stats'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'static')
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
