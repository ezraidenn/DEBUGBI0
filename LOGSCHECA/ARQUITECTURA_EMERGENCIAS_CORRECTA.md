# 🏢 Arquitectura de Emergencias - Dos Niveles

## 📐 **Estructura Jerárquica**

```
NIVEL 1: PhysicalArea (Edificios/Zonas Físicas)
├─ Casa Club
├─ Gimnasio
├─ Cafetería
└─ Oficinas Anexo

NIVEL 2: OrganizationalArea (Departamentos/Equipos)
├─ Área Sistemas
├─ Área Administración
├─ Área Contaduría
├─ Área Recursos Humanos
└─ Área Mantenimiento
```

---

## 🚨 **Flujo de Emergencia**

### **Escenario: Incendio en Casa Club**

```
1. ACTIVACIÓN
   ├─ Admin activa emergencia en "Casa Club" (PhysicalArea)
   ├─ Se activa alarma en Casa Club
   ├─ Se abren TODAS las puertas de Casa Club
   └─ Se inicia pase de lista automáticamente

2. PASE DE LISTA (Agrupado por Departamentos)
   ├─ 📋 Área Sistemas (5 personas)
   │   ├─ ✅ Juan Pérez - Presente
   │   ├─ ✅ María García - Presente
   │   ├─ ❌ Carlos López - Ausente
   │   ├─ ✅ Ana Martínez - Presente
   │   └─ ⏳ Luis Rodríguez - Pendiente
   │
   ├─ 📋 Área Administración (8 personas)
   │   ├─ ✅ Pedro Sánchez - Presente
   │   ├─ ✅ Laura Torres - Presente
   │   └─ ...
   │
   └─ 📋 Área Contaduría (3 personas)
       ├─ ✅ Roberto Díaz - Presente
       ├─ ❌ Carmen Ruiz - Ausente
       └─ ✅ Miguel Ángel - Presente

3. RESOLUCIÓN
   ├─ Admin marca emergencia como resuelta
   ├─ Se cierran las puertas de Casa Club
   ├─ Se desactiva la alarma
   └─ Se finaliza el pase de lista
```

---

## 🗄️ **Modelos de Base de Datos**

### **PhysicalArea** (Edificios/Zonas)
```python
- id
- name: "Casa Club"
- code: "CC-01"
- building_number: "Edificio A"
- floor: "Planta Baja"
- has_emergency_exit: True
- max_capacity: 150
- priority: 2 (Alta)

# Dispositivos asociados:
- Puerta Principal (entrada)
- Puerta Trasera (salida emergencia)
- Alarma Incendio
- Checadores internos
```

### **OrganizationalArea** (Departamentos)
```python
- id
- name: "Área Sistemas"
- code: "SIS"
- description: "Departamento de TI"

# Usuarios asociados:
- Juan Pérez (jperez)
- María García (mgarcia)
- Carlos López (clopez)
```

### **UserProfile** (Usuarios)
```python
- id
- user_id: "jperez"
- full_name: "Juan Pérez"
- organizational_area_id: 1 (Área Sistemas)
- last_known_location: "Casa Club"
```

---

## 🎯 **Relaciones**

```
PhysicalArea (1) ──── (N) DeviceConfig
  "Casa Club tiene 5 dispositivos"

OrganizationalArea (1) ──── (N) UserProfile
  "Área Sistemas tiene 5 empleados"

EmergencySession (1) ──── (1) PhysicalArea
  "Emergencia activa en Casa Club"

RollCallSession (1) ──── (1) EmergencySession
  "Pase de lista de la emergencia en Casa Club"

RollCallEntry (N) ──── (1) UserProfile
RollCallEntry (N) ──── (1) OrganizationalArea
  "Entrada del pase de lista agrupada por departamento"
```

---

## 📊 **Vista del Pase de Lista**

### **Interfaz Propuesta:**

```
┌─────────────────────────────────────────────────────────┐
│ 🚨 Pase de Lista - Emergencia: Incendio en Casa Club   │
│ Iniciado: 12/12/2024 11:30 AM                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 📋 Área Sistemas (5 personas)                          │
│ ┌─────────────────────────────────────────────────┐   │
│ │ ✅ Juan Pérez        | Presente | 11:32 AM      │   │
│ │ ✅ María García      | Presente | 11:33 AM      │   │
│ │ ❌ Carlos López      | Ausente  | Sin marcar    │   │
│ │ ✅ Ana Martínez      | Presente | 11:31 AM      │   │
│ │ ⏳ Luis Rodríguez    | Pendiente| Sin marcar    │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ 📋 Área Administración (8 personas)                    │
│ ┌─────────────────────────────────────────────────┐   │
│ │ ✅ Pedro Sánchez     | Presente | 11:32 AM      │   │
│ │ ✅ Laura Torres      | Presente | 11:34 AM      │   │
│ │ ...                                              │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ 📋 Área Contaduría (3 personas)                        │
│ ┌─────────────────────────────────────────────────┐   │
│ │ ✅ Roberto Díaz      | Presente | 11:35 AM      │   │
│ │ ❌ Carmen Ruiz       | Ausente  | Sin marcar    │   │
│ │ ✅ Miguel Ángel      | Presente | 11:33 AM      │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ ┌─────────────────────────────────────────────────┐   │
│ │ Total: 16 personas                               │   │
│ │ Presentes: 10 (62.5%)                           │   │
│ │ Ausentes: 2 (12.5%)                             │   │
│ │ Pendientes: 4 (25%)                             │   │
│ └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ **Ventajas de Esta Arquitectura**

1. **Orden lógico**: Las personas están agrupadas por su departamento
2. **Rapidez**: Los coordinadores de cada área pueden marcar a su equipo
3. **Claridad**: Se ve inmediatamente qué departamento falta
4. **Flexibilidad**: 
   - Emergencia en un edificio físico (Casa Club)
   - Pero el pase de lista es por equipos organizacionales
5. **Escalabilidad**: Puedes tener múltiples departamentos en un mismo edificio

---

## 🔧 **Implementación Actual vs Correcta**

### **❌ Problema Actual:**
- PhysicalArea y OrganizationalArea están separados
- No hay relación clara entre edificios y departamentos
- El pase de lista no agrupa por departamentos

### **✅ Solución:**
1. Mantener PhysicalArea para control físico (alarmas/puertas)
2. Mantener OrganizationalArea para agrupación de personas
3. UserProfile debe tener `organizational_area_id`
4. RollCallEntry debe agruparse por OrganizationalArea
5. La vista del pase de lista debe mostrar acordeones por departamento

---

## 📝 **Próximos Pasos**

1. ✅ Verificar que UserProfile tenga `organizational_area_id`
2. ✅ Modificar RollCallEntry para incluir `organizational_area_id`
3. ✅ Actualizar la API de pase de lista para agrupar por departamento
4. ✅ Modificar `roll_call.html` para mostrar acordeones por departamento
5. ✅ Agregar filtros por departamento en la interfaz

---

## 🎯 **Resultado Final**

```
EMERGENCIA en Casa Club (PhysicalArea)
  ↓
ALARMA + PUERTAS en Casa Club
  ↓
PASE DE LISTA agrupado por:
  - Área Sistemas
  - Área Administración  
  - Área Contaduría
  - etc.
  ↓
CHECK ORDENADO Y RÁPIDO ✅
```

**¡Esto es lo que necesitas!** 🚀
