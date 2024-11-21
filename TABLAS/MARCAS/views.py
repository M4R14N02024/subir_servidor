from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth import logout, authenticate, login, get_user_model
from django.db.models import Sum, Q, F,Count,DecimalField,Avg
from django.db.models.functions import Coalesce, Cast, TruncDate, TruncWeek,TruncMonth
from .models import *
from .forms import *
from django.http import JsonResponse, HttpResponseForbidden
from decimal import Decimal
from django.db import transaction
from django.views.decorators.http import require_http_methods, require_GET,  require_POST
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import json,logging
from django.core.paginator import Paginator
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string
from .decorators import *
from datetime import datetime, time,timedelta
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from calendar import day_name,month_abbr
import locale
import traceback
from .permissions import *
from django.contrib.auth.hashers import make_password
from django.utils.timezone import make_aware
# Create your views here.
#----------------------------------

logger = logging.getLogger(__name__)

def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('inicio')
    else:
        return redirect('login')


def login_view(request):
    # Inicializar variables
    error_message = request.session.pop('error_message', None)
    error_type = request.session.pop('error_type', None)
    
    # Si no es una petición POST, mostrar el formulario
    if request.method != 'POST':
        return render(request, 'registration/login.html', {
            'error_message': error_message,
            'error_type': error_type
        })
    
    # Obtener credenciales
    username = request.POST.get('username')
    password = request.POST.get('password')
    
    # Validar que se hayan proporcionado credenciales
    if not username or not password:
        request.session['error_message'] = "Por favor ingrese usuario y contraseña"
        request.session['error_type'] = "empty"
        return redirect('login')  # Asegúrate de tener definido este nombre de URL
    
    # Verificar bloqueo
    session_key = f'login_attempts_{username}'
    blocked_key = f'login_blocked_until_{username}'
    
    blocked_until = request.session.get(blocked_key)
    if blocked_until:
        blocked_until = timezone.datetime.fromisoformat(blocked_until)
        if blocked_until > timezone.now():
            tiempo_restante = blocked_until - timezone.now()
            minutos = int(tiempo_restante.total_seconds() / 60)
            request.session['error_message'] = f"Usuario bloqueado. Intente nuevamente en {minutos} minutos."
            request.session['error_type'] = "blocked"
            return redirect('login')
        else:
            del request.session[blocked_key]
            del request.session[session_key]
    
    try:
        # Verificar si existe el usuario
        user = User.objects.get(username=username)
        user_auth = authenticate(request, username=username, password=password)
        
        if user_auth is None:
            # Contraseña incorrecta
            attempts = request.session.get(session_key, 0) + 1
            request.session[session_key] = attempts
            
            if attempts >= 3:
                blocked_until = (timezone.now() + timedelta(minutes=15)).isoformat()
                request.session[blocked_key] = blocked_until
                request.session['error_message'] = "Usuario bloqueado por 15 minutos debido a múltiples intentos fallidos."
                request.session['error_type'] = "blocked"
                return redirect('login')
            
            request.session['error_message'] = f"Contraseña incorrecta. Le quedan {3 - attempts} intentos."
            request.session['error_type'] = "password"
            return redirect('login')
        
        # Login exitoso
        try:
            with transaction.atomic():
                empleado = Empleado.objects.get(user=user_auth)
                
                # Limpiar intentos fallidos
                if session_key in request.session:
                    del request.session[session_key]
                if blocked_key in request.session:
                    del request.session[blocked_key]
                
                # Cerrar sesiones activas
                sesiones_activas = RegistroSesion.objects.filter(
                    empleado=empleado,
                    cierre_s__isnull=True
                )
                
                for sesion in sesiones_activas:
                    sesion.cierre_s = timezone.now()
                    sesion.save()
                
                # Crear nueva sesión
                nueva_sesion = RegistroSesion.objects.create(
                    empleado=empleado,
                    inicio_s=timezone.now()
                )
                
                login(request, user_auth)
                return redirect('inicio')
                
        except ObjectDoesNotExist:
            request.session['error_message'] = "No se encontró registro de empleado"
            request.session['error_type'] = "employee"
            return redirect('login')
        except Exception as e:
            request.session['error_message'] = f"Error al iniciar sesión: {str(e)}"
            request.session['error_type'] = "system"
            return redirect('login')
    
    except User.DoesNotExist:
        # Usuario no existe
        attempts = request.session.get(session_key, 0) + 1
        request.session[session_key] = attempts
        request.session['error_message'] = "El usuario ingresado no existe"
        request.session['error_type'] = "username"
        return redirect('login')

@login_required
def logout_view(request):
    if request.user.is_authenticated:
        try:
            with transaction.atomic():
                empleado = Empleado.objects.get(user=request.user)
                
                # Buscar y cerrar todas las sesiones activas
                sesiones_activas = RegistroSesion.objects.filter(
                    empleado=empleado,
                    cierre_s__isnull=True
                )
                
                for sesion in sesiones_activas:
                    sesion.cierre_s = timezone.now()
                    sesion.save()
                    print(f"Sesión {sesion.id} cerrada correctamente")
                
                # Realizar el logout después de cerrar las sesiones
                logout(request)
                return redirect('login')
                
        except Exception as e:
            print(f"Error en logout: {str(e)}")
            logout(request)
    
    return redirect('login')

@admin_or_special_required
@login_required
def ver_sesiones(request):
    form = SessionFilterForm(request.GET)
    sesiones = RegistroSesion.objects.all().order_by('-inicio_s')

    # Debug para ver qué llega
    print("Request GET:", request.GET)

    if form.is_valid():
        empleado = form.cleaned_data.get('empleado')
        fecha_inicio = form.cleaned_data.get('fecha_inicio')
        fecha_fin = form.cleaned_data.get('fecha_fin')

        # Debug
        print("Form válido")
        print("Empleado:", empleado)
        print("Fecha inicio:", fecha_inicio)
        print("Fecha fin:", fecha_fin)

        if empleado:
            sesiones = sesiones.filter(empleado__nombre__icontains=empleado)
        
        if fecha_inicio:
            # Convertimos a la zona horaria correcta
            fecha_inicio_tz = timezone.make_aware(
                datetime.combine(fecha_inicio, time.min),
                timezone.get_current_timezone()
            )
            sesiones = sesiones.filter(inicio_s__gte=fecha_inicio_tz)
        
        if fecha_fin:
            # Convertimos a la zona horaria correcta
            fecha_fin_tz = timezone.make_aware(
                datetime.combine(fecha_fin, time.max),
                timezone.get_current_timezone()
            )
            sesiones = sesiones.filter(inicio_s__lte=fecha_fin_tz)
    else:
        # Debug para ver errores de formulario
        print("Form errors:", form.errors)

    paginator = Paginator(sesiones, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'tablas/ver_sesiones.html', {
        'sesiones': page_obj,
        'form': form,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    })

@login_required
def inicio(request):
    return render(request, 'paginas/inicio.html')

def nosotros(request):
    return render(request, 'paginas/nosotros.html')



##################################----MARCAS----#########################################
@any_employee_required
def marcas(request):
    marcas = Marca.objects.all().order_by('id')
    return render(request, 'tablas/LISTAR_MARCAS.html', {'marcas': marcas})

@any_employee_required
def crear(request):
    formulario = Marcaform(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if formulario.is_valid():
            formulario.save()

    return render(request, 'tablas/htmlbase/crear_marca.html', {'formulario': formulario})
@any_employee_required
def editar(request, id):
    marca = get_object_or_404(Marca, id=id)
    formulario = Marcaform(request.POST or None, request.FILES or None, instance=marca)
    if request.method == 'POST':
        if formulario.is_valid():
            marca.save()

    return render(request, 'tablas/htmlbase/editar_marca.html', {'formulario': formulario})
@admin_or_special_required
def eliminar(request, id):
    marca = get_object_or_404(Marca, id=id)
    marca.delete()
    return redirect('marcas')


##################################----EDADES----#######################################
@any_employee_required
def edades(request):
    edades = Edad.objects.all().order_by('id')
    return render(request, 'tablas/LISTAR_EDADES.html', {'edades': edades})
@any_employee_required
def crear_edad(request):
    formulario = Edadform(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if formulario.is_valid():
            formulario.save()


    return render(request, 'tablas/htmlbase/crear_edad.html', {'formulario': formulario})
@admin_or_special_required
def editar_edad(request, id):
    edad = get_object_or_404(Edad, id=id)
    formulario = Edadform(request.POST or None, request.FILES or None, instance=edad)
    if request.method == 'POST':
        if formulario.is_valid():
            edad.save()
    return render(request, 'tablas/htmlbase/editar_edad.html', {'formulario': formulario})
@admin_or_special_required
def eliminar_edad(request, id):
    edad = get_object_or_404(Edad, id=id)
    edad.delete()
    return redirect('edades')

##################################----EMPLEADOS----#######################################
def is_superuser(user):
    return user.is_superuser
@login_required
@admin_or_special_required
def empleados(request):
    """Vista para listar empleados"""
    empleados = Empleado.objects.select_related('user').filter(user__is_superuser=False)
    context = {
        'empleados': empleados,
        'is_admin': request.user.groups.filter(name='Administradores').exists()
    }
    return render(request, 'tablas/LISTAR_EMPLEADOS.html', context)


@login_required
@admin_required

def crear_empleado(request):
    """
    Vista para crear nuevos empleados.
    Solo administradores pueden crear empleados especiales.
    Empleados especiales solo pueden crear empleados regulares.
    """
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Validar tipo de empleado
                tipo_empleado = request.POST.get('tipo_empleado', 'regular')
                es_admin = request.user.groups.filter(name='Administradores').exists()
                
                # Solo administradores pueden crear empleados especiales
                if tipo_empleado == 'especial' and not es_admin:
                    messages.error(request, 'Solo los administradores pueden crear empleados especiales')
                    return render(request, 'tablas/htmlbase/crear_empleado.html', {
                        'error': 'No tienes permisos para crear empleados especiales'
                    })

                # Crear usuario
                user = get_user_model().objects.create_user(
                    username=request.POST['username'],
                    email=request.POST['email'],
                    password=request.POST['password']
                )
                
                # Mapeo de tipos de empleado a grupos
                grupo_nombre = {
                    'regular': 'Empleados Regulares',
                    'especial': 'Empleados Especiales',
                }
                
                # Asignar al grupo correspondiente
                try:
                    grupo = Group.objects.get(name=grupo_nombre[tipo_empleado])
                    user.groups.add(grupo)
                except Group.DoesNotExist:
                    user.delete()
                    messages.error(
                        request, 
                        f"Error de configuración: El grupo {grupo_nombre[tipo_empleado]} no existe. "
                        "Contacte al administrador del sistema."
                    )
                    return render(request, 'tablas/htmlbase/crear_empleado.html', {
                        'error': 'Error en la configuración de grupos'
                    })
                
                # Crear empleado con datos normalizados
                empleado = Empleado.objects.create(
                    user=user,
                    nombre=request.POST['nombre'].strip().title(),
                    apellido=request.POST['apellido'].strip().title(),
                    telefono=request.POST['telefono'].strip(),
                    direccion=request.POST['direccion'].strip(),
                    correo=request.POST['email'].strip().lower()
                )
                
                messages.success(
                    request, 
                    f'Empleado {empleado.nombre} {empleado.apellido} creado exitosamente como {grupo_nombre[tipo_empleado]}'
                )
                return redirect('empleados')
                
        except Exception as e:
            # Si algo falla, asegurarse de limpiar el usuario si fue creado
            if 'user' in locals():
                user.delete()
            
            messages.error(request, f'Error al crear empleado: {str(e)}')
            return render(request, 'tablas/htmlbase/crear_empleado.html', {
                'error': str(e)
            })
    
    # GET request - mostrar formulario
    return render(request, 'tablas/htmlbase/crear_empleado.html')
@admin_required
def editar_empleado(request, id):
    empleado = Empleado.objects.get(id=id)
    formulario = Empleadoform(request.POST or None, request.FILES or None, instance=empleado)
    
    if formulario.is_valid() and request.method == 'POST':
        formulario.save()
        return redirect('empleados')
    
    return render(request, 'tablas/htmlbase/editar_empleado.html', {
        'formulario': formulario
    })

@admin_required
@login_required
def eliminar_empleado(request, id):  # Nota que aquí el parámetro es 'id', no 'empleado_id'
    if request.method == 'POST':
        try:
            empleado = Empleado.objects.select_related('user').get(id=id)
            
            if empleado.user.is_superuser:
                messages.error(request, 'No se puede eliminar un superadministrador.')
                return redirect('empleados')
                
            nombre_empleado = f"{empleado.nombre} {empleado.apellido}"
            empleado.user.delete()
            messages.success(request, f'El empleado {nombre_empleado} ha sido eliminado exitosamente.')
            
        except Empleado.DoesNotExist:
            messages.error(request, 'Empleado no encontrado.')
            
    return redirect('empleados')

##################################----CATEGORIAS----#######################################
@any_employee_required
def categorias(request):
    categorias = Categoria.objects.all().order_by('id')
    return render(request, 'tablas/LISTAR_CATEGORIAS.html', {'categorias': categorias})
@any_employee_required
def crear_categoria(request):
    formulario = Categoriaform(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if formulario.is_valid():
            formulario.save()

    return render(request, 'tablas/htmlbase/crear_categoria.html', {'formulario': formulario})
@admin_or_special_required
def editar_categoria(request, id):
    categoria = get_object_or_404(Categoria, id=id)
    formulario = Categoriaform(request.POST or None, request.FILES or None, instance=categoria)
    if request.method == 'POST':
        if formulario.is_valid():
            categoria.save()

        
    return render(request, 'tablas/htmlbase/editar_categoria.html', {'formulario': formulario})
@admin_or_special_required
def eliminar_categoria(request, id):
    categoria = get_object_or_404(Categoria, id=id)
    categoria.delete()
    return redirect('categorias')



##################################----SUCURSALES----#######################################
@admin_or_special_required
def sucursales(request):
    sucursales= Sucursal.objects.all().order_by('id')
    return render(request, 'tablas/LISTAR_SUCURSALES.html', {'sucursales': sucursales})
@admin_or_special_required
def crear_sucursal(request):
    formulario= Sucursalform(request.POST or None, request.FILES or None)
    if formulario.is_valid():
        formulario.save()
        return redirect('sucursales')
    return render(request, 'tablas/htmlbase/crear_sucursal.html', {'formulario': formulario})
@admin_or_special_required
def editar_sucursal(request, id):
    sucursal = Sucursal.objects.get(id=id)
    formulario = Sucursalform(request.POST or None, request.FILES or None, instance=sucursal)
    if formulario.is_valid() and request.method == 'POST':
        formulario.save()
        return redirect('sucursales')
    return render(request, 'tablas/htmlbase/editar_sucursal.html', {'formulario': formulario})
@admin_or_special_required
def eliminar_sucursal(request, id):
    sucursal = Sucursal.objects.get(id=id)
    sucursal.delete()
    return redirect('sucursales')


##################################----CLIENTES----#######################################
@admin_or_special_required
def clientes(request):
    clientes= Cliente.objects.all().order_by('id')
    return render(request, 'tablas/LISTAR_CLIENTES.html', {'clientes': clientes})
@admin_or_special_required
def crear_cliente(request):
    formulario= Clienteform(request.POST or None, request.FILES or None)
    if formulario.is_valid():
        formulario.save()
        return redirect('clientes')
    return render(request, 'tablas/htmlbase/crear_cliente.html', {'formulario': formulario})
@admin_or_special_required
def editar_cliente(request, id):
    sucursal = Cliente.objects.get(id=id)
    formulario = Clienteform(request.POST or None, request.FILES or None, instance=sucursal)
    if formulario.is_valid() and request.method == 'POST':
        formulario.save()
        return redirect('clientes')
    return render(request, 'tablas/htmlbase/editar_cliente.html', {'formulario': formulario})
@admin_or_special_required
def eliminar_cliente(request, id):
    clientes = Cliente.objects.get(id=id)
    clientes.delete()
    return redirect('clientes')

##################################----TAMAÑOS----#######################################
@any_employee_required
def tamaños(request):
    tamaños = Tamaño.objects.all().order_by('id')
    return render(request, 'tablas/LISTAR_TAMAÑOS.html', {'tamaños': tamaños})
@any_employee_required
def crear_tamaño(request):
    formulario = Tamañoform(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if formulario.is_valid():
            formulario.save()
    return render(request, 'tablas/htmlbase/crear_tamaño.html', {'formulario': formulario})
@admin_or_special_required
def editar_tamaño(request, id):
    tamaño = get_object_or_404(Tamaño, id=id)
    formulario = Tamañoform(request.POST or None, request.FILES or None, instance=tamaño)
    if request.method == 'POST':
        if formulario.is_valid():
            formulario.save()
    return render(request, 'tablas/htmlbase/editar_tamaño.html', {'formulario': formulario})
@admin_or_special_required
def eliminar_tamaño(request, id):
    tamaño = get_object_or_404(Tamaño, id=id)
    tamaño.delete()
    return redirect('tamaños')
##################################----animal----#######################################
@any_employee_required
def animales(request):
    animales = Animal.objects.all().order_by('id')
    return render(request, 'tablas/LISTAR_ANIMALES.html', {'animales': animales})
@any_employee_required
def crear_animal(request):
    formulario = Animalform(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if formulario.is_valid():
            formulario.save()
    return render(request, 'tablas/htmlbase/crear_animal.html', {'formulario': formulario})
@admin_or_special_required
def editar_animal(request, id):
    animal = get_object_or_404(Animal, id=id)
    formulario = Animalform(request.POST or None, request.FILES or None, instance=animal)
    if request.method == 'POST':
        if formulario.is_valid():
            formulario.save()
    return render(request, 'tablas/htmlbase/editar_animal.html', {'formulario': formulario})
@admin_or_special_required
def eliminar_animal(request, id):
    animal = get_object_or_404(Animal, id=id)
    animal.delete()
    return redirect('animales')

##################################----consistencia----#######################################
@any_employee_required
def consistencias(request):
    consistencias = Consistencia.objects.all().order_by('id')
    return render(request, 'tablas/LISTAR_CONSISTENCIAS.html', {'consistencias': consistencias})
@any_employee_required
def crear_consistencia(request):
    formulario = Consistenciaform(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if formulario.is_valid():
            formulario.save()
    return render(request, 'tablas/htmlbase/crear_consistencia.html', {'formulario': formulario})
@admin_or_special_required
def editar_consistencia(request, id):
    consistencia = get_object_or_404(Consistencia, id=id)
    formulario = Consistenciaform(request.POST or None, request.FILES or None, instance=consistencia)
    if request.method == 'POST':
        if formulario.is_valid():
            consistencia.save()

    return render(request, 'tablas/htmlbase/editar_consistencia.html', {'formulario': formulario})
@admin_or_special_required
def eliminar_consistencia(request, id):
    consistencia = get_object_or_404(Consistencia, id=id)
    consistencia.delete()
    return redirect('consistencias')
##################################----PRODUCTOS----#######################################
@any_employee_required
def productos(request):
    # Obtener todos los productos
    lista_productos = Producto.objects.all()
    
    # Definir cuántos productos por página
    paginator = Paginator(lista_productos, 15)  # 15 productos por página
    
    # Obtener el número de página desde la URL
    page_number = request.GET.get('page', 1)
    
    # Obtener los productos para la página actual
    productos = paginator.get_page(page_number)
    
    return render(request, 'tablas/LISTAR_PRODUCTOS.html', {
        'productos': productos,
    })

@any_employee_required
def crear_producto(request):
    if request.method == 'POST':
        formulario = Productoform(request.POST, request.FILES)
        if formulario.is_valid():
            try:
                producto = formulario.save()
                messages.success(request, '¡Producto agregado exitosamente!')
                return redirect('productos')
            except ValidationError as e:
                # Manejar los errores de validación específicos
                for field, errors in e.message_dict.items():
                    for error in errors:
                        messages.error(request, error)
        else:
            # Mostrar errores del formulario de manera más limpia
            for field, errors in formulario.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, error)
                    else:
                        messages.error(request, f'{error}')
    else:
        formulario = Productoform()
    
    return render(request, 'tablas/htmlbase/crear_producto.html', {'formulario': formulario})
@any_employee_required
def editar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    if request.method == 'POST':
        formulario = Productoform(request.POST, request.FILES, instance=producto)
        if formulario.is_valid():
            formulario.save()
            return redirect('productos')
    else:
        formulario = Productoform(instance=producto)
    
    return render(request, 'tablas/htmlbase/editar_producto.html', {'formulario': formulario, 'producto': producto})
@admin_or_special_required
def eliminar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    
    if request.method == 'POST':
        if producto.stock_a > 0:
            messages.error(request, f'No se puede eliminar el producto "{producto}" porque tiene stock disponible ({producto.stock_a} unidades)')
            return redirect('productos')
        try:
            producto.delete()
            messages.success(request, f'El producto "{producto}" fue eliminado exitosamente')
        except Exception as e:
            messages.error(request, f'Ocurrió un error al eliminar el producto: {str(e)}')
            
    return redirect('productos')

@login_required
@any_employee_required
def productos_baja_existencia(request):
    """Vista para mostrar productos con stock bajo"""
    search_query = request.GET.get('search', '')
    
    # Obtener productos con stock bajo
    productos = Producto.objects.filter(
        stock_a__lte=F('stock_m')
    ).select_related(
        'categoria',
        'animal',
        'marca',
        'edad'
    )

    # Aplicar búsqueda si existe
    if search_query:
        productos = productos.filter(
            Q(nombre__icontains=search_query) |
            Q(marca__marca__icontains=search_query) |
            Q(categoria__categoria__icontains=search_query)
        )

    # Crear o actualizar alertas
    for producto in productos:
        StockAlert.objects.get_or_create(
            producto=producto,
            leido=False,
            defaults={'nivel_stock': producto.stock_a}
        )

    context = {
        'productos_baja_existencia': productos,
        'search_query': search_query,
        'alertas_count': StockAlert.objects.filter(leido=False).count()
    }
    
    return render(request, 'tablas/bajo_stock.html', context)

@login_required
@any_employee_required
def marcar_alerta_leida(request, alerta_id):
    """Vista para marcar una alerta como leída"""
    try:
        alerta = StockAlert.objects.get(id=alerta_id)
        alerta.leido = True
        alerta.save()
        return JsonResponse({'success': True})
    except StockAlert.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Alerta no encontrada'})

def autocomplete_productos(request):
    if 'term' in request.GET:
        qs = Producto.objects.filter(nombre__icontains=request.GET['term'])
        productos = list(qs.values_list('nombre', flat=True))
        return JsonResponse(productos, safe=False)
    return JsonResponse([], safe=False)

@login_required
@any_employee_required
def reposicion_producto(request, id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    try:
        data = json.loads(request.body)
        cantidad = int(data.get('cantidad', 0))
        
        if cantidad <= 0:
            return JsonResponse({
                'success': False,
                'message': 'La cantidad debe ser mayor a 0'
            })
        
        producto = Producto.objects.get(id=id)
        stock_anterior = producto.stock_a
        producto.stock_a += cantidad
        producto.save()
        
        # Marcar las alertas como leídas si el stock es suficiente
        if producto.stock_a > producto.stock_m:
            StockAlert.objects.filter(
                producto=producto,
                leido=False
            ).update(leido=True)
        
        return JsonResponse({
            'success': True,
            'message': f'Stock actualizado correctamente',
            'nuevo_stock': producto.stock_a
        })
        
    except Producto.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Producto no encontrado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })
@login_required
@any_employee_required
def check_alerts(request):
    try:
        # Productos sin stock (stock_a = 0)
        sin_stock = Producto.objects.filter(stock_a=0).count()
        
        # Productos con stock bajo (stock_a <= stock_m pero > 0)
        bajo_stock = Producto.objects.filter(
            stock_a__gt=0,
            stock_a__lte=F('stock_m')  # Usar el stock_m de cada producto
        ).count()
        
        print(f"Alertas - Sin stock: {sin_stock}, Bajo stock: {bajo_stock}")
        
        return JsonResponse({
            'sin_stock': sin_stock,
            'bajo_stock': bajo_stock,
            'success': True
        })
    except Exception as e:
        print(f"Error en check_alerts: {str(e)}")
        return JsonResponse({
            'error': str(e),
            'success': False
        })
##################################----CAJAS----#######################################
@login_required 
@any_employee_required
def cajas(request):
    today = timezone.localtime().date()
    
    ventas_resumen = {
        "Efectivo": Decimal('0.00'),
        "Tarjeta debito": Decimal('0.00'),
        "Transferencia": Decimal('0.00')
    }
    
    try:
        caja_dia = Caja.objects.filter(
            abierta=True
        ).select_related(
            'empleado',
            'sucursal'
        ).first()

        if not caja_dia:
            start_of_day = datetime.combine(today, time.min)
            end_of_day = datetime.combine(today, time.max)
            
            caja_dia = Caja.objects.filter(
                fecha_hs_ap__range=(start_of_day, end_of_day)
            ).select_related(
                'empleado',
                'sucursal'
            ).order_by('-fecha_hs_ap').first()
        
        if caja_dia:
            # Modificar la consulta para excluir ventas canceladas
            ventas = Venta.objects.filter(
                caja=caja_dia,
                estado='pagada'  # Solo ventas pagadas
            ).exclude(
                estado='cancelada'  # Excluir explícitamente las canceladas
            ).values('metodo_pago').annotate(
                total_venta=Sum('total_venta')
            )
            
            for venta in ventas:
                metodo = venta['metodo_pago']
                if metodo in ventas_resumen:
                    ventas_resumen[metodo] = Decimal(str(venta['total_venta'] or '0.00'))
        
        context = {
            'caja': caja_dia,
            'today': today,
            'is_superuser': request.user.is_superuser,
            'ventas_resumen': ventas_resumen
        }
        
    except Exception as e:
        print(f"Error en cajas view: {str(e)}")
        context = {
            'error': str(e),
            'today': today,
            'is_superuser': request.user.is_superuser,
            'ventas_resumen': ventas_resumen
        }
    
    return render(request, 'TABLAS/CAJA_DIA.html', context)

@admin_or_special_required
def listar_cajas(request):
    try:
        cajas = Caja.objects.all().select_related(
            'empleado',
            'sucursal'
        ).order_by('-fecha_hs_ap')
        
        context = {
            'cajas': cajas,
            'is_superuser': request.user.is_superuser
        }
        return render(request, 'tablas/LISTAR_CAJAS.html', context)
    except Exception as e:
        context = {
            'error': str(e),
            'is_superuser': request.user.is_superuser
        }
        return render(request, 'tablas/LISTAR_CAJAS.html', context)
    

@admin_or_special_required
def crear_caja(request):
    formulario= Cajaform(request.POST or None, request.FILES or None)
    if formulario.is_valid():
        formulario.save()
        return redirect('cajas')
    return render(request, 'tablas/htmlbase/crear_caja.html', {'formulario': formulario})
@admin_or_special_required
def editar_caja(request, id):
    caja = Caja.objects.get(id=id)
    formulario = Cajaform(request.POST or None, request.FILES or None, instance=caja)
    if formulario.is_valid() and request.method == 'POST':
        formulario.save()
        return redirect('cajas')
    return render(request, 'tablas/htmlbase/editar_caja.html', {'formulario': formulario})
@admin_or_special_required
def eliminar_caja(request, id):
    cajas = Caja.objects.get(id=id)
    cajas.delete()
    return redirect('cajas')
@login_required
@any_employee_required
@transaction.atomic
def cerrar_caja(request):
    if request.method == 'POST':
        try:
            # Obtener la caja actual con select_for_update
            caja_actual = Caja.objects.select_for_update().filter(abierta=True).first()
            
            if not caja_actual:
                return JsonResponse({
                    'success': False,
                    'error': 'No hay una caja abierta para cerrar.'
                })
            
            # Obtener el resumen antes de cerrar
            resumen = caja_actual.get_ventas_resumen()
            print("DEBUG - Resumen obtenido:", resumen)  # Agregar log
            
            # Cerrar la caja
            caja_actual.abierta = False
            caja_actual.fecha_hs_cier = timezone.now()
            caja_actual.total_ing = resumen['total']
            caja_actual.save(update_fields=['abierta', 'fecha_hs_cier', 'total_ing'])
            
            # Crear el objeto de respuesta y verificar sus valores
            respuesta = {
                'success': True,
                'resumen': {
                    'efectivo': float(resumen.get('Efectivo', 0)),
                    'tarjeta_debito': float(resumen.get('Tarjeta debito', 0)),
                    'transferencia': float(resumen.get('Transferencia', 0)),
                    'total': float(resumen.get('total', 0))
                }
            }
            print("DEBUG - Respuesta JSON:", respuesta)  # Agregar log
            return JsonResponse(respuesta)
            
        except Exception as e:
            print("DEBUG - Error:", str(e))  # Agregar log
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    })

##################################----LOGIN----#######################################
@login_required
def inicio(request):
    return render(request, 'paginas/menu_p.html')

def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('menu_p')
    else:
        return redirect('login')
def exit(request):
    logout(request)
    return redirect('inicio')

def menu_p(request):
    return render(request, 'paginas/menu_p.html')
##################################----APERTURA----#######################################
@login_required
@any_employee_required
def apertura_caja(request):
    if request.method == 'POST':
        monto_inicial = request.POST.get('monto_inicial')
        
        if monto_inicial and Decimal(monto_inicial) > 0:
            try:
                empleado = Empleado.objects.get(user=request.user)
                sucursal = Sucursal.objects.get(id=1)

                # Verificar si ya existe una caja abierta
                caja_abierta = Caja.objects.filter(abierta=True).first()

                if caja_abierta:
                    # Si la caja está abierta, cerrarla
                    caja_abierta.abierta = False
                    caja_abierta.fecha_hs_cier = timezone.now()
                    caja_abierta.save()

                # Crear una nueva caja
                caja = Caja(
                    nombre='Caja 1',
                    empleado=empleado,
                    sucursal=sucursal,
                    abierta=True,
                    fecha_hs_ap=timezone.now(),
                    fecha_hs_cier=None,
                    monto_ini=float(monto_inicial),
                    total_ing=0,
                    total_egr=0,
                )
                caja.save()
                return redirect('nueva_venta')

            except Exception as e:
                messages.error(request, f"Error al abrir la caja: {str(e)}")
        else:
            messages.error(request, "Por favor, ingrese un monto inicial válido.")
    
    return render(request, 'paginas/menu_p.html')





def stock(request):
    pass

@admin_or_special_required
def vista_registros(request):
    return render(request, 'paginas/registros.html')

@login_required
@any_employee_required
def agregarcosas(request):
    if request.method == 'POST':
        logger.debug(f"POST data: {request.POST}")
        logger.debug(f"GET data: {request.GET}")
        
        form_type = request.GET.get('form_type')
        logger.debug(f"Form type: {form_type}")
        
        formulario = None
        redirect_url = None

        if form_type == 'animal':
            formulario = Animalform(request.POST)
            redirect_url = reverse('animales')
        elif form_type == 'marca':
            formulario = Marcaform(request.POST)
            redirect_url = reverse('marcas')
        elif form_type == 'categoria':
            formulario = Categoriaform(request.POST)
            redirect_url = reverse('categorias')
        elif form_type == 'tamaño':
            formulario = Tamañoform(request.POST)
            redirect_url = reverse('tamaños')
        elif form_type == 'edad':
            formulario = Edadform(request.POST)
            redirect_url = reverse('edades')
        elif form_type == 'consistencia':
            formulario = Consistenciaform(request.POST)
            redirect_url = reverse('consistencias')

        if formulario:
            if formulario.is_valid():
                try:
                    formulario.save()
                    return JsonResponse({
                        'success': True,
                        'type': form_type.capitalize(),
                        'redirect_url': redirect_url
                    })
                except Exception as e:
                    logger.error(f"Error saving {form_type}: {str(e)}")
                    return JsonResponse({'success': False, 'errors': str(e)}, status=500)
            else:
                logger.error(f"Form errors: {formulario.errors}")
                return JsonResponse({'success': False, 'errors': formulario.errors}, status=400)
        else:
            logger.error(f"Invalid form type: {form_type}")
            return JsonResponse({'success': False, 'errors': 'Invalid form type'}, status=400)


    # Rest of the view function remains the same
    marca_form = Marcaform()
    categoria_form = Categoriaform()
    tamaño_form = Tamañoform()
    edad_form = Edadform()
    animal_form = Animalform()
    consistencia_form = Consistenciaform()

    form_type = request.GET.get('form_type')
    if form_type == 'marca':
        form_to_display = marca_form
    elif form_type == 'categoria':
        form_to_display = categoria_form
    elif form_type == 'tamaño':
        form_to_display = tamaño_form
    elif form_type == 'edad':
        form_to_display = edad_form
    elif form_type == 'animal':
        form_to_display = animal_form
    elif form_type == 'consistencia':
        form_to_display = consistencia_form
    else:
        form_to_display = None

    return render(request, 'tablas/agregar.html', {
        'form_to_display': form_to_display,
        'marca_form': marca_form,
        'categoria_form': categoria_form,
        'tamaño_form': tamaño_form,
        'edad_form': edad_form,
        'animal_form': animal_form,
        'consistencia_form': consistencia_form,
    })
##################################----VENTAS----#######################################
@login_required
@any_employee_required
def ventas(request):
    ventas_list = Venta.objects.all().order_by('-fecha_venta', '-hora_venta')
    
    # Actualiza la zona horaria si es necesario
    for venta in ventas_list:
        venta.hora_venta = timezone.localtime(
            timezone.make_aware(
                datetime.combine(venta.fecha_venta, venta.hora_venta)
            )
        ).time()
    
    paginator = Paginator(ventas_list, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj
    }
    return render(request, 'tablas/LISTAR_VENTAS.html', context)
@admin_or_special_required
def crear_ventas(request):
    formulario = Ventaform(request.POST or None, request.FILES or None)
    if formulario.is_valid():
        formulario.save()
        return redirect('ventas')
    return render(request, 'tablas/htmlbase/crear_venta.html', {'formulario': formulario})
@admin_or_special_required
def editar_venta(request, id):
    venta = get_object_or_404(Venta, id=id)
    formulario = Ventaform(request.POST or None, request.FILES or None, instance=venta)
    if formulario.is_valid() and request.method == 'POST':
        formulario.save()
        return redirect('ventas')
    return render(request, 'tablas/htmlbase/editar_venta.html', {'formulario': formulario})
@admin_or_special_required
def eliminar_venta(request, id):
    venta = get_object_or_404(Venta, id=id)
    venta.delete()
    return redirect('ventas')
@any_employee_required
def cancelar_venta(request, id):
    venta = get_object_or_404(Venta, id=id)

    # Verificar si el usuario tiene el permiso de cancelar
    if not request.user.has_perm('app_name.cancelar_venta'):
        messages.error(request, 'No tienes permiso para cancelar esta venta.')
        return redirect('ventas')

    # Intentar cancelar la venta y actualizar el stock
    try:
        # Cambiar el estado de la venta a 'cancelada'
        venta.cancelar_venta()

        # Actualizar el stock de los productos
        detalles = DetalleVenta.objects.filter(venta=venta)
        for detalle in detalles:
            producto = detalle.producto
            producto.stock_a += detalle.cantidad  # Añadir la cantidad al stock
            producto.save()

        messages.success(request, f'Venta #{id} cancelada exitosamente. El stock ha sido actualizado.')
    except Exception as e:
        messages.error(request, f'Error al cancelar la venta: {str(e)}')

    return redirect('ventas')

@any_employee_required
def cambiar_estado_venta(request, id):
    venta = get_object_or_404(Venta, id=id)
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        try:
            venta.cambiar_estado(nuevo_estado)

            if nuevo_estado == 'pagada':
                print(f"Total de venta: {venta.total_venta}")  # Debug
                if venta.total_venta:  
                    caja = venta.caja  
                    print(f"Total de ingresos antes: {caja.total_ing}")  # Debug
                    caja.total_ing += venta.total_venta
                    try:
                        caja.save()  
                        print(f"Total de ingresos después: {caja.total_ing}")  # Debug
                    except Exception as e:
                        print(f"Error al guardar la caja: {e}")  # Manejar error

            messages.success(request, f'Estado de la venta #{id} actualizado a {nuevo_estado}.')
        except ValueError:
            messages.error(request, 'Estado no válido.')
    return redirect('ventas')




##################################----DETALLES----#######################################

@login_required
@any_employee_required
def detalles(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)
    detalles = DetalleVenta.objects.filter(venta=venta)
    
    # Obtener estados disponibles según el estado actual
    if venta.estado == 'pagada' or venta.estado == 'cancelada':
        estados = [(venta.estado, venta.get_estado_display())]
    else:
        estados = venta.ESTADO_CHOICES

    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        if nuevo_estado and nuevo_estado != venta.estado:
            try:
                with transaction.atomic():
                    if nuevo_estado == 'pagada':
                        venta.estado = 'pagada'
                        venta.save(update_fields=['estado'])
                        # Actualizar la caja
                        if venta.caja and venta.caja.abierta:
                            if venta.caja.total_ing is None:
                                venta.caja.total_ing = Decimal('0')
                            venta.caja.total_ing += venta.total_venta
                            venta.caja.save()
                        messages.success(request, 'Venta marcada como pagada.')
                    
                    elif nuevo_estado == 'cancelada':
                        # Restaurar stock para cada producto
                        for detalle in detalles:
                            producto = detalle.producto
                            producto.stock_a += detalle.cantidad
                            producto.save()
                        
                        # Si la venta estaba pagada, ajustar la caja
                        if venta.estado == 'pagada' and venta.caja and venta.caja.abierta:
                            venta.caja.total_ing -= venta.total_venta
                            venta.caja.save()
                        
                        venta.estado = 'cancelada'
                        venta.save(update_fields=['estado'])
                        messages.success(request, 'Venta cancelada y stock restaurado.')
                    
                    elif nuevo_estado == 'pendiente' and venta.estado not in ['pagada', 'cancelada']:
                        venta.estado = 'pendiente'
                        venta.save(update_fields=['estado'])
                        messages.success(request, 'Estado actualizado a pendiente.')
                    
            except Exception as e:
                messages.error(request, f'Error al actualizar el estado: {str(e)}')
                print(f"Error en detalles view: {e}")
        
        return redirect('detalles', venta_id=venta_id)

    # Calcular totales
    subtotal = sum(detalle.subtotal for detalle in detalles)
    monto_descuento = (subtotal * Decimal(venta.descuento)) / Decimal(100)
    total_final = subtotal - monto_descuento

    context = {
        'venta': venta,
        'detalles': detalles,
        'estados': estados,
        'subtotal': subtotal,
        'monto_descuento': monto_descuento,
        'total_final': total_final,
    }
    
    return render(request, 'tablas/LISTAR_DETALLES.html', context)


@admin_or_special_required
def crear_detalles(request):
    formulario= DetalleVentaform(request.POST or None, request.FILES or None)
    if formulario.is_valid():
        formulario.save()
        return redirect('detalles')
    return render(request, 'tablas/htmlbase/crear_detalle.html', {'formulario': formulario})
@admin_or_special_required
def editar_detalle(request, id):
    detalle = DetalleVenta.objects.get(id=id)
    formulario = DetalleVentaform(request.POST or None, request.FILES or None, instance=detalle)
    if formulario.is_valid() and request.method == 'POST':
        formulario.save()
        return redirect('detalles')
    return render(request, 'tablas/htmlbase/editar_detalle.html', {'formulario': formulario})
@admin_or_special_required
def eliminar_detalle(request, id):
    detalles = DetalleVenta.objects.get(id=id)
    detalles.delete()
    return redirect('detalles')


@csrf_exempt
@transaction.atomic
# Modificación en views.py para la función nueva_venta
@any_employee_required
def nueva_venta(request):
    caja_actual = Caja.objects.filter(abierta=True).first()

    if request.method == 'POST' and request.POST.get('cerrar_caja') == 'true':
        try:
            # Obtener la caja actual con select_for_update
            caja_actual = Caja.objects.select_for_update().filter(abierta=True).first()
            
            if not caja_actual:
                return JsonResponse({
                    'success': False,
                    'error': 'No hay una caja abierta para cerrar.'
                })
            
            # Obtener el resumen antes de cerrar
            resumen = caja_actual.get_ventas_resumen()
            print("DEBUG - Resumen obtenido:", resumen)  # Para debug
            
            # Cerrar la caja
            caja_actual.abierta = False
            caja_actual.fecha_hs_cier = timezone.now()
            caja_actual.total_ing = resumen['total']
            caja_actual.save(update_fields=['abierta', 'fecha_hs_cier', 'total_ing'])
            
            # Usamos las claves exactas que devuelve get_ventas_resumen
            return JsonResponse({
            'success': True,
            'resumen': {
                'efectivo': float(resumen[Venta.EFECTIVO]),
                'tarjeta_debito': float(resumen[Venta.TARJETA_DEBITO]),
                'transferencia': float(resumen[Venta.TRANSFERENCIA]),
                'total': float(resumen['total'])
            }
        })
            
            
        except Exception as e:
            print(f"DEBUG - Error al cerrar caja: {str(e)}")  # Para debug
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Verificar caja abierta primero
            caja_actual = Caja.objects.select_for_update().filter(abierta=True).first()
            if not caja_actual:
                return JsonResponse({'success': False, 'error': 'No hay una caja abierta.'}, status=400)

            with transaction.atomic():
                now = timezone.localtime(timezone.now())
                # Crear la venta con los datos básicos
                venta = Venta(
                    cliente_id=1,
                    caja=caja_actual,
                    fecha_venta=now.date(),
                    hora_venta=now.time(),
                    total_venta=Decimal('0'),  # Inicializar en 0
                    metodo_pago=data['metodo_pago'],
                    estado='pagada' if data.get('pagada', False) else 'pendiente',
                    descuento=data.get('descuento', 0)
                )
                # Guardar la venta primero
                venta.save()
                
                total_venta = Decimal('0')
                
                # Procesar los productos y calcular el total
                for producto_data in data.get('productos', []):
                    if producto_data.get('es_suelto'):
                        monto_venta = Decimal(str(producto_data['monto_venta']))
                        bolsa = BolsaAbierta.objects.select_for_update().get(id=producto_data['bolsa_id'])
                        
                        if bolsa.precio_restante < monto_venta:
                            raise ValueError(f'Monto insuficiente en la bolsa para el producto {producto_data["nombre"]}')
                        
                        DetalleVenta.objects.create(
                            venta=venta,
                            producto_id=producto_data['id'],
                            cantidad=1,
                            precio_unitario=monto_venta,
                            subtotal=monto_venta,
                            es_suelto=True
                        )
                        
                        bolsa.vender(monto_venta)
                        total_venta += monto_venta
                        
                    else:
                        cantidad = Decimal(str(producto_data['cantidad']))
                        precio = Decimal(str(producto_data['precio']))
                        subtotal = precio * cantidad
                        producto = Producto.objects.select_for_update().get(id=producto_data['id'])
                        
                        if producto.stock_a < cantidad:
                            raise ValueError(f'Stock insuficiente para el producto {producto.nombre}')
                        
                        DetalleVenta.objects.create(
                            venta=venta,
                            producto=producto,
                            cantidad=cantidad,
                            precio_unitario=precio,
                            subtotal=subtotal,
                            es_suelto=False
                        )
                        
                        producto.stock_a -= cantidad
                        producto.save()
                        total_venta += subtotal
                
                # Calcular descuento
                if venta.descuento > 0:
                    descuento = (total_venta * Decimal(venta.descuento)) / Decimal(100)
                    total_venta -= descuento
                
                # Actualizar el total de la venta
                venta.total_venta = total_venta
                venta.save()

                # Actualizar caja si la venta está pagada
                if data.get('pagada', False):
                    if caja_actual.total_ing is None:
                        caja_actual.total_ing = Decimal('0')
                    caja_actual.total_ing += total_venta
                    caja_actual.save()

                return JsonResponse({
                    'success': True,
                    'message': f'Venta #{venta.id} creada exitosamente'
                })

        except Exception as e:
            transaction.set_rollback(True)
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

    return render(request, 'paginas/nueva_venta.html', {'caja_abierta': Caja.objects.filter(abierta=True).exists()})
@any_employee_required
def buscar_producto(request):
    """
    Búsqueda de productos adaptada a la estructura específica de los modelos
    """
    try:
        query = request.GET.get('q', '').strip()
        logger.info(f"Búsqueda recibida: '{query}'")

        if not query:
            return JsonResponse([], safe=False)

        keywords = [word.strip() for word in query.split() if word.strip()]

        # Comenzar con una consulta base
        productos = Producto.objects.select_related(
            'categoria',
            'animal',
            'marca',
            'edad',
            'tamaño',
            'consis'
        )

        # Construir filtro para cada palabra clave
        for keyword in keywords:
            productos = productos.filter(
                Q(nombre__icontains=keyword) |
                Q(categoria__categoria__icontains=keyword) |  # Usando el campo correcto
                Q(animal__animal__icontains=keyword) |       # Usando el campo correcto
                Q(marca__marca__icontains=keyword) |         # Usando el campo correcto
                Q(edad__edad__icontains=keyword) |           # Usando el campo correcto
                Q(des__icontains=keyword) |
                Q(obs__icontains=keyword)
            ).distinct()

        # Limitar resultados
        productos = productos[:10]

        # Preparar datos para la respuesta
        data = []
        for producto in productos:
            try:
                # Construir nombre completo del producto
                nombre_parts = []

                # Agregar cada parte del nombre si existe
                if producto.categoria:
                    nombre_parts.append(producto.categoria.categoria)
                if producto.animal:
                    nombre_parts.append(f"para {producto.animal.animal}")
                if producto.nombre:
                    nombre_parts.append(producto.nombre)
                if producto.edad:
                    nombre_parts.append(producto.edad.edad)
                if producto.marca:
                    nombre_parts.append(producto.marca.marca)
                if producto.peso:
                    nombre_parts.append(f"x {producto.peso} Kg")
                if producto.tamaño:
                    nombre_parts.append(producto.tamaño.tamaño)
                if producto.consis:
                    nombre_parts.append(producto.consis.consistencia)

                # Crear diccionario del producto
                producto_dict = {
                    'id': producto.id,
                    'nombre': ' '.join(filter(None, nombre_parts)),
                    'precio': str(producto.precio),
                    'stock': producto.stock_a,
                    'descripcion': producto.des if producto.des else ''
                }
                data.append(producto_dict)

            except Exception as e:
                logger.error(f"Error procesando producto {producto.id}: {str(e)}")
                continue

        return JsonResponse(data, safe=False)

    except Exception as e:
        logger.error(f"Error en la búsqueda: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': 'Error al buscar productos',
            'detail': str(e)
        }, status=500)

# VENTASSSSS
@any_employee_required
@require_GET
def obtener_productos(request):
    animal_nombre = request.GET.get('animal')
    categoria_nombre = request.GET.get('categoria')

    # Si no se proporcionan parámetros, devolver todos los productos
    if not animal_nombre and not categoria_nombre:
        productos = Producto.objects.all()
    elif animal_nombre and categoria_nombre:
        try:
            animal = Animal.objects.get(animal=animal_nombre)
            categoria = Categoria.objects.get(categoria=categoria_nombre)
            productos = Producto.objects.filter(animal=animal, categoria=categoria)
        except (Animal.DoesNotExist, Categoria.DoesNotExist):
            return JsonResponse({'error': 'Animal o categoría no encontrada'}, status=404)
    else:
        return JsonResponse({'error': 'Parámetros incompletos'}, status=400)

    productos_list = [
        {
            'id': producto.id,
            'nombre': producto.nombre,
            'marca': producto.marca.marca if producto.marca else 'Sin marca',
            'peso': f"{producto.peso} Kg" if producto.peso else 'N/A',
            'precio': float(producto.precio),
            'stock': producto.stock_a,
            'obs': producto.obs if not producto.peso else None
        } for producto in productos
    ]
    
    return JsonResponse(productos_list, safe=False)


@any_employee_required
@require_http_methods(["GET"])
def obtener_productos_sueltos(request):
    try:
        animal = request.GET.get('animal')
        if not animal:
            return JsonResponse({'error': 'Se requiere especificar un animal'}, status=400)

        productos = Producto.objects.filter(animal__animal=animal, peso__gte=15)
        
        productos_list = [{
            'id': p.id,
            'nombre': p.nombre,
            'marca': p.marca.marca if p.marca else 'Sin marca',
            'animal': p.animal.animal,
            'peso': f"{p.peso} Kg" if p.peso else 'N/A',
            'precio': float(p.precio)
        } for p in productos]
        
        return JsonResponse(productos_list, safe=False)
    except Exception as e:
        # Log the error for debugging
        import logging
        logging.error(f"Error en obtener_productos_sueltos: {str(e)}")
        return JsonResponse({'error': 'Ocurrió un error interno'}, status=500)
@admin_or_special_required
def bolsas(request):
    bolsas = BolsaAbierta.objects.all().order_by('id')
    return render(request, 'tablas/LISTAR_BOLSAS.html', {'bolsas': bolsas})
@any_employee_required
@require_http_methods(["GET"])
def obtener_bolsas_abiertas(request):
    try:
        animal = request.GET.get('animal')
        logging.info(f"Obteniendo bolsas abiertas para animal: {animal}")
        
        bolsas = BolsaAbierta.objects.filter(producto__animal__animal=animal, esta_abierta=True)
        logging.info(f"Número de bolsas encontradas: {bolsas.count()}")
        
        bolsas_data = [bolsa.to_dict() for bolsa in bolsas]
        
        return JsonResponse(bolsas_data, safe=False)
    except Exception as e:
        logging.error(f"Error en obtener_bolsas_abiertas: {str(e)}")
        return JsonResponse({'error': 'Ocurrió un error interno'}, status=500)
    
@any_employee_required
@require_http_methods(["POST"])
@transaction.atomic
def cerrar_bolsa(request):
    data = json.loads(request.body)
    bolsa_id = data.get('bolsa_id')

    try:
        bolsa = BolsaAbierta.objects.get(id=bolsa_id, esta_abierta=True)
        bolsa.cerrar_bolsa()
        return JsonResponse({'success': True, 'message': 'Bolsa cerrada exitosamente'})
    except BolsaAbierta.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Bolsa no encontrada o ya está cerrada'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
@any_employee_required
@require_http_methods(["POST"])
@transaction.atomic
def abrir_bolsa(request):
    data = json.loads(request.body)
    producto_id = data.get('producto_id')
    animal_nombre = data.get('animal')
    
    try:
        animal = Animal.objects.get(animal=animal_nombre)
        producto = Producto.objects.get(id=producto_id, animal=animal)
        
        # Verificar si hay stock disponible
        if producto.stock_a <= 0:
            return JsonResponse({
                'success': False, 
                'error': 'No hay stock disponible para este producto'
            })
        
        # Verificar si ya existe una bolsa abierta
        bolsa_existente = BolsaAbierta.objects.filter(
            producto=producto,
            esta_abierta=True
        ).first()
        
        if bolsa_existente:
            return JsonResponse({
                'success': False,
                'error': 'Ya existe una bolsa abierta para este producto',
                'bolsa': bolsa_existente.to_dict()  # Devolver información de la bolsa existente
            })
        
        # Crear nueva bolsa
        bolsa = BolsaAbierta.abrir_bolsa(producto, producto.precio)
        
        # Solo descontar stock si es una bolsa nueva
        if bolsa.precio_restante == producto.precio and bolsa.monto_vendido == 0:
            producto.stock_a -= 1
            producto.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Bolsa abierta exitosamente',
            'bolsa': bolsa.to_dict()
        })
        
    except Animal.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'error': f'Animal "{animal_nombre}" no encontrado'
        })
    except Producto.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'error': 'Producto no encontrado para el animal seleccionado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': f'Error inesperado: {str(e)}'
        })
    
@any_employee_required   
@require_http_methods(["POST"])
@transaction.atomic
def devolver_monto_bolsa(request):
    data = json.loads(request.body)
    bolsa_id = data.get('bolsa_id')
    monto = Decimal(data.get('monto'))

    try:
        bolsa = BolsaAbierta.objects.get(id=bolsa_id)
        bolsa.precio_restante += monto
        bolsa.save()
        return JsonResponse({'success': True})
    except BolsaAbierta.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Bolsa no encontrada'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@any_employee_required
@require_http_methods(["POST"])
@transaction.atomic
def vender_suelto(request):
    data = json.loads(request.body)
    bolsa_id = data.get('bolsa_id')
    monto_venta = Decimal(data.get('monto'))

    try:
        bolsa = BolsaAbierta.objects.get(id=bolsa_id)

        if bolsa.precio_restante < monto_venta and not bolsa.en_ultimo_50_porciento:
            return JsonResponse({'success': False, 'error': 'Monto insuficiente en la bolsa'})

        # Crear un nombre especial para productos sueltos que mantenga el identificador
        nombre_suelto = bolsa.producto.nombre
        if not nombre_suelto.endswith('(Suelto)'):
            nombre_suelto = f"{bolsa.producto.nombre} (Suelto)"

        response_data = {
            'success': True,
            'producto': {
                'id': bolsa.producto.id,
                'nombre': nombre_suelto,  # Usar el nombre con (Suelto)
                'precio': float(monto_venta),
                'stock': 1,
                'bolsa_id': bolsa.id,
                'monto_venta': float(monto_venta),
                'monto_vendido': float(bolsa.monto_vendido),
                'es_suelto': True  # Agregar un identificador explícito
            },
            'en_ultimo_50_porciento': bolsa.en_ultimo_50_porciento
        }

        return JsonResponse(response_data)

    except BolsaAbierta.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Bolsa no encontrada'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
@any_employee_required    
@require_http_methods(["GET"])
def verificar_ultimo_50_porciento(request, bolsa_id):
    try:
        bolsa = BolsaAbierta.objects.get(id=bolsa_id, esta_abierta=True)
        en_ultimo_50_porciento = bolsa.en_ultimo_50_porciento()
        return JsonResponse({'en_ultimo_50_porciento': en_ultimo_50_porciento})
    except BolsaAbierta.DoesNotExist:
        return JsonResponse({'error': 'Bolsa no encontrada o ya está cerrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    




#graficos#

def obtener_ventas_diarias(fecha_inicio, fecha_fin):
    """Función auxiliar para obtener datos de ventas diarias"""
    ventas = Venta.objects.filter(
        fecha_venta__range=(fecha_inicio, fecha_fin),
        estado='pagada'
    ).values('fecha_venta').annotate(
        total=Sum('total_venta')
    ).order_by('fecha_venta')
    
    # Crear diccionario para búsqueda O(1)
    dict_ventas = {
        venta['fecha_venta']: float(venta['total'])
        for venta in ventas
    }
    
    # Generar rango de fechas continuo
    fechas = []
    montos = []
    fecha_actual = fecha_inicio
    while fecha_actual <= fecha_fin:
        fechas.append(fecha_actual.strftime('%d/%m'))
        montos.append(dict_ventas.get(fecha_actual, 0))
        fecha_actual += timedelta(days=1)
        
    return {'labels': fechas, 'data': montos}

def obtener_ventas_semanales(semanas=4):
    """Función auxiliar para obtener datos de ventas semanales"""
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(weeks=semanas)
    
    ventas = Venta.objects.filter(
        fecha_venta__range=(fecha_inicio, fecha_fin),
        estado='pagada'
    ).values('fecha_venta__week', 'fecha_venta__year').annotate(
        total=Sum('total_venta')
    ).order_by('fecha_venta__year', 'fecha_venta__week')
    
    return {
        'labels': [f"Semana {venta['fecha_venta__week']}" for venta in ventas],
        'data': [float(venta['total']) for venta in ventas]
    }


def obtener_ventas_mensuales(meses=6):
    """Función auxiliar para obtener datos de ventas mensuales"""
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30*meses)
    
    meses_esp = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    ventas = Venta.objects.filter(
        fecha_venta__range=(fecha_inicio, fecha_fin),
        estado='pagada'
    ).values('fecha_venta__month', 'fecha_venta__year').annotate(
        total=Sum('total_venta')
    ).order_by('fecha_venta__year', 'fecha_venta__month')
    
    return {
        'labels': [meses_esp[venta['fecha_venta__month']] for venta in ventas],
        'data': [float(venta['total']) for venta in ventas]
    }

def obtener_marcas_vendidas():
    """Función auxiliar para obtener datos de marcas más vendidas"""
    marcas = DetalleVenta.objects.filter(
        venta__estado='pagada'
    ).values(
        'producto__marca__marca'  # Accedemos al nombre de la marca a través de la relación
    ).annotate(
        total=Sum(F('cantidad') * F('precio_unitario')),
        cantidad=Sum('cantidad')
    ).exclude(
        producto__marca__isnull=True
    ).order_by('-total')[:5]
    
    return {
        'labels': [marca['producto__marca__marca'] for marca in marcas],
        'data': [float(marca['total']) for marca in marcas],
        'cantidades': [int(marca['cantidad']) for marca in marcas]
    }

def obtener_top_sueltos():
    """Función auxiliar para obtener datos de alimentos sueltos más vendidos"""
    sueltos = DetalleVenta.objects.filter(
        venta__estado='pagada',
        es_suelto=True
    ).values(
        'producto__nombre',
        'producto__marca__marca'
    ).annotate(
        total_vendido=Sum(F('cantidad') * F('precio_unitario'))
    ).order_by('-total_vendido')[:5]
    
    # Formatear las etiquetas para incluir marca y nombre
    labels = []
    datos = []
    
    for suelto in sueltos:
        # Formatear la etiqueta: "Marca - Nombre"
        label = f"{suelto['producto__marca__marca']} - {suelto['producto__nombre']}"
        labels.append(label)
        datos.append(float(suelto['total_vendido']))
    
    return {
        'labels': labels,
        'data': datos
    }

@admin_or_special_required
@login_required
def dashboard_completo(request):
    """Vista principal del dashboard con manejo de errores"""
    try:
        hoy = timezone.now().date()
        hace_una_semana = hoy - timedelta(days=7)
        inicio_mes = hoy.replace(day=1)
        
        # Obtener datos usando las funciones auxiliares
        datos_diarios = obtener_ventas_diarias(hace_una_semana, hoy)
        datos_semanales = obtener_ventas_semanales()
        datos_mensuales = obtener_ventas_mensuales()
        datos_marcas = obtener_marcas_vendidas()
        datos_sueltos = obtener_top_sueltos()
        
        # Obtener queryset filtrado para ventas pagadas
        ventas_pagadas = Venta.objects.filter(estado='pagada')
        
        # Calcular métricas del mes actual
        ventas_mes = ventas_pagadas.filter(fecha_venta__gte=inicio_mes)
        total_mes = ventas_mes.aggregate(total=Sum('total_venta'))['total'] or 0
        
        # Calcular promedio diario de la última semana
        ventas_semana = ventas_pagadas.filter(fecha_venta__gte=hace_una_semana)
        promedio_diario = ventas_semana.aggregate(
            promedio=Avg('total_venta')
        )['promedio'] or 0

        context = {
            'ventas_diarias_json': json.dumps(datos_diarios, cls=DjangoJSONEncoder),
            'ventas_semanales_json': json.dumps(datos_semanales, cls=DjangoJSONEncoder),
            'ventas_mensuales_json': json.dumps(datos_mensuales, cls=DjangoJSONEncoder),
            'ventas_marcas_json': json.dumps(datos_marcas, cls=DjangoJSONEncoder),
            'ventas_sueltos_json': json.dumps(datos_sueltos, cls=DjangoJSONEncoder),
            'total_ventas': total_mes,
            'promedio_diario': promedio_diario
        }
        
        return render(request, 'tablas/graficos.html', context)
    except Exception as e:
        print(f"Error en dashboard: {str(e)}")
        print(traceback.format_exc())
        return redirect('registros')
    


##CAMBIAR CONTRASEÑAS Y ROELS ####

# views.py
@admin_required
@login_required
def cambiar_password_empleado(request, empleado_id):
    try:
        empleado = Empleado.objects.select_related('user').get(id=empleado_id)
        
        if request.method == 'POST':
            nueva_password = request.POST.get('nueva_password')
            confirmar_password = request.POST.get('confirmar_password')
            
            if not nueva_password or not confirmar_password:
                messages.error(request, 'Ambos campos de contraseña son requeridos.')
                return redirect('cambiar_password_empleado', empleado_id=empleado_id)
                
            if nueva_password != confirmar_password:
                messages.error(request, 'Las contraseñas no coinciden.')
                return redirect('cambiar_password_empleado', empleado_id=empleado_id)
                
            if len(nueva_password) < 8:
                messages.error(request, 'La contraseña debe tener al menos 8 caracteres.')
                return redirect('cambiar_password_empleado', empleado_id=empleado_id)
            
            empleado.user.password = make_password(nueva_password)
            empleado.user.save()
            
            messages.success(request, f'Contraseña actualizada exitosamente para {empleado.nombre}')
            return redirect('empleados')
            
        return render(request, 'tablas/cambiar_password.html', {
            'empleado': empleado
        })
        
    except Empleado.DoesNotExist:
        messages.error(request, 'Empleado no encontrado.')
        return redirect('empleados')

@admin_required 
@login_required
def cambiar_rol_empleado(request, empleado_id):
    try:
        empleado = Empleado.objects.select_related('user').get(id=empleado_id)
        
        # Verificar si el usuario es superadmin
        if empleado.user.is_superuser:
            messages.error(request, 'No se puede modificar el rol de un superadministrador.')
            return redirect('empleados')
        
        if request.method == 'POST':
            nuevo_rol = request.POST.get('nuevo_rol')
            
            if nuevo_rol not in ['regular', 'especial']:
                messages.error(request, 'Rol inválido seleccionado.')
                return redirect('cambiar_rol_empleado', empleado_id=empleado_id)
            
            grupos = {
                'regular': 'Empleados Regulares',
                'especial': 'Empleados Especiales'
            }
            
            with transaction.atomic():
                # Remover de grupos actuales (excepto admin)
                for grupo in empleado.user.groups.all():
                    if grupo.name in grupos.values():
                        empleado.user.groups.remove(grupo)
                
                # Añadir al nuevo grupo
                nuevo_grupo = Group.objects.get(name=grupos[nuevo_rol])
                empleado.user.groups.add(nuevo_grupo)
                
                messages.success(
                    request,
                    f'Rol actualizado exitosamente para {empleado.nombre} a {grupos[nuevo_rol]}'
                )
                return redirect('empleados')
        
        context = {
            'empleado': empleado,
            'rol_actual': 'especial' if empleado.user.groups.filter(
                name='Empleados Especiales'
            ).exists() else 'regular'
        }
        return render(request, 'tablas/cambiar_rol.html', context)
        
    except Empleado.DoesNotExist:
        messages.error(request, 'Empleado no encontrado.')
        return redirect('empleados')
    



#### DESCONTAR STOCK"""###
def descontar_stock_helper(producto_id, cantidad, motivo, usuario, observacion=''):
    try:
        with transaction.atomic():
            producto = Producto.objects.select_for_update().get(id=producto_id)
            
            if producto.stock_a < cantidad:
                raise ValueError("Stock insuficiente")
                
            producto.stock_a -= cantidad
            producto.save()
            
            MovimientoStock.objects.create(
                producto=producto,
                cantidad=cantidad,
                motivo=motivo,
                observacion=observacion,
                usuario=usuario
            )
            
            return True
                
    except Exception as e:
        return False

# views.py

@require_http_methods(["POST"])
@admin_or_special_required
def descontar_stock(request):
    try:
        producto_id = int(request.POST.get('producto_id'))
        cantidad = int(request.POST.get('cantidad'))
        motivo = request.POST.get('motivo')
        observacion = request.POST.get('observacion', '')

        # Validar datos
        if not all([producto_id, cantidad, motivo]):
            return JsonResponse({
                'success': False, 
                'error': 'Faltan datos requeridos'
            })

        with transaction.atomic():
            producto = Producto.objects.select_for_update().get(id=producto_id)
            
            if producto.stock_a < cantidad:
                return JsonResponse({
                    'success': False,
                    'error': f'Stock insuficiente. Stock actual: {producto.stock_a}'
                })
            
            producto.stock_a -= cantidad
            producto.save()
            
            MovimientoStock.objects.create(
                producto=producto,
                cantidad=cantidad,
                motivo=motivo,
                observacion=observacion,
                usuario=request.user
            )
            
            return JsonResponse({'success': True})
            
    except Producto.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Producto no encontrado'
        })
    except Exception as e:
        print(f"Error al descontar stock: {str(e)}")  # Para debugging
        return JsonResponse({
            'success': False,
            'error': 'Error al descontar el stock'
        })
@admin_or_special_required
def lista_movimientos(request):
    try:
        # Obtener los filtros de la URL
        search = request.GET.get('search', '').strip()
        fecha = request.GET.get('fecha')
        motivo = request.GET.get('motivo')

        # Iniciar el queryset
        movimientos = MovimientoStock.objects.all().order_by('-fecha')

        # Aplicar filtros
        if search:
            movimientos = movimientos.filter(
                Q(producto__nombre__icontains=search) |
                Q(producto__marca__nombre__icontains=search) |
                Q(producto__categoria__nombre__icontains=search) |
                Q(producto__animal__icontains=search)
            )

        if fecha:
            # Convertir a datetime y filtrar por ese día específico
            fecha_filtro = datetime.strptime(fecha, '%Y-%m-%d')
            fecha_inicio = make_aware(datetime.combine(fecha_filtro, time.min))
            fecha_fin = make_aware(datetime.combine(fecha_filtro, time.max))
            movimientos = movimientos.filter(fecha__range=(fecha_inicio, fecha_fin))

        if motivo:
            movimientos = movimientos.filter(motivo=motivo)

        # Paginación
        items_por_pagina = 10
        paginator = Paginator(movimientos, items_por_pagina)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        # Preparar contexto
        context = {
            'movimientos': page_obj,
            'form': {'MOTIVOS': MovimientoStock.MOTIVOS},
            'filtros_aplicados': {
                'search': search,
                'fecha': fecha,
                'motivo': motivo
            }
        }

        return render(request, 'tablas/LISTAR_DESCONTARSTOCK.html', context)

    except ValueError as e:
        context = {
            'movimientos': MovimientoStock.objects.none(),
            'form': {'MOTIVOS': MovimientoStock.MOTIVOS},
            'error': 'Error en el formato de fecha'
        }
        return render(request, 'tablas/LISTAR_DESCONTARSTOCK.html', context)

    except Exception as e:
        context = {
            'movimientos': MovimientoStock.objects.none(),
            'form': {'MOTIVOS': MovimientoStock.MOTIVOS},
            'error': 'Error al procesar la solicitud'
        }
        return render(request, 'tablas/LISTAR_DESCONTARSTOCK.html', context)