# 🚀 Auto-Deploy para Windows Server

## ⚡ Instalación Rápida (1 Click)

### Opción 1: Doble Click (Más Fácil)

**Simplemente haz doble click en:**

```
INSTALAR_Y_EJECUTAR.bat
```

¡Eso es todo! El script hará TODO automáticamente.

---

### Opción 2: PowerShell

```powershell
.\INSTALAR_AUTO_DEPLOY_WINDOWS.ps1
```

---

## 📋 ¿Qué hace el instalador?

1. ✅ Verifica Python
2. ✅ Crea entorno virtual
3. ✅ Instala dependencias
4. ✅ Verifica archivo .env
5. ✅ Configura firewall (puerto 5000)
6. ✅ Instala servicio de auto-deploy
7. ✅ Crea tarea programada de Windows

---

## 🎯 Cómo Funciona

### Sistema de Auto-Deploy

El sistema monitorea GitHub cada 60 segundos:

```
Verificar GitHub cada 60 segundos
         ↓
¿Hay nuevo commit?
         ↓ SI
Descargar cambios (git pull)
         ↓
Reiniciar aplicación
         ↓
✅ Deploy completado
```

### Flujo de Trabajo

1. **Haces cambios en el código**
2. **Commit y push a GitHub:**
   ```bash
   git add .
   git commit -m "feat: nueva funcionalidad"
   git push origin main
   ```
3. **Esperas 1-2 minutos**
4. **El servidor detecta el cambio automáticamente**
5. **Descarga y reinicia la aplicación**
6. **✅ Cambios aplicados**

---

## 🎮 Comandos

### Iniciar Auto-Deploy

```powershell
.\auto_deploy_windows.ps1 -Start
```

### Detener Auto-Deploy

```powershell
.\auto_deploy_windows.ps1 -Stop
```

### Ver Estado

```powershell
.\auto_deploy_windows.ps1 -Status
```

### Cambiar Intervalo de Verificación

```powershell
# Verificar cada 30 segundos
.\auto_deploy_windows.ps1 -Start -CheckInterval 30

# Verificar cada 5 minutos (300 segundos)
.\auto_deploy_windows.ps1 -Start -CheckInterval 300
```

---

## 📊 Monitoreo

### Ver Logs en Tiempo Real

```powershell
Get-Content logs\auto_deploy.log -Wait -Tail 20
```

### Ver Estado de la Aplicación

```powershell
.\auto_deploy_windows.ps1 -Status
```

### Ver Procesos Python

```powershell
Get-Process python
```

---

## 🔧 Configuración

### Archivo: `auto_deploy_windows.ps1`

Variables principales:

```powershell
$REPO_PATH = "C:\Users\Administrador\Documents\DebugBi0\DEBUGBI0"
$REPO_URL = "https://github.com/ezraidenn/DEBUGBI0.git"
$APP_SCRIPT = "iniciar_produccion.ps1"
$CheckInterval = 60  # Segundos
```

### Tarea Programada de Windows

El instalador crea una tarea programada llamada:
```
BioStarMonitor-AutoDeploy
```

**Ver tarea:**
```powershell
Get-ScheduledTask -TaskName "BioStarMonitor-AutoDeploy"
```

**Iniciar tarea manualmente:**
```powershell
Start-ScheduledTask -TaskName "BioStarMonitor-AutoDeploy"
```

**Deshabilitar tarea:**
```powershell
Disable-ScheduledTask -TaskName "BioStarMonitor-AutoDeploy"
```

---

## 🌐 Acceso a la Aplicación

Una vez instalado y ejecutando:

- **Local:** http://localhost:5000
- **Red:** http://10.0.2.64:5000

**Credenciales por defecto:**
- Usuario: `admin`
- Password: `admin123`

---

## 🔥 Firewall

El instalador crea automáticamente una regla de firewall:

**Nombre:** `BioStar Monitor - Puerto 5000`
**Puerto:** 5000 (TCP)
**Dirección:** Entrada (Inbound)

### Verificar Regla

```powershell
Get-NetFirewallRule -DisplayName "BioStar Monitor - Puerto 5000"
```

### Crear Regla Manualmente (si falla)

```powershell
New-NetFirewallRule -DisplayName "BioStar Monitor - Puerto 5000" `
    -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow
```

---

## 📁 Estructura de Archivos

```
DEBUGBI0/
├── auto_deploy_windows.ps1          # Script principal de auto-deploy
├── INSTALAR_AUTO_DEPLOY_WINDOWS.ps1 # Instalador
├── INSTALAR_Y_EJECUTAR.bat          # Instalador (doble click)
├── iniciar_produccion.ps1           # Script de inicio de la app
├── logs/
│   └── auto_deploy.log              # Logs de auto-deploy
├── .last_commit                     # Último commit procesado
└── auto_deploy.pid                  # PID del proceso de monitoreo
```

---

## 🆘 Solución de Problemas

### El auto-deploy no detecta cambios

**Verificar:**
```powershell
# 1. Ver estado
.\auto_deploy_windows.ps1 -Status

# 2. Ver logs
Get-Content logs\auto_deploy.log -Tail 50

# 3. Verificar conectividad con GitHub
git fetch origin main
```

### La aplicación no inicia después del deploy

**Verificar:**
```powershell
# 1. Ver procesos Python
Get-Process python

# 2. Iniciar manualmente
.\iniciar_produccion.ps1

# 3. Ver logs de la aplicación
Get-Content logs\app.log -Tail 50
```

### Error de permisos

**Ejecutar PowerShell como Administrador:**
```powershell
Start-Process powershell -Verb RunAs
```

### Puerto 5000 ya en uso

**Ver qué está usando el puerto:**
```powershell
Get-NetTCPConnection -LocalPort 5000
```

**Cambiar puerto en `.env`:**
```env
PORT=5001
```

---

## 🔄 Actualización Manual

Si necesitas actualizar manualmente (sin auto-deploy):

```powershell
# 1. Detener auto-deploy
.\auto_deploy_windows.ps1 -Stop

# 2. Detener aplicación
Get-Process python | Where-Object {$_.Path -like "*DEBUGBI0*"} | Stop-Process

# 3. Actualizar código
git pull origin main

# 4. Instalar dependencias (si cambiaron)
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 5. Iniciar aplicación
.\iniciar_produccion.ps1

# 6. Iniciar auto-deploy
.\auto_deploy_windows.ps1 -Start
```

---

## 📊 Logs

### Ubicación de Logs

- **Auto-Deploy:** `logs\auto_deploy.log`
- **Aplicación:** `logs\app.log`
- **Seguridad:** `logs\security_audit.log`

### Ver Logs en Tiempo Real

```powershell
# Auto-deploy
Get-Content logs\auto_deploy.log -Wait -Tail 20

# Aplicación
Get-Content logs\app.log -Wait -Tail 20
```

---

## ⚙️ Configuración Avanzada

### Cambiar Intervalo de Verificación

Edita `auto_deploy_windows.ps1`:

```powershell
$CheckInterval = 30  # Verificar cada 30 segundos
```

### Cambiar Script de Inicio

Edita `auto_deploy_windows.ps1`:

```powershell
$APP_SCRIPT = "tu_script.ps1"
```

### Deshabilitar Auto-Inicio

```powershell
Disable-ScheduledTask -TaskName "BioStarMonitor-AutoDeploy"
```

---

## 🎉 Resultado Final

Una vez instalado:

✅ **Auto-deploy activo** - Detecta cambios en GitHub cada 60 segundos
✅ **Aplicación corriendo** - Accesible en http://10.0.2.64:5000
✅ **Auto-inicio** - Se inicia automáticamente al arrancar Windows
✅ **Logs completos** - Monitoreo de todos los eventos
✅ **Firewall configurado** - Puerto 5000 abierto

### Flujo de Trabajo Diario

```bash
# En tu máquina de desarrollo
git add .
git commit -m "feat: nueva funcionalidad"
git push origin main

# Esperar 1-2 minutos
# ✅ El servidor detecta y aplica cambios automáticamente
```

---

## 📞 Comandos Rápidos

```powershell
# Ver todo el estado
.\auto_deploy_windows.ps1 -Status

# Reiniciar todo
.\auto_deploy_windows.ps1 -Stop
.\auto_deploy_windows.ps1 -Start

# Ver logs
Get-Content logs\auto_deploy.log -Tail 50

# Verificar aplicación
Start-Process "http://localhost:5000"
```

---

**Tiempo de instalación:** ~2 minutos  
**Dificultad:** ⭐ Muy Fácil  
**Resultado:** Auto-deploy 100% funcional en Windows
