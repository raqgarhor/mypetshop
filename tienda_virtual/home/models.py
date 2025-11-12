from decimal import Decimal
from django.db import models

# Create your models here.
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
    stock = models.IntegerField(default=0)
    disponible = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    num_pedido = models.IntegerField(default=0)
    class Estado(models.TextChoices):
        NUEVO = 'nuevo', 'Nuevo'
        PENDIENTE_DE_PAGO = 'pendiente_pago', 'Pendiente de Pago'
        LISTO_ENVIO = 'listo_envio', 'Listo para Envío'
        ENVIADO = 'enviado', 'Enviado'
        EN_REPARTO = 'reparto', 'Reparto'
        ENTREGADO = 'entregado', 'Entregado'
        CANCELADO = 'cancelado', 'Cancelado'

    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.NUEVO)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    impuestos = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    coste_entrega = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # precio_total no almacenado: se calcula dinámicamente desde subtotal, impuestos, coste_entrega y descuento
    metodo_pago = models.CharField(max_length=50, default='No especificado')
    direccion_envio = models.CharField(max_length=255, blank=True)
    telefono_contacto = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'

    def calcular_precio_total(self) -> Decimal:
      
        subtotal = Decimal(str(self.subtotal)) if self.subtotal is not None else Decimal('0.00')
        impuestos = Decimal(str(self.impuestos)) if self.impuestos is not None else Decimal('0.00')
        coste_entrega = Decimal(str(self.coste_entrega)) if self.coste_entrega is not None else Decimal('0.00')
        descuento = Decimal(str(self.descuento)) if self.descuento is not None else Decimal('0.00')
        total = subtotal + impuestos + coste_entrega - descuento
        return total.quantize(Decimal('0.01'))

    def __str__(self):
        return f"{self.nombre} ({self.precio_total})"

    @property
    def precio_total(self) -> Decimal:
        return self.calcular_precio_total()