# Arquitectura del Sistema

## Visión General
Sistema de gestión de asistencia y control de personal (MovPer) con integración a dispositivos BioStar, generación de formatos Excel, y capacidades de emergencia.

## Stack Tecnológico
- **Backend**: Flask (Python 3.9+)
- **Frontend**: HTML5 + CSS3 + JavaScript (vanilla)
- **Base de Datos**: SQLite (desarrollo) / PostgreSQL (producción)
- **Integración**: win32com para Excel, BioStar API para control de acceso
- **Autenticación**: Session-based con decoradores personalizados

## Estructura del Proyecto

```
DEBUGBI0/
├── webapp/                 # Aplicación Flask principal
│   ├── __init__.py         # Inicialización de app
│   ├── app.py              # Configuración principal
│   ├── models.py           # Modelos SQLAlchemy
│   ├── mobper_routes.py    # Rutas específicas de MovPer
│   ├── mobper_excel.py     # Generación de documentos Excel
│   ├── emergency_routes.py # Sistema de emergencia
│   ├── security.py         # Utilidades de seguridad
│   ├── cache_manager.py    # Gestión de caché
│   ├── monitoring.py       # Monitoreo y métricas
│   ├── realtime_*.py       # WebSockets y eventos en tiempo real
│   └── templates/          # Plantillas Jinja2
│       ├── mobper_*.html   # Vistas de MovPer
│       ├── panic_*.html    # Interfaz de emergencia
│       └── excel_*.html    # Pruebas de Excel
├── src/                    # Módulos de integración
│   ├── api/                # Clientes API externos
│   │   ├── biostar_client.py
│   │   ├── door_control.py
│   │   └── device_monitor.py
│   └── utils/              # Utilidades compartidas
│       ├── config.py
│       └── logger.py
├── tests/                  # Suite de pruebas
├── instance/               # Base de datos SQLite en ejecución
├── venv/                   # Entorno virtual
└── requirements.txt        # Dependencias Python
```

## Arquitectura por Capas

### 1. Capa de Presentación (Frontend)
- **Templates Jinja2**: Renderizado del lado del servidor
- **JavaScript vanilla**: Interactividad del cliente
- **CSS3**: Estilos responsive con sistema de diseño propio
- **Componentes**: Cards, modales, toasts, dashboards

### 2. Capa de Aplicación (Flask)
- **Blueprints**: Organización modular (`mobper_bp`, `emergency_bp`)
- **Decoradores**: Autenticación (`@mobper_login_required`, `@mobper_admin_required`)
- **Middleware**: Logging, caché, manejo de errores
- **APIs REST**: JSON endpoints para AJAX

### 3. Capa de Negocio (Services)
- **Cálculo de Incidencias**: `calcular_incidencias_quincena()`
- **Generación de Excel**: `generar_formato_excel()`
- **Control de Acceso**: Integración BioStar
- **Gestión de Emergencias**: Sistema de pánico

### 4. Capa de Datos (Models)
- **SQLAlchemy ORM**: Mapeo objeto-relacional
- **Migrations**: Scripts de migración de schema
- **Relaciones**: One-to-many, many-to-many, self-referential

## Módulos Principales

### MovPer (Movimiento de Personal)
**Propósito**: Control de asistencia, retardos, faltas y vacaciones

**Componentes**:
- **Checklist Individual**: Vista por empleado con clasificación de incidencias
- **Dashboard Grupal**: Vista por jefe con resumen de equipo
- **Generación de Excel**: Formato F-RH-18 y Aviso de Vacaciones
- **Configuración Personal**: Horarios, tolerancias, datos personales

**Flujo de Datos**:
1. BioStar → Eventos de checada
2. `fetch_events()` → Procesamiento crudo
3. `calcular_incidencias_quincena()` → Clasificación inteligente
4. UI → Justificación manual por usuario
5. `mobper_excel.py` → Generación de documento final

### Sistema de Emergencia
**Propósito**: Control remoto de accesos y protocolos de emergencia

**Componentes**:
- **Panic Button**: Activación de modo pánico
- **Door Control**: Apertura remota de puertas
- **Real-time Monitor**: Estado actual de dispositivos
- **Roll Call**: Pase de lista en emergencias

**Flujo de Datos**:
1. UI (panic_button.html) → Evento de pánico
2. `emergency_routes.py` → Lógica de control
3. `biostar_client.py` → Comandos a dispositivos
4. WebSocket → Actualizaciones en tiempo real

### Integración BioStar
**Propósito**: Conexión con sistema de control de acceso

**Componentes**:
- **Client API**: Wrapper sobre BioStar API
- **Device Monitor**: Estado y health checks
- **Event Processing**: Transformación de eventos crudos

## Patrones de Diseño

### 1. Repository Pattern
```python
# models.py
class MobPerUser(db.Model):
    # ... definición del modelo
    
# mobper_routes.py
def get_current_mobper_user():
    return MobPerUser.query.get(session['mobper_user_id'])
```

### 2. Service Layer Pattern
```python
# mobper_routes.py
def calcular_incidencias_quincena(user, quincena):
    # Lógica de negocio compleja
    # Retorna datos estructurados
```

### 3. Decorator Pattern
```python
# mobper_routes.py
@mobper_bp.route('/checklist')
@mobper_login_required
def checklist():
    # Endpoint protegido
```

### 4. Factory Pattern
```python
# mobper_excel.py
def generar_formato_excel(user, preset, incidencias, quincena, con_goce):
    # Factory para diferentes tipos de documentos
```

## Flujo de Autenticación

1. **Login**: `POST /mobper/login` → Validación credenciales
2. **Session**: `session['mobper_user_id']` = user.id
3. **Decoradores**: Verificación en cada ruta protegida
4. **Logout**: `POST /mobper/logout` → Limpieza de sesión
5. **Impersonación**: `session['mobper_impersonate_id']` para admins

## Gestión de Estado

### Estado de Incidencias
- **BORRADOR**: Edición activa por empleado
- **ENVIADO**: Enviado a jefe para revisión
- **REVISADO**: Revisado con observaciones
- **FIRMADO**: Firmado por jefe (bloqueado)
- **ENTREGADO_RH**: Enviado a Recursos Humanos

### Estado de Emergencia
- **NORMAL**: Operación regular
- **PANIC**: Modo pánico activado
- **LOCKDOWN**: Bloqueo total
- **EVACUATION**: Protocolo de evacuación

## Caching Strategy

### Redis/Memcached (producción)
- **Session Cache**: Datos de usuario frecuentes
- **Query Cache**: Resultados de cálculos complejos
- **Static Cache**: Templates y assets estáticos

### In-Memory (desarrollo)
- **Application Cache**: Datos temporales en memoria
- **Template Cache**: Cache de plantillas Jinja2

## Manejo de Errores

### Global Error Handler
```python
@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
```

### Custom Exceptions
- `BioStarConnectionError`: Fallos de conexión
- `ExcelGenerationError`: Errores en generación de documentos
- `InvalidQuincenaError**: Fechas inválidas

## Logging Strategy

### Niveles de Log
- **DEBUG**: Detalle de ejecución
- **INFO**: Eventos importantes
- **WARNING**: Situaciones anómalas
- **ERROR**: Errores de ejecución

### Destinations
- **File Logger**: `logs/app.log` rotación diaria
- **Console Logger**: Desarrollo y debugging
- **External Logger**: Integración con sistemas de monitoreo

## Security Considerations

### Authentication
- Password hashing con Werkzeug
- Session timeout configurable
- CSRF protection en forms

### Authorization
- Role-based access control
- Decoradores por recurso
- Validación de ownership

### Data Protection
- Input sanitization
- SQL injection prevention via ORM
- XSS protection en templates

## Performance Optimizations

### Database
- Índices en campos frecuentes
- Query optimization con eager loading
- Connection pooling

### Frontend
- Lazy loading de componentes
- Debouncing en búsquedas
- Optimización de CSS/JS

### Backend
- Async processing para tareas largas
- Background jobs con Celery (futuro)
- Response caching estático

## Deployment Architecture

### Development
- **SQLite**: Base de datos local
- **Flask Development Server**: Hot reload
- **File-based logging**: Debug local

### Production
- **PostgreSQL**: Base de datos robusta
- **Gunicorn + Nginx**: WSGI + reverse proxy
- **Redis**: Caching y session store
- **Docker**: Contenerización (opcional)

## Monitoring & Observability

### Health Checks
- `/health`: Estado general del sistema
- `/health/db`: Conectividad a base de datos
- `/health/biostar`: Estado de integración

### Metrics
- Response times por endpoint
- Error rates por módulo
- User activity y engagement

### Alerts
- High error rate (>5%)
- Database connection failures
- BioStar API timeouts

## Future Scalability

### Horizontal Scaling
- Load balancer + multiple app instances
- Database read replicas
- Distributed cache (Redis Cluster)

### Feature Roadmap
- Multi-tenancy (múltiples empresas)
- Mobile app (React Native)
- Advanced analytics y reporting
- Integration con HRIS systems
