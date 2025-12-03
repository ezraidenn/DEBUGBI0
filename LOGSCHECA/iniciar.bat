@echo off
chcp 65001 >nul
echo ================================================================================
echo                        INICIANDO LOGSCHECA
echo                        BioStar Debug Monitor
echo ================================================================================
echo.

REM Verificar que existe el entorno virtual
if not exist venv (
    echo ERROR: Entorno virtual no encontrado
    echo Ejecuta primero: instalar.bat
    echo.
    pause
    exit /b 1
)

REM Verificar que existe el archivo .env
if not exist .env (
    echo ERROR: Archivo .env no encontrado
    echo Copia .env.example a .env y configura tus credenciales
    echo.
    pause
    exit /b 1
)

echo Activando entorno virtual...
call venv\Scripts\activate.bat
echo ✓ Entorno virtual activado
echo.

echo Verificando puerto 5000...
netstat -ano | findstr :5000 >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠ El puerto 5000 ya está en uso
    echo.
    set /p CONTINUE="¿Deseas continuar de todas formas? (S/N): "
    if /i not "%CONTINUE%"=="S" (
        echo Inicio cancelado
        exit /b 0
    )
) else (
    echo ✓ Puerto 5000 disponible
)

echo.
echo ================================================================================
echo                        Iniciando servidor...
echo ================================================================================
echo.

REM Iniciar el servidor
python run_webapp.py
