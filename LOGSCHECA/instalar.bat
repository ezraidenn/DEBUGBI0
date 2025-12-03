@echo off
chcp 65001 >nul
echo ================================================================================
echo                    INSTALACIÓN - LOGSCHECA
echo                    BioStar Debug Monitor
echo ================================================================================
echo.

echo Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no está instalado o no está en el PATH
    echo.
    echo Descarga Python desde: https://www.python.org/downloads/
    echo IMPORTANTE: Durante la instalación, marca "Add Python to PATH"
    echo.
    echo Ver archivo: INSTALAR_PYTHON.md para más detalles
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✓ Python encontrado: %PYTHON_VERSION%
echo.

echo Creando entorno virtual...
if exist venv (
    echo ⚠ El entorno virtual ya existe
    set /p RECREATE="¿Deseas recrearlo? (S/N): "
    if /i "%RECREATE%"=="S" (
        echo Eliminando entorno virtual existente...
        rmdir /s /q venv
    )
)

if not exist venv (
    python -m venv venv
    if %errorlevel% equ 0 (
        echo ✓ Entorno virtual creado
    ) else (
        echo ERROR: No se pudo crear el entorno virtual
        pause
        exit /b 1
    )
)
echo.

echo Activando entorno virtual...
call venv\Scripts\activate.bat
echo ✓ Entorno virtual activado
echo.

echo Actualizando pip...
python -m pip install --upgrade pip --quiet
echo ✓ pip actualizado
echo.

echo Instalando dependencias...
echo Esto puede tardar varios minutos...
echo.
pip install -r requirements.txt

if %errorlevel% equ 0 (
    echo.
    echo ✓ Dependencias instaladas correctamente
) else (
    echo.
    echo ⚠ Hubo algunos errores durante la instalación
    echo Revisa los mensajes anteriores para más detalles
)
echo.

echo Verificando configuración...
if not exist .env (
    echo ⚠ Archivo .env no encontrado
    echo Copiando .env.example a .env...
    copy .env.example .env >nul
    echo ✓ Archivo .env creado
    echo.
    echo IMPORTANTE: Edita el archivo .env con tus credenciales de BioStar 2
) else (
    echo ✓ Archivo .env existe
)
echo.

echo Creando directorios...
if not exist data\outputs mkdir data\outputs
if not exist instance mkdir instance
echo ✓ Directorios creados
echo.

echo ================================================================================
echo                        INSTALACIÓN COMPLETADA
echo ================================================================================
echo.
echo Próximos pasos:
echo.
echo 1. Edita el archivo .env con tus credenciales:
echo    notepad .env
echo.
echo 2. Configura el firewall (ejecutar como Administrador):
echo    configurar_firewall.ps1
echo.
echo 3. Inicia el servidor:
echo    iniciar.bat
echo.
echo 4. Accede desde tu navegador:
echo    http://localhost:5000
echo    http://10.0.0.10:5000
echo.
echo Credenciales por defecto:
echo    Usuario: admin
echo    Contraseña: admin123
echo.
pause
