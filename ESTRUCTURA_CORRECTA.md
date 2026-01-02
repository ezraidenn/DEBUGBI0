# 📋 Estructura Correcta del Sistema de Emergencias

## 🎯 Menú de Navegación (Admin)

```
📊 Dashboard
👥 Usuarios
🏢 Zonas y Grupos          → /emergency/config
🚨 Emergencias             → /emergency/emergency
🛡️ Botón de Pánico         → /panic-button
⚙️ Configuración
```

---

## 🏢 Pantalla: "Zonas y Grupos" (`/emergency/config`)

### Propósito:
Configuración completa del sistema de emergencias

### Funcionalidades:

#### 1. **Gestión de Zonas**
- Crear zonas físicas (Casa Club, Gimnasio, Oficinas, etc.)
- Editar/Eliminar zonas
- Asignar color e icono a cada zona

#### 2. **Asignar Dispositivos a Zonas**
- Seleccionar zona
- Agregar checadores/dispositivos a la zona
- Los dispositivos asignados se desbloquearán automáticamente al activar emergencia
- **Importante:** Estos dispositivos emitirán alarma y desbloquearán puertas

#### 3. **Gestión de Grupos dentro de Zonas**
- Crear grupos/departamentos dentro de cada zona
- Ejemplos: IT, Desarrollo, Mantenimiento, Recepción

#### 4. **Asignar Usuarios a Grupos**
- Buscar usuarios de BioStar
- Agregar usuarios a grupos específicos
- Los usuarios asignados aparecerán en el pase de lista

### Archivo:
- `webapp/templates/emergency_config.html`

---

## 🚨 Pantalla: "Emergencias" (`/emergency/emergency`)

### Propósito:
Activar emergencias y hacer pase de lista en tiempo real

### Flujo de Uso:

#### 1. **Seleccionar Zona**
- Se muestran todas las zonas configuradas
- Click en una zona para seleccionarla

#### 2. **Activar Emergencia**
- Botón grande rojo: "ACTIVAR EMERGENCIA"
- Modal de confirmación con opciones:
  - ☑️ Desbloquear puertas (automático)
  - ☑️ Activar alarmas (opcional)

#### 3. **Acciones Automáticas al Activar:**
- Desbloquea TODOS los dispositivos asignados a la zona
- Activa alarmas en los dispositivos (si se seleccionó)
- Crea pase de lista con todos los usuarios de los grupos de la zona
- Guarda IDs de puertas desbloqueadas para cerrarlas después

#### 4. **Pase de Lista en Tiempo Real**
- Muestra estadísticas: Total, Presentes, Ausentes, Pendientes
- Lista de usuarios agrupados por grupo
- Marcar manualmente como presente/ausente
- Auto-detección de presencia basada en eventos de BioStar

#### 5. **Resolver Emergencia**
- Botón: "Resolver Emergencia"
- Cierra automáticamente TODAS las puertas que fueron desbloqueadas
- Desactiva alarmas
- Marca emergencia como resuelta

### Archivo:
- `webapp/templates/emergency_center.html`

---

## 🛡️ Pantalla: "Botón de Pánico" (`/panic-button`)

### Propósito:
Activación rápida individual por dispositivo

### Características:
- Selector de dispositivo (dropdown)
- Botón circular grande (250x250px)
- Modal con checkbox de alarma (**desactivado por defecto**)
- Animación pulsante cuando está activo
- Control individual (no afecta otros dispositivos)

### Diferencia con Emergencias:
- **Pánico:** Individual, rápido, un solo dispositivo
- **Emergencias:** Zona completa, múltiples dispositivos, pase de lista

### Archivo:
- `webapp/templates/panic_button.html`

---

## 🗄️ Modelos de Base de Datos

### Sistema de Emergencias:
```python
Zone                # Zonas físicas
Group               # Grupos dentro de zonas
GroupMember         # Usuarios asignados a grupos
ZoneDevice          # Dispositivos asignados a zonas
EmergencySession    # Sesiones de emergencia activas
RollCallEntry       # Pase de lista por emergencia
```

### Sistema de Pánico:
```python
PanicModeStatus     # Estado actual por dispositivo
PanicModeLog        # Log de acciones
```

---

## 🔄 Flujo Completo de Uso

### Configuración Inicial (Una vez):

1. **Ir a "Zonas y Grupos"**
2. **Crear Zonas:**
   - Casa Club
   - Gimnasio
   - Oficinas
   - etc.

3. **Asignar Dispositivos a cada Zona:**
   - Seleccionar zona
   - Agregar checadores que están en esa zona física
   - Estos se desbloquearán al activar emergencia

4. **Crear Grupos dentro de cada Zona:**
   - IT
   - Desarrollo
   - Mantenimiento
   - Recepción

5. **Asignar Usuarios a Grupos:**
   - Buscar usuarios de BioStar
   - Agregar a grupos correspondientes

### Uso en Emergencia:

1. **Ir a "Emergencias"**
2. **Seleccionar zona afectada**
3. **Click en "ACTIVAR EMERGENCIA"**
4. **Confirmar opciones:**
   - Desbloquear puertas: ✅ (siempre)
   - Activar alarmas: ☐ (opcional)
5. **Sistema automáticamente:**
   - Desbloquea todos los dispositivos de la zona
   - Activa alarmas (si se seleccionó)
   - Crea pase de lista
6. **Hacer pase de lista:**
   - Marcar presentes/ausentes manualmente
   - O esperar auto-detección por eventos
7. **Al terminar:**
   - Click en "Resolver Emergencia"
   - Sistema cierra todas las puertas automáticamente

---

## 📁 Archivos Clave

### Templates:
- `emergency_config.html` - Configuración de zonas/grupos
- `emergency_center.html` - Activación y pase de lista
- `panic_button.html` - Botón de pánico individual

### Backend:
- `emergency_routes.py` - Todas las rutas y API
- `models.py` - Modelos de BD
- `door_control.py` - Control de puertas y alarmas

---

## ✅ Estado Actual

- ✅ Archivos copiados desde LOGSCHECA
- ✅ Modelos de BD creados
- ✅ Rutas configuradas
- ✅ Menú actualizado con 3 opciones separadas
- ✅ Tablas migradas

**Listo para usar después de reiniciar el servidor.**
