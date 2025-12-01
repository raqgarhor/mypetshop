# Guía de Instalación

Este documento explica de forma clara los pasos necesarios para ejecutar el proyecto en entorno local con todas sus funcionalidades operativas.

## 🚀 Requisitos Previos
- Tener **Git** instalado
- Tener **Python 3.10** o superior
- Tener **7zip**

## 📥 Instalación
1. **Clona el repositorio o descomprime el archivo:**
   - Para clonar:
   ```bash
   git clone https://github.com/raqgarhor/mypetshop.git
   ```

3. **Entra en la carpeta del proyecto:**
   ```bash
   cd mypetshop
   ```

4. **Crear el entorno virtual Python:**
   ```bash
   python -m venv .venv
   ```

5. **Activar el entorno virtual Python:**
   ```bash
   .\.venv\Scripts\activate
   ```

6. **Instalar Django:**
   ```bash
   python -m pip install Django
   ```

7. **Instalar requisitos de requirements.txt:**
   ```bash
   cd tienda_virtual
   ```

   ```bash
   pip install -r requirements.txt
   ```

8. **Modificar tu .env:**
   - Descarga el env.zip [aquí](https://www.dropbox.com/scl/fi/ar51a5pzjju63ajfvuws8/.env.zip?rlkey=2t6xxhjbo8zxz5e61m9j7bqrt&st=tooi0v7z&dl=0)
   - Descomprime con 7zip y pon la contraseña *mypetshop*
   - agrega el archivo .env a la carpeta *tienda_virtual* del proyecto


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
