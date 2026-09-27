"""
Detecta (y opcionalmente borra) vacantes que parecen datos de prueba,
por título sospechosamente corto o palabras típicas de prueba.

NO borra nada por defecto — solo lista. Revisa la lista antes de confirmar.

Uso:
    python manage.py limpiar_datos_prueba              # solo muestra candidatos
    python manage.py limpiar_datos_prueba --confirmar  # borra los que se muestren
"""
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db.models.functions import Length
from core.models import Trabajo

PALABRAS_SOSPECHOSAS = ['test', 'prueba', 'asdf', 'qwerty', 'xxx', 'lorem', 'aaaa']


class Command(BaseCommand):
    help = 'Detecta vacantes (Trabajo) que parecen datos de prueba, por título corto o palabras típicas de prueba.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirmar', action='store_true',
            help='Borra los registros encontrados. Sin esta bandera, solo los lista.'
        )

    def handle(self, *args, **options):
        q_palabras = Q()
        for palabra in PALABRAS_SOSPECHOSAS:
            q_palabras |= Q(titulo__icontains=palabra) | Q(descripcion__icontains=palabra)

        candidatos = Trabajo.objects.annotate(titulo_len=Length('titulo')).filter(
            Q(titulo_len__lte=2) | q_palabras
        ).distinct()

        if not candidatos.exists():
            self.stdout.write(self.style.SUCCESS('No se encontraron vacantes que parezcan datos de prueba.'))
            return

        self.stdout.write(self.style.WARNING(f'Se encontraron {candidatos.count()} vacante(s) sospechosa(s):\n'))
        for t in candidatos:
            self.stdout.write(f'  ID {t.pk} — "{t.titulo}" — publicado por {t.contratista.get_full_name() or t.contratista.username}')

        if options['confirmar']:
            count = candidatos.count()
            candidatos.delete()
            self.stdout.write(self.style.SUCCESS(f'\n{count} vacante(s) borrada(s).'))
        else:
            self.stdout.write(self.style.NOTICE('\nEsto fue solo una vista previa. Revisa la lista y, si está correcta, corre:'))
            self.stdout.write('  python manage.py limpiar_datos_prueba --confirmar')