from django.core.management.base import BaseCommand
from core.models import PreguntaFrecuente

class Command(BaseCommand):
    help = 'Puebla preguntas frecuentes iniciales para el Centro de Ayuda (Sprint 4)'

    def handle(self, *args, **options):
        faqs = [
            # Seguridad y 2FA
            {
                "categoria": "seguridad",
                "pregunta": "¿Cómo activo la autenticación de dos factores (2FA)?",
                "respuesta": "Para activar 2FA, dirígete a tu Perfil > Ajustes de Seguridad y activa la opción 'Autenticación de dos factores'. Recibirás un código de 6 dígitos en tu correo para verificar y confirmar el dispositivo.",
                "orden": 1,
                "votos_util": 18,
            },
            {
                "categoria": "seguridad",
                "pregunta": "¿Qué pasa si cierro sesión en un dispositivo público?",
                "respuesta": "El cierre de sesión de Chambazo SV destruye automáticamente tu token de acceso e invalida la sesión activa, impidiendo que terceros puedan navegar hacia atrás en el historial del navegador.",
                "orden": 2,
                "votos_util": 12,
            },
            {
                "categoria": "seguridad",
                "pregunta": "¿Por qué mi ubicación exacta no es visible para todos?",
                "respuesta": "Por tu seguridad y privacidad (HU057), solo mostramos tu zona o departamento aproximado. Tu dirección exacta solo se desbloquea para la contraparte una vez que la contratación ha sido formalmente aceptada.",
                "orden": 3,
                "votos_util": 25,
            },
            # Empleos y Postulaciones
            {
                "categoria": "empleos",
                "pregunta": "¿Cómo postularme a una oferta de empleo?",
                "respuesta": "Navega al catálogo de ofertas, selecciona la vacante de tu interés y haz clic en 'Aplicar' o 'Aplicación rápida'. Puedes adjuntar tu propuesta económica y mensaje para el contratista.",
                "orden": 1,
                "votos_util": 34,
            },
            {
                "categoria": "empleos",
                "pregunta": "¿Cómo responder a una reseña que recibí?",
                "respuesta": "Como receptor de una reseña (trabajador o empleador), verás un botón 'Responder' bajo la reseña en tu perfil. Puedes escribir una réplica pública de hasta 500 caracteres para aclarar o agradecer.",
                "orden": 2,
                "votos_util": 15,
            },
            # Cuenta y Perfil
            {
                "categoria": "cuenta",
                "pregunta": "¿Cómo obtener la insignia de usuario verificado?",
                "respuesta": "Ingresa a tu perfil y sube tu Documento Único de Identidad (DUI) en el apartado de Verificación de Identidad (KYC). Nuestro equipo administrativo revisará tu documento y te otorgará la insignia azul.",
                "orden": 1,
                "votos_util": 41,
            },
            {
                "categoria": "cuenta",
                "pregunta": "¿Cómo solicitar la eliminación definitiva de mi cuenta?",
                "respuesta": "En Ajustes de Privacidad, puedes solicitar la eliminación de cuenta reingresando tu contraseña. Contarás con un periodo de gracia de 30 días antes del borrado permanente por si deseas cancelar la baja.",
                "orden": 2,
                "votos_util": 9,
            },
            # Pagos
            {
                "categoria": "pagos",
                "pregunta": "¿Qué comisiones o tarifas aplican para ofertas urgentes?",
                "respuesta": "Las publicaciones urgentes tienen una tarifa preferencial que destaca la oferta en los primeros puestos y envía notificaciones push inmediatas a los trabajadores de la zona.",
                "orden": 1,
                "votos_util": 20,
            },
            # Soporte
            {
                "categoria": "soporte",
                "pregunta": "¿Cómo contacto al equipo de soporte de Chambazo?",
                "respuesta": "Puedes enviar un mensaje a través de nuestro formulario en /ayuda/soporte/ o escribirnos directamente. Nuestro tiempo de respuesta promedio es menor a 24 horas hábiles.",
                "orden": 1,
                "votos_util": 28,
            },
        ]

        creados = 0
        for data in faqs:
            faq, created = PreguntaFrecuente.objects.get_or_create(
                pregunta=data["pregunta"],
                defaults=data
            )
            if created:
                creados += 1

        self.stdout.write(self.style.SUCCESS(f"Se crearon {creados} preguntas frecuentes para el Sprint 4."))
