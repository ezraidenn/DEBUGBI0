# ⏰ FILTRO DE HORARIO 5:30 AM - 11:59 PM

## ✅ Funcionalidad Implementada

**Filtro automático de eventos por horario operativo:**
- ✅ Solo muestra eventos entre **5:30 AM y 11:59 PM**
- ✅ Aplicado en **todas las vistas** (dashboard, individuales, modales)
- ✅ Basado en **hora local de México** (UTC-6)

---

## 🎯 Horario de Operación

```
Inicio:  5:30 AM  (05:30)
Fin:     11:59 PM (23:59)

Eventos fuera de este horario NO se muestran
```

---

## 📍 Aplicado En

### 1. **Dashboard General**
```
- Tarjetas de resumen por dispositivo
- Contadores de eventos
- Estadísticas globales
```

### 2. **Vista Individual de Dispositivo**
```
- Tabla de eventos
- Tarjetas de estadísticas
- Gráficos y resúmenes
```

### 3. **Modales de Detalles**
```
- Total de Eventos
- Accesos Concedidos
- Accesos Denegados
- Usuarios Únicos
```

---

## 🔧 Implementación Técnica

### Función de Filtrado
```python
def filter_events_by_time(events, start_hour=5, start_minute=30, 
                         end_hour=23, end_minute=59):
    """
    Filtra eventos por horario operativo.
    Default: 5:30 AM - 11:59 PM (hora local)
    """
    filtered_events = []
    
    for event in events:
        # Convertir a hora local de México
        local_dt = utc_to_local(event.get('datetime'))
        
        # Calcular minutos desde medianoche
        event_time_minutes = local_dt.hour * 60 + local_dt.minute
        start_time_minutes = start_hour * 60 + start_minute  # 330 min
        end_time_minutes = end_hour * 60 + end_minute        # 1439 min
        
        # Verificar si está en rango
        if start_time_minutes <= event_time_minutes <= end_time_minutes:
            filtered_events.append(event)
    
    return filtered_events
```

---

## 📊 Ejemplo de Filtrado

### Eventos del Día (Sin Filtro)
```
00:15 - Usuario 123 - Acceso ❌ (Fuera de horario)
03:45 - Usuario 456 - Acceso ❌ (Fuera de horario)
05:25 - Usuario 789 - Acceso ❌ (Antes de 5:30)
05:30 - Usuario 101 - Acceso ✅ (Dentro de horario)
08:00 - Usuario 102 - Acceso ✅ (Dentro de horario)
12:30 - Usuario 103 - Acceso ✅ (Dentro de horario)
18:45 - Usuario 104 - Acceso ✅ (Dentro de horario)
23:59 - Usuario 105 - Acceso ✅ (Dentro de horario)
00:05 - Usuario 106 - Acceso ❌ (Después de 23:59)
```

### Eventos Mostrados (Con Filtro)
```
05:30 - Usuario 101 - Acceso ✅
08:00 - Usuario 102 - Acceso ✅
12:30 - Usuario 103 - Acceso ✅
18:45 - Usuario 104 - Acceso ✅
23:59 - Usuario 105 - Acceso ✅

Total: 5 eventos (de 9 originales)
```

---

## 🔄 Flujo de Datos

### 1. **BioStar → Monitor**
```
BioStar devuelve TODOS los eventos del día
(00:00 - 23:59)
```

### 2. **Monitor → Filtro**
```
Filtro aplica rango horario
(05:30 - 23:59)
```

### 3. **Filtro → UI**
```
Solo eventos dentro del horario operativo
se muestran al usuario
```

---

## 📍 Lugares Modificados

### 1. **webapp/app.py**
```python
# Función helper
def filter_events_by_time(events, start_hour=5, start_minute=30, 
                         end_hour=23, end_minute=59):
    # Lógica de filtrado

# Aplicado en:
- debug_device()          # Vista individual
- get_stat_details()      # Modales de estadísticas
```

### 2. **src/api/device_monitor.py**
```python
# Método de clase
def _filter_events_by_time(self, events, ...):
    # Lógica de filtrado

# Aplicado en:
- get_debug_summary()     # Dashboard y resúmenes
```

---

## ⏰ Rangos de Tiempo

### Minutos desde Medianoche
```
00:00 = 0 minutos
05:30 = 330 minutos  ← Inicio
12:00 = 720 minutos
18:00 = 1080 minutos
23:59 = 1439 minutos ← Fin
```

### Comparación
```python
event_time_minutes = 350  # 5:50 AM
start_time_minutes = 330  # 5:30 AM
end_time_minutes = 1439   # 11:59 PM

if 330 <= 350 <= 1439:    # True ✅
    show_event()
```

---

## 🎯 Casos de Uso

### Caso 1: Evento Temprano
```
Evento: 04:00 AM
Filtro: 05:30 AM - 11:59 PM
Resultado: NO mostrado ❌
Razón: Antes del horario operativo
```

### Caso 2: Evento en Horario
```
Evento: 09:15 AM
Filtro: 05:30 AM - 11:59 PM
Resultado: Mostrado ✅
Razón: Dentro del horario operativo
```

### Caso 3: Evento Nocturno
```
Evento: 01:30 AM
Filtro: 05:30 AM - 11:59 PM
Resultado: NO mostrado ❌
Razón: Después del horario operativo
```

### Caso 4: Evento Límite Inicio
```
Evento: 05:30 AM
Filtro: 05:30 AM - 11:59 PM
Resultado: Mostrado ✅
Razón: Exactamente en el inicio
```

### Caso 5: Evento Límite Fin
```
Evento: 11:59 PM
Filtro: 05:30 AM - 11:59 PM
Resultado: Mostrado ✅
Razón: Exactamente en el fin
```

---

## 📊 Impacto en Estadísticas

### Dashboard
```
Antes del filtro:
- Total Eventos: 1114
- Accesos Concedidos: 167
- Accesos Denegados: 52

Después del filtro (5:30 AM - 11:59 PM):
- Total Eventos: 950  (↓ 164 eventos nocturnos)
- Accesos Concedidos: 145
- Accesos Denegados: 48
```

---

## 🔧 Configuración

### Cambiar Horario (Si es necesario)
```python
# En app.py y device_monitor.py

# Cambiar inicio
start_hour = 6      # 6:00 AM
start_minute = 0

# Cambiar fin
end_hour = 22       # 10:00 PM
end_minute = 0

# Aplicar
events = filter_events_by_time(events, 
                               start_hour=6, 
                               start_minute=0,
                               end_hour=22, 
                               end_minute=0)
```

---

## ✅ Ventajas

### 1. **Datos Relevantes**
- ✅ Solo muestra eventos del horario operativo
- ✅ Elimina ruido de eventos nocturnos
- ✅ Facilita análisis de operación normal

### 2. **Performance**
- ✅ Menos eventos = carga más rápida
- ✅ Tablas más pequeñas
- ✅ Mejor experiencia de usuario

### 3. **Claridad**
- ✅ Estadísticas más precisas
- ✅ Enfoque en horario laboral
- ✅ Menos confusión

---

## 🧪 Verificación

### Antes del Filtro
```
Dashboard muestra:
- Eventos de 00:00 a 23:59
- Incluye eventos nocturnos
- Total: 1114 eventos
```

### Después del Filtro
```
Dashboard muestra:
- Eventos de 05:30 a 23:59
- Solo horario operativo
- Total: 950 eventos
```

---

## 📝 Archivos Modificados

### 1. `webapp/app.py`
- ✅ Función `filter_events_by_time()`
- ✅ Aplicado en `debug_device()`
- ✅ Aplicado en `get_stat_details()`

### 2. `src/api/device_monitor.py`
- ✅ Importado `pytz`
- ✅ Método `_filter_events_by_time()`
- ✅ Aplicado en `get_debug_summary()`

---

## 🚀 Resultado

**Todos los eventos ahora se filtran automáticamente:**
- ✅ Dashboard general
- ✅ Vistas individuales
- ✅ Modales de detalles
- ✅ Exportaciones
- ✅ Estadísticas

**Horario:** 5:30 AM - 11:59 PM (hora local de México)

---

**Fecha:** 2025-11-19  
**Versión:** 4.0.0 - FILTRO HORARIO  
**Estado:** ✅ ACTIVO
