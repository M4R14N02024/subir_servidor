# permissions.py

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from .models import *

def setup_permission_groups():
    GROUPS = {
        'Administradores': {
            'models': {
                # Acceso total a todos los modelos
                Marca: ['add', 'change', 'delete', 'view'],
                Categoria: ['add', 'change', 'delete', 'view'],
                Producto: ['add', 'change', 'delete', 'view'],
                Venta: ['add', 'change', 'delete', 'view'],
                DetalleVenta: ['add', 'change', 'delete', 'view'],
                Empleado: ['add', 'change', 'delete', 'view'],
                Caja: ['add', 'change', 'delete', 'view'],
                BolsaAbierta: ['add', 'change', 'delete', 'view'],
                StockAlert: ['add', 'change', 'delete', 'view'],
                Sucursal: ['add', 'change', 'delete', 'view'],
                Cliente: ['add', 'change', 'delete', 'view'],
                Edad: ['add', 'change', 'delete', 'view'],
                Tamaño: ['add', 'change', 'delete', 'view'],
                Animal: ['add', 'change', 'delete', 'view'],
                Consistencia: ['add', 'change', 'delete', 'view'],
                MovimientoStock: ['add', 'change', 'delete', 'view'],
            },
            'custom_permissions': [
                ('ver_graficos', 'Puede ver gráficos y estadísticas'),
                ('ver_sesiones', 'Puede ver registro de sesiones'),
                ('gestionar_empleados', 'Puede gestionar empleados'),
                ('realizar_ventas', 'Puede realizar ventas'),
                ('gestionar_stock', 'Puede gestionar stock'),
                ('gestionar_bolsas', 'Puede gestionar bolsas'),
                ('descontar_stock', 'Puede descontar stock'),
                ('ver_reportes', 'Puede ver reportes'),
            ]
        },
        'Empleados Especiales': {
            'models': {
                Marca: ['add', 'change', 'view'],
                Categoria: ['add', 'change', 'view'],
                Producto: ['add', 'change', 'view'],
                Venta: ['add', 'change', 'view'],
                DetalleVenta: ['add', 'change', 'view'],
                Empleado: ['view'],  # Solo ver empleados
                Caja: ['add', 'view'],
                BolsaAbierta: ['add', 'delete', 'view'],
                StockAlert: ['add', 'view'],
                Sucursal: ['add', 'change', 'view'],
                Cliente: ['add', 'change', 'view'],
                Edad: ['add', 'change', 'delete', 'view'],
                Tamaño: ['add', 'change', 'delete', 'view'],
                Animal: ['add', 'change', 'delete', 'view'],
                Consistencia: ['add', 'change', 'delete', 'view'],
                MovimientoStock: ['add', 'change', 'delete', 'view'],
            },
            'custom_permissions': [
                ('ver_graficos', 'Puede ver gráficos y estadísticas'),
                ('ver_sesiones', 'Puede ver registro de sesiones'),
                ('realizar_ventas', 'Puede realizar ventas'),
                ('gestionar_stock', 'Puede gestionar stock'),
                ('gestionar_bolsas', 'Puede gestionar bolsas'),
                ('ver_reportes', 'Puede ver reportes'),
                ('descontar_stock', 'Puede descontar stock'),  
            ]
        },
        'Empleados Regulares': {
            'models': {
                Marca: ['view'],
                Categoria: ['view'],
                Producto: ['view', 'change'],
                Venta: ['add', 'view', 'change'],
                DetalleVenta: ['add', 'view'],
                Caja: ['add', 'change', 'view'],
                BolsaAbierta: ['add', 'change', 'view'],
                StockAlert: ['view'],
            },
            'custom_permissions': [
                ('realizar_ventas', 'Puede realizar ventas'),
                ('abrir_caja', 'Puede abrir caja'),
                ('cerrar_caja', 'Puede cerrar caja'),
                ('modificar_stock', 'Puede modificar stock de productos'),
                ('gestionar_bolsas', 'Puede gestionar bolsas para ventas'),
                ('cambiar_estado_venta', 'Puede cambiar estado de venta'),
            ]
        }
    }

    with transaction.atomic():
        for group_name, group_data in GROUPS.items():
            group, _ = Group.objects.get_or_create(name=group_name)
            group.permissions.clear()
            
            for model, permissions in group_data['models'].items():
                content_type = ContentType.objects.get_for_model(model)
                for permission in permissions:
                    codename = f'{permission}_{model._meta.model_name}'
                    try:
                        perm = Permission.objects.get(
                            codename=codename,
                            content_type=content_type,
                        )
                    except Permission.DoesNotExist:
                        perm = Permission.objects.create(
                            codename=codename,
                            name=f'Can {permission} {model._meta.verbose_name}',
                            content_type=content_type,
                        )
                    group.permissions.add(perm)
            
            for codename, name in group_data['custom_permissions']:
                content_type = ContentType.objects.get_for_model(Permission)
                try:
                    perm = Permission.objects.get(
                        codename=codename,
                        content_type=content_type,
                    )
                except Permission.DoesNotExist:
                    perm = Permission.objects.create(
                        codename=codename,
                        name=name,
                        content_type=content_type,
                    )
                group.permissions.add(perm)