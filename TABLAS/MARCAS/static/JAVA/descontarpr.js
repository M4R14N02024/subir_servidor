// Funciones para el modal de descuento
function abrirModalDescuento(productoId) {
    const modal = document.getElementById('modalDescuentoStock');
    modal.dataset.productoId = productoId;
    modal.style.display = 'block';
    
    // Resetear formulario
    document.getElementById('cantidadDescuento').value = '';
    document.getElementById('motivoDescuento').selectedIndex = 0;
    document.getElementById('observacionDescuento').value = '';
}

function cerrarModalDescuento() {
    document.getElementById('modalDescuentoStock').style.display = 'none';
}

function mostrarNotificacion(mensaje, tipo = 'success') {
    const toast = document.getElementById('toastNotification');
    toast.textContent = mensaje;
    toast.style.backgroundColor = tipo === 'success' ? '#4CAF50' : '#f44336';
    toast.style.display = 'block';
    toast.style.opacity = '1';
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
            toast.style.display = 'none';
        }, 300);
    }, 3000);
}

function confirmarDescuento() {
    const modal = document.getElementById('modalDescuentoStock');
    const cantidad = document.getElementById('cantidadDescuento').value;
    const motivo = document.getElementById('motivoDescuento').value;
    const observacion = document.getElementById('observacionDescuento').value;
    
    // Validaciones básicas
    if (!cantidad || cantidad <= 0) {
        mostrarNotificacion('Por favor ingrese una cantidad válida', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('producto_id', modal.dataset.productoId);
    formData.append('cantidad', cantidad);
    formData.append('motivo', motivo);
    formData.append('observacion', observacion);

    fetch('/descontar-stock/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Mostrar notificación de éxito
            mostrarNotificacion('Stock descontado exitosamente', 'success');
            
            // Cerrar el modal
            cerrarModalDescuento();
            
            // Recargar la página después de un breve delay para que se alcance a ver la notificación
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        } else {
            mostrarNotificacion(data.error || 'Error al descontar stock', 'error');
            console.log('Error details:', data);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        mostrarNotificacion('Error al procesar la solicitud', 'error');
    });
}

// Función auxiliar para obtener el token CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Validación de entrada numérica
document.getElementById('cantidadDescuento').addEventListener('input', function() {
    this.value = this.value.replace(/[^\d]/g, '');
    if (parseInt(this.value) > 99) {
        this.value = '99';
    }
});

let searchTimeout;


// Aplicar filtros
function aplicarFiltros() {
    const fecha = document.getElementById('fecha-filtro').value;
    const motivo = document.getElementById('motivo-select').value;
    const search = document.getElementById('search-input').value;
    
    // Construir URL con los filtros
    const params = new URLSearchParams();
    
    // Solo agregar parámetros si tienen valor
    if (search.trim()) params.append('search', search.trim());
    if (fecha) params.append('fecha', fecha);
    if (motivo) params.append('motivo', motivo);
    
    // Redirigir con los filtros aplicados
    const baseUrl = window.location.pathname;
    const queryString = params.toString();
    const finalUrl = baseUrl + (queryString ? `?${queryString}` : '');
    
    window.location.href = finalUrl;
}

// Limpiar filtros
function limpiarFiltros() {
    // Limpiar todos los campos
    document.getElementById('fecha-filtro').value = '';
    document.getElementById('motivo-select').value = '';
    document.getElementById('search-input').value = '';
    
    // Redirigir a la página sin filtros
    window.location.href = window.location.pathname;
}

// Inicializar eventos cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    // Configurar búsqueda con delay
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                aplicarFiltros();
            }, 500);
        });
    }
    
    // Configurar fecha para aplicar filtros al cambiar
    const fechaFiltro = document.getElementById('fecha-filtro');
    if (fechaFiltro) {
        fechaFiltro.addEventListener('change', aplicarFiltros);
    }
    
    // Configurar select de motivo para aplicar filtros al cambiar
    const motivoSelect = document.getElementById('motivo-select');
    if (motivoSelect) {
        motivoSelect.addEventListener('change', aplicarFiltros);
    }
});