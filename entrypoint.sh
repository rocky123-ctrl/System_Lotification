#!/bin/bash

# Función para verificar si las migraciones ya se han ejecutado
check_migrations() {
    python manage.py showmigrations --list | grep -q "\[X\]"
    return $?
}

# Función para verificar si existe superuser
check_superuser() {
    python manage.py shell -c "from django.contrib.auth.models import User; exit(0 if User.objects.filter(is_superuser=True).exists() else 1)"
    return $?
}

echo "🚀 Iniciando aplicación Django..."

# Ejecutar migraciones solo si no se han ejecutado
if ! check_migrations; then
    echo "📦 Ejecutando migraciones..."
    python manage.py makemigrations
    python manage.py migrate
    echo "✅ Migraciones completadas"
else
    echo "📋 Migraciones ya ejecutadas, omitiendo..."
fi

# Crear superuser solo si no existe
if ! check_superuser; then
    echo "👤 Creando superuser..."
    python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser creado: admin/admin123')
else:
    print('Superuser ya existe')
"
else
    echo "👤 Superuser ya existe, omitiendo..."
fi

# Recolectar archivos estáticos
echo "📁 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

# Iniciar servidor
echo "🌐 Iniciando servidor Django..."
python manage.py runserver 0.0.0.0:8000
