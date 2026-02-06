# 📋 MÓDULO MOBPER - PLANEACIÓN COMPLETA V2.0
## Sistema de Regularización de Asistencias Quincenal

> **Versión:** 2.0 - Actualizada con reglas de negocio confirmadas  
> **Fecha:** 30 de enero de 2026  
> **Diseño:** Mobile-First con código de colores  
> **Autor:** Raul Abel Cetina Pool

---

## 📑 ÍNDICE

1. [Principios Rectores](#principios-rectores)
2. [Producto Final](#producto-final)
3. [Presets y Configuración](#presets)
4. [Motor de Cálculo](#motor-calculo)
5. [Checklist Interactivo](#checklist)
6. [Persistencia y Auditoría](#persistencia)
7. [Generación de PDF](#generacion-pdf)
8. [Formato MOTIVO y Fechas](#formato-motivo)
9. [Mapeo de Círculos](#mapeo-circulos)
10. [Casos Especiales](#casos-especiales)
11. [Arquitectura Técnica](#arquitectura)

---

## 🎯 PRINCIPIOS RECTORES {#principios-rectores}

### ✅ Regla de Oro: NUNCA MODIFICAR EL FORMATO

1. **Plantilla inmutable:** El archivo Excel `F-RH-18-MIT-FORMATO-DE-MOVIMIENTO-DE-PERSONAL-3(1).xlsx` es sagrado
2. **Solo rellenar:** Escribir en celdas específicas y marcar círculos mediante overlay en PDF
3. **PDF sellado:** El producto final es un PDF con círculos pintados por ReportLab + pypdf
4. **Auditoría total:** Cada decisión queda registrada (qué, quién, cuándo, por qué)

---

## 📱 PRODUCTO FINAL {#producto-final}

### Un módulo de regularización quincenal que:

```
┌─────────────────────────────────────────────────────────┐
│  1. 🔍 TOMA primer registro del día desde BioStar       │
│     └─> Solo eventos ACCESS_GRANTED                    │
│     └─> Zona horaria: America/Merida                   │
│                                                         │
│  2. ⚙️ APLICA preset de usuario                         │
│     └─> Horario de entrada + tolerancia (10 min)       │
│     └─> Días de descanso (varía por área)              │
│     └─> Días inhábiles (catálogo oficial México)       │
│                                                         │
│  3. 🧮 CALCULA incidencias automáticas                  │
│     └─> A_TIEMPO: llegó dentro de tolerancia           │
│     └─> RETARDO: llegó después de tolerancia           │
│     └─> FALTA: no tiene checada                        │
│                                                         │
│  4. ✏️ PRESENTA checklist interactivo (mobile-first)    │
│     └─> Solo muestra RETARDOS y FALTAS                 │
│     └─> Clasificación rápida con atajos                │
│     └─> Validaciones y excepciones manuales            │
│                                                         │
│  5. 📄 GENERA PDF final                                 │
│     └─> Rellena celdas del Excel                       │
│     └─> Convierte a PDF con LibreOffice                │
│     └─> Pinta círculos con overlay (ReportLab+pypdf)   │
└─────────────────────────────────────────────────────────┘
```

---

## ⚙️ PRESETS Y CONFIGURACIÓN {#presets}

### 🎨 Código de Colores para UI

| Color | Significado | Uso | Requiere Acción |
|-------|-------------|-----|-----------------|
| 🟢 **Verde** | A tiempo | Llegó dentro de tolerancia | ❌ No |
| 🟡 **Amarillo** | Retardo | Llegó tarde (>10 min) | ✅ Sí - Justificar |
| 🔴 **Rojo** | Falta | Sin checada | ✅ Sí - Justificar |
| 🔵 **Azul** | Día inhábil | Festivo oficial | ❌ No aplica |
| ⚪ **Gris** | Descanso | Sábado/Domingo/etc | ❌ No aplica |

### 📝 Tabla: PresetUsuario

**Propósito:** Configuración base del usuario que se reutiliza cada quincena

| Campo | Tipo | Ejemplo | Descripción | Editable |
|-------|------|---------|-------------|----------|
| `user_id` | INT | 123 | ID del usuario (FK a User) | ❌ |
| `nombre_formato` | VARCHAR(100) | "Raul Abel Cetina Pool" | Nombre completo para documento | ✅ |
| `departamento_formato` | VARCHAR(50) | "TI" | Departamento para documento | ✅ |
| `jefe_directo_nombre` | VARCHAR(100) | "Juan Pérez" | Jefe que autoriza | ✅ |
| `hora_entrada_default` | TIME | 09:00:00 | Hora de entrada estándar | ✅ |
| `tolerancia_segundos` | INT | 600 | **10 minutos para TODOS** | ❌ |
| `dias_descanso` | JSON | [6,7] | Días de la semana (0=Lun, 6=Sáb) | ✅ |
| `lista_inhabiles` | JSON | ["2026-01-01", "2026-02-03"] | Días festivos oficiales | ✅ |
| `modo_redondeo` | ENUM | "EXACTO" | Segundos exactos (no redondear) | ❌ |
| `vigente_desde` | DATE | 2026-01-01 | Inicio de vigencia | ✅ |
| `vigente_hasta` | DATE | NULL | Fin (NULL = activo) | ✅ |
| `created_at` | TIMESTAMP | - | Fecha de creación | ❌ |
| `updated_at` | TIMESTAMP | - | Última actualización | ❌ |

**🔧 Comportamiento:**
- Se guarda **1 vez** al configurar usuario
- Se **edita** cuando cambia horario/departamento/jefe
- Guarda el **último** (no historial de versiones)
- Siguiente quincena: **abrir → revisar → generar** (3 clics)

### 🔄 Tabla: ExcepcionHorario

**Propósito:** Excepciones puntuales para días específicos (juntas, eventos, etc.)

| Campo | Tipo | Ejemplo | Descripción |
|-------|------|---------|-------------|
| `id` | INT | 1 | PK autoincremental |
| `user_id` | INT | 123 | FK a User |
| `fecha` | DATE | 2026-01-15 | Día específico |
| `hora_entrada_override` | TIME | 10:00:00 | Hora de entrada excepcional |
| `tolerancia_override_segundos` | INT | NULL | Tolerancia (NULL = usa preset) |
| `motivo` | VARCHAR(200) | "Junta temprano" | Razón de la excepción |
| `created_by` | INT | 123 | Usuario que creó |
| `created_at` | TIMESTAMP | - | Fecha de creación |

**📌 Reglas:**
- Si existe excepción para ese día → **manda sobre el preset**
- Tolerancia: si `tolerancia_override_segundos` es NULL → usa `PresetUsuario.tolerancia_segundos`
- **Se configura manualmente desde el checklist** (botón "Agregar excepción")
- Validación: no permitir excepciones en días inhábiles o descansos

---

## 🧮 MOTOR DE CÁLCULO DE INCIDENCIAS {#motor-calculo}

### 📊 Flujo de Decisión Completo

```
Para cada día D en la quincena (1-15 o 16-último):

┌─────────────────────────────────────────────────────────┐
│ PASO 1: Clasificar tipo de día                         │
├─────────────────────────────────────────────────────────┤
│ ¿D ∈ lista_inhabiles?                                   │
│   SÍ → 🔵 INHABIL (no aplica, fin)                      │
│   NO → Continuar                                        │
│                                                         │
│ ¿weekday(D) ∈ dias_descanso?                            │
│   SÍ → ⚪ DESCANSO (no aplica, fin)                      │
│   NO → D es LABORAL, continuar                          │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ PASO 2: Obtener primer registro del día                │
├─────────────────────────────────────────────────────────┤
│ primer_registro = MIN(timestamp)                        │
│   WHERE fecha = D                                       │
│   AND evento_tipo = 'ACCESS_GRANTED'                    │
│   AND user_id = {user_id}                               │
│                                                         │
│ Zona horaria: America/Merida (Yucatán)                 │
│ Si hay múltiples checadas → solo importa la PRIMERA    │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ PASO 3: Calcular hora objetivo y límite                │
├─────────────────────────────────────────────────────────┤
│ ¿Existe ExcepcionHorario para D?                        │
│   SÍ → hora_obj = ExcepcionHorario.hora_entrada_override│
│   NO  → hora_obj = PresetUsuario.hora_entrada_default   │
│                                                         │
│ limite = hora_obj + 600 segundos (10 minutos)          │
│                                                         │
│ Ejemplo:                                                │
│   hora_obj = 09:00:00                                   │
│   limite   = 09:10:00                                   │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ PASO 4: Determinar estado automático                   │
├─────────────────────────────────────────────────────────┤
│ ¿primer_registro es NULL?                               │
│   SÍ → 🔴 FALTA (inasistencia)                          │
│   NO → Continuar                                        │
│                                                         │
│ ¿primer_registro <= limite?                             │
│   SÍ → 🟢 A_TIEMPO (llegó a tiempo)                     │
│   NO → 🟡 RETARDO (llegó tarde)                         │
└─────────────────────────────────────────────────────────┘
```

### ✅ Tabla de Estados Finales

| Condición | Estado | Color | Mostrar en Checklist | Requiere Justificación |
|-----------|--------|-------|----------------------|------------------------|
| D ∈ inhábiles | 🔵 INHABIL | Azul | ❌ No (colapsado) | ❌ No aplica |
| D ∈ descansos | ⚪ DESCANSO | Gris | ❌ No (colapsado) | ❌ No aplica |
| LABORAL + sin checada | 🔴 FALTA | Rojo | ✅ Sí (expandido) | ✅ Sí |
| LABORAL + checada ≤ límite | 🟢 A_TIEMPO | Verde | ❌ No (colapsado) | ❌ No |
| LABORAL + checada > límite | 🟡 RETARDO | Amarillo | ✅ Sí (expandido) | ✅ Sí |

**🔒 Garantía:** Este algoritmo es determinista, reproducible y auditable.

---

## ✏️ CHECKLIST INTERACTIVO (UX Mobile-First) {#checklist}

### 📱 Diseño de Pantalla Principal

```
┌─────────────────────────────────────────────────────────┐
│  📋 Movimiento de Personal                              │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                         │
│  👤 Raul Abel Cetina Pool                               │
│  🏢 TI                                                  │
│  📅 Quincena: 1-15 enero 2026                           │
│                                                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                         │
│  📊 RESUMEN                                             │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 🟢 A tiempo:     8 días                         │   │
│  │ 🟡 Retardos:     5 días  ⚠️ Revisar             │   │
│  │ 🔴 Faltas:       2 días  ⚠️ Revisar             │   │
│  │ 🔵 Inhábiles:    0 días                         │   │
│  │ ⚪ Descansos:    0 días                         │   │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │   │
│  │ 📅 Total:       15 días                         │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ⚡ ATAJOS RÁPIDOS                                      │
│  ┌─────────────────────────────────────────────────┐   │
│  │ [✅ Justificar todos los retardos]              │   │
│  │ [🏠 Todas las faltas → Remoto]                  │   │
│  │ [📞 Todas las faltas → Guardia]                 │   │
│  │ [🔄 Restablecer valores automáticos]            │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                         │
│  🟡 RETARDOS (5 días)                                   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 📅 2 ene • 09:11:23 • +11 min                   │   │
│  │ ⏱️ Llegó 11 minutos tarde                        │   │
│  │ ▼ Retardo no justificado                        │   │
│  │   [Cambiar] [Agregar excepción]                 │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 📅 5 ene • 09:12:45 • +12 min                   │   │
│  │ ⏱️ Llegó 12 minutos tarde                        │   │
│  │ ▼ Retardo justificado                           │   │
│  │   [Cambiar] [Agregar excepción]                 │   │
│  └─────────────────────────────────────────────────┘   │
│  ... (3 más)                                            │
│                                                         │
│  🔴 FALTAS (2 días)                                     │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 📅 7 ene • Sin checada                           │   │
│  │ ❌ Inasistencia                                  │   │
│  │ ▼ Falta justificada, trabajo remoto            │   │
│  │   [Cambiar] [Marcar como inhábil]               │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 📅 13 ene • Sin checada                          │   │
│  │ ❌ Inasistencia                                  │   │
│  │ ▼ Falta justificada, guardia telefónico        │   │
│  │   [Cambiar] [Marcar como inhábil]               │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  🟢 A TIEMPO (8 días) [Mostrar ▼]                       │
│                                                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                         │
│  [📄 Generar PDF]                                       │
└─────────────────────────────────────────────────────────┘
```

### 🎯 Tarjeta Expandida (Modal de Clasificación)

```
┌──────────────────────────────────────────────────────┐
│  📅 5 de enero de 2026                               │
│  ⏱️ Checada: 09:12:45 (+12 minutos tarde)            │
├──────────────────────────────────────────────────────┤
│                                                      │
│  🎯 Clasificación:                                   │
│                                                      │
│  ⚪ Retardo no justificado                           │
│  🔘 Retardo justificado                              │
│  ⚪ Falta no justificada                             │
│  ⚪ Falta justificada                                │
│  ⚪ Falta justificada, trabajo remoto                │
│  ⚪ Falta justificada, guardia telefónico            │
│  ⚪ Otro (especificar)                               │
│                                                      │
│  💬 Comentario (opcional):                           │
│  ┌────────────────────────────────────────────────┐ │
│  │ Junta con cliente                              │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  ⚙️ Excepciones:                                     │
│  [ ] Marcar como día inhábil                         │
│  [ ] Cambiar hora de entrada a: [10:00] [Guardar]   │
│                                                      │
│  [Cancelar]  [Guardar]                               │
└──────────────────────────────────────────────────────┘
```

### 📋 Opciones de Clasificación

| Opción | Código Interno | Cuándo Usar | Círculo PDF | Goce Sueldo |
|--------|----------------|-------------|-------------|-------------|
| **Retardo no justificado** | `RETARDO_NO_JUST` | Llegó tarde sin razón válida | ⚫ PARA LLEGAR TARDE | ⚫ NO |
| **Retardo justificado** | `RETARDO_JUST` | Llegó tarde con razón válida (junta, tráfico, etc.) | ⚫ PARA LLEGAR TARDE | ⚫ SÍ |
| **Falta no justificada** | `FALTA_NO_JUST` | No llegó sin razón válida | ⚫ PARA FALTAR | ⚫ NO |
| **Falta justificada** | `FALTA_JUST` | No llegó con razón válida (enfermedad, emergencia) | ⚫ PARA FALTAR | ⚫ SÍ |
| **Falta justificada, trabajo remoto** | `FALTA_REMOTO` | Trabajó desde casa (home office) | ⚫ PARA FALTAR | ⚫ SÍ |
| **Falta justificada, guardia telefónico** | `FALTA_GUARDIA` | Guardia telefónica (no requiere presencia) | ⚫ PARA FALTAR | ⚫ SÍ |
| **Otro** | `OTRO` | Caso especial (requiere comentario obligatorio) | ⚫ Según tipo base | Variable |

**📌 Nota importante:** En el formato Excel, **FALTA es FALTA** (se marca "PARA FALTAR"), independientemente de si es remoto, guardia o justificada. La diferencia está en el campo MOTIVO y en GOCE DE SUELDO.

### 🔒 Validaciones

| Regla | Comportamiento | Mensaje |
|-------|----------------|---------|
| **Día INHABIL** | Tarjeta bloqueada (no editable) | "🔵 Día inhábil - No aplica" |
| **Día DESCANSO** | Tarjeta bloqueada (no editable) | "⚪ Día de descanso - No aplica" |
| **Opción "Otro"** | Campo comentario obligatorio (min 10 chars) | "Especifica el motivo (mínimo 10 caracteres)" |
| **Sin clasificar** | Botón "Generar PDF" deshabilitado | "⚠️ Debes clasificar todos los retardos y faltas" |
| **Checada en inhábil** | Mostrar alerta amarilla | "⚠️ Trabajó en día inhábil - Verificar" |
| **Checada en descanso** | Mostrar alerta amarilla | "⚠️ Trabajó en día de descanso - Verificar" |

### ⚡ Atajos Rápidos (Acciones Masivas)

```python
# Pseudocódigo de atajos

def justificar_todos_retardos():
    for dia in dias_con_retardo:
        dia.clasificacion = "RETARDO_JUST"
        dia.comentario = "Justificado en bloque"
    
def todas_faltas_remoto():
    for dia in dias_con_falta:
        dia.clasificacion = "FALTA_REMOTO"
        dia.comentario = "Trabajo remoto"

def todas_faltas_guardia():
    for dia in dias_con_falta:
        dia.clasificacion = "FALTA_GUARDIA"
        dia.comentario = "Guardia telefónica"

def restablecer_valores():
    for dia in todos_los_dias:
        dia.clasificacion = dia.estado_automatico
        dia.comentario = ""
```

---

## 💾 PERSISTENCIA Y AUDITORÍA {#persistencia}

### 📦 Tabla: MovPerPeriodo

**Propósito:** Snapshot crudo de lo que el sistema detectó automáticamente

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `movper_id` | INT | PK autoincremental |
| `user_id` | INT | FK a User |
| `periodo_inicio` | DATE | Primer día de la quincena |
| `periodo_fin` | DATE | Último día de la quincena |
| `preset_id` | INT | FK a PresetUsuario usado |
| `preset_snapshot` | JSON | Copia del preset (por si cambia después) |
| `raw_daily_first_checkins` | JSON | `{"2026-01-01": "09:05:23", "2026-01-02": null, ...}` |
| `raw_daily_status_auto` | JSON | `{"2026-01-01": "A_TIEMPO", "2026-01-02": "FALTA", ...}` |
| `fuente_asistencia` | VARCHAR | "biostar_api" o "manual" |
| `created_by` | INT | Usuario que generó |
| `created_at` | TIMESTAMP | Fecha de creación |
| `pdf_generated_at` | TIMESTAMP | Cuándo se generó el PDF |
| `pdf_hash` | VARCHAR | SHA256 del PDF final |

**✅ Garantía:** Aunque cambie el algoritmo mañana, lo de hoy queda replicable.

### 📝 Tabla: MovPerIncidencia

**Propósito:** Decisión final del usuario (clasificación manual)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | INT | PK autoincremental |
| `movper_id` | INT | FK a MovPerPeriodo |
| `fecha` | DATE | Día específico |
| `estado_auto` | ENUM | Estado automático (A_TIEMPO, RETARDO, FALTA, INHABIL, DESCANSO) |
| `tipo_final` | ENUM | Clasificación final (RETARDO_JUST, FALTA_REMOTO, etc.) |
| `comentario` | TEXT | Comentario del usuario |
| `edited_by` | INT | Usuario que clasificó |
| `edited_at` | TIMESTAMP | Fecha de clasificación |

**Enums:**
```sql
CREATE TYPE estado_auto_enum AS ENUM (
    'A_TIEMPO',
    'RETARDO',
    'FALTA',
    'INHABIL',
    'DESCANSO'
);

CREATE TYPE tipo_final_enum AS ENUM (
    'RETARDO_NO_JUST',
    'RETARDO_JUST',
    'FALTA_NO_JUST',
    'FALTA_JUST',
    'FALTA_REMOTO',
    'FALTA_GUARDIA',
    'OTRO'
);
```

### 📜 Tabla: MovPerAuditLog

**Propósito:** Audit trail de cambios (nivel enterprise)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | INT | PK autoincremental |
| `movper_incidencia_id` | INT | FK a MovPerIncidencia |
| `campo_modificado` | VARCHAR | "tipo_final", "comentario", etc. |
| `valor_anterior` | TEXT | Valor antes del cambio |
| `valor_nuevo` | TEXT | Valor después del cambio |
| `modified_by` | INT | Usuario que hizo el cambio |
| `modified_at` | TIMESTAMP | Fecha del cambio |
| `razon` | TEXT | Razón del cambio (opcional) |

---

## 📄 GENERACIÓN DE PDF {#generacion-pdf}

### 🔧 Estrategia Robusta (3 Pasos)

```
┌─────────────────────────────────────────────────────────┐
│ PASO A: Rellenar Excel plantilla                       │
├─────────────────────────────────────────────────────────┤
│ 1. Clonar F-RH-18-MIT-FORMATO-DE-MOVIMIENTO...xlsx     │
│ 2. Abrir con openpyxl (sin modificar layout)           │
│ 3. Escribir en celdas específicas:                      │
│    • E8:M8   → Nombre completo                          │
│    • Q8:R8   → Departamento                             │
│    • H10:L10 → Fecha de autorización                    │
│    • P10:R10 → Fecha de aplicación                      │
│    • G20:R21 → MOTIVO (texto consolidado)               │
│ 4. Guardar como temp_{movper_id}.xlsx                   │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ PASO B: Convertir a PDF                                │
├─────────────────────────────────────────────────────────┤
│ 1. Usar LibreOffice headless:                           │
│    soffice --headless --convert-to pdf \                │
│            --outdir /tmp temp_{movper_id}.xlsx          │
│ 2. Resultado: temp_{movper_id}.pdf (sin círculos)      │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ PASO C: Pintar círculos (overlay)                      │
├─────────────────────────────────────────────────────────┤
│ 1. Crear overlay con ReportLab:                         │
│    • Lienzo transparente del tamaño del PDF             │
│    • Dibujar círculos rellenos en coordenadas exactas   │
│    • canvas.circle(x, y, radius, fill=1)                │
│ 2. Merge con pypdf:                                     │
│    • Cargar PDF base                                    │
│    • Cargar overlay                                     │
│    • page.merge_page(overlay_page)                      │
│ 3. Guardar como movper_{movper_id}_final.pdf           │
└─────────────────────────────────────────────────────────┘
```

### 📍 Mapeo de Celdas (Confirmado)

| Campo | Rango Excel | Ejemplo de Contenido |
|-------|-------------|----------------------|
| **Nombre** | E8:M8 | "Raul Abel Cetina Pool" |
| **Departamento** | Q8:R8 | "TI" |
| **Fecha de Autorización** | H10:L10 | "19-ene-26" |
| **Fecha de Aplicación** | P10:R10 | "1,2,5,6,7,8,9,12,13,14,15 de enero" |
| **MOTIVO** | G20:R21 | "2,5,6,7,8,9,12,15 retardo justificado. 1ro falta justificada, Guardia telefónico. 13 y 14 falta justificada, trabajo remoto." |

### 🎯 Tabla: PdfStampMap (Coordenadas de Círculos)

**Propósito:** Guardar coordenadas (x, y) de círculos para overlay

| Campo | Tipo | Ejemplo | Descripción |
|-------|------|---------|-------------|
| `id` | INT | 1 | PK |
| `template_version` | VARCHAR | "v1.0" | Versión del formato Excel |
| `field_name` | VARCHAR | "CHK_PARA_LLEGAR_TARDE" | Nombre del círculo |
| `page` | INT | 0 | Página del PDF (0-indexed) |
| `x` | FLOAT | 85.5 | Coordenada X (puntos PDF) |
| `y` | FLOAT | 650.2 | Coordenada Y (puntos PDF) |
| `radius` | FLOAT | 8.0 | Radio del círculo (puntos) |
| `color` | VARCHAR | "#000000" | Color (negro por defecto) |

**Círculos a mapear (según imagen):**

| field_name | Descripción | Cuándo se marca |
|------------|-------------|-----------------|
| `CHK_PARA_FALTAR` | ⚫ PARA FALTAR | Cualquier tipo de falta |
| `CHK_PARA_SALIR_REGRESAR` | ⚫ PARA SALIR Y REGRESAR | (No usado actualmente) |
| `CHK_PARA_LLEGAR_TARDE` | ⚫ PARA LLEGAR TARDE | Cualquier tipo de retardo |
| `CHK_PARA_RETIRARSE_TEMPRANO` | ⚫ PARA RETIRARSE TEMPRANO | (No usado actualmente) |
| `CHK_OLVIDO_CHECAR` | ⚫ OLVIDO CHECAR TARJETA | (No usado actualmente) |
| `CHK_GOCE_SUELDO_SI` | ⚫ GOCE DE SUELDO - SÍ | Justificado (remoto, guardia, etc.) |
| `CHK_GOCE_SUELDO_NO` | ⚫ GOCE DE SUELDO - NO | No justificado |
| `CHK_SOLICITUD_PERMISO` | ☑️ SOLICITUD DE PERMISO | Siempre (checkbox superior) |

**🔧 Calibración:**
- Se hace **1 vez** al inicio del proyecto
- Se usa librería como `pdfplumber` o `PyMuPDF` para medir coordenadas
- Script de calibración: abrir PDF, hacer clic en círculo, guardar (x, y)
- **Nunca más se toca** (a menos que cambie el formato Excel)

---

## 📝 FORMATO MOTIVO Y FECHAS {#formato-motivo}

### 📅 Campo: Fecha de Aplicación

**Ubicación:** P10:R10

**Formato:** Lista de días con incidencias + mes

**Regla:**
- ✅ Incluir: Días con RETARDO o FALTA (según clasificación final)
- ❌ Excluir: A_TIEMPO, DESCANSO, INHABIL

**Ejemplos:**

| Días con incidencias | Formato correcto |
|----------------------|------------------|
| [1] | "1ro de enero" |
| [13, 14] | "13 y 14 de enero" |
| [1, 2, 5, 6, 7, 8, 9, 12, 13, 14, 15] | "1,2,5,6,7,8,9,12,13,14,15 de enero" |
| [2, 5, 6, 7, 8, 9, 12, 15, 16, 20, 21, 22, 23, 27, 28] | "2,5,6,7,8,9,12,15,16,20,21,22,23,27,28 de enero" |

**Algoritmo:**

```python
def generar_fecha_aplicacion(dias_con_incidencias, mes, anio):
    """
    dias_con_incidencias: [1, 2, 5, 6, 7, 8, 9, 12, 13, 14, 15]
    mes: "enero"
    anio: 2026
    """
    if len(dias_con_incidencias) == 0:
        return ""
    
    if len(dias_con_incidencias) == 1:
        dia = dias_con_incidencias[0]
        return f"{dia} de {mes}"
    
    if len(dias_con_incidencias) == 2:
        return f"{dias_con_incidencias[0]} y {dias_con_incidencias[1]} de {mes}"
    
    # 3 o más días: formato compacto sin espacios
    dias_str = ",".join(str(d) for d in dias_con_incidencias)
    return f"{dias_str} de {mes}"
```

### 💬 Campo: MOTIVO

**Ubicación:** G20:R21

**Formato:** Texto consolidado agrupado por tipo de incidencia

**Plantillas confirmadas:**

| Tipo Final | Plantilla | Ejemplo |
|------------|-----------|---------|
| `RETARDO_JUST` | `{dias} retardo justificado.` | "2,5,6,7,8,9,12,15 retardo justificado." |
| `RETARDO_NO_JUST` | `{dias} retardo no justificado.` | "2,5 retardo no justificado." |
| `FALTA_JUST` | `{dias} falta justificada.` | "1ro falta justificada." |
| `FALTA_NO_JUST` | `{dias} falta no justificada.` | "3,4 falta no justificada." |
| `FALTA_REMOTO` | `{dias} falta justificada, trabajo remoto.` | "13 y 14 falta justificada, trabajo remoto." |
| `FALTA_GUARDIA` | `{dias} falta justificada, guardia telefónico.` | "1ro falta justificada, guardia telefónico." |
| `OTRO` | `{dias} {comentario}.` | "10 permiso especial por trámite personal." |

**Reglas de formato de días:**

| Cantidad | Formato | Ejemplo |
|----------|---------|---------|
| 1 día | `{dia}` | "1", "5", "13" |
| 2 días | `{dia1} y {dia2}` | "13 y 14" |
| 3+ días | `{dia1},{dia2},{dia3},...` | "2,5,6,7,8,9,12,15" (sin espacios) |

**Ejemplo real (de la imagen):**

```
2,5,6,7,8,9,12,15 retardo justificado. 1ro falta justificada, Guardia telefónico. 13 y 14 falta justificada, trabajo remoto.
```

**Algoritmo:**

```python
def generar_motivo(incidencias):
    """
    incidencias: [
        {"fecha": "2026-01-02", "tipo_final": "RETARDO_JUST", "comentario": ""},
        {"fecha": "2026-01-05", "tipo_final": "RETARDO_JUST", "comentario": ""},
        {"fecha": "2026-01-01", "tipo_final": "FALTA_GUARDIA", "comentario": ""},
        {"fecha": "2026-01-13", "tipo_final": "FALTA_REMOTO", "comentario": ""},
        {"fecha": "2026-01-14", "tipo_final": "FALTA_REMOTO", "comentario": ""},
    ]
    """
    # Agrupar por tipo_final
    grupos = {}
    for inc in incidencias:
        tipo = inc["tipo_final"]
        dia = int(inc["fecha"].split("-")[2])  # Extraer día
        if tipo not in grupos:
            grupos[tipo] = []
        grupos[tipo].append(dia)
    
    # Ordenar días dentro de cada grupo
    for tipo in grupos:
        grupos[tipo].sort()
    
    # Generar texto por grupo
    textos = []
    for tipo, dias in grupos.items():
        dias_str = formatear_dias(dias)
        plantilla = PLANTILLAS[tipo]
        texto = plantilla.replace("{dias}", dias_str)
        textos.append(texto)
    
    # Unir con espacio
    return " ".join(textos)

def formatear_dias(dias):
    """
    [1] → "1"
    [13, 14] → "13 y 14"
    [2,5,6,7,8,9,12,15] → "2,5,6,7,8,9,12,15"
    """
    if len(dias) == 1:
        return str(dias[0])
    if len(dias) == 2:
        return f"{dias[0]} y {dias[1]}"
    return ",".join(str(d) for d in dias)

PLANTILLAS = {
    "RETARDO_JUST": "{dias} retardo justificado.",
    "RETARDO_NO_JUST": "{dias} retardo no justificado.",
    "FALTA_JUST": "{dias} falta justificada.",
    "FALTA_NO_JUST": "{dias} falta no justificada.",
    "FALTA_REMOTO": "{dias} falta justificada, trabajo remoto.",
    "FALTA_GUARDIA": "{dias} falta justificada, guardia telefónico.",
}
```

---

## 🎯 MAPEO DE CÍRCULOS (Reglas Confirmadas) {#mapeo-circulos}

### ✅ Matriz de Decisión: ¿Qué círculos marcar?

| Tipo Final | PARA FALTAR | PARA LLEGAR TARDE | GOCE SUELDO SÍ | GOCE SUELDO NO | SOLICITUD PERMISO |
|------------|-------------|-------------------|----------------|----------------|-------------------|
| `RETARDO_NO_JUST` | ❌ | ✅ | ❌ | ✅ | ✅ |
| `RETARDO_JUST` | ❌ | ✅ | ✅ | ❌ | ✅ |
| `FALTA_NO_JUST` | ✅ | ❌ | ❌ | ✅ | ✅ |
| `FALTA_JUST` | ✅ | ❌ | ✅ | ❌ | ✅ |
| `FALTA_REMOTO` | ✅ | ❌ | ✅ | ❌ | ✅ |
| `FALTA_GUARDIA` | ✅ | ❌ | ✅ | ❌ | ✅ |
| `OTRO` | Variable | Variable | Variable | Variable | ✅ |

**📌 Reglas clave:**

1. **SOLICITUD DE PERMISO:** Siempre se marca (checkbox superior)
2. **PARA FALTAR:** Se marca para **cualquier tipo de falta** (justificada, remota, guardia, no justificada)
3. **PARA LLEGAR TARDE:** Se marca para **cualquier tipo de retardo** (justificado o no)
4. **GOCE DE SUELDO SÍ:** Se marca si es justificado (retardo/falta justificada, remoto, guardia)
5. **GOCE DE SUELDO NO:** Se marca si NO es justificado

### 🔄 Múltiples Incidencias en la Misma Quincena

**Pregunta:** Si un empleado tiene RETARDOS + FALTAS, ¿cómo se maneja?

**Respuesta confirmada:** **1 solo documento con múltiples círculos marcados**

**Ejemplo real (de la imagen):**

```
Incidencias en la quincena:
- 2,5,6,7,8,9,12,15 → RETARDO_JUST
- 1 → FALTA_GUARDIA
- 13,14 → FALTA_REMOTO

Círculos marcados:
✅ SOLICITUD DE PERMISO
✅ PARA FALTAR (porque hay faltas)
✅ PARA LLEGAR TARDE (porque hay retardos)
✅ GOCE DE SUELDO - SÍ (todo es justificado)
❌ GOCE DE SUELDO - NO

MOTIVO:
"2,5,6,7,8,9,12,15 retardo justificado. 1ro falta justificada, Guardia telefónico. 13 y 14 falta justificada, trabajo remoto."
```

**Algoritmo:**

```python
def determinar_circulos(incidencias):
    """
    incidencias: lista de MovPerIncidencia
    """
    tiene_retardo = any(inc.tipo_final.startswith("RETARDO") for inc in incidencias)
    tiene_falta = any(inc.tipo_final.startswith("FALTA") for inc in incidencias)
    
    # Determinar goce de sueldo
    # SÍ si TODAS las incidencias son justificadas
    # NO si ALGUNA incidencia NO es justificada
    todas_justificadas = all(
        inc.tipo_final in ["RETARDO_JUST", "FALTA_JUST", "FALTA_REMOTO", "FALTA_GUARDIA"]
        for inc in incidencias
    )
    
    return {
        "CHK_SOLICITUD_PERMISO": True,  # Siempre
        "CHK_PARA_FALTAR": tiene_falta,
        "CHK_PARA_LLEGAR_TARDE": tiene_retardo,
        "CHK_GOCE_SUELDO_SI": todas_justificadas,
        "CHK_GOCE_SUELDO_NO": not todas_justificadas,
        "CHK_PARA_SALIR_REGRESAR": False,  # No usado
        "CHK_PARA_RETIRARSE_TEMPRANO": False,  # No usado
        "CHK_OLVIDO_CHECAR": False,  # No usado
    }
```

---

## ⚠️ CASOS ESPECIALES {#casos-especiales}

### 🔵 Caso 1: Checada en Día Inhábil

**Situación:** Usuario checó en un día festivo oficial

**Comportamiento:**
- ✅ Se ignora para el cálculo de incidencias
- ⚠️ Se muestra alerta amarilla en checklist: "Trabajó en día inhábil"
- 🔧 Permite corrección manual: botón "Marcar como retardo/falta"

**Ejemplo:**
```
📅 1 ene (Año Nuevo) • 09:05:23
🔵 Día inhábil
⚠️ Trabajó en día inhábil - Verificar
[Ignorar] [Marcar como retardo] [Marcar como falta]
```

### ⚪ Caso 2: Checada en Día de Descanso

**Situación:** Usuario checó en sábado/domingo (o su día de descanso)

**Comportamiento:**
- ✅ Se ignora para el cálculo de incidencias
- ⚠️ Se muestra alerta amarilla en checklist: "Trabajó en día de descanso"
- 🔧 Permite corrección manual: botón "Marcar como retardo/falta"

**Ejemplo:**
```
📅 4 ene (Sábado) • 09:12:45
⚪ Día de descanso
⚠️ Trabajó en día de descanso - Verificar
[Ignorar] [Marcar como retardo] [Marcar como falta]
```

### 🔴 Caso 3: Sin Checadas en Toda la Quincena

**Situación:** Usuario no tiene ninguna checada en 15 días

**Comportamiento:**
- ✅ Se genera documento con 15 faltas
- ⚠️ Alerta en resumen: "Sin checadas en toda la quincena"
- 🔧 Permite corrección masiva: "Marcar todos como inhábiles"

**Nota:** El sistema genera el documento **solo cuando el usuario lo solicita** (no automáticamente para todos).

### 🟡 Caso 4: Retardo de 11 Minutos en Día Inhábil

**Situación:** Usuario checó tarde en un día festivo

**Comportamiento:**
- 🔵 Día se clasifica como INHABIL (prioridad sobre retardo)
- ⚠️ Alerta: "Trabajó en día inhábil con retardo de 11 min"
- 🔧 Permite marcar como retardo si es necesario

### 📝 Caso 5: Comentarios Agrupados en MOTIVO

**Situación:** Usuario agregó comentarios individuales a cada día

**Comportamiento:**
- ✅ Comentarios se agrupan por tipo de incidencia
- 📝 Si hay comentarios diferentes → se concatenan

**Ejemplo:**
```
Incidencias:
- 2 ene: RETARDO_JUST, comentario: "Junta con cliente"
- 5 ene: RETARDO_JUST, comentario: "Tráfico"
- 7 ene: FALTA_REMOTO, comentario: "Home office"

MOTIVO generado:
"2,5 retardo justificado (Junta con cliente, Tráfico). 7 falta justificada, trabajo remoto (Home office)."
```

---

## 🏗️ ARQUITECTURA TÉCNICA {#arquitectura}

### 🌐 Acceso al Sistema

**MobPer funciona como una aplicación independiente con su propio login.**

**Rutas de acceso:**
- **Login:** `http://localhost:5000/mobper/login`
- **Checklist:** `http://localhost:5000/mobper/checklist` (requiere login)
- **API:** `http://localhost:5000/mobper/api/*`

**Características:**
- ✅ No aparece en el sidebar del sistema principal
- ✅ Login independiente (redirige a `/mobper/checklist` después de autenticar)
- ✅ Diseño mobile-first con código de colores
- ✅ Export a Excel con formato prellenado
- ✅ Previsualizador en nueva pestaña

### 📅 LÓGICA DE QUINCENAS (CONFIRMADA)

**Reglas oficiales en México:**

```python
# Primera quincena: día 1 al 15
# Segunda quincena: día 16 al ÚLTIMO día del mes

Ejemplos:
- Enero 2026 (31 días):
  * Q1: 1-15 enero (15 días)
  * Q2: 16-31 enero (16 días)

- Febrero 2026 (28 días):
  * Q1: 1-15 febrero (15 días)
  * Q2: 16-28 febrero (13 días)

- Abril 2026 (30 días):
  * Q1: 1-15 abril (15 días)
  * Q2: 16-30 abril (15 días)
```

**⚠️ IMPORTANTE:** Si consultas el día 7, NO se calculan "los últimos 15 días" (23-7), sino la **quincena actual** (1-15).

**Algoritmo implementado:**

```python
def calcular_quincena_actual(fecha=None):
    if fecha is None:
        fecha = now_cdmx().date()
    
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
        ultimo_dia = monthrange(anio, mes)[1]  # 28, 29, 30 o 31
        inicio = date(anio, mes, 16)
        fin = date(anio, mes, ultimo_dia)
    
    return {
        'numero': numero,
        'inicio': inicio,
        'fin': fin,
        'nombre': f"{'Primera' if numero == 1 else 'Segunda'} quincena de {mes_nombre} {anio}",
        'dias_totales': (fin - inicio).days + 1
    }
```

### 📦 Módulos del Sistema

```
webapp/
├── mobper_routes.py           # Blueprint principal (independiente)
├── templates/
│   ├── mobper_login.html      # Login independiente (sin sidebar)
│   ├── mobper_checklist.html  # Checklist mobile-first
│   ├── mobper_preview.html    # Previsualizador del formato
│   └── F-RH-18-MIT-FORMATO-DE-MOVIMIENTO-DE-PERSONAL-3(1).xlsx
└── models.py                  # Modelos SQLAlchemy (compartidos)
```

**Estructura simplificada (todo en un solo archivo por ahora):**
- `mobper_routes.py` contiene:
  - Utilidades de quincenas
  - Motor de cálculo de incidencias
  - Rutas y APIs
  - Generación de Excel

### 🔌 Endpoints API (Implementados)

| Método | Ruta | Descripción | Estado |
|--------|------|-------------|--------|
| `GET` | `/mobper/login` | Página de login independiente | ✅ Implementado |
| `GET` | `/mobper/checklist` | Página de checklist interactivo | ✅ Implementado |
| `POST` | `/mobper/api/calcular-quincena` | Calcular incidencias para quincena | ✅ Implementado |
| `POST` | `/mobper/api/exportar-excel` | Exportar formato Excel prellenado | ✅ Implementado |
| `POST` | `/mobper/api/previsualizar` | Generar vista previa HTML | ✅ Implementado |
| `GET` | `/mobper/config` | Configuración de preset | ⏳ Pendiente |
| `POST` | `/mobper/api/preset` | Guardar/actualizar preset | ⏳ Pendiente |
| `POST` | `/mobper/api/clasificar` | Guardar clasificación de incidencias | ⏳ Pendiente |
| `POST` | `/mobper/api/generar-pdf` | Generar PDF con overlay | ⏳ Pendiente |

### 🔧 Dependencias Técnicas

```python
# requirements.txt
openpyxl==3.1.2          # Manipular Excel
reportlab==4.0.7         # Generar overlay PDF
pypdf==3.17.1            # Merge PDFs
python-dateutil==2.8.2   # Manejo de fechas
pytz==2023.3             # Zona horaria
sqlalchemy==2.0.23       # ORM
flask==3.0.0             # Framework web
pydantic==2.5.0          # Validación de datos
```

### 🚀 Flujo Completo (End-to-End)

```
1. Usuario abre /mobper/checklist
   └─> Sistema carga preset actual
   └─> Sistema llama attendance_service.get_first_checkins(user_id, periodo)
   └─> Sistema llama calculation_service.calcular_incidencias()
   └─> Renderiza checklist con estados automáticos

2. Usuario clasifica incidencias
   └─> Frontend envía POST /mobper/api/clasificar
   └─> Sistema guarda en MovPerIncidencia
   └─> Sistema actualiza audit log

3. Usuario hace clic en "Generar PDF"
   └─> Frontend envía POST /mobper/api/generar-pdf
   └─> pdf_service.generar_pdf(movper_id):
       a) Clonar plantilla Excel
       b) Rellenar celdas con openpyxl
       c) Convertir a PDF con LibreOffice
       d) stamp_service.pintar_circulos(pdf_path, circulos)
       e) Guardar PDF final
   └─> Retorna URL de descarga

4. Usuario descarga PDF
   └─> GET /mobper/api/download/{movper_id}
   └─> Sistema valida permisos
   └─> Envía archivo PDF
```

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

### Fase 1: Base de Datos y Modelos
- [ ] Crear tablas: `PresetUsuario`, `ExcepcionHorario`, `MovPerPeriodo`, `MovPerIncidencia`, `MovPerAuditLog`, `PdfStampMap`
- [ ] Crear enums: `estado_auto_enum`, `tipo_final_enum`
- [ ] Crear índices para optimizar consultas
- [ ] Seed inicial: días inhábiles 2026 México

### Fase 2: Servicios Backend
- [ ] `preset_service.py`: CRUD de presets
- [ ] `attendance_service.py`: Integración con BioStar API
- [ ] `calculation_service.py`: Motor de cálculo de incidencias
- [ ] `pdf_service.py`: Generación de PDF (Excel → PDF → Overlay)
- [ ] `stamp_service.py`: Overlay de círculos con ReportLab

### Fase 3: Frontend Mobile-First
- [ ] `mobper_config.html`: Configuración de preset
- [ ] `mobper_checklist.html`: Checklist interactivo
- [ ] `mobper_history.html`: Historial de movimientos
- [ ] `mobper.css`: Estilos con código de colores
- [ ] JavaScript: Atajos rápidos, validaciones, modales

### Fase 4: Calibración y Testing
- [ ] Script de calibración de coordenadas PDF
- [ ] Poblar tabla `PdfStampMap` con coordenadas exactas
- [ ] Testing unitario de `calculation_service`
- [ ] Testing de generación de PDF
- [ ] Testing mobile (responsive)

### Fase 5: Integración y Deploy
- [ ] Integrar con sistema de autenticación existente
- [ ] Agregar permisos y roles
- [ ] Documentación de usuario
- [ ] Deploy a producción
- [ ] Capacitación a usuarios

---

## 📞 CONTACTO Y SOPORTE

**Desarrollador:** Raul Abel Cetina Pool  
**Departamento:** TI  
**Versión:** 2.0  
**Última actualización:** 30 de enero de 2026

---

**FIN DEL DOCUMENTO**
