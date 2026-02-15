# 🏠 Endpoints del Módulo de Lotes

## 📍 **URL Base**
```
http://localhost:8000/api/lotes/
```

## 🔐 **Autenticación**
Todos los endpoints requieren autenticación JWT. Incluye el token en el header:
```
Authorization: Bearer <tu_token_jwt>
```

---

## 🏘️ **MANZANAS**

### **GET** `/api/lotes/manzanas/`
**Obtener todas las manzanas**
- **Query Params:**
  - `nombre` (opcional): Filtrar por nombre de manzana
- **Respuesta:** Lista de manzanas activas
- **Ejemplo:** `GET /api/lotes/manzanas/?nombre=A`

### **GET** `/api/lotes/manzanas/{id}/`
**Obtener una manzana específica**
- **Respuesta:** Detalles de la manzana

### **POST** `/api/lotes/manzanas/`
**Crear una nueva manzana**
- **Body:**
```json
{
    "nombre": "A",
    "descripcion": "Manzana A - Zona Premium",
    "activo": true
}
```

### **PUT** `/api/lotes/manzanas/{id}/`
**Actualizar una manzana**
- **Body:** Mismos campos que POST

### **DELETE** `/api/lotes/manzanas/{id}/`
**Eliminar una manzana (desactivar)**

### **GET** `/api/lotes/manzanas/{id}/lotes/`
**Obtener lotes de una manzana específica**
- **Respuesta:** Lista de lotes de esa manzana

---

## 🏠 **LOTES**

### **GET** `/api/lotes/lotes/`
**Obtener todos los lotes**
- **Query Params:**
  - `manzana` (opcional): Filtrar por nombre de manzana
  - `estado` (opcional): Filtrar por estado (disponible, reservado, vendido, en_proceso, cancelado)
  - `precio_min` (opcional): Precio mínimo
  - `precio_max` (opcional): Precio máximo
  - `metros_min` (opcional): Metros cuadrados mínimos
  - `metros_max` (opcional): Metros cuadrados máximos
  - `solo_disponibles` (opcional): Solo lotes disponibles
- **Ejemplos:**
  - `GET /api/lotes/lotes/?estado=disponible`
  - `GET /api/lotes/lotes/?precio_min=50000&precio_max=100000`
  - `GET /api/lotes/lotes/?manzana=A&solo_disponibles=true`

### **GET** `/api/lotes/lotes/{id}/`
**Obtener un lote específico**
- **Respuesta:** Detalles completos del lote

### **POST** `/api/lotes/lotes/`
**Crear un nuevo lote**
- **Body:**
```json
{
    "manzana": 1,
    "numero_lote": "001",
    "metros_cuadrados": "150.00",
    "valor_total": "75000.00",
    "enganche": "15000.00",
    "costo_instalacion": "5000.00",
    "plazo_meses": 60,
    "cuota_mensual": "1200.00",
    "estado": "disponible"
}
```

### **PUT** `/api/lotes/lotes/{id}/`
**Actualizar un lote**
- **Body:** Mismos campos que POST

### **DELETE** `/api/lotes/lotes/{id}/`
**Eliminar un lote (desactivar)**

### **GET** `/api/lotes/lotes/disponibles/`
**Obtener solo lotes disponibles**
- **Respuesta:** Lista de lotes con estado "disponible"

### **GET** `/api/lotes/lotes/estadisticas/`
**Obtener estadísticas de lotes**
- **Respuesta:**
```json
{
    "total_lotes": 50,
    "lotes_disponibles": 30,
    "lotes_reservados": 10,
    "lotes_vendidos": 8,
    "lotes_en_proceso": 2,
    "lotes_cancelados": 0,
    "valor_total_inventario": "2250000.00",
    "valor_total_vendido": "600000.00",
    "promedio_metros_cuadrados": "180.50",
    "promedio_valor_lote": "75000.00"
}
```

### **GET** `/api/lotes/lotes/{id}/historial/`
**Obtener historial de un lote**
- **Respuesta:** Lista de cambios de estado del lote

### **POST** `/api/lotes/lotes/{id}/cambiar_estado/`
**Cambiar estado de un lote**
- **Body:**
```json
{
    "estado": "reservado",
    "notas": "Cliente interesado en reservar"
}
```

---

## 📊 **HISTORIAL**

### **GET** `/api/lotes/historial/`
**Obtener historial de cambios de estado**
- **Query Params:**
  - `lote_id` (opcional): Filtrar por ID de lote
  - `estado` (opcional): Filtrar por estado
  - `fecha_desde` (opcional): Fecha desde (YYYY-MM-DD)
  - `fecha_hasta` (opcional): Fecha hasta (YYYY-MM-DD)
- **Ejemplos:**
  - `GET /api/lotes/historial/?lote_id=1`
  - `GET /api/lotes/historial/?estado=vendido&fecha_desde=2024-01-01`

### **GET** `/api/lotes/historial/{id}/`
**Obtener un registro específico del historial**

---

## 🔍 **FILTROS Y CONSULTAS**

### **GET** `/api/lotes/lotes-disponibles-count/`
**Obtener conteo de lotes disponibles**
- **Respuesta:**
```json
{
    "lotes_disponibles": 30
}
```

### **POST** `/api/lotes/filtrar-lotes/`
**Filtrar lotes con múltiples criterios**
- **Body:**
```json
{
    "manzana": "A",
    "estado": "disponible",
    "precio_min": "50000.00",
    "precio_max": "100000.00",
    "metros_min": "100.00",
    "metros_max": "200.00",
    "solo_disponibles": true
}
```

---

## 📋 **ESTADOS DE LOTE**

Los lotes pueden tener los siguientes estados:
- `disponible` - Lote disponible para venta
- `reservado` - Lote reservado por un cliente
- `vendido` - Lote vendido
- `en_proceso` - Lote en proceso de venta
- `cancelado` - Lote cancelado

---

## 💰 **FORMATO DE MONEDA**

Todos los valores monetarios se manejan en **Quetzales (Q)** y se envían como strings con formato decimal:
- `"75000.00"` - 75,000 quetzales
- `"15000.00"` - 15,000 quetzales

---

## 📏 **FORMATO DE MEDIDAS**

Las medidas se manejan en **metros cuadrados (m²)**:
- `"150.00"` - 150 metros cuadrados
- `"200.50"` - 200.5 metros cuadrados

---

## 🔧 **EJEMPLOS DE USO EN FRONTEND**

### **React/Angular/Vue - Obtener Lotes Disponibles**
```javascript
// Obtener lotes disponibles
const response = await fetch('/api/lotes/lotes/disponibles/', {
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    }
});
const lotes = await response.json();
```

### **Filtrar Lotes por Precio**
```javascript
// Filtrar lotes entre 50,000 y 100,000 quetzales
const response = await fetch('/api/lotes/lotes/?precio_min=50000&precio_max=100000', {
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    }
});
const lotes = await response.json();
```

### **Cambiar Estado de un Lote**
```javascript
// Reservar un lote
const response = await fetch('/api/lotes/lotes/1/cambiar_estado/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        estado: 'reservado',
        notas: 'Cliente interesado en reservar'
    })
});
const lote = await response.json();
```

### **Obtener Estadísticas**
```javascript
// Obtener estadísticas generales
const response = await fetch('/api/lotes/lotes/estadisticas/', {
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    }
});
const stats = await response.json();
```

---

## 🚨 **CÓDIGOS DE RESPUESTA**

- `200` - OK - Operación exitosa
- `201` - Created - Recurso creado exitosamente
- `400` - Bad Request - Datos inválidos
- `401` - Unauthorized - No autenticado
- `403` - Forbidden - Sin permisos
- `404` - Not Found - Recurso no encontrado
- `500` - Internal Server Error - Error del servidor

---

## 📝 **NOTAS IMPORTANTES**

1. **Autenticación:** Todos los endpoints requieren token JWT válido
2. **Filtros:** Los filtros son opcionales y se pueden combinar
3. **Paginación:** Los endpoints de lista no tienen paginación por defecto
4. **Validación:** Los datos se validan automáticamente antes de guardar
5. **Historial:** Los cambios de estado se registran automáticamente
6. **Formato:** Usar formato decimal para valores monetarios y medidas
