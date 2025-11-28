from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Return dictionary.get(str(key)) safely from templates."""
    try:
        if dictionary is None:
            return None
        # ensure key is string for consistent lookup
        return dictionary.get(str(key))
    except Exception:
        return None


@register.filter
def sub(value, arg):
    """Subtract arg from value. Returns numeric result when possible."""
    try:
        if value is None:
            v = 0
        else:
            v = float(value)
        if arg is None:
            a = 0
        else:
            a = float(arg)
        # return int when both were integers
        if v.is_integer() and a.is_integer():
            return int(v - a)
        return v - a
    except Exception:
        try:
            return int(value) - int(arg)
        except Exception:
            return None


@register.filter
def total_stock_tallas(tallas_queryset):
    """Suma el stock de todas las tallas de un producto."""
    try:
        total = sum(t.stock for t in tallas_queryset.all())
        return total
    except Exception:
        return 0