from django.urls import path
from . import admin_views

app_name = 'admin_panel'

urlpatterns = [
    path('', admin_views.admin_dashboard, name='dashboard'),
    path('pedidos/', admin_views.admin_pedidos, name='pedidos'),
    path('pedidos/<int:pedido_id>/', admin_views.admin_pedido_detalle, name='pedido_detalle'),
    path('productos/', admin_views.admin_productos, name='productos'),
    path('productos/crear/', admin_views.admin_producto_crear, name='producto_crear'),
    path('productos/editar/<int:producto_id>/', admin_views.admin_producto_editar, name='producto_editar'),
    path('productos/eliminar/<int:producto_id>/', admin_views.admin_producto_eliminar, name='producto_eliminar'),
    path('clientes/', admin_views.admin_clientes, name='clientes'),
    path('clientes/crear/', admin_views.admin_cliente_crear, name='cliente_crear'),
    path('clientes/editar/<int:cliente_id>/', admin_views.admin_cliente_editar, name='cliente_editar'),
    path('clientes/eliminar/<int:cliente_id>/', admin_views.admin_cliente_eliminar, name='cliente_eliminar'),
    path('mensajes/', admin_views.admin_mensajes, name='mensajes'),
]

