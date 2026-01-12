# 🔍 BioStar Logs Monitor - Sistema de Monitoreo en Tiempo Real

Sistema web profesional para monitoreo y análisis de eventos de checadores BioStar 2 con actualización en tiempo real y **seguridad nivel gobierno**.

## 🎯 Funcionalidades Principales

### Dashboard en Tiempo Real
- ✅ **Monitoreo automático** de todos los dispositivos
- ✅ **Actualización en tiempo real** via Server-Sent Events (SSE)
- ✅ **Carga lazy** - Dashboard instantáneo con datos asíncronos
- ✅ **Estadísticas globales** (eventos totales, concedidos, usuarios únicos)
- ✅ **Reconexión automática** en caso de pérdida de conexión

### Gestión de Dispositivos
- ✅ **Dashboard interactivo** con tarjetas de dispositivos
- ✅ **Vista detallada** por dispositivo con tabla de eventos
- ✅ **Aliases personalizados** para identificar dispositivos
- ✅ **Clasificación automática** de eventos (accesos, denegados, puertas, etc.)
- ✅ **Filtros avanzados** por tipo de evento y rango de tiempo

### Análisis y Reportes
- ✅ **Exportación a Excel** de eventos y reportes
- ✅ **Caché inteligente** para optimizar rendimiento
- ✅ **Logs detallados** para debugging
- ✅ **Zona horaria México** (America/Mexico_City)

### 🔐 Seguridad Nivel Gobierno
- ✅ **2FA con TOTP** (Google Authenticator)
- ✅ **CSRF Protection** con tokens
- ✅ **Session Fingerprinting** (IP + User-Agent)
- ✅ **Rate Limiting** contra fuerza bruta
- ✅ **Bloqueo de cuentas** (temporal y permanente)
- ✅ **Expiración de contraseñas** (90 días)
- ✅ **Historial de contraseñas** (no reusar últimas 5)
- ✅ **IP Whitelisting** para admins
- ✅ **Auditoría completa** de eventos de seguridad
- ✅ **Encriptación de datos** sensibles
- ✅ **Headers HTTP seguros** (CSP, HSTS, X-Frame-Options)

## 📁 Estructura del Proyecto

```
biostar-debug-monitor/
├── src/
│   ├── api/
│   │   ├── biostar_client.py      # Cliente API BioStar 2
│   │   └── device_monitor.py      # Monitor de dispositivos y eventos
│   └── utils/
│       ├── config.py              # Configuración centralizada
│       └── logger.py              # Sistema de logging
├── webapp/
│   ├── templates/
│   │   ├── base.html              # Template base
│   │   ├── dashboard.html         # Dashboard principal
│   │   ├── debug_device.html      # Vista detallada de dispositivo
│   │   └── debug_general.html     # Vista general de debug
│   ├── static/
│   │   └── css/
│   │       └── custom.css         # Estilos personalizados
│   ├── app.py                     # Aplicación Flask principal
│   ├── models.py                  # Modelos de base de datos
│   ├── realtime_sse.py            # Server-Sent Events para tiempo real
│   ├── cache_manager.py           # Gestión de caché
│   └── monitoring.py              # Monitoreo y métricas
├── config/
│   └── device_aliases.json        # Aliases personalizados de dispositivos
├── data/
│   └── outputs/                   # Reportes y exportaciones
├── instance/
│   └── biostar_debug.db           # Base de datos SQLite
├── tests/                         # Tests unitarios y de integración
├── .env                           # Variables de entorno (NO SUBIR)
├── .env.example                   # Plantilla de variables
├── .gitignore                     # Archivos ignorados por Git
├── requirements.txt               # Dependencias Python
├── run_webapp.py                  # Script de inicio
└── README.md                      # Este archivo
```

## 🚀 Instalación y Configuración

### Requisitos Previos
- Python 3.8 o superior
- Acceso a BioStar 2 API
- Navegador web moderno (Chrome, Firefox, Edge)

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
git clone https://github.com/ezraidenn/DEBUGBI0.git
cd DEBUGBI0
```

2. **Crear entorno virtual (recomendado)**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
# Copiar plantilla
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# Editar .env con tus credenciales
```

5. **Iniciar la aplicación**
```bash
python run_webapp.py
```

6. **Acceder al sistema**
```
URL: http://localhost:5000
Usuario: admin
Contraseña: admin123
```

## 🔧 Configuración

### Variables de Entorno (.env)

```env
# BioStar 2 API
BIOSTAR_HOST=https://10.0.0.100
BIOSTAR_USER=tu_usuario
BIOSTAR_PASSWORD=tu_password
```

### Aliases de Dispositivos (config/device_aliases.json)

```json
{
  "12345": {
    "alias": "Entrada Principal",
    "location": "Planta Baja",
    "notes": "Checador principal de acceso"
  },
  "67890": {
    "alias": "Salida Emergencia",
    "location": "Segundo Piso",
    "notes": "Checador de emergencia"
  }
}
```

## 📖 Uso del Sistema

### Dashboard Principal
1. **Acceder** a `http://localhost:5000/dashboard`
2. **Ver estadísticas globales** en tiempo real
3. **Monitorear cada dispositivo** con sus contadores individuales
4. **Hacer clic** en cualquier tarjeta para ver detalles

### Vista Detallada de Dispositivo
1. **Seleccionar dispositivo** desde el dashboard
2. **Ver tabla de eventos** en tiempo real
3. **Observar estadísticas** actualizarse automáticamente
4. **Volver al dashboard** con el botón "Volver"

### Características del Tiempo Real
- ✅ **Conexión automática** al cargar la página
- ✅ **Indicador de estado** (verde = conectado, rojo = desconectado)
- ✅ **Reconexión automática** cada 5 segundos si se pierde conexión
- ✅ **Actualización silenciosa** sin notificaciones molestas
- ✅ **Animaciones suaves** al actualizar contadores

### Gestión de Aliases
Editar `config/device_aliases.json`:
```json
{
  "544502684": {
    "alias": "Gym",
    "location": "Planta Baja",
    "notes": "Checador principal gimnasio"
  }
}
```

## 📊 Clasificación de Eventos

El sistema clasifica automáticamente los eventos en las siguientes categorías:

| Categoría | Códigos | Badge Color | Descripción |
|-----------|---------|-------------|-------------|
| **Acceso Concedido** | 4864, 4865 | Verde | Acceso exitoso |
| **Acceso Denegado** | 4866, 4867, 4868, 4869, 4870, 4871 | Rojo | Acceso rechazado |
| **Puerta Forzada** | 20736, 20737, 20738, 20739 | Amarillo | Alerta de seguridad |
| **Puerta Bloqueada** | 20740, 20741, 20742, 20743 | Cyan | Estado de puerta |
| **Puerta Abierta** | 20744, 20745, 20746, 20747 | Azul | Puerta abierta |
| **Puerta Cerrada** | 20748, 20749, 20750, 20751 | Gris | Puerta cerrada |

## 🔧 Tecnologías Utilizadas

- **Backend**: Flask (Python)
- **Frontend**: Bootstrap 5, JavaScript ES6
- **Tiempo Real**: Server-Sent Events (SSE)
- **Base de Datos**: SQLite
- **API**: BioStar 2 REST API
- **Caché**: Flask-Caching
- **Zona Horaria**: pytz (America/Mexico_City)

## 🔒 Seguridad Nivel Gobierno

### Características de Seguridad Implementadas

| Protección | Descripción | Configuración |
|------------|-------------|---------------|
| **2FA (TOTP)** | Autenticación de dos factores con Google Authenticator | `REQUIRE_2FA_FOR_ADMIN=true` |
| **CSRF Protection** | Tokens únicos por sesión | `CSRF_ENABLED=true` |
| **Session Fingerprint** | Validación de IP + User-Agent | `SESSION_FINGERPRINT=true` |
| **Rate Limiting** | 5 intentos/minuto, bloqueo 15 min | `LOGIN_MAX_ATTEMPTS=5` |
| **Bloqueo Permanente** | Después de 3 lockouts temporales | `PERMANENT_LOCKOUT_AFTER=3` |
| **Password Expiration** | Forzar cambio cada 90 días | `PASSWORD_MAX_AGE_DAYS=90` |
| **Password History** | No reusar últimas 5 contraseñas | `PASSWORD_HISTORY_COUNT=5` |
| **IP Whitelisting** | Restringir acceso por IP | `IP_WHITELIST_ENABLED=true` |
| **Auditoría** | Log de todos los eventos de seguridad | `SECURITY_AUDIT_LOG=true` |
| **Encriptación** | Datos sensibles encriptados | `ENCRYPT_SENSITIVE_DATA=true` |
| **HTTPS** | Forzar conexiones seguras | `FORCE_HTTPS=true` |

### Política de Contraseñas (Nivel Gobierno)
- Mínimo 12 caracteres
- Al menos 1 mayúscula
- Al menos 1 minúscula
- Al menos 1 número
- Al menos 1 carácter especial
- No reutilizar últimas 5 contraseñas
- Expiración cada 90 días

### Configuración de Seguridad (.env)
```env
# Seguridad
SECRET_KEY=tu-clave-secreta-64-caracteres
FLASK_ENV=production

# Sesiones
SESSION_LIFETIME_MINUTES=30
SESSION_INACTIVITY_TIMEOUT=15
SESSION_FINGERPRINT=true

# Rate Limiting
LOGIN_MAX_ATTEMPTS=5
LOGIN_LOCKOUT_MINUTES=15
PERMANENT_LOCKOUT_AFTER=3

# Contraseñas
PASSWORD_MIN_LENGTH=12
PASSWORD_MAX_AGE_DAYS=90
PASSWORD_HISTORY_COUNT=5

# 2FA
REQUIRE_2FA_FOR_ADMIN=true

# HTTPS
FORCE_HTTPS=true
```

### Resetear Contraseña de Admin
```bash
python reset_admin.py
```

### Logs de Auditoría
Los eventos de seguridad se registran en `logs/security_audit.log`:
- Intentos de login (exitosos y fallidos)
- Bloqueos de cuenta
- Cambios de contraseña
- Creación/edición/eliminación de usuarios
- Intentos de acceso no autorizado

## 🐛 Troubleshooting

### El servidor no inicia
```bash
# Verificar que el puerto 5000 esté libre
netstat -ano | findstr :5000  # Windows
lsof -i :5000                 # Linux/Mac

# Matar proceso si es necesario
taskkill /F /PID <PID>        # Windows
kill -9 <PID>                 # Linux/Mac
```

### No se conecta a BioStar
1. Verificar credenciales en `.env`
2. Verificar que el host sea accesible
3. Revisar logs en consola
4. Verificar certificados SSL

### El tiempo real no funciona
1. Hacer hard refresh (Ctrl+Shift+R)
2. Verificar consola del navegador (F12)
3. Verificar que SSE esté habilitado
4. Reiniciar el servidor

## 📝 Notas Técnicas

- **Zona Horaria**: Todos los eventos se convierten a America/Mexico_City
- **Límite API**: ~2000 eventos por petición
- **Intervalo SSE**: 2 segundos por defecto
- **Caché**: 5 minutos para dispositivos, 1 minuto para eventos
- **Heartbeat**: Cada 16 segundos para mantener conexión SSE

## 🚀 Despliegue en Producción

### Usando Gunicorn (Linux)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 webapp.app:app
```

### Usando Waitress (Windows)
```bash
pip install waitress
waitress-serve --host=0.0.0.0 --port=5000 webapp.app:app
```

### Variables de Entorno Producción
```env
FLASK_ENV=production
SECRET_KEY=tu-clave-secreta-muy-segura
```

## 📄 Licencia

Este proyecto es de uso interno. Todos los derechos reservados.

## 🆘 Soporte

Para más información:
- **BioStar 2 API**: [Documentación oficial](https://bs2api.biostar2.com/)
- **Flask**: [Documentación Flask](https://flask.palletsprojects.com/)
- **Server-Sent Events**: [MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
