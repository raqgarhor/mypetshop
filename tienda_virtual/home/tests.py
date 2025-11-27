from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import timedelta

from .models import (
    Articulo,
    Escaparate,
    Producto,
    TallaProducto,
    ImagenProducto,
    Marca,
    Categoria,
    Cliente,
    Pedido,
    ItemPedido,
    Carrito,
    ItemCarrito,
    MensajeContacto,
)

User = get_user_model()


class ArticuloModelTest(TestCase):
    def test_crear_articulo(self):
        articulo = Articulo.objects.create(
            nombre="Juguete",
            descripcion="Juguete para perros"
        )
        self.assertEqual(articulo.nombre, "Juguete")
        self.assertEqual(articulo.descripcion, "Juguete para perros")
        self.assertEqual(str(articulo), "Juguete")


class EscaparateModelTest(TestCase):
    def setUp(self):
        self.articulo = Articulo.objects.create(
            nombre="Juguete",
            descripcion="Juguete para perros"
        )

    def test_crear_escaparate(self):
        escaparate = Escaparate.objects.create(articulo=self.articulo)
        self.assertEqual(escaparate.articulo, self.articulo)
        self.assertEqual(str(escaparate), "Juguete")

    def test_escaparate_cascade_delete(self):
        escaparate = Escaparate.objects.create(articulo=self.articulo)
        articulo_id = self.articulo.id
        self.articulo.delete()
        self.assertFalse(Escaparate.objects.filter(id=escaparate.id).exists())


class MarcaModelTest(TestCase):
    def setUp(self):
        self.imagen = SimpleUploadedFile(
            name="test.jpg",
            content=b"fake image content",
            content_type="image/jpeg"
        )

    def test_crear_marca(self):
        marca = Marca.objects.create(
            nombre="Royal Canin",
            imagen=self.imagen
        )
        self.assertEqual(marca.nombre, "Royal Canin")
        self.assertEqual(str(marca), "Royal Canin")

    def test_marca_nombre_unico(self):
        Marca.objects.create(nombre="Royal Canin", imagen=self.imagen)
        imagen2 = SimpleUploadedFile(
            name="test2.jpg",
            content=b"fake image content",
            content_type="image/jpeg"
        )
        with self.assertRaises(Exception):
            Marca.objects.create(nombre="Royal Canin", imagen=imagen2)


class CategoriaModelTest(TestCase):
    def setUp(self):
        self.imagen = SimpleUploadedFile(
            name="test.jpg",
            content=b"fake image content",
            content_type="image/jpeg"
        )

    def test_crear_categoria(self):
        categoria = Categoria.objects.create(
            nombre="Alimentación",
            descripcion="Productos de alimentación",
            imagen=self.imagen
        )
        self.assertEqual(categoria.nombre, "Alimentación")
        self.assertEqual(categoria.descripcion, "Productos de alimentación")
        self.assertEqual(str(categoria), "Alimentación")

    def test_categoria_nombre_unico(self):
        Categoria.objects.create(
            nombre="Alimentación",
            imagen=self.imagen
        )
        imagen2 = SimpleUploadedFile(
            name="test2.jpg",
            content=b"fake image content",
            content_type="image/jpeg"
        )
        with self.assertRaises(Exception):
            Categoria.objects.create(
                nombre="Alimentación",
                imagen=imagen2
            )


class ProductoModelTest(TestCase):
    def setUp(self):
        imagen_marca = SimpleUploadedFile(
            name="marca.jpg",
            content=b"fake image content",
            content_type="image/jpeg"
        )
        imagen_categoria = SimpleUploadedFile(
            name="categoria.jpg",
            content=b"fake image content",
            content_type="image/jpeg"
        )
        self.marca = Marca.objects.create(
            nombre="Royal Canin",
            imagen=imagen_marca
        )
        self.categoria = Categoria.objects.create(
            nombre="Alimentación",
            imagen=imagen_categoria
        )

    def test_crear_producto(self):
        producto = Producto.objects.create(
            nombre="Pienso Premium",
            descripcion="Pienso de alta calidad",
            precio=Decimal("29.99"),
            marca=self.marca,
            categoria=self.categoria,
            genero=Producto.Especie.PERRO,
            stock=100
        )
        self.assertEqual(producto.nombre, "Pienso Premium")
        self.assertEqual(producto.precio, Decimal("29.99"))
        self.assertEqual(producto.marca, self.marca)
        self.assertEqual(producto.categoria, self.categoria)
        self.assertEqual(producto.genero, Producto.Especie.PERRO)
        self.assertEqual(producto.stock, 100)
        self.assertTrue(producto.esta_disponible)
        self.assertFalse(producto.es_destacado)
        self.assertEqual(str(producto), "Pienso Premium")

    def test_producto_defaults(self):
        producto = Producto.objects.create(
            nombre="Producto Test",
            marca=self.marca
        )
        self.assertEqual(producto.precio, Decimal("0.00"))
        self.assertIsNone(producto.precio_oferta)
        self.assertEqual(producto.genero, Producto.Especie.PERRO)
        self.assertEqual(producto.stock, 0)
        self.assertTrue(producto.esta_disponible)
        self.assertFalse(producto.es_destacado)

    def test_producto_fecha_actualizacion_auto(self):
        producto = Producto.objects.create(
            nombre="Producto Test",
            marca=self.marca
        )
        fecha_creacion = producto.fecha_creacion
        fecha_actualizacion_inicial = producto.fecha_actualizacion
        
        # Esperar un poco para asegurar diferencia de tiempo
        import time
        time.sleep(0.01)
        
        producto.nombre = "Producto Actualizado"
        producto.save()
        
        producto.refresh_from_db()
        self.assertEqual(producto.fecha_creacion, fecha_creacion)
        self.assertGreater(producto.fecha_actualizacion, fecha_actualizacion_inicial)

    def test_producto_clean_precio_negativo(self):
        producto = Producto(
            nombre="Producto Test",
            precio=Decimal("-10.00"),
            marca=self.marca
        )
        with self.assertRaises(ValidationError):
            producto.full_clean()

    def test_producto_clean_precio_oferta_negativo(self):
        producto = Producto(
            nombre="Producto Test",
            precio=Decimal("10.00"),
            precio_oferta=Decimal("-5.00"),
            marca=self.marca
        )
        with self.assertRaises(ValidationError):
            producto.full_clean()

    def test_producto_clean_precio_oferta_mayor_igual_precio(self):
        producto = Producto(
            nombre="Producto Test",
            precio=Decimal("10.00"),
            precio_oferta=Decimal("10.00"),
            marca=self.marca
        )
        with self.assertRaises(ValidationError):
            producto.full_clean()

        producto.precio_oferta = Decimal("15.00")
        with self.assertRaises(ValidationError):
            producto.full_clean()

    def test_producto_clean_precio_oferta_valido(self):
        producto = Producto(
            nombre="Producto Test",
            precio=Decimal("10.00"),
            precio_oferta=Decimal("7.50"),
            marca=self.marca
        )
        producto.full_clean()  # No debe lanzar excepción
        producto.save()
        self.assertEqual(producto.precio_oferta, Decimal("7.50"))

    def test_producto_clean_stock_negativo(self):
        producto = Producto(
            nombre="Producto Test",
            precio=Decimal("10.00"),
            stock=-1,
            marca=self.marca
        )
        with self.assertRaises(ValidationError):
            producto.full_clean()

    def test_producto_especies_choices(self):
        producto = Producto.objects.create(
            nombre="Producto Perro",
            marca=self.marca,
            genero=Producto.Especie.PERRO
        )
        self.assertEqual(producto.genero, Producto.Especie.PERRO)

        producto.genero = Producto.Especie.GATO
        producto.save()
        self.assertEqual(producto.genero, Producto.Especie.GATO)

    def test_producto_sin_categoria(self):
        producto = Producto.objects.create(
            nombre="Producto Test",
            marca=self.marca,
            categoria=None
        )
        self.assertIsNone(producto.categoria)

    def test_producto_protect_marca(self):
        producto = Producto.objects.create(
            nombre="Producto Test",
            marca=self.marca
        )
        with self.assertRaises(Exception):
            self.marca.delete()

    def test_producto_protect_categoria(self):
        producto = Producto.objects.create(
            nombre="Producto Test",
            marca=self.marca,
            categoria=self.categoria
        )
        with self.assertRaises(Exception):
            self.categoria.delete()


class TallaProductoModelTest(TestCase):
    def setUp(self):
        imagen_marca = SimpleUploadedFile(
            name="marca.jpg",
            content=b"fake image content",
            content_type="image/jpeg"
        )
        self.marca = Marca.objects.create(
            nombre="Royal Canin",
            imagen=imagen_marca
        )
        self.producto = Producto.objects.create(
            nombre="Collar",
            precio=Decimal("15.00"),
            marca=self.marca
        )

    def test_crear_talla_producto(self):
        talla = TallaProducto.objects.create(
            producto=self.producto,
            talla="M",
            stock=50
        )
        self.assertEqual(talla.producto, self.producto)
        self.assertEqual(talla.talla, "M")
        self.assertEqual(talla.stock, 50)
        self.assertEqual(str(talla), "Collar - Talla: M")

    def test_talla_producto_cascade_delete(self):
        talla = TallaProducto.objects.create(
            producto=self.producto,
            talla="M",
            stock=50
        )
        self.producto.delete()
        self.assertFalse(TallaProducto.objects.filter(id=talla.id).exists())

    def test_talla_producto_sin_producto(self):
        talla = TallaProducto.objects.create(
            producto=None,
            talla="M",
            stock=50
        )
        self.assertIsNone(talla.producto)


class ImagenProductoModelTest(TestCase):
    def setUp(self):
        imagen_marca = SimpleUploadedFile(
            name="marca.jpg",
            content=b"fake image content",
            content_type="image/jpeg"
        )
        self.marca = Marca.objects.create(
            nombre="Royal Canin",
            imagen=imagen_marca
        )
        self.producto = Producto.objects.create(
            nombre="Producto Test",
            precio=Decimal("15.00"),
            marca=self.marca
        )
        self.imagen_file = SimpleUploadedFile(
            name="test.jpg",
            content=b"fake image content",
            content_type="image/jpeg"
        )

    def test_crear_imagen_producto(self):
        imagen = ImagenProducto.objects.create(
            producto=self.producto,
            imagen=self.imagen_file,
            es_principal=True
        )
        self.assertEqual(imagen.producto, self.producto)
        self.assertTrue(imagen.es_principal)
        self.assertEqual(str(imagen), "Imagen de Producto Test")

    def test_imagen_producto_cascade_delete(self):
        imagen = ImagenProducto.objects.create(
            producto=self.producto,
            imagen=self.imagen_file
        )
        self.producto.delete()
        self.assertFalse(ImagenProducto.objects.filter(id=imagen.id).exists())

    def test_imagen_producto_ordering(self):
        imagen_file1 = SimpleUploadedFile(
            name="test1.jpg",
            content=b"fake image content",
            content_type="image/jpeg"
        )
        imagen_file2 = SimpleUploadedFile(
            name="test2.jpg",
            content=b"fake image content",
            content_type="image/jpeg"
        )
        imagen1 = ImagenProducto.objects.create(
            producto=self.producto,
            imagen=imagen_file1,
            es_principal=False
        )
        imagen2 = ImagenProducto.objects.create(
            producto=self.producto,
            imagen=imagen_file2,
            es_principal=True
        )
        imagenes = list(ImagenProducto.objects.all())
        # La imagen principal debe aparecer primero
        self.assertEqual(imagenes[0], imagen2)


class ClienteModelTest(TestCase):
    def test_crear_cliente_sin_usuario(self):
        cliente = Cliente.objects.create(
            nombre="Juan",
            apellidos="Pérez",
            email="juan@example.com",
            telefono="123456789"
        )
        self.assertEqual(cliente.nombre, "Juan")
        self.assertEqual(cliente.apellidos, "Pérez")
        self.assertEqual(cliente.email, "juan@example.com")
        self.assertIsNone(cliente.user)

    def test_crear_cliente_con_usuario(self):
        user = User.objects.create_user(
            username="juan",
            email="juan@example.com",
            password="password123"
        )
        cliente = Cliente.objects.create(
            nombre="Juan",
            apellidos="Pérez",
            email="juan@example.com",
            user=user
        )
        self.assertEqual(cliente.user, user)
        self.assertEqual(user.cliente, cliente)

    def test_cliente_str_con_apellidos(self):
        cliente = Cliente.objects.create(
            nombre="Juan",
            apellidos="Pérez",
            email="juan@example.com"
        )
        self.assertEqual(str(cliente), "Juan Pérez")

    def test_cliente_str_sin_apellidos(self):
        cliente = Cliente.objects.create(
            nombre="Juan",
            email="juan@example.com"
        )
        self.assertEqual(str(cliente), "Juan")

    def test_cliente_str_solo_email(self):
        cliente = Cliente.objects.create(
            nombre="",
            email="juan@example.com"
        )
        self.assertEqual(str(cliente), "juan@example.com")

    def test_cliente_esta_logueado_sin_usuario(self):
        cliente = Cliente.objects.create(
            nombre="Juan",
            email="juan@example.com"
        )
        self.assertFalse(cliente.esta_logueado)

    def test_cliente_esta_logueado_con_usuario(self):
        user = User.objects.create_user(
            username="juan",
            email="juan@example.com",
            password="password123"
        )
        cliente = Cliente.objects.create(
            nombre="Juan",
            email="juan@example.com",
            user=user
        )
        # En Django, user.is_authenticated retorna True si el usuario tiene pk
        # La propiedad verifica user.is_authenticated, que será True para un usuario creado
        self.assertTrue(cliente.esta_logueado)

    def test_cliente_email_unico(self):
        Cliente.objects.create(
            nombre="Juan",
            email="juan@example.com"
        )
        with self.assertRaises(Exception):
            Cliente.objects.create(
                nombre="Pedro",
                email="juan@example.com"
            )


class PedidoModelTest(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nombre="Juan",
            email="juan@example.com"
        )
        imagen_marca = SimpleUploadedFile(
            name="marca.jpg",
            content=b"fake image content",
            content_type="image/jpeg"
        )
        self.marca = Marca.objects.create(
            nombre="Royal Canin",
            imagen=imagen_marca
        )
        self.producto = Producto.objects.create(
            nombre="Producto Test",
            precio=Decimal("10.00"),
            marca=self.marca
        )

    def test_crear_pedido(self):
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            numero_pedido="PED-001",
            estado=Pedido.Estados.PENDIENTE,
            subtotal=Decimal("10.00"),
            impuestos=Decimal("2.10"),
            coste_entrega=Decimal("5.00"),
            descuento=Decimal("0.00")
        )
        self.assertEqual(pedido.cliente, self.cliente)
        self.assertEqual(pedido.numero_pedido, "PED-001")
        self.assertEqual(pedido.estado, Pedido.Estados.PENDIENTE)
        self.assertEqual(pedido.subtotal, Decimal("10.00"))
        self.assertEqual(str(pedido), "Pedido #PED-001")

    def test_pedido_defaults(self):
        pedido = Pedido.objects.create(
            numero_pedido="PED-002"
        )
        self.assertIsNone(pedido.cliente)
        self.assertEqual(pedido.estado, Pedido.Estados.PENDIENTE)
        self.assertEqual(pedido.subtotal, Decimal("0.00"))
        self.assertEqual(pedido.impuestos, Decimal("0.00"))
        self.assertEqual(pedido.coste_entrega, Decimal("0.00"))
        self.assertEqual(pedido.descuento, Decimal("0.00"))

    def test_pedido_total_calculo_nuevo(self):
        pedido = Pedido.objects.create(
            numero_pedido="PED-003",
            subtotal=Decimal("100.00"),
            impuestos=Decimal("21.00"),
            coste_entrega=Decimal("5.00"),
            descuento=Decimal("10.00")
        )
        # Total = 100 + 21 + 5 - 10 = 116.00
        self.assertEqual(pedido.total, Decimal("116.00"))

    def test_pedido_recalcular_totales(self):
        pedido = Pedido.objects.create(
            numero_pedido="PED-004",
            subtotal=Decimal("0.00"),
            impuestos=Decimal("0.00"),
            coste_entrega=Decimal("0.00"),
            descuento=Decimal("0.00")
        )
        
        # Crear items del pedido
        ItemPedido.objects.create(
            pedido=pedido,
            producto=self.producto,
            cantidad=2,
            precio_unitario=Decimal("10.00")
        )
        
        # Recalcular debe actualizar subtotal y total
        pedido.recalcular_totales()
        pedido.save()
        pedido.refresh_from_db()
        
        self.assertEqual(pedido.subtotal, Decimal("20.00"))
        self.assertEqual(pedido.total, Decimal("20.00"))

    def test_pedido_recalcular_totales_con_impuestos(self):
        pedido = Pedido.objects.create(
            numero_pedido="PED-005",
            subtotal=Decimal("0.00"),
            impuestos=Decimal("4.20"),
            coste_entrega=Decimal("5.00"),
            descuento=Decimal("2.00")
        )
        
        ItemPedido.objects.create(
            pedido=pedido,
            producto=self.producto,
            cantidad=2,
            precio_unitario=Decimal("10.00")
        )
        
        pedido.recalcular_totales()
        pedido.save()
        pedido.refresh_from_db()
        
        # Subtotal: 20.00, Total: 20.00 + 4.20 + 5.00 - 2.00 = 27.20
        self.assertEqual(pedido.subtotal, Decimal("20.00"))
        self.assertEqual(pedido.total, Decimal("27.20"))

    def test_pedido_quantize_redondeo(self):
        pedido = Pedido.objects.create(
            numero_pedido="PED-006",
            subtotal=Decimal("10.005"),
            impuestos=Decimal("0.00"),
            coste_entrega=Decimal("0.00"),
            descuento=Decimal("0.00")
        )
        # Debe redondear a 2 decimales
        self.assertEqual(pedido.total, Decimal("10.01"))

    def test_pedido_estados(self):
        estados = [
            Pedido.Estados.PENDIENTE,
            Pedido.Estados.PAGADO,
            Pedido.Estados.EN_PROCESO,
            Pedido.Estados.ENVIADO,
            Pedido.Estados.ENTREGADO,
            Pedido.Estados.CANCELADO,
        ]
        for estado in estados:
            pedido = Pedido.objects.create(
                numero_pedido=f"PED-{estado}",
                estado=estado
            )
            self.assertEqual(pedido.estado, estado)

    def test_pedido_protect_cliente(self):
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            numero_pedido="PED-007"
        )
        with self.assertRaises(Exception):
            self.cliente.delete()


class ItemPedidoModelTest(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nombre="Juan",
            email="juan@example.com"
        )
        imagen_marca = SimpleUploadedFile(
            name="marca.jpg",
            content=b"fake image content",
            content_type="image/jpeg"
        )
        self.marca = Marca.objects.create(
            nombre="Royal Canin",
            imagen=imagen_marca
        )
        self.producto = Producto.objects.create(
            nombre="Producto Test",
            precio=Decimal("10.00"),
            marca=self.marca
        )
        self.pedido = Pedido.objects.create(
            cliente=self.cliente,
            numero_pedido="PED-001"
        )

    def test_crear_item_pedido(self):
        item = ItemPedido.objects.create(
            pedido=self.pedido,
            producto=self.producto,
            cantidad=3,
            talla="M"
        )
        self.assertEqual(item.pedido, self.pedido)
        self.assertEqual(item.producto, self.producto)
        self.assertEqual(item.cantidad, 3)
        self.assertEqual(item.talla, "M")
        self.assertEqual(str(item), "Producto Test x3")

    def test_item_pedido_precio_unitario_auto(self):
        item = ItemPedido.objects.create(
            pedido=self.pedido,
            producto=self.producto,
            cantidad=2
        )
        # Debe tomar el precio del producto automáticamente
        self.assertEqual(item.precio_unitario, Decimal("10.00"))

    def test_item_pedido_total_calculo(self):
        item = ItemPedido.objects.create(
            pedido=self.pedido,
            producto=self.producto,
            cantidad=3,
            precio_unitario=Decimal("10.00")
        )
        # Total = 3 * 10.00 = 30.00
        self.assertEqual(item.total, Decimal("30.00"))

    def test_item_pedido_recalcula_pedido_total(self):
        self.pedido.subtotal = Decimal("0.00")
        self.pedido.save()
        
        item = ItemPedido.objects.create(
            pedido=self.pedido,
            producto=self.producto,
            cantidad=2,
            precio_unitario=Decimal("10.00")
        )
        
        self.pedido.refresh_from_db()
        # El pedido debe tener subtotal actualizado
        self.assertEqual(self.pedido.subtotal, Decimal("20.00"))

    def test_item_pedido_cascade_delete(self):
        item = ItemPedido.objects.create(
            pedido=self.pedido,
            producto=self.producto,
            cantidad=1
        )
        item_id = item.id_item_pedido
        self.pedido.delete()
        self.assertFalse(ItemPedido.objects.filter(id_item_pedido=item_id).exists())

    def test_item_pedido_protect_producto(self):
        item = ItemPedido.objects.create(
            pedido=self.pedido,
            producto=self.producto,
            cantidad=1
        )
        with self.assertRaises(Exception):
            self.producto.delete()


class CarritoModelTest(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nombre="Juan",
            email="juan@example.com"
        )
        imagen_marca = SimpleUploadedFile(
            name="marca.jpg",
            content=b"fake image content",
            content_type="image/jpeg"
        )
        self.marca = Marca.objects.create(
            nombre="Royal Canin",
            imagen=imagen_marca
        )
        self.producto1 = Producto.objects.create(
            nombre="Producto 1",
            precio=Decimal("10.00"),
            marca=self.marca
        )
        self.producto2 = Producto.objects.create(
            nombre="Producto 2",
            precio=Decimal("20.00"),
            marca=self.marca
        )

    def test_crear_carrito(self):
        carrito = Carrito.objects.create(cliente=self.cliente)
        self.assertEqual(carrito.cliente, self.cliente)
        self.assertIsNotNone(carrito.fecha_creacion)
        self.assertIsNotNone(carrito.fecha_actualizacion)
        self.assertEqual(str(carrito), f"Carrito #{carrito.pk} - {self.cliente}")

    def test_crear_carrito_sin_cliente(self):
        carrito = Carrito.objects.create()
        self.assertIsNone(carrito.cliente)
        self.assertEqual(str(carrito), f"Carrito #{carrito.pk} - Anónimo")

    def test_carrito_fecha_actualizacion_auto(self):
        carrito = Carrito.objects.create(cliente=self.cliente)
        fecha_actualizacion_inicial = carrito.fecha_actualizacion
        
        import time
        time.sleep(0.01)
        
        carrito.save()
        carrito.refresh_from_db()
        self.assertGreater(carrito.fecha_actualizacion, fecha_actualizacion_inicial)

    def test_carrito_add_producto_nuevo(self):
        carrito = Carrito.objects.create(cliente=self.cliente)
        item, created = carrito.add_producto(self.producto1, cantidad=2)
        
        self.assertTrue(created)
        self.assertEqual(item.producto, self.producto1)
        self.assertEqual(item.cantidad, 2)
        self.assertEqual(carrito.items.count(), 1)

    def test_carrito_add_producto_existente(self):
        carrito = Carrito.objects.create(cliente=self.cliente)
        carrito.add_producto(self.producto1, cantidad=2)
        item, created = carrito.add_producto(self.producto1, cantidad=3)
        
        self.assertFalse(created)
        self.assertEqual(item.cantidad, 5)  # 2 + 3

    def test_carrito_add_producto_con_talla(self):
        carrito = Carrito.objects.create(cliente=self.cliente)
        item1, _ = carrito.add_producto(self.producto1, talla="M", cantidad=1)
        item2, _ = carrito.add_producto(self.producto1, talla="L", cantidad=1)
        
        # Deben ser items diferentes
        self.assertNotEqual(item1.id, item2.id)
        self.assertEqual(item1.talla, "M")
        self.assertEqual(item2.talla, "L")

    def test_carrito_add_producto_cantidad_invalida(self):
        carrito = Carrito.objects.create(cliente=self.cliente)
        with self.assertRaises(ValueError):
            carrito.add_producto(self.producto1, cantidad=0)
        
        with self.assertRaises(ValueError):
            carrito.add_producto(self.producto1, cantidad=-1)

    def test_carrito_remove_producto(self):
        carrito = Carrito.objects.create(cliente=self.cliente)
        carrito.add_producto(self.producto1, cantidad=2)
        self.assertEqual(carrito.items.count(), 1)
        
        carrito.remove_producto(self.producto1)
        self.assertEqual(carrito.items.count(), 0)

    def test_carrito_remove_producto_con_talla(self):
        carrito = Carrito.objects.create(cliente=self.cliente)
        carrito.add_producto(self.producto1, talla="M", cantidad=1)
        carrito.add_producto(self.producto1, talla="L", cantidad=1)
        self.assertEqual(carrito.items.count(), 2)
        
        carrito.remove_producto(self.producto1, talla="M")
        self.assertEqual(carrito.items.count(), 1)
        self.assertEqual(carrito.items.first().talla, "L")

    def test_carrito_set_cantidad(self):
        carrito = Carrito.objects.create(cliente=self.cliente)
        carrito.add_producto(self.producto1, cantidad=2)
        
        carrito.set_cantidad(self.producto1, "", 5)
        item = carrito.items.first()
        self.assertEqual(item.cantidad, 5)

    def test_carrito_set_cantidad_cero_elimina(self):
        carrito = Carrito.objects.create(cliente=self.cliente)
        carrito.add_producto(self.producto1, cantidad=2)
        self.assertEqual(carrito.items.count(), 1)
        
        carrito.set_cantidad(self.producto1, "", 0)
        self.assertEqual(carrito.items.count(), 0)

    def test_carrito_total_items(self):
        carrito = Carrito.objects.create(cliente=self.cliente)
        carrito.add_producto(self.producto1, cantidad=2)
        carrito.add_producto(self.producto2, cantidad=3)
        
        self.assertEqual(carrito.total_items(), 5)

    def test_carrito_total_items_vacio(self):
        carrito = Carrito.objects.create(cliente=self.cliente)
        self.assertEqual(carrito.total_items(), 0)

    def test_carrito_get_total(self):
        carrito = Carrito.objects.create(cliente=self.cliente)
        carrito.add_producto(self.producto1, cantidad=2)  # 2 * 10.00 = 20.00
        carrito.add_producto(self.producto2, cantidad=1)  # 1 * 20.00 = 20.00
        
        total = carrito.get_total()
        self.assertEqual(total, Decimal("40.00"))

    def test_carrito_get_total_con_oferta(self):
        self.producto1.precio_oferta = Decimal("8.00")
        self.producto1.save()
        
        carrito = Carrito.objects.create(cliente=self.cliente)
        carrito.add_producto(self.producto1, cantidad=2)  # 2 * 8.00 = 16.00
        
        total = carrito.get_total()
        self.assertEqual(total, Decimal("16.00"))

    def test_carrito_clear(self):
        carrito = Carrito.objects.create(cliente=self.cliente)
        carrito.add_producto(self.producto1, cantidad=2)
        carrito.add_producto(self.producto2, cantidad=3)
        self.assertEqual(carrito.items.count(), 2)
        
        carrito.clear()
        self.assertEqual(carrito.items.count(), 0)

    def test_carrito_cascade_delete(self):
        carrito = Carrito.objects.create(cliente=self.cliente)
        carrito.add_producto(self.producto1, cantidad=2)
        carrito_id = carrito.id
        
        self.cliente.delete()
        self.assertFalse(Carrito.objects.filter(id=carrito_id).exists())


class ItemCarritoModelTest(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nombre="Juan",
            email="juan@example.com"
        )
        imagen_marca = SimpleUploadedFile(
            name="marca.jpg",
            content=b"fake image content",
            content_type="image/jpeg"
        )
        self.marca = Marca.objects.create(
            nombre="Royal Canin",
            imagen=imagen_marca
        )
        self.producto = Producto.objects.create(
            nombre="Producto Test",
            precio=Decimal("10.00"),
            marca=self.marca
        )
        self.carrito = Carrito.objects.create(cliente=self.cliente)

    def test_crear_item_carrito(self):
        item = ItemCarrito.objects.create(
            carrito=self.carrito,
            producto=self.producto,
            cantidad=3,
            talla="M"
        )
        self.assertEqual(item.carrito, self.carrito)
        self.assertEqual(item.producto, self.producto)
        self.assertEqual(item.cantidad, 3)
        self.assertEqual(item.talla, "M")
        self.assertEqual(str(item), "Producto Test x3 (M)")

    def test_item_carrito_precio_unitario(self):
        item = ItemCarrito.objects.create(
            carrito=self.carrito,
            producto=self.producto,
            cantidad=2
        )
        self.assertEqual(item.precio_unitario, Decimal("10.00"))

    def test_item_carrito_precio_unitario_oferta(self):
        self.producto.precio_oferta = Decimal("8.00")
        self.producto.save()
        
        item = ItemCarrito.objects.create(
            carrito=self.carrito,
            producto=self.producto,
            cantidad=2
        )
        self.assertEqual(item.precio_unitario, Decimal("8.00"))

    def test_item_carrito_precio_unitario_sin_precio(self):
        self.producto.precio = Decimal("0.00")
        self.producto.save()
        
        item = ItemCarrito.objects.create(
            carrito=self.carrito,
            producto=self.producto,
            cantidad=2
        )
        self.assertEqual(item.precio_unitario, Decimal("0.00"))

    def test_item_carrito_subtotal(self):
        item = ItemCarrito.objects.create(
            carrito=self.carrito,
            producto=self.producto,
            cantidad=3
        )
        # Subtotal = 3 * 10.00 = 30.00
        self.assertEqual(item.subtotal, Decimal("30.00"))

    def test_item_carrito_subtotal_con_oferta(self):
        self.producto.precio_oferta = Decimal("8.00")
        self.producto.save()
        
        item = ItemCarrito.objects.create(
            carrito=self.carrito,
            producto=self.producto,
            cantidad=3
        )
        # Subtotal = 3 * 8.00 = 24.00
        self.assertEqual(item.subtotal, Decimal("24.00"))

    def test_item_carrito_subtotal_redondeo(self):
        # Crear producto con precio que cause redondeo
        # Nota: DecimalField con decimal_places=2 no permitirá 10.333
        # Usaremos un precio válido que cause redondeo en el cálculo
        producto2 = Producto.objects.create(
            nombre="Producto 2",
            precio=Decimal("10.33"),
            marca=self.marca
        )
        item = ItemCarrito.objects.create(
            carrito=self.carrito,
            producto=producto2,
            cantidad=3
        )
        # Subtotal = 3 * 10.33 = 30.99
        self.assertEqual(item.subtotal, Decimal("30.99"))

    def test_item_carrito_cascade_delete_carrito(self):
        item = ItemCarrito.objects.create(
            carrito=self.carrito,
            producto=self.producto,
            cantidad=2
        )
        self.carrito.delete()
        self.assertFalse(ItemCarrito.objects.filter(id=item.id).exists())

    def test_item_carrito_cascade_delete_producto(self):
        item = ItemCarrito.objects.create(
            carrito=self.carrito,
            producto=self.producto,
            cantidad=2
        )
        self.producto.delete()
        self.assertFalse(ItemCarrito.objects.filter(id=item.id).exists())


class MensajeContactoModelTest(TestCase):
    def test_crear_mensaje_contacto(self):
        mensaje = MensajeContacto.objects.create(
            nombre="Juan Pérez",
            email="juan@example.com",
            mensaje="Mensaje de prueba"
        )
        self.assertEqual(mensaje.nombre, "Juan Pérez")
        self.assertEqual(mensaje.email, "juan@example.com")
        self.assertEqual(mensaje.mensaje, "Mensaje de prueba")
        self.assertIsNotNone(mensaje.fecha)
        self.assertEqual(str(mensaje), "Juan Pérez - juan@example.com")

    def test_mensaje_contacto_fecha_auto(self):
        mensaje = MensajeContacto.objects.create(
            nombre="Juan",
            email="juan@example.com",
            mensaje="Test"
        )
        self.assertIsNotNone(mensaje.fecha)
        self.assertLessEqual(mensaje.fecha, timezone.now())
