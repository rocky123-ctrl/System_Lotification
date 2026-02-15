# ⚙️ Endpoints del Módulo de Configuración

## 📍 **URL Base**
```
http://localhost:8000/api/configuracion/
```

## 🔐 **Autenticación**
La mayoría de endpoints requieren autenticación JWT. Incluye el token en el header:
```
Authorization: Bearer <tu_token_jwt>
```

**Nota:** El endpoint `/api/configuracion/publica/` es público y no requiere autenticación.

---

## 🏢 **CONFIGURACIÓN GENERAL**

### **GET** `/api/configuracion/general/`
**Obtener todas las configuraciones generales**
- **Respuesta:** Lista de todas las configuraciones
- **Autenticación:** ✅ Requerida

### **GET** `/api/configuracion/general/{id}/`
**Obtener una configuración específica**
- **Respuesta:** Detalles completos de la configuración
- **Autenticación:** ✅ Requerida

### **POST** `/api/configuracion/general/`
**Crear una nueva configuración**
- **Body:**
```json
{
    "nombre_lotificacion": "Lotificación San Carlos",
    "ubicacion": "Villa Nueva, Guatemala",
    "descripcion": "Proyecto residencial con lotes de alta calidad",
    "direccion_completa": "Km 25 Carretera a El Salvador, Guatemala",
    "telefono": "+502 2234-5678",
    "email": "info@lotificacionsancarlos.com",
    "sitio_web": "www.lotificacionsancarlos.com",
    "fecha_inicio": "2024-01-15",
    "total_lotes": 96,
    "area_total": "15000.00",
    "tasa_anual": "12.00",
    "activo": true
}
```

### **PUT** `/api/configuracion/general/{id}/`
**Actualizar una configuración**
- **Body:** Mismos campos que POST
- **Autenticación:** ✅ Requerida

### **DELETE** `/api/configuracion/general/{id}/`
**Eliminar una configuración**
- **Autenticación:** ✅ Requerida

### **GET** `/api/configuracion/general/activa/`
**Obtener la configuración activa**
- **Respuesta:** Configuración actualmente activa
- **Autenticación:** ✅ Requerida

### **GET** `/api/configuracion/general/public/`
**Obtener información pública de la configuración**
- **Respuesta:** Información básica para mostrar al público
- **Autenticación:** ✅ Requerida
- **Ejemplo de respuesta:**
```json
{
    "nombre_lotificacion": "Lotificación San Carlos",
    "ubicacion": "Villa Nueva, Guatemala",
    "descripcion": "Proyecto residencial con lotes de alta calidad",
    "telefono": "+502 2234-5678",
    "email": "info@lotificacionsancarlos.com",
    "sitio_web": "www.lotificacionsancarlos.com"
}
```

### **GET** `/api/configuracion/general/completa/`
**Obtener configuración completa con datos financieros**
- **Respuesta:** Configuración completa incluyendo datos financieros
- **Autenticación:** ✅ Requerida

### **GET** `/api/configuracion/general/resumen/`
**Obtener resumen de configuración con estadísticas**
- **Respuesta:** Resumen con estadísticas de lotes
- **Autenticación:** ✅ Requerida
- **Ejemplo de respuesta:**
```json
{
    "nombre_lotificacion": "Lotificación San Carlos",
    "ubicacion": "Villa Nueva, Guatemala",
    "total_lotes_configurado": 96,
    "total_lotes_reales": 97,
    "lotes_disponibles": 30,
    "lotes_reservados": 15,
    "lotes_en_proceso": 5,
    "lotes_financiados": 3,
    "lotes_vendidos": 8,
    "lotes_cancelados": 2,
    "tasa_anual": "12.00",
    "tasa_anual_formateada": "12.00%",
    "valor_total_inventario": "2250000.00",
    "valor_total_reservados": "1125000.00",
    "valor_total_en_proceso": "375000.00",
    "valor_total_financiados": "225000.00",
    "valor_total_vendido": "600000.00",
    "fecha_ultima_actualizacion": "2024-01-15T10:30:00Z"
}
```

### **GET** `/api/configuracion/general/estadisticas/`
**Obtener estadísticas de configuración**
- **Respuesta:** Estadísticas del sistema de configuración
- **Autenticación:** ✅ Requerida
- **Ejemplo de respuesta:**
```json
{
    "total_configuraciones": 1,
    "configuracion_activa": true,
    "fecha_creacion_configuracion": "2024-01-15T10:30:00Z",
    "fecha_ultima_actualizacion": "2024-01-15T10:30:00Z",
    "tiene_logo": true,
    "tiene_configuracion_financiera": true
}
```

### **POST** `/api/configuracion/general/{id}/activar/`
**Activar una configuración específica**
- **Descripción:** Activa la configuración y desactiva las demás
- **Autenticación:** ✅ Requerida

### **POST** `/api/configuracion/general/{id}/subir_logo/`
**Subir logo para una configuración**
- **Body:** FormData con archivo de imagen
- **Autenticación:** ✅ Requerida
- **Ejemplo:**
```javascript
const formData = new FormData();
formData.append('logo', fileInput.files[0]);

const response = await fetch('/api/configuracion/general/1/subir_logo/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`
    },
    body: formData
});
```

---

## 💰 **CONFIGURACIÓN FINANCIERA**

### **GET** `/api/configuracion/financiera/`
**Obtener todas las configuraciones financieras**
- **Respuesta:** Lista de configuraciones financieras
- **Autenticación:** ✅ Requerida

### **GET** `/api/configuracion/financiera/{id}/`
**Obtener una configuración financiera específica**
- **Respuesta:** Detalles de la configuración financiera
- **Autenticación:** ✅ Requerida

### **POST** `/api/configuracion/financiera/`
**Crear una nueva configuración financiera**
- **Body:**
```json
{
    "plazo_minimo_meses": 12,
    "plazo_maximo_meses": 60,
    "enganche_minimo_porcentaje": "20.00",
    "enganche_maximo_porcentaje": "50.00",
    "costo_instalacion_default": "5000.00",
    "permitir_pagos_anticipados": true,
    "aplicar_penalizacion_atrasos": true,
    "penalizacion_atraso_porcentaje": "5.00"
}
```

### **PUT** `/api/configuracion/financiera/{id}/`
**Actualizar una configuración financiera**
- **Body:** Mismos campos que POST
- **Autenticación:** ✅ Requerida

### **DELETE** `/api/configuracion/financiera/{id}/`
**Eliminar una configuración financiera**
- **Autenticación:** ✅ Requerida

### **GET** `/api/configuracion/financiera/activa/`
**Obtener configuración financiera activa**
- **Respuesta:** Configuración financiera de la configuración general activa
- **Autenticación:** ✅ Requerida

### **POST** `/api/configuracion/financiera/crear_para_activa/`
**Crear configuración financiera para la configuración activa**
- **Body:** Mismos campos que POST de configuración financiera
- **Autenticación:** ✅ Requerida
- **Descripción:** Crea configuración financiera para la configuración general activa

---

## 🌐 **ENDPOINTS PÚBLICOS**

### **GET** `/api/configuracion/publica/`
**Obtener información pública de la lotificación**
- **Respuesta:** Información básica para mostrar al público
- **Autenticación:** ❌ No requerida
- **Ejemplo de respuesta:**
```json
{
    "nombre_lotificacion": "Lotificación San Carlos",
    "ubicacion": "Villa Nueva, Guatemala",
    "descripcion": "Proyecto residencial con lotes de alta calidad",
    "telefono": "+502 2234-5678",
    "email": "info@lotificacionsancarlos.com",
    "sitio_web": "www.lotificacionsancarlos.com"
}
```

---

## 🔧 **ENDPOINTS DE UTILIDAD**

### **POST** `/api/configuracion/inicializar/`
**Inicializar configuración por defecto**
- **Descripción:** Crea configuración general y financiera por defecto
- **Autenticación:** ✅ Requerida
- **Respuesta:** Configuración completa inicializada

---

## 📋 **CAMPOS DE CONFIGURACIÓN GENERAL**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `nombre_lotificacion` | String | Nombre de la lotificación |
| `ubicacion` | String | Ubicación general |
| `descripcion` | Text | Descripción del proyecto |
| `direccion_completa` | Text | Dirección completa |
| `telefono` | String | Teléfono de contacto |
| `email` | Email | Email de contacto |
| `sitio_web` | URL | Sitio web |
| `fecha_inicio` | Date | Fecha de inicio del proyecto |
| `total_lotes` | Integer | Total de lotes del proyecto |
| `area_total` | Decimal | Área total en m² |
| `tasa_anual` | Decimal | Tasa de interés anual (%) |
| `tasa_mensual` | Decimal | Tasa mensual (calculada automáticamente) |
| `logo` | Image | Logo de la empresa |
| `activo` | Boolean | Si la configuración está activa |

---

## 💰 **CAMPOS DE CONFIGURACIÓN FINANCIERA**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `plazo_minimo_meses` | Integer | Plazo mínimo de financiamiento |
| `plazo_maximo_meses` | Integer | Plazo máximo de financiamiento |
| `enganche_minimo_porcentaje` | Decimal | Porcentaje mínimo de enganche |
| `enganche_maximo_porcentaje` | Decimal | Porcentaje máximo de enganche |
| `costo_instalacion_default` | Decimal | Costo de instalación por defecto |
| `permitir_pagos_anticipados` | Boolean | Si permite pagos anticipados |
| `aplicar_penalizacion_atrasos` | Boolean | Si aplica penalización por atrasos |
| `penalizacion_atraso_porcentaje` | Decimal | Porcentaje de penalización por atraso |

---

## 🔧 **EJEMPLOS DE USO EN FRONTEND**

### **Obtener Configuración Activa**
```javascript
// Obtener configuración activa
const response = await fetch('/api/configuracion/general/activa/', {
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    }
});
const config = await response.json();
```

### **Obtener Información Pública (sin autenticación)**
```javascript
// Obtener información pública
const response = await fetch('/api/configuracion/publica/');
const publicInfo = await response.json();
```

### **Crear Nueva Configuración**
```javascript
// Crear nueva configuración
const response = await fetch('/api/configuracion/general/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        nombre_lotificacion: "Lotificación San Carlos",
        ubicacion: "Villa Nueva, Guatemala",
        descripcion: "Proyecto residencial con lotes de alta calidad",
        telefono: "+502 2234-5678",
        email: "info@lotificacionsancarlos.com",
        fecha_inicio: "2024-01-15",
        total_lotes: 96,
        area_total: "15000.00",
        tasa_anual: "12.00",
        activo: true
    })
});
const nuevaConfig = await response.json();
```

### **Activar Configuración**
```javascript
// Activar una configuración específica
const response = await fetch('/api/configuracion/general/1/activar/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    }
});
const configActivada = await response.json();
```

### **Subir Logo**
```javascript
// Subir logo
const formData = new FormData();
formData.append('logo', fileInput.files[0]);

const response = await fetch('/api/configuracion/general/1/subir_logo/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`
    },
    body: formData
});
const configConLogo = await response.json();
```

### **Obtener Resumen con Estadísticas**
```javascript
// Obtener resumen con estadísticas
const response = await fetch('/api/configuracion/general/resumen/', {
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    }
});
const resumen = await response.json();
```

### **Crear Configuración Financiera**
```javascript
// Crear configuración financiera para la configuración activa
const response = await fetch('/api/configuracion/financiera/crear_para_activa/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        plazo_minimo_meses: 12,
        plazo_maximo_meses: 60,
        enganche_minimo_porcentaje: "20.00",
        enganche_maximo_porcentaje: "50.00",
        costo_instalacion_default: "5000.00",
        permitir_pagos_anticipados: true,
        aplicar_penalizacion_atrasos: true,
        penalizacion_atraso_porcentaje: "5.00"
    })
});
const configFinanciera = await response.json();
```

### **Inicializar Configuración por Defecto**
```javascript
// Inicializar configuración por defecto
const response = await fetch('/api/configuracion/inicializar/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    }
});
const configInicializada = await response.json();
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

1. **Configuración Única:** Solo puede haber una configuración activa a la vez
2. **Tasa Mensual:** Se calcula automáticamente basada en la tasa anual
3. **Logo:** Se almacena en `media/configuracion/logos/`
4. **Configuración Financiera:** Se relaciona con la configuración general activa
5. **Endpoint Público:** `/publica/` no requiere autenticación
6. **Inicialización:** El endpoint `/inicializar/` crea configuración por defecto
7. **Activación:** Al activar una configuración, se desactivan las demás automáticamente

---

## 🔄 **FLUJO DE CONFIGURACIÓN RECOMENDADO**

1. **Inicializar:** Usar `/inicializar/` para crear configuración por defecto
2. **Personalizar:** Actualizar la configuración con datos específicos
3. **Subir Logo:** Usar `/subir_logo/` para agregar el logo
4. **Configurar Financiero:** Crear configuración financiera si es necesario
5. **Activar:** Asegurar que la configuración esté activa
6. **Usar:** Consumir `/activa/` o `/publica/` según el contexto
