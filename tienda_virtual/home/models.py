from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError


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
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'),
                                 validators=[MinValueValidator(Decimal('0.00'))])
    precio_oferta = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True,
                                        validators=[MinValueValidator(Decimal('0.00'))])

    marca = models.ForeignKey('Marca', on_delete=models.PROTECT, related_name='productos')
    categoria = models.ForeignKey('Categoria', on_delete=models.PROTECT, blank=True, null=True, related_name='productos')

    class Especie(models.TextChoices):
        PERRO = 'perro', 'Perro'
        GATO = 'gato', 'Gato'
        AVE = 'ave', 'Ave'
        ROEDOR = 'roedor', 'Roedor'
        REPTIL = 'reptil', 'Reptil'
        PEZ = 'pez', 'Pez'
        OTRO = 'otro', 'Otro'

    genero = models.CharField(max_length=20, choices=Especie.choices, default=Especie.PERRO)
    color = models.CharField(max_length=50, blank=True)
    material = models.CharField(max_length=100, blank=True)
    stock = models.PositiveIntegerField(default=0)
    esta_disponible = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(default=timezone.now)
    es_destacado = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def save(self, *args, **kwargs):
        self.fecha_actualizacion = timezone.now()
        self.full_clean()
        super().save(*args, **kwargs)
        

    def clean(self):
        errors = {}
        if self.precio is not None and self.precio < Decimal('0.00'):
            errors['precio'] = 'El precio no puede ser negativo.'
        if self.precio_oferta is not None:
            if self.precio_oferta < Decimal('0.00'):
                errors['precio_oferta'] = 'El precio de oferta no puede ser negativo.'
            elif self.precio_oferta >= self.precio:
                errors['precio_oferta'] = 'El precio de oferta debe ser menor que el precio normal.'
        if self.stock is not None and self.stock < 0:
            errors['stock'] = 'El stock no puede ser negativo.'

        if errors:
            raise ValidationError(errors)
        if self.fecha_creacion and self.fecha_actualizacion:
            if self.fecha_actualizacion < self.fecha_creacion:
                raise ValidationError({'fecha_actualizacion': 'La fecha de actualización no puede ser anterior a la fecha de creación.'})

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
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cliente",
        null=True,
        blank=True,
    )
    nombre = models.CharField(max_length=150)
    apellidos = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    codigo_postal = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        nombre_completo = " ".join(
            part for part in [self.nombre, self.apellidos] if part
        ).strip()
        return nombre_completo or self.email

    @property
    def esta_logueado(self) -> bool:
        """Helper to check if the related auth user has an active session."""
        user = getattr(self, "user", None)
        return bool(user and user.is_authenticated)


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
    talla = models.CharField(max_length=50, blank=True, null=True)
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


class Carrito(models.Model):
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="carritos",
        blank=True,
        null=True,
    )
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Carrito"
        verbose_name_plural = "Carritos"

    def save(self, *args, **kwargs):
        self.fecha_actualizacion = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Carrito #{self.pk} - {self.cliente or 'Anónimo'}"

    def add_producto(self, producto, talla="", cantidad=1):
        """
        Añade un producto al carrito. Si ya existe un ItemCarrito con el mismo producto y talla,
        incrementa la cantidad; en caso contrario crea uno nuevo.
        Devuelve (item, created_bool).
        """
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que 0")

        item, created = ItemCarrito.objects.get_or_create(
            carrito=self, producto=producto, talla=talla or ""
        )
        if not created:
            item.cantidad = item.cantidad + cantidad
        else:
            item.cantidad = cantidad
        item.save()
        # actualizar timestamp del carrito
        self.save(update_fields=["fecha_actualizacion"])
        return item, created

    def remove_producto(self, producto, talla=""):
        """Elimina el item correspondiente al producto/talla si existe."""
        ItemCarrito.objects.filter(carrito=self, producto=producto, talla=talla or "").delete()
        self.save(update_fields=["fecha_actualizacion"])

    def set_cantidad(self, producto, talla, cantidad):
        """Fija la cantidad de un item; si cantidad <= 0 elimina el item."""
        qs = ItemCarrito.objects.filter(carrito=self, producto=producto, talla=talla or "")
        if cantidad <= 0:
            qs.delete()
        else:
            qs.update(cantidad=cantidad)
        self.save(update_fields=["fecha_actualizacion"])

    def total_items(self) -> int:
        """Suma las cantidades de los items del carrito."""
        from django.db.models import Sum

        return self.items.aggregate(total=Sum("cantidad"))["total"] or 0

    def get_total(self) -> Decimal:
        """Suma los subtotales (usa precio_oferta cuando exista)."""
        total = Decimal("0.00")
        for item in self.items.select_related("producto").all():
            precio = item.producto.precio_oferta or item.producto.precio or Decimal("0.00")
            total += Decimal(item.cantidad) * precio
        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def clear(self):
        """Vacía el carrito."""
        self.items.all().delete()
        self.save(update_fields=["fecha_actualizacion"])


class ItemCarrito(models.Model):
    carrito = models.ForeignKey(
        Carrito,
        on_delete=models.CASCADE,
        related_name="items",
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="items_carrito",
    )
    talla = models.CharField(max_length=50, blank=True, null=True)
    cantidad = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Item de carrito"
        verbose_name_plural = "Items de carrito"

    @property
    def precio_unitario(self) -> Decimal:
        """Devuelve el precio unitario aplicable (oferta o normal)."""
        return self.producto.precio_oferta or self.producto.precio or Decimal("0.00")

    @property
    def subtotal(self) -> Decimal:
        """Subtotal = cantidad * precio_unitario (redondeado a 2 decimales)."""
        val = Decimal(self.cantidad) * self.precio_unitario
        return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad} ({self.talla})"

class MensajeContacto(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField()
    mensaje = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} - {self.email}"
