# 🐳 Docker Setup - Sistema de Lotificación

## 📋 **Configuración Rápida**

### **1. Preparar Variables de Entorno**
```bash
# Copiar archivo de ejemplo
cp env.example .env

# Editar con tus credenciales de PostgreSQL local
nano .env
```

### **2. Configurar PostgreSQL Local**
Asegúrate de que PostgreSQL esté corriendo en tu máquina local y que las credenciales en `.env` sean correctas.

### **3. Levantar Servicios**
```bash
# Construir y levantar todos los servicios
docker-compose up --build

# O en modo detached
docker-compose up -d --build
```

## 🚀 **Servicios Incluidos**

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| **Django** | 8000 | API y Admin |
| **Nginx** | 80 | Proxy reverso y archivos estáticos |
| **Redis** | 6379 | Cache y sesiones |

## 🔧 **Características Automáticas**

### **✅ Migraciones Inteligentes**
- Se ejecutan solo si no se han corrido antes
- Incluye `makemigrations` y `migrate`

### **✅ Superuser Automático**
- Se crea automáticamente si no existe
- Credenciales: `admin/admin123`

### **✅ Archivos Estáticos**
- Se recolectan automáticamente
- Servidos por Nginx con cache

### **✅ Fonts para PDFs**
- Incluye fuentes necesarias para generación de PDFs
- Soporte completo para Pillow

## 🌐 **Acceso a la Aplicación**

- **Django Admin**: http://localhost/admin
- **API**: http://localhost/api/
- **Django Directo**: http://localhost:8000

## 📝 **Comandos Útiles**

```bash
# Ver logs
docker-compose logs -f

# Ejecutar comandos en Django
docker-compose exec web python manage.py shell

# Crear superuser manual
docker-compose exec web python manage.py createsuperuser

# Hacer migraciones manual
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate

# Recolectar estáticos
docker-compose exec web python manage.py collectstatic

# Parar servicios
docker-compose down

# Parar y eliminar volúmenes
docker-compose down -v
```

## 🔍 **Troubleshooting**

### **Error de Conexión a PostgreSQL**
```bash
# Verificar que PostgreSQL esté corriendo
sudo systemctl status postgresql

# Verificar credenciales en .env
# Asegúrate de que DB_HOST=host.docker.internal
```

### **Permisos de Archivos**
```bash
# Si hay problemas de permisos
sudo chown -R $USER:$USER .
```

### **Limpiar Docker**
```bash
# Limpiar imágenes no usadas
docker system prune -a

# Limpiar volúmenes
docker volume prune
```

## 🛡️ **Seguridad**

- **Rate Limiting**: API limitada a 10 requests/segundo
- **Security Headers**: Configurados en Nginx
- **Usuario no-root**: Django corre como usuario `django`
- **Variables de entorno**: Separadas del código

## 📊 **Monitoreo**

```bash
# Ver uso de recursos
docker stats

# Ver logs específicos
docker-compose logs web
docker-compose logs nginx
docker-compose logs redis
```

¡Tu aplicación Django está lista para correr con Docker! 🎉
