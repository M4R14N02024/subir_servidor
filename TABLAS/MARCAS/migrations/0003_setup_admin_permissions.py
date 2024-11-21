from django.db import migrations
from django.contrib.auth import get_user_model

def asignar_grupo_admin(apps, schema_editor):
    # Importante: usar el modelo Group desde apps
    Group = apps.get_model('auth', 'Group')
    User = apps.get_model('auth', 'User')  # Cambio importante aquí
    
    # Crear o obtener el grupo Administradores
    admin_group, created = Group.objects.get_or_create(name='Administradores')
    print("✓ Grupo Administradores verificado")

    # Obtener todos los superusuarios
    superusers = User.objects.filter(is_superuser=True)
    
    # Asignar cada superusuario al grupo Administradores
    for user in superusers:
        user.groups.add(admin_group)
        user.is_staff = True
        user.save()
        print(f"✓ Usuario {user.username} añadido al grupo Administradores")

def revertir_asignacion(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    User = apps.get_model('auth', 'User')  # Usar el modelo User de apps
    
    try:
        admin_group = Group.objects.get(name='Administradores')
        superusers = User.objects.filter(is_superuser=True)
        for user in superusers:
            user.groups.remove(admin_group)
    except Group.DoesNotExist:
        pass

class Migration(migrations.Migration):
    dependencies = [
        ('MARCAS', '0002_create_initial_data'),  # Asegúrate que este sea el número correcto
        ('auth', '__first__'),  # Añadir dependencia del app auth
    ]

    operations = [
        migrations.RunPython(asignar_grupo_admin, revertir_asignacion),
    ]