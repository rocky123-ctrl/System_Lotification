# 💰 Endpoints del Módulo de Financiamiento

## 📍 **URL Base**
```
http://localhost:8000/api/financiamiento/
```

## 🔐 **Autenticación**
Todos los endpoints requieren autenticación JWT. Incluye el token en el header:
```
Authorization: Bearer <tu_token_jwt>
```

---

## 🏦 **FINANCIAMIENTOS**

### **GET** `/api/financiamiento/financiamientos/`
**Obtener todos los financiamientos**
- **Query Params:**
  - `promitente` (opcional): Filtrar por nombre del promitente comprador
  - `estado` (opcional): Filtrar por estado (activo, finalizado, cancelado, en_mora)
  - `manzana` (opcional): Filtrar por nombre de manzana
  - `en_mora` (opcional): Solo financiamientos en mora (true/false)
- **Ejemplos:**
  - `GET /api/financiamiento/financiamientos/?estado=activo`
  - `GET /api/financiamiento/financiamientos/?promitente=Juan`
  - `GET /api/financiamiento/financiamientos/?en_mora=true`

### **GET** `/api/financiamiento/financiamientos/{id}/`
**Obtener un financiamiento específico**
- **Respuesta:** Detalles completos del financiamiento con cuotas y pagos

### **POST** `/api/financiamiento/financiamientos/`
**Crear un nuevo financiamiento**
- **Body:**
```json
{
    "lote_id": 1,
    "promitente_comprador": "Juan Pérez",
    "totalidad": "75000.00",
    "enganche": "15000.00",
    "plazo_meses": 60,
    "cuota_mensual": "1200.00",
    "fecha_inicio_financiamiento": "2024-01-15"
}
```
- **Notas:** 
  - **`cuota_mensual` se calcula automáticamente** usando la fórmula de amortización
  - Al crear un financiamiento, se generan automáticamente todas las cuotas
  - La `fecha_vencimiento` se calcula automáticamente como fecha_inicio + plazo_meses
  - El `saldo` se calcula automáticamente como totalidad - enganche
  - Las cuotas se calculan usando la **fórmula de amortización** con la tasa mensual de la configuración
  - Cada cuota tiene el mismo monto total, pero varía la proporción capital/interés
  - **La tasa de interés se obtiene de ConfiguracionGeneral.tasa_mensual**

### **PUT** `/api/financiamiento/financiamientos/{id}/`
**Actualizar un financiamiento**
- **Body:**
```json
{
    "promitente_comprador": "Juan Pérez Actualizado",
    "totalidad": "80000.00",
    "enganche": "16000.00",
    "plazo_meses": 60,
    "cuota_mensual": "1300.00",
    "fecha_inicio_financiamiento": "2024-01-15",
    "estado": "activo"
}
```

### **DELETE** `/api/financiamiento/financiamientos/{id}/`
**Eliminar un financiamiento**

### **GET** `/api/financiamiento/financiamientos/activos/`
**Obtener financiamientos activos**
- **Respuesta:** Solo financiamientos con estado "activo"

### **GET** `/api/financiamiento/financiamientos/en_mora/`
**Obtener financiamientos en mora**
- **Respuesta:** Solo financiamientos con estado "en_mora"

### **GET** `/api/financiamiento/financiamientos/finalizados/`
**Obtener financiamientos finalizados**
- **Respuesta:** Solo financiamientos con estado "finalizado"

### **GET** `/api/financiamiento/financiamientos/estadisticas/`
**Obtener estadísticas de financiamientos**
- **Respuesta:**
```json
{
    "total_financiamientos": 25,
    "financiamientos_activos": 20,
    "financiamientos_finalizados": 3,
    "financiamientos_en_mora": 2,
    "total_cobrado": "450000.00",
    "total_pendiente": "300000.00",
    "total_mora": "2500.00",
    "cuotas_atrasadas_total": 5
}
```

### **POST** `/api/financiamiento/financiamientos/{id}/calcular_moras/`
**Calcular moras para un financiamiento específico**
- **Body:** No requiere body
- **Descripción:** Calcula moras para todas las cuotas pendientes del financiamiento

### **GET** `/api/financiamiento/financiamientos/{id}/cuotas/`
**Obtener cuotas de un financiamiento**
- **Respuesta:** Lista de todas las cuotas del financiamiento

### **GET** `/api/financiamiento/financiamientos/{id}/pagos/`
**Obtener pagos de un financiamiento**
- **Respuesta:** Lista de todos los pagos del financiamiento

---

## 📋 **CUOTAS**

### **GET** `/api/financiamiento/cuotas/`
**Obtener todas las cuotas**
- **Query Params:**
  - `financiamiento_id` (opcional): Filtrar por ID de financiamiento
  - `estado` (opcional): Filtrar por estado (pendiente, pagada, atrasada, parcial)
  - `atrasadas` (opcional): Solo cuotas atrasadas (true/false)
- **Ejemplos:**
  - `GET /api/financiamiento/cuotas/?financiamiento_id=1`
  - `GET /api/financiamiento/cuotas/?estado=atrasada`
  - `GET /api/financiamiento/cuotas/?atrasadas=true`

### **GET** `/api/financiamiento/cuotas/{id}/`
**Obtener una cuota específica**
- **Respuesta:** Detalles completos de la cuota con pagos

### **POST** `/api/financiamiento/cuotas/`
**Crear una nueva cuota**
- **Body:**
```json
{
    "financiamiento_id": 1,
    "numero_cuota": 1,
    "monto_capital": "1000.00",
    "monto_interes": "200.00",
    "monto_total": "1200.00",
    "fecha_vencimiento": "2024-02-15"
}
```

### **PUT** `/api/financiamiento/cuotas/{id}/`
**Actualizar una cuota**
- **Body:**
```json
{
    "financiamiento_id": 1,
    "numero_cuota": 1,
    "monto_capital": "1000.00",
    "monto_interes": "200.00",
    "monto_total": "1200.00",
    "fecha_vencimiento": "2024-02-15",
    "estado": "pendiente"
}
```

### **DELETE** `/api/financiamiento/cuotas/{id}/`
**Eliminar una cuota**

### **GET** `/api/financiamiento/cuotas/atrasadas/`
**Obtener cuotas atrasadas**
- **Respuesta:** Solo cuotas con estado "atrasada"

### **GET** `/api/financiamiento/cuotas/pendientes/`
**Obtener cuotas pendientes**
- **Respuesta:** Solo cuotas con estado "pendiente"

### **POST** `/api/financiamiento/cuotas/{id}/calcular_mora/`
**Calcular mora para una cuota específica**
- **Body:** No requiere body
- **Descripción:** Calcula la mora de una cuota si está atrasada

### **GET** `/api/financiamiento/cuotas/{id}/pagos/`
**Obtener pagos de una cuota**
- **Respuesta:** Lista de pagos realizados para esa cuota

---

## 💳 **PAGOS**

### **GET** `/api/financiamiento/pagos/`
**Obtener todos los pagos**
- **Query Params:**
  - `financiamiento_id` (opcional): Filtrar por ID de financiamiento
  - `cuota_id` (opcional): Filtrar por ID de cuota
  - `fecha_desde` (opcional): Fecha desde (YYYY-MM-DD)
  - `fecha_hasta` (opcional): Fecha hasta (YYYY-MM-DD)
- **Ejemplos:**
  - `GET /api/financiamiento/pagos/?financiamiento_id=1`
  - `GET /api/financiamiento/pagos/?fecha_desde=2024-01-01&fecha_hasta=2024-01-31`

### **GET** `/api/financiamiento/pagos/{id}/`
**Obtener un pago específico**
- **Respuesta:** Detalles completos del pago

### **POST** `/api/financiamiento/pagos/`
**Registrar un nuevo pago**
- **Body:**
```json
{
    "cuota_id": 1,
    "financiamiento_id": 1,
    "monto_capital": "1000.00",
    "monto_interes": "200.00",
    "monto_mora": "50.00",
    "monto_total": "1250.00",
    "fecha_pago": "2024-01-15",
    "metodo_pago": "Efectivo",
    "observaciones": "Pago realizado en efectivo"
}
```
- **Notas:**
  - **`referencia_pago` se genera automáticamente** con formato: `REF-{numero:03d}-{lote_manzana}`
  - Ejemplo: `REF-001-A1`, `REF-002-B3`, `REF-015-C7`
  - El número se incrementa secuencialmente para todos los pagos del sistema
  - El lote_manzana se obtiene de la manzana y número del lote del financiamiento

### **POST** `/api/financiamiento/pagos/multiples_pagos/`
**Crear múltiples pagos en una sola petición**
- **Body:**
```json
{
    "pagos": [
        {
            "cuota_id": 1,
            "financiamiento_id": 1,
            "monto_capital": "1000.00",
            "monto_interes": "200.00",
            "monto_total": "1200.00",
            "fecha_pago": "2024-01-15",
            "metodo_pago": "Efectivo"
        },
        {
            "cuota_id": 2,
            "financiamiento_id": 1,
            "monto_capital": "1050.00",
            "monto_interes": "150.00",
            "monto_total": "1200.00",
            "fecha_pago": "2024-01-15",
            "metodo_pago": "Transferencia"
        }
    ]
}
```
- **Notas:**
  - Máximo 50 pagos por petición
  - Si hay errores en algún pago, se hace rollback de todos
  - Respuesta incluye detalles de cada pago procesado
  - **`referencia_pago` se genera automáticamente** para cada pago

### **POST** `/api/financiamiento/pagos/pagos_por_financiamiento/`
**Crear múltiples pagos para un financiamiento específico**
- **Body:**
```json
{
    "financiamiento_id": 1,
    "pagos": [
        {
            "cuota_id": 1,
            "monto_capital": "1000.00",
            "monto_interes": "200.00",
            "monto_total": "1200.00",
            "fecha_pago": "2024-01-15",
            "metodo_pago": "Efectivo"
        },
        {
            "cuota_id": 2,
            "monto_capital": "1050.00",
            "monto_interes": "150.00",
            "monto_total": "1200.00",
            "fecha_pago": "2024-01-15",
            "metodo_pago": "Transferencia"
        }
    ]
}
```
- **Notas:**
  - No es necesario especificar `financiamiento_id` en cada pago
  - Se valida que todos los pagos pertenezcan al mismo financiamiento
  - Máximo 50 pagos por petición

### **PUT** `/api/financiamiento/pagos/{id}/`
**Actualizar un pago**
- **Body:**
```json
{
    "cuota_id": 1,
    "financiamiento_id": 1,
    "monto_capital": "1000.00",
    "monto_interes": "200.00",
    "monto_mora": "50.00",
    "monto_total": "1250.00",
    "fecha_pago": "2024-01-15",
    "metodo_pago": "Transferencia",
    "referencia_pago": "REF-002",
    "observaciones": "Pago actualizado"
}
```

### **DELETE** `/api/financiamiento/pagos/{id}/`
**Eliminar un pago**

### **GET** `/api/financiamiento/pagos/por_fecha/`
**Obtener pagos por rango de fechas**
- **Query Params:**
  - `fecha_desde` (requerido): Fecha desde (YYYY-MM-DD)
  - `fecha_hasta` (requerido): Fecha hasta (YYYY-MM-DD)
- **Ejemplo:** `GET /api/financiamiento/pagos/por_fecha/?fecha_desde=2024-01-01&fecha_hasta=2024-01-31`

### **GET** `/api/financiamiento/pagos/resumen_mensual/`
**Obtener resumen de pagos del mes actual**
- **Respuesta:**
```json
{
    "mes": "January 2024",
    "total_pagos": 15,
    "total_cobrado": "18000.00",
    "total_capital": "15000.00",
    "total_interes": "2500.00",
    "total_mora": "500.00"
}
```

---

## ⚙️ **CONFIGURACIONES DE PAGO**

### **GET** `/api/financiamiento/configuraciones-pago/`
**Obtener todas las configuraciones de pago**
- **Respuesta:** Lista de configuraciones de pago

### **GET** `/api/financiamiento/configuraciones-pago/{id}/`
**Obtener una configuración específica**

### **POST** `/api/financiamiento/configuraciones-pago/`
**Crear una nueva configuración**
- **Body:**
```json
{
    "tipo_pago": "fin_mes",
    "dia_pago": 30,
    "descripcion": "Pago fin de mes",
    "activo": true
}
```

### **PUT** `/api/financiamiento/configuraciones-pago/{id}/`
**Actualizar una configuración**
- **Body:**
```json
{
    "tipo_pago": "quincena",
    "dia_pago": 15,
    "descripcion": "Pago quincenal",
    "activo": true
}
```

### **DELETE** `/api/financiamiento/configuraciones-pago/{id}/`
**Eliminar una configuración**

### **GET** `/api/financiamiento/configuraciones-pago/activas/`
**Obtener configuraciones activas**
- **Respuesta:** Solo configuraciones con activo=true

---

## 🔧 **ENDPOINTS DE UTILIDAD**

### **POST** `/api/financiamiento/calcular-moras-generales/`
**Calcular moras para todos los financiamientos**
- **Body:** No requiere body
- **Descripción:** Calcula moras para todas las cuotas pendientes del sistema
- **Respuesta:**
```json
{
    "mensaje": "Se calcularon moras para 50 cuotas",
    "financiamientos_actualizados": 3
}
```

### **GET** `/api/financiamiento/reporte-financiamiento/`
**Generar reporte de financiamiento**
- **Query Params:**
  - `fecha_desde` (opcional): Fecha desde (YYYY-MM-DD)
  - `fecha_hasta` (opcional): Fecha hasta (YYYY-MM-DD)
  - `manzana` (opcional): Filtrar por manzana
- **Ejemplo:** `GET /api/financiamiento/reporte-financiamiento/?fecha_desde=2024-01-01&fecha_hasta=2024-01-31&manzana=A`
- **Respuesta:**
```json
{
    "periodo": {
        "fecha_desde": "2024-01-01",
        "fecha_hasta": "2024-01-31"
    },
    "filtros": {
        "manzana": "A"
    },
    "estadisticas": {
        "total_financiamientos": 25,
        "total_cobrado": "450000.00",
        "total_pendiente": "300000.00",
        "cuotas_atrasadas": 5
    },
    "financiamientos": [...]
}
```

---

## 🔧 **EJEMPLOS DE USO EN FRONTEND**

### **Crear Financiamiento**
```javascript
const response = await fetch('/api/financiamiento/financiamientos/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        lote_id: 1,
        promitente_comprador: "Juan Pérez",
        totalidad: "75000.00",
        enganche: "15000.00",
        plazo_meses: 60,
        cuota_mensual: "1200.00",
        fecha_inicio_financiamiento: "2024-01-15"
    })
});
const financiamiento = await response.json();
```

### **Registrar Pago**
```javascript
const response = await fetch('/api/financiamiento/pagos/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        cuota_id: 1,
        financiamiento_id: 1,
        monto_capital: "1000.00",
        monto_interes: "200.00",
        monto_mora: "50.00",
        monto_total: "1250.00",
        fecha_pago: "2024-01-15",
        metodo_pago: "Efectivo",
        referencia_pago: "REF-001"
    })
});
const pago = await response.json();
```

### **Registrar Múltiples Pagos**
```javascript
const response = await fetch('/api/financiamiento/pagos/multiples_pagos/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        pagos: [
            {
                cuota_id: 1,
                financiamiento_id: 1,
                monto_capital: "1000.00",
                monto_interes: "200.00",
                monto_total: "1200.00",
                fecha_pago: "2024-01-15",
                metodo_pago: "Efectivo"
            },
            {
                cuota_id: 2,
                financiamiento_id: 1,
                monto_capital: "1050.00",
                monto_interes: "150.00",
                monto_total: "1200.00",
                fecha_pago: "2024-01-15",
                metodo_pago: "Transferencia"
            }
        ]
    })
});
const resultado = await response.json();
```

### **Registrar Múltiples Pagos por Financiamiento**
```javascript
const response = await fetch('/api/financiamiento/pagos/pagos_por_financiamiento/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        financiamiento_id: 1,
        pagos: [
            {
                cuota_id: 1,
                monto_capital: "1000.00",
                monto_interes: "200.00",
                monto_total: "1200.00",
                fecha_pago: "2024-01-15",
                metodo_pago: "Efectivo"
            },
            {
                cuota_id: 2,
                monto_capital: "1050.00",
                monto_interes: "150.00",
                monto_total: "1200.00",
                fecha_pago: "2024-01-15",
                metodo_pago: "Transferencia"
            }
        ]
    })
});
const resultado = await response.json();
```

### **Obtener Financiamientos en Mora**
```javascript
const response = await fetch('/api/financiamiento/financiamientos/en_mora/', {
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    }
});
const financiamientosMora = await response.json();
```

### **Calcular Moras**
```javascript
const response = await fetch('/api/financiamiento/financiamientos/1/calcular_moras/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    }
});
const resultado = await response.json();
```

### **Obtener Estadísticas**
```javascript
const response = await fetch('/api/financiamiento/financiamientos/estadisticas/', {
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    }
});
const stats = await response.json();
```

### **Generar Reporte**
```javascript
const response = await fetch('/api/financiamiento/reporte-financiamiento/?fecha_desde=2024-01-01&fecha_hasta=2024-01-31', {
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    }
});
const reporte = await response.json();
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

1. **Generación Automática:** Al crear un financiamiento, se generan automáticamente todas las cuotas
2. **Cálculo de Moras:** Las moras se calculan automáticamente cuando una cuota está atrasada
3. **Actualización Automática:** Al registrar un pago, se actualizan automáticamente el financiamiento y la cuota
4. **Estados:** Los financiamientos pueden estar en estado activo, finalizado, cancelado o en_mora
5. **Campos de Mora:** El campo `mora_atraso` contiene el valor de la penalización por retraso
6. **Configuración:** Las configuraciones de pago permiten definir fechas de vencimiento
7. **Auditoría:** Todos los registros incluyen información de auditoría (usuario, fechas)

---

## 🔄 **FLUJO DE FINANCIAMIENTO RECOMENDADO**

1. **Crear Financiamiento:** Usar POST para crear el financiamiento (se generan cuotas automáticamente)
2. **Configurar Fechas:** Establecer configuraciones de pago según necesidades
3. **Registrar Pagos:** Usar POST en pagos para registrar cada pago realizado
4. **Calcular Moras:** Usar el endpoint de cálculo de moras periódicamente
5. **Monitorear:** Usar estadísticas y reportes para seguimiento
6. **Finalizar:** El sistema marca automáticamente como finalizado cuando se pagan todas las cuotas
