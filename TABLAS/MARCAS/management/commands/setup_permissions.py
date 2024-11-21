from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from ...models import *  # Importa tus modelos
from ...permissions import setup_permission_groups

class Command(BaseCommand):
    help = 'Configura los grupos y permisos del sistema'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                self.stdout.write(self.style.WARNING('Iniciando configuración de permisos...'))
                # Ejecutar la función de configuración de permisos
                setup_permission_groups()
                self.stdout.write(self.style.SUCCESS('Permisos configurados exitosamente'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al configurar permisos: {str(e)}')
            )
            raise e