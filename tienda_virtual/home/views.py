from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.urls import reverse

from .models import Articulo, Escaparate
from .models import Producto


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

    producto = get_object_or_404(Producto, pk=product_id, esta_disponible=True)
    cart = request.session.get('cart', {})

    if not isinstance(cart, dict):
        cart = {}
    key = str(product_id)
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
        for pid, qty in cart.items():
            try:
                producto = Producto.objects.get(pk=int(pid))
            except Producto.DoesNotExist:
                continue
            cantidad = int(qty)
            subtotal = producto.precio * cantidad
            items.append({'producto': producto, 'cantidad': cantidad, 'subtotal': subtotal})
            total += subtotal

    contexto = {'items': items, 'total': total}
    return render(request, 'cart.html', contexto)


def cart_decrement(request, product_id):
    """Decrementa la cantidad de `product_id` en el carrito de sesión."""
    if request.method != 'POST':
        return redirect(request.META.get('HTTP_REFERER', reverse('cart')))

    cart = request.session.get('cart', {})
    if isinstance(cart, dict):
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

    return redirect(reverse('cart'))


def cart_remove(request, product_id):
    """Elimina completamente `product_id` del carrito de sesión."""
    if request.method != 'POST':
        return redirect(request.META.get('HTTP_REFERER', reverse('cart')))

    cart = request.session.get('cart', {})
    if isinstance(cart, dict):
        cart.pop(str(product_id), None)
        request.session['cart'] = cart
        request.session.modified = True

    return redirect(reverse('cart'))


def cart_update(request):
    """Actualiza la cantidad de un item a un valor específico (POST)."""
    if request.method != 'POST':
        return redirect(reverse('cart'))

    product_id = request.POST.get('product_id')
    quantity = request.POST.get('quantity')
    if not product_id:
        return redirect(reverse('cart'))

    try:
        q = int(quantity)
    except Exception:
        q = 0

    cart = request.session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}

    key = str(product_id)
    if q > 0:
        cart[key] = q
    else:
        cart.pop(key, None)

    request.session['cart'] = cart
    request.session.modified = True
    return redirect(reverse('cart'))