from urllib import request
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
import datetime

from .models import Articulo, Escaparate, Categoria, Producto


def index(request):
    """Si se recibe ?q=texto, filtra por nombre, descripcion, genero, color o material."""
    q = request.GET.get('q', '')
    if q:
        query = q.strip()
        filtros = Q(nombre__icontains=query) | Q(descripcion__icontains=query) | Q(genero__icontains=query) | Q(color__icontains=query) | Q(material__icontains=query)
        productos = Producto.objects.filter(filtros, esta_disponible=True).order_by('-es_destacado', '-fecha_creacion')
    else:
        productos = Producto.objects.filter(esta_disponible=True).order_by('-es_destacado', '-fecha_creacion')[:8]
        query = ''

    contexto = {'productos': productos, 'query': query}
    return render(request, 'index.html', contexto)


def add_to_cart(request, product_id):
    """Añade un producto al carrito guardado en la sesión."""
    if request.method != 'POST':
        return redirect(request.META.get('HTTP_REFERER', reverse('home')))

    # Allow selecting a talla (size). Expect POST param 'size'
    size = (request.POST.get('size') or '').strip()
    producto = get_object_or_404(Producto, pk=product_id, esta_disponible=True)

    cart = request.session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}

    # use composite key productid:size (size may be empty string)
    key = f"{product_id}:{size}"
    cart[key] = int(cart.get(key, 0)) + 1
    request.session['cart'] = cart
    request.session.modified = True

    return redirect(request.META.get('HTTP_REFERER', reverse('home')))


def cart_view(request):
    """Muestra el contenido del carrito ."""
    cart = request.session.get('cart', {})
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
            subtotal = producto.precio * cantidad
            items.append({'producto': producto, 'cantidad': cantidad, 'subtotal': subtotal, 'size': size})
            total += subtotal

    contexto = {'items': items, 'total': total}
    return render(request, 'cart.html', contexto)


def cart_decrement(request, product_id):
    """Decrementa la cantidad de `product_id` en el carrito de sesión."""
    if request.method != 'POST':
        return redirect(request.META.get('HTTP_REFERER', reverse('home')))

    # Expect optional 'size' param from the form so we decrement the correct item
    size = (request.POST.get('size') or '').strip()
    cart = request.session.get('cart', {})
    if isinstance(cart, dict):
        key = f"{product_id}:{size}"
        # support legacy key without size
        if key not in cart and str(product_id) in cart:
            key = str(product_id)

        if key in cart:
            try:
                qty = int(cart.get(key, 0)) - 1
            except Exception:
                qty = 0
            if qty > 0:
                cart[key] = qty
            else:
                cart.pop(key, None)
            request.session['cart'] = cart
            request.session.modified = True

    return redirect(request.META.get('HTTP_REFERER', reverse('home')))


def cart_remove(request, product_id):
    """Elimina completamente `product_id` del carrito de sesión."""
    if request.method != 'POST':
        return redirect(request.META.get('HTTP_REFERER', reverse('home')))

    size = (request.POST.get('size') or '').strip()
    cart = request.session.get('cart', {})
    if isinstance(cart, dict):
        key = f"{product_id}:{size}"
        if key in cart:
            cart.pop(key, None)
        else:
            # fallback to legacy key
            cart.pop(str(product_id), None)

        request.session['cart'] = cart
        request.session.modified = True

    return redirect(request.META.get('HTTP_REFERER', reverse('home')))


def cart_update(request):
    """Actualiza la cantidad de un item a un valor específico (POST)."""
    if request.method != 'POST':
        return redirect(request.META.get('HTTP_REFERER', reverse('home')))

    product_id = request.POST.get('product_id')
    quantity = request.POST.get('quantity')
    size = (request.POST.get('size') or '').strip()
    if not product_id:
        return redirect(request.META.get('HTTP_REFERER', reverse('home')))

    try:
        q = int(quantity)
    except Exception:
        q = 0

    cart = request.session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}

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
    return redirect(request.META.get('HTTP_REFERER', reverse('home')))


def novedades(request):
    """Muestra productos ordenados por fecha de creación (más recientes primero)."""
    # show only products created within the last 30 days
    cutoff = timezone.now() - datetime.timedelta(days=30)
    productos = Producto.objects.filter(esta_disponible=True, fecha_creacion__gte=cutoff).order_by('-fecha_creacion')[:24]
    contexto = {'productos': productos, 'title': 'Novedades'}
    return render(request, 'products.html', contexto)


def productos(request):
    """Muestra productos destacados."""
    destacados = Producto.objects.filter(esta_disponible=True, es_destacado=True).order_by('-fecha_creacion')
    productos = Producto.objects.filter(esta_disponible=True).exclude(es_destacado=True).order_by('-fecha_creacion')
    contexto = {'destacados': destacados, 'productos': productos, 'title': 'Productos'}
    return render(request, 'products.html', contexto)


def ofertas(request):
    """Muestra productos que tienen precio de oferta definido."""
    productos = Producto.objects.filter(esta_disponible=True, precio_oferta__isnull=False).order_by('-fecha_creacion')
    contexto = {'productos': productos, 'title': 'Ofertas'}
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
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        email = request.POST.get("email")  
        mensaje = request.POST.get("mensaje")
        messages.success(request, "¡Gracias! Tu mensaje se ha enviado correctamente. Te responderemos pronto.")
        return redirect('contacto')
    return render(request, "contacto.html")

def categorias(request):
    # Mostrar las categorías reales definidas en el modelo `Categoria`.
    categorias = Categoria.objects.all().order_by('nombre')
    return render(request, "categorias.html", {"categorias": categorias})


def categoria_detail(request, categoria_id):
    """Muestra los productos que pertenecen a la categoría indicada."""
    categoria = get_object_or_404(Categoria, pk=categoria_id)
    productos = Producto.objects.filter(categoria=categoria, esta_disponible=True).order_by('-fecha_creacion')
    contexto = {'productos': productos, 'title': categoria.nombre}
    return render(request, 'products.html', contexto)