#!/usr/bin/env python
"""
Configuraciones CORS para diferentes entornos
"""

# Configuración CORS para DESARROLLO (permitir cualquier origen)
CORS_DEVELOPMENT = {
    'CORS_ALLOW_ALL_ORIGINS': True,
    'CORS_ALLOW_CREDENTIALS': True,
    'CORS_ALLOW_HEADERS': [
        'accept',
        'accept-encoding',
        'authorization',
        'content-type',
        'dnt',
        'origin',
        'user-agent',
        'x-csrftoken',
        'x-requested-with',
        'x-forwarded-for',
        'x-forwarded-proto',
    ],
    'CORS_ALLOW_METHODS': [
        'DELETE',
        'GET',
        'OPTIONS',
        'PATCH',
        'POST',
        'PUT',
    ],
    'CORS_EXPOSE_HEADERS': [
        'content-type',
        'content-disposition',
    ],
    'CORS_ALLOWED_ORIGINS': [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5173",  # Vite
        "http://127.0.0.1:5173",  # Vite
        "http://localhost:4200",  # Angular
        "http://127.0.0.1:4200",  # Angular
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:5174",  # Vite con puerto alternativo
        "http://127.0.0.1:5174",
    ],
}

# Configuración CORS para PRODUCCIÓN (orígenes específicos)
CORS_PRODUCTION = {
    'CORS_ALLOW_ALL_ORIGINS': False,
    'CORS_ALLOW_CREDENTIALS': True,
    'CORS_ALLOWED_ORIGINS': [
        "https://tu-dominio.com",
        "https://www.tu-dominio.com",
    ],
    'CORS_ALLOW_HEADERS': [
        'accept',
        'accept-encoding',
        'authorization',
        'content-type',
        'origin',
        'user-agent',
    ],
    'CORS_ALLOW_METHODS': [
        'DELETE',
        'GET',
        'OPTIONS',
        'PATCH',
        'POST',
        'PUT',
    ],
}

def get_cors_config(environment='development'):
    """
    Obtener configuración CORS según el entorno
    
    Args:
        environment (str): 'development' o 'production'
    
    Returns:
        dict: Configuración CORS
    """
    if environment == 'production':
        return CORS_PRODUCTION
    else:
        return CORS_DEVELOPMENT

# Ejemplo de uso:
if __name__ == "__main__":
    print("🔧 Configuraciones CORS disponibles:")
    print("\n📋 Desarrollo (permitir cualquier origen):")
    dev_config = get_cors_config('development')
    print(f"   CORS_ALLOW_ALL_ORIGINS: {dev_config['CORS_ALLOW_ALL_ORIGINS']}")
    print(f"   Orígenes permitidos: {len(dev_config['CORS_ALLOWED_ORIGINS'])}")
    
    print("\n📋 Producción (orígenes específicos):")
    prod_config = get_cors_config('production')
    print(f"   CORS_ALLOW_ALL_ORIGINS: {prod_config['CORS_ALLOW_ALL_ORIGINS']}")
    print(f"   Orígenes permitidos: {len(prod_config['CORS_ALLOWED_ORIGINS'])}")
