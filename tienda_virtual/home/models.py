from decimal import Decimal, ROUND_HALF_UP

from django.db import models
from django.utils import timezone


class Articulo(models.Model):
    nombre = models.CharField(max_length=30)
    descripcion = models.TextField(max_length=100)

    def __str__(self):
        return self.nombre


class Escaparate(models.Model):
    articulo = models.ForeignKey(Articulo, on_delete=models.CASCADE)

    def __str__(self):
        return self.articulo.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    precio_oferta = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    marca = models.ForeignKey('Marca', on_delete=models.PROTECT, related_name='productos')
    categoria = models.ForeignKey('Categoria', on_delete=models.PROTECT, blank=True, null=True, related_name='productos')

    class Especie(models.TextChoices):
        PERRO = 'perro', 'Perro'
        GATO = 'gato', 'Gato'
        AVE = 'ave', 'Ave'
        ROEDOR = 'roedor', 'Roedor'
        REPTIL = 'reptil', 'Reptil'
        PECERA = 'pecera', 'Pecera'
        OTRO = 'otro', 'Otro'

    genero = models.CharField(max_length=20, choices=Especie.choices, default=Especie.PERRO)
    color = models.CharField(max_length=50, blank=True)
    material = models.CharField(max_length=100, blank=True)

    ###imagen = models.ImageField(upload_to='productos/', blank=True, null=True) -> hay que quitarlo
    stock = models.IntegerField(default=0)
    esta_disponible = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(default=timezone.now)
    es_destacado = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def save(self, *args, **kwargs):
        self.fecha_actualizacion = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

class TallaProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='tallas', null=True, blank=True)
    talla = models.CharField(max_length=50)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.producto.nombre} - Talla: {self.talla}"

class ImagenProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='imagenes', null=True, blank=True)
    imagen = models.ImageField(upload_to='productos/imagenes/')
    es_principal = models.BooleanField(default=False)

    def __str__(self):
        return f"Imagen de {self.producto.nombre}"
    
    class Meta:
        # Mostrar primero las imágenes marcadas como principales
        ordering = ['-es_principal', 'id']

class Marca(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    imagen = models.ImageField(upload_to='marcas/imagenes/')

    def __str__(self):
        return self.nombre

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='categorias/imagenes/')

    def __str__(self):
        return self.nombre


class Cliente(models.Model):
    nombre = models.CharField(max_length=150)
    apellidos = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    direccion = models.CharField(max_length=255, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    codigo_postal = models.CharField(max_length=20, blank=True)
    password = models.CharField(max_length=128)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        nombre_completo = f"{self.nombre} {self.apellidos}".strip()
        return nombre_completo or self.email


class Pedido(models.Model):
    class Estados(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        PAGADO = "pagado", "Pagado"
        EN_PROCESO = "en_proceso", "En proceso"
        ENVIADO = "enviado", "Enviado"
        ENTREGADO = "entregado", "Entregado"
        CANCELADO = "cancelado", "Cancelado"

    id_pedido = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name="pedidos",
        blank=True,
        null=True,
    )
    fecha_creacion = models.DateTimeField(default=timezone.now)
    numero_pedido = models.CharField(max_length=50, unique=True)
    estado = models.CharField(
        max_length=20,
        choices=Estados.choices,
        default=Estados.PENDIENTE,
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    impuestos = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    coste_entrega = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    descuento = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    metodo_pago = models.CharField(max_length=100, blank=True)
    direccion_envio = models.CharField(max_length=255, blank=True)
    telefono = models.CharField(max_length=20, blank=True)


    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-fecha_creacion"]

    def _quantize(self, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def recalcular_totales(self):
        items = self.items.all()
        subtotal = sum((item.total for item in items), Decimal("0.00"))
        subtotal = self._quantize(subtotal)

        self.subtotal = subtotal
        total = subtotal + self.impuestos + self.coste_entrega - self.descuento
        self.total = self._quantize(total)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if not is_new:
            self.recalcular_totales()
        else:
            self.total = self._quantize(
                self.subtotal + self.impuestos + self.coste_entrega - self.descuento
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pedido #{self.numero_pedido}"


class ItemPedido(models.Model):
    id_item_pedido = models.AutoField(primary_key=True)
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="items",
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name="items_pedido",
    )
    talla = models.CharField(max_length=50, blank=True)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    class Meta:
        verbose_name = "Item de pedido"
        verbose_name_plural = "Items de pedido"

    def save(self, *args, **kwargs):
        if not self.precio_unitario:
            self.precio_unitario = self.producto.precio or Decimal("0.00")

        self.total = Decimal(self.cantidad) * self.precio_unitario
        self.total = self.total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        super().save(*args, **kwargs)
        # Recalcular totales del pedido asociado
        self.pedido.recalcular_totales()
        Pedido.objects.filter(pk=self.pedido.pk).update(
            subtotal=self.pedido.subtotal,
            total=self.pedido.total,
        )

    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad}"