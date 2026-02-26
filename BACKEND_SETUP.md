# Configuración del backend en otra laptop

## Requisitos previos

- **Python 3.10, 3.11, 3.12 o 3.13** (recomendado 3.11 o 3.12)
- **PostgreSQL** instalado y un usuario/BD creados
- **Redis** instalado y en ejecución (para cache y sesiones)

## Pasos

### 1. Entorno virtual e instalar dependencias

```bash
cd system_lotification-main   # carpeta donde está manage.py
python -m venv env
# Windows:
env\Scripts\activate
# Linux/Mac:
# source env/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Variables de entorno

Crea un archivo `.env` en la misma carpeta que `manage.py` (no lo subas a Git). Ejemplo con valores por defecto del proyecto:

```env
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=lotificadora_bd
DB_USER=lotificadora_user
DB_PASSWORD=lotificadorapass
DB_HOST=127.0.0.1
DB_PORT=5432
REDIS_URL=redis://localhost:6379/0
CORS_ALLOW_ALL_ORIGINS=True
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173
```

Crea la base de datos en PostgreSQL antes de migrar:

```sql
CREATE USER lotificadora_user WITH PASSWORD 'lotificadorapass';
CREATE DATABASE lotificadora_bd OWNER lotificadora_user;
```

### 3. Migraciones y servidor

```bash
python manage.py migrate
python manage.py runserver
```

El backend quedará en `http://127.0.0.1:8000/`.

### 4. (Opcional) Usuario admin

```bash
python manage.py createsuperuser
```

## Comprobación de versiones

- **Django 5.2.5** y **djangorestframework 3.16.1** son compatibles.
- **djangorestframework-simplejwt 5.5.1** funciona con Django 5.x.
- Si en la nueva laptop usas otra versión de Python, las versiones del `requirements.txt` están fijadas para evitar conflictos al hacer `pip install -r requirements.txt`.

## Si algo falla

- **Error con psycopg2 en Windows:** asegúrate de tener Python y PostgreSQL de 32 o 64 bits coherentes; si sigue fallando, prueba `pip install psycopg2-binary` de nuevo en el venv.
- **Redis no conecta:** revisa que Redis esté instalado y que `REDIS_URL` en `.env` sea correcta; sin Redis, sesiones y cache fallarán.
- **ImportError de algún paquete:** desde el venv activado, ejecuta de nuevo `pip install -r requirements.txt`.
