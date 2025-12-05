# Documentación de Tests - My Pet Shop

Este documento forma parte de los **elementos configurables** del proyecto según el *Plan de Gestión de la Configuración* y recoge:

- Los **casos de prueba** implementados  
- Su estado de ejecución  
- El alcance cubierto (modelos, vistas y funcionalidades clave)  
- Las evidencias de validación de las funcionalidades  

Cumple además con la *Lista de Control de Calidad*, que exige comprobar la ejecución de pruebas unitarias e integración antes de la aceptación del entregable.

---

## 1. Alcance del Documento

El objetivo de este documento es describir todas las pruebas implementadas en el sistema **My Pet Shop**, incluyendo:

- Pruebas unitarias de modelos  
- Pruebas de lógica interna (carrito, totales, validaciones, etc.)  
- Pruebas de vistas  
- Pruebas de flujo del proceso de compra (checkout)  

Asimismo, este documento demuestra el cumplimiento de:

- El *Plan de Gestión de la Calidad*: ejecución de pruebas unitarias e integración  
- El *Plan de Gestión de la Configuración*: elemento configurable **Plan de Pruebas**, con casos de prueba y criterios de validación

---

## 2. Criterios Generales de Aceptación de las Pruebas

Una prueba se considera **superada (✓)** cuando:

1. La funcionalidad ejecuta el comportamiento especificado sin errores.
2. La salida coincide exactamente con el **resultado esperado**.
3. Los modelos validan correctamente los datos según sus métodos `clean()` y restricciones.
4. Las vistas devuelven:
   - el código HTTP adecuado,
   - el contexto esperado,
   - la plantilla o redirección correspondiente.
5. Las operaciones en BD respetan las reglas de integridad (`CASCADE`, `PROTECT`, etc.).
6. Las respuestas AJAX incluyen el JSON esperado.
7. Al finalizar la prueba, el estado del sistema es consistente.

---

## 3. Resumen General de Pruebas Ejecutadas

- **Total de Tests**: 131
- **Tests de Modelos**: 65
- **Tests de Vistas**: 66

---

## 4. Tests de Modelos (`tests.py`)

### ArticuloModelTest

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_crear_articulo` | Verifica la creación de un artículo con nombre y descripción | ✅ |

### EscaparateModelTest

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_crear_escaparate` | Verifica la creación de un escaparate asociado a un artículo | ✅ |
| `test_escaparate_cascade_delete` | Verifica que al eliminar un artículo se elimina el escaparate (CASCADE) | ✅ |

### MarcaModelTest

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_crear_marca` | Verifica la creación de una marca con nombre e imagen | ✅ |
| `test_marca_nombre_unico` | Verifica que el nombre de marca debe ser único | ✅ |

### CategoriaModelTest

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_crear_categoria` | Verifica la creación de una categoría con nombre, descripción e imagen | ✅ |
| `test_categoria_nombre_unico` | Verifica que el nombre de categoría debe ser único | ✅ |

### ProductoModelTest

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_crear_producto` | Verifica la creación de un producto con todos sus campos | ✅ |
| `test_producto_defaults` | Verifica los valores por defecto de un producto | ✅ |
| `test_producto_fecha_actualizacion_auto` | Verifica que la fecha de actualización se actualiza automáticamente | ✅ |
| `test_producto_clean_precio_negativo` | Verifica que no se permite precio negativo | ✅ |
| `test_producto_clean_precio_oferta_negativo` | Verifica que no se permite precio de oferta negativo | ✅ |
| `test_producto_clean_precio_oferta_mayor_igual_precio` | Verifica que el precio de oferta debe ser menor que el precio normal | ✅ |
| `test_producto_clean_precio_oferta_valido` | Verifica que un precio de oferta válido se guarda correctamente | ✅ |
| `test_producto_clean_stock_negativo` | Verifica que no se permite stock negativo | ✅ |
| `test_producto_especies_choices` | Verifica que se pueden usar las diferentes especies (PERRO, GATO, etc.) | ✅ |
| `test_producto_sin_categoria` | Verifica que un producto puede crearse sin categoría | ✅ |
| `test_producto_protect_marca` | Verifica que no se puede eliminar una marca si tiene productos (PROTECT) | ✅ |
| `test_producto_protect_categoria` | Verifica que no se puede eliminar una categoría si tiene productos (PROTECT) | ✅ |

### TallaProductoModelTest

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_crear_talla_producto` | Verifica la creación de una talla para un producto | ✅ |
| `test_talla_producto_cascade_delete` | Verifica que al eliminar un producto se eliminan sus tallas (CASCADE) | ✅ |
| `test_talla_producto_sin_producto` | Verifica que una talla puede crearse sin producto | ✅ |

### ImagenProductoModelTest

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_crear_imagen_producto` | Verifica la creación de una imagen para un producto | ✅ |
| `test_imagen_producto_cascade_delete` | Verifica que al eliminar un producto se eliminan sus imágenes (CASCADE) | ✅ |
| `test_imagen_producto_ordering` | Verifica que las imágenes principales aparecen primero en el ordenamiento | ✅ |

### ClienteModelTest

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_crear_cliente_sin_usuario` | Verifica la creación de un cliente sin usuario asociado | ✅ |
| `test_crear_cliente_con_usuario` | Verifica la creación de un cliente con usuario asociado | ✅ |
| `test_cliente_str_con_apellidos` | Verifica el método `__str__` con apellidos | ✅ |
| `test_cliente_str_sin_apellidos` | Verifica el método `__str__` sin apellidos | ✅ |
| `test_cliente_str_solo_email` | Verifica el método `__str__` cuando solo hay email | ✅ |
| `test_cliente_esta_logueado_sin_usuario` | Verifica que `esta_logueado` retorna False sin usuario | ✅ |
| `test_cliente_esta_logueado_con_usuario` | Verifica que `esta_logueado` retorna True con usuario | ✅ |
| `test_cliente_email_unico` | Verifica que el email debe ser único | ✅ |

### PedidoModelTest

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_crear_pedido` | Verifica la creación de un pedido con todos sus campos | ✅ |
| `test_pedido_defaults` | Verifica los valores por defecto de un pedido | ✅ |
| `test_pedido_total_calculo_nuevo` | Verifica el cálculo del total del pedido | ✅ |
| `test_pedido_recalcular_totales` | Verifica el método `recalcular_totales()` | ✅ |
| `test_pedido_recalcular_totales_con_impuestos` | Verifica el recálculo con impuestos, envío y descuento | ✅ |
| `test_pedido_quantize_redondeo` | Verifica que el total se redondea correctamente a 2 decimales | ✅ |
| `test_pedido_estados` | Verifica que se pueden usar todos los estados del pedido | ✅ |
| `test_pedido_protect_cliente` | Verifica que no se puede eliminar un cliente si tiene pedidos (PROTECT) | ✅ |

### ItemPedidoModelTest

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_crear_item_pedido` | Verifica la creación de un item de pedido | ✅ |
| `test_item_pedido_precio_unitario_auto` | Verifica que el precio unitario se toma del producto automáticamente | ✅ |
| `test_item_pedido_total_calculo` | Verifica el cálculo del total del item (cantidad × precio) | ✅ |
| `test_item_pedido_recalcula_pedido_total` | Verifica que al crear un item se recalcula el total del pedido | ✅ |
| `test_item_pedido_cascade_delete` | Verifica que al eliminar un pedido se eliminan sus items (CASCADE) | ✅ |
| `test_item_pedido_protect_producto` | Verifica que no se puede eliminar un producto si tiene items en pedidos (PROTECT) | ✅ |

### CarritoModelTest

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_crear_carrito` | Verifica la creación de un carrito con cliente | ✅ |
| `test_crear_carrito_sin_cliente` | Verifica la creación de un carrito sin cliente (anónimo) | ✅ |
| `test_carrito_fecha_actualizacion_auto` | Verifica que la fecha de actualización se actualiza automáticamente | ✅ |
| `test_carrito_add_producto_nuevo` | Verifica añadir un producto nuevo al carrito | ✅ |
| `test_carrito_add_producto_existente` | Verifica que añadir un producto existente incrementa la cantidad | ✅ |
| `test_carrito_add_producto_con_talla` | Verifica añadir productos con diferentes tallas como items separados | ✅ |
| `test_carrito_add_producto_cantidad_invalida` | Verifica que no se permite cantidad 0 o negativa | ✅ |
| `test_carrito_remove_producto` | Verifica eliminar un producto del carrito | ✅ |
| `test_carrito_remove_producto_con_talla` | Verifica eliminar un producto con talla específica | ✅ |
| `test_carrito_set_cantidad` | Verifica establecer la cantidad de un producto | ✅ |
| `test_carrito_set_cantidad_cero_elimina` | Verifica que establecer cantidad a 0 elimina el producto | ✅ |
| `test_carrito_total_items` | Verifica el cálculo del total de items en el carrito | ✅ |
| `test_carrito_total_items_vacio` | Verifica que un carrito vacío tiene 0 items | ✅ |
| `test_carrito_get_total` | Verifica el cálculo del total monetario del carrito | ✅ |
| `test_carrito_get_total_con_oferta` | Verifica que se usa precio_oferta cuando existe | ✅ |
| `test_carrito_clear` | Verifica que el método `clear()` elimina todos los items | ✅ |
| `test_carrito_cascade_delete` | Verifica que al eliminar un cliente se elimina su carrito (CASCADE) | ✅ |

### ItemCarritoModelTest

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_crear_item_carrito` | Verifica la creación de un item de carrito | ✅ |
| `test_item_carrito_precio_unitario` | Verifica que el precio unitario se toma del producto | ✅ |
| `test_item_carrito_precio_unitario_oferta` | Verifica que se usa precio_oferta cuando existe | ✅ |
| `test_item_carrito_precio_unitario_sin_precio` | Verifica el comportamiento con precio 0.00 | ✅ |
| `test_item_carrito_subtotal` | Verifica el cálculo del subtotal (cantidad × precio) | ✅ |
| `test_item_carrito_subtotal_con_oferta` | Verifica el subtotal usando precio_oferta | ✅ |
| `test_item_carrito_subtotal_redondeo` | Verifica el redondeo correcto del subtotal | ✅ |
| `test_item_carrito_cascade_delete_carrito` | Verifica que al eliminar un carrito se eliminan sus items (CASCADE) | ✅ |
| `test_item_carrito_cascade_delete_producto` | Verifica que al eliminar un producto se eliminan sus items del carrito (CASCADE) | ✅ |

### MensajeContactoModelTest

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_crear_mensaje_contacto` | Verifica la creación de un mensaje de contacto | ✅ |
| `test_mensaje_contacto_fecha_auto` | Verifica que la fecha se asigna automáticamente | ✅ |

---

## 5. Tests de Vistas (`test_views.py`)

### IndexViewTest

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_index_sin_busqueda` | Verifica que la página principal muestra productos disponibles (paginado, 12 por página) | ✅ |
| `test_index_con_busqueda` | Verifica que la búsqueda filtra productos correctamente | ✅ |
| `test_index_busqueda_por_genero` | Verifica que la búsqueda funciona por género | ✅ |
| `test_index_no_muestra_productos_no_disponibles` | Verifica que no se muestran productos no disponibles | ✅ |

### ProductosViewTest

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_productos_view` | Verifica que la vista de productos muestra destacados y normales | ✅ |
| `test_ofertas_view` | Verifica que la vista de ofertas muestra solo productos con oferta | ✅ |
| `test_novedades_view` | Verifica que la vista de novedades muestra productos recientes (últimos 30 días) | ✅ |
| `test_product_detail_view` | Verifica que la vista de detalle muestra el producto correcto | ✅ |
| `test_product_detail_404_no_disponible` | Verifica que productos no disponibles devuelven 404 | ✅ |

### CategoriaViewTest

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_categorias_view` | Verifica que la vista de categorías lista todas las categorías | ✅ |
| `test_categoria_detail_view` | Verifica que la vista de detalle de categoría muestra sus productos | ✅ |

### CartViewTest

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_cart_view_vacio` | Verifica que el carrito vacío se muestra correctamente | ✅ |
| `test_add_to_cart` | Verifica que se puede añadir un producto al carrito (sin AJAX) | ✅ |
| `test_add_to_cart_ajax` | Verifica que se puede añadir un producto al carrito vía AJAX | ✅ |
| `test_add_to_cart_con_talla` | Verifica que se puede añadir un producto con talla | ✅ |
| `test_add_to_cart_con_talla_ajax` | Verifica que se puede añadir un producto con talla vía AJAX | ✅ |
| `test_add_to_cart_incrementa_cantidad` | Verifica que añadir el mismo producto incrementa la cantidad | ✅ |
| `test_cart_view_con_productos` | Verifica que el carrito muestra los productos correctamente | ✅ |
| `test_cart_decrement` | Verifica que se puede decrementar la cantidad en el carrito | ✅ |
| `test_cart_decrement_ajax` | Verifica que se puede decrementar la cantidad vía AJAX | ✅ |
| `test_cart_decrement_elimina_si_cero` | Verifica que decrementar a 0 elimina el producto del carrito | ✅ |
| `test_cart_remove` | Verifica que se puede eliminar un producto del carrito | ✅ |
| `test_cart_remove_ajax` | Verifica que se puede eliminar un producto del carrito vía AJAX | ✅ |
| `test_cart_update` | Verifica que se puede actualizar la cantidad de un producto | ✅ |
| `test_cart_update_ajax` | Verifica que se puede actualizar la cantidad vía AJAX | ✅ |
| `test_cart_update_elimina_si_cero` | Verifica que actualizar a 0 elimina el producto | ✅ |
| `test_add_to_cart_solo_post` | Verifica que add_to_cart solo acepta POST | ✅ |
| `test_add_to_cart_ajax_devuelve_items` | Verifica que la respuesta AJAX incluye los items del carrito | ✅ |

### AuthenticationViewTest

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_login_view_get` | Verifica que la vista de login se muestra correctamente | ✅ |
| `test_login_view_post_valido` | Verifica que el login funciona con credenciales válidas | ✅ |
| `test_login_view_post_invalido` | Verifica que el login falla con credenciales inválidas | ✅ |
| `test_login_redirect_si_autenticado` | Verifica que usuarios autenticados son redirigidos | ✅ |
| `test_logout_view` | Verifica que el logout funciona correctamente | ✅ |
| `test_register_view_get` | Verifica que la vista de registro se muestra correctamente | ✅ |
| `test_register_view_post_valido` | Verifica que el registro crea un nuevo usuario y cliente | ✅ |
| `test_register_view_post_invalido` | Verifica que el registro falla con datos inválidos | ✅ |
| `test_register_redirect_si_autenticado` | Verifica que usuarios autenticados son redirigidos del registro | ✅ |

### ContactoViewTest

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_contacto_view_get` | Verifica que la vista de contacto se muestra correctamente | ✅ |
| `test_contacto_view_post_valido` | Verifica que se puede enviar un mensaje de contacto | ✅ |

### CheckoutViewTest

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_checkout_datos_requiere_login` | Verifica que checkout_datos requiere autenticación | ✅ |
| `test_checkout_datos_carrito_vacio` | Verifica que checkout_datos redirige si el carrito está vacío | ✅ |
| `test_checkout_datos_con_carrito` | Verifica que checkout_datos se muestra con carrito | ✅ |
| `test_checkout_datos_post_valido` | Verifica que se pueden guardar los datos de envío | ✅ |
| `test_detalles_pago_requiere_login` | Verifica que detalles_pago requiere autenticación | ✅ |
| `test_detalles_pago_carrito_vacio` | Verifica que detalles_pago redirige si el carrito está vacío | ✅ |
| `test_detalles_pago_sin_cliente` | Verifica que detalles_pago redirige si no hay cliente | ✅ |
| `test_detalles_pago_con_carrito` | Verifica que detalles_pago muestra el resumen correcto (con impuestos y envío) | ✅ |
| `test_detalles_pago_con_oferta` | Verifica que detalles_pago usa precio_oferta cuando existe | ✅ |

### SeguimientoPedidoViewTest

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_seguimiento_pedido_get` | Verifica que la vista de seguimiento se muestra correctamente | ✅ |
| `test_seguimiento_pedido_encontrado` | Verifica que se encuentra un pedido válido | ✅ |
| `test_seguimiento_pedido_no_encontrado` | Verifica que se muestra error si el pedido no existe | ✅ |
| `test_seguimiento_pedido_case_insensitive` | Verifica que la búsqueda es case-insensitive | ✅ |

### PagoViewsTest

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_pago_ok_cambia_estado` | Verifica que pago_ok cambia el estado del pedido a PAGADO | ✅ |
| `test_pago_ok_vacia_carrito` | Verifica que pago_ok vacía el carrito de la sesión | ✅ |
| `test_pago_cancelado_cambia_estado` | Verifica que pago_cancelado cambia el estado a CANCELADO | ✅ |

### AcercaDeViewTest

| Test | Descripción | Estado |
|------|-------------|--------|
| `test_acerca_de_view` | Verifica que la vista acerca_de se muestra correctamente | ✅ |

---

## 6. Notas Técnicas

### Configuración de Tests

- Todos los tests que requieren imágenes usan `@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)` para evitar crear archivos en el repositorio
- Se utiliza un directorio temporal que se limpia después de cada clase de tests
- Los tests de carrito usan claves compuestas (`product_id:size`) para manejar productos con tallas

### Cobertura

- **Modelos**: Todos los modelos principales tienen tests de creación, validación, relaciones y eliminación
- **Vistas**: Se cubren las vistas principales incluyendo casos de éxito, error, autenticación y redirecciones
- **Carrito**: Se prueban tanto las operaciones normales como las operaciones AJAX
- **Checkout**: Se verifica el flujo completo desde el carrito hasta el pago

## 8. Ejecución de las Pruebas

Para ejecutar todos los tests:

```bash
python manage.py test home.tests home.test_views
```

Para ejecutar una clase específica:

```bash
python manage.py test home.tests.ProductoModelTest
```

Para ejecutar un test específico:

```bash
python manage.py test home.tests.ProductoModelTest.test_crear_producto
```

