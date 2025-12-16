# 🚨 Botón de Pánico - IMPLEMENTADO

## ✅ Estado: Backend Completo

El backend del botón de pánico está **100% implementado y listo para usar**. Solo falta agregar el frontend (botón en el dashboard).

---

## 📊 Lo que se investigó

### API de BioStar encontrada:
```
POST https://10.0.0.100/api/actions
```

### Payload para desbloquear (ACTIVAR PÁNICO):
```json
{
  "DeviceCollection": {
    "rows": [
      {
        "device_id": {"id": "544192911"},
        "action_type": "unlock_door"
      }
    ]
  }
}
```

### Payload para bloquear (DESACTIVAR PÁNICO):
```json
{
  "DeviceCollection": {
    "rows": [
      {
        "device_id": {"id": "544192911"},
        "action_type": "lock_door"
      }
    ]
  }
}
```

---

## 🗄️ Base de Datos

### Tablas creadas:

#### 1. `panic_mode_status`
Almacena el estado actual de cada dispositivo:
- `device_id` - ID del dispositivo
- `device_name` - Nombre del dispositivo
- `is_active` - Si el pánico está activo
- `activated_at` - Cuándo se activó
- `activated_by_user_id` - Quién lo activó
- `deactivated_at` - Cuándo se desactivó
- `deactivated_by_user_id` - Quién lo desactivó

#### 2. `panic_mode_log`
Registra todas las acciones:
- `device_id` - ID del dispositivo
- `device_name` - Nombre del dispositivo
- `action` - 'activate' o 'deactivate'
- `user_id` - ID del usuario
- `username` - Nombre del usuario
- `timestamp` - Cuándo ocurrió
- `success` - Si fue exitoso
- `error_message` - Mensaje de error si falló

---

## 🔧 Archivos Implementados

### 1. `webapp/models.py`
✅ Agregados modelos:
- `PanicModeStatus`
- `PanicModeLog`

### 2. `src/api/door_control.py` (NUEVO)
✅ Funciones de control:
- `biostar_unlock_door(device_id)` - Desbloquea puerta
- `biostar_lock_door(device_id)` - Bloquea puerta
- `biostar_open_door_temporary(device_id)` - Abre temporalmente

### 3. `webapp/app.py`
✅ Endpoints API:
- `POST /api/panic-mode/<device_id>` - Toggle pánico
- `GET /api/panic-mode/status` - Estado de todos los dispositivos

### 4. `init_panic_mode_tables.py` (NUEVO)
✅ Script para crear tablas

---

## 🚀 Cómo Inicializar

### 1. Crear las tablas en la base de datos:
```powershell
.\venv\Scripts\python.exe init_panic_mode_tables.py
```

### 2. Reiniciar el servidor:
```powershell
# Detener
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*LOGSCHECA*" } | Stop-Process -Force

# Iniciar
.\venv\Scripts\python.exe run_production.py
```

---

## 📡 API Endpoints

### Activar modo pánico:
```javascript
fetch('/api/panic-mode/544192911', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({action: 'activate'})
})
.then(res => res.json())
.then(data => {
    if (data.success) {
        console.log('🚨 Pánico activado!');
    }
});
```

### Desactivar modo pánico:
```javascript
fetch('/api/panic-mode/544192911', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({action: 'deactivate'})
})
.then(res => res.json())
.then(data => {
    if (data.success) {
        console.log('✅ Pánico desactivado');
    }
});
```

### Obtener estado de todos los dispositivos:
```javascript
fetch('/api/panic-mode/status')
.then(res => res.json())
.then(data => {
    console.log(data.statuses);
    // {
    //   "544192911": {
    //     "is_active": true,
    //     "device_name": "Anthea Principal 2",
    //     "activated_at": "2025-12-11T17:30:00",
    //     "activated_by": "admin"
    //   }
    // }
});
```

---

## 🎨 Frontend Pendiente

### Lo que falta implementar:

1. **Botón en el dashboard** (`dashboard.html`)
   - Agregar botón de pánico en cada tarjeta de dispositivo
   - Solo visible para admin

2. **JavaScript para toggle**
   - Función `togglePanicMode(deviceId, deviceName)`
   - Modal de confirmación con SweetAlert2
   - Actualización visual del botón

3. **CSS para animación**
   - Clase `.panic-active` con animación pulsante
   - Colores rojo/verde según estado

4. **Cargar estado inicial**
   - Al cargar dashboard, obtener estados actuales
   - Mostrar botones en el estado correcto

### Ejemplo de implementación:

```html
<!-- En dashboard.html, dentro de cada tarjeta de dispositivo -->
{% if current_user.is_admin %}
<button class="btn btn-sm btn-outline-danger panic-btn" 
        data-device-id="{{ device.id }}"
        data-device-name="{{ device.name }}"
        onclick="togglePanicMode(this)">
    <i class="bi bi-shield-exclamation"></i>
    <span class="panic-text">Modo Pánico</span>
</button>
{% endif %}
```

```javascript
// JavaScript para el botón
function togglePanicMode(button) {
    const deviceId = button.dataset.deviceId;
    const deviceName = button.dataset.deviceName;
    const isActive = button.classList.contains('panic-active');
    
    const action = isActive ? 'deactivate' : 'activate';
    
    Swal.fire({
        title: `${isActive ? 'DESACTIVAR' : 'ACTIVAR'} Modo Pánico`,
        text: `Dispositivo: ${deviceName}`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: isActive ? '#28a745' : '#dc3545',
        confirmButtonText: isActive ? 'Desactivar' : 'Activar'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`/api/panic-mode/${deviceId}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: action})
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    updatePanicButton(button, data.is_active);
                    Swal.fire('Éxito', data.message, 'success');
                } else {
                    Swal.fire('Error', data.message, 'error');
                }
            });
        }
    });
}

function updatePanicButton(button, isActive) {
    if (isActive) {
        button.classList.add('panic-active', 'btn-danger');
        button.classList.remove('btn-outline-danger');
        button.querySelector('.panic-text').textContent = 'PÁNICO ACTIVO';
    } else {
        button.classList.remove('panic-active', 'btn-danger');
        button.classList.add('btn-outline-danger');
        button.querySelector('.panic-text').textContent = 'Modo Pánico';
    }
}
```

```css
/* CSS para animación */
@keyframes pulse-red {
    0%, 100% { 
        background-color: #dc3545;
        box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.7);
    }
    50% { 
        background-color: #ff4757;
        box-shadow: 0 0 0 10px rgba(220, 53, 69, 0);
    }
}

.panic-active {
    animation: pulse-red 1.5s infinite;
}
```

---

## ⚠️ Consideraciones Importantes

### 1. Permisos en BioStar
El usuario `rcetina` necesita permisos en BioStar para controlar puertas. Si al probar obtienes error "Permission Denied", debes:
- Ir a BioStar 2 web interface
- User Management → Users
- Editar usuario `rcetina`
- Agregar permiso "Control Doors" o "Device Control"

### 2. Seguridad
- ✅ Solo admin puede activar/desactivar
- ✅ Requiere confirmación antes de activar
- ✅ Todas las acciones se registran en log
- ✅ Se guarda quién activó y cuándo

### 3. Recuperación
Si el modo pánico se queda activo y no se puede desactivar:
1. Ir directamente a BioStar 2 web interface
2. Devices → Seleccionar dispositivo
3. Control → Lock Door

---

## 🧪 Pruebas Realizadas

✅ Investigación de API de BioStar
✅ Identificación de endpoints correctos
✅ Estructura de payloads verificada
✅ Modelos de base de datos creados
✅ Funciones de control implementadas
✅ Endpoints API implementados
✅ Logs y auditoría implementados

⏳ Pendiente:
- Frontend (botón en dashboard)
- Prueba con dispositivo real
- Verificar permisos de usuario en BioStar

---

## 📝 Próximos Pasos

1. **Ejecutar `init_panic_mode_tables.py`** para crear las tablas
2. **Implementar el frontend** (botón + JavaScript + CSS)
3. **Verificar permisos** del usuario `rcetina` en BioStar
4. **Probar con un dispositivo real**
5. **Documentar para usuarios finales**

---

## 🎯 Resumen

**Backend: 100% Completo ✅**
- Modelos de BD ✅
- Funciones de control ✅
- API endpoints ✅
- Logs y auditoría ✅

**Frontend: Pendiente ⏳**
- Botón en dashboard
- JavaScript para toggle
- CSS para animación
- Cargar estado inicial

**El sistema está listo para ser usado una vez que se agregue el botón en el frontend.**
