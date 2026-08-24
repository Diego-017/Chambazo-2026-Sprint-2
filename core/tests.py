from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from core.models import (
    UserProfile, Trabajo, Solicitud, Resena, GaleriaItem, Logro, LogroObtenido
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
            ubicacion='San Salvador'
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
            tarifa_hora=15.00,
            experiencia_anos=8
        )

        # Crear trabajo
        self.trabajo = Trabajo.objects.create(
            contratista=self.contratista_user,
            titulo='Instalación de acometida eléctrica',
            categoria='electricidad',
            descripcion='Instalación de acometida trifásica en casa de campo.',
            ubicacion='Santa Tecla',
            presupuesto=180.00,
            habilidades_req=['electricidad']
        )

    def test_user_profile_properties(self):
        """Valida propiedades calculadas del perfil (nombre display, completitud)."""
        self.assertEqual(self.contratista_profile.nombre_display, 'Constructora Nacional S.A.')
        self.assertEqual(self.trabajador_profile.nombre_display, 'Carlos Gómez')
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
            trabajador=self.trabajador_user,
            titulo='Panel de distribución 220V',
            categoria='electricidad',
            descripcion='Instalación limpia de breakers industriales.'
        )
        self.assertEqual(item.trabajador, self.trabajador_user)
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
