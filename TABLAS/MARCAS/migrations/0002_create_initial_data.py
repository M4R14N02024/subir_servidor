from django.db import migrations

def crear_datos_iniciales(apps, schema_editor):
    # Crear Sucursal por defecto
    Sucursal = apps.get_model('MARCAS', 'Sucursal')
    sucursal_default, created = Sucursal.objects.get_or_create(
        direccion='Av.Hipólito Yrigoyen 550',
        defaults={
            'telefono': '123456789'
        }
    )
    print("✓ Sucursal creada" if created else "→ Sucursal ya existente")
    
    # Crear Cliente por defecto
    Cliente = apps.get_model('MARCAS', 'Cliente')
    cliente_default, created = Cliente.objects.get_or_create(
        consumidor='Consumidor Final'
    )
    print("✓ Cliente por defecto creado" if created else "→ Cliente ya existente")
    
    # Crear Tamaños
    Tamaño = apps.get_model('MARCAS', 'Tamaño')
    for tamaño in ['Pequeño', 'Mediano', 'Grande', 'Gigante', 'Estándar']:
        _, created = Tamaño.objects.get_or_create(tamaño=tamaño)
        print(f"{'✓' if created else '→'} Tamaño '{tamaño}' {'creado' if created else 'ya existe'}")
    
    # Crear Consistencias
    Consistencia = apps.get_model('MARCAS', 'Consistencia')
    for consistencia in ['Seco', 'Húmedo']:
        _, created = Consistencia.objects.get_or_create(consistencia=consistencia)
        print(f"{'✓' if created else '→'} Consistencia '{consistencia}' {'creada' if created else 'ya existe'}")
    
    # Crear Edades
    Edad = apps.get_model('MARCAS', 'Edad')
    for edad in ['Cachorro', 'Adulto', 'Senior']:
        _, created = Edad.objects.get_or_create(edad=edad)
        print(f"{'✓' if created else '→'} Edad '{edad}' {'creada' if created else 'ya existe'}")
        
    # Crear Categorías
    Categoria = apps.get_model('MARCAS', 'Categoria')
    for categoria in ['Alimento', 'Medicamento', 'Indumentaria']:
        _, created = Categoria.objects.get_or_create(categoria=categoria)
        print(f"{'✓' if created else '→'} Categoría '{categoria}' {'creada' if created else 'ya existe'}")
    
    # Crear Animales
    Animal = apps.get_model('MARCAS', 'Animal')
    for animal in ['Perro', 'Gato']:
        _, created = Animal.objects.get_or_create(animal=animal)
        print(f"{'✓' if created else '→'} Animal '{animal}' {'creado' if created else 'ya existe'}")

def revertir_datos_iniciales(apps, schema_editor):
    Animal = apps.get_model('MARCAS', 'Animal')
    Categoria = apps.get_model('MARCAS', 'Categoria')
    Edad = apps.get_model('MARCAS', 'Edad')
    Consistencia = apps.get_model('MARCAS', 'Consistencia')
    Tamaño = apps.get_model('MARCAS', 'Tamaño')
    Cliente = apps.get_model('MARCAS', 'Cliente')
    Sucursal = apps.get_model('MARCAS', 'Sucursal')
    
    Animal.objects.filter(animal__in=['Perro', 'Gato']).delete()
    Categoria.objects.filter(categoria__in=['Alimento', 'Medicamento', 'Indumentaria']).delete()
    Edad.objects.filter(edad__in=['Cachorro', 'Adulto', 'Senior']).delete()
    Consistencia.objects.filter(consistencia__in=['Seco', 'Húmedo']).delete()
    Tamaño.objects.filter(tamaño__in=['Pequeño', 'Mediano', 'Grande', 'Gigante', 'Estándar']).delete()
    Cliente.objects.filter(consumidor='Consumidor Final').delete()
    Sucursal.objects.filter(direccion='Av.Hipólito Yrigoyen 550').delete()

class Migration(migrations.Migration):
    dependencies = [
        ('MARCAS', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(crear_datos_iniciales, revertir_datos_iniciales),
    ]