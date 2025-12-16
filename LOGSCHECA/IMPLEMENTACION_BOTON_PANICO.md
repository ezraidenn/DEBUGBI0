# 🚨 Botón de Pánico - Implementación

## 📊 Investigación de API de BioStar

### Endpoint correcto encontrado:
```
POST https://10.0.0.100/api/actions
```

### Estructura del payload:
```json
{
  "DeviceCollection": {
    "rows": [
      {
        "device_id": {"id": "544192911"},
        "action_type": "unlock_door"  // o "lock_door"
      }
    ]
  }
}
```

### Acciones disponibles:
| Acción | Descripción | Uso para pánico |
|--------|-------------|-----------------|
| `open_door` | Abre temporalmente (3-5 seg) | ❌ No sirve (temporal) |
| `unlock_door` | Desbloquea permanentemente | ✅ **ACTIVAR PÁNICO** |
| `lock_door` | Bloquea (modo normal) | ✅ **DESACTIVAR PÁNICO** |
| `release_door` | Modo libre (siempre abierta) | ⚠️ Alternativa |

### Dispositivos con puertas encontrados:
1. Anthea Principal 2 (ID: 544192911)
2. Club por Snack (ID: 544157116)
3. Golf (ID: 544140331)
4. Gym (ID: 544502684)
5. Lockers Hombres Planta Baja (ID: 544124814)
6. Oficinas Ekogolf (ID: 543728578)
7. TEST (ID: 543728576)
8. Recepcion (ID: 544125435)
9. Tenis (ID: 544140858)
10. Vestidor Hombres Por Snack (ID: 544125444)

---

## 🎯 Diseño del Botón de Pánico

### Características:
- ✅ **Individual por dispositivo** - Cada checador tiene su propio botón
- ✅ **Toggle ON/OFF** - Estado visual claro
- ✅ **Confirmación** - Modal de confirmación antes de activar
- ✅ **Estado persistente** - Se guarda en base de datos
- ✅ **Indicador visual** - Color rojo cuando está activo
- ✅ **Log de acciones** - Registra quién activó/desactivó y cuándo
- ✅ **Solo admin** - Solo usuarios admin pueden usar el botón

### Estados del botón:
```
🔒 NORMAL (OFF)
   - Color: Gris/Verde
   - Texto: "Activar Modo Pánico"
   - Acción: unlock_door

🚨 PÁNICO ACTIVO (ON)
   - Color: Rojo pulsante
   - Texto: "PÁNICO ACTIVO - Click para desactivar"
   - Acción: lock_door
```

---

## 🗄️ Base de Datos

### Nueva tabla: `panic_mode_status`
```sql
CREATE TABLE panic_mode_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL UNIQUE,
    device_name TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 0,
    activated_at DATETIME,
    activated_by_user_id INTEGER,
    deactivated_at DATETIME,
    deactivated_by_user_id INTEGER,
    last_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (activated_by_user_id) REFERENCES users(id),
    FOREIGN KEY (deactivated_by_user_id) REFERENCES users(id)
);
```

### Nueva tabla: `panic_mode_log`
```sql
CREATE TABLE panic_mode_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    device_name TEXT NOT NULL,
    action TEXT NOT NULL,  -- 'activate' o 'deactivate'
    user_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN NOT NULL DEFAULT 1,
    error_message TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## 🎨 UI/UX

### Ubicación del botón:
```
┌─────────────────────────────────────┐
│ 📱 Academia de Golf                 │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ 👥 Accesos hoy: 45                  │
│ 👤 Usuarios únicos: 32              │
│                                     │
│ [🚨 Modo Pánico]  [⚙️ Config]      │
└─────────────────────────────────────┘
```

### Modal de confirmación:
```
┌──────────────────────────────────────────┐
│  ⚠️ Confirmar Modo Pánico                │
├──────────────────────────────────────────┤
│                                          │
│  ¿Deseas ACTIVAR el modo pánico para:   │
│                                          │
│  📱 Academia de Golf                     │
│                                          │
│  Esto desbloqueará la puerta            │
│  permanentemente hasta que la           │
│  desactives manualmente.                │
│                                          │
│  [Cancelar]  [🚨 Activar Pánico]        │
└──────────────────────────────────────────┘
```

### Botón activo (pulsante):
```css
@keyframes pulse-red {
  0%, 100% { background-color: #dc3545; }
  50% { background-color: #ff4757; }
}

.panic-active {
  animation: pulse-red 1.5s infinite;
  box-shadow: 0 0 20px rgba(220, 53, 69, 0.6);
}
```

---

## 🔧 Implementación Backend

### Nuevo endpoint: `/api/panic-mode/<device_id>`
```python
@app.route('/api/panic-mode/<device_id>', methods=['POST'])
@login_required
def toggle_panic_mode(device_id):
    """
    Activa o desactiva el modo pánico para un dispositivo.
    Solo admin puede usar esta función.
    """
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    data = request.json
    action = data.get('action')  # 'activate' o 'deactivate'
    
    # Obtener estado actual
    status = PanicModeStatus.query.filter_by(device_id=device_id).first()
    
    if action == 'activate':
        # Llamar a BioStar API para desbloquear
        success = biostar_unlock_door(device_id)
        
        if success:
            if not status:
                status = PanicModeStatus(device_id=device_id)
            status.is_active = True
            status.activated_at = datetime.now()
            status.activated_by_user_id = current_user.id
            db.session.add(status)
            
            # Log
            log = PanicModeLog(
                device_id=device_id,
                action='activate',
                user_id=current_user.id,
                username=current_user.username
            )
            db.session.add(log)
            db.session.commit()
            
            return jsonify({'success': True, 'is_active': True})
    
    elif action == 'deactivate':
        # Llamar a BioStar API para bloquear
        success = biostar_lock_door(device_id)
        
        if success:
            if status:
                status.is_active = False
                status.deactivated_at = datetime.now()
                status.deactivated_by_user_id = current_user.id
                db.session.add(status)
            
            # Log
            log = PanicModeLog(
                device_id=device_id,
                action='deactivate',
                user_id=current_user.id,
                username=current_user.username
            )
            db.session.add(log)
            db.session.commit()
            
            return jsonify({'success': True, 'is_active': False})
    
    return jsonify({'success': False, 'message': 'Acción inválida'}), 400
```

### Funciones de control de BioStar:
```python
def biostar_unlock_door(device_id):
    """Desbloquea una puerta permanentemente."""
    try:
        monitor = DeviceMonitor(Config())
        if not monitor.login():
            return False
        
        url = f"{monitor.client.host}/api/actions"
        headers = {"bs-session-id": monitor.client.token}
        payload = {
            "DeviceCollection": {
                "rows": [
                    {
                        "device_id": {"id": str(device_id)},
                        "action_type": "unlock_door"
                    }
                ]
            }
        }
        
        response = monitor.client.session.post(
            url, json=payload, headers=headers, verify=False, timeout=10
        )
        
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error al desbloquear puerta: {e}")
        return False

def biostar_lock_door(device_id):
    """Bloquea una puerta (modo normal)."""
    try:
        monitor = DeviceMonitor(Config())
        if not monitor.login():
            return False
        
        url = f"{monitor.client.host}/api/actions"
        headers = {"bs-session-id": monitor.client.token}
        payload = {
            "DeviceCollection": {
                "rows": [
                    {
                        "device_id": {"id": str(device_id)},
                        "action_type": "lock_door"
                    }
                ]
            }
        }
        
        response = monitor.client.session.post(
            url, json=payload, headers=headers, verify=False, timeout=10
        )
        
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error al bloquear puerta: {e}")
        return False
```

---

## 🎨 Implementación Frontend

### HTML del botón:
```html
<button class="btn btn-panic" 
        data-device-id="{{ device.id }}"
        data-device-name="{{ device.name }}"
        data-panic-active="false"
        onclick="togglePanicMode(this)">
    <i class="bi bi-shield-exclamation"></i>
    <span class="panic-text">Modo Pánico</span>
</button>
```

### JavaScript:
```javascript
function togglePanicMode(button) {
    const deviceId = button.dataset.deviceId;
    const deviceName = button.dataset.deviceName;
    const isActive = button.dataset.panicActive === 'true';
    
    const action = isActive ? 'deactivate' : 'activate';
    const actionText = isActive ? 'DESACTIVAR' : 'ACTIVAR';
    
    // Mostrar modal de confirmación
    Swal.fire({
        title: `${actionText} Modo Pánico`,
        html: `
            <p>¿Deseas <strong>${actionText}</strong> el modo pánico para:</p>
            <p class="text-primary"><strong>${deviceName}</strong></p>
            <p class="text-muted">
                ${isActive 
                    ? 'Esto bloqueará la puerta y volverá al modo normal.' 
                    : 'Esto desbloqueará la puerta permanentemente.'}
            </p>
        `,
        icon: isActive ? 'question' : 'warning',
        showCancelButton: true,
        confirmButtonColor: isActive ? '#28a745' : '#dc3545',
        cancelButtonColor: '#6c757d',
        confirmButtonText: `${actionText}`,
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            executePanicAction(deviceId, deviceName, action, button);
        }
    });
}

function executePanicAction(deviceId, deviceName, action, button) {
    // Mostrar loading
    Swal.fire({
        title: 'Procesando...',
        text: 'Enviando comando al dispositivo',
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });
    
    fetch(`/api/panic-mode/${deviceId}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({action: action})
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            // Actualizar estado del botón
            button.dataset.panicActive = data.is_active;
            updatePanicButton(button, data.is_active);
            
            Swal.fire({
                icon: 'success',
                title: action === 'activate' ? '🚨 Modo Pánico Activado' : '✅ Modo Pánico Desactivado',
                text: `${deviceName}`,
                timer: 2000
            });
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: data.message || 'No se pudo ejecutar la acción'
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

function updatePanicButton(button, isActive) {
    const icon = button.querySelector('i');
    const text = button.querySelector('.panic-text');
    
    if (isActive) {
        button.classList.add('panic-active');
        button.classList.remove('btn-outline-danger');
        button.classList.add('btn-danger');
        icon.className = 'bi bi-exclamation-triangle-fill';
        text.textContent = 'PÁNICO ACTIVO';
    } else {
        button.classList.remove('panic-active');
        button.classList.remove('btn-danger');
        button.classList.add('btn-outline-danger');
        icon.className = 'bi bi-shield-exclamation';
        text.textContent = 'Modo Pánico';
    }
}
```

---

## ✅ Checklist de Implementación

- [ ] Crear modelos de base de datos
- [ ] Crear migración de base de datos
- [ ] Implementar funciones de control de BioStar
- [ ] Crear endpoint `/api/panic-mode/<device_id>`
- [ ] Agregar botón en dashboard de dispositivos
- [ ] Implementar JavaScript para toggle
- [ ] Agregar estilos CSS para animación
- [ ] Agregar permisos solo para admin
- [ ] Crear vista de logs de modo pánico
- [ ] Agregar notificaciones en tiempo real (opcional)
- [ ] Probar con dispositivo real
- [ ] Documentar uso para usuarios

---

## ⚠️ Consideraciones de Seguridad

1. **Solo admin** puede activar/desactivar
2. **Confirmación obligatoria** antes de activar
3. **Log completo** de todas las acciones
4. **Timeout de sesión** - Si admin cierra sesión, el pánico sigue activo
5. **Notificación** - Considerar enviar email/SMS cuando se activa
6. **Recuperación** - Si falla la desactivación, tener plan B

---

## 🚀 Próximos Pasos

1. Verificar permisos del usuario `rcetina` en BioStar
2. Implementar modelos de base de datos
3. Crear funciones de control
4. Implementar UI
5. Probar con dispositivo real
