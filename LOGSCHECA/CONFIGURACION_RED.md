# Configuración de Red - LOGSCHECA

## Configuración Actual

### Servidor Web
- **Host**: `0.0.0.0` (Acepta conexiones desde cualquier interfaz de red)
- **Puerto**: `5000`
- **CORS**: Habilitado para todos los orígenes (`*`)
- **WebSockets**: Habilitado con SocketIO

### Acceso desde Red Local

El servidor está configurado para aceptar conexiones desde:
- **IP Local**: `http://localhost:5000`
- **IP de Red**: `http://10.0.0.10:5000`
- **Cualquier IP en la red local**: `http://<IP_DEL_SERVIDOR>:5000`

### Credenciales por Defecto
- **Usuario**: `admin`
- **Contraseña**: `admin123`

⚠️ **IMPORTANTE**: Cambia la contraseña por defecto en producción.

## Configuración de Firewall (Windows)

Para permitir conexiones entrantes en el puerto 5000, ejecuta estos comandos en PowerShell como Administrador:

```powershell
# Permitir conexiones entrantes en el puerto 5000
New-NetFirewallRule -DisplayName "BioStar Monitor - Puerto 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow

# Verificar que la regla se creó correctamente
Get-NetFirewallRule -DisplayName "BioStar Monitor - Puerto 5000"
```

## Verificar Conectividad

### Desde el servidor local:
```powershell
# Verificar que el puerto está escuchando
netstat -ano | findstr :5000
```

### Desde otra máquina en la red (10.0.0.10):
```powershell
# Probar conectividad al puerto
Test-NetConnection -ComputerName <IP_DEL_SERVIDOR> -Port 5000
```

O desde un navegador:
```
http://10.0.0.10:5000
```

## Configuración BioStar 2 API

El archivo `.env` contiene la configuración para conectarse a BioStar 2:

```env
BIOSTAR_HOST=https://10.0.0.100
BIOSTAR_USER=rcetina
BIOSTAR_PASSWORD=aP1su.ser
```

## Solución de Problemas

### El servidor no es accesible desde la red
1. Verifica que el firewall de Windows permita conexiones en el puerto 5000
2. Verifica que el servidor esté escuchando en `0.0.0.0` y no solo en `localhost`
3. Verifica la configuración de red de la máquina servidor

### Error de conexión a BioStar
1. Verifica que la IP `10.0.0.100` sea accesible desde el servidor
2. Verifica las credenciales en el archivo `.env`
3. Revisa los logs del servidor para más detalles

## Iniciar el Servidor

```powershell
# Activar entorno virtual (si existe)
.\venv\Scripts\Activate.ps1

# Iniciar el servidor
python run_webapp.py
```

El servidor mostrará:
```
================================================================================
🌐 BIOSTAR DEBUG MONITOR - WEB APPLICATION (TIEMPO REAL)
================================================================================

✓ Iniciando servidor web con WebSockets...
✓ URL Local: http://localhost:5000
✓ URL Red: http://10.0.0.10:5000
✓ Usuario por defecto: admin
✓ Contraseña por defecto: admin123
✓ Tiempo Real: ACTIVADO ⚡
✓ Permitiendo conexiones desde: 10.0.0.10

⚠️  Presiona Ctrl+C para detener el servidor

================================================================================
```
