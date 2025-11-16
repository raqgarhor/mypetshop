def cart_count(request):

    cart = request.session.get('cart', {})
    try:
        total = sum(int(v) for v in cart.values()) if isinstance(cart, dict) else 0
    except Exception:
        total = 0
    return {'cart_count': total}
