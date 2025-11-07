from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader

from .models import Articulo, Escaparate

def index(request):
    escaparates = Escaparate.objects.all() if Escaparate.objects.exists() else None
    escaparate = escaparates.first() if escaparates else None
    articulos = Articulo.objects.filter(pk=escaparate.articulo.id) if escaparate else None
    articulo = articulos.first() if articulos else None
    contexto = {'nombre_articulo': articulo.nombre} if articulo else {'nombre_articulo': 'Sin artículos disponibles'}
    plantilla = loader.get_template('index.html')
    return HttpResponse(plantilla.render(contexto, request))