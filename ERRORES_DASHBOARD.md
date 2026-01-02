# Errores Identificados en Dashboard

## 📊 Análisis de Errores en Dashboard

### 1. **Problema: Contadores no se actualizan correctamente**

#### **Error en carga inicial:**
- `dashboard.html` línea 224: `fetch('/api/dashboard-data')` - **FALTA PREFIJO**
- `dashboard.html` línea 482: `fetch('/api/unique-users')` - **FALTA PREFIJO**
- `dashboard.html` línea 516: `fetch('/api/unique-users')` - **FALTA PREFIJO**
- `dashboard.html` línea 545: `fetch('/api/unique-users')` - **FALTA PREFIJO**

**PROBLEMA:** Las rutas `/api/dashboard-data` y `/api/unique-users` NO tienen prefijo `/emergency/` pero están en `app.py` sin blueprint, por lo que deberían funcionar. Sin embargo, si hay un problema de routing, estas rutas pueden no estar respondiendo correctamente.

#### **Error en SSE (Server-Sent Events):**
- `dashboard.html` línea 338: `new EventSource('/stream/all-devices?interval=3')` - **FALTA VERIFICAR SI EXISTE**

### 2. **Problema: Suma de accesos incorrecta**

**Ubicación:** `dashboard.html` líneas 405-419

```javascript
function updateHeaderTotals() {
    // Sumar accesos de todas las tarjetas
    let totalAccesos = 0;
    document.querySelectorAll('.device-card .device-stat:first-child strong').forEach(el => {
        totalAccesos += parseInt(el.textContent || 0);
    });
    
    // Actualizar accesos en el header
    const statAccesos = document.getElementById('statAccesos');
    if (statAccesos) statAccesos.textContent = totalAccesos;
    
    // Actualizar usuarios únicos en tiempo real
    const statUsuarios = document.getElementById('statUsuarios');
    if (statUsuarios) statUsuarios.textContent = allUserIds.size;
}
```

**PROBLEMA:** Esta función suma los accesos de las tarjetas de dispositivos, pero si las tarjetas no se han cargado correctamente o si hay errores en el renderizado, la suma será incorrecta.

### 3. **Problema: Usuarios únicos no se cuentan correctamente**

**Ubicación:** `dashboard.html` líneas 372-383

```javascript
// 2. Agregar usuario al set global Y actualizar contador
if (event.user_id) {
    const userId = String(event.user_id);
    const isNewUser = !allUserIds.has(userId);
    allUserIds.add(userId);
    
    // Actualizar contador de usuarios únicos en tiempo real
    if (isNewUser) {
        const statUsuarios = document.getElementById('statUsuarios');
        if (statUsuarios) {
            statUsuarios.textContent = allUserIds.size;
        }
    }
    
    // 3. Actualizar cache de usuarios para el modal
    updateUsersCache(event, deviceId);
}
```

**PROBLEMA:** El Set `allUserIds` se inicializa vacío al cargar la página. Solo se llena cuando:
1. Se cargan usuarios desde `/api/unique-users` (línea 531)
2. Llegan eventos nuevos en tiempo real

Si la carga inicial falla, el contador será 0 o incorrecto.

### 4. **Problema: Agrupación de dispositivos por tipo**

**Ubicación:** `dashboard.html` líneas 258-315

La función `renderDevices()` agrupa dispositivos por tipo, pero:
- Depende de que `device.device_type` esté definido
- Si `device.device_type` es `null` o `undefined`, usa 'checador' por defecto
- Puede causar agrupaciones incorrectas

### 5. **Problema: Tiempo real (SSE) puede no estar funcionando**

**Ubicación:** `dashboard.html` línea 338

```javascript
dashboardEventSource = new EventSource('/stream/all-devices?interval=3');
```

**NECESITA VERIFICAR:** ¿Existe la ruta `/stream/all-devices` en `app.py`?

---

## 🔧 Correcciones Necesarias:

1. ✅ Verificar que las rutas `/api/dashboard-data` y `/api/unique-users` existan y funcionen
2. ✅ Verificar que la ruta `/stream/all-devices` exista para SSE
3. ✅ Asegurar que `allUserIds` se inicialice correctamente con los usuarios del día
4. ✅ Verificar que la suma de accesos se calcule correctamente
5. ✅ Revisar la lógica de agrupación de dispositivos

---

## 📝 Próximos pasos:

1. Verificar rutas en `app.py`
2. Probar carga de datos del dashboard
3. Verificar SSE en consola del navegador
4. Corregir errores encontrados
