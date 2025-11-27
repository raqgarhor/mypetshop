from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Sum, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta

from .decorators import admin_required
from .forms import ProductoAdminForm, ClienteAdminForm
from .models import (
    Cliente,
    Pedido,
    Producto,
    Categoria,
    Marca,
    MensajeContacto,
    ImagenProducto,
)


@admin_required
def admin_dashboard(request):
    """Panel principal del administrador"""
    
    # Estadísticas generales
    total_clientes = Cliente.objects.count()
    total_productos = Producto.objects.count()
    total_pedidos = Pedido.objects.count()
    
    # Estadísticas de pedidos
    pedidos_pendientes = Pedido.objects.filter(estado='pendiente').count()
    pedidos_pagados = Pedido.objects.filter(estado='pagado').count()
    pedidos_enviados = Pedido.objects.filter(estado='enviado').count()
    
    # Ventas del mes
    inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ventas_mes = Pedido.objects.filter(
        fecha_creacion__gte=inicio_mes,
        estado__in=['pagado', 'enviado', 'entregado']
    ).aggregate(total=Sum('total'))['total'] or 0
    
    # Pedidos recientes
    pedidos_recientes = Pedido.objects.select_related('cliente').order_by('-fecha_creacion')[:10]
    
    # Productos con bajo stock
    productos_bajo_stock = Producto.objects.filter(stock__lt=10, esta_disponible=True)[:10]
    
    contexto = {
        'total_clientes': total_clientes,
        'total_productos': total_productos,
        'total_pedidos': total_pedidos,
        'pedidos_pendientes': pedidos_pendientes,
        'pedidos_pagados': pedidos_pagados,
        'pedidos_enviados': pedidos_enviados,
        'ventas_mes': ventas_mes,
        'pedidos_recientes': pedidos_recientes,
        'productos_bajo_stock': productos_bajo_stock,
    }
    
    return render(request, 'admin_portal/dashboard.html', contexto)


@admin_required
def admin_pedidos(request):
    """Lista de todos los pedidos"""
    estado_filtro = request.GET.get('estado', '')
    
    pedidos_list = Pedido.objects.select_related('cliente').order_by('-fecha_creacion')
    
    if estado_filtro:
        pedidos_list = pedidos_list.filter(estado=estado_filtro)
    
    # Paginación
    paginator = Paginator(pedidos_list, 20)  # 20 pedidos por página
    page = request.GET.get('page')
    try:
        pedidos = paginator.page(page)
    except PageNotAnInteger:
        pedidos = paginator.page(1)
    except EmptyPage:
        pedidos = paginator.page(paginator.num_pages)
    
    estados = Pedido.Estados.choices
    
    contexto = {
        'pedidos': pedidos,
        'estados': estados,
        'estado_filtro': estado_filtro,
    }
    
    return render(request, 'admin_portal/pedidos.html', contexto)


@admin_required
def admin_pedido_detalle(request, pedido_id):
    """Detalle de un pedido específico"""
    pedido = get_object_or_404(Pedido.objects.select_related('cliente'), id_pedido=pedido_id)
    items = pedido.items.select_related('producto').all()
    
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        if nuevo_estado in [estado[0] for estado in Pedido.Estados.choices]:
            pedido.estado = nuevo_estado
            pedido.save()
            messages.success(request, f'Estado del pedido actualizado a: {pedido.get_estado_display()}')
            return redirect('admin_panel:pedido_detalle', pedido_id=pedido_id)
    
    estados = Pedido.Estados.choices
    
    # Filtrar estados para el slider (excluir cancelado)
    estados_slider = [estado for estado in estados if estado[0] != 'cancelado']
    
    # Determinar qué estados ya pasaron para el timeline
    orden_estados = ['pendiente', 'pagado', 'en_proceso', 'enviado', 'entregado']
    estado_actual = pedido.estado
    indice_actual = orden_estados.index(estado_actual) if estado_actual in orden_estados else -1
    
    estados_timeline = []
    for idx, estado in enumerate(orden_estados):
        if idx < indice_actual:
            estados_timeline.append({'estado': estado, 'tipo': 'completado'})
        elif idx == indice_actual:
            estados_timeline.append({'estado': estado, 'tipo': 'actual'})
        else:
            estados_timeline.append({'estado': estado, 'tipo': 'pendiente'})
    
    contexto = {
        'pedido': pedido,
        'items': items,
        'estados': estados,
        'estados_slider': estados_slider,
        'estados_timeline': estados_timeline,
    }
    
    return render(request, 'admin_portal/pedido_detalle.html', contexto)


@admin_required
def admin_productos(request):
    """Gestión de productos"""
    productos_list = Producto.objects.select_related('marca', 'categoria').all()
    
    # Filtros
    categoria_filtro = request.GET.get('categoria', '')
    disponible_filtro = request.GET.get('disponible', '')
    busqueda = request.GET.get('q', '')
    
    if categoria_filtro:
        productos_list = productos_list.filter(categoria_id=categoria_filtro)
    
    if disponible_filtro == 'si':
        productos_list = productos_list.filter(esta_disponible=True)
    elif disponible_filtro == 'no':
        productos_list = productos_list.filter(esta_disponible=False)
    
    if busqueda:
        productos_list = productos_list.filter(
            Q(nombre__icontains=busqueda) |
            Q(descripcion__icontains=busqueda)
        )
    
    # Paginación
    paginator = Paginator(productos_list, 20)  # 20 productos por página
    page = request.GET.get('page')
    try:
        productos = paginator.page(page)
    except PageNotAnInteger:
        productos = paginator.page(1)
    except EmptyPage:
        productos = paginator.page(paginator.num_pages)
    
    categorias = Categoria.objects.all()
    
    contexto = {
        'productos': productos,
        'categorias': categorias,
        'categoria_filtro': categoria_filtro,
        'disponible_filtro': disponible_filtro,
        'busqueda': busqueda,
    }
    
    return render(request, 'admin_portal/productos.html', contexto)


@admin_required
def admin_producto_crear(request):
    """Crear un nuevo producto"""
    if request.method == 'POST':
        form = ProductoAdminForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save()
            
            # Manejar imágenes subidas
            imagenes = request.FILES.getlist('imagenes')
            if imagenes:
                # La primera imagen será la principal
                for idx, imagen_file in enumerate(imagenes):
                    ImagenProducto.objects.create(
                        producto=producto,
                        imagen=imagen_file,
                        es_principal=(idx == 0)
                    )
            
            messages.success(request, f'Producto "{producto.nombre}" creado exitosamente.')
            return redirect('admin_panel:productos')
    else:
        form = ProductoAdminForm()
    
    contexto = {
        'form': form,
        'titulo': 'Crear Nuevo Producto',
        'accion': 'Crear',
        'imagenes_existentes': [],
    }
    
    return render(request, 'admin_portal/producto_form.html', contexto)


@admin_required
def admin_producto_editar(request, producto_id):
    """Editar un producto existente"""
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        form = ProductoAdminForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            producto = form.save()
            
            # Manejar nuevas imágenes subidas
            imagenes = request.FILES.getlist('imagenes')
            if imagenes:
                # Si no hay imágenes principales, la primera nueva será principal
                tiene_principal = ImagenProducto.objects.filter(producto=producto, es_principal=True).exists()
                for idx, imagen_file in enumerate(imagenes):
                    es_principal = (idx == 0 and not tiene_principal)
                    ImagenProducto.objects.create(
                        producto=producto,
                        imagen=imagen_file,
                        es_principal=es_principal
                    )
            
            # Manejar eliminación de imágenes
            imagenes_eliminar = request.POST.getlist('eliminar_imagen')
            if imagenes_eliminar:
                ImagenProducto.objects.filter(id__in=imagenes_eliminar, producto=producto).delete()
            
            # Manejar cambio de imagen principal
            imagen_principal_id = request.POST.get('imagen_principal')
            if imagen_principal_id:
                # Quitar principal de todas las imágenes
                ImagenProducto.objects.filter(producto=producto).update(es_principal=False)
                # Marcar la seleccionada como principal
                ImagenProducto.objects.filter(id=imagen_principal_id, producto=producto).update(es_principal=True)
            
            messages.success(request, f'Producto "{producto.nombre}" actualizado exitosamente.')
            return redirect('admin_panel:productos')
    else:
        form = ProductoAdminForm(instance=producto)
    
    imagenes_existentes = producto.imagenes.all()
    
    contexto = {
        'form': form,
        'producto': producto,
        'titulo': f'Editar Producto: {producto.nombre}',
        'accion': 'Guardar Cambios',
        'imagenes_existentes': imagenes_existentes,
    }
    
    return render(request, 'admin_portal/producto_form.html', contexto)


@admin_required
def admin_producto_eliminar(request, producto_id):
    """Eliminar un producto"""
    producto = get_object_or_404(Producto, id=producto_id)
    
    # Verificar si el producto tiene pedidos asociados (PROTECT)
    pedidos_count = producto.items_pedido.count()
    
    if pedidos_count > 0:
        messages.error(
            request, 
            f'No se puede eliminar el producto "{producto.nombre}" porque tiene {pedidos_count} pedido(s) asociado(s).'
        )
        return redirect('admin_panel:productos')
    
    nombre_producto = producto.nombre
    producto.delete()
    messages.success(request, f'Producto "{nombre_producto}" eliminado exitosamente.')
    return redirect('admin_panel:productos')


@admin_required
def admin_clientes(request):
    """Lista de clientes"""
    clientes_list = Cliente.objects.select_related('user').all()
    
    busqueda = request.GET.get('q', '')
    admin_filtro = request.GET.get('admin', '')
    
    if busqueda:
        clientes_list = clientes_list.filter(
            Q(nombre__icontains=busqueda) |
            Q(apellidos__icontains=busqueda) |
            Q(email__icontains=busqueda)
        )
    
    if admin_filtro == 'si':
        clientes_list = clientes_list.filter(es_admin=True)
    elif admin_filtro == 'no':
        clientes_list = clientes_list.filter(es_admin=False)
    
    # Paginación
    paginator = Paginator(clientes_list, 20)  # 20 clientes por página
    page = request.GET.get('page')
    try:
        clientes = paginator.page(page)
    except PageNotAnInteger:
        clientes = paginator.page(1)
    except EmptyPage:
        clientes = paginator.page(paginator.num_pages)
    
    contexto = {
        'clientes': clientes,
        'busqueda': busqueda,
        'admin_filtro': admin_filtro,
    }
    
    return render(request, 'admin_portal/clientes.html', contexto)


@admin_required
def admin_cliente_crear(request):
    """Crear un nuevo cliente"""
    if request.method == 'POST':
        form = ClienteAdminForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f'Cliente "{cliente.nombre}" creado exitosamente.')
            return redirect('admin_panel:clientes')
    else:
        form = ClienteAdminForm()
    
    contexto = {
        'form': form,
        'titulo': 'Crear Nuevo Cliente',
        'accion': 'Crear',
    }
    
    return render(request, 'admin_portal/cliente_form.html', contexto)


@admin_required
def admin_cliente_editar(request, cliente_id):
    """Editar un cliente existente"""
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    if request.method == 'POST':
        form = ClienteAdminForm(request.POST, instance=cliente)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f'Cliente "{cliente.nombre}" actualizado exitosamente.')
            return redirect('admin_panel:clientes')
    else:
        form = ClienteAdminForm(instance=cliente)
    
    contexto = {
        'form': form,
        'cliente': cliente,
        'titulo': f'Editar Cliente: {cliente.nombre}',
        'accion': 'Guardar Cambios',
    }
    
    return render(request, 'admin_portal/cliente_form.html', contexto)


@admin_required
def admin_cliente_eliminar(request, cliente_id):
    """Eliminar un cliente"""
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    # Verificar si el cliente tiene pedidos asociados (PROTECT)
    pedidos_count = cliente.pedidos.count()
    
    if pedidos_count > 0:
        messages.error(
            request, 
            f'No se puede eliminar el cliente "{cliente.nombre} {cliente.apellidos or ""}" porque tiene {pedidos_count} pedido(s) asociado(s).'
        )
        return redirect('admin_panel:clientes')
    
    # No eliminar si es el cliente actual (el admin que está logueado)
    if request.user.is_authenticated and request.user.cliente and request.user.cliente.id == cliente.id:
        messages.error(request, 'No puedes eliminar tu propio perfil de cliente.')
        return redirect('admin_panel:clientes')
    
    nombre_cliente = f"{cliente.nombre} {cliente.apellidos or ''}".strip() or cliente.email
    
    # Eliminar el usuario asociado si existe (CASCADE se encargará, pero lo hacemos explícito)
    if cliente.user:
        usuario = cliente.user
        cliente.delete()  # Esto eliminará el cliente y el usuario por CASCADE
    else:
        cliente.delete()
    
    messages.success(request, f'Cliente "{nombre_cliente}" eliminado exitosamente.')
    return redirect('admin_panel:clientes')


@admin_required
def admin_mensajes(request):
    """Mensajes de contacto"""
    mensajes_list = MensajeContacto.objects.all().order_by('-fecha')
    
    # Paginación
    paginator = Paginator(mensajes_list, 20)  # 20 mensajes por página
    page = request.GET.get('page')
    try:
        mensajes = paginator.page(page)
    except PageNotAnInteger:
        mensajes = paginator.page(1)
    except EmptyPage:
        mensajes = paginator.page(paginator.num_pages)
    
    contexto = {
        'mensajes': mensajes,
    }
    
    return render(request, 'admin_portal/mensajes.html', contexto)

