# 🚪 ESTADOS DE ENTRADA Y SALIDA EN BIOSTAR

## 🔍 Investigación

### ¿Los checadores envían estados de entrada/salida?

**Respuesta: NO directamente, pero se puede configurar.**

---

## 📊 Cómo Funciona BioStar

### 1. **Eventos Básicos**
Por defecto, los checadores BioStar envían:
- ✅ **Evento de verificación exitosa** (código 4097-4115)
- ✅ **Evento de verificación fallida** (código 4609-4627)
- ✅ **Usuario ID**
- ✅ **Timestamp**
- ✅ **Dispositivo ID**

**NO envían:**
- ❌ Si es entrada o salida
- ❌ Dirección del movimiento
- ❌ Estado del empleado

---

## 🔧 Configuración de Entrada/Salida

### Opción 1: **Modo de Entrada/Salida en Dispositivo**

Algunos modelos de BioStar (BioStation 2, BioStation 3) tienen un modo especial:

```
Configuración en BioStar 2:
1. Device → [Seleccionar dispositivo]
2. Advanced Settings
3. Authentication Mode → "Entry/Exit"
```

**Cuando está activado:**
- El dispositivo pregunta al usuario: "¿Entrada o Salida?"
- El usuario selecciona en la pantalla
- Se envía un evento con el tipo

**Códigos de evento:**
```
- 16385: Entrada (Entry)
- 16386: Salida (Exit)
```

---

### Opción 2: **Dispositivos Pareados (Entrada/Salida)**

Configurar dos dispositivos:
- **Dispositivo A**: Entrada (fuera → dentro)
- **Dispositivo B**: Salida (dentro → fuera)

```
Lógica:
- Evento en Dispositivo A = Entrada
- Evento en Dispositivo B = Salida
```

**Ventajas:**
- ✅ Automático
- ✅ No requiere interacción del usuario
- ✅ Más rápido

**Desventajas:**
- ❌ Requiere 2 dispositivos por puerta
- ❌ Más costoso

---

### Opción 3: **Zonas de Acceso (Access Zones)**

BioStar 2 tiene un sistema de zonas:

```
Configuración:
1. Access Control → Access Zones
2. Crear zona "Oficina"
3. Asignar dispositivos:
   - Entry Devices: [Dispositivo entrada]
   - Exit Devices: [Dispositivo salida]
```

**Cómo funciona:**
- BioStar rastrea en qué zona está cada usuario
- Si está fuera y usa dispositivo de entrada → Entrada
- Si está dentro y usa dispositivo de salida → Salida

---

## 📝 Códigos de Evento Relevantes

### Eventos de Entrada/Salida (si está configurado)

```python
ENTRY_EXIT_CODES = {
    'ENTRY': [
        '16385',  # Entry (Entrada)
    ],
    'EXIT': [
        '16386',  # Exit (Salida)
    ]
}
```

### Eventos de Zona

```python
ZONE_CODES = {
    'ZONE_APB_VIOLATION': [
        '28673',  # Anti-Passback violation
    ],
    'ZONE_ENTRY': [
        '28674',  # Zone entry
    ],
    'ZONE_EXIT': [
        '28675',  # Zone exit
    ]
}
```

---

## 🔍 Cómo Verificar en Tu Sistema

### 1. **Revisar Eventos Actuales**

Busca en los eventos si aparecen códigos 16385 o 16386:

```python
# En tu código actual
events = monitor.get_device_events_today(device_id)

for event in events:
    code = event.get('event_code')
    if code in ['16385', '16386']:
        print(f"¡Evento de entrada/salida encontrado! Código: {code}")
```

### 2. **Revisar Configuración del Dispositivo**

En BioStar 2 Web:
```
1. Device → [Tu dispositivo]
2. Advanced Settings
3. Buscar "Authentication Mode" o "Entry/Exit Mode"
```

### 3. **Revisar Modelo del Dispositivo**

No todos los modelos soportan entrada/salida:

**Soportan:**
- ✅ BioStation 2
- ✅ BioStation 3
- ✅ BioLite Net
- ✅ XPass D2

**NO soportan:**
- ❌ BioEntry W2
- ❌ Modelos antiguos

---

## 💡 Alternativa: Lógica de Negocio

Si los dispositivos NO soportan entrada/salida, puedes implementar lógica:

### Ejemplo: Alternar Entrada/Salida

```python
# Tabla de estado de usuarios
user_states = {
    'user_123': 'outside',  # outside o inside
}

def process_event(user_id, event_time):
    current_state = user_states.get(user_id, 'outside')
    
    if current_state == 'outside':
        # Próximo evento es entrada
        event_type = 'ENTRADA'
        user_states[user_id] = 'inside'
    else:
        # Próximo evento es salida
        event_type = 'SALIDA'
        user_states[user_id] = 'outside'
    
    return event_type
```

### Ejemplo: Por Horario

```python
def determine_entry_exit(event_time):
    hour = event_time.hour
    
    if 5 <= hour < 12:
        return 'ENTRADA'  # Mañana = entrada
    elif 12 <= hour < 14:
        return 'SALIDA_COMIDA'  # Mediodía = salida a comer
    elif 14 <= hour < 18:
        return 'ENTRADA_COMIDA'  # Tarde = regreso de comer
    else:
        return 'SALIDA'  # Noche = salida
```

### Ejemplo: Por Dispositivo

```python
DEVICE_TYPES = {
    542346241: 'ENTRADA',  # Casaclub - Entrada
    544502684: 'SALIDA',   # Casaclub - Salida
}

def get_event_type(device_id):
    return DEVICE_TYPES.get(device_id, 'ACCESO')
```

---

## 🎯 Recomendación

### Para Tu Sistema Actual:

1. **Verificar si los dispositivos soportan entrada/salida**
   - Revisar modelo en BioStar 2
   - Buscar códigos 16385/16386 en eventos

2. **Si NO soportan:**
   - Opción A: Implementar lógica por dispositivo (más simple)
   - Opción B: Implementar lógica alternada (más complejo)
   - Opción C: Dejar como "Acceso" genérico (actual)

3. **Si SÍ soportan:**
   - Activar modo entrada/salida en BioStar 2
   - Actualizar código para detectar códigos 16385/16386
   - Mostrar en UI como "Entrada" o "Salida"

---

## 📝 Código para Detectar Entrada/Salida

### Si está configurado en BioStar:

```python
# En device_monitor.py
EVENT_CODES = {
    # ... códigos existentes ...
    
    'ENTRY': ['16385'],
    'EXIT': ['16386'],
}

def classify_event(event_code):
    if event_code in EVENT_CODES['ENTRY']:
        return 'info', 'Entrada'
    elif event_code in EVENT_CODES['EXIT']:
        return 'warning', 'Salida'
    # ... resto de clasificaciones ...
```

---

## ✅ Conclusión

**Los checadores BioStar:**
- ❌ NO envían entrada/salida por defecto
- ✅ PUEDEN configurarse para hacerlo (modelos compatibles)
- ✅ Alternativa: Lógica de negocio en tu aplicación

**Próximos pasos:**
1. Verificar modelo de tus dispositivos
2. Revisar si aparecen códigos 16385/16386
3. Decidir estrategia (configuración vs lógica)

---

**Fecha:** 2025-11-19  
**Estado:** 📋 INVESTIGACIÓN COMPLETADA
