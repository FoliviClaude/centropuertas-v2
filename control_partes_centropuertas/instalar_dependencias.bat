@echo off
REM ============================================================
REM  Instalacion inicial de la app de Partes de Trabajo.
REM  Ejecutar este archivo UNA SOLA VEZ (o cada vez que se
REM  actualice requirements.txt). Doble clic para ejecutarlo.
REM ============================================================
cd /d "%~dp0"

echo Instalando dependencias de Python...
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo Hubo un problema instalando las dependencias.
    echo Comprueba que Python esta instalado y disponible en el PATH.
    pause
    exit /b 1
)

echo.
echo Instalacion completada correctamente.
echo Ya puedes usar "iniciar_app.bat" para arrancar la aplicacion.
pause
