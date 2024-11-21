const AlertSystem = {
    init() {
        this.addStyles();
        this.startAlertCheck();
        this.setupAudio();
        console.log('Sistema de alertas inicializado');
    },

    setupAudio() {
        this.alertSound = new Audio('data:audio/mpeg;base64,SUQzBAAAAAABEVRYWFgAAAAtAAADY29tbWVudABCaWdTb3VuZEJhbmsuY29tIC8gTGFTb25vdGhlcXVlLm9yZwBURU5DAAAAHQAAA1N3aXRjaCBQbHVzIMKpIE5DSCBTb2Z0d2FyZQBUSVQyAAAABgAAAzIyMzUAVFNTRQAAAA8AAANMYXZmNTcuODMuMTAwAAAAAAAAAAAAAAD/+7DEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAASW5mbwAAAA8AAAARAAAh+QANDRISFxccHCEhJiYrKzAwNTU6Oj8/RERJSU5OU1NYWENDSEhNTVJSV1dcXGFhZmZra3BwdXV6en9/REREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREREf/zUMRbAAAGkAKAAAAAABYjgAACGkQZJITmxwYwDcCCAJABUB8H8Pn/iAMEQJBAGCQR/lE/+KA+D6ggQIIECGf/5c4IEMQOIECBAn//+sAQQgQIECYP///+UEYCBAhzggUIP////8oEEAYBhAg4QBgQKAoD4IAgCAIA+CAIAgj//OCPggCAMEgQBA7y5//5c4g+BAEDgMAgCB///1KAgQQAIAj6lE//5c6gNBQgkhAFAYP///+pzgSAkhiAMFAYP////wsDQEAKAwIUBTq///KHOCBQYghBAYDDP///+XBQYWQCAEgbB8H8Pn//gGBwOlxhhIAEexhMFmXoHUTEIhK8LAIBgClAJAOgOAKAFzCEAcAwBEuAOAwAQjCxDAQEwgWGdRwuiGNJK0LEgG4TADiUEYZg8B4qCQgYTgRGKPxNAUgYcAHGBgCKGCEDRqJ0Eh2QJGCu7rmFcAKGFgkX2ThBDIMWGHDCWBZNEgKtAoARZcmCAzBGrUXkNtGxpvkKQSQgxwYCQRggGwBRoIhQo4TGNgUxgPMxcxOKA4cB7BwNDWGAIYSGWFMPFxdkyDR7E5ISGGgIXCEsxkJLqWFpU1RFHQkuC0UpPRCyY8cJwJDghDQUDoOTBAATEEUTEiEzRKVGI5hBAhigYYQFGAhBgcGYGAmDgZjCGChBpVm5KBNwFSVxCpUXFZBJeXUAgOABGBQUPAEVU2ExgxBDGgNxcSCxbZNBgsaxQPtbX5IVwRBYKBEkRiWgpIiMXSJopelEWhDN1bWXBEhF0tKXBrOEPCxTLkYQhJxbLxAksAkzDRjbGE6BUuEQEHyZJ63XWFX5q////+aqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqv/7UMR5A8AAAf4cAAAAAAA0g4AABKqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq');
        this.alertSound.volume = 0.5;
    },

    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .bell-container {
                position: relative;
                display: inline-block;
            }

            #bell-icon {
                transition: color 0.3s ease;
            }

            #bell-icon.warning {
                color: #ffd700 !important;
            }

            #bell-icon.danger {
                color: #ff4444 !important;
            }

            .alert-count {
                position: absolute;
                top: -8px;
                right: -8px;
                background-color: #ff4444;
                color: white;
                border-radius: 50%;
                padding: 2px 6px;
                font-size: 12px;
                min-width: 16px;
                text-align: center;
            }

            @keyframes bellShake {
                0% { transform: rotate(0); }
                25% { transform: rotate(10deg); }
                50% { transform: rotate(0); }
                75% { transform: rotate(-10deg); }
                100% { transform: rotate(0); }
            }

            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 15px 25px;
                border-radius: 5px;
                color: white;
                font-weight: 500;
                z-index: 1000;
                animation: slideIn 0.5s ease-out;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }

            .notification.warning {
                background-color: #ffd700;
                color: #333;
            }

            .notification.danger {
                background-color: #ff4444;
            }

            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(style);
    },

    showNotification(message, type = 'warning') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);

        // Reproducir sonido
        this.alertSound.play().catch(e => console.log('Error al reproducir sonido:', e));

        // Remover la notificación después de 5 segundos
        setTimeout(() => {
            notification.style.animation = 'slideIn 0.5s ease-out reverse';
            setTimeout(() => notification.remove(), 500);
        }, 5000);
    },

    checkAlerts() {
        fetch('/check_alerts/')
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    throw new Error(data.error || 'Error desconocido');
                }

                const bellIcon = document.querySelector('#bell-icon');
                if (!bellIcon) return;

                // Limpiar clases existentes
                bellIcon.classList.remove('warning', 'danger');

                // Aplicar clase según el estado y mostrar notificación
                if (data.sin_stock > 0) {
                    bellIcon.classList.add('danger');
                    bellIcon.parentElement.style.animation = 'bellShake 0.5s cubic-bezier(.36,.07,.19,.97) both';
                    this.showNotification(`¡Alerta! ${data.sin_stock} productos sin stock`, 'danger');
                } else if (data.bajo_stock > 0) {
                    bellIcon.classList.add('warning');
                    bellIcon.parentElement.style.animation = 'bellShake 0.5s cubic-bezier(.36,.07,.19,.97) both';
                    this.showNotification(`¡Atención! ${data.bajo_stock} productos con stock bajo`, 'warning');
                }

                // Actualizar contador
                const totalAlertas = data.sin_stock + data.bajo_stock;
                const alertCount = document.querySelector('.alert-count');
                if (alertCount) {
                    alertCount.textContent = totalAlertas;
                    alertCount.style.display = totalAlertas > 0 ? 'block' : 'none';
                }

                // Resetear la animación para futuros cambios
                setTimeout(() => {
                    if (bellIcon.parentElement) {
                        bellIcon.parentElement.style.animation = '';
                    }
                }, 500);
            })
            .catch(error => {
                console.error('Error al verificar alertas:', error);
                this.showNotification('Error al verificar alertas', 'danger');
            });
    },

    startAlertCheck() {
        this.checkAlerts();
        setInterval(() => this.checkAlerts(), 30000);
    }
};

document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        StockManager.init();
        AlertSystem.init();
    }, 200);
});