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

// Función para actualizar la página del carrito sin recargar
function updateCartPage(data, form) {
    console.log('Actualizando página del carrito...');
    
    if (!form) return;
    
    const action = form.getAttribute('action') || '';
    const isRemoveAction = action.includes('cart_remove');
    
    if (isRemoveAction) {
        const productId = form.dataset.productId || form.querySelector('input[name="product_id"]')?.value;
        const size = form.dataset.size || form.querySelector('input[name="size"]')?.value || '';
        
        // Buscar el elemento del carrito a eliminar
        const cartItem = document.querySelector(`.cart-item-card[data-product-id="${productId}"][data-size="${size}"]`);
        if (cartItem) {
            // Animación de desvanecimiento
            cartItem.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            cartItem.style.opacity = '0';
            cartItem.style.transform = 'translateX(-20px)';
            
            setTimeout(() => {
                cartItem.remove();
                
                // Verificar si quedan items
                const remainingItems = document.querySelectorAll('.cart-item-card');
                if (remainingItems.length === 0) {
                    // Mostrar mensaje de carrito vacío
                    const cartItemsContainer = document.querySelector('.cart-items');
                    const cartSummary = document.querySelector('.cart-summary');
                    if (cartItemsContainer) {
                        cartItemsContainer.innerHTML = '<p>Tu carrito está vacío.</p>';
                    }
                    if (cartSummary) {
                        cartSummary.remove();
                    }
                } else {
                    // Actualizar el total
                    updateCartTotal(data.cart_total);
                }
            }, 300);
        }
    } else {
        // Para incremento, decremento o actualización, recargar la página para mostrar cambios
        if (data.cart_items && data.cart_items.length === 0) {
            const cartItemsContainer = document.querySelector('.cart-items');
            const cartSummary = document.querySelector('.cart-summary');
            if (cartItemsContainer) {
                cartItemsContainer.innerHTML = '<p>Tu carrito está vacío.</p>';
            }
            if (cartSummary) {
                cartSummary.remove();
            }
        } else {
            // Recargar para mostrar los cambios correctamente (cantidades, subtotales, etc.)
            window.location.reload();
        }
    }
}

// Función para actualizar el total del carrito
function updateCartTotal(total) {
    const totalElement = document.querySelector('.cart-total-amount');
    if (totalElement) {
        totalElement.textContent = `${parseFloat(total).toFixed(2)} €`;
    }
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
    
    // Construir HTML del mini-carrito con botón de eliminar todo
    let html = `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
        <h2 style="margin:0;">Carrito (${count || 0})</h2>
        <button id="clear-cart-btn" class="btn-clear-cart" style="background:none;border:none;color:#c62828;cursor:pointer;font-size:16px;padding:4px 8px;border-radius:4px;transition:background 0.2s;" title="Vaciar carrito">
            <i class="fas fa-trash-alt"></i>
        </button>
    </div>`;
    html += '<ul class="mini-cart-list" style="list-style:none;margin:0;padding:0;">';
    
    const baseUrl = window.location.origin;
    
    items.forEach(item => {
        const imagenHtml = item.imagen_url 
            ? `<img class="mini-cart-thumb" src="${item.imagen_url}" alt="${escapeHtml(item.nombre)}" style="width:40px;height:40px;object-fit:cover;border-radius:6px;">`
            : '<div class="mini-cart-thumb placeholder" style="width:40px;height:40px;display:flex;align-items:center;justify-content:center;background:#f0f0f0;color:#999;border-radius:6px;font-size:10px;">Sin imagen</div>';
        
        const sizeHtml = item.size ? `<span class="mini-cart-size" style="color:#666;font-size:11px;"> - Talla: ${escapeHtml(item.size)}</span>` : '';
        
        // Mostrar stock restante
        const remaining = item.remaining !== undefined ? item.remaining : null;
        const remainingHtml = remaining !== null && remaining !== undefined
            ? `<span class="mini-cart-remaining" style="margin-left:8px;font-size:12px;color:#666;vertical-align:middle;">
                ${remaining > 0 ? `Quedan ${remaining}` : 'Agotado'}
               </span>`
            : '';
        
        const isOutOfStock = remaining !== null && remaining <= 0;
        
        html += `
            <li class="mini-cart-item" style="display:flex;gap:8px;align-items:center;padding:6px 4px;border-bottom:1px solid #f3f3f3;">
                ${imagenHtml}
                <div class="mini-cart-info" style="display:flex;flex-direction:column;font-size:12px;flex:1;">
                    <span class="mini-cart-name" style="font-weight:600;">${escapeHtml(item.nombre)}</span>
                    ${sizeHtml}
                    <div class="mini-cart-controls" style="margin-top:4px;">
                        <form action="${baseUrl}/cart/decrement/${item.producto_id}/" method="post" style="display:inline-block; margin-right:6px">
                            <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                            <input type="hidden" name="size" value="${escapeHtml(item.size || '')}">
                            <button type="submit" class="btn small" style="padding:4px 8px;font-size:12px;">-</button>
                        </form>
                        ${remainingHtml}
                        <form action="${baseUrl}/cart/add/${item.producto_id}/" method="post" style="display:inline-block">
                            <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                            <input type="hidden" name="size" value="${escapeHtml(item.size || '')}">
                            <button type="submit" class="btn small" style="padding:4px 8px;font-size:12px;" ${isOutOfStock ? 'disabled' : ''}>+</button>
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
    
    // Configurar botón de vaciar carrito
    const clearBtn = miniCart.querySelector('#clear-cart-btn');
    if (clearBtn) {
        clearBtn.addEventListener('mouseenter', function() {
            this.style.background = '#f5f5f5';
        });
        clearBtn.addEventListener('mouseleave', function() {
            this.style.background = 'none';
        });
        clearBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            clearCart();
        });
    }
    
    // Reconfigurar los formularios del mini-carrito para que también usen AJAX
    // Esperar un momento para que el DOM se actualice
    setTimeout(() => {
        setupCartForms();
    }, 100);
}

// Función para vaciar el carrito
function clearCart() {
    if (!confirm('¿Estás seguro de que quieres vaciar todo el carrito?')) {
        return;
    }
    
    const baseUrl = window.location.origin;
    const csrfToken = getCsrfToken();
    
    fetch(`${baseUrl}/cart/clear/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken,
        },
        credentials: 'same-origin',
        body: new URLSearchParams({
            'csrfmiddlewaretoken': csrfToken
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartCount(0);
            updateMiniCart([], 0, 0);
            // Actualizar dropdowns con carrito vacío para que todos los productos vuelvan a estar disponibles
            updateSizeDropdowns([]);
            showNotification('Carrito vaciado', 'success');
        } else {
            showNotification(data.error || 'Error al vaciar el carrito', 'error');
        }
    })
    .catch(error => {
        console.error('Error al vaciar carrito:', error);
        showNotification('Error de conexión', 'error');
    });
}

// Función para obtener el token CSRF
function getCsrfToken() {
    const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (csrfInput) {
        return csrfInput.value;
    }
    const name = 'csrftoken';
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [key, value] = cookie.trim().split('=');
        if (key === name) {
            return value;
        }
    }
    return '';
}

// Función para actualizar los dropdowns de tallas dinámicamente y la disponibilidad del producto
function updateSizeDropdowns(cartItems, remainingByProduct = {}) {
    // Si cartItems está vacío o es null, restaurar todos los productos
    if (!cartItems || cartItems.length === 0) {
        // Restaurar todos los dropdowns y formularios
        const sizeSelects = document.querySelectorAll('select[id^="size-"]');
        sizeSelects.forEach(select => {
            const productId = select.id.replace('size-', '');
            const options = Array.from(select.querySelectorAll('option[value]'));
            
            let hasAvailableSize = false;
            options.forEach(option => {
                if (!option.value) return;
                
                const stock = parseInt(option.dataset.stock) || 0;
                if (stock > 0) {
                    hasAvailableSize = true;
                }
                
                // Restaurar texto original
                if (option.dataset.originalText) {
                    option.textContent = option.dataset.originalText;
                } else {
                    option.textContent = option.textContent.replace(/\s*\(agotado\)/i, '').trim();
                    option.dataset.originalText = option.textContent;
                }
                option.disabled = stock <= 0;
            });
            
            // Restaurar formulario
            const form = select.closest('form');
            if (form) {
                form.style.display = 'inline';
                form.style.visibility = 'visible';
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = !hasAvailableSize;
                    submitBtn.style.opacity = hasAvailableSize ? '1' : '0.5';
                    submitBtn.style.cursor = hasAvailableSize ? 'pointer' : 'not-allowed';
                }
            }
            
            // Eliminar "No disponible"
            const productContainer = form ? (form.closest('article') || form.closest('.card') || form.parentElement) : null;
            if (productContainer) {
                const noDisponibleDiv = productContainer.querySelector('.product-no-disponible');
                if (noDisponibleDiv) {
                    noDisponibleDiv.remove();
                }
            }
        });
        
        // Restaurar productos sin tallas
        const allForms = document.querySelectorAll('form[action*="/cart/add/"]');
        allForms.forEach(form => {
            const select = form.querySelector('select[id^="size-"]');
            if (!select) {
                form.style.display = 'inline';
                form.style.visibility = 'visible';
                const productContainer = form.closest('article') || form.closest('.card') || form.parentElement;
                if (productContainer) {
                    const noDisponibleDiv = productContainer.querySelector('.product-no-disponible');
                    if (noDisponibleDiv) {
                        noDisponibleDiv.remove();
                    }
                }
            }
        });
        
        return;
    }
    
    // Crear un mapa de cantidad por producto:talla desde el carrito
    const qtyByItem = {};
    const qtyByProduct = {};
    cartItems.forEach(item => {
        const key = `${item.producto_id}:${item.size || ''}`;
        qtyByItem[key] = (qtyByItem[key] || 0) + item.cantidad;
        qtyByProduct[item.producto_id] = (qtyByProduct[item.producto_id] || 0) + item.cantidad;
    });
    
    // Buscar todos los dropdowns de tallas en la página
    const sizeSelects = document.querySelectorAll('select[id^="size-"]');
    console.log('Encontrados', sizeSelects.length, 'dropdowns de tallas en la página');
    
    if (sizeSelects.length === 0) {
        console.log('No se encontraron dropdowns de tallas. Esto puede ser normal si no hay productos con tallas en esta página.');
    }
    
    sizeSelects.forEach((select, idx) => {
        const productId = select.id.replace('size-', '');
        console.log(`  📦 Procesando producto ${idx + 1}/${sizeSelects.length}: ID=${productId}`);
        const options = Array.from(select.querySelectorAll('option[value]'));
        
        let hasAvailableSize = false;
        let totalStock = 0;
        
        options.forEach(option => {
            if (!option.value) return; // Skip placeholder option
            
            const size = option.value;
            const key = `${productId}:${size}`;
            const taken = qtyByItem[key] || 0;
            
            // Guardar el texto original si no está guardado
            if (!option.dataset.originalText) {
                const cleanText = option.textContent.replace(/\s*\(agotado\)/i, '').trim();
                option.dataset.originalText = cleanText;
            }
            
            // Obtener el stock del atributo data-stock
            const stock = parseInt(option.dataset.stock) || 0;
            totalStock += stock;
            const remaining = stock - taken;
            const originalText = option.dataset.originalText || size;
            
            // Actualizar el texto y estado de la opción
            const currentText = option.textContent.trim();
            if (remaining <= 0 && stock > 0) {
                const newText = `${originalText} (agotado)`;
                if (currentText !== newText) {
                    option.textContent = newText;
                    console.log(`    ✓ ${size} → "${newText}" (stock:${stock}, taken:${taken}, rem:${remaining})`);
                }
                option.disabled = true;
            } else {
                // Si el texto actual tiene "(agotado)" pero ahora hay stock, restaurar
                if (currentText.includes('(agotado)')) {
                    option.textContent = originalText;
                    console.log(`    ✓ ${size} → "${originalText}" (stock:${stock}, taken:${taken}, rem:${remaining})`);
                } else if (currentText !== originalText) {
                    option.textContent = originalText;
                }
                option.disabled = false;
                if (remaining > 0) {
                    hasAvailableSize = true;
                }
            }
        });
        
        // Actualizar disponibilidad del producto y el botón
        updateProductAvailability(productId, hasAvailableSize, select);
        
        // Actualizar el botón según disponibilidad y talla seleccionada
        const form = select.closest('form');
        if (form) {
            // Si no hay tallas disponibles, deshabilitar el botón
            if (!hasAvailableSize) {
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.style.opacity = '0.5';
                    submitBtn.style.cursor = 'not-allowed';
                }
            } else {
                // Si hay tallas disponibles, actualizar el botón según la selección actual
                updateAddToCartButton(form);
            }
            
            // Agregar listener al select para actualizar el botón cuando cambie la selección
            if (!select.dataset.changeListenerAdded) {
                select.dataset.changeListenerAdded = 'true';
                select.addEventListener('change', function() {
                    updateAddToCartButton(form);
                });
            }
        }
    });
    
    // También actualizar productos sin tallas
    updateProductsWithoutSizes(cartItems, qtyByProduct, remainingByProduct);
    
    // Actualizar todos los botones de "Añadir al carrito" después de actualizar los dropdowns
    const allAddToCartForms = document.querySelectorAll('form[action*="/cart/add/"]');
    allAddToCartForms.forEach(form => {
        updateAddToCartButton(form);
    });
}

// Función para actualizar la disponibilidad de un producto con tallas
function updateProductAvailability(productId, hasAvailableSize, selectElement) {
    // Buscar el formulario
    const form = selectElement.closest('form');
    if (!form) return;
    
    // Buscar el contenedor del producto (puede ser un article, div, etc.)
    const productContainer = form.closest('article') || form.closest('.card') || form.closest('.product') || form.parentElement;
    if (!productContainer) return;
    
    // Buscar el mensaje "No disponible" existente
    let noDisponibleDiv = productContainer.querySelector('.product-no-disponible');
    
    if (hasAvailableSize) {
        // Si hay tallas disponibles, mostrar el formulario y ocultar "No disponible"
        form.style.display = 'inline';
        form.style.visibility = 'visible';
        if (noDisponibleDiv) {
            noDisponibleDiv.style.display = 'none';
            noDisponibleDiv.remove(); // Eliminar completamente para evitar problemas
        }
    } else {
        // Si no hay tallas disponibles, ocultar el formulario y mostrar "No disponible"
        form.style.display = 'none';
        
        // Crear el div si no existe
        if (!noDisponibleDiv) {
            noDisponibleDiv = document.createElement('div');
            noDisponibleDiv.className = 'product-no-disponible';
            noDisponibleDiv.style.cssText = 'color:#c62828;font-weight:700';
            noDisponibleDiv.textContent = 'No disponible';
            // Insertar en el mismo lugar donde estaba el formulario
            form.parentNode.insertBefore(noDisponibleDiv, form);
        } else {
            noDisponibleDiv.style.display = 'block';
        }
    }
}

// Función para actualizar productos sin tallas
function updateProductsWithoutSizes(cartItems, qtyByProduct, remainingByProduct = {}) {
    // Buscar todos los formularios de productos sin tallas
    // Estos son formularios que no tienen un select de tallas
    const allForms = document.querySelectorAll('form[action*="/cart/add/"]');
    
    allForms.forEach(form => {
        const action = form.getAttribute('action');
        const match = action.match(/\/cart\/add\/(\d+)\//);
        if (!match) return;
        
        const productId = match[1];
        const select = form.querySelector('select[id^="size-"]');
        
        // Si tiene select de tallas, ya fue procesado
        if (select) return;
        
        // Es un producto sin tallas
        const taken = qtyByProduct[productId] || 0;
        
        // Buscar el contenedor del producto
        const productContainer = form.closest('article') || form.closest('.card') || form.closest('.product') || form.parentElement;
        if (!productContainer) return;
        
        // Buscar información de stock del item en el carrito si existe
        let remaining = null;
        const cartItem = cartItems.find(item => item.producto_id == productId && (!item.size || item.size === ''));
        if (cartItem && cartItem.remaining !== undefined) {
            // Usar el remaining del carrito (más confiable)
            remaining = cartItem.remaining;
            console.log(`  📦 Producto sin talla ${productId}: remaining=${remaining} (del carrito)`);
        } else if (remainingByProduct[productId] !== undefined) {
            // Usar remaining_by_product del servidor si está disponible
            remaining = remainingByProduct[productId];
            console.log(`  📦 Producto sin talla ${productId}: remaining=${remaining} (de remaining_by_product)`);
        } else {
            // Obtener el stock del contenedor del producto (data-stock)
            const stockAttr = productContainer.dataset.stock || productContainer.dataset.productStock;
            if (stockAttr) {
                const stock = parseInt(stockAttr);
                remaining = Math.max(0, stock - taken);
                console.log(`  📦 Producto sin talla ${productId}: stock=${stock}, taken=${taken}, remaining=${remaining}`);
            } else {
                // Si no tenemos información de stock, no podemos determinar el estado
                // No hacer cambios en este caso para evitar ocultar productos incorrectamente
                console.log(`  ⚠️ Producto sin talla ${productId}: No se pudo determinar el stock (no data-stock en contenedor)`);
                return; // No podemos determinar, no hacer cambios
            }
        }
        
        // Buscar o crear el mensaje "No disponible"
        let noDisponibleDiv = productContainer.querySelector('.product-no-disponible');
        
        // Mostrar/ocultar según disponibilidad
        if (remaining > 0) {
            form.style.display = 'inline';
            form.style.visibility = 'visible';
            if (noDisponibleDiv) {
                noDisponibleDiv.style.display = 'none';
                noDisponibleDiv.remove(); // Eliminar completamente
            }
        } else {
            form.style.display = 'none';
            if (noDisponibleDiv) {
                noDisponibleDiv.style.display = 'block';
            } else {
                noDisponibleDiv = document.createElement('div');
                noDisponibleDiv.className = 'product-no-disponible';
                noDisponibleDiv.style.cssText = 'color:#c62828;font-weight:700';
                noDisponibleDiv.textContent = 'No disponible';
                form.parentNode.insertBefore(noDisponibleDiv, form);
            }
        }
    });
}

// Función para validar si se puede añadir un producto al carrito
function canAddToCart(form) {
    const select = form.querySelector('select[id^="size-"]');
    if (!select) {
        // Producto sin tallas, permitir
        return true;
    }
    
    // Verificar que hay una talla seleccionada
    const selectedIndex = select.selectedIndex;
    if (selectedIndex <= 0) {
        // No hay talla seleccionada (índice 0 es el placeholder "Selecciona")
        console.log('canAddToCart: No hay talla seleccionada (selectedIndex:', selectedIndex, ')');
        return false;
    }
    
    const selectedOption = select.options[selectedIndex];
    if (!selectedOption) {
        console.log('canAddToCart: No se encontró la opción seleccionada');
        return false;
    }
    
    const selectedValue = selectedOption.value;
    if (!selectedValue || selectedValue.trim() === '') {
        console.log('canAddToCart: La talla seleccionada está vacía');
        return false; // No hay talla seleccionada
    }
    
    // Verificar que la opción no está deshabilitada (agotada)
    if (selectedOption.disabled) {
        console.log('canAddToCart: La talla seleccionada está deshabilitada (agotada)');
        return false; // La talla está agotada
    }
    
    // Verificar que el texto no contiene "(agotado)"
    if (selectedOption.textContent.includes('(agotado)')) {
        console.log('canAddToCart: La talla seleccionada está agotada (texto contiene agotado)');
        return false; // La talla está agotada
    }
    
    console.log('canAddToCart: Validación exitosa, talla seleccionada:', selectedValue);
    return true;
}

// Función para actualizar el estado del botón según la talla seleccionada
function updateAddToCartButton(form) {
    const select = form.querySelector('select[id^="size-"]');
    const submitBtn = form.querySelector('button[type="submit"]');
    
    if (!select || !submitBtn) {
        // Si no hay select, es un producto sin tallas, habilitar el botón
        if (!select && submitBtn) {
            submitBtn.disabled = false;
            submitBtn.style.opacity = '1';
            submitBtn.style.cursor = 'pointer';
        }
        return;
    }
    
    // Asegurar que el listener del select esté configurado
    if (!select.dataset.changeListenerAdded) {
        select.dataset.changeListenerAdded = 'true';
        select.addEventListener('change', function() {
            updateAddToCartButton(form);
        });
    }
    
    const canAdd = canAddToCart(form);
    
    if (canAdd) {
        submitBtn.disabled = false;
        submitBtn.style.opacity = '1';
        submitBtn.style.cursor = 'pointer';
    } else {
        submitBtn.disabled = true;
        submitBtn.style.opacity = '0.5';
        submitBtn.style.cursor = 'not-allowed';
    }
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
            
            // Guardar el evento para usar en updateCartPage
            window.cartFormEvent = e;
            
            const action = form.getAttribute('action');
            
            // Validar si se puede añadir al carrito (para productos con tallas)
            if (action && action.includes('add_to_cart')) {
                const select = form.querySelector('select[id^="size-"]');
                if (select) {
                    // Es un producto con tallas, validar
                    if (!canAddToCart(form)) {
                        const selectedIndex = select.selectedIndex;
                        if (selectedIndex <= 0) {
                            showNotification('Por favor selecciona una talla', 'error');
                        } else {
                            const selectedOption = select.options[selectedIndex];
                            if (selectedOption && selectedOption.disabled) {
                                showNotification('La talla seleccionada no está disponible', 'error');
                            } else {
                                showNotification('Por favor selecciona una talla disponible', 'error');
                            }
                        }
                        return;
                    }
                }
            }
            
            const formData = new FormData(form);
            const method = form.getAttribute('method') || 'POST';
            
            // Log para depuración
            const sizeValue = formData.get('size');
            console.log('Enviando petición AJAX a:', action, 'con talla:', sizeValue);
            
            // Guardar texto original del botón
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.dataset.originalText) {
                submitBtn.dataset.originalText = submitBtn.textContent;
            }
            
            // Deshabilitar botón para evitar doble envío
            if (submitBtn) {
                submitBtn.disabled = true;
                const buttonText = action.includes('cart_remove') ? 'Eliminando...' : 
                                  action.includes('cart_decrement') ? 'Actualizando...' :
                                  action.includes('cart_update') ? 'Actualizando...' :
                                  'Añadiendo...';
                submitBtn.textContent = buttonText;
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
                    
                    // Si estamos en la página del carrito y es una acción de eliminar o actualizar
                    const isCartPage = window.location.pathname.includes('/cart') && !window.location.pathname.includes('/checkout');
                    const isRemoveAction = action && action.includes('cart_remove');
                    const isUpdateAction = action && action.includes('cart_update');
                    const isDecrementAction = action && action.includes('cart_decrement');
                    
                    if (isCartPage && (isRemoveAction || isUpdateAction || isDecrementAction)) {
                        updateCartPage(data, form);
                    }
                    
                    // Actualizar mini-carrito si hay datos
                    if (data.cart_items !== undefined) {
                        console.log('Actualizando mini-carrito con', data.cart_items.length, 'items');
                        updateMiniCart(data.cart_items, data.cart_total, data.cart_count);
                    }
                    
                    // SIEMPRE actualizar dropdowns, incluso si no hay items en el carrito
                    console.log('🔄 Actualizando dropdowns de tallas en la página de productos...');
                    console.log('   Items en carrito:', data.cart_items ? data.cart_items.length : 0);
                    // Ejecutar inmediatamente
                    updateSizeDropdowns(data.cart_items || [], data.remaining_by_product || {});
                    // También ejecutar con un pequeño delay para asegurar que el DOM esté completamente actualizado
                    setTimeout(() => {
                        console.log('🔄 Re-ejecutando actualización de dropdowns (segunda pasada)...');
                        updateSizeDropdowns(data.cart_items || [], data.remaining_by_product || {});
                    }, 150);
                    
                    // También obtener el estado completo del carrito para asegurar sincronización
                    // (esto se ejecuta en paralelo, no bloquea la actualización inmediata)
                    const baseUrl = window.location.origin;
                    fetch(`${baseUrl}/cart/status/`, {
                        method: 'GET',
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest',
                        },
                        credentials: 'same-origin'
                    })
                    .then(response => response.json())
                    .then(statusData => {
                        if (statusData && statusData.success) {
                            console.log('Sincronizando dropdowns con estado completo del carrito:', statusData.cart_items.length, 'items');
                            updateSizeDropdowns(statusData.cart_items || [], statusData.remaining_by_product || {});
                        }
                    })
                    .catch(error => {
                        console.log('Error al sincronizar estado del carrito (no crítico):', error);
                    });
                    
                    // Mostrar notificación
                    const message = data.message || 'Carrito actualizado';
                    showNotification(message, 'success');
                    
                    // Si estamos en la página del carrito y eliminamos un item, no necesitamos rehabilitar el botón
                    const isCartPage = window.location.pathname.includes('/cart') && !window.location.pathname.includes('/checkout');
                    const isRemoveAction = action && action.includes('cart_remove');
                    const isUpdateAction = action && action.includes('cart_update');
                    const isDecrementAction = action && action.includes('cart_decrement');
                    
                    // Solo rehabilitar el botón si no estamos en la página del carrito o si no es una acción que requiere recarga
                    if (!isCartPage || (!isRemoveAction && !isUpdateAction && !isDecrementAction)) {
                        // Rehabilitar botón (pero validar si puede añadir)
                        if (submitBtn) {
                            setTimeout(() => {
                                submitBtn.textContent = submitBtn.dataset.originalText || 'Añadir al carrito';
                                submitBtn.disabled = false;
                                // Actualizar el botón según la validación actual (puede estar deshabilitado si la talla está agotada)
                                updateAddToCartButton(form);
                            }, 1000);
                        }
                    }
                } else {
                    console.error('Error en respuesta:', data.error);
                    showNotification(data.error || 'Error al actualizar el carrito', 'error');
                    
                    // Rehabilitar botón (pero validar si puede añadir)
                    if (submitBtn) {
                        submitBtn.textContent = submitBtn.dataset.originalText || 'Añadir al carrito';
                        // Actualizar el botón según la validación actual
                        updateAddToCartButton(form);
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

// Función para inicializar el carrito al cargar la página
function initializeCart() {
    // Primero, leer el valor inicial del DOM (renderizado por el servidor)
    const cartCountElement = document.querySelector('.cart-count');
    let initialCount = 0;
    if (cartCountElement) {
        const text = cartCountElement.textContent.trim();
        initialCount = parseInt(text) || 0;
        console.log('Cart count inicial del DOM:', initialCount, '(texto:', text, ')');
    }
    
    // Asegurarse de que el valor está visible (incluso si es 0)
    updateCartCount(initialCount);
    
    // Luego, obtener el estado actual del carrito desde el servidor para sincronizar
    const baseUrl = window.location.origin;
    fetch(`${baseUrl}/cart/status/`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        }
        return null;
    })
    .then(data => {
        if (data && data.success) {
            console.log('Cart status recibido del servidor:', data);
            // Actualizar contador con el valor del servidor (más confiable)
            updateCartCount(data.cart_count);
            
            // Actualizar mini-carrito si hay items
            if (data.cart_items && data.cart_items.length > 0) {
                updateMiniCart(data.cart_items, data.cart_total, data.cart_count);
            } else {
                // Si no hay items, asegurarse de que el mini-carrito no esté visible
                const miniCart = document.getElementById('mini-cart-container') || document.querySelector('.mini-cart');
                if (miniCart && !window.location.pathname.includes('/checkout') && !window.location.pathname.includes('/cart')) {
                    // El mini-carrito del servidor debería manejar esto, pero por si acaso
                    const path = window.location.pathname;
                    if (!path.includes('/checkout') && !path.includes('/cart')) {
                        // No hacer nada, dejar que el servidor maneje la visibilidad
                    }
                }
            }
            
            // Actualizar dropdowns de tallas
            updateSizeDropdowns(data.cart_items || [], data.remaining_by_product || {});
            
            // Inicializar botones de "Añadir al carrito" después de actualizar dropdowns
            setTimeout(() => {
                const allAddToCartForms = document.querySelectorAll('form[action*="/cart/add/"]');
                allAddToCartForms.forEach(form => {
                    updateAddToCartButton(form);
                    // Asegurar que los selects tengan listeners
                    const select = form.querySelector('select[id^="size-"]');
                    if (select && !select.dataset.changeListenerAdded) {
                        select.dataset.changeListenerAdded = 'true';
                        select.addEventListener('change', function() {
                            updateAddToCartButton(form);
                        });
                    }
                });
            }, 200);
        }
    })
    .catch(error => {
        console.log('Error al obtener estado del carrito (no crítico):', error);
        // No es crítico, el valor del DOM debería ser suficiente
        // Aún así, inicializar los botones
        setTimeout(() => {
            const allAddToCartForms = document.querySelectorAll('form[action*="/cart/add/"]');
            allAddToCartForms.forEach(form => {
                updateAddToCartButton(form);
                // Asegurar que los selects tengan listeners
                const select = form.querySelector('select[id^="size-"]');
                if (select && !select.dataset.changeListenerAdded) {
                    select.dataset.changeListenerAdded = 'true';
                    select.addEventListener('change', function() {
                        updateAddToCartButton(form);
                    });
                }
            });
        }, 200);
    });
}

// Ejecutar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        console.log('DOM cargado, configurando formularios...');
        initializeCart();
        setupCartForms();
    });
} else {
    // DOM ya está cargado
    console.log('DOM ya cargado, configurando formularios...');
    initializeCart();
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
