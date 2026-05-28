# REPORTE COMPLETO DEL SISTEMA MOBPER
## Sistema de Movimiento de Personal - Documentación Técnica Integral

---

## 1. VISIÓN GENERAL Y ARQUITECTURA

### 1.1 Propósito del Sistema
MovPer es un sistema integral de gestión de asistencias quincenales que:
- Obtiene registros de checada desde BioStar 2
- Clasifica automáticamente incidencias (retardos, faltas, salidas tempranas)
- Permite justificación manual por parte del empleado
- Genera formatos Excel oficiales (F-RH-18) con datos pre-llenados
- Gestiona vacaciones en formato separado (Aviso de Vacaciones)

### 1.2 Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SISTEMA MOBPER                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   BioStar 2  │───▶│   Backend    │───▶│   Frontend   │                   │
│  │    API       │    │   Flask      │    │   HTML/JS    │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│         │                   │                   │                           │
│         │                   ▼                   ▼                           │
│         │          ┌──────────────┐    ┌──────────────┐                   │
│         │          │   SQLite     │    │   Excel      │                   │
│         │          │   Database   │    │   Generator  │                   │
│         │          └──────────────┘    └──────────────┘                   │
│         │                                                                  │
│  ┌──────▼──────────────────────────────────────────────────────────┐      │
│  │                    FLUJO DE DATOS                                │      │
│  │                                                                  │      │
│  │  1. BioStar Events → 2. Cache/Store → 3. Process/Classify      │      │
│  │       ↓                    ↓               ↓                   │      │
│  │  4. User Override → 5. Save to DB → 6. Generate Excel          │      │
│  └──────────────────────────────────────────────────────────────────┘      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Componentes Principales

| Componente | Archivo | Descripción |
|------------|---------|-------------|
| Backend Routes | `webapp/mobper_routes.py` | Lógica de negocio, APIs REST, cálculo de incidencias |
| Models | `webapp/models.py` | Modelos SQLAlchemy (MobPerUser, IncidenciaDia, PresetUsuario) |
| Excel Generator | `webapp/mobper_excel.py` | Generación de formatos Excel con win32com |
| Frontend | `webapp/templates/mobper_checklist_v3.html` | Interfaz de usuario y lógica de interacción |
| BioStar Client | `src/api/biostar_client.py` | Cliente API para BioStar 2 |

---

## 2. FLUJO DE DATOS DESDE BIOSTAR

### 2.1 Obtención de Eventos (fetch_events)

```python
def fetch_events():
    """
    Obtiene eventos de BioStar y retorna dict por día:
    {date: {'first': datetime, 'last': datetime, 'count': int}}
    """
```

**Proceso de obtención:**

1. **Cache de Cliente BioStar**
   ```python
   _biostar_client_cache = {
       'client': None,
       'last_login': 0,
       'ttl': 300  # 5 minutos de sesión válida
   }
   ```
   - Se reutiliza la sesión por 5 minutos para evitar re-login constante
   - Pre-calentamiento en background para primera carga rápida

2. **Query a BioStar API**
   ```python
   conditions = [
       {"column": "user_id.user_id", "operator": 0, "values": [biostar_user_id]},
       {"column": "datetime", "operator": 3, "values": [
           inicio_quincena.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
           fin_quincena.strftime('%Y-%m-%dT%H:%M:%S.000Z')
       ]}
   ]
   eventos = client.search_events(conditions=conditions, limit=1000, descending=False)
   ```

3. **Filtrado por Códigos de Acceso**
   ```python
   ACCESS_GRANTED_CODES = frozenset([
       '4097', '4098', '4099', '4100', '4101', '4102', '4103', '4104', 
       '4105', '4106', '4107', '4112', '4113', '4114', '4115', '4118', 
       '4119', '4120', '4121', '4122', '4123', '4128', '4129',
       '4865', '4866', '4867', '4868', '4869', '4870', '4871', '4872'
   ])
   ```
   - Solo eventos de "Acceso Concedido" se consideran válidos
   - Se descartan denegados, puertas forzadas, etc.

4. **Agrupación por Día**
   ```python
   for evento in eventos:
       dt_utc = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S.%fZ')
       dt = dt_utc.astimezone(MEXICO_TZ)  # Conversión a hora local CDMX
       
       if fecha_evento not in registros:
           registros[fecha_evento] = {'first': dt, 'last': dt, 'count': 1}
       else:
           r['count'] += 1
           if dt < r['first']: r['first'] = dt
           if dt > r['last']: r['last'] = dt
   ```

### 2.2 Correcciones Automáticas (CorreccionDia)

El sistema permite definir reglas de corrección para días donde el checador tuvo problemas:

```python
class CorreccionDia(db.Model):
    """
    Regla de corrección permanente para un día específico.
    Cuando un checador pierde sincronización con BioStar, los eventos
    llegan con offset horario. Esta tabla almacena la regla para corregir
    automáticamente la primera checada.
    
    Lógica:
      - Si el usuario tiene >= min_eventos_requeridos ese día
      - Y su primera checada cae dentro de [hora_anomala_inicio, hora_anomala_fin]
      - Entonces se resta offset_minutos a esa primera checada
      - La última checada (salida) NO se toca
    """
```

**Ejemplo de aplicación:**
```python
correcciones = CorreccionDia.query.filter(
    CorreccionDia.activa == True,
    CorreccionDia.fecha >= quincena['inicio'],
    CorreccionDia.fecha <= quincena['fin']
).all()

for corr in correcciones:
    if r['count'] >= corr.min_eventos_requeridos:
        if corr.hora_anomala_inicio <= hora_primera <= corr.hora_anomala_fin:
            corregida = r['first'] - timedelta(minutes=corr.offset_minutos)
            r['first'] = corregida
```

### 2.3 Caché de Eventos

```python
_biostar_events_cache = {}
_EVENTS_CACHE_TTL = 300  # 5 minutos

def get_cached_events(user_id, quincena_key, fetch_fn):
    """Cache de eventos por usuario+quincena."""
    cache_key = f"{user_id}_{quincena_key}"
    
    if cache_key in _biostar_events_cache:
        entry = _biostar_events_cache[cache_key]
        if (now - entry['timestamp']) < _EVENTS_CACHE_TTL:
            return entry['data']  # Cache HIT
    
    # Cache MISS - fetch y almacenar
    data = fetch_fn()
    _biostar_events_cache[cache_key] = {'data': data, 'timestamp': now}
    return data
```

---

## 3. MODELOS DE BASE DE DATOS

### 3.1 MobPerUser (Usuarios del Sistema)

```python
class MobPerUser(db.Model):
    __tablename__ = 'mobper_users'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_socio = db.Column(db.String(20), unique=True, nullable=False)  # ID BioStar
    nombre_completo = db.Column(db.String(200), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relaciones
    preset = db.relationship('PresetUsuario', backref='user', uselist=False)
    incidencias_dia = db.relationship('IncidenciaDia', backref='user', lazy='dynamic')
```

### 3.2 PresetUsuario (Configuración Personal)

```python
class PresetUsuario(db.Model):
    __tablename__ = 'mobper_presets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('mobper_users.id'), nullable=False)
    
    # Datos para el formato Excel
    nombre_formato = db.Column(db.String(200))              # Nombre en F-RH-18
    departamento_formato = db.Column(db.String(100))        # Departamento
    jefe_directo_nombre = db.Column(db.String(200))           # Jefe para firma
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))  # Logo
    
    # Configuración de horario
    hora_entrada_default = db.Column(db.Time, default='09:00:00')
    tolerancia_segundos = db.Column(db.Integer, default=600)  # 10 minutos
    hora_salida_default = db.Column(db.Time, default='18:00:00')
    tolerancia_salida_segundos = db.Column(db.Integer, default=600)
    dias_descanso = db.Column(db.JSON, default=[5, 6])      # Sábado y Domingo
    lista_inhabiles = db.Column(db.JSON, default=list)       # Días inhábiles extra
    
    vigente_desde = db.Column(db.Date, default=datetime.utcnow)
    vigente_hasta = db.Column(db.Date)
```

### 3.3 IncidenciaDia (Registro Diario)

```python
class IncidenciaDia(db.Model):
    __tablename__ = 'mobper_incidencias_dia'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('mobper_users.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    
    # Estado automático detectado por el sistema
    estado_auto = db.Column(db.String(20))  # A_TIEMPO, RETARDO, FALTA, DESCANSO, INHABIL
    
    # Clasificación manual del usuario
    clasificacion = db.Column(db.String(50))  # REMOTO, GUARDIA, VACACIONES, PERMISO, INCAPACIDAD, ERROR_SISTEMA
    con_goce_sueldo = db.Column(db.Boolean, default=True)
    
    # Campos de entrada
    hora_entrada = db.Column(db.Time)           # Hora de entrada manual (parche)
    minutos_diferencia = db.Column(db.Integer)  # Minutos de retardo
    justificado = db.Column(db.Boolean, default=True)  # Toggle de justificación
    
    # Campos de salida
    hora_salida = db.Column(db.Time)
    minutos_diferencia_salida = db.Column(db.Integer)
    salida_estado = db.Column(db.String(20))    # NORMAL, SALIDA_TEMPRANA
    salida_justificado = db.Column(db.Boolean, default=True)
    
    # Detección de olvido de checada
    entrada_no_checada = db.Column(db.Boolean, default=False)
    salida_no_checada = db.Column(db.Boolean, default=False)
    olvido_checar_justificado = db.Column(db.Boolean, default=True)
    
    # Flag para evitar duplicar vacaciones
    vacaciones_impresa = db.Column(db.Boolean, default=False)
    
    # Motivo generado automáticamente
    motivo_auto = db.Column(db.String(200))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'fecha', name='unique_user_fecha_dia'),
    )
```

---

## 4. LÓGICA DE CÁLCULO DE INCIDENCIAS

### 4.1 Función Principal: calcular_incidencias_quincena()

```python
def calcular_incidencias_quincena(user, quincena):
    """
    Calcula las incidencias automáticas para una quincena completa.
    
    Args:
        user: Usuario MovPer
        quincena: Dict con 'inicio', 'fin', 'nombre', 'anio', 'mes', 'numero'
    
    Returns:
        Lista de diccionarios con información de cada día
    """
```

### 4.2 Parámetros de Configuración

```python
# Configuración desde PresetUsuario
hora_entrada_default = preset.hora_entrada_default      # ej: 09:00
tolerancia_segundos = preset.tolerancia_segundos          # ej: 600 (10 min)
hora_salida_default = preset.hora_salida_default          # ej: 18:00
tolerancia_salida_segundos = getattr(preset, 'tolerancia_salida_segundos', 0)
dias_descanso = preset.dias_descanso or [5, 6]            # Sábado (5) y Domingo (6)

# Cálculos derivados
hora_limite = hora_entrada_default + timedelta(seconds=tolerancia_segundos)
hora_salida_limite = hora_salida_default - timedelta(seconds=tolerancia_salida_segundos)

# Punto medio para distinguir entrada vs salida con 1 solo evento
punto_medio_ts = (entrada_min_timestamp + salida_min_timestamp) / 2
```

### 4.3 Clasificación de Días

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        CLASIFICACIÓN DE DÍAS                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────┐                                                        │
│   │ ¿Es inhábil?    │──SÍ──▶ INHABIL (festivo oficial)                     │
│   │ (días oficiales)│                                                        │
│   └────────┬────────┘                                                        │
│            │NO                                                               │
│            ▼                                                                 │
│   ┌─────────────────┐                                                        │
│   │ ¿Es descanso?   │──SÍ──▶ DESCANSO (Sábado/Domingo configurable)            │
│   │ (días_descanso) │                                                        │
│   └────────┬────────┘                                                        │
│            │NO                                                               │
│            ▼                                                                 │
│   ┌─────────────────┐                                                        │
│   │ ¿Hay registros? │──NO──▶ FALTA (no checó)                               │
│   │ (BioStar)       │                                                        │
│   └────────┬────────┘                                                        │
│            │SÍ                                                               │
│            ▼                                                                 │
│   ┌─────────────────┐                                                        │
│   │ ¿Cuántos        │──1──▶ Evaluar según hora (punto medio)                │
│   │ eventos?        │                                                        │
│   └────────┬────────┘                                                        │
│            │2+                                                              │
│            ▼                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ Evaluar entrada: A_TIEMPO si <= hora_limite, RETARDO si > hora_limite │   │
│   │ Evaluar salida: NORMAL si >= hora_salida_limite, SALIDA_TEMPRANA si <  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 4.4 Lógica de Detección de Olvido de Checada (1 Solo Evento)

```python
if n_eventos == 1:
    hora_unico = primer_registro.time()
    
    if hora_unico >= punto_medio:
        # Único evento en segunda mitad → es SALIDA, falta ENTRADA
        # Ejemplo: Solo checó a las 17:00, falta entrada de la mañana
        entrada_no_checada = True
        estado_auto = 'A_TIEMPO'  # Asumimos llegó a tiempo
        minutos_diferencia = 0
        # Simular entrada a hora default
        primer_registro = datetime.combine(fecha, hora_entrada_default)
    else:
        # Único evento en primera mitad → es ENTRADA, falta SALIDA
        # Ejemplo: Solo checó a las 09:00, olvidó salida
        salida_no_checada = True
        ultimo_registro = None
        # Evaluar entrada normalmente
        if hora_registro <= hora_limite:
            estado_auto = 'A_TIEMPO'
        else:
            estado_auto = 'RETARDO'
```

### 4.5 Lógica de Entrada Manual (Parche)

Cuando un usuario no pudo checar (problema con BioStar), se permite ingresar hora manual:

```python
# La hora_entrada manual SIEMPRE gana sobre BioStar (override forzado)
_hora_entrada_manual = clasificaciones_guardadas.get(fecha_actual, {}).get('hora_entrada')

if _hora_entrada_manual:
    _dt_manual = MEXICO_TZ.localize(datetime.combine(fecha_actual, _hora_entrada_manual))
    
    if reg_dia is None:
        # Sin evento BioStar: simular entrada+salida con la hora manual
        reg_dia = {'first': _dt_manual, 'last': _dt_manual, 'count': 2}
    else:
        # Con evento BioStar: la entrada manual reemplaza 'first', BioStar es salida
        reg_dia = {'first': _dt_manual, 'last': reg_dia['last'], 'count': 2}
```

---

## 5. SISTEMA DE CLASIFICACIÓN Y JUSTIFICACIÓN

### 5.1 Clasificaciones de Faltas

| Código | Descripción | Goce de Sueldo | Incluye en Excel |
|--------|-------------|----------------|------------------|
| `REMOTO` | Trabajo Remoto | Sí | Sí |
| `GUARDIA` | Guardia Telefónica | Sí | Sí |
| `PERMISO` | Permiso Personal | Variable | Sí |
| `VACACIONES` | Vacaciones | Sí | NO (formato separado) |
| `INCAPACIDAD` | Incapacidad Médica | Según ley | NO |
| `ERROR_SISTEMA` | No es falta real | Sí | NO |

### 5.2 Estados Automáticos

| Estado | Descripción | Acción Requerida |
|--------|-------------|------------------|
| `A_TIEMPO` | Llegó puntual | Ninguna |
| `RETARDO` | Llegó tarde | Toggle de justificación |
| `FALTA` | No checó | Clasificación manual |
| `DESCANSO` | Día de descanso | Ninguna |
| `INHABIL` | Día inhábil (festivo) | Ninguna |
| `SALIDA_TEMPRANA` | Salió antes de hora | Toggle de justificación |

### 5.3 Sistema de Toggles (Justificación)

#### Retardos (`/api/toggle-justificacion`)
```python
@app.route('/api/toggle-justificacion', methods=['POST'])
def toggle_justificacion():
    data = request.get_json()
    fecha_str = data.get('fecha')
    justificado = data.get('justificado', True)  # True/False
    
    # Guardar en IncidenciaDia
    incidencia.justificado = justificado
    if justificado:
        incidencia.motivo_auto = 'Retardo justificado'
    else:
        incidencia.motivo_auto = 'Retardo NO justificado'
```

**Comportamiento:**
- `justificado=True`: El retardo aparece en el Excel con "retardo justificado"
- `justificado=False`: El retardo NO aparece en el Excel (como si no existiera)

#### Salidas Tempranas (`/api/toggle-justificacion-salida`)
```python
@app.route('/api/toggle-justificacion-salida', methods=['POST'])
def toggle_justificacion_salida():
    incidencia.salida_justificado = justificado
```

**Comportamiento:**
- `salida_justificado=True`: Salida temprana incluida en Excel
- `salida_justificado=False`: Salida temprana excluida del Excel

#### Olvido de Checada (`/api/toggle-justificacion-olvido`)
```python
@app.route('/api/toggle-justificacion-olvido', methods=['POST'])
def toggle_justificacion_olvido():
    incidencia.olvido_checar_justificado = justificado
```

**Comportamiento:**
- `olvido_checar_justificado=True` (default): Olvido incluido en Excel
- `olvido_checar_justificado=False`: Olvido excluido (error del sistema)

### 5.4 Generación de Motivo Automático

```python
def generar_motivo_auto(estado_auto, clasificacion, numero_dia):
    if estado_auto == 'RETARDO':
        return f"{numero_dia} retardo justificado"
    
    elif estado_auto == 'FALTA':
        motivos = {
            'REMOTO': f"{numero_dia} falta justificada, trabajo remoto",
            'GUARDIA': f"{numero_dia} falta justificada, guardia",
            'PERMISO': f"{numero_dia} falta justificada, permiso",
            'VACACIONES': f"{numero_dia} falta justificada, vacaciones",
            'INCAPACIDAD': f"{numero_dia} falta justificada, incapacidad",
            'INHABIL': f"{numero_dia} día inhábil",
            'ERROR_SISTEMA': '',
        }
        return motivos.get(clasificacion, f"{numero_dia} falta")
```

---

## 6. FILTRADO DE INCIDENCIAS PARA EXCEL

### 6.1 Función filtrar_incidencias_a_justificar()

```python
def filtrar_incidencias_a_justificar(incidencias: List[Dict]) -> List[Dict]:
    """
    Filtra las incidencias que deben aparecer en el formato MovPer.
    
    INCLUYE:
    - Retardos con justificado=True
    - Faltas clasificadas (excepto INCAPACIDAD, VACACIONES, ERROR_SISTEMA)
    - Salidas tempranas con salida_justificado=True
    - Olvido de checada con olvido_checar_justificado=True
    
    EXCLUYE:
    - A_TIEMPO, INHABIL, DESCANSO
    - Retardos con justificado=False
    - Faltas sin clasificar
    - Faltas clasificadas como INCAPACIDAD o VACACIONES
    - Salidas tempranas con salida_justificado=False
    """
```

### 6.2 Matriz de Inclusión en Excel

| Tipo | Estado | Justificación | Incluye en Excel |
|------|--------|---------------|------------------|
| Retardo | RETARDO | `justificado=True` | SÍ |
| Retardo | RETARDO | `justificado=False` | NO |
| Falta | FALTA | Sin clasificar | NO |
| Falta | FALTA | `REMOTO` | SÍ |
| Falta | FALTA | `GUARDIA` | SÍ |
| Falta | FALTA | `PERMISO` | SÍ |
| Falta | FALTA | `VACACIONES` | NO (formato separado) |
| Falta | FALTA | `INCAPACIDAD` | NO |
| Falta | FALTA | `ERROR_SISTEMA` | NO |
| Salida | SALIDA_TEMPRANA | `salida_justificado=True` | SÍ |
| Salida | SALIDA_TEMPRANA | `salida_justificado=False` | NO |
| Olvido | entrada/salida_no_checada | `olvido_justificado=True` | SÍ |
| Olvido | entrada/salida_no_checada | `olvido_justificado=False` | NO |

### 6.3 Análisis de Tipos de Incidencias

```python
def analizar_tipos_incidencias(incidencias: List[Dict]) -> Dict:
    """
    Agrupa incidencias por tipo para el resumen y marcado de círculos.
    
    Returns:
        {
            'faltas': [],           # Faltas sin clasificar
            'retardos': [],        # Días con retardo
            'remotos': [],         # Faltas clasificadas REMOTO
            'guardias': [],        # Faltas clasificadas GUARDIA
            'permisos': [],        # Faltas clasificadas PERMISO
            'vacaciones': [],      # Faltas clasificadas VACACIONES
            'incapacidades': [],   # Faltas clasificadas INCAPACIDAD
            'olvido_checar': [],   # Días con olvido justificado
            'salir_regresar': [],  # (legacy)
            'retirarse_temprano': [],  # Días con salida temprana
        }
    """
```

---

## 7. EXPORTACIÓN A EXCEL

### 7.1 Mapeo de Celdas del Template F-RH-18

```python
CELDAS = {
    # Encabezado
    'NOMBRE': 'E8',              # Nombre del empleado
    'DEPARTAMENTO': 'Q8',        # Departamento
    'FECHA_AUTORIZACION': 'H10', # Fecha de autorización (hoy)
    'FECHA_APLICACION': 'P10',   # Días del período
    
    # Círculos de tipo de permiso
    'PARA_FALTAR': 'D15',        # Checkbox para faltar
    'PARA_SALIR_REGRESAR': 'D16', 
    'PARA_LLEGAR_TARDE': 'D17',  # Checkbox para llegar tarde (retardos)
    'PARA_RETIRARSE': 'M15',     # Checkbox retirarse temprano
    'OLVIDO_CHECAR': 'M16',      # Checkbox olvidó checar
    
    # Goce de sueldo
    'GOCE_SI': 'F17',            # Círculo SI
    'GOCE_NO': 'G17',            # Círculo NO
    
    # Motivo
    'MOTIVO': 'G20',             # Campo de motivo
    
    # Firmas
    'SOLICITO_NOMBRE': 'E56',    # Nombre del solicitante
    'AUTORIZO_NOMBRE': 'J56',    # Nombre del autorizador/jefe
    'RECIBIO_NOMBRE': 'Q56',     # Recursos Humanos
}

# Índices de Shapes (círculos) en el template
SHAPES = {
    'PARA_FALTAR': 1,
    'PARA_SALIR_REGRESAR': 2,
    'OLVIDO_CHECAR': 3,
    'PARA_RETIRARSE': 4,
    'PARA_LLEGAR_TARDE': 5,
    'GOCE_SI': 9,
    'GOCE_NO': 10,
}
```

### 7.2 Adaptación Inteligente de Fuente

```python
CAMPO_CONFIG = {
    #                col_width  fmax  fmin  wrap  ratio
    'NOMBRE':             (40.66,   10,  10,    1,   RATIO_NARROW),
    'DEPARTAMENTO':       (11.86,   14,   6,    1,   RATIO_NARROW),
    'FECHA_AUTORIZACION': (21.71,   10,  10,    1,   RATIO_NARROW),
    'FECHA_APLICACION':   (17.29,   10,   6,    1,   RATIO_NARROW),
    'MOTIVO':             (65.00,   11,   7,    2,   RATIO_ARIAL),
    'SOLICITO_NOMBRE':    (11.53,   12,   6,    1,   RATIO_NARROW),
    'AUTORIZO_NOMBRE':    ( 6.00,   10,   6,    1,   RATIO_NARROW),
    'RECIBIO_NOMBRE':     (27.43,   12,   7,    1,   RATIO_NARROW),
}

def calcular_font_adaptativo(texto: str, campo: str) -> int:
    """
    Calcula el tamaño de fuente óptimo para que el texto quepa.
    
    Formula: chars_reales = col_width / ratio * (11.0 / font_size) * wrap_lines
    """
    col_width, font_max, font_min, wrap_lines, ratio = CAMPO_CONFIG[campo]
    n_chars = len(texto)
    
    for font_size in range(font_max, font_min - 1, -1):
        capacidad = col_width / ratio * (11.0 / font_size) * wrap_lines
        if n_chars <= capacidad:
            return font_size
    
    return font_min
```

### 7.3 Proceso de Generación de Excel

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PROCESO DE GENERACIÓN DE EXCEL                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. COPIAR TEMPLATE                                                          │
│     └── shutil.copy(TEMPLATE_PATH, output_path)                             │
│                                                                              │
│  2. INICIALIZAR WIN32COM                                                     │
│     └── pythoncom.CoInitialize()                                            │
│     └── excel = win32.gencache.EnsureDispatch('Excel.Application')         │
│                                                                              │
│  3. ABRIR WORKBOOK                                                           │
│     └── wb = excel.Workbooks.Open(output_path)                              │
│     └── sheet = wb.ActiveSheet                                               │
│                                                                              │
│  4. REEMPLAZAR LOGO                                                          │
│     └── Obtener shape original (Shape 25)                                   │
│     └── Eliminar logo MIT                                                   │
│     └── Insertar logo de la empresa del usuario                             │
│     └── Mantener proporciones y posición                                    │
│                                                                              │
│  5. LLENAR CAMPOS                                                            │
│     ├── NOMBRE: preset.nombre_formato.title()                               │
│     ├── DEPARTAMENTO: preset.departamento_formato.upper()                   │
│     ├── FECHA_AUTORIZACION: hoy en formato dd-mmm-yy                      │
│     ├── FECHA_APLICACION: días de incidencias agrupados                   │
│     └── MOTIVO: texto generado automáticamente                            │
│                                                                              │
│  6. MARCAR CÍRCULOS                                                          │
│     └── Analizar tipos de incidencias                                       │
│     └── set_circle_color(shape_index, True/False)                         │
│                                                                              │
│  7. GOCE DE SUELDO                                                           │
│     └── Marcar SI o NO según parámetro con_goce                             │
│                                                                              │
│   8. FIRMAS                                                                  │
│     ├── SOLICITO: nombre del empleado                                       │
│     ├── AUTORIZO: preset.jefe_directo_nombre                              │
│     └── RECIBIO: "RECURSOS HUMANOS"                                         │
│                                                                              │
│  9. GUARDAR Y CERRAR                                                         │
│     └── wb.Save()                                                           │
│     └── wb.Close(SaveChanges=False)                                         │
│     └── excel.Quit()                                                        │
│     └── pythoncom.CoUninitialize()                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.4 Generación de Aviso de Vacaciones

```python
def generar_aviso_vacaciones(user, preset, periodo_vac, quincena):
    """
    Genera un AVISO DE VACACIONES separado.
    
    Diferencias con MovPer regular:
    - Llena sección inferior del template (filas 39-52)
    - No llena círculos de permiso (todos en blanco)
    - Limpia sección superior de motivo
    - Calcula fecha_regreso = último día de vacaciones + 1
    """
    
    # Campos específicos de vacaciones
    CELDAS['VAC_DIAS_EFECTIVOS']     # Días que corresponden
    CELDAS['VAC_FECHA_SALIDA']       # Primer día de vacaciones
    CELDAS['VAC_FECHA_REGRESO']      # Día siguiente al último
    CELDAS['VAC_DEPARTAMENTO']       # Departamento
    CELDAS['VAC_SOLICITO']           # Firma empleado
    CELDAS['VAC_AUTORIZO']           # Firma jefe
    CELDAS['VAC_RECIBIO']            # Firma RH
```

---

## 8. FRONTEND Y UI

### 8.1 Estructura del Template

```html
<!-- mobper_checklist_v3.html -->
<!DOCTYPE html>
<html lang="es">
<head>
    <!-- Critical CSS inline para LCP óptimo -->
    <style>
        /* Variables CSS */
        :root {
            --primary: #3E2723;    /* Café MIT */
            --accent: #5D4037;    /* Café claro */
            --bg: #f5f3f1;        /* Fondo */
            --text: #3E2723;     /* Texto */
            --success: #059669;   /* Verde */
            --warning: #D97706;   /* Naranja */
            --danger: #DC2626;    /* Rojo */
        }
    </style>
</head>
<body>
    <!-- Header sticky -->
    <header class="header">...</header>
    
    <!-- Resumen de Quincena -->
    <section class="resumen-card">...</section>
    
    <!-- Tabs: Retardos | Faltas | Salidas | Olvidos -->
    <div class="tabs">...</div>
    
    <!-- Cards de Incidencias -->
    <div class="cards-container">...</div>
    
    <!-- Acciones (Generar Excel) -->
    <div class="actions-bar">...</div>
</body>
</html>
```

### 8.2 Componentes de UI

#### Card de Retardo
```html
<div class="incidencia-card retardo">
    <div class="card-header">
        <span class="fecha">Lunes 15 de Enero</span>
        <span class="hora">09:15</span>
    </div>
    <div class="card-body">
        <span class="diferencia">+15 min</span>
        <!-- Toggle de Justificación -->
        <label class="toggle-switch">
            <input type="checkbox" checked onchange="toggleJustificacion('2026-01-15', this.checked)">
            <span class="slider"></span>
        </label>
        <span class="just-label">Justificado</span>
    </div>
</div>
```

#### Card de Falta (con Dropdown)
```html
<div class="incidencia-card falta">
    <div class="card-header">
        <span class="fecha">Martes 16 de Enero</span>
        <span class="badge">Sin checar</span>
    </div>
    <div class="card-body">
        <!-- Dropdown de Clasificación -->
        <select onchange="clasificarFalta('2026-01-16', this.value)">
            <option value="">Seleccionar...</option>
            <option value="REMOTO">Trabajo Remoto</option>
            <option value="GUARDIA">Guardia Telefónica</option>
            <option value="PERMISO">Permiso Personal</option>
            <option value="VACACIONES">Vacaciones</option>
            <option value="INCAPACIDAD">Incapacidad</option>
            <option value="ERROR_SISTEMA">No es falta (error)</option>
        </select>
        
        <!-- Tag de clasificación actual -->
        <div class="class-tag remoto" style="display:none;">Trabajo Remoto</div>
    </div>
</div>
```

#### Card de Olvido de Checada
```html
<div class="incidencia-card olvido">
    <div class="card-header">
        <span class="fecha">Miércoles 17 de Enero</span>
    </div>
    <div class="card-body">
        <p>Solo registró salida (18:30)</p>
        <p class="auto-just">Auto-justificado por el sistema</p>
        
        <!-- Toggle para marcar como error -->
        <label class="toggle-switch">
            <input type="checkbox" checked onchange="toggleJustificacionOlvido('2026-01-17', this.checked)">
            <span class="slider"></span>
        </label>
        <span class="just-label">Es olvido real</span>
    </div>
</div>
```

### 8.3 Funciones JavaScript Principales

```javascript
// Justificar/Desjustificar retardo
async function toggleJustificacion(fecha, justificado) {
    const response = await fetch('/mobper/api/toggle-justificacion', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({fecha, justificado})
    });
    
    if (response.ok) {
        showToast(justificado ? 'Retardo justificado' : 'Retardo no justificado');
        actualizarResumen();  // Recalcular contadores
    }
}

// Clasificar una falta
async function clasificarFalta(fecha, clasificacion) {
    const response = await fetch('/mobper/api/clasificar', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({fecha, clasificacion})
    });
    
    if (response.ok) {
        // Actualizar UI: mostrar tag, ocultar dropdown
        mostrarTagClasificacion(fecha, clasificacion);
        showToast('Clasificación guardada');
    }
}

// Generar Excel
async function generarExcel(conGoce) {
    const overlay = document.getElementById('loadingOverlay');
    overlay.style.display = 'flex';
    
    // Usar fetch para blob + descarga automática
    const response = await fetch(`/mobper/generar-excel?con_goce=${conGoce ? 1 : 0}`);
    const blob = await response.blob();
    
    // Crear enlace temporal y descargar
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `MovPer_${userId}_${fecha}.xlsx`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    
    overlay.style.display = 'none';
}
```

---

## 9. FLUJO COMPLETO DE DATOS

### 9.1 Diagrama de Secuencia

```
┌─────────┐     ┌──────────┐     ┌──────────┐     ┌─────────┐     ┌─────────┐
│ Usuario │     │ Frontend │     │ Backend  │     │ BioStar │     │   DB    │
└────┬────┘     └────┬─────┘     └────┬─────┘     └────┬────┘     └────┬────┘
     │               │                │                │               │
     │─── Accede a ─▶│                │                │               │
     │   checklist   │                │                │               │
     │               │── GET /checklist ────────────────▶│               │
     │               │                │                │               │
     │               │                │── Verificar cache de eventos    │
     │               │                │                │               │
     │               │                │── Cache MISS? ─────────────────▶│
     │               │                │                │               │
     │               │                │◀── Sí: Query BioStar API ────────│
     │               │                │    (search_events)              │
     │               │                │                │               │
     │               │                │── Guardar en cache              │
     │               │                │                │               │
     │               │                │── Cargar clasificaciones de DB ─▶│
     │               │                │                │               │
     │               │                │◀── IncidenciaDia rows ───────────│
     │               │                │                │               │
     │               │                │── Calcular incidencias          │
     │               │                │   (calcular_incidencias_quincena)│
     │               │                │                │               │
     │               │◀── JSON con incidencias ─────────│                │
     │               │                │                │               │
     │◀── Renderizar ─│                │                │               │
     │   checklist   │                │                │               │
     │               │                │                │               │
     │─── Toggle   ─▶│                │                │               │
     │   justificar  │                │                │               │
     │               │                │                │               │
     │               │── POST /api/toggle ──────────────▶│               │
     │               │                │                │               │
     │               │                │── Guardar en IncidenciaDia ────▶│
     │               │                │                │               │
     │               │                │◀── OK ───────────────────────────│
     │               │                │                │               │
     │               │◀── JSON success ─────────────────│                │
     │               │                │                │               │
     │◀── Actualizar ─│                │                │               │
     │   UI          │                │                │               │
     │               │                │                │               │
     │── Generar   ─▶│                │                │               │
     │   Excel       │                │                │               │
     │               │                │                │               │
     │               │── GET /generar-excel ────────────▶│               │
     │               │                │                │               │
     │               │                │── Cargar incidencias + DB ─────▶│
     │               │                │                │               │
     │               │                │◀── Datos ────────────────────────│
     │               │                │                │               │
     │               │                │── Filtrar incidencias a         │
     │               │                │   incluir en Excel              │
     │               │                │                │               │
     │               │                │── Generar Excel con win32com    │
     │               │                │                │               │
     │               │                │◀── Archivo temporal ─────────────│
     │               │                │                │               │
     │               │◀── Blob Excel ────────────────────│                │
     │               │                │                │               │
     │◀── Descarga ──│                │                │               │
     │   automática  │                │                │               │
     │               │                │                │               │
```

---

## 10. DECORADORES Y SEGURIDAD

### 10.1 Autenticación MovPer

```python
def mobper_login_required(f):
    """Decorador que verifica que el usuario esté autenticado en MovPer."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'mobper_user_id' not in session:
            return redirect(url_for('mobper.login'))
        return f(*args, **kwargs)
    return decorated_function

def mobper_admin_required(f):
    """Decorador para rutas de admin en MovPer."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'mobper_user_id' not in session:
            return redirect(url_for('mobper.login'))
        
        user = MobPerUser.query.get(session['mobper_user_id'])
        if not user or not user.is_admin:
            flash('Acceso denegado.', 'danger')
            return redirect(url_for('mobper.checklist'))
        return f(*args, **kwargs)
    return decorated_function
```

### 10.2 Impersonación (Admin como otro usuario)

```python
def get_current_mobper_user():
    """Obtiene el usuario actual, respetando impersonación si está activa."""
    if 'mobper_user_id' not in session:
        return None
    
    base_user = MobPerUser.query.get(session['mobper_user_id'])
    if not base_user:
        return None
    
    # Si hay impersonación y el usuario base es admin, retornar el usuario objetivo
    impersonate_id = session.get('mobper_impersonate_id')
    if impersonate_id and base_user.is_admin:
        target = MobPerUser.query.get(impersonate_id)
        if target:
            return target
    
    return base_user
```

---

## 11. RESUMEN DE APIS REST

### 11.1 Endpoints del Sistema

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/mobper/` | Redirect a login o dashboard | - |
| GET/POST | `/mobper/login` | Página de login | - |
| GET | `/mobper/logout` | Cerrar sesión | Sí |
| GET | `/mobper/checklist` | Checklist de quincena | Sí |
| GET | `/mobper/config` | Configuración de horarios | Sí |
| POST | `/mobper/config` | Guardar configuración | Sí |
| GET | `/mobper/api/incidencias` | JSON de incidencias | Sí |
| POST | `/mobper/api/clasificar` | Clasificar falta | Sí |
| POST | `/mobper/api/toggle-justificacion` | Toggle justificación retardo | Sí |
| POST | `/mobper/api/toggle-justificacion-salida` | Toggle justificación salida | Sí |
| POST | `/mobper/api/toggle-justificacion-olvido` | Toggle justificación olvido | Sí |
| POST | `/mobper/api/patch-hora-entrada` | Parchear hora entrada | Sí |
| GET | `/mobper/api/periodos-vacaciones` | Lista de períodos vacaciones | Sí |
| GET | `/mobper/generar-excel` | Generar Excel MovPer | Sí |
| GET | `/mobper/grupo` | Dashboard grupal (jefes) | Admin |
| GET | `/mobper/grupo/api/resumen` | Resumen del grupo | Admin |

---

## 12. CONFIGURACIÓN Y PERSONALIZACIÓN

### 12.1 Variables de Entorno

```env
# BioStar 2 API
BIOSTAR_HOST=https://10.0.0.100
BIOSTAR_USER=usuario
BIOSTAR_PASSWORD=password

# Flask
SECRET_KEY=clave-secreta
FLASK_ENV=production

# MovPer
MOBPER_CACHE_TTL=300  # Segundos de cache de BioStar
MOBPER_DEBUG=false    # Logs detallados
```

### 12.2 Configuración por Usuario

Cada usuario puede configurar:

1. **Horarios**
   - Hora de entrada (default: 09:00)
   - Tolerancia de entrada (default: 10 min)
   - Hora de salida (default: 18:00)
   - Tolerancia de salida (default: 10 min)

2. **Días**
   - Días de descanso (default: Sábado, Domingo)
   - Días inhábiles adicionales

3. **Datos del Formato**
   - Nombre para el formato
   - Departamento
   - Jefe directo (para firma)
   - Empresa (para logo)

---

## 14. SISTEMA DE QUINCENAS

### 14.1 Funciones de Cálculo de Quincenas

#### calcular_quincena_actual(fecha=None)

```python
def calcular_quincena_actual(fecha=None):
    """
    Calcula la quincena actual basándose en la fecha proporcionada.
    
    Reglas:
    - Primera quincena: día 1 al 15
    - Segunda quincena: día 16 al último día del mes
    
    Returns:
        dict: {
            'numero': 1 o 2,
            'inicio': date,
            'fin': date,
            'mes': int,
            'anio': int,
            'nombre': str (ej: "Primera quincena de enero 2026"),
            'dias_totales': int
        }
    """
```

**Lógica de cálculo:**
```python
dia = fecha.day
mes = fecha.month
anio = fecha.year

if dia <= 15:
    # Primera quincena: 1 al 15
    numero = 1
    inicio = date(anio, mes, 1)
    fin = date(anio, mes, 15)
else:
    # Segunda quincena: 16 al último día del mes
    numero = 2
    ultimo_dia = monthrange(anio, mes)[1]  # Último día del mes
    inicio = date(anio, mes, 16)
    fin = date(anio, mes, ultimo_dia)
```

#### calcular_quincena(anio, mes, numero)

```python
def calcular_quincena(anio, mes, numero):
    """Calcula los límites de una quincena específica."""
    if numero == 1:
        inicio = date(anio, mes, 1)
        fin = date(anio, mes, 15)
    else:
        ultimo_dia = monthrange(anio, mes)[1]
        inicio = date(anio, mes, 16)
        fin = date(anio, mes, ultimo_dia)
    
    return {
        'numero': numero,
        'inicio': inicio,
        'fin': fin,
        'mes': mes,
        'anio': anio,
        'nombre': f"{'Primera' if numero == 1 else 'Segunda'} quincena de {mes_nombre} {anio}",
        'dias_totales': (fin - inicio).days + 1
    }
```

#### obtener_quincena_anterior(quincena_actual)

```python
def obtener_quincena_anterior(quincena_actual):
    """
    Obtiene la quincena anterior a la proporcionada.
    
    Lógica:
    - Si es primera quincena (1), la anterior es la segunda (2) del mes anterior
    - Si es segunda quincena (2), la anterior es la primera (1) del mismo mes
    """
    if quincena_actual['numero'] == 1:
        # Primera quincena → segunda del mes anterior
        mes_anterior = quincena_actual['mes'] - 1
        anio_anterior = quincena_actual['anio']
        if mes_anterior == 0:
            mes_anterior = 12
            anio_anterior -= 1
        fecha_anterior = date(anio_anterior, mes_anterior, 20)
    else:
        # Segunda quincena → primera del mismo mes
        fecha_anterior = date(quincena_actual['anio'], quincena_actual['mes'], 10)
    
    return calcular_quincena_actual(fecha_anterior)
```

#### obtener_quincena_siguiente(quincena_actual)

```python
def obtener_quincena_siguiente(quincena_actual):
    """
    Obtiene la quincena siguiente a la proporcionada.
    
    Lógica:
    - Si es segunda quincena (2), la siguiente es la primera (1) del mes siguiente
    - Si es primera quincena (1), la siguiente es la segunda (2) del mismo mes
    """
    if quincena_actual['numero'] == 2:
        # Segunda quincena → primera del mes siguiente
        mes_siguiente = quincena_actual['mes'] + 1
        anio_siguiente = quincena_actual['anio']
        if mes_siguiente == 13:
            mes_siguiente = 1
            anio_siguiente += 1
        fecha_siguiente = date(anio_siguiente, mes_siguiente, 5)
    else:
        # Primera quincena → segunda del mismo mes
        fecha_siguiente = date(quincena_actual['anio'], quincena_actual['mes'], 20)
    
    return calcular_quincena_actual(fecha_siguiente)
```

### 14.2 Navegación entre Quincenas

El sistema permite navegar entre quincenas mediante parámetros GET:

```
/mobper/checklist                    → Quincena anterior a la actual (default)
/mobper/checklist?year=2026&month=1&quincena=1  → Primera quincena de enero 2026
/mobper/checklist?year=2026&month=1&quincena=2  → Segunda quincena de enero 2026
```

**Lógica de navegación en checklist:**
```python
year = request.args.get('year', type=int)
month = request.args.get('month', type=int)
quincena_num = request.args.get('quincena', type=int)

if year and month and quincena_num:
    quincena = calcular_quincena(year, month, quincena_num)
else:
    # Por defecto: mostrar quincena anterior a la actual
    quincena_actual = calcular_quincena_actual()
    quincena = obtener_quincena_anterior(quincena_actual)
```

---

## 15. SISTEMA DE DÍAS INHÁBILES

### 15.1 Estructura de Días Inhábiles

```python
# dias_inhabiles.py

# Días inhábiles oficiales de México para 2026
DIAS_INHABILES_2026 = [
    date(2026, 1, 1),    # Año Nuevo
    date(2026, 2, 2),    # Día de la Constitución (primer lunes de febrero)
    date(2026, 3, 16),   # Natalicio de Benito Juárez (tercer lunes de marzo)
    date(2026, 4, 2),    # Jueves Santo (variable)
    date(2026, 4, 3),    # Viernes Santo (variable)
    date(2026, 5, 1),    # Día del Trabajo
    date(2026, 9, 16),   # Día de la Independencia
    date(2026, 11, 16),  # Revolución Mexicana (tercer lunes de noviembre)
    date(2026, 12, 25),  # Navidad
]

# Diccionario completo por año
DIAS_INHABILES_POR_ANIO = {
    2025: DIAS_INHABILES_2025,
    2026: DIAS_INHABILES_2026,
    2027: DIAS_INHABILES_2027,
}
```

### 15.2 Funciones de Días Inhábiles

```python
def obtener_dias_inhabiles(anio):
    """Obtiene la lista de días inhábiles oficiales para un año específico."""
    return DIAS_INHABILES_POR_ANIO.get(anio, [])

def es_dia_inhabil(fecha):
    """Verifica si una fecha es día inhábil oficial."""
    dias_inhabiles = obtener_dias_inhabiles(fecha.year)
    return fecha in dias_inhabiles

def obtener_nombre_dia_inhabil(fecha):
    """Obtiene el nombre del día inhábil si aplica."""
    if not es_dia_inhabil(fecha):
        return None
    
    nombres = {
        (1, 1): "Año Nuevo",
        (2, 1): "Día de la Constitución",  # Primer lunes de febrero
        (2, 2): "Día de la Constitución",
        (2, 3): "Día de la Constitución",
        (3, 15): "Natalicio de Benito Juárez",  # Tercer lunes de marzo
        (3, 16): "Natalicio de Benito Juárez",
        (3, 17): "Natalicio de Benito Juárez",
        (5, 1): "Día del Trabajo",
        (9, 16): "Día de la Independencia",
        (11, 15): "Revolución Mexicana",  # Tercer lunes de noviembre
        (11, 16): "Revolución Mexicana",
        (11, 17): "Revolución Mexicana",
        (12, 25): "Navidad",
    }
    
    return nombres.get((fecha.month, fecha.day), "Día Inhábil Oficial")
```

### 15.3 Integración con el Sistema

En `calcular_incidencias_quincena`:

```python
# Obtener días inhábiles oficiales del año de la quincena
anio_quincena = quincena['inicio'].year
dias_inhabiles_oficiales = obtener_dias_inhabiles(anio_quincena)

# Combinar días inhábiles del preset con los oficiales
lista_inhabiles_preset = preset.lista_inhabiles or []
lista_inhabiles = list(set(lista_inhabiles_preset + dias_inhabiles_oficiales))

# Clasificación de días
if fecha_actual in lista_inhabiles:
    tipo_dia = 'INHABIL'
    estado_auto = 'INHABIL'
    nombre_inhabil = obtener_nombre_dia_inhabil(fecha_actual)
```

---

## 16. DASHBOARD DE GRUPO (GESTIÓN DE EQUIPO)

### 16.1 Arquitectura del Dashboard Grupal

El dashboard grupal permite a los administradores/jefes:
- Ver el resumen de asistencias de todo su equipo
- Generar Excel individuales o masivos (ZIP)
- Revisar detalles de incidencias por miembro
- Identificar miembros con faltas sin clasificar

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DASHBOARD DE GRUPO                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Selector de Quincena  [Anterior] [Quincena Actual] [Siguiente]        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  RESUMEN DEL GRUPO                                                    │  │
│  │  ├── Miembros: 12                                                     │  │
│  │  ├── A tiempo: 180 días                                               │  │
│  │  ├── Retardos: 15                                                     │  │
│  │  ├── Faltas: 8                                                        │  │
│  │  └── Pendientes: 3 (con faltas sin clasificar)                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  MIEMBROS DEL GRUPO                                                   │  │
│  │  ┌──────────────┬──────────┬──────┬───────┬───────┬──────────┐       │  │
│  │  │ Nombre       │ Depto    │ OK   │ Retar │ Faltas│ Estado   │       │  │
│  │  ├──────────────┼──────────┼──────┼───────┼───────┼──────────┤       │  │
│  │  │ Juan Pérez   │ Sistemas │ 10   │ 0     │ 0     │ [verde]  │       │  │
│  │  │ María García │ RH       │ 8    │ 2     │ 0     │ [amaril] │       │  │
│  │  │ Pedro López  │ Ventas   │ 5    │ 1     │ 3(*)  │ [rojo]   │       │  │
│  │  └──────────────┴──────────┴──────┴───────┴───────┴──────────┘       │  │
│  │                                                                       │  │
│  │  (*) = Tiene faltas sin clasificar                                   │  │
│  │                                                                       │  │
│  │  Acciones: [Ver Detalle] [Generar Excel] [Descargar Todo ZIP]          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 16.2 Funciones del Dashboard Grupal

#### get_group_members(leader_user)

```python
def get_group_members(leader_user):
    """
    Obtiene los miembros del grupo de un líder.
    
    SIMULACIÓN ACTUAL: 
    - Todos los usuarios activos excepto el líder pertenecen al grupo
    
    FUTURO:
    - Filtrar por relación jefe-empleado en el preset (jefe_directo_nombre)
    """
    members = MobPerUser.query.filter(
        MobPerUser.id != leader_user.id,
        MobPerUser.is_active == True
    ).order_by(MobPerUser.nombre_completo).all()
    return members
```

#### calcular_resumen_miembro(user, quincena)

```python
def calcular_resumen_miembro(user, quincena):
    """Calcula el resumen de incidencias de un miembro para una quincena."""
    try:
        incidencias = calcular_incidencias_quincena(user, quincena)
        
        # Contar por tipo
        a_tiempo = sum(1 for i in incidencias if i['estado_auto'] == 'A_TIEMPO')
        retardos = sum(1 for i in incidencias if i['estado_auto'] == 'RETARDO')
        faltas = sum(1 for i in incidencias if i['estado_auto'] == 'FALTA')
        inhabiles = sum(1 for i in incidencias if i['estado_auto'] == 'INHABIL')
        descansos = sum(1 for i in incidencias if i['estado_auto'] == 'DESCANSO')
        
        # Faltas sin clasificar (requieren atención)
        faltas_sin_clasificar = sum(
            1 for i in incidencias
            if i['estado_auto'] == 'FALTA' and not i.get('clasificacion')
        )
        
        # Determinar estado visual
        if faltas_sin_clasificar > 0:
            estado = 'pendiente'  # Naranja - requiere acción
        elif faltas > 0 or retardos > 2:
            estado = 'alerta'     # Rojo - muchas incidencias
        else:
            estado = 'ok'         # Verde - todo bien
        
        return {
            'a_tiempo': a_tiempo,
            'retardos': retardos,
            'faltas': faltas,
            'inhabiles': inhabiles,
            'descansos': descansos,
            'faltas_sin_clasificar': faltas_sin_clasificar,
            'estado': estado,
            'incidencias': incidencias,
        }
    except Exception as e:
        print(f"[GRUPO] Error calculando resumen de {user.numero_socio}: {e}")
        return {
            'a_tiempo': 0, 'retardos': 0, 'faltas': 0,
            'inhabiles': 0, 'descansos': 0,
            'faltas_sin_clasificar': 0,
            'estado': 'error',
            'incidencias': [],
        }
```

### 16.3 APIs del Dashboard Grupal

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/mobper/grupo` | GET | Página principal del dashboard |
| `/mobper/grupo/api/resumen` | GET | JSON con resumen de todos los miembros |
| `/mobper/grupo/api/miembro/<id>/detalle` | GET | Detalle completo de incidencias de un miembro |
| `/mobper/grupo/api/generar-excel/<id>` | GET | Genera Excel individual (o ZIP si tiene vacaciones) |
| `/mobper/grupo/api/generar-excel-todos` | GET | Genera ZIP con todos los Excel del grupo |

### 16.4 Generación Masiva de Excel

```python
@mobper_bp.route('/grupo/api/generar-excel-todos', methods=['GET'])
@mobper_admin_required
def grupo_api_generar_excel_todos():
    """API: Genera un ZIP con los Excel de todos los miembros del grupo."""
    import zipfile
    import tempfile
    
    try:
        leader = get_current_mobper_user()
        members = get_group_members(leader)
        
        # Obtener quincena
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        quincena_num = request.args.get('quincena_num', type=int)
        con_goce = request.args.get('con_goce', '1') == '1'
        
        if year and month and quincena_num:
            quincena = calcular_quincena(year, month, quincena_num)
        else:
            quincena = calcular_quincena_actual()
        
        # Crear ZIP temporal
        zip_dir = tempfile.mkdtemp()
        zip_path = os.path.join(zip_dir, 'MovPer_Grupo.zip')
        generated_files = []
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for m in members:
                try:
                    preset = PresetUsuario.query.filter_by(user_id=m.id).first()
                    incidencias = calcular_incidencias_quincena(m, quincena)
                    output_path, filename = generar_formato_excel(
                        user=m, preset=preset, incidencias=incidencias,
                        quincena=quincena, con_goce=con_goce
                    )
                    zf.write(output_path, filename)
                    generated_files.append(output_path)
                except Exception as e:
                    print(f"[GRUPO ZIP] Error con {m.nombre_completo}: {e}")
        
        # Limpiar archivos temporales
        for fp in generated_files:
            try:
                os.remove(fp)
            except Exception:
                pass
        
        # Cleanup después de enviar
        @after_this_request
        def cleanup_grupo_zip(response):
            try:
                os.remove(zip_path)
                os.rmdir(zip_dir)
            except Exception:
                pass
            return response
        
        q_name = quincena['nombre'].replace(' ', '_')
        return send_file(
            zip_path, as_attachment=True,
            download_name=f'MovPer_Grupo_{q_name}.zip',
            mimetype='application/zip'
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
```

---

## 17. PANEL DE ADMINISTRACIÓN

### 17.1 APIs Administrativas

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/mobper/admin` | GET | Panel de administración (UI) |
| `/mobper/admin/api/users` | GET | Lista todos los usuarios con presets |
| `/mobper/admin/api/users/<id>` | GET | Obtiene detalle de un usuario |
| `/mobper/admin/api/users/<id>` | PUT | Actualiza datos de usuario |
| `/mobper/admin/api/users/<id>` | DELETE | Elimina usuario y sus datos |
| `/mobper/admin/api/users/<id>/toggle-active` | POST | Activa/desactiva usuario |
| `/mobper/admin/api/users/<id>/toggle-admin` | POST | Otorga/revoca permisos admin |
| `/mobper/admin/api/users/<id>/reset-password` | POST | Resetea contraseña |

### 17.2 Gestión de Usuarios

#### Crear Usuario (a través de /register)

```python
@mobper_bp.route('/api/register', methods=['POST'])
def api_register():
    """API: Registra un nuevo usuario en MovPer."""
    data = request.get_json()
    numero_socio = data.get('numero_socio', '').strip()
    nombre_completo = data.get('nombre_completo', '').strip()
    password = data.get('password', '').strip()
    
    # Validaciones
    if not numero_socio or not nombre_completo or not password:
        return jsonify({'success': False, 'error': 'Faltan datos'})
    
    # Verificar si ya existe
    existing = MobPerUser.query.filter_by(numero_socio=numero_socio).first()
    if existing:
        return jsonify({'success': False, 'error': 'Número de socio ya registrado'})
    
    # Crear usuario
    user = MobPerUser(
        numero_socio=numero_socio,
        nombre_completo=nombre_completo,
        is_active=True,
        is_admin=False
    )
    user.set_password(password)
    
    # Crear preset por defecto
    preset = PresetUsuario(
        user_id=user.id,
        nombre_formato=nombre_completo,
        departamento_formato='',
        jefe_directo_nombre='',
        hora_entrada_default=datetime.strptime('09:00:00', '%H:%M:%S').time(),
        tolerancia_segundos=600,
        dias_descanso=[5, 6],
        lista_inhabiles=[],
        vigente_desde=date.today()
    )
    
    db.session.add(user)
    db.session.add(preset)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Usuario registrado correctamente'})
```

---

## 18. CLIENTE BIOSTAR API

### 18.1 Inicialización y Autenticación

```python
class BioStarAPIClient:
    """Cliente para interactuar con la API de BioStar 2."""
    
    def __init__(self, host: str, username: str, password: str):
        self.host = host.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
        self.session = requests.Session()
        self.session.verify = False  # Desactivar verificación SSL
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def login(self) -> bool:
        """Autentica contra BioStar 2 con reintentos."""
        url = f"{self.host}/api/login"
        
        # BioStar requiere formato específico con objeto "User"
        payload = {
            "User": {
                "login_id": self.username,
                "password": self.password
            }
        }
        
        # Reintentar hasta 3 veces
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.post(
                    url, json=payload, 
                    headers={"Content-Type": "application/json"},
                    verify=False, timeout=30
                )
                
                if response.status_code == 200:
                    # Extraer token del header bs-session-id
                    self.token = response.headers.get('bs-session-id')
                    if self.token:
                        # Agregar token como cookie
                        self.session.cookies.set(
                            'bs-session-id', self.token,
                            domain=self.host.replace('https://', '').replace('http://', '')
                        )
                        return True
            except requests.exceptions.ConnectionError:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
        
        return False
```

### 18.2 Métodos Principales

| Método | Descripción |
|--------|-------------|
| `login()` | Autentica y obtiene token de sesión |
| `get_all_devices()` | Lista todos los dispositivos/lectores |
| `get_device_by_id(id)` | Obtiene un dispositivo específico |
| `search_events(conditions, limit)` | Busca eventos con filtros personalizados |
| `get_all_users(limit)` | Lista todos los usuarios de BioStar |
| `search_users(query, limit)` | Busca usuarios por nombre o ID |
| `get_all_doors()` | Lista todas las puertas configuradas |
| `open_door(door_id)` | Abre una puerta (desbloqueo temporal) |
| `unlock_door(door_id)` | Desbloquea una puerta permanentemente |
| `release_door(door_id)` | Libera una puerta (vuelve a modo normal) |

### 18.3 Búsqueda de Eventos (search_events)

```python
def search_events(self, conditions: List[Dict], limit: int = 1000, 
                 order_by: str = "datetime", descending: bool = True) -> List[Dict]:
    """
    Búsqueda genérica de eventos con filtros personalizados.
    
    Args:
        conditions: Lista de condiciones de filtrado
            - column: columna a filtrar (ej: "user_id.user_id", "datetime")
            - operator: tipo de operador
                - 0 = EQUAL
                - 3 = BETWEEN
                - 4 = CONTAINS
            - values: lista de valores
        limit: Cantidad máxima de registros
        order_by: Columna para ordenar
        descending: True = descendente, False = ascendente
    
    Returns:
        Lista de eventos con estructura:
        {
            'id': str,
            'datetime': str (ISO format),
            'event_type_id': {'code': str, 'name': str},
            'user_id': {'user_id': str, 'name': str},
            'device_id': {'id': str, 'name': str}
        }
    """
    url = f"{self.host}/api/events/search"
    
    payload = {
        "Query": {
            "limit": limit,
            "conditions": conditions,
            "orders": [{"column": order_by, "descending": descending}]
        }
    }
    
    response = self.session.post(
        url, json=payload,
        headers={"bs-session-id": self.token, "Content-Type": "application/json"},
        verify=False, timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        events = data.get('EventCollection', {}).get('rows', [])
        return events
    return []
```

### 18.4 Ejemplo de Uso en MovPer

```python
# Obtener eventos de un usuario en una quincena
conditions = [
    {"column": "user_id.user_id", "operator": 0, "values": [biostar_user_id]},
    {"column": "datetime", "operator": 3, "values": [
        inicio_quincena.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
        fin_quincena.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    ]}
]

eventos = client.search_events(conditions=conditions, limit=1000, descending=False)

# Procesar eventos
for evento in eventos:
    event_code = evento.get('event_type_id', {}).get('code')
    if event_code in ACCESS_GRANTED_CODES:  # Solo accesos concedidos
        dt_str = evento.get('datetime')
        dt_utc = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        dt_utc = pytz.UTC.localize(dt_utc)
        dt = dt_utc.astimezone(MEXICO_TZ)  # Convertir a CDMX
        # ... procesar
```

---

## 19. MANEJO DE ERRORES Y SEGURIDAD

### 19.1 Patrón de Manejo de Errores

En todas las rutas API se usa el patrón:

```python
@mobper_bp.route('/api/algo', methods=['POST'])
@mobper_login_required
def api_algo():
    try:
        data = request.get_json()
        
        # Validar datos
        if not data or 'campo' not in data:
            return jsonify({'success': False, 'error': 'Campo requerido'}), 400
        
        # Operación en BD
        db.session.add(objeto)
        db.session.commit()
        
        return jsonify({'success': True, 'data': resultado})
        
    except Exception as e:
        db.session.rollback()  # Importante: rollback en error
        import traceback
        traceback.print_exc()  # Log del stack trace
        return jsonify({'success': False, 'error': str(e)}), 500
```

### 19.2 Rollback de Sesiones

```python
try:
    # Múltiples operaciones
    incidencia.clasificacion = clasificacion
    incidencia.motivo_auto = motivo
    db.session.add(incidencia)
    db.session.commit()
    
except Exception as e:
    db.session.rollback()  # Deshacer cambios parciales
    return jsonify({'success': False, 'error': str(e)}), 500
```

### 19.3 After Request Cleanup

Para archivos temporales (Excel, ZIP):

```python
from flask import after_this_request

@mobper_bp.route('/generar-excel')
def generar_excel():
    output_path, filename = generar_formato_excel(...)
    
    # Registrar cleanup después de enviar respuesta
    @after_this_request
    def cleanup(response):
        try:
            os.remove(output_path)
        except Exception:
            pass
        return response
    
    return send_file(output_path, ...)
```

### 19.4 Validaciones de Seguridad

```python
# No puede desactivarse a sí mismo
if u.id == current.id:
    return jsonify({'success': False, 'error': 'No puedes desactivar tu propia cuenta'}), 400

# No puede quitarse admin a sí mismo
if u.id == current.id:
    return jsonify({'success': False, 'error': 'No puedes modificar tu propio rol'}), 400

# Validar contraseña mínima
if len(nueva) < 4:
    return jsonify({'success': False, 'error': 'Mínimo 4 caracteres'}), 400

# Verificar unicidad
existing = MobPerUser.query.filter_by(numero_socio=numero_socio).first()
if existing:
    return jsonify({'success': False, 'error': 'Número de socio ya registrado'})
```

---

## 20. UTILIDADES Y HELPERS

### 20.1 Normalización de Nombres

```python
def normalizar_nombre_biostar(nombre_biostar: str) -> str:
    """
    Convierte nombre de BioStar (APELLIDO1 APELLIDO2 NOMBRE1 NOMBRE2)
    a formato normal (Nombre1 Nombre2 Apellido1 Apellido2) con Title Case.
    
    BioStar guarda: "CETINA POOL RAUL ABEL"
    Resultado: "Raúl Abel Cetina Pool"
    """
    if not nombre_biostar:
        return ''
    
    partes = nombre_biostar.strip().split()
    
    if len(partes) == 4:
        # APELLIDO1 APELLIDO2 NOMBRE1 NOMBRE2 → NOMBRE1 NOMBRE2 APELLIDO1 APELLIDO2
        nombre_reordenado = f"{partes[2]} {partes[3]} {partes[0]} {partes[1]}"
    elif len(partes) == 3:
        nombre_reordenado = f"{partes[2]} {partes[0]} {partes[1]}"
    elif len(partes) == 2:
        nombre_reordenado = f"{partes[1]} {partes[0]}"
    else:
        nombre_reordenado = nombre_biostar
    
    return aplicar_title_case(nombre_reordenado)

def aplicar_title_case(texto: str) -> str:
    """
    Aplica Title Case respetando acentos.
    'RAUL ABEL CETINA POOL' → 'Raul Abel Cetina Pool'
    'MARÍA JOSÉ' → 'María José'
    """
    if not texto:
        return ''
    return ' '.join(palabra.capitalize() for palabra in texto.lower().split())
```

### 20.2 Formato de Fechas

```python
def formatear_fecha_espanol(fecha):
    """Formatea fecha como 'Lunes 28 de Enero'"""
    DIAS_SEMANA = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    MESES = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
             'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    
    dia_semana = DIAS_SEMANA[fecha.weekday()]
    mes = MESES[fecha.month]
    return f"{dia_semana} {fecha.day} de {mes}"

# Formato compacto para Excel
mes_corto = {1:'ene',2:'feb',3:'mar',4:'abr',5:'may',6:'jun',
             7:'jul',8:'ago',9:'sep',10:'oct',11:'nov',12:'dic'}
fecha_auth = f"{now.day:02d}-{mes_corto[now.month]}-{now.strftime('%y')}"
# Resultado: "15-ene-26"
```

### 20.3 Función now_cdmx()

```python
def now_cdmx():
    """Retorna la fecha/hora actual en zona horaria CDMX."""
    MEXICO_TZ = pytz.timezone('America/Mexico_City')
    return datetime.now(MEXICO_TZ)
```

### 20.4 Timezones en el Sistema

```python
# Constante global
MEXICO_TZ = pytz.timezone('America/Mexico_City')

# Convertir UTC a CDMX
dt_utc = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S.%fZ')
dt_utc = pytz.UTC.localize(dt_utc)
dt_cdmx = dt_utc.astimezone(MEXICO_TZ)

# Localizar datetime naive
inicio_dia = datetime.combine(fecha, datetime.min.time())
inicio_dia = MEXICO_TZ.localize(inicio_dia)
```

---

## 21. ESQUEMA COMPLETO DE RUTAS

### 21.1 Blueprint MovPer

| Método | Ruta | Handler | Descripción | Auth |
|--------|------|---------|-------------|------|
| GET | `/mobper/` | `mobper_root` | Redirect a login/dashboard | - |
| GET/POST | `/mobper/login` | `login` | Login de usuarios | - |
| GET | `/mobper/logout` | `logout` | Cerrar sesión | Sí |
| GET | `/mobper/register` | `register_page` | Página de registro | - |
| POST | `/mobper/api/register` | `api_register` | API registro | - |
| GET | `/mobper/checklist` | `checklist` | Checklist quincena | Sí |
| GET | `/mobper/config` | `config` | Configuración horarios | Sí |
| POST | `/mobper/config` | `config` | Guardar config | Sí |
| GET | `/mobper/api/incidencias` | `api_incidencias` | JSON incidencias | Sí |
| POST | `/mobper/api/clasificar` | `api_clasificar` | Clasificar falta | Sí |
| POST | `/mobper/api/toggle-justificacion` | `toggle_justificacion` | Toggle retardo | Sí |
| POST | `/mobper/api/toggle-justificacion-salida` | `toggle_justificacion_salida` | Toggle salida | Sí |
| POST | `/mobper/api/toggle-justificacion-olvido` | `toggle_justificacion_olvido` | Toggle olvido | Sí |
| POST | `/mobper/api/patch-hora-entrada` | `api_patch_hora_entrada` | Parche hora | Sí |
| GET | `/mobper/api/periodos-vacaciones` | `api_periodos_vacaciones` | Períodos vacaciones | Sí |
| GET | `/mobper/generar-excel` | `generar_excel` | Generar Excel | Sí |
| POST | `/mobper/api/impersonate` | `api_impersonate` | Impersonar usuario | Admin |
| POST | `/mobper/api/stop-impersonate` | `api_stop_impersonate` | Detener impersonación | Sí |
| GET | `/mobper/grupo` | `grupo_dashboard` | Dashboard grupo | Admin |
| GET | `/mobper/grupo/api/resumen` | `grupo_api_resumen` | Resumen grupo | Admin |
| GET | `/mobper/grupo/api/miembro/<id>/detalle` | `grupo_api_miembro_detalle` | Detalle miembro | Admin |
| GET | `/mobper/grupo/api/generar-excel/<id>` | `grupo_api_generar_excel_miembro` | Excel miembro | Admin |
| GET | `/mobper/grupo/api/generar-excel-todos` | `grupo_api_generar_excel_todos` | Excel todos | Admin |
| GET | `/mobper/admin` | `admin_panel` | Panel admin | Admin |
| GET | `/mobper/admin/api/users` | `admin_api_users` | Lista usuarios | Admin |
| GET | `/mobper/admin/api/users/<id>` | `admin_api_get_user` | Obtener usuario | Admin |
| PUT | `/mobper/admin/api/users/<id>` | `admin_api_update_user` | Actualizar usuario | Admin |
| DELETE | `/mobper/admin/api/users/<id>` | `admin_api_delete_user` | Eliminar usuario | Admin |
| POST | `/mobper/admin/api/users/<id>/toggle-active` | `admin_api_toggle_active` | Toggle activo | Admin |
| POST | `/mobper/admin/api/users/<id>/toggle-admin` | `admin_api_toggle_admin` | Toggle admin | Admin |
| POST | `/mobper/admin/api/users/<id>/reset-password` | `admin_api_reset_password` | Reset password | Admin |

### 21.2 Flujo de Autenticación

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FLUJO DE AUTENTICACIÓN                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   1. Usuario accede a /mobper/                                              │
│      └── Si no tiene 'mobper_user_id' en session → redirect /mobper/login  │
│                                                                              │
│   2. En /mobper/login                                                       │
│      └── POST: numero_socio + password                                     │
│          └── MobPerUser.query.filter_by(numero_socio=...).first()         │
│          └── user.check_password(password)                                  │
│          └── Si OK: session['mobper_user_id'] = user.id                     │
│          └── redirect /mobper/checklist                                     │
│                                                                              │
│   3. @mobper_login_required                                                │
│      └── Verifica 'mobper_user_id' en session                              │
│      └── Si no existe → redirect login                                     │
│                                                                              │
│   4. @mobper_admin_required                                                │
│      └── Verifica login + user.is_admin == True                            │
│      └── Si no es admin → redirect checklist + flash 'Acceso denegado'       │
│                                                                              │
│   5. Impersonación (admin como otro usuario)                                │
│      └── Admin hace POST /api/impersonate con user_id objetivo              │
│      └── session['mobper_impersonate_id'] = user_id                         │
│      └── get_current_mobper_user() retorna usuario objetivo                 │
│      └── En UI se muestra banner: "Viendo como: [Nombre] [X]"              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 22. CONCLUSIÓN

El sistema MovPer es una solución completa de gestión de asistencias que:

1. **Integra** datos de BioStar 2 con procesamiento inteligente
2. **Clasifica** automáticamente incidencias con lógica de horarios configurable
3. **Permite** justificaciones manuales mediante toggles intuitivos
4. **Genera** formatos Excel F-RH-18 completos y profesionales
5. **Gestiona** vacaciones en formato separado
6. **Soporta** múltiples empresas con logos personalizados
7. **Incluye** dashboard grupal para supervisores

El flujo de datos es optimizado mediante:
- Cache de sesión BioStar (5 minutos)
- Cache de eventos por quincena (5 minutos)
- Carga lazy de datos
- Correcciones automáticas por día configurable

La arquitectura permite que cada usuario gestione sus propias justificaciones mientras mantiene un registro auditado de todas las clasificaciones y cambios.

---

**Fin del Reporte**
