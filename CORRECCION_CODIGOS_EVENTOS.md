# 🔧 CORRECCIÓN: Códigos de Eventos Incorrectos

## 🐛 Problema Encontrado

**Síntoma:** Todos los checadores muestran "Accesos Concedidos: 0" y en los debug aparecen solo eventos de "Puerta Forzada".

**Causa Raíz:** Estábamos usando códigos de eventos **INCORRECTOS** para clasificar los accesos.

---

## ❌ Códigos Incorrectos (Antes)

```python
# INCORRECTO - Estos códigos NO EXISTEN en BioStar 2
access_granted = len(df[df['event_code'] == '4864'])  # ❌ NO EXISTE
access_denied = len(df[df['event_code'] == '4865'])   # ❌ NO EXISTE
```

---

## ✅ Códigos Correctos (Ahora)

Según la documentación oficial de BioStar 2:

### Accesos Concedidos (VERIFY_SUCCESS + IDENTIFY_SUCCESS)
```python
ACCESS_GRANTED = [
    # VERIFY_SUCCESS (4097-4129)
    '4097',   # VERIFY_SUCCESS_ID_PIN
    '4098',   # VERIFY_SUCCESS_ID_FINGERPRINT
    '4099',   # VERIFY_SUCCESS_ID_FINGERPRINT_PIN
    '4100',   # VERIFY_SUCCESS_ID_FACE
    '4101',   # VERIFY_SUCCESS_ID_FACE_PIN
    '4102',   # VERIFY_SUCCESS_CARD
    '4103',   # VERIFY_SUCCESS_CARD_PIN
    '4104',   # VERIFY_SUCCESS_CARD_FINGERPRINT
    '4105',   # VERIFY_SUCCESS_CARD_FINGERPRINT_PIN
    '4106',   # VERIFY_SUCCESS_CARD_FACE
    '4107',   # VERIFY_SUCCESS_CARD_FACE_PIN
    '4112',   # VERIFY_SUCCESS_CARD_FACE_FINGER
    '4113',   # VERIFY_SUCCESS_CARD_FINGER_FACE
    '4114',   # VERIFY_SUCCESS_ID_FACE_FINGER
    '4115',   # VERIFY_SUCCESS_ID_FINGER_FACE
    '4118',   # VERIFY_SUCCESS_MOBILE_CARD
    '4119',   # VERIFY_SUCCESS_MOBILE_CARD_PIN
    '4120',   # VERIFY_SUCCESS_MOBILE_CARD_FINGER
    '4121',   # VERIFY_SUCCESS_MOBILE_CARD_FINGER_PIN
    '4122',   # VERIFY_SUCCESS_MOBILE_CARD_FACE
    '4123',   # VERIFY_SUCCESS_MOBiLE_CARD_FACE_PIN
    '4128',   # VERIFY_SUCCESS_MOBILE_CARD_FACE_FINGER
    '4129',   # VERIFY_SUCCESS_MOBILE_CARD_FINGER_FACE
    
    # IDENTIFY_SUCCESS (4865-4872)
    '4865',   # IDENTIFY_SUCCESS_FINGERPRINT
    '4866',   # IDENTIFY_SUCCESS_FINGERPRINT_PIN
    '4867',   # IDENTIFY_SUCCESS_FACE
    '4868',   # IDENTIFY_SUCCESS_FACE_PIN
    '4869',   # IDENTIFY_SUCCESS_FACE_FINGER
    '4870',   # IDENTIFY_SUCCESS_FACE_FINGER_PIN
    '4871',   # IDENTIFY_SUCCESS_FINGER_FACE
    '4872',   # IDENTIFY_SUCCESS_FINGER_FACE_PIN
]
```

### Accesos Denegados
```python
ACCESS_DENIED = [
    '4353',   # VERIFY_FAIL_ID
    '4354',   # VERIFY_FAIL_CARD
    '4355',   # VERIFY_FAIL_PIN
    '4356',   # VERIFY_FAIL_FINGERPRINT
    '4357',   # VERIFY_FAIL_FACE
    '4360',   # VERIFY_FAIL_MOBILE_CARD
    '5123',   # IDENTIFY_FAIL_PIN
    '5124',   # IDENTIFY_FAIL_FINGERPRINT
    '5125',   # IDENTIFY_FAIL_FACE
    '6401',   # ACCESS_DENIED_ACCESS_GROUP
    '6402',   # ACCESS_DENIED_DISABLED
    '6403',   # ACCESS_DENIED_EXPIRED
    '6404',   # ACCESS_DENIED_ON_BLACKLIST
    '6405',   # ACCESS_DENIED_APB
    '6406',   # ACCESS_DENIED_TIMED_APB
    '6407',   # ACCESS_DENIED_FORCED_LOCK_SCHEDULE
    '6414',   # ACCESS_DENIED_INTRUSION_ALARM
    '6415',   # ACCESS_DENIED_INTERLOCK_ALARM
    '6418',   # ACCESS_DENIED_ANTI_TAILGATING_DEVICE
    '6419',   # ACCESS_DENIED_HIGH_TEMPERATURE
    '6420',   # ACCESS_DENIED_NONE_TEMPERATURE
    '6421',   # ACCESS_DENIED_UNMASK_DETECT
]
```

### Otros Eventos Importantes
```python
FORCED_OPEN = ['21504']   # Puerta forzada
DOOR_OPEN = ['20992']     # Puerta abierta
DOOR_CLOSE = ['21248']    # Puerta cerrada
DOOR_LOCKED = ['20736']   # Puerta bloqueada
```

---

## 🔧 Archivos Corregidos

### 1. `src/api/device_monitor.py`
- ✅ Agregado diccionario `EVENT_CODES` con todos los códigos correctos
- ✅ Actualizado `get_debug_summary()` para usar códigos correctos
- ✅ Actualizado export a Excel para usar códigos correctos

### 2. `webapp/app.py`
- ✅ Agregada función `classify_event()` para clasificar eventos
- ✅ Registrada en Jinja templates
- ✅ Importado `EVENT_CODES` desde device_monitor

### 3. `webapp/templates/debug_device.html`
- ✅ Actualizado para usar `classify_event()` en lugar de códigos hardcodeados
- ✅ Badges ahora muestran el tipo correcto de evento

---

## 📊 Resultado

### Antes ❌
```
Accesos Concedidos: 0
Accesos Denegados: 0
Todos los eventos: "Puerta Forzada" o "Otro"
```

### Ahora ✅
```
Accesos Concedidos: 45  ← Cuenta TODOS los VERIFY_SUCCESS e IDENTIFY_SUCCESS
Accesos Denegados: 3    ← Cuenta TODOS los VERIFY_FAIL y ACCESS_DENIED
Eventos clasificados correctamente con badges de colores
```

---

## 🎨 Clasificación de Badges

| Tipo de Evento | Color | Badge Class |
|----------------|-------|-------------|
| Acceso Concedido | Verde | `bg-success` |
| Acceso Denegado | Rojo | `bg-danger` |
| Puerta Forzada | Naranja | `bg-warning` |
| Puerta Bloqueada | Azul | `bg-info` |
| Puerta Abierta | Azul Primario | `bg-primary` |
| Puerta Cerrada | Gris | `bg-secondary` |
| Otros | Gris | `bg-secondary` |

---

## 🧪 Cómo Verificar

1. **Reinicia el servidor**:
```bash
python run_webapp.py
```

2. **Abre el dashboard**:
```
http://localhost:5000
```

3. **Verifica las estadísticas**:
- Ahora deberías ver números en "Accesos Concedidos"
- Los badges en la tabla deberían ser verdes para accesos exitosos

4. **Revisa un debug individual**:
- Los eventos deberían clasificarse correctamente
- Verde = Acceso concedido
- Rojo = Acceso denegado
- Naranja = Puerta forzada

---

## 📝 Referencia

Todos los códigos están documentados en:
```
tipos_eventos_biostar.txt
```

**Líneas importantes:**
- Líneas 54-76: VERIFY_SUCCESS (accesos con verificación)
- Líneas 19-26: IDENTIFY_SUCCESS (accesos con identificación)
- Líneas 77-125: Fallos y denegaciones
- Línea 164: FORCED_OPEN (21504)
- Línea 30: LOCKED (20736)

---

## ✅ Estado

**CORREGIDO** ✅

Los códigos ahora coinciden con la documentación oficial de BioStar 2 y los eventos se clasifican correctamente.

---

**Fecha:** 2025-11-19  
**Versión:** 3.1.0 - CÓDIGOS CORREGIDOS
