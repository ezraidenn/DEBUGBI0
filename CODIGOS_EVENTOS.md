# 📋 Códigos de Eventos BioStar 2

Referencia completa de los códigos de eventos más comunes en BioStar 2.

## 🚪 Eventos de Acceso

| Código | Nombre | Descripción |
|--------|--------|-------------|
| 4864 | Access granted | ✅ Acceso concedido - Usuario autenticado correctamente |
| 4865 | Access denied | ❌ Acceso denegado - Credenciales inválidas o sin permisos |
| 4866 | Access granted (APB) | ✅ Acceso concedido con Anti-Passback |
| 4867 | Access denied (APB) | ❌ Acceso denegado por Anti-Passback |

## 🔐 Eventos de Autenticación

| Código | Nombre | Descripción |
|--------|--------|-------------|
| 4608 | Card only | Acceso solo con tarjeta |
| 4609 | Fingerprint only | Acceso solo con huella |
| 4610 | Card + Fingerprint | Acceso con tarjeta y huella |
| 4611 | Card + PIN | Acceso con tarjeta y PIN |
| 4612 | Fingerprint + PIN | Acceso con huella y PIN |

## 🚨 Eventos de Seguridad

| Código | Nombre | Descripción |
|--------|--------|-------------|
| 20736 | Forced door open | 🚨 Puerta forzada - Apertura sin autorización |
| 20737 | Door held open | ⚠️ Puerta abierta por mucho tiempo |
| 20738 | Exit button | Botón de salida presionado |
| 20739 | Door closed | Puerta cerrada normalmente |
| 20740 | Door open | Puerta abierta normalmente |

## 🔌 Eventos de Dispositivo

| Código | Nombre | Descripción |
|--------|--------|-------------|
| 28672 | Device connected | 🔌 Dispositivo conectado al servidor |
| 28673 | Device disconnected | 🔌 Dispositivo desconectado del servidor |
| 28674 | Device rebooted | 🔄 Dispositivo reiniciado |
| 28928 | Input activated | Entrada activada |
| 28929 | Input deactivated | Entrada desactivada |

## 👤 Eventos de Usuario

| Código | Nombre | Descripción |
|--------|--------|-------------|
| 12288 | User enrolled | Usuario registrado en el sistema |
| 12289 | User deleted | Usuario eliminado del sistema |
| 12290 | User updated | Información de usuario actualizada |
| 12544 | Fingerprint enrolled | Huella registrada |
| 12545 | Fingerprint deleted | Huella eliminada |
| 12800 | Card enrolled | Tarjeta registrada |
| 12801 | Card deleted | Tarjeta eliminada |

## ⏰ Eventos de Tiempo

| Código | Nombre | Descripción |
|--------|--------|-------------|
| 16384 | Time zone changed | Zona horaria modificada |
| 16385 | Daylight saving time | Horario de verano activado/desactivado |

## 🔧 Eventos de Sistema

| Código | Nombre | Descripción |
|--------|--------|-------------|
| 32768 | System started | Sistema iniciado |
| 32769 | System shutdown | Sistema apagado |
| 32770 | Backup started | Respaldo iniciado |
| 32771 | Backup completed | Respaldo completado |
| 32772 | Database backup | Respaldo de base de datos |

## 🔒 Eventos de Bloqueo

| Código | Nombre | Descripción |
|--------|--------|-------------|
| 24576 | Door locked | Puerta bloqueada |
| 24577 | Door unlocked | Puerta desbloqueada |
| 24578 | Door lock released | Bloqueo de puerta liberado |

## 📊 Uso en el Código

### Filtrar por tipo de evento

```python
from datetime import datetime, timedelta

# Obtener solo accesos concedidos
events = monitor.get_device_events_by_type(
    device_id=12345,
    event_codes=["4864"],  # Access granted
    start_date=datetime.now().replace(hour=0, minute=0),
    end_date=datetime.now()
)

# Obtener eventos de seguridad
security_events = monitor.get_device_events_by_type(
    device_id=12345,
    event_codes=["20736", "20737"],  # Forced door + Door held open
    start_date=datetime.now() - timedelta(days=7),
    end_date=datetime.now()
)
```

### Analizar eventos en DataFrame

```python
import pandas as pd

events = monitor.get_device_events_today(device_id=12345)
df = monitor.events_to_dataframe(events)

# Contar eventos por tipo
event_summary = df['event_code'].value_counts()
print(event_summary)

# Filtrar solo accesos denegados
denied = df[df['event_code'] == '4865']
print(f"Accesos denegados: {len(denied)}")
```

## 🔍 Debugging Común

### Problemas de Acceso
- **4865** (Access denied): Revisar permisos del usuario o validez de credenciales
- **4867** (APB denied): Verificar configuración de Anti-Passback

### Problemas de Seguridad
- **20736** (Forced door): Investigar intentos de acceso no autorizado
- **20737** (Door held open): Verificar si alguien está bloqueando la puerta

### Problemas de Conectividad
- **28673** (Device disconnected): Revisar conexión de red del dispositivo
- **28674** (Device rebooted): Verificar estabilidad del dispositivo

## 📚 Referencias

- [BioStar 2 API Documentation](https://bs2api.biostar2.com/)
- [Suprema Support](https://support.supremainc.com/)

---

**Nota**: Los códigos pueden variar según la versión de BioStar 2. Usa `client.get_event_types()` para obtener la lista completa de tu sistema.
