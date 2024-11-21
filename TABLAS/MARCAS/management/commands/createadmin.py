# Archivo: management/commands/createadministrador.py
from django.contrib.auth.management.commands import createsuperuser
from django.db import transaction
from django.core.management import CommandError
from ...models import Empleado
import re

class ValidationMixin:
    """Mixin con métodos de validación compartidos"""
    
    def validate_username(self, username):
        """Valida el formato del nombre de usuario."""
        if not 1 <= len(username) <= 12:
            raise CommandError("El nombre de usuario debe tener entre 1 y 12 caracteres.")
        
        if not re.match(r'^[a-zA-Z0-9]+$', username):
            raise CommandError("El nombre de usuario solo puede contener letras y números.")
        
        return username

    def validate_password(self, password):
        """Valida el formato de la contraseña."""
        if not 6 <= len(password) <= 14:
            raise CommandError("La contraseña debe tener entre 6 y 14 caracteres.")
        
        if not re.match(r'^[a-zA-Z0-9]+$', password):
            raise CommandError("La contraseña solo puede contener letras y números.")
        
        return password

    def validate_nombre(self, nombre, campo="Nombre"):
        """Valida y formatea el nombre o apellido."""
        if not nombre.strip():
            raise CommandError(f"El {campo.lower()} no puede estar vacío.")
        
        palabras = nombre.strip().split()
        nombre_formateado = ' '.join(palabra.capitalize() for palabra in palabras)
        
        return nombre_formateado
        
    def validate_telefono(self, telefono):
        """Valida el formato del teléfono."""
        if not telefono.strip():
            raise CommandError("El teléfono no puede estar vacío.")
        
        if not re.match(r'^\d{10}$', telefono.strip()):
            raise CommandError("El teléfono debe contener exactamente 10 dígitos.")
        
        return telefono.strip()

class Command(ValidationMixin, createsuperuser.Command):
    help = 'Crea un administrador (superusuario) y su empleado asociado con validaciones'

    def handle(self, *args, **options):
        UserModel = self.UserModel
        username = options.get(UserModel.USERNAME_FIELD)
        email = options.get('email')
        password = options.get('password')

        # Solicitar y validar nombre de usuario
        while True:
            if not username:
                username = input("Username (1-12 caracteres, solo letras y números): ")
            try:
                username = self.validate_username(username)
                break
            except CommandError as e:
                self.stderr.write(self.style.ERROR(str(e)))
                username = None

        # Solicitar email
        while True:
            if not email:
                email = input("Email address: ")
            if '@' in email:  # Validación básica de email
                break
            self.stderr.write(self.style.ERROR("Email inválido. Debe contener @"))
            email = None

        # Solicitar y validar contraseña
        while True:
            if not password:
                password = input("Password (6-14 caracteres, solo letras y números): ")
            try:
                password = self.validate_password(password)
                break
            except CommandError as e:
                self.stderr.write(self.style.ERROR(str(e)))
                password = None

        with transaction.atomic():
            try:
                # Verificar si el usuario ya existe
                if UserModel.objects.filter(username=username).exists():
                    raise CommandError(f"El usuario '{username}' ya existe.")

                # Crear el superusuario
                user = UserModel._default_manager.create_superuser(
                    **{
                        UserModel.USERNAME_FIELD: username,
                        'email': email,
                        'password': password,
                    }
                )

                # Solicitar y validar nombre
                while True:
                    try:
                        nombre = self.validate_nombre(input("Nombre: "))
                        break
                    except CommandError as e:
                        self.stderr.write(self.style.ERROR(str(e)))

                # Solicitar y validar apellido
                while True:
                    try:
                        apellido = self.validate_nombre(input("Apellido: "), "Apellido")
                        break
                    except CommandError as e:
                        self.stderr.write(self.style.ERROR(str(e)))

                # Solicitar y validar teléfono
                while True:
                    try:
                        telefono = self.validate_telefono(input("Teléfono (10 dígitos): "))
                        break
                    except CommandError as e:
                        self.stderr.write(self.style.ERROR(str(e)))

                # Crear el empleado asociado
                empleado = Empleado.objects.create(
                    user=user,
                    nombre=nombre,
                    apellido=apellido,
                    telefono=telefono,
                    direccion=input("Dirección: "),
                    correo=email
                )

                self.stdout.write(self.style.SUCCESS(
                    f"Administrador y Empleado {empleado.nombre} {empleado.apellido} creados exitosamente."
                ))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error al crear administrador: {str(e)}"))
                raise CommandError(f"Error al crear administrador: {str(e)}")