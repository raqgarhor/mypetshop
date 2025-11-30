from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse


def admin_required(view_func):
    """
    Decorador que verifica que el usuario esté autenticado y tenga es_admin=True
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Debes iniciar sesión para acceder a esta página.')
            return redirect(f"{reverse('login')}?next={request.path}")

        # Verificar si el usuario tiene un cliente asociado y si es administrador
        try:
            cliente = request.user.cliente
            if not cliente or not cliente.es_admin:
                messages.error(request, 'No tienes permisos para acceder a esta sección.')
                return redirect('home')
        except (AttributeError, Exception):
            # El usuario no tiene un cliente asociado o ocurrió algún error
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('home')

        return view_func(request, *args, **kwargs)
    return _wrapped_view

