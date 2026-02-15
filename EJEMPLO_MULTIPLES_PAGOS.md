# 💳 Ejemplos de Múltiples Pagos

## 🚀 **Nuevos Endpoints Disponibles**

### **1. Múltiples Pagos Generales**
```
POST /api/financiamiento/pagos/multiples_pagos/
```

### **2. Múltiples Pagos por Financiamiento**
```
POST /api/financiamiento/pagos/pagos_por_financiamiento/
```

---

## 📝 **Ejemplo 1: Múltiples Pagos Generales**

### **Request:**
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
            "metodo_pago": "Efectivo",
            "referencia_pago": "REF-001"
        },
        {
            "cuota_id": 2,
            "financiamiento_id": 1,
            "monto_capital": "1050.00",
            "monto_interes": "150.00",
            "monto_total": "1200.00",
            "fecha_pago": "2024-01-15",
            "metodo_pago": "Transferencia",
            "referencia_pago": "REF-002"
        },
        {
            "cuota_id": 5,
            "financiamiento_id": 2,
            "monto_capital": "800.00",
            "monto_interes": "400.00",
            "monto_mora": "50.00",
            "monto_total": "1250.00",
            "fecha_pago": "2024-01-15",
            "metodo_pago": "Efectivo",
            "referencia_pago": "REF-003"
        }
    ]
}
```

### **Response (Éxito):**
```json
{
    "mensaje": "Se crearon 3 pagos exitosamente",
    "pagos_creados": [
        {
            "indice": 0,
            "pago": {
                "id": 1,
                "cuota": {
                    "id": 1,
                    "numero_cuota": 1,
                    "estado": "pagada"
                },
                "financiamiento": {
                    "id": 1,
                    "saldo_restante": "61323.25"
                },
                "monto_capital": "1000.00",
                "monto_interes": "200.00",
                "monto_total": "1200.00",
                "fecha_pago": "2024-01-15",
                "metodo_pago": "Efectivo",
                "referencia_pago": "REF-001"
            },
            "estado": "creado"
        },
        {
            "indice": 1,
            "pago": {
                "id": 2,
                "cuota": {
                    "id": 2,
                    "numero_cuota": 2,
                    "estado": "pagada"
                },
                "financiamiento": {
                    "id": 1,
                    "saldo_restante": "60273.25"
                },
                "monto_capital": "1050.00",
                "monto_interes": "150.00",
                "monto_total": "1200.00",
                "fecha_pago": "2024-01-15",
                "metodo_pago": "Transferencia",
                "referencia_pago": "REF-002"
            },
            "estado": "creado"
        },
        {
            "indice": 2,
            "pago": {
                "id": 3,
                "cuota": {
                    "id": 5,
                    "numero_cuota": 5,
                    "estado": "pagada"
                },
                "financiamiento": {
                    "id": 2,
                    "saldo_restante": "45000.00"
                },
                "monto_capital": "800.00",
                "monto_interes": "400.00",
                "monto_mora": "50.00",
                "monto_total": "1250.00",
                "fecha_pago": "2024-01-15",
                "metodo_pago": "Efectivo",
                "referencia_pago": "REF-003"
            },
            "estado": "creado"
        }
    ],
    "total_procesados": 3,
    "exitosos": 3,
    "errores": 0
}
```

---

## 📝 **Ejemplo 2: Múltiples Pagos por Financiamiento**

### **Request:**
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
        },
        {
            "cuota_id": 3,
            "monto_capital": "1100.00",
            "monto_interes": "100.00",
            "monto_total": "1200.00",
            "fecha_pago": "2024-01-15",
            "metodo_pago": "Efectivo"
        }
    ]
}
```

### **Response (Éxito):**
```json
{
    "mensaje": "Se crearon 3 pagos para el financiamiento 1",
    "financiamiento_id": 1,
    "pagos_creados": [
        {
            "indice": 0,
            "pago": {
                "id": 4,
                "cuota": {
                    "id": 1,
                    "numero_cuota": 1,
                    "estado": "pagada"
                },
                "financiamiento": {
                    "id": 1,
                    "saldo_restante": "61323.25"
                },
                "monto_capital": "1000.00",
                "monto_interes": "200.00",
                "monto_total": "1200.00",
                "fecha_pago": "2024-01-15",
                "metodo_pago": "Efectivo"
            },
            "estado": "creado"
        },
        {
            "indice": 1,
            "pago": {
                "id": 5,
                "cuota": {
                    "id": 2,
                    "numero_cuota": 2,
                    "estado": "pagada"
                },
                "financiamiento": {
                    "id": 1,
                    "saldo_restante": "60273.25"
                },
                "monto_capital": "1050.00",
                "monto_interes": "150.00",
                "monto_total": "1200.00",
                "fecha_pago": "2024-01-15",
                "metodo_pago": "Transferencia"
            },
            "estado": "creado"
        },
        {
            "indice": 2,
            "pago": {
                "id": 6,
                "cuota": {
                    "id": 3,
                    "numero_cuota": 3,
                    "estado": "pagada"
                },
                "financiamiento": {
                    "id": 1,
                    "saldo_restante": "59173.25"
                },
                "monto_capital": "1100.00",
                "monto_interes": "100.00",
                "monto_total": "1200.00",
                "fecha_pago": "2024-01-15",
                "metodo_pago": "Efectivo"
            },
            "estado": "creado"
        }
    ],
    "total_procesados": 3,
    "exitosos": 3,
    "errores": 0
}
```

---

## 📝 **Ejemplo 3: Con Errores**

### **Request (Con error en el segundo pago):**
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
            "cuota_id": 999,  // Cuota que no existe
            "monto_capital": "1050.00",
            "monto_interes": "150.00",
            "monto_total": "1200.00",
            "fecha_pago": "2024-01-15",
            "metodo_pago": "Transferencia"
        },
        {
            "cuota_id": 3,
            "monto_capital": "1100.00",
            "monto_interes": "100.00",
            "monto_total": "1200.00",
            "fecha_pago": "2024-01-15",
            "metodo_pago": "Efectivo"
        }
    ]
}
```

### **Response (Con errores - Rollback):**
```json
{
    "error": "Error al procesar los pagos",
    "mensaje": "Errores en algunos pagos",
    "financiamiento_id": 1,
    "pagos_creados": [],
    "errores": [
        {
            "indice": 1,
            "error": {
                "cuota": [
                    "Instancia con pk 999 no existe."
                ]
            },
            "estado": "error"
        }
    ],
    "total_procesados": 3,
    "exitosos": 0,
    "errores": 1
}
```

---

## 🔧 **Casos de Uso Comunes**

### **1. Pago de Múltiples Cuotas del Mismo Cliente**
```javascript
// Cliente paga 3 cuotas atrasadas de una vez
const pagos = [
    { cuota_id: 1, monto_capital: "1000", monto_interes: "200", monto_mora: "50", monto_total: "1250" },
    { cuota_id: 2, monto_capital: "1050", monto_interes: "150", monto_mora: "30", monto_total: "1230" },
    { cuota_id: 3, monto_capital: "1100", monto_interes: "100", monto_mora: "20", monto_total: "1220" }
];
```

### **2. Pago de Cuotas de Diferentes Financiamientos**
```javascript
// Cliente paga cuotas de diferentes lotes
const pagos = [
    { cuota_id: 1, financiamiento_id: 1, monto_capital: "1000", monto_interes: "200", monto_total: "1200" },
    { cuota_id: 5, financiamiento_id: 2, monto_capital: "800", monto_interes: "400", monto_total: "1200" }
];
```

### **3. Pago Masivo de Cuotas Pendientes**
```javascript
// Sistema procesa pagos masivos de cuotas pendientes
const cuotasPendientes = await getCuotasPendientes();
const pagos = cuotasPendientes.map(cuota => ({
    cuota_id: cuota.id,
    financiamiento_id: cuota.financiamiento_id,
    monto_capital: cuota.monto_capital,
    monto_interes: cuota.monto_interes,
    monto_total: cuota.monto_total,
    fecha_pago: new Date().toISOString().split('T')[0],
    metodo_pago: "Transferencia"
}));
```

---

## ⚠️ **Limitaciones y Consideraciones**

### **Límites:**
- **Máximo 50 pagos** por petición
- **Transacción atómica**: Si falla un pago, se revierten todos
- **Validación estricta**: Todos los campos requeridos deben estar presentes

### **Validaciones:**
- ✅ Cuota debe existir
- ✅ Financiamiento debe existir
- ✅ Cuota debe pertenecer al financiamiento
- ✅ Montos deben ser válidos
- ✅ Fecha de pago debe ser válida

### **Seguridad:**
- 🔐 Requiere autenticación JWT
- 🔐 Validación de permisos
- 🔐 Prevención de pagos duplicados
- 🔐 Auditoría completa de transacciones

---

## 🎯 **Ventajas de Múltiples Pagos**

1. **🚀 Rendimiento**: Menos peticiones HTTP
2. **🔄 Consistencia**: Transacción atómica
3. **📊 Reportes**: Respuesta detallada de cada pago
4. **🛡️ Seguridad**: Validación centralizada
5. **📱 UX**: Mejor experiencia de usuario
6. **💾 Base de Datos**: Menos overhead de conexiones

¡Ahora puedes procesar múltiples pagos de manera eficiente y segura! 🎉
