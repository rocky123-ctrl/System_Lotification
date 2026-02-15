# 🐳 Despliegue con Docker Hub - Sistema de Lotificación

## 📋 **Configuración Rápida (Producción)**

### **🎯 Ventajas de usar Docker Hub:**
- ✅ **Despliegue ultra-rápido** (no compilación)
- ✅ **Imagen optimizada** y probada
- ✅ **Consistencia** entre entornos
- ✅ **Escalabilidad** fácil

## 🚀 **Despliegue Automático**

### **Windows (PowerShell):**
```powershell
# Ejecutar script de despliegue
.\deploy-prod.ps1
```

### **Linux/Mac (Bash):**
```bash
# Dar permisos de ejecución
chmod +x deploy-prod.sh

# Ejecutar script de despliegue
./deploy-prod.sh
```

### **Manual:**
```bash
# 1. Parar contenedores existentes
docker-compose -f docker-compose.prod.yml down

# 2. Desplegar con imagen de Docker Hub
docker-compose -f docker-compose.prod.yml up -d

# 3. Verificar estado
docker-compose -f docker-compose.prod.yml ps
```

## 📦 **Imagen de Docker Hub**

### **Detalles de la Imagen:**
- **Repositorio**: `josedaniel001/system_lotificacion-web`
- **Tag**: `latest`
- **Base**: Python 3.11-slim
- **Tamaño**: Optimizada (~500MB)

### **Contenido de la Imagen:**
- ✅ Django 5.2.5
- ✅ Todas las dependencias Python
- ✅ Fonts para PDFs
- ✅ Configuración de seguridad
- ✅ Usuario no-root (django)

## 🔧 **Configuración**

### **1. Variables de Entorno (.env):**
```bash
# Copiar archivo de ejemplo
cp env.example .env

# Editar con tus credenciales
nano .env
```

### **2. Configuración Mínima:**
```bash
# Base de datos (PostgreSQL local)
DB_NAME=system_lotificacion
DB_USER=postgres
DB_PASSWORD=tu_password_aqui
DB_HOST=host.docker.internal
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# Django
DEBUG=False
SECRET_KEY=tu_secret_key_aqui
ALLOWED_HOSTS=localhost,127.0.0.1,tu_dominio.com
```

## 🌐 **Acceso a la Aplicación**

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Django Admin** | http://localhost/admin | Panel de administración |
| **API** | http://localhost/api/ | Endpoints de la API |
| **Django Directo** | http://localhost:8000 | Servidor Django directo |

### **👤 Credenciales de Superuser:**
- **Usuario**: `admin`
- **Contraseña**: `admin123`

## 📝 **Comandos Útiles**

### **Gestión de Contenedores:**
```bash
# Ver estado
docker-compose -f docker-compose.prod.yml ps

# Ver logs
docker-compose -f docker-compose.prod.yml logs -f

# Ver logs específicos
docker-compose -f docker-compose.prod.yml logs web
docker-compose -f docker-compose.prod.yml logs nginx
docker-compose -f docker-compose.prod.yml logs redis

# Parar servicios
docker-compose -f docker-compose.prod.yml down

# Reiniciar servicios
docker-compose -f docker-compose.prod.yml restart

# Recrear contenedores
docker-compose -f docker-compose.prod.yml up -d --force-recreate
```

### **Ejecutar Comandos en Django:**
```bash
# Shell de Django
docker-compose -f docker-compose.prod.yml exec web python manage.py shell

# Crear superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Migraciones
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Recolectar estáticos
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic
```

## 🔍 **Troubleshooting**

### **Error de Conexión a Base de Datos:**
```bash
# Verificar que PostgreSQL esté corriendo
sudo systemctl status postgresql

# Verificar credenciales en .env
# Asegúrate de que DB_HOST=host.docker.internal
```

### **Error de Redis:**
```bash
# Verificar que Redis esté corriendo
docker-compose -f docker-compose.prod.yml logs redis

# Reiniciar Redis
docker-compose -f docker-compose.prod.yml restart redis
```

### **Error de Permisos:**
```bash
# Verificar permisos de archivos
ls -la

# Corregir permisos si es necesario
chmod 644 .env
chmod +x deploy-prod.sh
```

### **Limpiar Docker:**
```bash
# Limpiar contenedores no usados
docker container prune

# Limpiar imágenes no usadas
docker image prune

# Limpiar volúmenes no usados
docker volume prune

# Limpiar todo
docker system prune -a
```

## 📊 **Monitoreo**

### **Uso de Recursos:**
```bash
# Ver uso de recursos
docker stats

# Ver información detallada
docker-compose -f docker-compose.prod.yml top
```

### **Logs en Tiempo Real:**
```bash
# Todos los servicios
docker-compose -f docker-compose.prod.yml logs -f

# Solo Django
docker-compose -f docker-compose.prod.yml logs -f web

# Solo Nginx
docker-compose -f docker-compose.prod.yml logs -f nginx
```

## 🚀 **Actualización de Imagen**

### **Actualizar a Nueva Versión:**
```bash
# Parar servicios
docker-compose -f docker-compose.prod.yml down

# Eliminar imagen local
docker rmi josedaniel001/system_lotificacion-web:latest

# Desplegar con nueva imagen
docker-compose -f docker-compose.prod.yml up -d
```

### **Forzar Descarga de Nueva Imagen:**
```bash
# Desplegar forzando nueva imagen
docker-compose -f docker-compose.prod.yml up -d --pull always
```

## 🎉 **¡Listo para Producción!**

Tu aplicación está ahora desplegada usando la imagen optimizada de Docker Hub. El despliegue es rápido, confiable y fácil de mantener.

**¡Disfruta de tu sistema de lotificación en producción!** 🚀

