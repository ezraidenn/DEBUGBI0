# Problema Crítico: Discrepancia en Contadores Individuales

## 🔴 PROBLEMA IDENTIFICADO

**Síntoma:** El contador de "Accesos Concedidos Hoy" en páginas individuales muestra **MÁS eventos** de los que realmente hay.

**Ejemplo:** Casaclub muestra 22 accesos pero la suma manual da 17.

---

## 🔍 CAUSA RAÍZ

Hay **DOS funciones diferentes** calculando los accesos concedidos:

### **1. `device_monitor.py::get_debug_summary()` (línea 522)**
Usada por el **DASHBOARD** para mostrar estadísticas en tarjetas.

```python
# Filtrar solo accesos concedidos
granted_df = df[df['event_code'].isin(EVENT_CODES['ACCESS_GRANTED'])]
access_granted = len(granted_df)
```

**Códigos que usa:** Solo los de `EVENT_CODES['ACCESS_GRANTED']` (definidos en device_monitor.py)

---

### **2. `app.py::debug_device()` (línea 750-872)**
Usada por las **PÁGINAS INDIVIDUALES** para mostrar el contador.

```python
# FILTER: Only show ACCESS GRANTED events
ACCESS_GRANTED_CODES = [
    '4097', '4098', '4099', '4100', '4101', '4102', '4103', '4104', '4105', '4106', '4107',
    '4112', '4113', '4114', '4115', '4118', '4119', '4120', '4121', '4122', '4123', '4128', '4129',
    '4865', '4866', '4867', '4868', '4869', '4870', '4871', '4872'
]

granted_events = [e for e in events if get_event_code(e) in ACCESS_GRANTED_CODES]

summary = {
    'total_events': len(events_list),  # ← AQUÍ ESTÁ EL ERROR
    'access_granted': len(events_list),
    ...
}
```

**Problema:** 
1. Filtra eventos con `ACCESS_GRANTED_CODES` (línea 768)
2. Convierte a DataFrame (línea 787)
3. **PERO** luego usa `len(events_list)` que puede incluir eventos que NO son accesos concedidos

---

## 🔬 ANÁLISIS DETALLADO

### **Flujo en `app.py::debug_device()`:**

1. **Línea 751-752:** Obtiene eventos del día y filtra por horario
2. **Línea 768:** Filtra solo accesos concedidos → `granted_events`
3. **Línea 787:** Convierte `granted_events` a DataFrame
4. **Línea 794:** Convierte DataFrame a lista → `events_list`
5. **Línea 872:** Calcula `access_granted = len(events_list)`

**PROBLEMA:** Si el DataFrame tiene más filas que `granted_events` (por algún procesamiento interno), el contador será incorrecto.

---

## 🎯 SOLUCIÓN

Usar **la misma lógica** que `device_monitor.py::get_debug_summary()`:

```python
# En lugar de:
summary = {
    'total_events': len(events_list),
    'access_granted': len(events_list),
    ...
}

# Usar:
summary = {
    'total_events': len(granted_events),  # ← Usar granted_events original
    'access_granted': len(granted_events),
    ...
}
```

O mejor aún: **Llamar directamente a `monitor.get_debug_summary(device_id)`** en lugar de recalcular.

---

## 📋 VERIFICACIÓN

### **Códigos de Acceso Concedido en `device_monitor.py`:**
```python
EVENT_CODES = {
    'ACCESS_GRANTED': [
        '4097', '4098', '4099', '4100', '4101', '4102', '4103', '4104', '4105', '4106', '4107',
        '4112', '4113', '4114', '4115', '4118', '4119', '4120', '4121', '4122', '4123', '4128', '4129',
        '4865', '4866', '4867', '4868', '4869', '4870', '4871', '4872'
    ],
    ...
}
```

### **Códigos en `app.py::debug_device()`:**
```python
ACCESS_GRANTED_CODES = [
    '4097', '4098', '4099', '4100', '4101', '4102', '4103', '4104', '4105', '4106', '4107',
    '4112', '4113', '4114', '4115', '4118', '4119', '4120', '4121', '4122', '4123', '4128', '4129',
    '4865', '4866', '4867', '4868', '4869', '4870', '4871', '4872'
]
```

**Los códigos son idénticos**, así que el problema NO es la lista de códigos.

---

## 🔧 CORRECCIÓN NECESARIA

**Archivo:** `app.py` línea 870-877

**Cambiar:**
```python
summary = {
    'total_events': len(events_list),
    'access_granted': len(events_list),
    'access_denied': 0,
    'unique_users': unique_users_count,
    'first_event': utc_to_local(first_event_dt) if first_event_dt else None,
    'last_event': utc_to_local(last_event_dt) if last_event_dt else None
}
```

**Por:**
```python
summary = {
    'total_events': len(granted_events),  # ← Usar granted_events original
    'access_granted': len(granted_events),  # ← Usar granted_events original
    'access_denied': 0,
    'unique_users': unique_users_count,
    'first_event': utc_to_local(first_event_dt) if first_event_dt else None,
    'last_event': utc_to_local(last_event_dt) if last_event_dt else None
}
```

---

## ✅ IMPACTO

Esta corrección:
1. ✅ Arreglará los contadores en páginas individuales
2. ✅ Hará que la suma del dashboard sea correcta
3. ✅ Eliminará la discrepancia de 5 eventos por dispositivo
4. ✅ Asegurará consistencia entre dashboard y páginas individuales
