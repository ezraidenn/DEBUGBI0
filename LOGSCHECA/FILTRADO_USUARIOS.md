# 🚫 Filtrado de Usuarios por Grupo

## Descripción

Esta funcionalidad permite excluir automáticamente ciertos grupos de usuarios de todos los reportes, logs y estadísticas del sistema. Los usuarios de grupos excluidos no aparecerán en:

- ✅ Dashboard principal
- ✅ Logs de checadores individuales
- ✅ Modal de "Usuarios del Día"
- ✅ Búsquedas de usuarios
- ✅ Estadísticas de accesos
- ✅ Exportaciones a Excel
- ✅ Cualquier otro reporte del sistema

## Configuración

### 1. Editar archivo `.env.production`

Abre el archivo `.env.production` y busca la sección:

```bash
# ============================================
# Filtrado de Usuarios
# ============================================
# Grupos de usuarios a excluir (separados por coma)
EXCLUDED_USER_GROUPS=Socias Mayores 16,Socias Mayores 14,Socios Mayores 16
```

### 2. Agregar o quitar grupos

Simplemente agrega o quita los nombres de los grupos separados por comas:

```bash
# Ejemplo: Excluir 3 grupos
EXCLUDED_USER_GROUPS=Socias Mayores 16,Socios Menores 14,Anthea

# Ejemplo: Excluir 1 solo grupo
EXCLUDED_USER_GROUPS=Anthea

# Ejemplo: No excluir ningún grupo (dejar vacío)
EXCLUDED_USER_GROUPS=
```

### 3. Reiniciar el servidor

Después de modificar el archivo `.env.production`, reinicia el servidor:

```powershell
# Detener servidor
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*LOGSCHECA*" } | Stop-Process -Force

# Iniciar servidor
.\venv\Scripts\python.exe run_production.py
```

## Cómo funciona

El sistema busca coincidencias en:

1. **Nombre del usuario** - Si el nombre del usuario contiene alguno de los grupos excluidos
2. **Grupo del usuario** - Si el usuario pertenece a un grupo excluido (campo `user_group_id`)

La búsqueda es **case-insensitive** (no distingue mayúsculas/minúsculas) y busca **coincidencias parciales**.

### Ejemplos:

Si configuras:
```bash
EXCLUDED_USER_GROUPS=Socias Mayores,Anthea
```

Se excluirán usuarios con nombres como:
- "Socias Mayores 16"
- "Socias Mayores 14"
- "Anthea"
- "ANTHEA GARCIA"
- "socias mayores cualquier cosa"

## Verificar que funciona

1. **Antes de configurar**: Abre el dashboard y cuenta cuántos usuarios únicos aparecen
2. **Configura los grupos excluidos** en `.env.production`
3. **Reinicia el servidor**
4. **Verifica el dashboard**: Deberías ver menos usuarios únicos
5. **Abre el modal "Usuarios del Día"**: Los usuarios de grupos excluidos no deberían aparecer

## Logs de debug

Para verificar qué usuarios están siendo filtrados, revisa los logs del servidor. Verás mensajes como:

```
[INFO] Obteniendo eventos del dispositivo 12345...
[INFO] ✓ 150 eventos encontrados
[INFO] 🚫 Filtrados 45 eventos de usuarios excluidos
[INFO] ✓ 105 eventos después del filtrado
```

## Notas importantes

- ⚠️ **Los eventos siguen existiendo en BioStar**, solo se ocultan en esta aplicación
- ⚠️ **El filtrado es permanente** mientras la configuración esté activa
- ⚠️ **Reinicia el servidor** después de cada cambio en `.env.production`
- ✅ **No afecta la base de datos** de BioStar, solo filtra la visualización

## Desactivar el filtrado

Para desactivar completamente el filtrado y ver todos los usuarios:

```bash
# Dejar vacío
EXCLUDED_USER_GROUPS=
```

O comentar la línea:

```bash
# EXCLUDED_USER_GROUPS=Socias Mayores 16,Anthea
```

Luego reinicia el servidor.

## Grupos actualmente excluidos

Según tu configuración actual en `.env.production`:

```
✅ Socias Mayores 16
✅ Socias Mayores 14
✅ Socios Mayores 16
✅ Socios Menores 16
✅ Socias Menores 14
✅ Anthea
```

Estos usuarios **NO** aparecerán en ninguna parte del sistema.
