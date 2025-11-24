import datetime
from decimal import Decimal

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import ClienteEnvioForm, EmailAuthenticationForm, RegistroForm
from .models import (
    Articulo,
    Carrito,
    Cliente,
    Escaparate,
    ItemCarrito,
    ItemPedido,
    Pedido,
    Producto,
)


stripe.api_key = settings.STRIPE_SECRET_KEY


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

    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            login(request, cliente.user)
            messages.success(request, "Tu cuenta se creó correctamente.")
            return redirect('checkout_datos')
    else:
        form = RegistroForm()

    return render(request, 'register.html', {'form': form})


@login_required(login_url='login')
def checkout_datos_cliente_envio(request):
    cart = request.session.get("cart", {})
    if not cart:
        messages.error(request, "Tu carrito está vacío.")
        return redirect("cart")

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
    if request.method == "POST" and form.is_valid():
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
        },
    )

from decimal import Decimal
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404



@login_required(login_url='login')
def detalles_pago(request):
    cliente = getattr(request.user, "cliente", None)
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

    impuestos = Decimal("0.00")
    coste_entrega = Decimal("0.00")
    descuento = Decimal("0.00")
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
        },
    )



from django.utils.crypto import get_random_string
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

def generar_numero_pedido():
    return f"MP-{timezone.now().strftime('%Y%m%d%H%M%S')}-{get_random_string(4).upper()}"


@login_required(login_url='login')
def checkout_stripe(request):
    if request.method != "POST":
        return redirect("detalles_pago")

    cart = request.session.get("cart", {})
    if not cart:
        messages.error(request, "Tu carrito está vacío.")
        return redirect("cart")

    cliente = getattr(request.user, "cliente", None)
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

    # Sesión de Stripe
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=line_items,
        success_url=request.build_absolute_uri(
            reverse("pago_ok", args=[pedido.id_pedido])
        ),
        cancel_url=request.build_absolute_uri(
            reverse("pago_cancelado", args=[pedido.id_pedido])
        ),
    )

    return redirect(session.url, code=303)


def pago_ok(request, pedido_id):
    pedido = get_object_or_404(Pedido, id_pedido=pedido_id)
    pedido.estado = Pedido.Estados.PAGADO
    pedido.save()

    # vaciar carrito
    request.session["cart"] = {}
    request.session.modified = True

    return render(request, "pago_ok.html", {"pedido": pedido})


def pago_cancelado(request, pedido_id):
    pedido = get_object_or_404(Pedido, id_pedido=pedido_id)
    pedido.estado = Pedido.Estados.CANCELADO
    pedido.save()

    return render(request, "pago_cancelado.html", {"pedido": pedido})
