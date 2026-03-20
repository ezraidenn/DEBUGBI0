# Sistema de Gestión de Personal y Emergencias

Sistema integral para control de asistencia, gestión de incidencias de personal (MovPer) y control de emergencias con integración a dispositivos BioStar.

## Funcionalidades Principales

### MovPer - Movimiento de Personal
- **Control de asistencia**: Registro automático de checadas BioStar
- **Clasificación inteligente**: Detección de retardos, faltas, salidas tempranas
- **Justificación manual**: Toggle switches para retardos y salidas
- **Formatos Excel**: Generación de F-RH-18 y Aviso de Vacaciones
- **Dashboard grupal**: Vista por jefe con resumen de equipo
- **Configuración personal**: Horarios, tolerancias, datos personales

### Sistema de Emergencia
- **Modo Pánico**: Activación remota de desbloqueo de puertas
- **Control de Acceso**: Apertura remota de dispositivos
- **Monitoreo en Tiempo Real**: Estado actual de dispositivos via SSE
- **Roll Call**: Pase de lista durante emergencias
- **Gestión de Zonas**: Organización por áreas físicas

### Seguridad y Auditoría
- **Autenticación robusta**: Session-based con decoradores
- **Control de acceso**: Roles de usuario (admin/empleado)
- **Auditoría completa**: Registro de todas las acciones
- **Validaciones**: Input sanitization y protección CSRF

## Estructura del Proyecto

```
DEBUGBI0/
├── webapp/                        # Aplicación Flask principal
│   ├── app.py                     # Configuración principal
│   ├── models.py                  # Modelos SQLAlchemy
│   ├── mobper_routes.py           # Rutas de MovPer
│   ├── mobper_excel.py            # Generación de Excel
│   ├── emergency_routes.py        # Sistema de emergencia
│   ├── security.py                # Utilidades de seguridad
│   ├── cache_manager.py           # Gestión de caché
│   ├── monitoring.py              # Monitoreo y métricas
│   ├── realtime_*.py              # WebSockets y eventos
│   └── templates/                 # Plantillas Jinja2
│       ├── mobper_*.html          # Vistas de MovPer
│       ├── panic_*.html           # Interfaz de emergencia
│       └── excel_*.html           # Pruebas de Excel
├── src/                           # Módulos de integración
│   ├── api/                       # Clientes API externos
│   │   ├── biostar_client.py      # Cliente BioStar
│   │   ├── door_control.py        # Control de puertas
│   │   └── device_monitor.py      # Monitor de dispositivos
│   └── utils/                     # Utilidades compartidas
│       ├── config.py              # Configuración
│       └── logger.py              # Logging
├── tests/                         # Suite de pruebas
├── instance/                      # Base de datos SQLite
├── venv/                          # Entorno virtual
├── .env                           # Variables de entorno
├── requirements.txt                # Dependencias Python
├── ARCHITECTURE.md                # Documentación de arquitectura
├── DATA_DICTIONARY.md             # Diccionario de datos
└── README.md                      # Este archivo
```

## Instalación y Configuración

### Requisitos Previos
- Python 3.9 o superior
- Acceso a BioStar 2 API
- Microsoft Office (para generación de Excel)

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd DEBUGBI0
```

2. **Crear entorno virtual**
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
```

5. **Iniciar la aplicación**
```bash
# Desde el directorio webapp
python app.py
```

6. **Acceder al sistema**
```
MovPer: http://localhost:5000/mobper
Emergencia: http://localhost:5000/emergency
```

## Configuración

### Variables de Entorno (.env)

```env
# BioStar 2 API
BIOSTAR_HOST=https://10.0.0.100
BIOSTAR_USER=tu_usuario
BIOSTAR_PASSWORD=tu_password

# Flask
SECRET_KEY=tu-clave-secreta
FLASK_ENV=development
```

## Uso del Sistema

### MovPer
1. **Acceder** a `/mobper/login`
2. **Ver checklist** de la quincena actual
3. **Clasificar faltas** usando el dropdown
4. **Justificar retardos/salidas** con los toggles
5. **Generar Excel** del formato F-RH-18

### Dashboard Grupal (Jefes)
1. **Acceder** a `/mobper/grupo`
2. **Ver resumen** de todo el equipo
3. **Revisar incidencias** de cada miembro
4. **Descargar Excel** individual o bulk

### Sistema de Emergencia
1. **Acceder** a `/emergency`
2. **Activar modo pánico** para desbloquear puertas
3. **Monitorear dispositivos** en tiempo real
4. **Realizar roll call** durante emergencias

## Tecnologías

- **Backend**: Flask (Python 3.9+)
- **Frontend**: HTML5 + CSS3 + JavaScript
- **Base de Datos**: SQLite (desarrollo) / PostgreSQL (producción)
- **Excel**: win32com (Microsoft Office)
- **API**: BioStar 2 REST API
- **Tiempo Real**: Server-Sent Events (SSE)

## Documentación

- **ARCHITECTURE.md**: Arquitectura detallada del sistema
- **DATA_DICTIONARY.md**: Diccionario de datos completo

## Licencia

Uso interno. Todos los derechos reservados.
