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
from django.urls import path
from home import views as home_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('cart/add/<int:product_id>/', home_views.add_to_cart, name='add_to_cart'),
    path('cart/decrement/<int:product_id>/', home_views.cart_decrement, name='cart_decrement'),
    path('cart/remove/<int:product_id>/', home_views.cart_remove, name='cart_remove'),
    path('cart/update/', home_views.cart_update, name='cart_update'),
    path('cart/', home_views.cart_view, name='cart'),
    path('novedades/', home_views.novedades, name='novedades'),
    path('productos/', home_views.productos, name='productos'),
    path('producto/<int:product_id>/', home_views.product_detail, name='product_detail'),
    path('ofertas/', home_views.ofertas, name='ofertas'),
    path('', home_views.index, name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
