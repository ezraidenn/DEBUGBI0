# 📋 Sistema de Clasificación Individual por Día

## ✅ IMPLEMENTADO

### 1. **Modelo de Base de Datos**
```python
class IncidenciaDia(db.Model):
    """Clasificación individual por día"""
    user_id: int
    fecha: date
    estado_auto: str  # A_TIEMPO, RETARDO, FALTA, DESCANSO, INHABIL
    clasificacion: str  # PERMISO_GOCE, REMOTO, GUARDIA, etc.
    observaciones: text
    hora_entrada: time
    minutos_diferencia: int
```

### 2. **APIs Implementadas**

#### `/mobper/api/clasificar-dia` (POST)
Guardar clasificación de **un día específico**

```json
{
  "fecha": "2026-01-16",
  "clasificacion": "REMOTO",
  "observaciones": "Trabajo desde casa por proyecto X"
}
```

#### `/mobper/api/clasificar-multiple` (POST)
Aplicar clasificación a **múltiples días** (atajos rápidos)

```json
{
  "fechas": ["2026-01-16", "2026-01-20", "2026-01-23"],
  "clasificacion": "GUARDIA",
  "observaciones": "Guardia de fin de semana"
}
```

### 3. **Opciones de Clasificación**

| Código | Descripción |
|--------|-------------|
| `PERMISO_GOCE` | Permiso con goce de sueldo |
| `PERMISO_SIN_GOCE` | Permiso sin goce de sueldo |
| `VACACIONES` | Vacaciones |
| `REMOTO` | Trabajo remoto |
| `GUARDIA` | Guardia |
| `JUSTIFICADO` | Retardo/falta justificado |
| `INHABIL` | Día inhábil |
| `INCAPACIDAD` | Incapacidad médica |
| `SIN_CLASIFICAR` | Sin clasificar |

### 4. **Ejemplo de Uso**

**Escenario:** Quincena del 16-31 Enero

- **16 Ene:** Retardo 11 min → Clasificar como `JUSTIFICADO` (Junta con cliente)
- **19 Ene:** Retardo 20 min → Clasificar como `REMOTO` (Trabajó desde casa)
- **20 Ene:** Retardo 16 min → Clasificar como `REMOTO` (Trabajó desde casa)
- **21 Ene:** Retardo 21 min → Clasificar como `GUARDIA` (Guardia nocturna)
- **26 Ene:** Falta → Clasificar como `PERMISO_GOCE` (Permiso personal)

**Cada día tiene su propia clasificación independiente.**

---

## 🔄 FLUJO DE TRABAJO

1. **Usuario ve su checklist** → Sistema muestra incidencias automáticas
2. **Usuario clasifica cada día** → Dropdown individual por día
3. **Usuario agrega observaciones** → Campo de texto opcional
4. **Sistema guarda en BD** → Tabla `mobper_incidencias_dia`
5. **Usuario puede usar atajos** → Clasificar múltiples días a la vez

---

## 🎯 PRÓXIMOS PASOS

### Actualizar Template del Checklist
Agregar para cada día:
```html
<select class="clasificacion-dropdown" data-fecha="2026-01-16">
    <option value="">Sin clasificar</option>
    <option value="PERMISO_GOCE">Permiso con goce</option>
    <option value="PERMISO_SIN_GOCE">Permiso sin goce</option>
    <option value="VACACIONES">Vacaciones</option>
    <option value="REMOTO">Trabajo remoto</option>
    <option value="GUARDIA">Guardia</option>
    <option value="JUSTIFICADO">Justificado</option>
    <option value="INHABIL">Día inhábil</option>
    <option value="INCAPACIDAD">Incapacidad</option>
</select>

<textarea class="observaciones" data-fecha="2026-01-16" 
          placeholder="Observaciones..."></textarea>

<button onclick="guardarClasificacion('2026-01-16')">
    Guardar
</button>
```

### Hacer Funcionales los Atajos Rápidos
```javascript
// Justificar todos los retardos
function justificarRetardos() {
    const fechasRetardos = ['2026-01-16', '2026-01-19', ...];
    fetch('/mobper/api/clasificar-multiple', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            fechas: fechasRetardos,
            clasificacion: 'JUSTIFICADO',
            observaciones: 'Retardo justificado'
        })
    });
}

// Todas las faltas → Remoto
function faltasRemoto() {
    const fechasFaltas = ['2026-01-26'];
    fetch('/mobper/api/clasificar-multiple', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            fechas: fechasFaltas,
            clasificacion: 'REMOTO',
            observaciones: 'Trabajo remoto'
        })
    });
}
```

### Resumen con Desglose
```
📊 Resumen de Quincena

✅ A tiempo: 2 días
⚠️ Retardos: 8 días
   - 3 justificados
   - 2 trabajo remoto
   - 2 guardia
   - 1 sin clasificar
❌ Faltas: 1 día
   - 1 permiso con goce
🏖️ Descansos: 5 días
```

---

## 🚀 SERVIDOR CORRIENDO

**URL:** http://127.0.0.1:5000/mobper/login

**Tablas creadas:**
- `mobper_users`
- `mobper_presets`
- `mobper_incidencias_dia` ← **NUEVA**
- `mobper_periodos`
