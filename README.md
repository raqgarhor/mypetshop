# Guía de Instalación

Este documento explica de forma clara los pasos necesarios para ejecutar el proyecto en entorno local con todas sus funcionalidades operativas.

## 🚀 Requisitos Previos
- Tener **Git** instalado
- Tener **Python 3.10** o superior

## 📥 Instalación
1. **Clona el repositorio:**
   ```bash
   git clone [url]
   ```

2. **Entra en la carpeta del proyecto:**
   ```bash
   cd mypetshop
   ```

3. **Crear el entorno virtual Python:**
   ```bash
   python –m venv .venv
   ```

4. **Activar el entorno virtual Python:**
   ```bash
   .\.venv\Scripts\actívate.bat
   ```

5. **Instalar Django:**
   ```bash
   python –m pip install Django
   ```

6. **Instalar requisitos de requirements.txt:**
   ```bash
   cd tienda_virtual
   ```

   ```bash
   pip install -r requirements.txt
   ```

7. **Modificar tu .env:**
    ```bash
   nano .env
   ```
   - Y poner los siquientes datos de prueba:
       ```bash
      STRIPE_PUBLISHABLE_KEY=pk_test_51SWd8HI0c80U4VWYIzD4P88VfqkSiOyUUFY3WZqiyDdBxVMFkfSq9ZrtRM4Zo9newkCV458NFP13shXW4KhEo4WJ00sbTmx1sq
      STRIPE_SECRET_KEY=sk_test_51SWd8HI0c80U4VWY96OlMqS4MQnZFOW4ehQvbKk3xnoheoxu1Jb6N6JP059FbMQtaMt62Tfv1IhdtRbYLIxJiBTq00XwfdKlUA
      SENDGRID_API_KEY=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
      EMAIL_FROM=raqgarhor@alum.us.es
      ```

## 💾 Cargar la base de datos

1. **Crear los archivos de migración:**
   ```bash
   cd tienda_virtual
   ```
   ```bash
   python manage.py makemigrations
   ```

2. **Aplicar las migraciones:**
   ```bash
   python manage.py migrate
   ```
   
3. **Poblar la DB con datos de prueba:**
   ```bash
   python manage.py seed --flush
   ```

## ▶️ Ejecutar en modo desarrollo
```bash
cd tienda_virtual
```
```bash
python manage.py runserver
```
