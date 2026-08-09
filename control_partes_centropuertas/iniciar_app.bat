@echo off
REM ============================================================
REM  Arranque diario de la app de Partes de Trabajo Centropuertas.
REM  Doble clic aqui para abrir la aplicacion en el navegador.
REM  Para cerrarla: cerrar esta ventana negra (o pulsar Ctrl+C).
REM ============================================================
cd /d "%~dp0"

echo Iniciando Centropuertas - Partes de Trabajo...
echo (No cierres esta ventana mientras uses la aplicacion)
echo.

python -m streamlit run app.py

pause
