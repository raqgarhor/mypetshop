"""
URL configuration for tienda_virtual project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from home import views as home_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),  # Admin de Django (separado)
    path('panel-admin/', include('home.admin_urls')),  # Panel de administrador personalizado
    path('cart/add/<int:product_id>/', home_views.add_to_cart, name='add_to_cart'),
    path('cart/decrement/<int:product_id>/', home_views.cart_decrement, name='cart_decrement'),
    path('cart/remove/<int:product_id>/', home_views.cart_remove, name='cart_remove'),
    path('cart/update/', home_views.cart_update, name='cart_update'),
    path('cart/clear/', home_views.cart_clear, name='cart_clear'),
    path('cart/status/', home_views.cart_status, name='cart_status'),
    path('cart/', home_views.cart_view, name='cart'),
    path('novedades/', home_views.novedades, name='novedades'),
    path('productos/', home_views.productos, name='productos'),
    path('producto/<int:product_id>/', home_views.product_detail, name='product_detail'),
    path('ofertas/', home_views.ofertas, name='ofertas'),
    path('categoria/<int:categoria_id>/', home_views.categoria_detail, name='categoria_detail'),
    path('acerca-de/', home_views.acerca_de, name='acerca_de'),
    path('contacto/', home_views.contacto, name='contacto'),
    path('categorias/', home_views.categorias, name='categorias'),
    path("checkout/datos/", home_views.checkout_datos_cliente_envio, name="checkout_datos"),
    path("checkout/pago/", home_views.detalles_pago, name="detalles_pago"),
    path("checkout/stripe/", home_views.checkout_stripe, name="checkout_stripe"),
    path("checkout/contrareembolso/", home_views.checkout_contrareembolso, name="checkout_contrareembolso"),
    path("pago/ok/<int:pedido_id>/", home_views.pago_ok, name="pago_ok"),
    path("pago/cancelado/<int:pedido_id>/", home_views.pago_cancelado, name="pago_cancelado"),    
    path("cuenta/registro/", home_views.register, name="register"),
    path("cuenta/login/", home_views.login_view, name="login"),
    path("cuenta/logout/", home_views.logout_view, name="logout"),
    path("seguimiento/", home_views.seguimiento_pedido, name="tracking"),
    path('', home_views.index, name='home'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
