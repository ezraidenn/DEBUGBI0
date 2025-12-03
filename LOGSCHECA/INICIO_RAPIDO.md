# 🚀 Inicio Rápido - LOGSCHECA

## Instalación Automática

### 1. Instalar el sistema

Abre PowerShell en esta carpeta y ejecuta:

```powershell
.\instalar.ps1
```

Este script:
- ✅ Verifica Python
- ✅ Crea entorno virtual
- ✅ Instala todas las dependencias
- ✅ Crea archivo .env
- ✅ Crea directorios necesarios

### 2. Configurar Firewall (Opcional pero recomendado)

Abre PowerShell **como Administrador** y ejecuta:

```powershell
.\configurar_firewall.ps1
```

Este script:
- ✅ Crea regla de firewall para el puerto 5000
- ✅ Permite conexiones desde la red local
- ✅ Verifica la configuración

### 3. Configurar Credenciales

Edita el archivo `.env` con tus credenciales de BioStar 2:

```powershell
notepad .env
```

Configura:
```env
BIOSTAR_HOST=https://10.0.0.100
BIOSTAR_USER=tu_usuario
BIOSTAR_PASSWORD=tu_contraseña
```

### 4. Iniciar el Servidor

```powershell
.\iniciar.ps1
```

O manualmente:
```powershell
.\venv\Scripts\Activate.ps1
python run_webapp.py
```

## 🌐 Acceso al Sistema

### Desde el servidor local:
```
http://localhost:5000
```

### Desde otra máquina en la red (10.0.0.10):
```
http://10.0.0.10:5000
```

### Credenciales por defecto:
- **Usuario**: `admin`
- **Contraseña**: `admin123`

⚠️ **IMPORTANTE**: Cambia la contraseña después del primer inicio de sesión.

## 📋 Requisitos

- Windows 10/11 o Windows Server
- Python 3.8 o superior
- Acceso a BioStar 2 API
- Conexión de red a 10.0.0.100 (servidor BioStar)

## 🔧 Verificación de Conectividad

### Verificar que el servidor está escuchando:
```powershell
netstat -ano | findstr :5000
```

### Probar desde otra máquina:
```powershell
Test-NetConnection -ComputerName 10.0.0.10 -Port 5000
```

## 🐛 Solución de Problemas

### Error: "Puerto 5000 ya está en uso"
```powershell
# Ver qué proceso está usando el puerto
Get-NetTCPConnection -LocalPort 5000 | Select-Object OwningProcess
Get-Process -Id <PID>

# Detener el proceso si es necesario
Stop-Process -Id <PID> -Force
```

### Error: "No se puede conectar desde la red"
1. Verifica que el firewall esté configurado: `.\configurar_firewall.ps1`
2. Verifica que el servidor esté escuchando en `0.0.0.0` (ya configurado)
3. Verifica la configuración de red de Windows

### Error: "No se puede conectar a BioStar"
1. Verifica la IP en `.env`: `BIOSTAR_HOST=https://10.0.0.100`
2. Prueba la conectividad: `Test-NetConnection -ComputerName 10.0.0.100 -Port 443`
3. Verifica las credenciales en `.env`

## 📚 Documentación Adicional

- **README.md**: Documentación completa del sistema
- **CONFIGURACION_RED.md**: Detalles de configuración de red
- **config/device_aliases.json**: Configuración de aliases de dispositivos

## 🔄 Actualización

Para actualizar el sistema:

```powershell
# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Actualizar dependencias
pip install -r requirements.txt --upgrade

# Reiniciar el servidor
python run_webapp.py
```

## 📞 Soporte

Para más información, consulta:
- README.md (documentación completa)
- CONFIGURACION_RED.md (configuración de red)
- Logs del servidor (consola)

---

**Versión**: 1.0  
**Última actualización**: 2025-11-25
