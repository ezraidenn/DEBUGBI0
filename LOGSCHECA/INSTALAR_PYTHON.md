# 🐍 Instalación de Python - Requisito Previo

## ⚠️ Python no está instalado

Para ejecutar LOGSCHECA necesitas instalar Python primero.

## 📥 Descargar Python

### Opción 1: Desde el sitio oficial (Recomendado)

1. Ve a: **https://www.python.org/downloads/**
2. Descarga **Python 3.11** o superior (versión estable más reciente)
3. Ejecuta el instalador

### Opción 2: Desde Microsoft Store

1. Abre **Microsoft Store**
2. Busca **"Python 3.11"** o **"Python 3.12"**
3. Haz clic en **Instalar**

## ⚙️ Instalación (IMPORTANTE)

Al instalar Python, **MARCA ESTAS OPCIONES**:

✅ **Add Python to PATH** (MUY IMPORTANTE)
✅ **Install pip**
✅ **Install for all users** (opcional pero recomendado)

### Pasos de instalación:

1. Ejecuta el instalador de Python
2. ✅ **MARCA "Add Python to PATH"** en la primera pantalla
3. Selecciona **"Install Now"** o **"Customize installation"**
4. Si eliges personalizar:
   - ✅ Marca todas las opciones
   - ✅ Asegúrate de marcar "Add Python to environment variables"
5. Haz clic en **Install**
6. Espera a que termine la instalación
7. Haz clic en **Close**

## 🔄 Verificar la instalación

Después de instalar Python, **cierra y vuelve a abrir PowerShell**, luego ejecuta:

```powershell
python --version
```

Deberías ver algo como:
```
Python 3.11.x
```

O intenta con:
```powershell
py --version
```

## 📦 Verificar pip

```powershell
python -m pip --version
```

O:
```powershell
py -m pip --version
```

## ✅ Después de instalar Python

Una vez que Python esté instalado y verificado, ejecuta:

```powershell
cd c:\Users\Administrador\Documents\ChecadoresDEBUG\LOGSCHECA
.\instalar.ps1
```

O manualmente:

```powershell
# 1. Crear entorno virtual
python -m venv venv

# 2. Activar entorno virtual
.\venv\Scripts\Activate.ps1

# 3. Actualizar pip
python -m pip install --upgrade pip

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Iniciar el servidor
python run_webapp.py
```

## 🔧 Solución de problemas

### "python no se reconoce como comando"

**Causa**: Python no está en el PATH del sistema.

**Solución**:
1. Reinstala Python y marca "Add Python to PATH"
2. O agrega Python manualmente al PATH:
   - Busca donde está instalado Python (ej: `C:\Python311\` o `C:\Users\Administrador\AppData\Local\Programs\Python\Python311\`)
   - Agrega esa ruta al PATH del sistema
   - Reinicia PowerShell

### Verificar si Python está instalado pero no en PATH

```powershell
# Buscar Python en el sistema
Get-ChildItem -Path C:\ -Filter python.exe -Recurse -ErrorAction SilentlyContinue | Select-Object FullName
```

### Agregar Python al PATH manualmente

1. Abre **Panel de Control** → **Sistema** → **Configuración avanzada del sistema**
2. Haz clic en **Variables de entorno**
3. En **Variables del sistema**, selecciona **Path** y haz clic en **Editar**
4. Haz clic en **Nuevo** y agrega la ruta de Python (ej: `C:\Python311\`)
5. Agrega también la ruta de Scripts (ej: `C:\Python311\Scripts\`)
6. Haz clic en **Aceptar** en todas las ventanas
7. **Cierra y vuelve a abrir PowerShell**

## 📋 Versiones recomendadas

- **Python 3.11.x** o **Python 3.12.x** (más reciente)
- **pip 23.x** o superior (se instala automáticamente con Python)

## 🔗 Enlaces útiles

- **Python oficial**: https://www.python.org/downloads/
- **Documentación Python**: https://docs.python.org/3/
- **Tutorial pip**: https://pip.pypa.io/en/stable/getting-started/

---

**Nota**: Después de instalar Python, continúa con el archivo **INICIO_RAPIDO.md** para completar la instalación de LOGSCHECA.
