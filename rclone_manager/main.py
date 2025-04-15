"""
Rclone Manager - Aplicación de gestión para rclone
--------------------------------------------------
Punto de entrada principal para la aplicación de gestión de rclone.

Este script inicializa la aplicación y carga la interfaz gráfica.
"""
import sys
from pathlib import Path

# Añadir el directorio padre al PATH para importaciones de módulos
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Importar la aplicación GUI
from gui.app import RcloneManagerApp

def main():
    """Punto de entrada principal para la aplicación."""
    app = RcloneManagerApp()
    app.run()

if __name__ == "__main__":
    main()