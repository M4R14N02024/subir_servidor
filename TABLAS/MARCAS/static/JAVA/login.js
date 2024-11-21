document.addEventListener('DOMContentLoaded', function() {
    // Obtener elementos
    const modal = document.getElementById('modalIntentos');
    const closeButton = document.querySelector('.modalIntentos-close');
    const acceptButton = document.querySelector('.modalIntentos-button');
    const usernameInput = document.getElementById('id_username');
    const passwordInput = document.getElementById('id_password');
    const loginForm = document.querySelector('.formulario-inicio-sesion');
    const submitButton = document.querySelector('.boton-iniciar-sesion');

    // Configurar restricciones de entrada
    if (usernameInput) {
        usernameInput.setAttribute('maxlength', '15');
        usernameInput.setAttribute('pattern', '[a-zA-Z0-9]+');
        usernameInput.setAttribute('title', 'Solo se permiten letras y números. Máximo 15 caracteres.');
    }

    if (passwordInput) {
        passwordInput.setAttribute('maxlength', '14');
        passwordInput.setAttribute('pattern', '[a-zA-Z0-9]+');
        passwordInput.setAttribute('title', 'Solo se permiten letras y números. Máximo 14 caracteres.');
    }

    // Función para mostrar el loader
    function mostrarLoader() {
        submitButton.innerHTML = '<span class="loader"></span>';
        submitButton.disabled = true;
    }

    // Función para ocultar el loader
    function ocultarLoader() {
        submitButton.innerHTML = 'Iniciar Sesión';
        submitButton.disabled = false;
    }

    // Función para validar caracteres especiales
    function validarCaracteresEspeciales(valor) {
        return /^[a-zA-Z0-9]*$/.test(valor);
    }

    // Función para agregar clase de error
    function mostrarError(elemento, mensaje) {
        elemento.classList.add('campo-error');
        elemento.parentElement.querySelector('.error-mensaje')?.remove();
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-mensaje';
        errorDiv.textContent = mensaje;
        elemento.parentElement.appendChild(errorDiv);
    }

    // Función para remover clase de error
    function removerError(elemento) {
        elemento.classList.remove('campo-error');
        elemento.parentElement.querySelector('.error-mensaje')?.remove();
    }

    // Validación de usuario en tiempo real
    usernameInput?.addEventListener('input', function(e) {
        const valor = e.target.value;
        
        if (!validarCaracteresEspeciales(valor)) {
            e.target.value = valor.replace(/[^a-zA-Z0-9]/g, '');
            mostrarError(usernameInput, 'Solo se permiten letras y números');
        } else if (valor.length > 15) {
            e.target.value = valor.slice(0, 15);
            mostrarError(usernameInput, 'Máximo 15 caracteres');
        } else {
            removerError(usernameInput);
        }
    });

    // Validación de contraseña en tiempo real
    passwordInput?.addEventListener('input', function(e) {
        const valor = e.target.value;
        
        if (!validarCaracteresEspeciales(valor)) {
            e.target.value = valor.replace(/[^a-zA-Z0-9]/g, '');
            mostrarError(passwordInput, 'Solo se permiten letras y números');
        } else if (valor.length > 14) {
            e.target.value = valor.slice(0, 14);
            mostrarError(passwordInput, 'Máximo 14 caracteres');
        } else {
            removerError(passwordInput);
        }
    });

    // Función para cerrar el modal
    function closeModal() {
        if (modal) {
            modal.classList.remove('modalIntentos-visible');
            
            const errorType = modal.getAttribute('data-error-type');
            if (errorType === 'blocked') {
                window.location.href = '/login/';
            }
        }
    }

    // Validación del formulario antes de enviar
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            let isValid = true;
            
            // Validar username
            if (!usernameInput.value.trim()) {
                mostrarError(usernameInput, 'El usuario es requerido');
                isValid = false;
            } else if (!validarCaracteresEspeciales(usernameInput.value)) {
                mostrarError(usernameInput, 'Solo se permiten letras y números');
                isValid = false;
            }

            // Validar password
            if (!passwordInput.value.trim()) {
                mostrarError(passwordInput, 'La contraseña es requerida');
                isValid = false;
            } else if (!validarCaracteresEspeciales(passwordInput.value)) {
                mostrarError(passwordInput, 'Solo se permiten letras y números');
                isValid = false;
            }

            if (!isValid) {
                e.preventDefault();
            } else {
                mostrarLoader();
            }
        });
    }

    // Eventos del modal
    if (closeButton) closeButton.addEventListener('click', closeModal);
    if (acceptButton) acceptButton.addEventListener('click', closeModal);
    if (modal) {
        modal.addEventListener('click', function(event) {
            if (event.target === modal) closeModal();
        });
    }

    // Cerrar con ESC
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && modal?.classList.contains('modalIntentos-visible')) {
            closeModal();
        }
    });

    // Mostrar errores existentes
    if (modal?.classList.contains('modalIntentos-visible')) {
        const errorType = modal.getAttribute('data-error-type');
        const errorMessage = modal.querySelector('.modalIntentos-body p')?.textContent;

        switch (errorType) {
            case 'username':
                mostrarError(usernameInput, errorMessage);
                break;
            case 'password':
                mostrarError(passwordInput, errorMessage);
                break;
            case 'empty':
                if (!usernameInput.value) mostrarError(usernameInput, 'Campo requerido');
                if (!passwordInput.value) mostrarError(passwordInput, 'Campo requerido');
                break;
        }
        ocultarLoader();
    }

    // Modal de Olvidé Contraseña
    const forgotButton = document.querySelector('.boton-olvidar-contraseña');
    const forgotModal = document.getElementById('modalOlvidePass');
    const forgotCloseButton = document.querySelector('.modalOlvide-close');
    const forgotAcceptButton = document.querySelector('.modalOlvide-button');

    // Función para abrir el modal de olvido de contraseña
    function openForgotModal() {
        if (forgotModal) {
            forgotModal.classList.add('modalOlvide-visible');
        }
    }

    // Función para cerrar el modal de olvido de contraseña
    function closeForgotModal() {
        if (forgotModal) {
            forgotModal.classList.remove('modalOlvide-visible');
        }
    }

    // Eventos para el modal de olvido de contraseña
    if (forgotButton) forgotButton.addEventListener('click', openForgotModal);
    if (forgotCloseButton) forgotCloseButton.addEventListener('click', closeForgotModal);
    if (forgotAcceptButton) forgotAcceptButton.addEventListener('click', closeForgotModal);
    if (forgotModal) {
        forgotModal.addEventListener('click', function(event) {
            if (event.target === forgotModal) {
                closeForgotModal();
            }
        });
    }

    // Cerrar modal de olvido con ESC
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && forgotModal?.classList.contains('modalOlvide-visible')) {
            closeForgotModal();
        }
    });
});