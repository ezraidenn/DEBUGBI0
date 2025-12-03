# Diseño: Nueva Arquitectura de Permisos y Filtros

## 📋 Resumen de Requerimientos

### 1. Filtros de Eventos
- **Por defecto**: Solo mostrar accesos concedidos
- **Filtro toggleable**: Poder ver todos los eventos si se desea
- Aplica tanto a contadores como a listados
- Mantener funcionamiento en tiempo real

### 2. Lógica de Pares (Entrada/Salida)
- **Solo para tipo "Checador"** (no aplica a "Puerta")
- Si usuario tiene **2 registros** en el día = Entró Y Salió ✅
- Si usuario tiene **1 registro** = Entró pero NO salió ⚠️
- Vista especial: "Usuarios que no han salido"

### 3. Clasificación de Dispositivos
- **Tipos de dispositivo**: Checador, Puerta, Facial, etc.
- **Etiquetas personalizadas**: Admin crea etiquetas/grupos
- **Asignación manual**: Admin asigna dispositivos a categorías

### 4. Control de Permisos
- **Admin**: Ve todos los dispositivos
- **Usuario normal**: Solo ve dispositivos asignados
- Asignación desde panel de configuración de usuarios

---

## 🗄️ Modelo de Base de Datos

### Nuevas Tablas

```python
# 1. Categorías/Etiquetas de dispositivos
class DeviceCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    color = db.Column(db.String(7), default='#6c757d')  # Color hex para UI
    icon = db.Column(db.String(50), default='bi-hdd')   # Bootstrap icon
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 2. Configuración de dispositivos (info local)
class DeviceConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, unique=True, nullable=False)  # ID de BioStar
    device_type = db.Column(db.String(20), default='checador')      # checador, puerta, facial
    category_id = db.Column(db.Integer, db.ForeignKey('device_category.id'))
    alias = db.Column(db.String(100))                               # Nombre personalizado
    location = db.Column(db.String(200))                            # Ubicación
    supports_pairs = db.Column(db.Boolean, default=True)            # ¿Aplica lógica de pares?
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    category = db.relationship('DeviceCategory', backref='devices')

# 3. Permisos de usuario por dispositivo
class UserDevicePermission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    device_id = db.Column(db.Integer, nullable=False)  # ID de BioStar
    can_view = db.Column(db.Boolean, default=True)
    can_export = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='device_permissions')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'device_id', name='unique_user_device'),
    )
```

### Modificaciones a User existente

```python
class User(db.Model):
    # ... campos existentes ...
    
    # Nuevos campos
    can_see_all_events = db.Column(db.Boolean, default=False)  # Ver eventos no-concedidos
    can_manage_devices = db.Column(db.Boolean, default=False)  # Acceso a config dispositivos
```

---

## 🎨 Nuevas Pantallas

### 1. Configuración de Dispositivos (`/config/devices`)

```
┌─────────────────────────────────────────────────────────────┐
│ ⚙️ Configuración de Dispositivos                    [+ Categoría] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 🏷️ CATEGORÍAS                                               │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│ │ 🟢 Entrada  │ │ 🔴 Salida   │ │ 🟡 Gimnasio │            │
│ │ 3 devices   │ │ 2 devices   │ │ 1 device    │            │
│ └─────────────┘ └─────────────┘ └─────────────┘            │
│                                                             │
│ 📋 DISPOSITIVOS                           [Filtrar ▼]       │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 📟 Checador Entrada Principal                          │ │
│ │ ID: 1234 | Tipo: Checador | Cat: Entrada | Pares: ✅   │ │
│ │                                    [Editar] [Permisos] │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ 🚪 Puerta Gimnasio                                     │ │
│ │ ID: 5678 | Tipo: Puerta | Cat: Gimnasio | Pares: ❌    │ │
│ │                                    [Editar] [Permisos] │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 2. Modal Editar Dispositivo

```
┌─────────────────────────────────────────┐
│ ✏️ Editar Dispositivo                   │
├─────────────────────────────────────────┤
│ Nombre/Alias: [Entrada Principal    ]   │
│ Ubicación:    [Lobby Edificio A     ]   │
│                                         │
│ Tipo de Dispositivo:                    │
│ ◉ Checador (huella/facial entrada)      │
│ ○ Puerta (solo salida sin registro)     │
│ ○ Facial                                │
│                                         │
│ Categoría: [Entrada         ▼]          │
│                                         │
│ ☑️ Aplica lógica de pares               │
│    (entrada/salida)                     │
│                                         │
│            [Cancelar] [Guardar]         │
└─────────────────────────────────────────┘
```

### 3. Panel de Usuario - Asignación Dispositivos

```
┌─────────────────────────────────────────┐
│ 👤 Editar Usuario: juan.perez           │
├─────────────────────────────────────────┤
│ ... campos existentes ...               │
│                                         │
│ ─────────────────────────────────────── │
│ 📟 DISPOSITIVOS ASIGNADOS               │
│                                         │
│ ☑️ Entrada Principal (Checador)         │
│ ☑️ Salida Principal (Checador)          │
│ ☐ Gimnasio (Puerta)                     │
│ ☐ Comedor (Facial)                      │
│                                         │
│ ─────────────────────────────────────── │
│ 🔐 PERMISOS ESPECIALES                  │
│                                         │
│ ☐ Ver todos los eventos (no solo OK)   │
│ ☐ Gestionar dispositivos               │
│                                         │
│            [Cancelar] [Guardar]         │
└─────────────────────────────────────────┘
```

---

## 🔄 Lógica de Pares (Entrada/Salida)

### Algoritmo

```python
def calcular_estado_usuarios(device_id, fecha):
    """
    Retorna diccionario con estado de cada usuario:
    - 'completo': Tiene entrada Y salida
    - 'pendiente': Solo tiene entrada, no ha salido
    - 'irregular': Más de 2 registros (revisar)
    """
    # 1. Obtener todos los accesos CONCEDIDOS del día
    eventos = get_eventos_concedidos(device_id, fecha)
    
    # 2. Agrupar por user_id
    por_usuario = {}
    for evento in eventos:
        if evento.user_id not in por_usuario:
            por_usuario[evento.user_id] = []
        por_usuario[evento.user_id].append(evento)
    
    # 3. Clasificar
    resultado = {
        'completos': [],    # 2 registros = entrada + salida
        'pendientes': [],   # 1 registro = solo entrada
        'irregulares': []   # 3+ registros = revisar
    }
    
    for user_id, eventos_usuario in por_usuario.items():
        count = len(eventos_usuario)
        primer_evento = eventos_usuario[0]
        
        info = {
            'user_id': user_id,
            'user_name': primer_evento.user_name,
            'eventos': eventos_usuario,
            'primer_registro': eventos_usuario[0].datetime,
            'ultimo_registro': eventos_usuario[-1].datetime if count > 1 else None
        }
        
        if count == 2:
            resultado['completos'].append(info)
        elif count == 1:
            resultado['pendientes'].append(info)
        else:  # count > 2
            resultado['irregulares'].append(info)
    
    return resultado
```

### Vista "No han salido"

```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️ Usuarios que NO han salido              Checador: Entrada │
├─────────────────────────────────────────────────────────────┤
│ 👤 JUAN PÉREZ          │ Entrada: 08:15:23 │ ⏱️ 2h 15min    │
│ 👤 MARÍA GARCÍA        │ Entrada: 09:30:45 │ ⏱️ 1h 00min    │
│ 👤 CARLOS LÓPEZ        │ Entrada: 10:00:12 │ ⏱️ 0h 30min    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎛️ Filtros en Tiempo Real

### UI de Filtros

```
┌─────────────────────────────────────────────────────────────┐
│ 🔍 FILTROS                                                  │
│                                                             │
│ [✅ Solo Accesos OK] [👥 No han salido] [📋 Todos]          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Implementación SSE con Filtros

```javascript
// El filtro se envía como parámetro al SSE
function startRealtimeSSE(filter = 'granted_only') {
    const url = `/api/events/stream/${deviceId}?filter=${filter}`;
    eventSource = new EventSource(url);
    // ...
}

// Cambiar filtro sin reconectar (enviar mensaje)
function changeFilter(newFilter) {
    // Opción 1: Reconectar con nuevo filtro
    stopRealtimeSSE();
    startRealtimeSSE(newFilter);
    
    // Opción 2: Filtrar en cliente (mejor UX)
    currentFilter = newFilter;
    filterDisplayedEvents();
}
```

---

## 📁 Estructura de Archivos Nuevos

```
webapp/
├── models.py                 # Agregar nuevos modelos
├── templates/
│   ├── config/
│   │   ├── devices.html      # Configuración de dispositivos
│   │   └── categories.html   # Gestión de categorías
│   └── partials/
│       ├── device_modal.html # Modal editar dispositivo
│       └── filter_bar.html   # Barra de filtros reutilizable
├── static/
│   └── js/
│       ├── filters.js        # Lógica de filtros
│       └── pairs.js          # Lógica de pares
└── app.py                    # Nuevas rutas
```

---

## 🚀 Plan de Implementación

### Fase 1: Base de Datos y Modelos (Actual)
1. ✅ Crear modelos DeviceCategory, DeviceConfig, UserDevicePermission
2. ✅ Migrar base de datos
3. ✅ Crear datos iniciales (categorías por defecto)

### Fase 2: Configuración de Dispositivos
1. Página de configuración `/config/devices`
2. CRUD de categorías
3. Edición de dispositivos (tipo, categoría, pares)

### Fase 3: Filtros y Lógica
1. Filtro "solo accesos concedidos" (por defecto)
2. Lógica de pares para checadores
3. Vista "usuarios que no han salido"

### Fase 4: Permisos de Usuario
1. Asignación de dispositivos a usuarios
2. Filtrar dashboard por permisos
3. Permisos especiales (ver todos eventos, gestionar)

---

## ✅ Decisiones de Diseño

| Decisión | Opción Elegida | Razón |
|----------|---------------|-------|
| Filtro por defecto | Solo accesos OK | Reduce ruido, muestra lo relevante |
| Lógica de pares | Solo en "Checador" | Puertas no registran salida |
| Conteo de pares | 2 = completo, 1 = pendiente | Simple y efectivo |
| Permisos | Por dispositivo | Flexibilidad máxima |
| Categorías | Creadas por admin | Personalización según necesidad |

---

¿Procedo con la implementación? Empezaré por los modelos de BD.
