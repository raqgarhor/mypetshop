from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from django.db import models
from django.forms import NumberInput

from .models import (
    Articulo,
    Cliente,
    Escaparate,
    ItemPedido,
    Pedido,
    Producto,
    ImagenProducto,
    Marca,
    Categoria,
    TallaProducto,
    Carrito, 
    ItemCarrito,
    MensajeContacto,
)

#Inlines
class ImagenProductoInline(admin.TabularInline):
    model = ImagenProducto
    extra = 1
    fields = ("imagen", "es_principal", "imagen_preview")
    readonly_fields = ("imagen_preview",)

    def imagen_preview(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" style="max-height:50px;"/>', obj.imagen.url)
        return "-"

class TallaProductoInline(admin.TabularInline):
    model = TallaProducto
    extra = 1
    fields = ("talla", "stock")




@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "precio",
        "precio_oferta",
        "stock",
        "esta_disponible",
        "es_destacado",
        "marca",
        "categoria",
    )
    readonly_fields = ()
    list_filter = ("esta_disponible", "es_destacado", "marca", "categoria")
    search_fields = ("nombre", "descripcion", "color", "material", "genero")
    inlines = [ImagenProductoInline, TallaProductoInline]

   
    formfield_overrides = {
        models.DecimalField: {'widget': NumberInput(attrs={'min': '0', 'step': '0.01'})},
        models.IntegerField: {'widget': NumberInput(attrs={'min': '0', 'step': '1'})},
    }

    def imagen_preview(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" style="max-height:50px;"/>', obj.imagen.url)
        return "-"

@admin.register(TallaProducto)
class TallaProductoAdmin(admin.ModelAdmin):
    list_display = ("producto", "talla", "stock")
    list_filter = ("talla",)
    search_fields = ("producto__nombre",)

@admin.register(ImagenProducto)
class ImagenProductoAdmin(admin.ModelAdmin):
    list_display = ("producto", "es_principal", "imagen_preview")
    list_filter = ("es_principal",)
    search_fields = ("producto__nombre",)

    def imagen_preview(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" style="max-height:50px;"/>', obj.imagen.url)
        return "-"

    imagen_preview.short_description = "Imagen"

@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "imagen_preview")
    search_fields = ("nombre",)

    def imagen_preview(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" style="max-height:50px;"/>', obj.imagen.url)
        return "-"

    imagen_preview.short_description = "Imagen"

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "imagen_preview")
    search_fields = ("nombre",)

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
    list_display = ("nombre", "apellidos", "email", "telefono", "user", "fecha_creacion")
    search_fields = ("nombre", "apellidos", "email", "user__username")
    readonly_fields = ("fecha_creacion",)


class ItemCarritoInline(admin.TabularInline):
    model = ItemCarrito
    extra = 0
    fields = ("producto", "talla", "cantidad")
    readonly_fields = ()


@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "fecha_creacion", "fecha_actualizacion", "total_items")
    search_fields = ("cliente__nombre", "cliente__email")
    list_filter = ("fecha_creacion",)
    readonly_fields = ("fecha_creacion", "fecha_actualizacion")
    inlines = [ItemCarritoInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Anotar la suma de cantidades para mostrar en la lista
        from django.db.models import Sum

        return qs.annotate(_total_items=Sum("items__cantidad"))

    def total_items(self, obj):
        total = getattr(obj, "_total_items", None)
        if total is not None:
            return total or 0
        return obj.items.aggregate(total=Sum("cantidad"))["total"] or 0
    total_items.short_description = "Items"


@admin.register(ItemCarrito)
class ItemCarritoAdmin(admin.ModelAdmin):
    list_display = ("carrito", "producto", "talla", "cantidad")
    search_fields = ("producto__nombre", "carrito__cliente__nombre")

@admin.register(MensajeContacto)
class MensajeContactoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "email", "fecha")
    search_fields = ("nombre", "email", "mensaje")


admin.site.register(Articulo)
admin.site.register(Escaparate)
