"""
Pruebas de integración para las vistas de la aplicación.
Estas pruebas verifican el flujo completo de interacción entre vistas, modelos, formularios y sesiones.
"""
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.messages import get_messages
import json
import datetime

from .models import (
    Producto,
    Marca,
    Categoria,
    Cliente,
    Pedido,
    ItemPedido,
    MensajeContacto,
    ImagenProducto,
)

User = get_user_model()


class IndexViewTest(TestCase):
    def setUp(self):
        self.client = Client()
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
            nombre="Pienso Premium",
            descripcion="Pienso de alta calidad",
            precio=Decimal("29.99"),
            marca=self.marca,
            esta_disponible=True,
            es_destacado=True
        )
        self.producto2 = Producto.objects.create(
            nombre="Juguete para perros",
            descripcion="Juguete resistente",
            precio=Decimal("15.00"),
            marca=self.marca,
            esta_disponible=True,
            es_destacado=False
        )
        self.producto_no_disponible = Producto.objects.create(
            nombre="Producto no disponible",
            precio=Decimal("10.00"),
            marca=self.marca,
            esta_disponible=False
        )

    def test_index_sin_busqueda(self):
        """Test que la página principal muestra productos disponibles."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('productos', response.context)
        productos = response.context['productos']
        # Debe mostrar solo productos disponibles
        self.assertTrue(all(p.esta_disponible for p in productos))
        # No debe mostrar más de 8 productos
        self.assertLessEqual(len(productos), 8)

    def test_index_con_busqueda(self):
        """Test que la búsqueda filtra productos correctamente."""
        response = self.client.get(reverse('home'), {'q': 'Pienso'})
        self.assertEqual(response.status_code, 200)
        productos = response.context['productos']
        self.assertGreater(len(productos), 0)
        # Todos deben contener "Pienso" en algún campo
        self.assertTrue(any('Pienso' in p.nombre for p in productos))

    def test_index_busqueda_por_genero(self):
        """Test que la búsqueda funciona por género."""
        self.producto1.genero = Producto.Especie.PERRO
        self.producto1.save()
        response = self.client.get(reverse('home'), {'q': 'perro'})
        self.assertEqual(response.status_code, 200)
        productos = response.context['productos']
        self.assertGreater(len(productos), 0)

    def test_index_no_muestra_productos_no_disponibles(self):
        """Test que no se muestran productos no disponibles."""
        response = self.client.get(reverse('home'))
        productos = response.context['productos']
        self.assertNotIn(self.producto_no_disponible, productos)


class ProductosViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        imagen_marca = SimpleUploadedFile(
            name="marca.jpg",
            content=b"fake image content",
            content_type="image/jpeg"
        )
        self.marca = Marca.objects.create(
            nombre="Royal Canin",
            imagen=imagen_marca
        )
        self.producto_destacado = Producto.objects.create(
            nombre="Producto Destacado",
            precio=Decimal("20.00"),
            marca=self.marca,
            esta_disponible=True,
            es_destacado=True
        )
        self.producto_normal = Producto.objects.create(
            nombre="Producto Normal",
            precio=Decimal("15.00"),
            marca=self.marca,
            esta_disponible=True,
            es_destacado=False
        )

    def test_productos_view(self):
        """Test que la vista de productos muestra destacados y normales."""
        response = self.client.get(reverse('productos'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('destacados', response.context)
        self.assertIn('productos', response.context)
        self.assertIn(self.producto_destacado, response.context['destacados'])
        self.assertIn(self.producto_normal, response.context['productos'])

    def test_ofertas_view(self):
        """Test que la vista de ofertas muestra solo productos con oferta."""
        self.producto_destacado.precio_oferta = Decimal("15.00")
        self.producto_destacado.save()
        
        response = self.client.get(reverse('ofertas'))
        self.assertEqual(response.status_code, 200)
        productos = response.context['productos']
        self.assertIn(self.producto_destacado, productos)
        self.assertNotIn(self.producto_normal, productos)

    def test_novedades_view(self):
        """Test que la vista de novedades muestra productos recientes."""
        # Crear producto reciente
        producto_reciente = Producto.objects.create(
            nombre="Producto Nuevo",
            precio=Decimal("10.00"),
            marca=self.marca,
            esta_disponible=True,
            fecha_creacion=timezone.now()
        )
        
        response = self.client.get(reverse('novedades'))
        self.assertEqual(response.status_code, 200)
        productos = response.context['productos']
        # El producto reciente debe estar en la lista
        self.assertIn(producto_reciente, productos)

    def test_product_detail_view(self):
        """Test que la vista de detalle muestra el producto correcto."""
        response = self.client.get(reverse('product_detail', args=[self.producto_destacado.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['producto'], self.producto_destacado)

    def test_product_detail_404_no_disponible(self):
        """Test que productos no disponibles devuelven 404."""
        self.producto_destacado.esta_disponible = False
        self.producto_destacado.save()
        response = self.client.get(reverse('product_detail', args=[self.producto_destacado.id]))
        self.assertEqual(response.status_code, 404)


class CategoriaViewTest(TestCase):
    def setUp(self):
        self.client = Client()
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
        self.producto = Producto.objects.create(
            nombre="Pienso",
            precio=Decimal("20.00"),
            marca=self.marca,
            categoria=self.categoria,
            esta_disponible=True
        )

    def test_categorias_view(self):
        """Test que la vista de categorías lista todas las categorías."""
        response = self.client.get(reverse('categorias'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('categorias', response.context)
        self.assertIn(self.categoria, response.context['categorias'])

    def test_categoria_detail_view(self):
        """Test que la vista de detalle de categoría muestra sus productos."""
        response = self.client.get(reverse('categoria_detail', args=[self.categoria.id]))
        self.assertEqual(response.status_code, 200)
        productos = response.context['productos']
        self.assertIn(self.producto, productos)


class CartViewTest(TestCase):
    def setUp(self):
        self.client = Client()
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
            marca=self.marca,
            esta_disponible=True
        )

    def test_cart_view_vacio(self):
        """Test que el carrito vacío se muestra correctamente."""
        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['items']), 0)
        self.assertEqual(response.context['total'], 0)

    def test_add_to_cart(self):
        """Test que se puede añadir un producto al carrito (sin AJAX)."""
        response = self.client.post(reverse('add_to_cart', args=[self.producto.id]))
        self.assertEqual(response.status_code, 302)  # Redirect
        
        # Verificar que el producto está en la sesión
        session = self.client.session
        self.assertIn('cart', session)
        key = f"{self.producto.id}:"
        self.assertIn(key, session['cart'])
        self.assertEqual(session['cart'][key], 1)

    def test_add_to_cart_ajax(self):
        """Test que se puede añadir un producto al carrito vía AJAX."""
        response = self.client.post(
            reverse('add_to_cart', args=[self.producto.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)  # JSON response
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['cart_count'], 1)
        self.assertIn('cart_items', data)
        self.assertIn('cart_total', data)
        
        # Verificar que el producto está en la sesión
        session = self.client.session
        self.assertIn('cart', session)
        key = f"{self.producto.id}:"
        self.assertIn(key, session['cart'])
        self.assertEqual(session['cart'][key], 1)

    def test_add_to_cart_con_talla(self):
        """Test que se puede añadir un producto con talla."""
        response = self.client.post(
            reverse('add_to_cart', args=[self.producto.id]),
            {'size': 'M'}
        )
        self.assertEqual(response.status_code, 302)
        
        session = self.client.session
        key = f"{self.producto.id}:M"
        self.assertIn(key, session['cart'])

    def test_add_to_cart_con_talla_ajax(self):
        """Test que se puede añadir un producto con talla vía AJAX."""
        response = self.client.post(
            reverse('add_to_cart', args=[self.producto.id]),
            {'size': 'M'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        session = self.client.session
        key = f"{self.producto.id}:M"
        self.assertIn(key, session['cart'])

    def test_add_to_cart_incrementa_cantidad(self):
        """Test que añadir el mismo producto incrementa la cantidad."""
        self.client.post(reverse('add_to_cart', args=[self.producto.id]))
        self.client.post(reverse('add_to_cart', args=[self.producto.id]))
        
        session = self.client.session
        key = f"{self.producto.id}:"
        self.assertEqual(session['cart'][key], 2)

    def test_cart_view_con_productos(self):
        """Test que el carrito muestra los productos correctamente."""
        # Añadir productos al carrito
        self.client.post(reverse('add_to_cart', args=[self.producto.id]))
        self.client.post(reverse('add_to_cart', args=[self.producto.id]))
        
        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)
        items = response.context['items']
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['cantidad'], 2)
        self.assertEqual(items[0]['producto'], self.producto)
        self.assertEqual(response.context['total'], Decimal("20.00"))

    def test_cart_decrement(self):
        """Test que se puede decrementar la cantidad en el carrito."""
        # Añadir 2 productos
        self.client.post(reverse('add_to_cart', args=[self.producto.id]))
        self.client.post(reverse('add_to_cart', args=[self.producto.id]))
        
        # Decrementar
        response = self.client.post(reverse('cart_decrement', args=[self.producto.id]))
        self.assertEqual(response.status_code, 302)
        
        session = self.client.session
        key = f"{self.producto.id}:"
        self.assertEqual(session['cart'][key], 1)

    def test_cart_decrement_ajax(self):
        """Test que se puede decrementar la cantidad vía AJAX."""
        # Añadir 2 productos
        self.client.post(reverse('add_to_cart', args=[self.producto.id]))
        self.client.post(reverse('add_to_cart', args=[self.producto.id]))
        
        # Decrementar vía AJAX
        response = self.client.post(
            reverse('cart_decrement', args=[self.producto.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['cart_count'], 1)
        
        session = self.client.session
        key = f"{self.producto.id}:"
        self.assertEqual(session['cart'][key], 1)

    def test_cart_decrement_elimina_si_cero(self):
        """Test que decrementar a 0 elimina el producto del carrito."""
        self.client.post(reverse('add_to_cart', args=[self.producto.id]))
        self.client.post(reverse('cart_decrement', args=[self.producto.id]))
        
        session = self.client.session
        key = f"{self.producto.id}:"
        self.assertNotIn(key, session['cart'])

    def test_cart_remove(self):
        """Test que se puede eliminar un producto del carrito."""
        self.client.post(reverse('add_to_cart', args=[self.producto.id]))
        response = self.client.post(reverse('cart_remove', args=[self.producto.id]))
        self.assertEqual(response.status_code, 302)
        
        session = self.client.session
        key = f"{self.producto.id}:"
        self.assertNotIn(key, session['cart'])

    def test_cart_remove_ajax(self):
        """Test que se puede eliminar un producto del carrito vía AJAX."""
        self.client.post(reverse('add_to_cart', args=[self.producto.id]))
        response = self.client.post(
            reverse('cart_remove', args=[self.producto.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['cart_count'], 0)
        
        session = self.client.session
        key = f"{self.producto.id}:"
        self.assertNotIn(key, session['cart'])

    def test_cart_update(self):
        """Test que se puede actualizar la cantidad de un producto."""
        self.client.post(reverse('add_to_cart', args=[self.producto.id]))
        
        response = self.client.post(
            reverse('cart_update'),
            {'product_id': self.producto.id, 'quantity': '5', 'size': ''}
        )
        self.assertEqual(response.status_code, 302)
        
        session = self.client.session
        key = f"{self.producto.id}:"
        self.assertEqual(session['cart'][key], 5)

    def test_cart_update_ajax(self):
        """Test que se puede actualizar la cantidad vía AJAX."""
        self.client.post(reverse('add_to_cart', args=[self.producto.id]))
        
        response = self.client.post(
            reverse('cart_update'),
            {'product_id': self.producto.id, 'quantity': '5', 'size': ''},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['cart_count'], 5)
        
        session = self.client.session
        key = f"{self.producto.id}:"
        self.assertEqual(session['cart'][key], 5)

    def test_cart_update_elimina_si_cero(self):
        """Test que actualizar a 0 elimina el producto."""
        self.client.post(reverse('add_to_cart', args=[self.producto.id]))
        
        self.client.post(
            reverse('cart_update'),
            {'product_id': self.producto.id, 'quantity': '0', 'size': ''}
        )
        
        session = self.client.session
        key = f"{self.producto.id}:"
        self.assertNotIn(key, session['cart'])

    def test_add_to_cart_solo_post(self):
        """Test que add_to_cart solo acepta POST."""
        response = self.client.get(reverse('add_to_cart', args=[self.producto.id]))
        self.assertEqual(response.status_code, 302)  # Redirect

    def test_add_to_cart_ajax_devuelve_items(self):
        """Test que la respuesta AJAX incluye los items del carrito."""
        # Añadir producto con imagen
        imagen = SimpleUploadedFile(
            name="producto.jpg",
            content=b"fake image content",
            content_type="image/jpeg"
        )
        ImagenProducto.objects.create(
            producto=self.producto,
            imagen=imagen,
            es_principal=True
        )
        
        response = self.client.post(
            reverse('add_to_cart', args=[self.producto.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['cart_items']), 1)
        self.assertEqual(data['cart_items'][0]['producto_id'], self.producto.id)
        self.assertEqual(data['cart_items'][0]['nombre'], self.producto.nombre)
        self.assertIsNotNone(data['cart_items'][0]['imagen_url'])
        self.assertEqual(data['cart_total'], float(self.producto.precio))


class AuthenticationViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password="testpass123"
        )
        self.cliente = Cliente.objects.create(
            nombre="Test",
            email="test@example.com",
            user=self.user
        )

    def test_login_view_get(self):
        """Test que la vista de login se muestra correctamente."""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_login_view_post_valido(self):
        """Test que el login funciona con credenciales válidas."""
        response = self.client.post(
            reverse('login'),
            {'username': 'test@example.com', 'password': 'testpass123'}
        )
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_view_post_invalido(self):
        """Test que el login falla con credenciales inválidas."""
        response = self.client.post(
            reverse('login'),
            {'username': 'test@example.com', 'password': 'wrongpass'}
        )
        self.assertEqual(response.status_code, 200)  # Vuelve al formulario
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_redirect_si_autenticado(self):
        """Test que usuarios autenticados son redirigidos."""
        self.client.login(username='test@example.com', password='testpass123')
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 302)

    def test_logout_view(self):
        """Test que el logout funciona correctamente."""
        self.client.login(username='test@example.com', password='testpass123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_register_view_get(self):
        """Test que la vista de registro se muestra correctamente."""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_register_view_post_valido(self):
        """Test que el registro crea un nuevo usuario y cliente."""
        response = self.client.post(
            reverse('register'),
            {
                'nombre': 'Nuevo',
                'apellidos': 'Usuario',
                'email': 'nuevo@example.com',
                'telefono': '123456789',
                'direccion': 'Calle Test 123',
                'ciudad': 'Madrid',
                'codigo_postal': '28001',
                'password1': 'newpass123',
                'password2': 'newpass123',
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect
        
        # Verificar que se creó el usuario
        self.assertTrue(User.objects.filter(email='nuevo@example.com').exists())
        # Verificar que se creó el cliente
        self.assertTrue(Cliente.objects.filter(email='nuevo@example.com').exists())
        # Verificar que el usuario está autenticado
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_register_view_post_invalido(self):
        """Test que el registro falla con datos inválidos."""
        response = self.client.post(
            reverse('register'),
            {
                'nombre': 'Nuevo',
                'email': 'test@example.com',  # Email ya existe
                'password1': 'pass123',
                'password2': 'pass456',  # Contraseñas no coinciden
            }
        )
        self.assertEqual(response.status_code, 200)  # Vuelve al formulario
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_register_redirect_si_autenticado(self):
        """Test que usuarios autenticados son redirigidos del registro."""
        self.client.login(username='test@example.com', password='testpass123')
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 302)


class ContactoViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_contacto_view_get(self):
        """Test que la vista de contacto se muestra correctamente."""
        response = self.client.get(reverse('contacto'))
        self.assertEqual(response.status_code, 200)

    def test_contacto_view_post_valido(self):
        """Test que se puede enviar un mensaje de contacto."""
        response = self.client.post(
            reverse('contacto'),
            {
                'nombre': 'Juan Pérez',
                'email': 'juan@example.com',
                'mensaje': 'Mensaje de prueba'
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect
        
        # Verificar que se creó el mensaje
        self.assertTrue(MensajeContacto.objects.filter(email='juan@example.com').exists())
        
        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('correctamente' in str(m) for m in messages))


class CheckoutViewTest(TestCase):
    def setUp(self):
        self.client = Client()
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
            marca=self.marca,
            esta_disponible=True
        )
        self.user = User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            password="testpass123"
        )
        self.cliente = Cliente.objects.create(
            nombre="Test",
            email="test@example.com",
            user=self.user
        )

    def test_checkout_datos_requiere_login(self):
        """Test que checkout_datos requiere autenticación."""
        response = self.client.get(reverse('checkout_datos'))
        self.assertEqual(response.status_code, 302)  # Redirect a login

    def test_checkout_datos_carrito_vacio(self):
        """Test que checkout_datos redirige si el carrito está vacío."""
        self.client.login(username='test@example.com', password='testpass123')
        response = self.client.get(reverse('checkout_datos'))
        self.assertEqual(response.status_code, 302)  # Redirect a cart
        
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('vacío' in str(m) for m in messages))

    def test_checkout_datos_con_carrito(self):
        """Test que checkout_datos se muestra con carrito."""
        self.client.login(username='test@example.com', password='testpass123')
        # Añadir producto al carrito
        self.client.post(reverse('add_to_cart', args=[self.producto.id]))
        
        response = self.client.get(reverse('checkout_datos'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIn('cliente', response.context)

    def test_checkout_datos_post_valido(self):
        """Test que se pueden guardar los datos de envío."""
        self.client.login(username='test@example.com', password='testpass123')
        self.client.post(reverse('add_to_cart', args=[self.producto.id]))
        
        response = self.client.post(
            reverse('checkout_datos'),
            {
                'nombre': 'Test Actualizado',
                'apellidos': 'Apellidos',
                'telefono': '123456789',
                'direccion': 'Calle Nueva 123',
                'ciudad': 'Madrid',
                'codigo_postal': '28001',
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect a detalles_pago
        
        # Verificar que se actualizó el cliente
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.direccion, 'Calle Nueva 123')

    def test_detalles_pago_requiere_login(self):
        """Test que detalles_pago requiere autenticación."""
        response = self.client.get(reverse('detalles_pago'))
        self.assertEqual(response.status_code, 302)

    def test_detalles_pago_carrito_vacio(self):
        """Test que detalles_pago redirige si el carrito está vacío."""
        self.client.login(username='test@example.com', password='testpass123')
        response = self.client.get(reverse('detalles_pago'))
        self.assertEqual(response.status_code, 302)

    def test_detalles_pago_sin_cliente(self):
        """Test que detalles_pago redirige si no hay cliente."""
        # Crear usuario sin cliente
        user2 = User.objects.create_user(
            username="test2@example.com",
            email="test2@example.com",
            password="testpass123"
        )
        self.client.login(username='test2@example.com', password='testpass123')
        self.client.post(reverse('add_to_cart', args=[self.producto.id]))
        
        response = self.client.get(reverse('detalles_pago'))
        self.assertEqual(response.status_code, 302)  # Redirect a checkout_datos

    def test_detalles_pago_con_carrito(self):
        """Test que detalles_pago muestra el resumen correcto."""
        self.client.login(username='test@example.com', password='testpass123')
        self.client.post(reverse('add_to_cart', args=[self.producto.id]))
        self.client.post(reverse('add_to_cart', args=[self.producto.id]))
        
        response = self.client.get(reverse('detalles_pago'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('items', response.context)
        self.assertIn('total', response.context)
        self.assertEqual(response.context['total'], Decimal("20.00"))

    def test_detalles_pago_con_oferta(self):
        """Test que detalles_pago usa precio_oferta cuando existe."""
        self.producto.precio_oferta = Decimal("8.00")
        self.producto.save()
        
        self.client.login(username='test@example.com', password='testpass123')
        self.client.post(reverse('add_to_cart', args=[self.producto.id]))
        
        response = self.client.get(reverse('detalles_pago'))
        self.assertEqual(response.status_code, 200)
        # El total debe usar precio_oferta
        items = response.context['items']
        self.assertEqual(items[0]['subtotal'], Decimal("8.00"))


class SeguimientoPedidoViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.cliente = Cliente.objects.create(
            nombre="Test",
            email="test@example.com"
        )
        self.pedido = Pedido.objects.create(
            cliente=self.cliente,
            numero_pedido="MP-20240101120000-ABCD",
            estado=Pedido.Estados.PAGADO
        )

    def test_seguimiento_pedido_get(self):
        """Test que la vista de seguimiento se muestra correctamente."""
        response = self.client.get(reverse('tracking'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_seguimiento_pedido_encontrado(self):
        """Test que se encuentra un pedido válido."""
        response = self.client.post(
            reverse('tracking'),
            {'numero_pedido': 'MP-20240101120000-ABCD'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['pedido'])
        self.assertEqual(response.context['pedido'], self.pedido)

    def test_seguimiento_pedido_no_encontrado(self):
        """Test que se muestra error si el pedido no existe."""
        response = self.client.post(
            reverse('tracking'),
            {'numero_pedido': 'MP-99999999999999-XXXX'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['pedido'])
        
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('No encontramos' in str(m) for m in messages))

    def test_seguimiento_pedido_case_insensitive(self):
        """Test que la búsqueda es case-insensitive."""
        response = self.client.post(
            reverse('tracking'),
            {'numero_pedido': 'mp-20240101120000-abcd'}  # minúsculas
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['pedido'])


class PagoViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
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
            marca=self.marca,
            esta_disponible=True
        )
        self.cliente = Cliente.objects.create(
            nombre="Test",
            email="test@example.com"
        )
        self.pedido = Pedido.objects.create(
            cliente=self.cliente,
            numero_pedido="MP-20240101120000-ABCD",
            estado=Pedido.Estados.PENDIENTE
        )

    def test_pago_ok_cambia_estado(self):
        """Test que pago_ok cambia el estado del pedido a PAGADO."""
        response = self.client.get(reverse('pago_ok', args=[self.pedido.id_pedido]))
        self.assertEqual(response.status_code, 200)
        
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, Pedido.Estados.PAGADO)

    def test_pago_ok_vacia_carrito(self):
        """Test que pago_ok vacía el carrito de la sesión."""
        session = self.client.session
        session['cart'] = {'1:': 2}
        session.save()
        
        response = self.client.get(reverse('pago_ok', args=[self.pedido.id_pedido]))
        self.assertEqual(response.status_code, 200)
        
        session = self.client.session
        self.assertEqual(session.get('cart', {}), {})

    def test_pago_cancelado_cambia_estado(self):
        """Test que pago_cancelado cambia el estado a CANCELADO."""
        response = self.client.get(reverse('pago_cancelado', args=[self.pedido.id_pedido]))
        self.assertEqual(response.status_code, 200)
        
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, Pedido.Estados.CANCELADO)


class AcercaDeViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_acerca_de_view(self):
        """Test que la vista acerca_de se muestra correctamente."""
        response = self.client.get(reverse('acerca_de'))
        self.assertEqual(response.status_code, 200)

