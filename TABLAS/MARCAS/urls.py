from django.urls import path, include
from . import views
from .views import inicio, home_redirect
from django.contrib.auth import views as auth_views

#Imagen
from django.conf import settings
from django.contrib.staticfiles.urls import static
from .decorators import *


urlpatterns = [
    ######LOGIN######
    path('', home_redirect, name='home_redirect'),  
    path('inicio/', inicio, name='inicio'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('sesiones/', views.ver_sesiones, name='ver_sesiones'),
    ######MENU######
    path('menu/', views.menu_p, name='menu_p'),
    path('apertura-caja/', views.apertura_caja, name='apertura_caja'),
    path('stock/', views.stock, name= 'stock'),
    path('registros/', admin_or_special_required(views.vista_registros), name='registros'),



    #######MARCAS######
    path('marcas', views.marcas, name='marcas'),
    path('marcas/crear', views.crear, name='crear'),
    path('eliminar_marca/<int:id>', admin_or_special_required(views.eliminar), name='eliminar_marca'),
    path('tablas/editar-marca', admin_or_special_required(views.editar), name='editar_marca'),
    path('tablas/editar-marca/<int:id>', admin_or_special_required(views.editar), name='editar_marca'),


    ######EDADES######
    path('edades', views.edades, name='edades'),
    path('edades/crear', views.crear_edad, name='crear_edad'),
    path('tablas/editar-edad', admin_or_special_required(views.editar_edad), name='editar_edad'),
    path('tablas/editar-edad/<int:id>', admin_or_special_required(views.editar_edad), name='editar_edad'),
    path('eliminar_edad/<int:id>', admin_or_special_required(views.eliminar_edad), name='eliminar_edad'),


    ######EMPLEADOS######
    path('empleados', admin_or_special_required(views.empleados), name='empleados'),
    path('tablas/editar-empleado', admin_required(views.editar_empleado), name='editar_edad'),
    path('tablas/editar-empleado/<int:id>', admin_required(views.editar_empleado), name='editar_empleado'),
    path('eliminar-empleado/<int:id>', admin_required(views.eliminar_empleado), name='eliminar_empleado'),
    path('empleados/crear/', admin_required(views.crear_empleado), name='crear_empleado'),


    ######CATEGORIAS######
    path('categorias', views.categorias, name='categorias'),
    path('categorias/crear', views.crear_categoria, name='crear_categoria'),
    path('tablas/editar-categoria', admin_or_special_required(views.editar_categoria), name='editar_categoria'),
    path('tablas/editar-categoria/<int:id>', admin_or_special_required(views.editar_categoria), name='editar_categoria'),
    path('eliminar_categoria/<int:id>', admin_or_special_required(views.eliminar_categoria), name='eliminar_categoria'),


    ######EMPLEADOS######
    path('sucursales', views.sucursales, name='sucursales'),
    path('sucursales/crear', admin_or_special_required(views.crear_sucursal), name='crear_sucursal'),
    path('tablas/editar-sucursal', admin_or_special_required(views.editar_sucursal), name='editar_sucursal'),
    path('tablas/editar-sucursal/<int:id>', admin_or_special_required(views.editar_sucursal), name='editar_sucursal'),
    path('eliminar-sucursal/<int:id>',admin_required(views.eliminar_sucursal), name='eliminar_sucursal'),



    ######CLIENTE######
    path('clientes', views.clientes, name='clientes'),
    path('clientes/crear', admin_or_special_required(views.crear_cliente), name='crear_cliente'),
    path('tablas/editar-cliente', admin_required(views.editar_cliente), name='editar_cliente'),
    path('tablas/editar-cliente/<int:id>', admin_required(views.editar_cliente), name='editar_cliente'),
    path('eliminar-cliente/<int:id>', admin_required(views.eliminar_cliente), name='eliminar_cliente'),

        ######tamaño######
    path('tamaños', views.tamaños, name='tamaños'),
    path('tamaños/crear', views.crear_tamaño, name='crear_tamaño'),
    path('tablas/editar-tamaño', admin_or_special_required(views.editar_tamaño), name='editar_tamaño'),
    path('tablas/editar-tamaño/<int:id>', admin_or_special_required(views.editar_tamaño), name='editar_tamaño'),
    path('eliminar_tamaño/<int:id>', admin_or_special_required(views.eliminar_tamaño), name='eliminar_tamaño'),

    ######animal######
    path('animales', views.animales, name='animales'),
    path('animales/crear', views.crear_animal, name='crear_animal'),
    path('tablas/editar-animal',admin_or_special_required( views.editar_animal), name='editar_animal'),
    path('tablas/editar-animal/<int:id>',admin_or_special_required( views.editar_animal), name='editar_animal'),
    path('eliminar_animal/<int:id>',admin_or_special_required(views.eliminar_animal), name='eliminar_animal'),

    ######consistencia######
    path('consistencias', views.consistencias, name='consistencias'),
    path('consistencias/crear', views.crear_consistencia, name='crear_consistencia'),
    path('tablas/editar-consistencia', admin_or_special_required(views.editar_consistencia), name='editar_consistencia'),
    path('tablas/editar-consistencia/<int:id>', admin_or_special_required(views.editar_consistencia), name='editar_consistencia'),
    path('eliminar_consistencia/<int:id>', admin_or_special_required(views.eliminar_consistencia), name='eliminar_consistencia'),

    ######PRODUCTOS######
    path('productos', views.productos, name='productos'),
    path('productos/crear', views.crear_producto, name='crear_producto'),
    path('tablas/editar-producto', admin_or_special_required(views.editar_producto), name='editar_producto'),
    path('tablas/editar-producto/<int:id>', admin_or_special_required(views.editar_producto), name='editar_producto'),
    path('eliminar_producto/<int:id>/', admin_or_special_required(views.eliminar_producto), name='eliminar_producto'),
    path('productos/bajo-stock/', (views.productos_baja_existencia), name='productos_baja_existencia'),
    path('alertas/marcar-leida/<int:alerta_id>/', (views.marcar_alerta_leida), name='marcar_alerta_leida'),
    path('productos/reposicion_producto/<int:id>/', (views.reposicion_producto), name='reposicion_producto'),
    path('productos/autocomplete/', (views.autocomplete_productos), name='autocomplete_productos'),
    path('check_alerts/', (views.check_alerts), name='check_alerts'),


    path('agregar/', views.agregarcosas, name='agregar'),


    ######CAJAS######
    path('cajas/', views.cajas, name='cajas'),
    path('crear_caja/', views.crear_caja, name='crear_caja'),
    path('editar_caja/<int:id>/', admin_required(views.editar_caja), name='editar_caja'),
    path('eliminar_caja/<int:id>/', admin_required(views.eliminar_caja), name='eliminar_caja'),
    path('cerrar-caja/', views.cerrar_caja, name='cerrar_caja'),
    path('cajas/listar/',admin_or_special_required(views.listar_cajas), name='listar_cajas'),


    ######VENTAS######
    path('ventas', views.ventas, name='ventas'),
    path('ventas/<int:venta_id>/detalles/', views.detalles, name='detalles'),
    path('ventas/crear', views.crear_ventas, name='crear_venta'),
    path('tablas/editar-venta', views.editar_venta, name='editar_venta'),
    path('tablas/editar-venta/<int:id>', views.editar_venta, name='editar_venta'),
    path('eliminar-venta/<int:id>', admin_required(views.eliminar_venta), name='eliminar_venta'),
    path('ventas/cancelar/<int:id>/', views.cancelar_venta, name='cancelar_venta'),
    path('ventas/cambiar-estado/<int:id>/', views.cambiar_estado_venta, name='cambiar_estado_venta'),
    path('ventas/nueva/', views.nueva_venta, name='nueva_venta'),

    ######DETALLE DE VENTA######
    path('ventas/<int:venta_id>/detalles/', views.detalles, name='detalles'),
    path('detalles/crear', views.crear_detalles, name='crear_detalle'),
    path('tablas/editar-detalle', views.editar_detalle, name='editar_detalle'),
    path('tablas/editar-detalle/<int:id>', views.editar_detalle, name='editar_detalle'),
    path('eliminar-detalle/<int:id>', admin_required(views.eliminar_detalle), name='eliminar_detalle'),

    path('apertura-caja/', views.apertura_caja, name='apertura_caja'),
    path('buscar-producto/', views.buscar_producto, name='buscar_productos'),
    path('obtener_productos/', views.obtener_productos, name='obtener_productos'),

    path('obtener_productos_sueltos/', views.obtener_productos_sueltos, name='obtener_productos_sueltos'),
    path('obtener_bolsas_abiertas/', views.obtener_bolsas_abiertas, name='obtener_bolsas_abiertas'),
    path('abrir_bolsa/', views.abrir_bolsa, name='abrir_bolsa'),
    path('vender_suelto/', views.vender_suelto, name='vender_suelto'),
    path('cerrar_bolsa/', views.cerrar_bolsa, name='cerrar_bolsa'),
    path('devolver_monto_bolsa/', views.devolver_monto_bolsa, name='devolver_monto_bolsa'),
    path('bolsas/', admin_or_special_required(views.bolsas), name='bolsas'),
    path('verificar_ultimo_50_porciento/<int:bolsa_id>/', views.verificar_ultimo_50_porciento, name='verificar_ultimo_50_porciento'),
    
    ########GRAFICOS#######################
    path('registros/graficos/', views.dashboard_completo, name='graficos'),
    ########contraseñaa#######################
    path('empleados/cambiar-password/<int:empleado_id>/',admin_required(views.cambiar_password_empleado), name='cambiar_password_empleado'),
    path('empleados/cambiar-rol/<int:empleado_id>/', admin_required(views.cambiar_rol_empleado), name='cambiar_rol_empleado'),
    #####################descontar productos###########################
    path('descontar-stock/', views.descontar_stock, name='descontar-stock'),
    path('movimientos-stock/', views.lista_movimientos, name='lista_movimientos'),


]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
