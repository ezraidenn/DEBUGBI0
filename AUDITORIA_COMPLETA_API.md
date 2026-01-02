# Auditoría Completa de APIs y Rutas

## 📋 DASHBOARD.HTML

### ✅ Rutas API Correctas:
1. `/api/dashboard-data` - ✅ Existe en app.py línea 630
2. `/api/unique-users` - ✅ Existe en app.py línea 465 (llamada 3 veces)
3. `/api/clear-all-cache` - ✅ Existe en app.py línea 941
4. `/stream/all-devices?interval=3` - ✅ Existe en app.py línea 1398

### ⚠️ Observaciones:
- `/api/unique-users` se llama **3 veces** en diferentes funciones:
  - `loadUniqueUsersCount()` - línea 527
  - `loadUniqueUsers()` - línea 574
  - `refreshUsersInBackground()` - línea 603
  - **ESTO ES CORRECTO** - diferentes contextos de uso

---

## 📋 DEBUG_DEVICE.HTML

### ✅ Rutas API Correctas:
1. `/stream/device/${deviceId}?interval=2` - ✅ Existe en app.py línea 1376
2. `/debug/device/${deviceId}/clear-cache` - ❓ NECESITA VERIFICACIÓN
3. `/api/device/${deviceId}/stat/${statType}` - ✅ Existe en app.py línea 977

### ❌ Rutas que NECESITAN VERIFICACIÓN:
- `/debug/device/${deviceId}/clear-cache` - No encontrada en grep inicial

---

## 📋 DEBUG_GENERAL.HTML

### ✅ Rutas API Correctas:
1. `/debug/device/${deviceId}/export` - ❓ NECESITA VERIFICACIÓN

---

## 📋 EMERGENCY_CONFIG.HTML (Ya corregidas anteriormente)

### ✅ Rutas API Correctas (con prefijo /emergency/):
1. `/emergency/api/zones` - ✅
2. `/emergency/api/zones/${id}/groups` - ✅
3. `/emergency/api/zones/${id}/devices` - ✅
4. `/emergency/api/groups/${id}/members` - ✅
5. `/emergency/api/users/all` - ✅

---

## 📋 EMERGENCY_CENTER.HTML (Ya corregidas anteriormente)

### ✅ Rutas API Correctas (con prefijo /emergency/):
1. `/emergency/api/emergency/activate` - ✅
2. `/emergency/api/emergency/${id}/roll-call` - ✅
3. `/emergency/api/emergency/${id}/resolve` - ✅
4. `/emergency/stream/emergency/${id}` - ✅
5. `/emergency/api/roll-call/${id}/mark` - ✅

---

## 🔍 RUTAS VERIFICADAS:

1. `/debug/device/${deviceId}/clear-cache` (POST) - ✅ Existe en app.py línea 907
2. `/debug/device/${deviceId}/export` (GET) - ✅ Existe en app.py línea 888

## ❌ RUTAS CON PROBLEMAS:

1. `/api/users/search?q=` - ❌ NO EXISTE en app.py (llamada en emergency_config.html línea 590)
2. `/api/areas/${areaId}/devices` - ❓ NECESITA VERIFICACIÓN (llamada en config_areas.html línea 374)

---

## 📊 RESUMEN:

### ✅ CORRECTO:
- Dashboard: Todas las rutas existen y son correctas
- Debug Device: Rutas de clear-cache y export existen
- Emergencias: Todas las rutas corregidas con prefijo `/emergency/`
- SSE: Rutas de tiempo real correctas con parámetros:
  - `/stream/device/{id}?interval=2` ✅
  - `/stream/all-devices?interval=3` ✅

### ❌ PROBLEMAS ENCONTRADOS:
1. **emergency_config.html línea 590**: Llama a `/api/users/search?q=` que NO EXISTE
   - Debería usar `/emergency/api/users/all` y filtrar localmente
2. **config_areas.html línea 374**: Llama a `/api/areas/${areaId}/devices` - necesita verificación

### 📝 OBSERVACIONES:
- `/api/unique-users` se llama 3 veces en dashboard.html (CORRECTO - diferentes contextos)
- Todos los intervalos de SSE son apropiados (2-3 segundos)

---

## 🔧 ACCIONES NECESARIAS:
1. ✅ Verificar rutas de debug individual - COMPLETADO
2. ❌ Corregir ruta `/api/users/search` en emergency_config.html
3. ❓ Verificar ruta `/api/areas/${areaId}/devices` en config_areas.html
4. ✅ Verificar parámetros de SSE - COMPLETADO
5. ⏳ Buscar duplicados de código - EN PROCESO
