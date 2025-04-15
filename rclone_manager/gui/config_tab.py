"""
Pestaña de configuraciones para Rclone Manager.

Este módulo gestiona la pestaña de configuraciones donde el usuario puede
configurar la ruta de rclone, ver la versión, y gestionar los remotos.
"""
import os
import platform
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from tkinter import filedialog, simpledialog
import threading
import webbrowser

from core.rclone import RcloneRunner


class ConfigTab:
    """Clase que maneja la pestaña de configuraciones."""

    def __init__(self, app):
        """
        Inicializa la pestaña de configuraciones.

        Args:
            app (RcloneManagerApp): Referencia a la aplicación principal.
        """
        self.app = app
        self.rclone_runner = RcloneRunner(app.rclone_path)

        # Crear el frame principal de la pestaña
        self.frame = ttk.Frame(app.notebook, padding=10)

        # Configurar componentes de la interfaz
        self.setup_ui()

    def setup_ui(self):
        """Configura los componentes de la interfaz de usuario."""
        # Panel de ruta de rclone
        self.setup_path_panel()

        # Panel de versión
        self.setup_version_panel()

        # Separador
        ttk.Separator(self.frame, orient="horizontal").pack(fill="x", pady=10)

        # Título de configuraciones
        ttk.Label(
            self.frame,
            text="Configuraciones de Rclone",
            font=("Arial", 12, "bold")
        ).pack(pady=5, anchor="w")

        # Panel de remotos
        self.setup_remotes_panel()

        # Panel de detalles
        self.setup_details_panel()

        # Panel de botones
        self.setup_buttons_panel()

    def setup_path_panel(self):
        """Configura el panel de ruta de rclone."""
        path_frame = ttk.Frame(self.frame)
        path_frame.pack(fill="x", pady=10)

        ttk.Label(
            path_frame,
            text="Ruta de rclone:"
        ).pack(side=LEFT, padx=5)

        self.rclone_path_var = ttk.StringVar(value=self.app.rclone_path)
        ttk.Entry(
            path_frame,
            textvariable=self.rclone_path_var,
            width=50
        ).pack(side=LEFT, padx=5, fill="x", expand=True)

        ttk.Button(
            path_frame,
            text="Examinar",
            command=self.browse_rclone
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            path_frame,
            text="Guardar",
            command=self.save_rclone_path
        ).pack(side=LEFT, padx=5)

    def setup_version_panel(self):
        """Configura el panel de versión."""
        version_frame = ttk.Frame(self.frame)
        version_frame.pack(fill="x", pady=5)

        ttk.Label(
            version_frame,
            text="Versión de rclone:"
        ).pack(side=LEFT, padx=5)

        self.version_var = ttk.StringVar(value="Desconocida")
        ttk.Label(
            version_frame,
            textvariable=self.version_var
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            version_frame,
            text="Verificar",
            command=self.check_version
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            version_frame,
            text="Actualizar rclone",
            command=self.update_rclone
        ).pack(side=LEFT, padx=5)

    def setup_remotes_panel(self):
        """Configura el panel de remotos."""
        remotes_frame = ttk.Frame(self.frame)
        remotes_frame.pack(fill="both", expand=True, pady=5)

        self.remotes_list = tk.Listbox(remotes_frame, height=10)
        self.remotes_list.pack(side=LEFT, fill="both", expand=True, padx=5)

        scrollbar = ttk.Scrollbar(
            remotes_frame,
            orient="vertical",
            command=self.remotes_list.yview
        )
        scrollbar.pack(side=RIGHT, fill="y")
        self.remotes_list.config(yscrollcommand=scrollbar.set)

        # Vincular selección a mostrar detalles
        self.remotes_list.bind('<<ListboxSelect>>', lambda e: self.view_remote_details())

    def setup_details_panel(self):
        """Configura el panel de detalles."""
        details_frame = ttk.Labelframe(self.frame, text="Detalles")
        details_frame.pack(fill="both", expand=True, pady=10)

        self.remote_details = tk.Text(
            details_frame,
            height=8,
            width=70,
            wrap="word"
        )
        self.remote_details.pack(fill="both", expand=True, padx=5, pady=5)

    def setup_buttons_panel(self):
        """Configura el panel de botones."""
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill="x", pady=10)

        ttk.Button(
            btn_frame,
            text="Nueva configuración",
            command=self.new_config
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Ver detalles",
            command=self.view_remote_details
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Eliminar configuración",
            command=self.delete_config
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Refrescar",
            command=self.refresh_configs
        ).pack(side=LEFT, padx=5)

    def browse_rclone(self):
        """Abre un diálogo para seleccionar el ejecutable de rclone."""
        is_windows = platform.system() == "Windows"
        filetypes = [("Ejecutable", "*.exe"), ("Todos los archivos", "*.*")] if is_windows else [
            ("Todos los archivos", "*.*")]

        path = filedialog.askopenfilename(
            title="Seleccionar rclone",
            filetypes=filetypes
        )

        if path:
            self.rclone_path_var.set(path)

    def save_rclone_path(self):
        """Guarda la ruta de rclone en la configuración."""
        path = self.rclone_path_var.get()

        if not os.path.exists(path):
            Messagebox.show_error(
                title="Error",
                message="La ruta especificada no existe."
            )
            return

        # Actualizar rutas
        self.app.rclone_path = path
        self.app.config["rclone_path"] = path
        self.app.config_manager.save_config(self.app.config)

        # Actualizar el runner
        self.rclone_runner.set_rclone_path(path)

        # Notificar al usuario
        self.app.status_var.set("Ruta de rclone guardada")

        # Verificar versión con la nueva ruta
        self.check_version()

    def check_version(self):
        """Verifica la versión de rclone."""

        def task():
            try:
                version = self.rclone_runner.get_version()
                self.version_var.set(version)
                self.app.status_var.set("Versión verificada")
            except Exception as e:
                self.version_var.set("Error")
                self.app.status_var.set(f"Error al obtener la versión: {e}")

        # Ejecutar en un hilo para no bloquear la interfaz
        threading.Thread(target=task, daemon=True).start()

    def update_rclone(self):
        """Abre el navegador para descargar la última versión de rclone."""
        webbrowser.open("https://rclone.org/downloads/")
        self.app.status_var.set("Navegador abierto para descargar rclone")

    def load_remotes(self):
        """Carga la lista de remotos configurados."""
        # Limpiar lista actual
        self.remotes_list.delete(0, "end")

        def task():
            try:
                # Obtener remotos
                remotes = self.rclone_runner.list_remotes()

                # Actualizar interfaz desde el hilo principal
                self.app.root.after(0, lambda: self._update_remotes_list(remotes))
            except Exception as e:
                # Notificar error
                self.app.root.after(0, lambda: self.app.status_var.set(f"Error al cargar remotos: {e}"))

        # Ejecutar en un hilo
        threading.Thread(target=task, daemon=True).start()

    def _update_remotes_list(self, remotes):
        """
        Actualiza la lista de remotos en la interfaz.

        Args:
            remotes (list): Lista de nombres de remotos.
        """
        if not remotes:
            self.app.status_var.set("No se encontraron remotos configurados")
            return

        # Actualizar lista
        for remote in remotes:
            self.remotes_list.insert("end", remote)

        # Actualizar comboboxes en todas las pestañas
        for tab_name, tab in self.app.tabs.items():
            if hasattr(tab, 'update_remotes'):
                tab.update_remotes(remotes)

        # Notificar
        self.app.status_var.set(f"Se cargaron {len(remotes)} remotos")

    def new_config(self):
        """Abre una nueva ventana para configurar un remoto."""
        # Simplemente ejecutar rclone config en una nueva ventana
        import subprocess
        import os

        try:
            # En Windows usar CMD, en Unix usar terminal
            if platform.system() == "Windows":
                subprocess.Popen(["cmd", "/k", self.app.rclone_path, "config"])
            else:
                terminal_cmd = "xterm"  # Predeterminado
                # Detectar terminal disponible
                for term in ["gnome-terminal", "konsole", "xfce4-terminal", "terminal", "iTerm", "xterm"]:
                    if shutil.which(term):
                        terminal_cmd = term
                        break

                # Ejecutar en terminal
                subprocess.Popen([terminal_cmd, "-e", f"{self.app.rclone_path} config"])

            # Programar actualización de remotos después de un tiempo
            self.app.root.after(5000, self.refresh_configs)

            self.app.status_var.set("Abriendo configuración de rclone")
        except Exception as e:
            Messagebox.show_error(
                title="Error",
                message=f"No se pudo abrir la configuración: {e}"
            )

    def view_remote_details(self):
        """Muestra los detalles del remoto seleccionado."""
        try:
            # Obtener selección
            index = self.remotes_list.curselection()[0]
            remote = self.remotes_list.get(index)

            # Limpiar y mostrar mensaje de espera
            self.remote_details.delete("1.0", "end")
            self.remote_details.insert("end", f"Obteniendo detalles para {remote}...\n")
            self.remote_details.update()

            # Función para obtener detalles
            def fetch_details():
                details = self.rclone_runner.get_remote_details(remote)

                # Actualizar desde el hilo principal
                self.app.root.after(0, lambda: self._update_remote_details(details))

            # Ejecutar en un hilo
            threading.Thread(target=fetch_details, daemon=True).start()

        except IndexError:
            # No hay selección
            self.remote_details.delete("1.0", "end")
            self.remote_details.insert("end", "Seleccione un remoto para ver detalles.")
        except Exception as e:
            # Otro error
            self.remote_details.delete("1.0", "end")
            self.remote_details.insert("end", f"Error: {str(e)}")

    def _update_remote_details(self, details):
        """
        Actualiza el panel de detalles con la información obtenida.

        Args:
            details (str): Detalles del remoto.
        """
        self.remote_details.delete("1.0", "end")
        self.remote_details.insert("end", details)

    def delete_config(self):
        """Elimina un remoto seleccionado."""
        try:
            # Obtener selección
            index = self.remotes_list.curselection()[0]
            remote = self.remotes_list.get(index)

            # Confirmar eliminación
            if Messagebox.yesno(
                    title="Eliminar remoto",
                    message=f"¿Estás seguro de eliminar el remoto '{remote}'?\n\nEsta acción no se puede deshacer."
            ):
                # Eliminar remoto
                result = self.rclone_runner.delete_remote(remote)

                if result['success']:
                    # Actualizar lista
                    self.remotes_list.delete(index)
                    self.app.status_var.set(f"Remoto '{remote}' eliminado")

                    # Actualizar comboboxes en otras pestañas
                    self.refresh_configs()
                else:
                    Messagebox.show_error(
                        title="Error",
                        message=f"No se pudo eliminar el remoto: {result['error']}"
                    )
        except IndexError:
            # No hay selección
            Messagebox.show_warning(
                title="Aviso",
                message="No se ha seleccionado ningún remoto."
            )
        except Exception as e:
            # Otro error
            Messagebox.show_error(
                title="Error",
                message=f"Error al eliminar el remoto: {e}"
            )

    def refresh_configs(self):
        """Actualiza la lista de remotos."""
        self.load_remotes()
        self.app.status_var.set("Actualizando lista de remotos...")