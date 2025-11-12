from decimal import Decimal
from django.db import models
from django.utils import timezone

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
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    precio_oferta = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
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
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    stock = models.IntegerField(default=0)
    esta_disponible = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(default=timezone.now)
    es_destacado = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'

    def save(self, *args, **kwargs):
        self.fecha_actualizacion = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre