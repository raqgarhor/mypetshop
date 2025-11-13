from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Articulo,
    Cliente,
    Escaparate,
    ItemPedido,
    Pedido,
    Producto,
)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "precio",
        "precio_oferta",
        "stock",
        "esta_disponible",
        "es_destacado",
        "imagen_preview",
    )
    readonly_fields = ()
    list_filter = ("esta_disponible", "es_destacado")
    search_fields = ("nombre", "descripcion", "color", "material", "genero")

    def imagen_preview(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" style="max-height:50px;"/>', obj.imagen.url)
        return "-"

    imagen_preview.short_description = "Imagen"


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        "numero_pedido",
        "cliente",
        "fecha_creacion",
        "estado",
        "total",
    )
    list_filter = ("estado", "fecha_creacion")
    search_fields = ("numero_pedido", "cliente__nombre", "cliente__email")
    readonly_fields = ("subtotal", "total", "fecha_creacion")


@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = (
        "pedido",
        "producto",
        "talla",
        "cantidad",
        "precio_unitario",
        "total",
    )
    list_filter = ("pedido__estado",)
    search_fields = ("pedido__numero_pedido", "producto__nombre")


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "apellidos", "email", "telefono", "fecha_creacion")
    search_fields = ("nombre", "apellidos", "email")


admin.site.register(Articulo)
admin.site.register(Escaparate)
