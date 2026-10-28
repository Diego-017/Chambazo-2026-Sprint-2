from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from core.models import PlanSuscripcion, SuscripcionUsuario

class Command(BaseCommand):
    help = 'Asigna el plan Básico gratuito a usuarios sin suscripción'

    def handle(self, *args, **options):
        count = 0
        now = timezone.now()
        for user in User.objects.all():
            if not SuscripcionUsuario.objects.filter(usuario=user).exists():
                rol = 'trabajador'
                if hasattr(user, 'profile') and user.profile.rol:
                    rol = user.profile.rol
                plan = PlanSuscripcion.objects.filter(rol=rol, tipo='basico', activo=True).first()
                if not plan:
                    plan = PlanSuscripcion.objects.filter(tipo='basico', activo=True).first()
                if plan:
                    SuscripcionUsuario.objects.create(
                        usuario=user,
                        plan=plan,
                        fecha_renovacion=now + timedelta(days=30),
                        mes_actual=now.month,
                        usos_este_mes=0,
                        activa=True
                    )
                    count += 1
        self.stdout.write(self.style.SUCCESS(f'Suscripciones básicas creadas: {count}'))
