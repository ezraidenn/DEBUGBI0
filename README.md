# 🔍 Debug BioStar - Monitor de Checadores

Sistema para monitoreo y debugging de checadores (dispositivos) de BioStar 2.

## 🎯 Funcionalidades

- ✅ Listar todos los checadores conectados
- ✅ Asignar nombres/alias personalizados a checadores
- ✅ Obtener logs y eventos del día de cada checador
- ✅ Monitorear estado de dispositivos en tiempo real
- ✅ Exportar reportes de debug a Excel
- ✅ Filtrar eventos por tipo (accesos, errores, etc.)

## 📁 Estructura del Proyecto

```
debug biostar para checadores/
├── src/
│   ├── api/
│   │   ├── biostar_client.py      # Cliente básico de API
│   │   └── device_monitor.py      # Monitor de dispositivos
│   ├── utils/
│   │   ├── config.py              # Configuración
│   │   └── logger.py              # Sistema de logs
│   └── main.py                    # Script principal
├── config/
│   └── device_aliases.json        # Nombres personalizados de checadores
├── data/
│   └── outputs/                   # Reportes generados
├── .env                           # Credenciales (NO SUBIR A GIT)
├── .env.example                   # Plantilla de credenciales
├── requirements.txt               # Dependencias
└── README.md                      # Este archivo
```

## 🚀 Instalación

1. **Clonar/Descargar el proyecto**

2. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

3. **Configurar credenciales**:
   - Copiar `.env.example` a `.env`
   - Editar `.env` con las credenciales reales

4. **Ejecutar**:
```bash
python src/main.py
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

## 📖 Uso Básico

### 1. Listar Todos los Checadores

```python
from src.api.device_monitor import DeviceMonitor

monitor = DeviceMonitor()
if monitor.login():
    devices = monitor.get_all_devices()
    for device in devices:
        print(f"{device['id']} - {device['name']}")
```

### 2. Obtener Logs del Día de un Checador

```python
# Obtener eventos de hoy
events = monitor.get_device_events_today(device_id=12345)
print(f"Eventos del día: {len(events)}")
```

### 3. Exportar Debug a Excel

```python
# Exportar todos los eventos del día
monitor.export_daily_debug(device_id=12345, filename="debug_checador_12345.xlsx")
```

## 🎨 Ejemplos de Uso

Ver carpeta `examples/` para scripts de ejemplo completos.

## 📊 Tipos de Eventos Comunes

| Código | Descripción |
|--------|-------------|
| 4864   | Acceso concedido |
| 4865   | Acceso denegado |
| 20736  | Puerta forzada |
| 28672  | Dispositivo conectado |
| 28673  | Dispositivo desconectado |

## 🔒 Seguridad

- **NO** subir el archivo `.env` a repositorios públicos
- Usar credenciales con permisos mínimos necesarios
- El SSL está deshabilitado para certificados autofirmados

## 📝 Notas

- Los eventos se obtienen en UTC
- La API tiene límite de ~2000 registros por petición
- Se recomienda hacer consultas por rangos de tiempo

## 🆘 Soporte

Para más información sobre la API de BioStar 2:
- [Documentación oficial](https://bs2api.biostar2.com/)
- [Guía de inicio](https://support.supremainc.com/en/support/solutions/articles/24000047041)
