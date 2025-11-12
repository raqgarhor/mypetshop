from django.contrib import admin
from django.utils.html import format_html
from .models import Articulo, Escaparate, Producto


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
	list_display = ('nombre', 'precio', 'precio_oferta', 'stock', 'esta_disponible', 'es_destacado', 'imagen_preview')
	readonly_fields = ()
	list_filter = ('esta_disponible', 'es_destacado')
	search_fields = ('nombre', 'descripcion', 'color', 'material', 'genero')

	def imagen_preview(self, obj):
		if obj.imagen:
			return format_html('<img src="{}" style="max-height:50px;"/>', obj.imagen.url)
		return '-'

	imagen_preview.short_description = 'Imagen'


admin.site.register(Articulo)
admin.site.register(Escaparate)
