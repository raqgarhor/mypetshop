/**
 * Manejo de carrito con AJAX para evitar recargas de página
 */

console.log('cart.js cargado');

// Función para escapar HTML (prevenir XSS)
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Función para actualizar el contador del carrito
function updateCartCount(count) {
    console.log('Actualizando contador del carrito a:', count);
    const cartCountElements = document.querySelectorAll('.cart-count');
    console.log('Elementos .cart-count encontrados:', cartCountElements.length);
    
    cartCountElements.forEach(el => {
        const oldValue = el.textContent;
        el.textContent = count || 0;
        console.log(`Contador actualizado: ${oldValue} -> ${el.textContent}`);
        
        // Animación
        el.style.transition = 'transform 0.2s ease';
        el.style.transform = 'scale(1.2)';
        setTimeout(() => {
            el.style.transform = 'scale(1)';
        }, 200);
    });
}

// Función para mostrar notificaciones
function showNotification(message, type) {
    // Eliminar notificación anterior si existe
    const existing = document.querySelector('.cart-notification');
    if (existing) {
        existing.remove();
    }
    
    // Crear nueva notificación
    const notification = document.createElement('div');
    notification.className = `cart-notification ${type}`;
    notification.innerHTML = `
        <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
        <span>${escapeHtml(message)}</span>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-eliminar después de 3 segundos
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Función para actualizar el mini-carrito
function updateMiniCart(items, total, count) {
    console.log('Actualizando mini-carrito con', items.length, 'items');
    
    // Buscar el mini-carrito (por ID o clase)
    let miniCart = document.getElementById('mini-cart-container') || document.querySelector('.mini-cart');
    
    // Verificar si estamos en checkout o cart page (no mostrar mini-carrito ahí)
    const path = window.location.pathname;
    if (path.includes('/checkout') || path.includes('/cart')) {
        if (miniCart) {
            miniCart.remove();
        }
        return;
    }
    
    // Si no hay items, ocultar o eliminar el mini-carrito
    if (items.length === 0) {
        if (miniCart) {
            miniCart.remove();
        }
        return;
    }
    
    // Si no existe y hay items, crearlo
    if (!miniCart && items.length > 0) {
        miniCart = document.createElement('section');
        miniCart.id = 'mini-cart-container';
        miniCart.className = 'mini-cart';
        miniCart.style.cssText = 'position:fixed;right:20px;bottom:20px;top:auto;width:260px;max-width:calc(100% - 40px);max-height:50vh;overflow:auto;background:#fff;border:1px solid rgba(0,0,0,0.08);box-shadow:0 6px 18px rgba(0,0,0,0.08);border-radius:8px;padding:8px;z-index:9999;box-sizing:border-box;font-size:13px;';
        document.body.appendChild(miniCart);
    }
    
    // Obtener el token CSRF de cualquier formulario en la página
    let csrfToken = '';
    const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (csrfInput) {
        csrfToken = csrfInput.value;
    }
    
    // Si no hay token, intentar obtenerlo de las cookies
    if (!csrfToken) {
        const name = 'csrftoken';
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [key, value] = cookie.trim().split('=');
            if (key === name) {
                csrfToken = value;
                break;
            }
        }
    }
    
    // Construir HTML del mini-carrito
    let html = `<h2>Carrito (${count || 0})</h2>`;
    html += '<ul class="mini-cart-list" style="list-style:none;margin:0;padding:0;">';
    
    const baseUrl = window.location.origin;
    
    items.forEach(item => {
        const imagenHtml = item.imagen_url 
            ? `<img class="mini-cart-thumb" src="${item.imagen_url}" alt="${escapeHtml(item.nombre)}" style="width:40px;height:40px;object-fit:cover;border-radius:6px;">`
            : '<div class="mini-cart-thumb placeholder" style="width:40px;height:40px;display:flex;align-items:center;justify-content:center;background:#f0f0f0;color:#999;border-radius:6px;font-size:10px;">Sin imagen</div>';
        
        const sizeHtml = item.size ? `<span class="mini-cart-size" style="color:#666;font-size:11px;"> - Talla: ${escapeHtml(item.size)}</span>` : '';
        
        html += `
            <li class="mini-cart-item" style="display:flex;gap:8px;align-items:center;padding:6px 4px;border-bottom:1px solid #f3f3f3;">
                ${imagenHtml}
                <div class="mini-cart-info" style="display:flex;flex-direction:column;font-size:12px;flex:1;">
                    <span class="mini-cart-name" style="font-weight:600;">${escapeHtml(item.nombre)}</span>
                    ${sizeHtml}
                    <div class="mini-cart-controls" style="margin-top:4px;">
                        <form action="${baseUrl}/cart/add/${item.producto_id}/" method="post" style="display:inline-block; margin-right:6px">
                            <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                            <input type="hidden" name="size" value="${escapeHtml(item.size || '')}">
                            <button type="submit" class="btn small" style="padding:4px 8px;font-size:12px;">+</button>
                        </form>
                        <form action="${baseUrl}/cart/decrement/${item.producto_id}/" method="post" style="display:inline-block">
                            <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                            <input type="hidden" name="size" value="${escapeHtml(item.size || '')}">
                            <button type="submit" class="btn small" style="padding:4px 8px;font-size:12px;">-</button>
                        </form>
                        <div style="margin-top:6px;font-size:13px;color:#444">Cantidad: ${item.cantidad} — ${item.subtotal.toFixed(2)} €</div>
                    </div>
                </div>
            </li>
        `;
    });
    
    html += '</ul>';
    html += `<p class="mini-cart-total" style="font-weight:700;margin:8px 0;text-align:right;font-size:13px;color:#27ae60;">Total: ${total.toFixed(2)} €</p>`;
    html += `<a href="${baseUrl}/checkout/datos/" class="btn small" style="display:block;text-align:center;margin-top:8px;padding:6px 8px;font-size:13px;">Tramitar pedido</a>`;
    
    miniCart.innerHTML = html;
    
    // Reconfigurar los formularios del mini-carrito para que también usen AJAX
    // Esperar un momento para que el DOM se actualice
    setTimeout(() => {
        setupCartForms();
    }, 100);
}

// Función para interceptar formularios
function setupCartForms() {
    // Buscar todos los formularios
    const allForms = document.querySelectorAll('form');
    const cartForms = Array.from(allForms).filter(form => {
        const action = form.getAttribute('action') || '';
        return action.includes('cart/') || 
               action.includes('add_to_cart') || 
               action.includes('cart_decrement') || 
               action.includes('cart_remove') || 
               action.includes('cart_update');
    });
    
    console.log('Formularios de carrito encontrados:', cartForms.length);
    
    cartForms.forEach((form, index) => {
        // Evitar añadir múltiples listeners
        if (form.dataset.cartListener === 'true') {
            return;
        }
        form.dataset.cartListener = 'true';
        
        console.log(`Configurando formulario ${index}:`, form.getAttribute('action'));
        
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const formData = new FormData(form);
            const action = form.getAttribute('action');
            const method = form.getAttribute('method') || 'POST';
            
            console.log('Enviando petición AJAX a:', action);
            
            // Guardar texto original del botón
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.dataset.originalText) {
                submitBtn.dataset.originalText = submitBtn.textContent;
            }
            
            // Deshabilitar botón para evitar doble envío
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Añadiendo...';
            }
            
            // Crear petición AJAX
            fetch(action, {
                method: method,
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin'
            })
            .then(response => {
                console.log('Respuesta recibida:', response.status, response.statusText);
                const contentType = response.headers.get('content-type') || '';
                console.log('Content-Type:', contentType);
                
                if (contentType.includes('application/json')) {
                    return response.json();
                } else {
                    // Si no es JSON, recargar página
                    console.log('Respuesta no es JSON, recargando...');
                    window.location.reload();
                    return null;
                }
            })
            .then(data => {
                if (!data) return;
                
                console.log('Datos recibidos:', data);
                
                if (data.success) {
                    // Actualizar contador
                    updateCartCount(data.cart_count);
                    
                    // Actualizar mini-carrito si hay datos
                    if (data.cart_items !== undefined) {
                        console.log('Actualizando mini-carrito con', data.cart_items.length, 'items');
                        updateMiniCart(data.cart_items, data.cart_total, data.cart_count);
                    }
                    
                    // Mostrar notificación
                    const message = data.message || 'Carrito actualizado';
                    showNotification(message, 'success');
                    
                    // Rehabilitar botón
                    if (submitBtn) {
                        setTimeout(() => {
                            submitBtn.disabled = false;
                            submitBtn.textContent = submitBtn.dataset.originalText || 'Añadir al carrito';
                        }, 1000);
                    }
                } else {
                    console.error('Error en respuesta:', data.error);
                    showNotification(data.error || 'Error al actualizar el carrito', 'error');
                    
                    // Rehabilitar botón
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.textContent = submitBtn.dataset.originalText || 'Añadir al carrito';
                    }
                }
            })
            .catch(error => {
                console.error('Error en petición:', error);
                showNotification('Error de conexión. Recargando...', 'error');
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            });
        });
    });
}

// Ejecutar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        console.log('DOM cargado, configurando formularios...');
        setupCartForms();
    });
} else {
    // DOM ya está cargado
    console.log('DOM ya cargado, configurando formularios...');
    setupCartForms();
}

// Observer para formularios que se añadan dinámicamente
const observer = new MutationObserver(function(mutations) {
    setupCartForms();
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});

// Exportar funciones para uso global
window.updateCartCount = updateCartCount;
window.showNotification = showNotification;
window.updateMiniCart = updateMiniCart;
