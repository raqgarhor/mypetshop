# Guía de Instalación

Este documento explica de forma clara los pasos necesarios para ejecutar el proyecto en entorno local con todas sus funcionalidades operativas.

## 🚀 Requisitos Previos
- Tener **Git** instalado
- Tener **Python 3.10** o superior

## 📥 Instalación
1. **Clona el repositorio:**
   ```bash
   git clone https://github.com/raqgarhor/mypetshop.git
   ```

2. **Entra en la carpeta del proyecto:**
   ```bash
   cd mypetshop
   ```

3. **Crear el entorno virtual Python:**
   ```bash
   python -m venv .venv
   ```

4. **Activar el entorno virtual Python:**
   ```bash
   .\.venv\Scripts\activate
   ```

5. **Instalar Django:**
   ```bash
   python -m pip install Django
   ```

6. **Instalar requisitos de requirements.txt:**
   ```bash
   cd tienda_virtual
   ```

   ```bash
   pip install -r requirements.txt
   ```

7. **Modificar tu .env:**
   
   Para Linux / WSL / Mac
    ```bash
   nano .env
   ```
   Para Windows
    ```bash
   notepad .env
   ```
   - Y poner los siquientes datos de prueba:
       ```bash
      STRIPE_PUBLISHABLE_KEY= PUBLISH_KEY
      STRIPE_SECRET_KEY= SECRET_KEY 
      SENDGRID_API_KEY=API_KEY
      EMAIL_FROM=EMAIL
      ```
       *Estos datos se deben solicitar al equipo*

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
