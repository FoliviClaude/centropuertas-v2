@echo off
REM ============================================================
REM  Compila la app a un ejecutable de Windows independiente
REM  (no requiere tener Python instalado en el equipo destino).
REM
REM  Resultado: dist\CentropuertasPartes\CentropuertasPartes.exe
REM  Para distribuirla, comprime toda la carpeta
REM  "dist\CentropuertasPartes" en un .zip y compartela.
REM ============================================================
cd /d "%~dp0"

echo Instalando PyInstaller (si no esta ya instalado)...
python -m pip install --quiet pyinstaller

echo.
echo Compilando... esto puede tardar varios minutos.
echo.

python -m PyInstaller --name CentropuertasPartes --onedir --noconfirm --clean ^
    --icon "assets\logo_centropuertas.ico" ^
    --add-data "app.py;." ^
    --add-data "pages_app;pages_app" ^
    --add-data "database;database" ^
    --add-data "utils;utils" ^
    --add-data "assets;assets" ^
    --add-data ".streamlit;.streamlit" ^
    --collect-all streamlit ^
    --collect-all altair ^
    --collect-all pandas ^
    --collect-all plotly ^
    --collect-all reportlab ^
    --collect-all openpyxl ^
    --collect-all PIL ^
    launcher.py

if errorlevel 1 (
    echo.
    echo La compilacion ha fallado. Revisa el mensaje de error de arriba.
    pause
    exit /b 1
)

echo.
echo Compilacion completada: dist\CentropuertasPartes\CentropuertasPartes.exe
pause
