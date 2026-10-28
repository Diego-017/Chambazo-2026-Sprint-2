from django.core.management.base import BaseCommand
from core.models import PlanSuscripcion

class Command(BaseCommand):
    help = 'Crea los planes de suscripción por defecto'

    def handle(self, *args, **options):
        planes = [
            # Contratista
            {'nombre': 'Básico Empleador', 'slug': 'basico-empleador', 'rol': 'contratista', 'tipo': 'basico',
             'precio_mensual': 0, 'cupo_mensual': 2, 'icono': '🆓', 'color': '#64748b', 'orden': 1,
             'beneficios': ['2 vacantes por mes', 'Publicación estándar', 'Soporte por chat']},
            {'nombre': 'Pro Empleador', 'slug': 'pro-empleador', 'rol': 'contratista', 'tipo': 'pro',
             'precio_mensual': 14.99, 'cupo_mensual': 15, 'icono': '⭐', 'color': '#f59e0b', 'orden': 2, 'destacado': True,
             'beneficios': ['15 vacantes por mes', 'Vacantes destacadas', 'Badge "Empresa Pro"', 'Estadísticas avanzadas', 'Filtro de candidatos', 'Soporte prioritario']},
            {'nombre': 'Premium Empleador', 'slug': 'premium-empleador', 'rol': 'contratista', 'tipo': 'premium',
             'precio_mensual': 29.99, 'cupo_mensual': 0, 'icono': '💎', 'color': '#8b5cf6', 'orden': 3,
             'beneficios': ['Vacantes ilimitadas', 'Todo lo de Pro', 'Vacantes urgentes gratis', 'Comparador de candidatos ilimitado', 'Badge "Premium"', 'Soporte VIP 24/7']},
            # Trabajador
            {'nombre': 'Básico Trabajador', 'slug': 'basico-trabajador', 'rol': 'trabajador', 'tipo': 'basico',
             'precio_mensual': 0, 'cupo_mensual': 5, 'icono': '🆓', 'color': '#64748b', 'orden': 1,
             'beneficios': ['5 aplicaciones por mes', 'Búsqueda de empleos', 'Perfil básico']},
            {'nombre': 'Pro Trabajador', 'slug': 'pro-trabajador', 'rol': 'trabajador', 'tipo': 'pro',
             'precio_mensual': 4.99, 'cupo_mensual': 30, 'icono': '⭐', 'color': '#f59e0b', 'orden': 2, 'destacado': True,
             'beneficios': ['30 aplicaciones por mes', 'Badge "Trabajador Pro"', 'Aplicación rápida', 'Prioridad en búsquedas', 'Alertas de trabajos nuevos']},
            {'nombre': 'Premium Trabajador', 'slug': 'premium-trabajador', 'rol': 'trabajador', 'tipo': 'premium',
             'precio_mensual': 9.99, 'cupo_mensual': 0, 'icono': '💎', 'color': '#8b5cf6', 'orden': 3,
             'beneficios': ['Aplicaciones ilimitadas', 'Todo lo de Pro', 'CV destacado', 'Visibilidad máxima', 'Estadísticas de perfil', 'Soporte VIP 24/7']},
        ]
        created = 0
        for p in planes:
            obj, was_created = PlanSuscripcion.objects.update_or_create(slug=p['slug'], defaults=p)
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Planes creados: {created}, actualizados: {len(planes) - created}'))
