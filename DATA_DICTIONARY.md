# Diccionario de Datos

## Base de Datos: SQLite/PostgreSQL

### Tablas Principales

#### 1. users
Usuarios del sistema principal (no MobPer)

| Campo | Tipo | Restricciones | Descripción |
|-------|------|--------------|-------------|
| id | Integer | PK, Autoincrement | Identificador único |
| username | String(80) | Unique, Not Null | Nombre de usuario |
| email | String(120) | Unique, Not Null | Correo electrónico |
| password_hash | String(255) | Not Null | Hash de contraseña |
| is_active | Boolean | Default True | Usuario activo |
| created_at | DateTime | Default utcnow | Fecha de creación |
| last_login | DateTime | Nullable | Último login |
| role | String(20) | Default 'user' | Rol (user/admin) |

#### 2. companies
Información de empresas para logos en formatos

| Campo | Tipo | Restricciones | Descripción |
|-------|------|--------------|-------------|
| id | Integer | PK, Autoincrement | Identificador único |
| name | String(100) | Not Null | Nombre de empresa |
| logo_path | String(255) | Nullable | Ruta a archivo de logo |
| created_at | DateTime | Default utcnow | Fecha de creación |

#### 3. zones
Zonas físicas del edificio

| Campo | Tipo | Restricciones | Descripción |
|-------|------|--------------|-------------|
| id | Integer | PK, Autoincrement | Identificador único |
| name | String(100) | Unique, Not Null | Nombre de zona |
| description | String(200) | Nullable | Descripción |
| color | String(7) | Default '#6c757d' | Color hexadecimal |
| icon | String(50) | Default 'bi-building' | Icono Bootstrap |
| is_active | Boolean | Default True | Zona activa |
| created_at | DateTime | Default utcnow | Fecha de creación |

#### 4. groups
Grupos/departamentos dentro de zonas

| Campo | Tipo | Restricciones | Descripción |
|-------|------|--------------|-------------|
| id | Integer | PK, Autoincrement | Identificador único |
| name | String(100) | Not Null | Nombre de grupo |
| description | String(200) | Nullable | Descripción |
| zone_id | Integer | FK zones.id, Not Null | Zona padre |
| color | String(7) | Default '#007bff' | Color hexadecimal |
| is_active | Boolean | Default True | Grupo activo |
| created_at | DateTime | Default utcnow | Fecha de creación |

#### 5. group_members
Usuarios asignados a grupos

| Campo | Tipo | Restricciones | Descripción |
|-------|------|--------------|-------------|
| id | Integer | PK, Autoincrement | Identificador único |
| group_id | Integer | FK groups.id, Not Null | Grupo |
| biostar_user_id | String(50) | Not Null | ID en BioStar |
| user_name | String(200) | Nullable | Nombre de usuario |
| added_at | DateTime | Default utcnow | Fecha de asignación |

#### 6. zone_devices
Dispositivos asignados a zonas

| Campo | Tipo | Restricciones | Descripción |
|-------|------|--------------|-------------|
| id | Integer | PK, Autoincrement | Identificador único |
| zone_id | Integer | FK zones.id, Not Null | Zona |
| device_id | Integer | Not Null | ID de dispositivo BioStar |
| device_name | String(200) | Nullable | Nombre descriptivo |
| is_active | Boolean | Default True | Dispositivo activo |
| added_at | DateTime | Default utcnow | Fecha de asignación |

#### 7. emergency_sessions
Sesiones de emergencia activas

| Campo | Tipo | Restricciones | Descripción |
|-------|------|--------------|-------------|
| id | Integer | PK, Autoincrement | Identificador único |
| zone_id | Integer | FK zones.id, Not Null | Zona afectada |
| emergency_type | String(50) | Default 'general' | Tipo de emergencia |
| started_by | Integer | FK users.id, Not Null | Usuario que inició |
| started_at | DateTime | Default utcnow | Inicio de emergencia |
| resolved_at | DateTime | Nullable | Resolución |
| status | String(20) | Default 'active' | Estado (active/resolved) |
| notes | Text | Nullable | Notas adicionales |
| unlocked_doors | Text | Nullable | Puertas desbloqueadas |

#### 8. roll_call_entries
Registros de pase de lista

| Campo | Tipo | Restricciones | Descripción |
|-------|------|--------------|-------------|
| id | Integer | PK, Autoincrement | Identificador único |
| emergency_id | Integer | FK emergency_sessions.id, Not Null | Sesión |
| group_id | Integer | FK groups.id, Nullable | Grupo (opcional) |
| biostar_user_id | String(50) | Not Null | ID BioStar |
| user_name | String(200) | Nullable | Nombre |
| status | String(20) | Default 'pending' | Estado (present/absent/pending) |
| marked_by | Integer | FK users.id, Nullable | Quién marcó |
| marked_at | DateTime | Nullable | Cuándo marcó |
| notes | Text | Nullable | Notas |
| manual_group_name | String(200) | Nullable | Grupo temporal |

### Tablas MobPer (Sistema Independiente)

#### 9. mobper_users
Usuarios del sistema MovPer

| Campo | Tipo | Restricciones | Descripción |
|-------|------|--------------|-------------|
| id | Integer | PK, Autoincrement | Identificador único |
| numero_socio | String(20) | Unique, Not Null | Número de socio |
| nombre_completo | String(200) | Not Null | Nombre completo |
| password_hash | String(255) | Not Null | Hash de contraseña |
| is_active | Boolean | Default True | Usuario activo |
| is_admin | Boolean | Default False | Es administrador |
| created_at | DateTime | Default utcnow | Fecha de creación |
| last_login | DateTime | Nullable | Último login |

#### 10. mobper_presets
Configuración personal de horarios

| Campo | Tipo | Restricciones | Descripción |
|-------|------|--------------|-------------|
| id | Integer | PK, Autoincrement | Identificador único |
| user_id | Integer | FK mobper_users.id, Not Null | Usuario |
| nombre_formato | String(200) | Nullable | Nombre para formato |
| departamento_formato | String(100) | Nullable | Departamento |
| jefe_directo_nombre | String(200) | Nullable | Nombre del jefe |
| company_id | Integer | FK companies.id, Nullable | Empresa |
| hora_entrada_default | Time | Default 09:00:00 | Hora entrada |
| tolerancia_segundos | Integer | Default 600 | Tolerancia (segundos) |
| hora_salida_default | Time | Default 18:00:00 | Hora salida |
| tolerancia_salida_segundos | Integer | Default 600 | Tolerancia salida |
| dias_descanso | JSON | Default [5,6] | Días descanso (0=Lunes) |
| lista_inhabiles | JSON | Default [] | Días inhábiles |
| vigente_desde | Date | Default today | Vigencia desde |
| vigente_hasta | Date | Nullable | Vigencia hasta |

#### 11. mobper_incidencias_dia
Registro diario de incidencias

| Campo | Tipo | Restricciones | Descripción |
|-------|------|--------------|-------------|
| id | Integer | PK, Autoincrement | Identificador único |
| user_id | Integer | FK mobper_users.id, Not Null | Usuario |
| fecha | Date | Not Null | Fecha del registro |
| estado_auto | String(20) | Not Null | Estado automático |
| minutos_diferencia | Integer | Nullable | Minutos de diferencia |
| primer_registro | Time | Nullable | Primer checada |
| ultimo_registro | Time | Nullable | Último checada |
| hora_limite | Time | Nullable | Hora límite |
| clasificacion | String(50) | Nullable | Clasificación manual |
| motivo_auto | String(200) | Nullable | Motivo automático |
| con_goce_sueldo | Boolean | Default True | Con goce de sueldo |
| justificado | Boolean | Default True | Justificado (retardos) |
| salida_justificado | Boolean | Default True | Justificado (salidas) |
| hora_salida | Time | Nullable | Hora de salida |
| minutos_diferencia_salida | Integer | Nullable | Minutos diferencia salida |
| salida_estado | String(20) | Nullable | Estado salida |
| entrada_no_checada | Boolean | Default False | Entrada no checada |
| salida_no_checada | Boolean | Default False | Salida no checada |
| olvido_checar_justificado | Boolean | Default True | Olvido justificado |
| created_at | DateTime | Default utcnow | Fecha creación |
| updated_at | DateTime | Default utcnow | Fecha actualización |

#### 12. mobper_periodos
Snapshot de quincenas procesadas

| Campo | Tipo | Restricciones | Descripción |
|-------|------|--------------|-------------|
| id | Integer | PK, Autoincrement | Identificador único |
| user_id | Integer | FK mobper_users.id, Not Null | Usuario |
| periodo_inicio | Date | Not Null | Inicio del período |
| periodo_fin | Date | Not Null | Fin del período |
| preset_snapshot | JSON | Nullable | Copia del preset |
| raw_daily_first_checkins | JSON | Nullable | Primeros checadas |
| raw_daily_status_auto | JSON | Nullable | Estados automáticos |
| created_at | DateTime | Default utcnow | Fecha creación |
| pdf_generated_at | DateTime | Nullable | Generación PDF |
| pdf_hash | String(64) | Nullable | Hash del PDF |

#### 13. correcciones_dia
Correcciones manuales de incidencias

| Campo | Tipo | Restricciones | Descripción |
|-------|------|--------------|-------------|
| id | Integer | PK, Autoincrement | Identificador único |
| user_id | Integer | FK users.id, Not Null | Usuario |
| fecha | Date | Not Null | Fecha |
| tipo_correccion | String(50) | Not Null | Tipo de corrección |
| valor_original | String(100) | Nullable | Valor original |
| valor_corregido | String(100) | Nullable | Valor corregido |
| autor_id | Integer | FK users.id, Not Null | Autor |
| justificacion | Text | Nullable | Justificación |
| created_at | DateTime | Default utcnow | Fecha creación |

#### 14. auditor
Registro de auditoría

| Campo | Tipo | Restricciones | Descripción |
|-------|------|--------------|-------------|
| id | Integer | PK, Autoincrement | Identificador único |
| user_id | Integer | FK users.id, Not Null | Usuario |
| accion | String(100) | Not Null | Acción realizada |
| tabla_afectada | String(50) | Nullable | Tabla afectada |
| registro_id | Integer | Nullable | ID del registro |
| datos_anteriores | JSON | Nullable | Datos anteriores |
| datos_nuevos | JSON | Nullable | Datos nuevos |
| ip_address | String(45) | Nullable | Dirección IP |
| user_agent | String(500) | Nullable | User agent |
| created_at | DateTime | Default utcnow | Fecha creación |

## Estados y Códigos

### Estados Automáticos de Incidencia
| Código | Descripción |
|--------|-------------|
| A_TIEMPO | Llegada puntual |
| RETARDO | Llegada tarde |
| FALTA | No checó |
| DESCANSO | Día de descanso |
| INHABIL | Día inhábil |
| SALIDA_TEMPRANA | Salida antes de hora |

### Estados de Salida
| Código | Descripción |
|--------|-------------|
| NORMAL | Salida normal |
| SALIDA_TEMPRANA | Salida temprana |

### Clasificaciones de Faltas
| Código | Descripción |
|--------|-------------|
| REMOTO | Trabajo remoto |
| GUARDIA | Guardia telefónica |
| PERMISO | Permiso personal |
| VACACIONES | Vacaciones |
| INCAPACIDAD | Incapacidad médica |
| ERROR_SISTEMA | No es falta (error del sistema) |

### Estados de Emergencia
| Código | Descripción |
|--------|-------------|
| active | Emergencia activa |
| resolved | Emergencia resuelta |

### Estados de Roll Call
| Código | Descripción |
|--------|-------------|
| pending | Pendiente de verificación |
| present | Presente |
| absent | Ausente |

## Relaciones Importantes

### Relaciones One-to-Many
- `users` → `correcciones_dia` (autor)
- `companies` → `mobper_presets`
- `zones` → `groups`
- `zones` → `emergency_sessions`
- `groups` → `group_members`
- `groups` → `roll_call_entries`
- `emergency_sessions` → `roll_call_entries`

### Relaciones Many-to-One
- `group_members` → `groups`
- `zone_devices` → `zones`
- `mobper_presets` → `mobper_users`
- `mobper_incidencias_dia` → `mobper_users`

### Relaciones Self-Referential
- `users` (potencial jerarquía jefe-subordinado)

## Índices Recomendados

### Índices de Rendimiento
```sql
-- MobPer incidencias por usuario y fecha
CREATE INDEX idx_incidencias_user_fecha ON mobper_incidencias_dia(user_id, fecha);

-- BioStar events por usuario y fecha
CREATE INDEX idx_events_user_fecha ON events(user_id, event_time);

-- Auditoría por usuario y fecha
CREATE INDEX idx_auditor_user_fecha ON auditor(user_id, created_at);

-- Emergency sessions activas
CREATE INDEX idx_emergency_active ON emergency_sessions(status, started_at);
```

### Índices Únicos
```sql
-- Número de socio único
CREATE UNIQUE INDEX idx_mobper_users_numero ON mobper_users(numero_socio);

-- Miembro único por grupo
CREATE UNIQUE INDEX idx_group_member_unique ON group_members(group_id, biostar_user_id);

-- Dispositivo único por zona
CREATE UNIQUE INDEX idx_zone_device_unique ON zone_devices(zone_id, device_id);
```

## Validaciones de Datos

### Validaciones a Nivel de Aplicación
- **Horas**: Formato HH:MM, rango 00:00-23:59
- **Fechas**: ISO 8601, no futuras para incidencias
- **Números**: Solo dígitos para número de socio
- **Correos**: Formato email válido
- **Estados**: Solo valores permitidos en enums

### Validaciones de Integridad
- **Fechas**: `periodo_inicio` ≤ `periodo_fin`
- **Vigencia**: `vigente_desde` ≤ `vigente_hasta`
- **Tolerancias**: Valores positivos
- **JSON**: Estructura válida en campos JSON

## Políticas de Retención

### Datos de MovPer
- **Incidencias**: 2 años (cumplimiento fiscal)
- **Períodos**: 5 años (historial)
- **Correcciones**: 3 años (auditoría)

### Datos de Emergencia
- **Sesiones**: 30 días (operación)
- **Roll Calls**: 90 días (reportes)

### Datos de Auditoría
- **Logs**: 1 año (seguridad)
- **Access**: 6 meses (monitoreo)

## Migraciones y Versiones

### Schema Versioning
- Cada migración tiene timestamp único
- Rollback automático cuando es posible
- Backup previo a migraciones destructivas

### Migraciones Importantes
- `migrate_salida_fields.py`: Campos de salida
- `migrate_olvido_justificado.py`: Justificación de olvido
- `migrate_correcciones_dia.py`: Sistema de correcciones
- `migrate_emergency_tables.py`: Sistema de emergencia

## Consideraciones de Performance

### Query Optimization
- Usar ` eager loading` para relaciones frecuentes
- Limitar resultados con `LIMIT` en paginación
- Evitar N+1 queries con `joinedload()`

### Caching Strategy
- Cache de presets por usuario
- Cache de quincenas calculadas
- Cache de dispositivos activos

### Bulk Operations
- Insert en batch para incidencias
- Bulk updates para estados
- Transacciones para operaciones complejas
