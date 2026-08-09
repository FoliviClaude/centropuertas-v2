"""
launcher.py
============
Punto de entrada exclusivo para la version compilada (.exe) de la app.

Streamlit se ejecuta normalmente con el comando `streamlit run app.py`,
pero un ejecutable de Windows necesita un unico punto de arranque que
Python pueda invocar directamente. Este lanzador reproduce ese mismo
comando en el mismo proceso, llamando a la CLI interna de Streamlit
(`streamlit.web.cli`) con los argumentos equivalentes.

No se usa para desarrollo normal (ahi se sigue usando
"streamlit run app.py" o "iniciar_app.bat") -- solo lo usa PyInstaller
como script principal al compilar.
"""

from __future__ import annotations

import os
import sys


def _directorio_base() -> str:
    """
    Carpeta donde viven app.py y el resto del codigo fuente de la app.

    - En un .exe compilado con PyInstaller, `sys._MEIPASS` apunta a la
      carpeta donde PyInstaller coloca los ficheros incluidos con
      `--add-data` (app.py, pages_app/, database/, utils/, assets/...).
    - En modo normal (sin compilar), es simplemente la carpeta de este
      archivo.
    """
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    base_dir = _directorio_base()
    os.chdir(base_dir)

    # Import diferido: streamlit debe importarse ya con el cwd correcto.
    from streamlit.web import cli as stcli

    sys.argv = [
        "streamlit",
        "run",
        os.path.join(base_dir, "app.py"),
        "--server.headless=false",
        "--global.developmentMode=false",
        "--server.port=8501",
    ]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
