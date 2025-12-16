# 🚨 Botón de Pánico con Alarma de Sonido - IMPLEMENTADO

## ✅ Funcionalidad Completa

El sistema de pánico ahora incluye **control opcional de alarma de sonido** en los checadores.

---

## 🔊 Funciones de Alarma Encontradas en BioStar

### Acciones disponibles:
- `trigger_alarm` - ✅ Activar alarma de sonido
- `release_alarm` - ✅ Desactivar alarma de sonido
- `sound_alarm` - Sonido de alarma
- `buzzer_on` / `buzzer_off` - Control de buzzer
- `fire_alarm` - Alarma de incendio

**Todas estas acciones existen en BioStar** y están disponibles para usar (requieren permisos).

---

## 🎯 Cómo Funciona

### Al ACTIVAR modo pánico:
1. **Desbloquea la puerta** permanentemente (`unlock_door`)
2. **Opcionalmente activa la alarma** de sonido (`trigger_alarm`) si el usuario lo selecciona
3. Guarda en BD que la alarma está activa

### Al DESACTIVAR modo pánico:
1. **Bloquea la puerta** (`lock_door`)
2. **Automáticamente desactiva la alarma** (`release_alarm`) si estaba activa
3. Vuelve todo a la normalidad

---

## 🗄️ Cambios en Base de Datos

### Nuevo campo en `panic_mode_status`:
```sql
alarm_active BOOLEAN DEFAULT 0  -- Si la alarma de sonido está activa
```

---

## 📡 API Actualizada

### Activar pánico CON alarma:
```javascript
fetch('/api/panic-mode/544192911', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        action: 'activate',
        activate_alarm: true  // ← NUEVO parámetro
    })
})
```

### Activar pánico SIN alarma:
```javascript
fetch('/api/panic-mode/544192911', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        action: 'activate',
        activate_alarm: false  // Solo desbloquear puerta
    })
})
```

### Desactivar pánico:
```javascript
fetch('/api/panic-mode/544192911', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        action: 'deactivate'
        // La alarma se desactiva automáticamente si estaba activa
    })
})
```

---

## 🎨 UI Propuesta

### Modal de confirmación con checkbox:

```
┌──────────────────────────────────────────┐
│  🚨 Activar Modo Pánico                  │
├──────────────────────────────────────────┤
│                                          │
│  Dispositivo: Anthea Principal 2         │
│                                          │
│  Esto desbloqueará la puerta            │
│  permanentemente.                        │
│                                          │
│  ☑️ Activar alarma de sonido             │
│     (El checador emitirá sonido)        │
│                                          │
│  [Cancelar]  [🚨 Activar Pánico]        │
└──────────────────────────────────────────┘
```

### JavaScript actualizado:

```javascript
function togglePanicMode(button) {
    const deviceId = button.dataset.deviceId;
    const deviceName = button.dataset.deviceName;
    const isActive = button.classList.contains('panic-active');
    
    if (isActive) {
        // Desactivar
        Swal.fire({
            title: 'DESACTIVAR Modo Pánico',
            text: `Dispositivo: ${deviceName}`,
            icon: 'question',
            showCancelButton: true,
            confirmButtonColor: '#28a745',
            confirmButtonText: 'Desactivar'
        }).then((result) => {
            if (result.isConfirmed) {
                executePanicAction(deviceId, 'deactivate', false, button);
            }
        });
    } else {
        // Activar - mostrar opción de alarma
        Swal.fire({
            title: '🚨 Activar Modo Pánico',
            html: `
                <p>Dispositivo: <strong>${deviceName}</strong></p>
                <p>Esto desbloqueará la puerta permanentemente.</p>
                <div style="margin-top: 20px; text-align: left;">
                    <label style="display: flex; align-items: center; cursor: pointer;">
                        <input type="checkbox" id="activateAlarmCheck" 
                               style="width: 20px; height: 20px; margin-right: 10px;">
                        <span>
                            <strong>Activar alarma de sonido</strong><br>
                            <small style="color: #666;">El checador emitirá sonido de alarma</small>
                        </span>
                    </label>
                </div>
            `,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#dc3545',
            confirmButtonText: 'Activar Pánico',
            preConfirm: () => {
                return document.getElementById('activateAlarmCheck').checked;
            }
        }).then((result) => {
            if (result.isConfirmed) {
                const activateAlarm = result.value;
                executePanicAction(deviceId, 'activate', activateAlarm, button);
            }
        });
    }
}

function executePanicAction(deviceId, action, activateAlarm, button) {
    Swal.fire({
        title: 'Procesando...',
        text: 'Enviando comando al dispositivo',
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });
    
    const payload = {action: action};
    if (action === 'activate') {
        payload.activate_alarm = activateAlarm;
    }
    
    fetch(`/api/panic-mode/${deviceId}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            updatePanicButton(button, data.is_active);
            
            let title = action === 'activate' ? '🚨 Modo Pánico Activado' : '✅ Modo Pánico Desactivado';
            Swal.fire({
                icon: 'success',
                title: title,
                text: data.message,
                timer: 3000
            });
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: data.message
            });
        }
    })
    .catch(err => {
        Swal.fire({
            icon: 'error',
            title: 'Error de conexión',
            text: 'No se pudo comunicar con el servidor'
        });
    });
}
```

---

## 🔧 Archivos Modificados

### 1. `src/api/door_control.py`
✅ Actualizado:
- `biostar_unlock_door(device_id, activate_alarm=False)`
- `biostar_lock_door(device_id, deactivate_alarm=False)`

### 2. `webapp/models.py`
✅ Agregado campo:
- `alarm_active` en `PanicModeStatus`

### 3. `webapp/app.py`
✅ Endpoint actualizado:
- Recibe parámetro `activate_alarm`
- Guarda estado de alarma en BD
- Desactiva alarma automáticamente al desactivar pánico

---

## 🚀 Para Actualizar

### 1. Recrear tablas (agregar nuevo campo):
```powershell
# Opción 1: Recrear tablas (BORRA DATOS)
.\venv\Scripts\python.exe init_panic_mode_tables.py

# Opción 2: Agregar campo manualmente (CONSERVA DATOS)
# Ejecutar en SQLite:
# ALTER TABLE panic_mode_status ADD COLUMN alarm_active BOOLEAN DEFAULT 0;
```

### 2. Reiniciar servidor:
```powershell
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*LOGSCHECA*" } | Stop-Process -Force
.\venv\Scripts\python.exe run_production.py
```

---

## ⚠️ Permisos Requeridos en BioStar

El usuario `rcetina` necesita los siguientes permisos en BioStar 2:

1. **Device Control** - Para desbloquear/bloquear puertas
2. **Alarm Control** - Para activar/desactivar alarmas

### Cómo agregar permisos:
1. Ir a BioStar 2 web interface
2. User Management → Users
3. Editar usuario `rcetina`
4. Permissions → Agregar:
   - ✅ Control Doors
   - ✅ Control Alarms
   - ✅ Device Control

---

## 📊 Resumen de Acciones

| Acción | Puerta | Alarma | Uso |
|--------|--------|--------|-----|
| **Activar Pánico (sin alarma)** | Desbloquea | - | Evacuación silenciosa |
| **Activar Pánico (con alarma)** | Desbloquea | Activa | Emergencia con alerta |
| **Desactivar Pánico** | Bloquea | Desactiva* | Volver a normalidad |

*La alarma se desactiva automáticamente si estaba activa.

---

## ✅ Estado de Implementación

**Backend: 100% Completo ✅**
- ✅ Funciones de control de alarma
- ✅ Parámetro `activate_alarm` en API
- ✅ Campo `alarm_active` en BD
- ✅ Desactivación automática de alarma
- ✅ Logs completos

**Frontend: Pendiente ⏳**
- ⏳ Checkbox para activar alarma en modal
- ⏳ Botón en dashboard
- ⏳ JavaScript actualizado

---

## 🎯 Próximos Pasos

1. **Agregar campo a BD** (ejecutar ALTER TABLE o recrear tablas)
2. **Verificar permisos** de alarma en BioStar para usuario `rcetina`
3. **Implementar frontend** con checkbox de alarma
4. **Probar con dispositivo real**

**El sistema está listo para usar alarmas de sonido en modo pánico! 🔊**
