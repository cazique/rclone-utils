"""
Clase principal de la aplicación RcloneManager.

Este módulo contiene la clase principal que inicializa y
gestiona la interfaz de usuario de la aplicación.
"""
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from gui.config_tab import ConfigTab
from gui.mount_tab import MountTab
from gui.transfer_tab import TransferTab
from gui.tools_tab import ToolsTab
from rclone_manager.core.config import ConfigManager
from rclone_manager.core.system import find_rclone_path


class RcloneManagerApp:
    """Clase principal de la aplicación RcloneManager."""

    def __init__(self):
        """Inicializa la aplicación con el tema predeterminado."""
        # Cargar configuración antes de crear la interfaz
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()

        # Configurar el tema
        theme = self.config.get("theme", "flatly")
        self.style = ttk.Style(theme=theme)
        self.root = self.style.master
        self.setup_main_window()

        # Detectar ruta de rclone
        self.rclone_path = self.config.get("rclone_path") or find_rclone_path()
        if self.rclone_path:
            self.config["rclone_path"] = self.rclone_path
            self.config_manager.save_config(self.config)

        # Crear componentes de la interfaz
        self.create_widgets()

        # Variable compartida de estado para todas las pestañas
        self.status_var = ttk.StringVar(value="Listo")

        # Iniciar carga de remotos y verificación de versión
        self.root.after(100, self.tabs["config"].check_version)
        self.root.after(300, self.tabs["config"].load_remotes)

    def setup_main_window(self):
        """Configura la ventana principal de la aplicación."""
        self.root.title("Rclone Manager")
        self.root.geometry("950x700")
        self.root.minsize(850, 650)

        # Hacer que la ventana sea redimensionable
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Configurar el icono de la aplicación si está disponible
        try:
            # En sistemas Windows puede requerir un .ico
            # En Linux/Mac puede usar .png
            icon_path = "assets/icon.png"
            if os.path.exists(icon_path):
                icon = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, icon)
        except Exception:
            pass  # Fallar silenciosamente si no hay icono

    def create_widgets(self):
        """Crea todos los widgets de la interfaz de usuario."""
        # Selector de tema
        self.setup_theme_selector()

        # Notebook para pestañas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=1, fill="both", padx=5, pady=5)

        # Crear pestañas
        self.tabs = {}
        self.tabs["config"] = ConfigTab(self)
        self.tabs["mount"] = MountTab(self)
        self.tabs["transfer"] = TransferTab(self)
        self.tabs["tools"] = ToolsTab(self)

        # Añadir todas las pestañas al notebook
        self.notebook.add(self.tabs["config"].frame, text='Configuraciones')
        self.notebook.add(self.tabs["mount"].frame, text='Montar')
        self.notebook.add(self.tabs["transfer"].frame, text='Transferir')
        self.notebook.add(self.tabs["tools"].frame, text='Herramientas')

        # Barra de estado
        status_bar = ttk.Label(self.root, textvariable=self.status_var,
                               relief=SOLID, anchor="w")
        status_bar.pack(side="bottom", fill="x")

    def setup_theme_selector(self):
        """Configura el selector de temas para la aplicación."""
        container = ttk.Frame(self.root)
        container.pack(fill="x", pady=5, padx=10)

        ttk.Label(container, text="Tema:").pack(side="left", padx=5)

        # Lista de temas disponibles
        themes = [
            "flatly", "darkly", "solar", "superhero", "cosmo",
            "litera", "minty", "lumen", "sandstone", "yeti",
            "pulse", "united", "morph"
        ]

        # Variable para el tema actual
        self.theme_var = ttk.StringVar(value=self.config.get("theme", "flatly"))

        # Combobox para seleccionar tema
        theme_combo = ttk.Combobox(
            container,
            textvariable=self.theme_var,
            values=themes,
            state="readonly",
            width=15
        )
        theme_combo.pack(side="left", padx=5)

        # Función para cambiar tema
        def change_theme(event):
            new_theme = self.theme_var.get()
            self.style.theme_use(new_theme)
            self.config["theme"] = new_theme
            self.config_manager.save_config(self.config)
            self.status_var.set(f"Tema cambiado a {new_theme}")

        # Vincular evento
        theme_combo.bind("<<ComboboxSelected>>", change_theme)

    def run(self):
        """Inicia el bucle principal de la aplicación."""
        self.root.mainloop()