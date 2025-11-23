from decimal import Decimal
import random
import json
import os
from django.utils import timezone

from django.core.management.base import BaseCommand
from django.db import transaction

from home.models import Categoria, Marca, Producto, ImagenProducto, TallaProducto, Cliente, Pedido, ItemPedido, ItemCarrito, Carrito

class Command(BaseCommand):
    help = 'Seed the database with initial data for development'

    def add_arguments(self, parser):
        parser.add_argument('--flush', action='store_true', help='Delete existing seeded data before running')

    @transaction.atomic
    def handle(self, *args, **options):
        if options.get('flush'):
            self.stdout.write('Borrando productos, categorias, marcas, pedidos y clientes existentes...')
            ItemPedido.objects.all().delete()
            Pedido.objects.all().delete()
            Producto.objects.all().delete()
            Categoria.objects.all().delete()
            Marca.objects.all().delete()
            Cliente.objects.all().delete()
            ItemCarrito.objects.all().delete()
            Carrito.objects.all().delete()

        # =====================================
        # CATEGORÍAS
        # ====================================
        categorias = [
            {'nombre': 'Alimentación', 'descripcion': 'Productos pensados para que tu mascota coma rico y sano.', 'imagen': 'categorias/comida.png'},
            {'nombre': 'Medicina', 'descripcion': 'Todo lo básico para su salud.', 'imagen': 'categorias/medicina.jpg'},
            {'nombre': 'Moda', 'descripcion': 'Ropa para que tu compi peludo vaya siempre estiloso.', 'imagen': 'categorias/moda.webp'},
            {'nombre': 'Juguetes', 'descripcion': 'Juguetes para todo tipo de mascotas', 'imagen': 'categorias/jueguetes.jpg'},
            {'nombre': 'Cuidado e Higiene', 'descripcion': 'Todo lo necesario para mantener a tu mascota limpia y sana', 'imagen': 'categorias/higiene.webp'},
            {'nombre': 'Accesorios', 'descripcion': 'Correas, arneses, collares, bebederos portátiles, bolsas, transportines...', 'imagen': 'categorias/accesorios.webp'},
            {'nombre': 'Viviendas', 'descripcion': 'Camas, casetas, terrarios, jaulas, acuarios y espacios diseñados para que cada animal tenga un hogar cómodo, seguro y adaptado a su especie.', 'imagen': 'categorias/viviendas.avif'},
            {'nombre': 'Hogar', 'descripcion': 'Productos pensados para tu casa', 'imagen': 'categorias/hogar.jpg'},
        ]
        for cat in categorias:
            obj, created = Categoria.objects.get_or_create(
                nombre=cat['nombre'],
                defaults={'descripcion': cat['descripcion'], 'imagen': cat['imagen']},
            )
            if created:
                self.stdout.write(f'Categoria creada: {obj.nombre}')

        # =====================================
        # MARCAS
        # ====================================
        marcas = [
            {'nombre': 'Marca 1', 'imagen': 'marcas/imagenes/logo-placeholder-1.png'},
            {'nombre': 'Marca 2', 'imagen': 'marcas/imagenes/logo-placeholder-2.png'},
            {'nombre': 'Marca 3', 'imagen': 'marcas/imagenes/logo-placeholder-3.png'},
            {'nombre': 'Marca 4', 'imagen': 'marcas/imagenes/logo-placeholder-4.png'},
            {'nombre': 'Marca 5', 'imagen': 'marcas/imagenes/logo-placeholder-5.png'},
        ]
        for m in marcas:
            obj, created = Marca.objects.get_or_create(
                nombre=m['nombre'],
                defaults={'imagen': m['imagen']},
            )
            if created:
                self.stdout.write(f'Marca creada: {obj.nombre}')

        # =====================================
        # PRODUCTOS
        # ====================================
        management_dir = os.path.dirname(os.path.dirname(__file__))
        fixture_path = os.path.join(management_dir, 'fixtures', 'productos.json')
        if not os.path.exists(fixture_path):
            self.stdout.write(self.style.ERROR(f'Fixture no encontrada: {fixture_path}'))
            return

        with open(fixture_path, 'r', encoding='utf-8') as f:
            productos_data = json.load(f)

        created_count = 0
        for item in productos_data:
            # Marca (case-insensitive), si no existe crear con placeholder
            marca_nombre = item.get('marca') or 'Marca desconocida'
            marca_obj = None
            marca_qs = Marca.objects.filter(nombre__iexact=marca_nombre)
            if marca_qs.exists():
                marca_obj = marca_qs.first()
            else:
                marca_obj = Marca.objects.create(nombre=marca_nombre, imagen='marcas/imagenes/logo-placeholder.png')

            # Categoria: intentar coincidencias razonables (iexact, startswith, contains, singular/plural)
            categoria_nombre = item.get('categoria') or 'Sin categoría'
            categoria_obj = Categoria.objects.filter(nombre__iexact=categoria_nombre).first()
            if not categoria_obj:
                if categoria_nombre.endswith('s'):
                    categoria_obj = Categoria.objects.filter(nombre__iexact=categoria_nombre.rstrip('s')).first()
            if not categoria_obj:
                categoria_obj = Categoria.objects.filter(nombre__icontains=categoria_nombre).first()
            if not categoria_obj:
                # fallback: crear categoría con imagen por defecto
                categoria_obj, _ = Categoria.objects.get_or_create(
                    nombre=categoria_nombre,
                    defaults={'descripcion': '', 'imagen': 'categorias/viviendas.avif'},
                )

            # Convertir precio y precio_oferta a Decimal
            try:
                precio = Decimal(str(item.get('precio') or '0').replace(',', '.'))
            except Exception:
                precio = Decimal('0.00')

            precio_oferta = None
            if item.get('precio_oferta') not in (None, '', 'null'):
                try:
                    precio_oferta = Decimal(str(item.get('precio_oferta')).replace(',', '.'))
                except Exception:
                    precio_oferta = None

            # Validar género
            genero = item.get('genero', Producto.Especie.PERRO)
            allowed = [c[0] for c in Producto.Especie.choices]
            if genero not in allowed:
                genero = Producto.Especie.PERRO

            producto = Producto.objects.create(
                nombre=item.get('nombre', 'Producto sin nombre'),
                descripcion=item.get('descripcion', ''),
                precio=precio,
                precio_oferta=precio_oferta,
                marca=marca_obj,
                categoria=categoria_obj,
                genero=genero,
                color=item.get('color', ''),
                material=item.get('material', ''),
                stock=item.get('stock', 0) or 0,
                esta_disponible=item.get('esta_disponible', True),
                es_destacado=item.get('es_destacado', False),
                fecha_creacion=timezone.now(),
                fecha_actualizacion=timezone.now(),
            )
            created_count += 1

            # Tallaje: si el item trae una lista de tallas las añadimos
            tallas = item.get('tallas')
            if isinstance(tallas, (list, tuple)) and tallas:
                for t in tallas:
                    try:
                        TallaProducto.objects.create(producto=producto, talla=str(t), stock=int(item.get('stock', 0) or 0))
                    except Exception:
                        continue

            # Imágenes: si el item trae lista de rutas las añadimos (marca la primera como principal)
            imagenes = item.get('imagenes')
            if isinstance(imagenes, (list, tuple)) and imagenes:
                for idx, img in enumerate(imagenes):
                    try:
                        ImagenProducto.objects.create(producto=producto, imagen=img, es_principal=(idx == 0))
                    except Exception:
                        continue

        self.stdout.write(self.style.SUCCESS(f'¡Productos cargados correctamente! Total: {created_count}'))

        # ===========================================
        # IMAGENES PRODUCTO (MAPEO MANUAL)
        # ===========================================

        management_dir = os.path.dirname(os.path.dirname(__file__))
        fixture_path = os.path.join(management_dir, 'fixtures', 'imagenes.json')
        if not os.path.exists(fixture_path):
            self.stdout.write(self.style.ERROR(f'Fixture no encontrada: {fixture_path}'))
            return

        with open(fixture_path, 'r', encoding='utf-8') as f:
            imagenes_data = json.load(f)

        for item in imagenes_data:
            nombre = item["producto"]

            try:
                producto = Producto.objects.get(nombre=nombre)
            except Producto.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Producto no encontrado para imágenes: {nombre}'))
                continue
            
            ImagenProducto.objects.create(
                producto=producto,
                imagen=item["imagen"],
                es_principal=item.get("es_principal")
            )

        self.stdout.write(self.style.SUCCESS("Imágenes insertadas correctamente"))

        #==========================================
        #TALLAS
        #==========================================

        management_dir = os.path.dirname(os.path.dirname(__file__))
        fixture_path = os.path.join(management_dir, 'fixtures', 'tallas.json')
        if not os.path.exists(fixture_path):
            self.stdout.write(self.style.ERROR(f'Fixture no encontrada: {fixture_path}'))
            return

        with open(fixture_path, 'r', encoding='utf-8') as f:
            tallas_data = json.load(f)

        for item in tallas_data:
            nombre = item["producto"]

            try:
                producto = Producto.objects.get(nombre=nombre)
            except Producto.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Producto no encontrado para imágenes: {nombre}'))
                continue
            
            TallaProducto.objects.create(
                producto=producto,
                talla=item["talla"],
                stock=item.get("stock", 0) or 0
            )

        self.stdout.write(self.style.SUCCESS("Tallas insertadas correctamente"))

    #==========================================
    #CLIENTES
    #==========================================
        management_dir = os.path.dirname(os.path.dirname(__file__))
        fixture_path = os.path.join(management_dir, 'fixtures', 'clientes.json')
        if not os.path.exists(fixture_path):
            self.stdout.write(self.style.ERROR(f'Fixture no encontrada: {fixture_path}'))
            return

        with open(fixture_path, 'r', encoding='utf-8') as f:
            clientes_data = json.load(f)

        for item in clientes_data:
            # Use email as unique lookup to avoid IntegrityError on repeated runs
            Cliente.objects.get_or_create(
                email=item["email"],
                defaults={
                    'nombre': item.get("nombre", ''),
                    'apellidos': item.get("apellidos", ''),
                    'telefono': item.get("telefono", ''),
                    'fecha_creacion': timezone.now(),
                    'direccion': item.get("direccion", ''),
                    'ciudad': item.get("ciudad", ''),
                    'codigo_postal': item.get("codigo_postal", ''),
                    'password': item.get("password", ''),
                }
            )

        self.stdout.write(self.style.SUCCESS("Clientes insertados correctamente"))
        

        #==========================================
        #PEDIDOS
        #==========================================
        management_dir = os.path.dirname(os.path.dirname(__file__))
        fixture_path = os.path.join(management_dir, 'fixtures', 'pedidos.json')
        if not os.path.exists(fixture_path):
            self.stdout.write(self.style.ERROR(f'Fixture no encontrada: {fixture_path}'))
            return

        with open(fixture_path, 'r', encoding='utf-8') as f:
            pedidos_data = json.load(f)

        for item in pedidos_data:
            try:
                cliente_obj = Cliente.objects.get(nombre=item["cliente"])
            except Cliente.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Cliente no encontrado para pedido: {item.get("cliente")}'))
                continue

            pedido = Pedido.objects.create(
                cliente=cliente_obj,
                numero_pedido=item["numero_pedido"],
                estado=item["estado"],
                subtotal=Decimal(str(item.get('subtotal') or '0').replace(',', '.')),
                impuestos=Decimal(str(item.get('impuestos') or '0').replace(',', '.')),
                coste_entrega=Decimal(str(item.get('coste_entrega') or '0').replace(',', '.')),
                descuento=Decimal(str(item.get('descuento') or '0').replace(',', '.')),
                metodo_pago=item.get("metodo_pago", ''),
                direccion_envio=item.get("direccion_envio", ''),
                telefono=item.get("telefono", '')
            )
            pedido.save()
        self.stdout.write(self.style.SUCCESS("Pedidos insertados correctamente"))

        #==========================================
        #ITEMS PEDIDO
        #==========================================
        
        management_dir = os.path.dirname(os.path.dirname(__file__))
        fixture_path = os.path.join(management_dir, 'fixtures', 'itemPedido.json')
        if not os.path.exists(fixture_path):
            self.stdout.write(self.style.ERROR(f'Fixture no encontrada: {fixture_path}'))
            return

        with open(fixture_path, 'r', encoding='utf-8') as f:
            items_pedido_data = json.load(f)

        for item in items_pedido_data:
            try:
                pedido_obj = Pedido.objects.get(numero_pedido=item["pedido"])
            except Pedido.DoesNotExist or Producto.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Pedido no encontrado para item: {item.get("pedido")}'))
                continue
            
            try:
                producto_obj = Producto.objects.get(nombre=item["producto"])
            except Producto.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Producto no encontrado para item: {item.get("producto")}'))
                continue

            pedido = ItemPedido.objects.create(
                pedido=pedido_obj,
                producto=producto_obj,
                talla=item["talla"],
                cantidad=item["cantidad"]
            )

            pedido.save()

        self.stdout.write(self.style.SUCCESS("Items de pedido insertados correctamente"))

        #==========================================
        # CARRITOS
        #==========================================
        
        management_dir = os.path.dirname(os.path.dirname(__file__))
        fixture_path = os.path.join(management_dir, 'fixtures', 'carritos.json')
        if not os.path.exists(fixture_path):
            self.stdout.write(self.style.ERROR(f'Fixture no encontrada: {fixture_path}'))
            return

        with open(fixture_path, 'r', encoding='utf-8') as f:
            carritos_data = json.load(f)

        for item in carritos_data:
            try:
                cliente_obj = Cliente.objects.get(nombre=item["cliente"])
            except Cliente.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Cliente no encontrado para carrito: {item.get("cliente")}'))
                continue

            carrito = Carrito.objects.create(
                cliente=cliente_obj,
            )

            carrito.save()
        self.stdout.write(self.style.SUCCESS("Carritos insertados correctamente"))

        #==========================================
        # ITEM CARRITOS
        #==========================================
        
        management_dir = os.path.dirname(os.path.dirname(__file__))
        fixture_path = os.path.join(management_dir, 'fixtures', 'itemCarrito.json')
        if not os.path.exists(fixture_path):
            self.stdout.write(self.style.ERROR(f'Fixture no encontrada: {fixture_path}'))
            return

        with open(fixture_path, 'r', encoding='utf-8') as f:
            item_carritos_data = json.load(f)

        for item in item_carritos_data:
            try:
                cliente_obj = Cliente.objects.get(nombre=item["carrito"])
            except Cliente.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Cliente no encontrado: {item.get("cliente")}'))
                continue
            try:
                carrito_obj = Carrito.objects.get(cliente=cliente_obj)
            except Carrito.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Cliente no encontrado para carrito: {item.get("cliente")}'))
                continue
            try:
                producto_obj = Producto.objects.get(nombre=item["producto"])
            except Producto.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Producto no encontrado para item de carrito: {item.get("producto")}'))
                continue

            item = ItemCarrito.objects.create(
                carrito=carrito_obj,
                producto=producto_obj,
                talla=item["talla"],
                cantidad=item["cantidad"]
            )
            item.save()
            
        self.stdout.write(self.style.SUCCESS("Items de carrito insertados correctamente"))


        self.stdout.write('Para recrear los datos use: python manage.py seed --flush')



                
