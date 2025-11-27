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

    # maps for templates: total qty per product and per product:size
    qty_by_product = {}
    qty_by_item = {}
    # remaining stock per cart item key ("id:size")
    remaining_by_item = {}

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

                pid_key = str(int(pid_str))
                qty_by_product[pid_key] = qty_by_product.get(pid_key, 0) + cantidad
                key = f"{pid_key}:{size}"
                qty_by_item[key] = qty_by_item.get(key, 0) + cantidad
            except Exception:
                # ignore malformed entries and keep the processor safe
                continue

        # compute remaining per cart item using talla stock when applicable
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

                pid_key = str(int(pid_str))
                key = f"{pid_key}:{size}"
                if size:
                    talla = producto.tallas.filter(talla=size).first()
                    stock = talla.stock if talla else 0
                    taken = qty_by_item.get(key, 0)
                    remaining_by_item[key] = max(0, stock - taken)
                else:
                    if producto.tallas.exists():
                        taken = qty_by_product.get(pid_key, 0)
                        remaining_by_item[key] = max(0, producto.available_stock - taken)
                    else:
                        taken = qty_by_product.get(pid_key, 0)
                        remaining_by_item[key] = max(0, producto.stock - taken)
            except Exception:
                continue

    return {
        'cart_count': count,
        'cart_items': items,
        'cart_total': total_amount,
        'cart_qty_by_product': qty_by_product,
        'cart_qty_by_item': qty_by_item,
        'cart_remaining_by_item': remaining_by_item,
    }
