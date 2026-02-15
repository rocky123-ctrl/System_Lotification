# 💰 Pagos a Capital - Sistema de Lotificación

## 📋 **Descripción General**

Los **Pagos a Capital** permiten a los clientes realizar pagos adelantados sobre el capital de su financiamiento, lo que reduce automáticamente los intereses de las cuotas pendientes y puede disminuir el monto de las cuotas mensuales.

## 🎯 **Beneficios de los Pagos a Capital**

### **Para el Cliente:**
- ✅ **Ahorro en intereses**: Reduce el costo total del financiamiento
- ✅ **Cuotas más bajas**: Disminuye el monto de las cuotas pendientes
- ✅ **Pago más rápido**: Acelera el proceso de liquidación
- ✅ **Flexibilidad**: Puede hacer pagos adicionales cuando tenga disponibilidad

### **Para la Empresa:**
- ✅ **Mejor flujo de caja**: Ingresos adicionales antes de lo programado
- ✅ **Reducción de riesgo**: Menor exposición crediticia
- ✅ **Satisfacción del cliente**: Mejora la relación comercial

## 🔧 **Funcionalidades Implementadas**

### **1. Modelo PagoCapital**
- Registro de pagos adelantados a capital
- Referencias automáticas (formato: `CAP-001-A1`)
- Cálculo automático de saldos restantes
- Recalculo automático de cuotas pendientes

### **2. Recalculo Inteligente de Cuotas**
- **Nueva cuota mensual**: Se recalcula usando la fórmula de amortización
- **Redistribución de capital e intereses**: Se ajustan automáticamente
- **Actualización de fechas de vencimiento**: Se mantienen las fechas originales
- **Estado de cuotas**: Se actualiza según el nuevo saldo

### **3. Simulación de Pagos**
- **Antes de aplicar**: Simula el efecto del pago a capital
- **Muestra ahorro estimado**: Calcula intereses que se evitan
- **Compara cuotas**: Antes y después del pago

## 📊 **Fórmulas de Cálculo**

### **Nueva Cuota Mensual:**
```
nueva_cuota = saldo_restante * (tasa_mensual * (1 + tasa_mensual)^plazo) / ((1 + tasa_mensual)^plazo - 1)
```

### **Ahorro Estimado en Intereses:**
```
ahorro = monto_pago * tasa_mensual * cuotas_pendientes / 2
```

## 🌐 **Endpoints de la API**

### **Pagos a Capital**

#### **1. Crear Pago a Capital**
```http
POST /api/financiamiento/pagos-capital/
```

**Body:**
```json
{
    "financiamiento_id": 1,
    "monto": "5000.00",
    "fecha_pago": "2025-08-25",
    "concepto": "Pago adelantado por bonificación"
}
```

**Response:**
```json
{
    "id": 1,
    "financiamiento": 1,
    "monto": "5000.00",
    "fecha_pago": "2025-08-25",
    "concepto": "Pago adelantado por bonificación",
    "referencia_pago": "CAP-001-A1",
    "financiamiento_info": {
        "id": 1,
        "lote_numero": "1",
        "manzana": "A",
        "promitente_comprador": "Juan Pérez",
        "saldo_restante": "45000.00",
        "cuotas_pendientes": 10
    },
    "ahorro_intereses": "312.50"
}
```

#### **2. Listar Pagos a Capital**
```http
GET /api/financiamiento/pagos-capital/
```

#### **3. Pagos por Financiamiento**
```http
GET /api/financiamiento/pagos-capital/por_financiamiento/?financiamiento_id=1
```

#### **4. Resumen Mensual**
```http
GET /api/financiamiento/pagos-capital/resumen_mensual/?año=2025&mes=8
```

#### **5. Estadísticas Generales**
```http
GET /api/financiamiento/pagos-capital/estadisticas/
```

### **Financiamientos (Acciones Adicionales)**

#### **6. Aplicar Pago a Capital (Acción Directa)**
```http
POST /api/financiamiento/financiamientos/{id}/aplicar_pago_capital/
```

**Body:**
```json
{
    "monto": "5000.00",
    "fecha_pago": "2025-08-25",
    "concepto": "Pago adelantado"
}
```

#### **7. Simular Pago a Capital**
```http
GET /api/financiamiento/financiamientos/{id}/simulacion_pago_capital/?monto=5000.00
```

**Response:**
```json
{
    "monto_pago": "5000.00",
    "saldo_anterior": "50000.00",
    "saldo_nuevo": "45000.00",
    "cuota_actual": "5724.48",
    "nueva_cuota_mensual": "5152.03",
    "cuotas_pendientes": 10,
    "ahorro_estimado_intereses": "312.50",
    "reduccion_cuota": "572.45"
}
```

#### **8. Pagos a Capital de un Financiamiento**
```http
GET /api/financiamiento/financiamientos/{id}/pagos_capital/
```

## 💡 **Ejemplos de Uso**

### **Ejemplo 1: Pago a Capital Básico**
```python
# Crear un pago a capital de Q5,000
pago_data = {
    "financiamiento_id": 1,
    "monto": "5000.00",
    "fecha_pago": "2025-08-25",
    "concepto": "Pago adelantado por bonificación"
}

response = requests.post('/api/financiamiento/pagos-capital/', json=pago_data)
```

### **Ejemplo 2: Simular Antes de Aplicar**
```python
# Simular el efecto de un pago a capital
response = requests.get('/api/financiamiento/financiamientos/1/simulacion_pago_capital/?monto=10000.00')
simulacion = response.json()

print(f"Ahorro estimado: Q{simulacion['ahorro_estimado_intereses']}")
print(f"Reducción de cuota: Q{simulacion['reduccion_cuota']}")
```

### **Ejemplo 3: Obtener Estadísticas**
```python
# Obtener estadísticas de pagos a capital
response = requests.get('/api/financiamiento/pagos-capital/estadisticas/')
stats = response.json()

print(f"Total pagos a capital: {stats['total_pagos']}")
print(f"Monto total: Q{stats['monto_total']}")
print(f"Promedio por pago: Q{stats['promedio_pago']}")
```

## 🔍 **Validaciones y Restricciones**

### **Validaciones Automáticas:**
- ✅ **Monto positivo**: El pago debe ser mayor a 0
- ✅ **Saldo disponible**: No puede exceder el saldo restante
- ✅ **Estado activo**: Solo financiamientos activos permiten pagos
- ✅ **Referencia única**: Se genera automáticamente

### **Restricciones:**
- ❌ **Financiamientos finalizados**: No permiten pagos adicionales
- ❌ **Financiamientos cancelados**: No permiten pagos adicionales
- ❌ **Monto excesivo**: No puede ser mayor al saldo restante

## 📈 **Reportes y Estadísticas**

### **Reportes Disponibles:**
1. **Resumen Mensual**: Pagos a capital por mes
2. **Por Financiamiento**: Historial de pagos de un cliente
3. **Estadísticas Generales**: Totales y promedios
4. **Impacto en Cuotas**: Reducción de cuotas por pago

### **Métricas Clave:**
- Total de pagos a capital
- Monto total aplicado
- Promedio por pago
- Ahorro estimado en intereses
- Reducción promedio de cuotas

## 🎨 **Interfaz de Usuario (Admin Django)**

### **Página de Pagos a Capital:**
- Lista de todos los pagos a capital
- Filtros por fecha y financiamiento
- Búsqueda por referencia o concepto
- Acciones en lote

### **Integración en Financiamientos:**
- Pestaña de "Pagos a Capital" en cada financiamiento
- Vista de historial de pagos
- Botón para crear nuevo pago
- Información de ahorro estimado

## 🚀 **Casos de Uso Comunes**

### **1. Cliente con Bonificación**
- **Situación**: Cliente recibe bonificación de Q10,000
- **Acción**: Aplicar pago a capital
- **Resultado**: Cuotas reducidas y ahorro en intereses

### **2. Pago Adelantado por Conveniencia**
- **Situación**: Cliente quiere pagar más rápido
- **Acción**: Pagos regulares a capital
- **Resultado**: Liquidación anticipada del financiamiento

### **3. Ajuste por Negociación**
- **Situación**: Cliente negocia mejoras en el lote
- **Acción**: Pago a capital como parte del acuerdo
- **Resultado**: Reducción de la deuda pendiente

## 🔧 **Configuración Técnica**

### **Variables de Entorno:**
```bash
# Configuración de tasas (ya configurado en ConfiguracionGeneral)
TASA_ANUAL=15.79
TASA_MENSUAL=1.25  # Calculado automáticamente
```

### **Dependencias:**
- `django-redis` (para cache)
- `python-dateutil` (para cálculos de fechas)
- `decimal` (para precisión en cálculos financieros)

## 📝 **Notas Importantes**

### **Precisión en Cálculos:**
- Todos los cálculos usan `Decimal` para evitar errores de punto flotante
- Las tasas se manejan como porcentajes (ej: 1.25 para 1.25%)
- Los redondeos se hacen a 2 decimales

### **Auditoría:**
- Todos los pagos registran usuario creador
- Fechas de creación automáticas
- Referencias únicas para trazabilidad

### **Rendimiento:**
- Los cálculos se optimizan para evitar consultas innecesarias
- Se usa cache para configuraciones frecuentes
- Las migraciones son eficientes y no bloquean la aplicación

## 🎉 **¡Funcionalidad Lista!**

La implementación de **Pagos a Capital** está completa y lista para usar. Esta funcionalidad mejora significativamente la experiencia del cliente y proporciona flexibilidad financiera tanto para clientes como para la empresa.

**¡Disfruta de esta nueva funcionalidad!** 🚀
