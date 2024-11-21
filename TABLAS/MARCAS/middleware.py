from django.shortcuts import redirect
from django.urls import reverse
import re

class LoginRequiredMiddleware:
    """
    Middleware para controlar el acceso a las páginas que requieren autenticación.
    Redirige a la página de login si el usuario no está autenticado.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Patrones de URL que no requieren autenticación
        self.public_patterns = [
            # URLs de autenticación
            re.compile(r'^login/?$'),
            re.compile(r'^logout/?$'),
            re.compile(r'^accounts/login/?$'),
            re.compile(r'^accounts/logout/?$'),
            
            # Admin y autenticación de admin
            re.compile(r'^admin/login/?$'),
            re.compile(r'^admin/logout/?$'),
            re.compile(r'^admin/.*$'),
            
            # Archivos estáticos y media
            re.compile(r'^static/.*$'),
            re.compile(r'^media/.*$'),
            
            # Otras rutas públicas
            re.compile(r'^$'),  # Página principal
            re.compile(r'^favicon\.ico$'),
        ]

    def __call__(self, request):
        # Obtener la ruta actual sin el slash inicial
        path = request.path_info.lstrip('/')
        
        # Si la petición es POST a login, permitirla
        if request.method == 'POST' and path in ['login/', 'login', 'accounts/login/', 'accounts/login']:
            return self.get_response(request)
        
        # Verificar si la ruta coincide con algún patrón público
        if any(pattern.match(path) for pattern in self.public_patterns):
            return self.get_response(request)
        
        # Verificar la autenticación
        if not request.user.is_authenticated:
            # Guardar la URL actual para redirección después del login
            next_url = request.get_full_path()
            login_url = reverse('login')
            
            # Añadir el parámetro next si no es la página de login
            if next_url and next_url != login_url:
                login_url = f'{login_url}?next={next_url}'
            
            return redirect(login_url)
        
        # Usuario autenticado, procesar la solicitud normalmente
        return self.get_response(request)