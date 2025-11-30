import datetime
from decimal import Decimal, ROUND_HALF_UP

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.http import url_has_allowed_host_and_scheme
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from .forms import (
    ClienteEnvioForm,
    EmailAuthenticationForm,
    GuestCheckoutForm,
    RegistroForm,
    SeguimientoPedidoForm,
)
from .models import (
    Categoria,
    Cliente,
    ItemPedido,
    Marca,
    MensajeContacto,
    Pedido,
    Producto,
    TallaProducto,
)


stripe.api_key = settings.STRIPE_SECRET_KEY


def calculate_remaining_stock(cart, producto, size=''):
    """
    Calcula el stock restante para un producto/talla considerando lo que hay en el carrito.
    Similar a la lógica en context_processors.py
    """
    if not isinstance(cart, dict):
        cart = {}
    
    # Calcular cantidad total en el carrito para este producto
    qty_by_product = {}
    qty_by_item = {}
    
    for composite_key, qty in cart.items():
        try:
            if isinstance(composite_key, str) and ':' in composite_key:
                pid_str, item_size = composite_key.split(':', 1)
            else:
                pid_str = str(composite_key)
                item_size = ''
            
            if int(pid_str) == producto.id:
                cantidad = int(qty)
                pid_key = str(producto.id)
                qty_by_product[pid_key] = qty_by_product.get(pid_key, 0) + cantidad
                key = f"{pid_key}:{item_size}"
                qty_by_item[key] = qty_by_item.get(key, 0) + cantidad
        except Exception:
            continue
    
    # Calcular stock restante
    pid_key = str(producto.id)
    key = f"{pid_key}:{size}"
    
    if size:
        # Si tiene talla específica, usar el stock de esa talla
        talla = producto.tallas.filter(talla=size).first()
        stock = talla.stock if talla else 0
        taken = qty_by_item.get(key, 0)
        return max(0, stock - taken)
    else:
        # Sin talla específica
        if producto.tallas.exists():
            # Si el producto tiene tallas, sumar todos los stocks
            total_stock = sum(t.stock for t in producto.tallas.all())
            taken = qty_by_product.get(pid_key, 0)
            return max(0, total_stock - taken)
        else:
            # Sin tallas, usar el stock del producto
            taken = qty_by_product.get(pid_key, 0)
            return max(0, producto.stock - taken)


def _build_cart_json_response(cart, extra_data=None):
    """
    Helper function para construir la respuesta JSON del carrito.
    Evita duplicación de código en las funciones de carrito.
    
    Args:
        cart: Diccionario del carrito de sesión
        extra_data: Diccionario opcional con datos adicionales para incluir en la respuesta
    
    Returns:
        Dict con la estructura estándar de respuesta del carrito
    """
    if not isinstance(cart, dict):
        cart = {}
    
    total_count = sum(int(qty) for qty in cart.values())
    items = []
    total_amount = Decimal('0.00')
    remaining_by_product = {}
    
    for composite_key, qty in cart.items():
        try:
            if isinstance(composite_key, str) and ':' in composite_key:
                pid_str, size = composite_key.split(':', 1)
            else:
                pid_str = str(composite_key)
                size = ''
            
            prod = Producto.objects.filter(pk=int(pid_str)).first()
            if not prod:
                continue
            
            cantidad = int(qty)
            precio = prod.precio_oferta or prod.precio or Decimal('0.00')
            subtotal = precio * cantidad
            total_amount += subtotal
            
            # Obtener imagen
            imagen_url = None
            imagen = prod.imagenes.first()
            if imagen:
                imagen_url = imagen.imagen.url
            
            # Calcular stock restante
            remaining = calculate_remaining_stock(cart, prod, size)
            
            items.append({
                'producto_id': prod.id,
                'nombre': prod.nombre,
                'cantidad': cantidad,
                'subtotal': float(subtotal),
                'size': size,
                'imagen_url': imagen_url,
                'precio': float(precio),
                'remaining': remaining
            })
            
            # Guardar remaining para productos sin tallas
            if not size and not prod.tallas.exists():
                remaining_by_product[prod.id] = remaining
        except Exception:
            continue
    
    response = {
        'success': True,
        'cart_count': total_count,
        'cart_items': items,
        'cart_total': float(total_amount),
        'remaining_by_product': remaining_by_product
    }
    
    # Agregar datos extra si se proporcionan
    if extra_data:
        response.update(extra_data)
    
    return response


def index(request):
    """Si se recibe ?q=texto, filtra por nombre, descripcion, genero, color o material.
    También permite filtrar por marca, especie, color y material."""
    q = request.GET.get('q', '')
    marca_filtro = request.GET.get('marca', '')
    especie_filtro = request.GET.get('especie', '')
    color_filtro = request.GET.get('color', '')
    material_filtro = request.GET.get('material', '')
    
    productos_list = Producto.objects.filter(esta_disponible=True)
    
    # Filtro de búsqueda por texto
    if q:
        query = q.strip()
        filtros_texto = Q(nombre__icontains=query) | Q(descripcion__icontains=query) | Q(genero__icontains=query) | Q(color__icontains=query) | Q(material__icontains=query)
        productos_list = productos_list.filter(filtros_texto)
    else:
        query = ''
    
    # Filtros específicos
    if marca_filtro:
        productos_list = productos_list.filter(marca_id=marca_filtro)
    
    if especie_filtro:
        productos_list = productos_list.filter(genero=especie_filtro)
    
    if color_filtro:
        productos_list = productos_list.filter(color__icontains=color_filtro)
    
    if material_filtro:
        productos_list = productos_list.filter(material__icontains=material_filtro)
    
    productos_list = productos_list.order_by('-es_destacado', '-fecha_creacion')

    # Paginación
    paginator = Paginator(productos_list, 12)  # 12 productos por página
    page = request.GET.get('page')
    try:
        productos = paginator.page(page)
    except PageNotAnInteger:
        productos = paginator.page(1)
    except EmptyPage:
        productos = paginator.page(paginator.num_pages)

    # Obtener marcas y especies para los filtros
    marcas = Marca.objects.all().order_by('nombre')
    especies = Producto.Especie.choices
    
    # Obtener colores y materiales únicos para los filtros
    colores = Producto.objects.filter(esta_disponible=True, color__isnull=False).exclude(color='').values_list('color', flat=True).distinct().order_by('color')
    materiales = Producto.objects.filter(esta_disponible=True, material__isnull=False).exclude(material='').values_list('material', flat=True).distinct().order_by('material')

    contexto = {
        'productos': productos,
        'query': query,
        'marcas': marcas,
        'especies': especies,
        'colores': colores,
        'materiales': materiales,
        'marca_filtro': marca_filtro,
        'especie_filtro': especie_filtro,
        'color_filtro': color_filtro,
        'material_filtro': material_filtro,
    }
    return render(request, 'index.html', contexto)


def add_to_cart(request, product_id):
    """Añade un producto al carrito guardado en la sesión."""
    if request.method != 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
        return redirect(request.META.get('HTTP_REFERER', reverse('home')))

    # Allow selecting a talla (size). Expect POST param 'size'
    size = (request.POST.get('size') or '').strip()
    producto = get_object_or_404(Producto, pk=product_id, esta_disponible=True)

    # Validar que si el producto tiene tallas, se haya seleccionado una talla válida
    if producto.tallas.exists():
        if not size:
            error_msg = 'Por favor selecciona una talla para este producto'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg}, status=400)
            messages.error(request, error_msg)
            return redirect(request.META.get('HTTP_REFERER', reverse('home')))
        
        # Verificar que la talla existe y tiene stock disponible
        talla_obj = producto.tallas.filter(talla=size).first()
        if not talla_obj:
            error_msg = f'La talla "{size}" no es válida para este producto'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg}, status=400)
            messages.error(request, error_msg)
            return redirect(request.META.get('HTTP_REFERER', reverse('home')))

    # Asegurar que el carrito siempre sea un diccionario
    cart = request.session.get('cart')
    if not isinstance(cart, dict):
        cart = {}
        request.session['cart'] = cart

    # use composite key productid:size (size may be empty string)
    key = f"{product_id}:{size}"
    
    # Verificar stock disponible antes de añadir
    if producto.tallas.exists() and size:
        talla_obj = producto.tallas.filter(talla=size).first()
        if talla_obj:
            # Calcular cantidad actual en el carrito para esta talla
            cantidad_en_carrito = int(cart.get(key, 0))
            if cantidad_en_carrito >= talla_obj.stock:
                error_msg = f'No hay suficiente stock disponible para la talla "{size}"'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg}, status=400)
                messages.error(request, error_msg)
                return redirect(request.META.get('HTTP_REFERER', reverse('home')))
    
    cart[key] = int(cart.get(key, 0)) + 1
    request.session['cart'] = cart
    request.session.modified = True

    # Si es petición AJAX, devolver JSON con datos del carrito
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        response = _build_cart_json_response(cart, {
            'message': f'{producto.nombre} añadido al carrito',
            'product_name': producto.nombre
        })
        return JsonResponse(response)

    return redirect(request.META.get('HTTP_REFERER', reverse('home')))


def cart_status(request):
    """Devuelve el estado actual del carrito en formato JSON para AJAX."""
    cart = request.session.get('cart')
    if not isinstance(cart, dict):
        cart = {}
        request.session['cart'] = cart
    response = _build_cart_json_response(cart)
    return JsonResponse(response)


def cart_view(request):
    """Muestra el contenido del carrito ."""
    cart = request.session.get('cart')
    if not isinstance(cart, dict):
        cart = {}
        request.session['cart'] = cart
    items = []
    total = 0
    if isinstance(cart, dict):
        for composite_key, qty in cart.items():
            # composite_key can be "<product_id>:<size>" or legacy "<product_id>"
            if isinstance(composite_key, str) and ':' in composite_key:
                pid_str, size = composite_key.split(':', 1)
            else:
                pid_str = str(composite_key)
                size = ''

            try:
                producto = Producto.objects.get(pk=int(pid_str))
            except Producto.DoesNotExist:
                continue

            cantidad = int(qty)
            precio_unitario = producto.precio_oferta or producto.precio
            subtotal = precio_unitario * cantidad
            items.append({'producto': producto, 'cantidad': cantidad, 'subtotal': subtotal, 'size': size})
            total += subtotal

    contexto = {'items': items, 'total': total}
    return render(request, 'cart.html', contexto)


def cart_decrement(request, product_id):
    """Decrementa la cantidad de `product_id` en el carrito de sesión."""
    if request.method != 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
        return redirect(request.META.get('HTTP_REFERER', reverse('home')))

    # Expect optional 'size' param from the form so we decrement the correct item
    size = (request.POST.get('size') or '').strip()
    cart = request.session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}
    
    key = f"{product_id}:{size}"
    # support legacy key without size
    if key not in cart and str(product_id) in cart:
        key = str(product_id)

    if key in cart:
        try:
            current_qty = int(cart.get(key, 0))
        except Exception:
            current_qty = 0
        
        # Validar que la cantidad actual sea mayor que 0 antes de decrementar
        if current_qty <= 0:
            # Si la cantidad ya es 0 o menos, no hacer nada
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                response = _build_cart_json_response(cart)
                return JsonResponse(response)
            return redirect(request.META.get('HTTP_REFERER', reverse('home')))
        
        qty = current_qty - 1
        if qty > 0:
            cart[key] = qty
        else:
            cart.pop(key, None)
        request.session['cart'] = cart
        request.session.modified = True

    # Si es petición AJAX, devolver JSON con datos del carrito
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        response = _build_cart_json_response(cart)
        return JsonResponse(response)

    return redirect(request.META.get('HTTP_REFERER', reverse('home')))


def cart_remove(request, product_id):
    """Elimina completamente `product_id` del carrito de sesión."""
    if request.method != 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
        return redirect(request.META.get('HTTP_REFERER', reverse('home')))

    size = (request.POST.get('size') or '').strip()
    cart = request.session.get('cart')
    if not isinstance(cart, dict):
        cart = {}
    
    key = f"{product_id}:{size}"
    if key in cart:
        cart.pop(key, None)
    else:
        # fallback to legacy key
        cart.pop(str(product_id), None)

    request.session['cart'] = cart
    request.session.modified = True

    # Si es petición AJAX, devolver JSON con datos del carrito
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        response = _build_cart_json_response(cart)
        return JsonResponse(response)

    return redirect(request.META.get('HTTP_REFERER', reverse('home')))


def cart_update(request):
    """Actualiza la cantidad de un item a un valor específico (POST)."""
    if request.method != 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
        return redirect(request.META.get('HTTP_REFERER', reverse('home')))

    product_id = request.POST.get('product_id')
    quantity = request.POST.get('quantity')
    size = (request.POST.get('size') or '').strip()
    if not product_id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Producto no especificado'}, status=400)
        return redirect(request.META.get('HTTP_REFERER', reverse('home')))

    try:
        q = int(quantity)
    except Exception:
        q = 0

    cart = request.session.get('cart')
    if not isinstance(cart, dict):
        cart = {}
        request.session['cart'] = cart

    key = f"{product_id}:{size}"
    # if key not present but legacy key exists, use legacy
    if key not in cart and str(product_id) in cart and size == '':
        key = str(product_id)

    if q > 0:
        cart[key] = q
    else:
        cart.pop(key, None)

    request.session['cart'] = cart
    request.session.modified = True

    # Si es petición AJAX, devolver JSON con datos del carrito
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        response = _build_cart_json_response(cart)
        return JsonResponse(response)

    return redirect(request.META.get('HTTP_REFERER', reverse('home')))


def cart_clear(request):
    """Elimina todos los productos del carrito."""
    if request.method != 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
        return redirect(request.META.get('HTTP_REFERER', reverse('home')))

    request.session['cart'] = {}
    request.session.modified = True

    # Si es petición AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Carrito vaciado',
            'cart_count': 0,
            'cart_items': [],
            'cart_total': 0.00
        })

    messages.success(request, "Carrito vaciado.")
    return redirect('cart')


def novedades(request):
    """Muestra productos ordenados por fecha de creación (más recientes primero)."""
    cutoff = timezone.now() - datetime.timedelta(days=30)
    productos_list = Producto.objects.filter(esta_disponible=True, fecha_creacion__gte=cutoff)
    
    # Aplicar filtros
    marca_filtro = request.GET.get('marca', '')
    especie_filtro = request.GET.get('especie', '')
    color_filtro = request.GET.get('color', '')
    material_filtro = request.GET.get('material', '')
    
    if marca_filtro:
        productos_list = productos_list.filter(marca_id=marca_filtro)
    if especie_filtro:
        productos_list = productos_list.filter(genero=especie_filtro)
    if color_filtro:
        productos_list = productos_list.filter(color__icontains=color_filtro)
    if material_filtro:
        productos_list = productos_list.filter(material__icontains=material_filtro)
    
    productos_list = productos_list.order_by('-fecha_creacion')
    
    # Paginación
    paginator = Paginator(productos_list, 12)
    page = request.GET.get('page')
    try:
        productos = paginator.page(page)
    except PageNotAnInteger:
        productos = paginator.page(1)
    except EmptyPage:
        productos = paginator.page(paginator.num_pages)
    
    # Obtener datos para filtros
    marcas = Marca.objects.all().order_by('nombre')
    especies = Producto.Especie.choices
    colores = Producto.objects.filter(esta_disponible=True, color__isnull=False).exclude(color='').values_list('color', flat=True).distinct().order_by('color')
    materiales = Producto.objects.filter(esta_disponible=True, material__isnull=False).exclude(material='').values_list('material', flat=True).distinct().order_by('material')
    
    contexto = {
        'productos': productos,
        'title': 'Novedades',
        'marcas': marcas,
        'especies': especies,
        'colores': colores,
        'materiales': materiales,
        'marca_filtro': marca_filtro,
        'especie_filtro': especie_filtro,
        'color_filtro': color_filtro,
        'material_filtro': material_filtro,
    }
    return render(request, 'products.html', contexto)


def productos(request):
    """Muestra productos destacados."""
    # Aplicar filtros
    marca_filtro = request.GET.get('marca', '')
    especie_filtro = request.GET.get('especie', '')
    color_filtro = request.GET.get('color', '')
    material_filtro = request.GET.get('material', '')
    
    destacados_list = Producto.objects.filter(esta_disponible=True, es_destacado=True)
    productos_list = Producto.objects.filter(esta_disponible=True).exclude(es_destacado=True)
    
    # Aplicar filtros a destacados
    if marca_filtro:
        destacados_list = destacados_list.filter(marca_id=marca_filtro)
    if especie_filtro:
        destacados_list = destacados_list.filter(genero=especie_filtro)
    if color_filtro:
        destacados_list = destacados_list.filter(color__icontains=color_filtro)
    if material_filtro:
        destacados_list = destacados_list.filter(material__icontains=material_filtro)
    
    # Aplicar filtros a productos normales
    if marca_filtro:
        productos_list = productos_list.filter(marca_id=marca_filtro)
    if especie_filtro:
        productos_list = productos_list.filter(genero=especie_filtro)
    if color_filtro:
        productos_list = productos_list.filter(color__icontains=color_filtro)
    if material_filtro:
        productos_list = productos_list.filter(material__icontains=material_filtro)
    
    destacados_list = destacados_list.order_by('-fecha_creacion')
    productos_list = productos_list.order_by('-fecha_creacion')
    
    # Paginación para productos destacados
    paginator_destacados = Paginator(destacados_list, 12)
    page_destacados = request.GET.get('page_destacados', 1)
    try:
        destacados = paginator_destacados.page(page_destacados)
    except PageNotAnInteger:
        destacados = paginator_destacados.page(1)
    except EmptyPage:
        destacados = paginator_destacados.page(paginator_destacados.num_pages)
    
    # Paginación para productos no destacados
    paginator = Paginator(productos_list, 12)
    page = request.GET.get('page', 1)
    try:
        productos = paginator.page(page)
    except PageNotAnInteger:
        productos = paginator.page(1)
    except EmptyPage:
        productos = paginator.page(paginator.num_pages)
    
    # Obtener datos para filtros
    marcas = Marca.objects.all().order_by('nombre')
    especies = Producto.Especie.choices
    colores = Producto.objects.filter(esta_disponible=True, color__isnull=False).exclude(color='').values_list('color', flat=True).distinct().order_by('color')
    materiales = Producto.objects.filter(esta_disponible=True, material__isnull=False).exclude(material='').values_list('material', flat=True).distinct().order_by('material')
    
    contexto = {
        'destacados': destacados,
        'productos': productos,
        'title': 'Productos',
        'marcas': marcas,
        'especies': especies,
        'colores': colores,
        'materiales': materiales,
        'marca_filtro': marca_filtro,
        'especie_filtro': especie_filtro,
        'color_filtro': color_filtro,
        'material_filtro': material_filtro,
    }
    return render(request, 'products.html', contexto)


def ofertas(request):
    """Muestra productos que tienen precio de oferta definido."""
    productos_list = Producto.objects.filter(esta_disponible=True, precio_oferta__isnull=False)
    
    # Aplicar filtros
    marca_filtro = request.GET.get('marca', '')
    especie_filtro = request.GET.get('especie', '')
    color_filtro = request.GET.get('color', '')
    material_filtro = request.GET.get('material', '')
    
    if marca_filtro:
        productos_list = productos_list.filter(marca_id=marca_filtro)
    if especie_filtro:
        productos_list = productos_list.filter(genero=especie_filtro)
    if color_filtro:
        productos_list = productos_list.filter(color__icontains=color_filtro)
    if material_filtro:
        productos_list = productos_list.filter(material__icontains=material_filtro)
    
    productos_list = productos_list.order_by('-fecha_creacion')
    
    # Paginación
    paginator = Paginator(productos_list, 12)
    page = request.GET.get('page')
    try:
        productos = paginator.page(page)
    except PageNotAnInteger:
        productos = paginator.page(1)
    except EmptyPage:
        productos = paginator.page(paginator.num_pages)
    
    # Obtener datos para filtros
    marcas = Marca.objects.all().order_by('nombre')
    especies = Producto.Especie.choices
    colores = Producto.objects.filter(esta_disponible=True, color__isnull=False).exclude(color='').values_list('color', flat=True).distinct().order_by('color')
    materiales = Producto.objects.filter(esta_disponible=True, material__isnull=False).exclude(material='').values_list('material', flat=True).distinct().order_by('material')
    
    contexto = {
        'productos': productos,
        'title': 'Ofertas',
        'marcas': marcas,
        'especies': especies,
        'colores': colores,
        'materiales': materiales,
        'marca_filtro': marca_filtro,
        'especie_filtro': especie_filtro,
        'color_filtro': color_filtro,
        'material_filtro': material_filtro,
    }
    return render(request, 'products.html', contexto)


def product_detail(request, product_id):
    """Muestra la página de detalle de un producto."""
    producto = get_object_or_404(Producto, pk=product_id, esta_disponible=True)

    # prepare context for template
    contexto = {
        'producto': producto,
        'title': producto.nombre,
    }
    return render(request, 'product_detail.html', contexto)

def acerca_de(request):
    return render(request, "acerca_de.html")

def contacto(request):
    contacto_message = None
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        email = request.POST.get("email")  
        mensaje = request.POST.get("mensaje")

        MensajeContacto.objects.create(
            nombre=nombre,
            email=email,
            mensaje=mensaje
        )
        enviar_email_respuesta_contacto_admin(
            nombre=nombre,
            email_destino="mypetshop.309@gmail.com",  # o un settings.CONTACT_EMAIL
            mensaje_usuario=f"De: {nombre} ({email})\n\n{mensaje}",
        )
        # 2. Enviar email de confirmación al usuario (SendGrid)
        try:
            enviar_email_respuesta_contacto(nombre, email, mensaje)
            enviar_email_respuesta_contacto_admin(nombre=nombre,
            email_destino="mypetshop.309@gmail.com",  # o un settings.CONTACT_EMAIL
            mensaje_usuario=f"De: {nombre} ({email})\n\n{mensaje}",
            )
            print("✅ Email de contacto enviado correctamente a", email)
            print("✅ Email de notificación enviado al admin")
        except Exception as e:
            print("❌ Error enviando email de contacto:", e)

        contacto_message = "¡Gracias! Tu mensaje se ha enviado correctamente. Revisa tu correo electrónico (el mensaje enviado puede llegar a la carpeta de spam o correo no deseado). Te responderemos pronto."
        messages.success(request, contacto_message)
        return redirect('contacto')
    
    # Obtener solo mensajes relacionados con contacto
    from django.contrib.messages import get_messages
    contacto_messages = []
    storage = get_messages(request)
    for message in storage:
        msg_text = str(message)
        if any(keyword in msg_text.lower() for keyword in ['mensaje', 'contacto', 'enviado', 'gracias']):
            contacto_messages.append(message)
    
    return render(request, "contacto.html", {"contacto_messages": contacto_messages})


def enviar_email_respuesta_contacto(nombre, email_destino, mensaje_usuario):
    """Envía un correo de confirmación al usuario que ha usado el formulario de contacto."""
    html = f"""
    <table width="100%" cellpadding="0" cellspacing="0"
           style="font-family:Arial, sans-serif; background:#f7f7f7; padding:20px;">
      <tr>
        <td align="center">
          <table width="600" cellpadding="0" cellspacing="0"
                 style="background:#ffffff; border-radius:12px; overflow:hidden;">
            <!-- Header -->
            <tr>
              <td style="background:#4a90e2; padding:20px; text-align:center; color:white;">
                <h1 style="margin:0; font-size:26px;">🐾 My Pet Shop</h1>
              </td>
            </tr>

            <!-- Body -->
            <tr>
              <td style="padding:30px; color:#333;">
                <h2 style="margin-top:0;">
                    ¡Hola {nombre or "amigo"}! 🐶
                </h2>

                <p style="font-size:15px; line-height:22px;">
                    Hemos recibido tu mensaje a través del formulario de contacto.
                </p>

                <p style="font-size:15px; line-height:22px;">
                    <strong>Esto es lo que nos has enviado:</strong>
                </p>

                <blockquote style="font-size:14px; line-height:22px; color:#555; border-left:4px solid #4a90e2; margin:15px 0; padding-left:10px;">
                    {mensaje_usuario}
                </blockquote>

                <p style="font-size:15px; line-height:22px;">
                    Te responderemos lo antes posible a este mismo correo: <strong>{email_destino}</strong>.
                </p>

                <hr style="border:none; border-top:1px solid #ddd; margin:30px 0;">

                <p style="font-size:14px; color:#777; text-align:center;">
                    Este es un correo automático de confirmación.
                    <br><br>
                    
                </p>

                <p style="font-size:14px; color:#777; text-align:center;">
                    ❤️ Gracias por contactar con My Pet Shop
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
    """

    mensaje = Mail(
        from_email=settings.EMAIL_FROM,
        to_emails=email_destino,
        subject="Hemos recibido tu mensaje 🐾 - My Pet Shop",
        html_content=html,
    )

    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    sg.send(mensaje)


def enviar_email_respuesta_contacto_admin(nombre, email_destino, mensaje_usuario):
    asunto = f"Nuevo mensaje de contacto de {nombre}"

    html = f"""
    <table width="100%" cellpadding="0" cellspacing="0"
           style="font-family:Arial, sans-serif; background:#f7f7f7; padding:20px;">
      <tr>
        <td align="center">
          <table width="600" cellpadding="0" cellspacing="0"
                 style="background:#ffffff; border-radius:12px; overflow:hidden;">
            <!-- Header -->
            <tr>
              <td style="background:#4a90e2; padding:20px; text-align:center; color:white;">
                <h1 style="margin:0; font-size:24px;">🐾 My Pet Shop – Nuevo mensaje</h1>
              </td>
            </tr>

            <!-- Body -->
            <tr>
              <td style="padding:24px; color:#333; font-size:15px; line-height:22px;">
                <p style="margin-top:0;">
                    Has recibido un nuevo mensaje desde el formulario de
                    <strong>“Contáctanos”</strong>.
                </p>

                <p>
                    <strong>Nombre:</strong> {nombre}<br>
                </p>

                <p style="margin-top:20px;"><strong>Mensaje:</strong></p>
                <div style="background:#f4f4f4; padding:15px; border-radius:8px;">
                    {mensaje_usuario.replace('\n', '<br>')}
                </div>

                <p style="font-size:13px; color:#777; margin-top:24px;">
                    Este correo se ha enviado automáticamente desde la web de My Pet Shop.
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
    """

    message = Mail(
        from_email=settings.EMAIL_FROM,      # tu remitente configurado (SendGrid)
        to_emails=settings.EMAIL_FROM,             # tu Gmail de la tienda, por ejemplo
        subject=asunto,
        html_content=html,
    )

   

    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    sg.send(message)



def categorias(request):
    # Mostrar las categorías reales definidas en el modelo `Categoria`.
    categorias = Categoria.objects.all().order_by('nombre')
    return render(request, "categorias.html", {"categorias": categorias})


def categoria_detail(request, categoria_id):
    """Muestra los productos que pertenecen a la categoría indicada."""
    categoria = get_object_or_404(Categoria, pk=categoria_id)
    productos_list = Producto.objects.filter(categoria=categoria, esta_disponible=True).order_by('-fecha_creacion')
    
    # Paginación
    paginator = Paginator(productos_list, 12)
    page = request.GET.get('page')
    try:
        productos = paginator.page(page)
    except PageNotAnInteger:
        productos = paginator.page(1)
    except EmptyPage:
        productos = paginator.page(paginator.num_pages)
    
    contexto = {
        'productos': productos,
        'title': categoria.nombre,
        'categoria': categoria,
        'es_categoria': True,  # Flag para identificar que es vista de categoría
    }
    return render(request, 'products.html', contexto)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = EmailAuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)
        return redirect('home')

    return render(request, 'login.html', {'form': form, 'next': request.GET.get('next', '')})


def logout_view(request):
    logout(request)
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect('home')


def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    next_url = request.GET.get('next') or request.POST.get('next', '')
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            login(request, cliente.user)
            messages.success(request, "Tu cuenta se creó correctamente.")
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('checkout_datos')
    else:
        form = RegistroForm()

    return render(request, 'register.html', {'form': form, 'next': next_url})


def seguimiento_pedido(request):
    pedido = None
    found = False
    form = SeguimientoPedidoForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            codigo = form.cleaned_data["numero_pedido"].strip()
            pedido = Pedido.objects.select_related("cliente").prefetch_related("items__producto").filter(
                numero_pedido__iexact=codigo
            ).first()
            if pedido:
                found = True
            else:
                messages.error(request, "No encontramos un pedido con ese código. Revisa el número y vuelve a intentarlo.")

    return render(
        request,
        "tracking.html",
        {
            "form": form,
            "pedido": pedido if found else None,
        },
    )

def checkout_datos_cliente_envio(request):
    cart = request.session.get("cart", {})
    if not cart:
        messages.error(request, "Tu carrito está vacío.")
        return redirect("cart")

    # Si el usuario está autenticado, usar el flujo normal
    if request.user.is_authenticated:
        cliente = getattr(request.user, "cliente", None)
        email_real = (request.user.email or "").strip().lower()
        if email_real:
            lookup_email = email_real
        else:
            username_slug = (request.user.username or "usuario").strip().lower()
            lookup_email = username_slug if "@" in username_slug else f"{username_slug}@local"

        if not cliente and lookup_email:
            cliente = Cliente.objects.filter(email__iexact=lookup_email).first()
            if cliente and cliente.user is None:
                cliente.user = request.user
                cliente.save(update_fields=["user"])

        if not cliente:
            nombre_base = request.user.first_name or (lookup_email.split("@")[0] if lookup_email else "")
            cliente = Cliente.objects.create(
                user=request.user,
                email=lookup_email or request.user.username,
                nombre=nombre_base or "Cliente",
                apellidos=request.user.last_name or "",
            )

        if email_real and cliente.email != email_real:
            cliente.email = email_real
            cliente.save(update_fields=["email"])
        elif not cliente.email and lookup_email:
            cliente.email = lookup_email
            cliente.save(update_fields=["email"])

        form = ClienteEnvioForm(request.POST or None, instance=cliente)
        if request.method == "POST":
            shipping_method = request.POST.get("shipping_method", "delivery") 
            request.session['shipping_method'] = shipping_method
            request.session.modified = True
        
        if form.is_valid():
            form.save()
            messages.success(request, "Datos guardados correctamente. Revisa el pago.")
            return redirect("detalles_pago")

        return render(
            request,
            "checkout_datos.html",
            {
                "form": form,
                "cliente": cliente,
                "email_usuario": request.user.email or lookup_email,
                "shipping_method": request.session.get('shipping_method', 'delivery'),
            },
        )
    
    # Usuario no autenticado - mostrar formularios de login/registro y checkout invitado
    else:
        login_form = EmailAuthenticationForm(request, data=request.POST if request.POST.get('form_type') == 'login' else None)
        register_form = RegistroForm(request.POST if request.POST.get('form_type') == 'register' else None)
        guest_form = GuestCheckoutForm(request.POST if request.POST.get('form_type') == 'guest' else None)
        
        # Manejar login
        if request.method == 'POST' and request.POST.get('form_type') == 'login' and login_form.is_valid():
            user = login_form.get_user()
            login(request, user)
            messages.success(request, "Sesión iniciada correctamente.")
            return redirect("checkout_datos")
        
        # Manejar registro
        if request.method == 'POST' and request.POST.get('form_type') == 'register' and register_form.is_valid():
            cliente = register_form.save()
            login(request, cliente.user)
            messages.success(request, "Tu cuenta se creó correctamente.")
            return redirect("checkout_datos")
        
        # Manejar checkout invitado
        if request.method == 'POST' and request.POST.get('form_type') == 'guest' and guest_form.is_valid():
            shipping_method = request.POST.get("shipping_method", "delivery")
            request.session["shipping_method"] = shipping_method
            request.session.modified = True
            
            email = guest_form.cleaned_data['email'].strip().lower()
            
            # Verificar si ya existe un cliente con ese email que tiene usuario
            existing_cliente_with_user = Cliente.objects.filter(email__iexact=email, user__isnull=False).first()
            if existing_cliente_with_user:
                messages.error(request, f"Ya existe una cuenta con el email {email}. Por favor, inicia sesión para continuar.")
                # Mostrar formulario de login
                return render(
                    request,
                    "checkout_datos.html",
                    {
                        "login_form": EmailAuthenticationForm(request),
                        "register_form": register_form,
                        "guest_form": guest_form,
                        "is_guest": True,
                        "shipping_method": shipping_method,
                    },
                )
            
            # Buscar si ya existe un cliente con ese email (sin usuario)
            cliente = Cliente.objects.filter(email__iexact=email, user__isnull=True).first()
            
            if not cliente:
                # Crear nuevo cliente invitado (sin usuario)
                try:
                    cliente = Cliente.objects.create(
                        email=email,
                        nombre=guest_form.cleaned_data['nombre'],
                        apellidos=guest_form.cleaned_data.get('apellidos', ''),
                        telefono=guest_form.cleaned_data.get('telefono', ''),
                        direccion=guest_form.cleaned_data['direccion'],
                        ciudad=guest_form.cleaned_data['ciudad'],
                        codigo_postal=guest_form.cleaned_data['codigo_postal'],
                        user=None,  # Cliente invitado sin cuenta
                    )
                except Exception as e:
                    # Si falla por email duplicado u otro error
                    messages.error(request, "Error al crear el cliente. Por favor, verifica tus datos.")
                    return render(
                        request,
                        "checkout_datos.html",
                        {
                            "login_form": login_form,
                            "register_form": register_form,
                            "guest_form": guest_form,
                            "is_guest": True,
                            "shipping_method": shipping_method,
                        },
                    )
            else:
                # Actualizar cliente existente
                cliente.nombre = guest_form.cleaned_data['nombre']
                cliente.apellidos = guest_form.cleaned_data.get('apellidos', '')
                cliente.telefono = guest_form.cleaned_data.get('telefono', '')
                cliente.direccion = guest_form.cleaned_data['direccion']
                cliente.ciudad = guest_form.cleaned_data['ciudad']
                cliente.codigo_postal = guest_form.cleaned_data['codigo_postal']
                cliente.save()
            
            # Guardar cliente_id en sesión para usar en el checkout
            request.session['guest_cliente_id'] = cliente.id
            request.session.modified = True
            
            messages.success(request, "Datos guardados correctamente. Revisa el pago.")
            return redirect("detalles_pago")
        
        return render(
            request,
            "checkout_datos.html",
            {
                "login_form": login_form,
                "register_form": register_form,
                "guest_form": guest_form,
                "is_guest": True,
                "shipping_method": request.session.get('shipping_method', 'delivery'),
            },
        )

def detalles_pago(request):
    # Obtener cliente: autenticado o invitado
    if request.user.is_authenticated:
        cliente = getattr(request.user, "cliente", None)
    else:
        # Cliente invitado desde sesión
        guest_cliente_id = request.session.get('guest_cliente_id')
        if guest_cliente_id:
            try:
                cliente = Cliente.objects.get(pk=guest_cliente_id, user__isnull=True)
            except Cliente.DoesNotExist:
                cliente = None
        else:
            cliente = None
    
    if not cliente:
        messages.error(request, "Primero debes completar tus datos de envío.")
        return redirect("checkout_datos")

    cart = request.session.get("cart", {})
    if not cart:
        messages.error(request, "Tu carrito está vacío.")
        return redirect("cart")

    items = []
    subtotal = Decimal("0.00")

    for key, cantidad in cart.items():
        # key debería ser "product_id:talla"
        key_str = str(key)
        if ":" in key_str:
            pid_str, talla = key_str.split(":", 1)
        else:
            pid_str = key_str
            talla = ""

        try:
            producto = Producto.objects.get(pk=int(pid_str))
        except Producto.DoesNotExist:
            # DEBUG: ver qué id está fallando
            print("⚠ Producto no encontrado, id =", pid_str, "key completa =", key_str)
            continue  # saltamos este item

        cantidad = int(cantidad)
        precio_unitario = producto.precio_oferta or producto.precio
        total_item = precio_unitario * cantidad

        items.append({
            "producto": producto,
            "cantidad": cantidad,
            "talla": talla,
            "subtotal": total_item,
        })
        subtotal += total_item

    # Si después de limpiar no queda nada, vaciamos carrito
    if not items:
        request.session["cart"] = {}
        request.session.modified = True
        messages.error(
            request,
            "Tu carrito se ha vaciado porque algunos productos ya no están disponibles."
        )
        return redirect("cart")

    impuestos = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    descuento = Decimal("0.00")

    shipping_method = request.session.get('shipping_method', 'delivery')

    if shipping_method == 'pickup':
        coste_entrega = Decimal("0.00")
        envio_gratis = True
    else:
        coste_entrega = Decimal("0.00") if subtotal >= Decimal("30.00") else Decimal("2.99")
        envio_gratis = subtotal >= Decimal("30.00")

    total = subtotal + impuestos + coste_entrega - descuento

    return render(
        request,
        "detalles_pago.html",
        {
            "cliente": cliente,
            "items": items,
            "subtotal": subtotal,
            "impuestos": impuestos,
            "coste_entrega": coste_entrega,
            "descuento": descuento,
            "total": total,
            "shipping_method": shipping_method,
            "envio_gratis": envio_gratis,
        },
    )



def generar_numero_pedido():
    return f"MP-{timezone.now().strftime('%Y%m%d%H%M%S')}-{get_random_string(4).upper()}"


def checkout_stripe(request):
    if request.method != "POST":
        return redirect("detalles_pago")

    cart = request.session.get("cart", {})
    if not cart:
        messages.error(request, "Tu carrito está vacío.")
        return redirect("cart")

    # Obtener cliente: autenticado o invitado
    if request.user.is_authenticated:
        cliente = getattr(request.user, "cliente", None)
    else:
        # Cliente invitado desde sesión
        guest_cliente_id = request.session.get('guest_cliente_id')
        if guest_cliente_id:
            try:
                cliente = Cliente.objects.get(pk=guest_cliente_id, user__isnull=True)
            except Cliente.DoesNotExist:
                cliente = None
        else:
            cliente = None
    
    if not cliente:
        messages.error(request, "Primero debes completar tus datos de envío.")
        return redirect("checkout_datos")

    # Calcular totales y preparar items
    subtotal = Decimal("0.00")
    impuestos = Decimal("0.00")
    coste_entrega = Decimal("0.00")
    descuento = Decimal("0.00")

    line_items = []          # para Stripe
    items_lista = []         # para crear ItemPedido

    for key, cantidad in cart.items():
        key_str = str(key)
        if ":" in key_str:
            pid_str, talla = key_str.split(":", 1)
        else:
            pid_str = key_str
            talla = ""

        try:
            producto = Producto.objects.get(pk=int(pid_str))
        except Producto.DoesNotExist:
            # Debug opcional:
            # print("⚠ Producto no encontrado en checkout_stripe, id =", pid_str)
            continue

        cantidad = int(cantidad)
        precio_unitario = producto.precio_oferta or producto.precio or Decimal("0.00")
        total_item = precio_unitario * cantidad

        subtotal += total_item

        items_lista.append((producto, talla, cantidad, precio_unitario, total_item))

        line_items.append({
            "price_data": {
                "currency": "eur",
                "product_data": {"name": producto.nombre},
                "unit_amount": int(precio_unitario * 100),  # en céntimos
            },
            "quantity": cantidad,
        })

    # Si no hay ningún producto válido, vaciamos carrito y salimos
    if not items_lista:
        request.session["cart"] = {}
        request.session.modified = True
        messages.error(
            request,
            "Tu carrito se ha vaciado porque los productos ya no están disponibles."
        )
        return redirect("cart")

    impuestos = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    shipping_method = request.session.get('shipping_method', 'delivery')
    
    if shipping_method == 'pickup':
        coste_entrega = Decimal("0.00")
    else:
        coste_entrega = Decimal("0.00") if subtotal >= Decimal("30.00") else Decimal("2.99")

    total = subtotal + impuestos + coste_entrega - descuento

    # Crear Pedido
    pedido = Pedido.objects.create(
        cliente=cliente,
        numero_pedido=generar_numero_pedido(),
        subtotal=subtotal,
        impuestos=impuestos,
        coste_entrega=coste_entrega,
        descuento=descuento,
        total=total,
        estado=Pedido.Estados.PENDIENTE,
        metodo_pago="stripe_test",
        direccion_envio=cliente.direccion,
        telefono=cliente.telefono,
    )

    # Crear Items de pedido
    for producto, talla, cantidad, precio_unitario, total_item in items_lista:
        ItemPedido.objects.create(
            pedido=pedido,
            producto=producto,
            talla=talla,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            total=total_item,
        )

    # Enviar a Stripe un único `line_item` con el total final (incluye impuestos y envío)
    # para que la pantalla de Checkout muestre claramente el importe total.
    summary_line = [
        {
            "price_data": {
                "currency": "eur",
                "product_data": {"name": f"Pedido {pedido.numero_pedido} (importe total)"},
                "unit_amount": int(total * 100),
            },
            "quantity": 1,
        }
    ]

    metadata = {
        "pedido_id": str(pedido.id_pedido),
        "subtotal": str(subtotal),
        "impuestos": str(impuestos),
        "coste_entrega": str(coste_entrega),
        "descuento": str(descuento),
        "total": str(total),
    }

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=summary_line,
        metadata=metadata,
        success_url=request.build_absolute_uri(
            reverse("pago_ok", args=[pedido.id_pedido])
        ),
        cancel_url=request.build_absolute_uri(
            reverse("pago_cancelado", args=[pedido.id_pedido])
        ),
    )

    return redirect(session.url, code=303)

def checkout_contrareembolso(request):
    # 1) Comprobar carrito
    cart = request.session.get("cart", {})
    if not cart:
        messages.error(request, "Tu carrito está vacío.")
        return redirect("cart")

    # 2) Obtener cliente: autenticado o invitado (usar guest_cliente_id usado en checkout_datos)
    if request.user.is_authenticated:
        cliente = getattr(request.user, "cliente", None)
    else:
        guest_cliente_id = request.session.get('guest_cliente_id')
        if guest_cliente_id:
            try:
                cliente = Cliente.objects.get(pk=guest_cliente_id, user__isnull=True)
            except Cliente.DoesNotExist:
                cliente = None
        else:
            cliente = None

    if not cliente:
        messages.error(request, "Primero debes completar tus datos de envío.")
        return redirect("checkout_datos")

    # 3) Reconstruir items y totales igual que en detalles_pago / Stripe
    items_lista = []
    subtotal = Decimal("0.00")

    for key, cantidad in cart.items():
        key_str = str(key)
        if ":" in key_str:
            pid_str, talla = key_str.split(":", 1)
        else:
            pid_str = key_str
            talla = ""

        producto = get_object_or_404(Producto, pk=int(pid_str))
        cantidad = int(cantidad)
        precio_unitario = producto.precio_oferta or producto.precio or Decimal("0.00")
        total_item = precio_unitario * cantidad

        subtotal += total_item
        items_lista.append((producto, talla, cantidad, precio_unitario, total_item))

    impuestos = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"))  # o tu regla
    if subtotal >= Decimal("30.00"):
        coste_entrega = Decimal("0.00")
    else:
        coste_entrega = Decimal("2.99")

    descuento = Decimal("0.00")
    total = subtotal + impuestos + coste_entrega - descuento

    # 4) Crear Pedido en BD con método contrareembolso
    pedido = Pedido.objects.create(
        cliente=cliente,
        numero_pedido=generar_numero_pedido(),
        subtotal=subtotal,
        impuestos=impuestos,
        coste_entrega=coste_entrega,
        descuento=descuento,
        total=total,
        estado=Pedido.Estados.PENDIENTE,
        metodo_pago="contrareembolso",
        direccion_envio=cliente.direccion,
        telefono=cliente.telefono,
    )

    # 5) Crear líneas de pedido
    for producto, talla, cantidad, precio_unitario, total_item in items_lista:
        ItemPedido.objects.create(
            pedido=pedido,
            producto=producto,
            talla=talla,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            total=total_item,
        )

    # 5b) Restar stock de los productos comprados (similar a pago_ok)
    # Es importante decrementar el stock aquí también para contrareembolso
    # para evitar sobreventa cuando el pedido queda pendiente de pago en entrega.
    for item in pedido.items.all():
        producto = item.producto
        cantidad = item.cantidad
        talla = item.talla or ''

        if talla:
            try:
                talla_obj = TallaProducto.objects.get(producto=producto, talla=talla)
                if talla_obj.stock >= cantidad:
                    talla_obj.stock -= cantidad
                    talla_obj.save()
                else:
                    # Ajustar a 0 y avisar por consola (no romper el flujo)
                    print(f"⚠ Advertencia: Stock insuficiente para {producto.nombre} talla {talla}. Stock actual: {talla_obj.stock}, solicitado: {cantidad}")
                    talla_obj.stock = 0
                    talla_obj.save()
            except TallaProducto.DoesNotExist:
                print(f"⚠ Error: No se encontró la talla '{talla}' para el producto {producto.nombre}")
        else:
            if producto.stock >= cantidad:
                producto.stock -= cantidad
                producto.save()
            else:
                print(f"⚠ Advertencia: Stock insuficiente para {producto.nombre}. Stock actual: {producto.stock}, solicitado: {cantidad}")
                producto.stock = 0
                producto.save()

    # 6) Vaciar carrito
    request.session["cart"] = {}
    request.session.modified = True

    # 7) Enviar email (tu función, tal cual)
    try:
        enviar_email_contrareembolso(pedido)
    except Exception as e:
        print("Error email:", e)

    # 8) Mostrar página de OK contrareembolso
    return render(request, "pago_contrareembolso_ok.html", {"pedido": pedido})


def enviar_email_contrareembolso(pedido):
    """Email de confirmación para pedidos con pago contrareembolso."""
    cliente = pedido.cliente

    html = f"""
    <table width="100%" cellpadding="0" cellspacing="0"
           style="font-family:Arial, sans-serif; background:#f7f7f7; padding:20px;">
      <tr>
        <td align="center">
          <table width="600" cellpadding="0" cellspacing="0"
                 style="background:#ffffff; border-radius:12px; overflow:hidden;">
            <!-- Header -->
            <tr>
              <td style="background:#4a90e2; padding:20px; text-align:center; color:white;">
                <h1 style="margin:0; font-size:26px;">🐾 My Pet Shop</h1>
              </td>
            </tr>

            <!-- Body -->
            <tr>
              <td style="padding:30px; color:#333;">
                <h2 style="margin-top:0;">
                    ¡Gracias por tu compra, {pedido.cliente.nombre}! 🎉
                </h2>

                <p style="font-size:15px; line-height:22px;">
                    Hemos recibido tu pedido <strong>#{pedido.numero_pedido}</strong>.
                </p>

                <p style="font-size:15px; line-height:22px;">
                    <strong>Método de pago:</strong> Contrareembolso
                </p>

                <p style="font-size:15px; line-height:22px;">
                    <strong>Total a pagar al repartidor:</strong> {pedido.total} €
                </p>

                <p style="font-size:15px; line-height:22px;">
                    No hemos hecho ningún cargo ahora: pagarás cuando recibas tu pedido
                    en la dirección indicada 🏠.
                </p>

                <p style="font-size:15px; margin-top:25px;">
                    Puedes comprobar el estado de tu pedido aquí:
                </p>

                <!-- Botón de seguimiento -->
                <div style="text-align:center; margin:30px 0;">
                  <a href="https://mypetshop-6cea.onrender.com/seguimiento/"
                     style="background:#4a90e2; padding:14px 28px; color:white;
                            text-decoration:none; font-size:16px; border-radius:8px;
                            display:inline-block;">
                    Seguir mi pedido 📦
                  </a>
                </div>

                <p style="font-size:15px; line-height:22px; color:#444; margin-top:20px;">
                    Ten en cuenta que el repartidor no siempre lleva cambio, por lo que es recomendable tener el importe exacto preparado.
                </p>
      

                <hr style="border:none; border-top:1px solid #ddd; margin:30px 0;">

                <p style="font-size:14px; color:#777; text-align:center;">
                        Este es un correo automático, por favor no respondas a este mensaje.
                        <br><br>
                        Si tienes dudas, contáctanos en 
                        <a href="mailto:mypetshop.309@gmail.com" style="color:#4da3ff;">
                            mypetshop.309@gmail.com
                        </a>.
                </p>
                <p style="font-size:14px; color:#777; text-align:center;">
                    ❤️ Gracias por confiar en My Pet Shop
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
    """

    mensaje = Mail(
        from_email=settings.EMAIL_FROM,
        to_emails=cliente.email,
        subject=f"Confirmación de tu pedido #{pedido.numero_pedido} (contrareembolso)",
        html_content=html,
    )

    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    sg.send(mensaje)
    print("✔ Email contrareembolso enviado correctamente")



def pago_ok(request, pedido_id):
    pedido = get_object_or_404(Pedido, id_pedido=pedido_id)
    
    # Solo procesar si el pedido aún no está pagado (evitar procesar dos veces)
    if pedido.estado != Pedido.Estados.PAGADO:
        pedido.estado = Pedido.Estados.PAGADO
        pedido.save()
        
        # Restar stock de los productos comprados
        items = pedido.items.all()
        for item in items:
            producto = item.producto
            cantidad = item.cantidad
            talla = item.talla or ''
            
            if talla:
                # Si el producto tiene talla, restar del stock de la talla específica
                try:
                    talla_obj = TallaProducto.objects.get(producto=producto, talla=talla)
                    if talla_obj.stock >= cantidad:
                        talla_obj.stock -= cantidad
                        talla_obj.save()
                    else:
                        # Si no hay suficiente stock, ajustar a 0 (no debería pasar si la validación es correcta)
                        print(f"⚠ Advertencia: Stock insuficiente para {producto.nombre} talla {talla}. Stock actual: {talla_obj.stock}, solicitado: {cantidad}")
                        talla_obj.stock = 0
                        talla_obj.save()
                except TallaProducto.DoesNotExist:
                    print(f"⚠ Error: No se encontró la talla '{talla}' para el producto {producto.nombre}")
            else:
                # Si no tiene talla, restar del stock general del producto
                if producto.stock >= cantidad:
                    producto.stock -= cantidad
                    producto.save()
                else:
                    # Si no hay suficiente stock, ajustar a 0
                    print(f"⚠ Advertencia: Stock insuficiente para {producto.nombre}. Stock actual: {producto.stock}, solicitado: {cantidad}")
                    producto.stock = 0
                    producto.save()

    # --- Email de confirmación ---

    mensaje = Mail(
        from_email=settings.EMAIL_FROM,
        to_emails=pedido.cliente.email,
        subject=f"Confirmación de tu pedido #{pedido.numero_pedido}",
        html_content = f"""
        <table width="100%" cellpadding="0" cellspacing="0" style="font-family:Arial, sans-serif; background:#f7f7f7; padding:20px;">
        <tr>
            <td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff; border-radius:12px; overflow:hidden;">
                
                <!-- Header -->
                <tr>
                <td style="background:#4a90e2; padding:20px; text-align:center; color:white;">
                    <h1 style="margin:0; font-size:26px;">🐾 My Pet Shop</h1>
                </td>
                </tr>

                <!-- Body -->
                <tr>
                <td style="padding:30px; color:#333;">
                    <h2 style="margin-top:0;">¡Gracias por tu compra, {pedido.cliente.nombre}! 🎉</h2>

                    <p style="font-size:15px; line-height:22px;">
                    Hemos recibido tu pedido <strong>#{pedido.numero_pedido}</strong>.
                    </p>

                    <p style="font-size:15px; line-height:22px;">
                    <strong>Total:</strong> {pedido.total} €
                    </p>

                    <p style="font-size:15px; line-height:22px;">
                    Te avisaremos cuando tu pedido salga de nuestro almacén 🐾
                    </p>

                    <p style="font-size:15px; margin-top:25px;">
                    Puedes comprobar el estado de tu pedido aquí:
                    </p>

                    <!-- Botón de seguimiento -->
                    <div style="text-align:center; margin:30px 0;">
                    <a href="https://mypetshop-6cea.onrender.com/seguimiento/"
                        style="background:#4a90e2; padding:14px 28px; color:white;
                                text-decoration:none; font-size:16px; border-radius:8px;
                                display:inline-block;">
                        Seguir mi pedido 📦
                    </a>
                    </div>

                    <hr style="border:none; border-top:1px solid #ddd; margin:30px 0;">

                    <p style="font-size:14px; color:#777; text-align:center;">
                        Este es un correo automático, por favor no respondas a este mensaje.
                        <br><br>
                        Si tienes dudas, contáctanos en 
                        <a href="mailto:mypetshop.309@gmail.com" style="color:#4da3ff;">
                            mypetshop.309@gmail.com
                        </a>.
                    </p>


                    <p style="font-size:14px; color:#777; text-align:center;">
                    ❤️ Gracias por confiar en My Pet Shop
                    </p>
                </td>
                </tr>

            </table>
            </td>
        </tr>
        </table>
        """

        
        
    )

    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        sg.send(mensaje)
        print("✔ Email enviado correctamente")
    except Exception as e:
        print("❌ Error enviando email:", e)


    # vaciar carrito
    request.session["cart"] = {}
    request.session.modified = True

    return render(request, "pago_ok.html", {"pedido": pedido})


def pago_cancelado(request, pedido_id):
    pedido = get_object_or_404(Pedido, id_pedido=pedido_id)
    pedido.estado = Pedido.Estados.CANCELADO
    pedido.save()

    return render(request, "pago_cancelado.html", {"pedido": pedido})
