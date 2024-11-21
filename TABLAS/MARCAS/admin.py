from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(Marca)
admin.site.register(Edad)
admin.site.register(Empleado)
admin.site.register(Categoria)
admin.site.register(Sucursal)
admin.site.register(Cliente)
admin.site.register(Producto)
admin.site.register(Caja)
admin.site.register(Animal)
admin.site.register(Consistencia)
admin.site.register(Tamaño)
admin.site.register(Venta)
admin.site.register(DetalleVenta)
@admin.register(RegistroSesion)
class RegistroSesionAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'inicio_s', 'cierre_s', 'duracion')
    list_filter = ('empleado', 'inicio_s', 'cierre_s')
    search_fields = ['empleado__nombre', 'empleado__apellido']

    def duracion(self, obj):
        if obj.cierre_s:
            return obj.cierre_s - obj.inicio_s
        return timezone.now() - obj.inicio_s
    duracion.short_description = 'Duración'
from django.contrib import admin
from .models import StockAlert

@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ['producto', 'fecha_creacion', 'leido', 'nivel_stock']
    list_filter = ['leido', 'fecha_creacion']
    search_fields = ['producto__nombre']