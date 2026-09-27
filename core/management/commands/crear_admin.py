"""
Crea una cuenta de Administrador completa: User + UserProfile (rol='administrador')
+ is_staff=True, todo en un solo paso. Evita el caso de un superusuario de Django
creado con createsuperuser que no tiene UserProfile (eso rompe el login normal
de Chambazo, que espera request.user.profile en todas las cuentas).

Uso:
    python manage.py crear_admin --username admin --email admin@chambazo.sv --password "clave-segura"
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from core.models import UserProfile


class Command(BaseCommand):
    help = 'Crea una cuenta de Administrador de Chambazo (User + UserProfile + is_staff).'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True)
        parser.add_argument('--email', required=True)
        parser.add_argument('--password', required=True)
        parser.add_argument('--nombre', default='', help='Nombre completo (opcional)')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']

        if User.objects.filter(username=username).exists():
            raise CommandError(f'Ya existe un usuario con username "{username}".')
        if User.objects.filter(email=email).exists():
            raise CommandError(f'Ya existe un usuario con email "{email}".')

        nombre = options['nombre'].strip()
        first_name, _, last_name = nombre.partition(' ')

        user = User.objects.create_user(
            username=username, email=email, password=options['password'],
            first_name=first_name, last_name=last_name,
        )
        user.is_staff = True
        user.save(update_fields=['is_staff'])

        UserProfile.objects.create(user=user, rol='administrador')

        self.stdout.write(self.style.SUCCESS(
            f'Cuenta de administrador creada: {username} ({email}). '
            f'Ya puede iniciar sesión normalmente en /login/ y será enviado a la consola de administración.'
        ))