from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from core.models import (
    UserProfile, Trabajo, Solicitud, Resena, GaleriaItem, Mensaje, Logro, LogroObtenido, TrabajoGuardado
)


class ChambazoCoreTests(TestCase):
    def setUp(self):
        # Crear usuario Contratista
        self.contratista_user = User.objects.create_user(
            username='constructora_demo',
            email='demo@constructora.com',
            password='password123',
            first_name='Constructora',
            last_name='Nacional'
        )
        self.contratista_profile = UserProfile.objects.create(
            user=self.contratista_user,
            rol='contratista',
            empresa='Constructora Nacional S.A.',
            ubicacion='San Salvador',
            nit_nrc='0614-010190-001-1',
            giro_comercial='Construcción y Acabados'
        )

        # Crear usuario Trabajador
        self.trabajador_user = User.objects.create_user(
            username='carlos_electricista',
            email='carlos@electricidad.sv',
            password='password123',
            first_name='Carlos',
            last_name='Gómez'
        )
        self.trabajador_profile = UserProfile.objects.create(
            user=self.trabajador_user,
            rol='trabajador',
            telefono='+503 7777-8888',
            ubicacion='Santa Tecla',
            descripcion='Electricista con 8 años de experiencia en residencias.',
            habilidades=['electricidad', 'instalaciones'],
            dui='01234567-8',
            vehiculo='moto'
        )

        # Crear trabajo
        self.trabajo = Trabajo.objects.create(
            contratista=self.contratista_user,
            titulo='Instalación de acometida eléctrica',
            categoria='electricidad',
            descripcion='Instalación de acometida trifásica en casa de campo.',
            ubicacion='Santa Tecla',
            lat=13.6740,
            lng=-89.2797,
            presupuesto=180.00,
            habilidades_req=['electricidad'],
            nivel_experiencia='experto',
            vacantes_disponibles=2
        )

    def test_user_profile_properties(self):
        """Valida propiedades calculadas del perfil y campos extendidos."""
        self.assertEqual(self.contratista_profile.nombre_display, 'Constructora Nacional S.A.')
        self.assertEqual(self.trabajador_profile.nombre_display, 'Carlos Gómez')
        self.assertEqual(self.trabajador_profile.dui, '01234567-8')
        self.assertEqual(self.trabajador_profile.vehiculo, 'moto')
        self.assertGreater(self.trabajador_profile.completitud_perfil, 50)

    def test_match_score(self):
        """Valida que el match score coincida con las habilidades requeridas."""
        score = self.trabajador_profile.match_score(self.trabajo)
        self.assertEqual(score, 100)

    def test_solicitud_lifecycle(self):
        """Valida el ciclo de vida completo de una solicitud."""
        # 1. Postulación
        solicitud = Solicitud.objects.create(
            trabajo=self.trabajo,
            trabajador=self.trabajador_user,
            mensaje='Cuento con herramientas y transporte inmediato.',
            tarifa_propuesta=175.00
        )
        self.assertEqual(solicitud.estado, 'pendiente')

        # 2. Contratación
        solicitud.estado = 'contratado'
        solicitud.save()
        self.assertEqual(solicitud.estado_label, 'Contratado')

        # 3. En progreso
        solicitud.estado = 'en_progreso'
        solicitud.save()
        self.assertEqual(solicitud.estado_label, 'En progreso')

        # 4. Completado
        solicitud.estado = 'completado'
        solicitud.save()
        self.assertEqual(solicitud.estado_label, 'Completado')

    def test_calcular_tarifas_normal_y_urgente(self):
        """Valida el cálculo de comisiones base y recargo por urgencia."""
        # Trabajo normal ($100 -> comisión 2.50)
        t_normal = Trabajo.objects.create(
            contratista=self.contratista_user,
            titulo='Pintura de sala',
            categoria='pintura',
            descripcion='Pintura interior',
            ubicacion='San Salvador',
            presupuesto=100.00,
            es_urgente=False
        )
        t_normal.calcular_tarifas()
        self.assertEqual(t_normal.comision_plataforma, Decimal('2.50'))
        self.assertEqual(t_normal.tarifa_urgencia, Decimal('0.00'))
        self.assertEqual(t_normal.total_a_pagar, Decimal('2.50'))

        # Trabajo urgente ($100 -> comisión 2.50 + urgencia 3.00 = 5.50)
        t_urgente = Trabajo.objects.create(
            contratista=self.contratista_user,
            titulo='Reparación urgente de fuga',
            categoria='plomeria',
            descripcion='Fuga inundando cocina',
            ubicacion='San Salvador',
            presupuesto=100.00,
            es_urgente=True
        )
        t_urgente.calcular_tarifas()
        self.assertEqual(t_urgente.tarifa_urgencia, Decimal('3.00'))
        self.assertEqual(t_urgente.total_a_pagar, Decimal('5.50'))

    def test_mensaje_multimedia_y_checks_whatsapp(self):
        """Valida la creación de mensajes con geolocalización y checks estilo WhatsApp."""
        solicitud = Solicitud.objects.create(
            trabajo=self.trabajo,
            trabajador=self.trabajador_user,
            estado='en_progreso'
        )
        msg = Mensaje.objects.create(
            solicitud=solicitud,
            autor=self.trabajador_user,
            texto='Ya voy en camino al lugar del trabajo.',
            lat=13.6751,
            lng=-89.2491,
            ubicacion_nombre='Redondel Masferrer, San Salvador',
            estado_entrega='entregado'
        )
        self.assertEqual(msg.check_icon['symbol'], '✓✓')
        self.assertEqual(msg.check_icon['title'], 'Entregado')

        # Al leerse cambia a leido (azul)
        msg.estado_entrega = 'leido'
        msg.leido = True
        msg.save()
        self.assertEqual(msg.check_icon['symbol'], '✓✓')
        self.assertEqual(msg.check_icon['color'], '#38bdf8')

    def test_resena_y_reputacion(self):
        """Valida que al crear una reseña se actualice la calificación promedio."""
        solicitud = Solicitud.objects.create(
            trabajo=self.trabajo,
            trabajador=self.trabajador_user,
            estado='completado'
        )

        # Calificación 5 estrellas del contratista al trabajador
        resena = Resena.objects.create(
            trabajo=self.trabajo,
            solicitud=solicitud,
            autor=self.contratista_user,
            destinatario=self.trabajador_user,
            calificacion=5,
            comentario='Excelente trabajo, muy profesional y ordenado.',
            etiquetas='Puntualidad, Calidad de trabajo'
        )

        self.trabajador_profile.refresh_from_db()
        self.assertEqual(self.trabajador_profile.calificacion, 5.0)
        self.assertEqual(resena.estrellas, '★★★★★')

    def test_galeria_portafolio(self):
        """Valida la creación de ítems de portafolio para el trabajador."""
        item = GaleriaItem.objects.create(
            usuario=self.trabajador_user,
            titulo='Panel de distribución 220V',
            categoria='electricidad',
            descripcion='Instalación limpia de breakers industriales.'
        )
        self.assertEqual(item.usuario, self.trabajador_user)
        self.assertEqual(self.trabajador_user.galeria.count(), 1)


class ChambazoAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='api_user',
            email='api@chambazo.com',
            password='password123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            rol='trabajador',
            ubicacion='San Salvador'
        )
        self.trabajo = Trabajo.objects.create(
            contratista=self.user,
            titulo='Reparación de tubería',
            categoria='plomeria',
            descripcion='Fuga en baño principal.',
            ubicacion='San Salvador',
            presupuesto=60.00
        )

    def test_api_listar_trabajos(self):
        """Valida el endpoint público de listado de trabajos /api/v1/trabajos/."""
        response = self.client.get('/api/v1/trabajos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_api_listar_perfiles(self):
        """Valida el endpoint público de directorio de perfiles /api/v1/perfiles/."""
        response = self.client.get('/api/v1/perfiles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_api_plataforma_stats(self):
        """Valida el endpoint de estadísticas globales /api/v1/stats/."""
        response = self.client.get('/api/v1/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_ofertas', response.data)
        self.assertIn('promedio_calificacion', response.data)


class ChambazoSprint3Tests(TestCase):
    """
    Casos de prueba automatizados correspondientes al Sprint 3 (HU032 - HU048),
    según lo documentado en la Semana 11 y Semana 12.
    """
    def setUp(self):
        self.contratista = User.objects.create_user(
            username='empleador3',
            email='empleador3@chambazo.com',
            password='password123',
            first_name='Empleador',
            last_name='Sprint3'
        )
        self.contratista_profile = UserProfile.objects.create(
            user=self.contratista,
            rol='contratista',
            empresa='Empresa Demo S.A. de C.V.',
            verificado=True
        )

        self.trabajador = User.objects.create_user(
            username='trabajador_demo3',
            email='trabajador_demo3@chambazo.com',
            password='password123',
            first_name='Trabajador',
            last_name='Sprint3'
        )
        self.trabajador_profile = UserProfile.objects.create(
            user=self.trabajador,
            rol='trabajador',
            telefono='+503 7000-0000',
            ubicacion='San Salvador',
            dui='04859603-9'
        )

        self.trabajo = Trabajo.objects.create(
            contratista=self.contratista,
            titulo='Auxiliar de bodega VAC-2026-050',
            categoria='general',
            descripcion='Carga y descarga de inventario.',
            ubicacion='San Salvador',
            presupuesto=150.00,
            activo=True
        )

        self.solicitud = Solicitud.objects.create(
            trabajo=self.trabajo,
            trabajador=self.trabajador,
            estado='pendiente',
            mensaje='Disponible inmediatamente con experiencia previa.'
        )

    def test_h01_tc_xss3_001_escape_html_en_vacantes(self):
        """TC-XSS3-001 (RNF-02): El contenido HTML/JS se muestra sanitizado/escapado como texto."""
        payload = "<script>alert('xss')</script>"
        trabajo_xss = Trabajo.objects.create(
            contratista=self.contratista,
            titulo=payload,
            categoria='general',
            descripcion='Test payload: ' + payload,
            ubicacion='San Salvador',
            presupuesto=50.00
        )
        self.client.login(username='trabajador_demo3', password='password123')
        response = self.client.get(reverse('trabajo_detalle', args=[trabajo_xss.pk]))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        # Se asegura que la carga maliciosa no se ejecute ni aparezca cruda
        self.assertNotIn("<script>alert('xss')</script>", content)
        self.assertIn("&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;", content)

    def test_def001_rnf01_seleccion_no_se_bloquea_por_smtp_lento(self):
        """DEF-001 / RNF-01: La respuesta responde en < 2.0s gracias al envío asíncrono en segundo plano."""
        import time
        from unittest.mock import patch

        def _smtp_simulado_lento(*args, **kwargs):
            time.sleep(3) # Simula latencia de 3 segundos en el servidor SMTP

        self.client.login(username='empleador3', password='password123')
        with patch("django.core.mail.EmailMultiAlternatives.send", side_effect=_smtp_simulado_lento):
            inicio = time.perf_counter()
            response = self.client.get(
                reverse('cambiar_estado_solicitud', args=[self.solicitud.pk, 'aceptado'])
            )
            duracion = time.perf_counter() - inicio

            # Debe redirigir y responder casi de inmediato (< 2.0s)
            self.assertEqual(response.status_code, 302)
            self.assertLess(duracion, 2.0, f"DEF-001 no resuelto: tardó {duracion:.2f}s")
            
            self.solicitud.refresh_from_db()
            self.assertEqual(self.solicitud.estado, 'aceptado')

    def test_tc_descand3_001_descartar_candidato_con_motivo(self):
        """HU034 / TC-DESCAND3-001: Descartar candidato registrando motivo."""
        self.client.login(username='empleador3', password='password123')
        response = self.client.post(
            reverse('descartar_candidato', args=[self.solicitud.pk]),
            {'motivo': 'Perfil no cumple con la experiencia requerida'}
        )
        self.assertEqual(response.status_code, 302)
        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, 'rechazado')
        self.assertEqual(self.solicitud.motivo_descarte, 'Perfil no cumple con la experiencia requerida')

    def test_tc_guardarof3_001_guardar_favoritos(self):
        """HU042 / TC-GUARDAROF3-001: Guardar y retirar vacante de guardados/favoritos."""
        self.client.login(username='trabajador_demo3', password='password123')
        # Guardar
        res1 = self.client.post(reverse('toggle_guardado', args=[self.trabajo.pk]))
        self.assertEqual(res1.status_code, 302)
        self.assertTrue(TrabajoGuardado.objects.filter(usuario=self.trabajador, trabajo=self.trabajo).exists())
        
        # Quitar de guardados
        res2 = self.client.post(reverse('toggle_guardado', args=[self.trabajo.pk]))
        self.assertEqual(res2.status_code, 302)
        self.assertFalse(TrabajoGuardado.objects.filter(usuario=self.trabajador, trabajo=self.trabajo).exists())

    def test_tc_prefnot3_001_preferencias_notificaciones(self):
        """HU041 / TC-PREFNOT3-001: Actualización de preferencias de comunicación."""
        self.client.login(username='trabajador_demo3', password='password123')
        response = self.client.post(reverse('preferencias_notificaciones'), {
            'notif_email': '0',
            'notif_sistema': '1',
            'notif_recordatorios': '1',
            'notif_mensajes': '0'
        })
        self.assertEqual(response.status_code, 302)
        self.trabajador_profile.refresh_from_db()
        self.assertFalse(self.trabajador_profile.notif_email)
        self.assertTrue(self.trabajador_profile.notif_sistema)

    def test_tc_onboarding_completar(self):
        """CP-018: Guía inicial / Onboarding completado por el usuario."""
        self.client.login(username='trabajador_demo3', password='password123')
        response = self.client.post(reverse('completar_onboarding'))
        self.assertEqual(response.status_code, 200)
        self.trabajador_profile.refresh_from_db()
        self.assertTrue(self.trabajador_profile.onboarding_completado)

    def test_tc_represena3_001_reportar_resena(self):
        """HU048 / TC-REPRESENA3-001: Reporte de reseña inapropiada."""
        resena = Resena.objects.create(
            trabajo=self.trabajo,
            solicitud=self.solicitud,
            autor=self.contratista,
            destinatario=self.trabajador,
            calificacion=1,
            comentario='Comentario ofensivo de prueba'
        )
        self.client.login(username='trabajador_demo3', password='password123')
        response = self.client.post(reverse('reportar_resena', args=[resena.pk]), {
            'motivo': 'Lenguaje inapropiado y ofensivo'
        })
        self.assertEqual(response.status_code, 302)
        resena.refresh_from_db()
        self.assertTrue(resena.reportada)
