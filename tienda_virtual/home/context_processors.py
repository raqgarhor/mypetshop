from .models import Producto


def cart_count(request):
    """Expose cart summary to templates: count, items and total amount.

    Returns a dict with keys: `cart_count` (total quantity),
    `cart_items` (list of {'producto','cantidad','subtotal','size'}) and
    `cart_total` (sum of subtotals).
    """
    cart = request.session.get('cart', {})
    items = []
    total_amount = 0
    count = 0

    if isinstance(cart, dict):
        for composite_key, qty in cart.items():
            try:
                if isinstance(composite_key, str) and ':' in composite_key:
                    pid_str, size = composite_key.split(':', 1)
                else:
                    pid_str = str(composite_key)
                    size = ''

                producto = Producto.objects.filter(pk=int(pid_str)).first()
                if not producto:
                    continue

                cantidad = int(qty)
                subtotal = producto.precio * cantidad
                items.append({'producto': producto, 'cantidad': cantidad, 'subtotal': subtotal, 'size': size})
                total_amount += subtotal
                count += cantidad
            except Exception:
                # ignore malformed entries and keep the processor safe
                continue

    return {'cart_count': count, 'cart_items': items, 'cart_total': total_amount}
