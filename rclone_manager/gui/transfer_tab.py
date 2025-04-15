"""
Pestaña de transferencia para Rclone Manager.

Este módulo gestiona la pestaña de transferencia donde el usuario puede
transferir archivos entre ubicaciones locales y remotos.
"""
import os
import platform
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from tkinter import filedialog
import threading
import datetime

from core.rclone import RcloneRunner


class TransferTab:
    """Clase que maneja la pestaña de transferencia."""

    def __init__(self, app):
        """
        Inicializa la pestaña de transferencia.

        Args:
            app (RcloneManagerApp): Referencia a la aplicación principal.
        """
        self.app = app
        self.rclone_runner = RcloneRunner(app.rclone_path)
        self.transfer_process_id = None

        # Crear el frame principal de la pestaña
        self.frame = ttk.Frame(app.notebook, padding=10)

        # Configurar componentes de la interfaz
        self.setup_ui()

        # Cargar configuración guardada
        self.load_config()

    def setup_ui(self):
        """Configura los componentes de la interfaz de usuario."""
        # Panel de origen
        self.setup_source_panel()

        # Panel de destino
        self.setup_destination_panel()

        # Panel de método de transferencia
        self.setup_method_panel()

        # Panel de opciones
        self.setup_options_panel()

        # Panel de botones
        self.setup_buttons_panel()

    def setup_source_panel(self):
        """Configura el panel de origen."""
        source_frame = ttk.Labelframe(self.frame, text="Origen", padding=10)
        source_frame.pack(fill="x", pady=10)

        # Tipo de origen (local o remoto)
        ttk.Label(source_frame, text="Tipo de origen:").grid(row=0, column=0, sticky="w", pady=5)

        self.source_type_var = ttk.StringVar(value="local")
        ttk.Radiobutton(
            source_frame,
            text="Carpeta local",
            variable=self.source_type_var,
            value="local",
            command=self.update_source_ui
        ).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Radiobutton(
            source_frame,
            text="Almacenamiento remoto",
            variable=self.source_type_var,
            value="remote",
            command=self.update_source_ui
        ).grid(row=0, column=2, sticky="w", padx=5)

        # Panel para origen local
        self.source_local_frame = ttk.Frame(source_frame)
        ttk.Label(self.source_local_frame, text="Ruta local:").pack(side=LEFT, padx=5)

        self.source_path_var = ttk.StringVar()
        self.source_path_entry = ttk.Entry(
            self.source_local_frame,
            textvariable=self.source_path_var,
            width=50
        )
        self.source_path_entry.pack(side=LEFT, padx=5, fill="x", expand=True)

        self.source_browse_btn = ttk.Button(
            self.source_local_frame,
            text="Examinar",
            command=self.browse_source
        )
        self.source_browse_btn.pack(side=LEFT, padx=5)

        # Panel para origen remoto (inicialmente oculto)
        self.source_remote_frame = ttk.Frame(source_frame)
        ttk.Label(self.source_remote_frame, text="Remoto:").pack(side=LEFT, padx=5)

        self.source_remote_var = ttk.StringVar()
        self.source_remote_combo = ttk.Combobox(
            self.source_remote_frame,
            textvariable=self.source_remote_var,
            state="readonly",
            width=20
        )
        self.source_remote_combo.pack(side=LEFT, padx=5, fill="x", expand=True)

        ttk.Label(self.source_remote_frame, text="Ruta en remoto:").pack(side=LEFT, padx=(15, 5))

        self.source_remote_path_var = ttk.StringVar()
        ttk.Entry(
            self.source_remote_frame,
            textvariable=self.source_remote_path_var,
            width=20
        ).pack(side=LEFT, padx=5, fill="x", expand=True)

        # Colocar el frame inicial
        self.source_local_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=5)

    def setup_destination_panel(self):
        """Configura el panel de destino."""
        dest_frame = ttk.Labelframe(self.frame, text="Destino", padding=10)
        dest_frame.pack(fill="x", pady=10)

        # Tipo de destino (local o remoto)
        ttk.Label(dest_frame, text="Tipo de destino:").grid(row=0, column=0, sticky="w", pady=5)

        self.dest_type_var = ttk.StringVar(value="remote")
        ttk.Radiobutton(
            dest_frame,
            text="Carpeta local",
            variable=self.dest_type_var,
            value="local",
            command=self.update_dest_ui
        ).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Radiobutton(
            dest_frame,
            text="Almacenamiento remoto",
            variable=self.dest_type_var,
            value="remote",
            command=self.update_dest_ui
        ).grid(row=0, column=2, sticky="w", padx=5)

        # Panel para destino local
        self.dest_local_frame = ttk.Frame(dest_frame)
        ttk.Label(self.dest_local_frame, text="Ruta local:").pack(side=LEFT, padx=5)

        self.dest_path_var = ttk.StringVar()
        self.dest_path_entry = ttk.Entry(
            self.dest_local_frame,
            textvariable=self.dest_path_var,
            width=50
        )
        self.dest_path_entry.pack(side=LEFT, padx=5, fill="x", expand=True)

        self.dest_browse_btn = ttk.Button(
            self.dest_local_frame,
            text="Examinar",
            command=self.browse_dest
        )
        self.dest_browse_btn.pack(side=LEFT, padx=5)

        # Panel para destino remoto
        self.dest_remote_frame = ttk.Frame(dest_frame)
        ttk.Label(self.dest_remote_frame, text="Remoto:").pack(side=LEFT, padx=5)

        self.dest_remote_var = ttk.StringVar()
        self.dest_remote_combo = ttk.Combobox(
            self.dest_remote_frame,
            textvariable=self.dest_remote_var,
            state="readonly",
            width=20
        )
        self.dest_remote_combo.pack(side=LEFT, padx=5, fill="x", expand=True)

        # En el archivo transfer_tab.py, modifica setup_destination_panel()
        # Añade un botón de exploración junto al campo de ruta remota

        ttk.Label(self.dest_remote_frame, text="Ruta en remoto:").pack(side=LEFT, padx=(15, 5))
        self.dest_remote_path_var = ttk.StringVar()
        ttk.Entry(
            self.dest_remote_frame,
            textvariable=self.dest_remote_path_var,
            width=20
        ).pack(side=LEFT, padx=5, fill="x", expand=True)

        # Añadir este botón nuevo
        ttk.Button(
            self.dest_remote_frame,
            text="Explorar",
            command=self.browse_remote_dest
        ).pack(side=LEFT, padx=5)

        # Colocar el frame inicial según valor predeterminado
        self.dest_remote_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=5)

    def browse_remote_dest(self):
        """Abre un explorador para navegar por el remoto seleccionado."""
        remote = self.dest_remote_var.get()
        if not remote:
            Messagebox.show_error(
                title="Error",
                message="Selecciona un remoto primero."
            )
            return

        # Crear y configurar una ventana de exploración
        explorer = RemoteExplorer(
            self.app.root,
            self.rclone_runner,
            remote,
            self.dest_remote_path_var
        )
        # La ventana actualizará dest_remote_path_var cuando el usuario seleccione una ubicación
    def setup_method_panel(self):
        """Configura el panel de método de transferencia."""
        method_frame = ttk.Labelframe(self.frame, text="Método de transferencia", padding=10)
        method_frame.pack(fill="x", pady=10)

        self.transfer_method_var = ttk.StringVar(value="copy")

        method_info_frame = ttk.Frame(method_frame)
        method_info_frame.pack(fill="x", expand=True)

        methods = [
            ("copy", "Copiar", "Duplica archivos del origen al destino sin modificar el origen"),
            ("move", "Mover", "Copia archivos y elimina del origen"),
            ("sync", "Sincronizar", "PRECAUCIÓN: Hace el destino idéntico al origen (puede borrar archivos)")
        ]

        for i, (value, name, desc) in enumerate(methods):
            option_frame = ttk.Frame(method_info_frame)
            option_frame.grid(row=i, column=0, sticky="w", pady=3)

            ttk.Radiobutton(
                option_frame,
                text=name,
                variable=self.transfer_method_var,
                value=value
            ).pack(side=LEFT, padx=5)

            ttk.Label(
                option_frame,
                text=desc,
                foreground="gray"
            ).pack(side=LEFT, padx=5)

    def setup_options_panel(self):
        """Configura el panel de opciones de transferencia."""
        options_frame = ttk.Labelframe(self.frame, text="Opciones de transferencia", padding=10)
        options_frame.pack(fill="x", pady=10)

        options_grid = ttk.Frame(options_frame)
        options_grid.pack(fill="x", expand=True, padx=5, pady=5)

        # Transferencias simultáneas
        ttk.Label(
            options_grid,
            text="Transferencias simultáneas:"
        ).grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self.transfers_var = ttk.StringVar(value="4")
        ttk.Spinbox(
            options_grid,
            from_=1,
            to=32,
            textvariable=self.transfers_var,
            width=5
        ).grid(row=0, column=1, sticky="w", padx=5, pady=5)

        # Tamaño de buffer
        ttk.Label(
            options_grid,
            text="Tamaño de buffer (MB):"
        ).grid(row=0, column=2, sticky="w", padx=(15, 5), pady=5)

        self.buffer_var = ttk.StringVar(value="32")
        ttk.Spinbox(
            options_grid,
            from_=8,
            to=1024,
            textvariable=self.buffer_var,
            width=5
        ).grid(row=0, column=3, sticky="w", padx=5, pady=5)

        # Verificadores
        ttk.Label(
            options_grid,
            text="Verificadores:"
        ).grid(row=1, column=0, sticky="w", padx=5, pady=5)

        self.checkers_var = ttk.StringVar(value="8")
        ttk.Spinbox(
            options_grid,
            from_=1,
            to=64,
            textvariable=self.checkers_var,
            width=5
        ).grid(row=1, column=1, sticky="w", padx=5, pady=5)

        # Chunk size
        ttk.Label(
            options_grid,
            text="Chunk size (MB):"
        ).grid(row=1, column=2, sticky="w", padx=(15, 5), pady=5)

        self.chunk_var = ttk.StringVar(value="16")
        ttk.Spinbox(
            options_grid,
            from_=1,
            to=256,
            textvariable=self.chunk_var,
            width=5
        ).grid(row=1, column=3, sticky="w", padx=5, pady=5)

        # Opciones adicionales
        checks_frame = ttk.Frame(options_frame)
        checks_frame.pack(fill="x", expand=True, padx=5, pady=5)

        # Verificar archivos
        self.check_var = ttk.BooleanVar(value=False)
        ttk.Checkbutton(
            checks_frame,
            text="Verificar archivos al terminar (--check-first)",
            variable=self.check_var
        ).pack(side=LEFT, padx=10)

        # Simulación
        self.dry_run_var = ttk.BooleanVar(value=False)
        ttk.Checkbutton(
            checks_frame,
            text="Simulación (--dry-run: no realiza cambios)",
            variable=self.dry_run_var
        ).pack(side=LEFT, padx=10)

    def setup_buttons_panel(self):
        """Configura el panel de botones."""
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill="x", pady=15)

        # Botón de transferencia
        self.transfer_btn = ttk.Button(
            btn_frame,
            text="Iniciar Transferencia",
            command=self.transfer_files,
            style="Accent.TButton"
        )
        self.transfer_btn.pack(side=LEFT, padx=5)

        # Guardar configuración
        ttk.Button(
            btn_frame,
            text="Guardar configuración",
            command=self.save_transfer_config
        ).pack(side=LEFT, padx=5)

    def update_remotes(self, remotes):
        """
        Actualiza la lista de remotos disponibles.

        Args:
            remotes (list): Lista de nombres de remotos.
        """
        # Actualizar combos de remotos
        self.source_remote_combo["values"] = remotes
        self.dest_remote_combo["values"] = remotes

        # Seleccionar el primer remoto si no hay ninguno seleccionado
        if remotes:
            if not self.source_remote_var.get():
                self.source_remote_var.set(remotes[0])

            if not self.dest_remote_var.get():
                self.dest_remote_var.set(remotes[0])

    def load_config(self):
        """Carga la configuración guardada."""
        if "last_transfer" in self.app.config:
            last = self.app.config["last_transfer"]

            # Tipo de origen/destino
            if "source_type" in last:
                self.source_type_var.set(last["source_type"])
                self.update_source_ui()

            if "dest_type" in last:
                self.dest_type_var.set(last["dest_type"])
                self.update_dest_ui()

            # Rutas
            if "source_path" in last:
                self.source_path_var.set(last["source_path"])

            if "dest_path" in last:
                self.dest_path_var.set(last["dest_path"])

            if "source_remote" in last and last["source_remote"]:
                self.source_remote_var.set(last["source_remote"])

            if "source_remote_path" in last:
                self.source_remote_path_var.set(last["source_remote_path"])

            if "dest_remote" in last and last["dest_remote"]:
                self.dest_remote_var.set(last["dest_remote"])

            if "dest_remote_path" in last:
                self.dest_remote_path_var.set(last["dest_remote_path"])

            # Método
            if "method" in last:
                self.transfer_method_var.set(last["method"])

            # Opciones
            if "transfers" in last:
                self.transfers_var.set(last["transfers"])

            if "buffer" in last:
                self.buffer_var.set(last["buffer"])

            if "checkers" in last:
                self.checkers_var.set(last["checkers"])

            if "chunk" in last:
                self.chunk_var.set(last["chunk"])

            if "check" in last:
                self.check_var.set(last["check"])

    def update_source_ui(self):
        """Actualiza la interfaz de origen según el tipo seleccionado."""
        if self.source_type_var.get() == "local":
            # Mostrar panel local, ocultar remoto
            self.source_local_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=5)
            self.source_remote_frame.grid_remove()

            # Habilitar entrada y botón
            self.source_browse_btn.config(state=NORMAL)
            self.source_path_entry.config(state=NORMAL)
        else:
            # Mostrar panel remoto, ocultar local
            self.source_remote_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=5)
            self.source_local_frame.grid_remove()

            # Deshabilitar entrada y botón
            self.source_browse_btn.config(state=DISABLED)
            self.source_path_entry.config(state=DISABLED)

            # Actualizar remotos si es necesario
            if not self.source_remote_combo["values"]:
                remotos = self.app.tabs["config"].remotes_list.get(0, "end")
                if remotos:
                    self.source_remote_combo["values"] = remotos
                    if not self.source_remote_var.get():
                        self.source_remote_var.set(remotos[0])

    def update_dest_ui(self):
        """Actualiza la interfaz de destino según el tipo seleccionado."""
        if self.dest_type_var.get() == "local":
            # Mostrar panel local, ocultar remoto
            self.dest_local_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=5)
            self.dest_remote_frame.grid_remove()

            # Habilitar entrada y botón
            self.dest_browse_btn.config(state=NORMAL)
            self.dest_path_entry.config(state=NORMAL)
        else:
            # Mostrar panel remoto, ocultar local
            self.dest_remote_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=5)
            self.dest_local_frame.grid_remove()

            # Deshabilitar entrada y botón
            self.dest_browse_btn.config(state=DISABLED)
            self.dest_path_entry.config(state=DISABLED)

            # Actualizar remotos si es necesario
            if not self.dest_remote_combo["values"]:
                remotos = self.app.tabs["config"].remotes_list.get(0, "end")
                if remotos:
                    self.dest_remote_combo["values"] = remotos
                    if not self.dest_remote_var.get():
                        self.dest_remote_var.set(remotos[0])

    def browse_source(self):
        """Abre un diálogo para seleccionar la carpeta de origen."""
        path = filedialog.askdirectory(title="Seleccionar carpeta de origen")
        if path:
            self.source_path_var.set(path)

    def browse_dest(self):
        """Abre un diálogo para seleccionar la carpeta de destino."""
        path = filedialog.askdirectory(title="Seleccionar carpeta de destino")
        if path:
            self.dest_path_var.set(path)

    def build_path(self, path_type, remote, remote_path, local_path):
        """
        Construye la ruta completa según el tipo.

        Args:
            path_type (str): Tipo de ruta ('local' o 'remote').
            remote (str): Nombre del remoto.
            remote_path (str): Ruta dentro del remoto.
            local_path (str): Ruta local.

        Returns:
            str: Ruta completa, o None si es inválida.
        """
        if path_type == "local":
            return local_path if local_path else None
        elif path_type == "remote":
            if not remote:
                Messagebox.show_error(
                    title="Error",
                    message="Selecciona un remoto"
                )
                return None

            # Quitar / inicial si existe
            if remote_path and remote_path.startswith("/"):
                remote_path = remote_path[1:]

            return f"{remote}:{remote_path}"

        return None

    def save_transfer_config(self):
        """Guarda la configuración de transferencia."""
        self.app.config["last_transfer"] = {
            "source_type": self.source_type_var.get(),
            "source_path": self.source_path_var.get(),
            "source_remote": self.source_remote_var.get(),
            "source_remote_path": self.source_remote_path_var.get(),
            "dest_type": self.dest_type_var.get(),
            "dest_path": self.dest_path_var.get(),
            "dest_remote": self.dest_remote_var.get(),
            "dest_remote_path": self.dest_remote_path_var.get(),
            "method": self.transfer_method_var.get(),
            "transfers": self.transfers_var.get(),
            "buffer": self.buffer_var.get(),
            "checkers": self.checkers_var.get(),
            "chunk": self.chunk_var.get(),
            "check": self.check_var.get()
        }

        # Guardar configuración
        self.app.config_manager.save_config(self.app.config)

        # Notificar
        self.app.status_var.set("Configuración de transferencia guardada")

    def transfer_files(self):
        """Inicia la transferencia de archivos."""
        # Construir rutas de origen y destino
        if self.source_type_var.get() == "local":
            source = self.build_path("local", None, None, self.source_path_var.get())
        else:
            source = self.build_path(
                "remote",
                self.source_remote_var.get(),
                self.source_remote_path_var.get(),
                None
            )

        if self.dest_type_var.get() == "local":
            dest = self.build_path("local", None, None, self.dest_path_var.get())
        else:
            dest = self.build_path(
                "remote",
                self.dest_remote_var.get(),
                self.dest_remote_path_var.get(),
                None
            )

        # Verificar rutas
        if not source:
            Messagebox.show_error(
                title="Error",
                message="Origen incompleto. Verifica que hayas especificado la ruta (local o en remoto)."
            )
            return

        if not dest:
            Messagebox.show_error(
                title="Error",
                message="Destino incompleto. Verifica que hayas especificado la ruta (local o en remoto)."
            )
            return

        # Obtener método
        method = self.transfer_method_var.get()

        # Confirmar si es sincronización
        if method == "sync" and not self.dry_run_var.get():
            if not Messagebox.yesno(
                    title="Confirmar sincronización",
                    message="La sincronización hará que el destino sea idéntico al origen.\n\n"
                            "Esto podría ELIMINAR archivos en el destino que no existen en el origen.\n\n"
                            "¿Estás seguro de continuar?"
            ):
                return

        # Guardar configuración
        self.save_transfer_config()

        # Configurar opciones
        options = {
            "transfers": self.transfers_var.get(),
            "buffer-size": f"{self.buffer_var.get()}M",
            "checkers": self.checkers_var.get(),
            "drive-chunk-size": f"{self.chunk_var.get()}M",
            "progress": True
        }

        if self.check_var.get():
            options["check-first"] = True

        if self.dry_run_var.get():
            options["dry-run"] = True

        # Crear ventana de progreso
        self._create_progress_window(source, dest, method, options)

    def _create_progress_window(self, source, dest, method, options):
        """
        Crea una ventana de progreso para la transferencia.

        Args:
            source (str): Ruta de origen.
            dest (str): Ruta de destino.
            method (str): Método de transferencia.
            options (dict): Opciones adicionales.
        """
        # Crear ventana
        progress_window = ttk.Toplevel(self.app.root)
        progress_window.title(f"Progreso de transferencia: {method}")
        progress_window.geometry("700x500")
        progress_window.grab_set()  # Modal

        # Panel de información
        info_frame = ttk.Frame(progress_window, padding=10)
        info_frame.pack(fill="x")

        # Origen
        ttk.Label(
            info_frame,
            text="Origen:",
            font=("", 10, "bold")
        ).grid(row=0, column=0, sticky="w", padx=5)

        ttk.Label(
            info_frame,
            text=source
        ).grid(row=0, column=1, sticky="w", padx=5)

        # Destino
        ttk.Label(
            info_frame,
            text="Destino:",
            font=("", 10, "bold")
        ).grid(row=1, column=0, sticky="w", padx=5)

        ttk.Label(
            info_frame,
            text=dest
        ).grid(row=1, column=1, sticky="w", padx=5)

        # Método
        ttk.Label(
            info_frame,
            text="Método:",
            font=("", 10, "bold")
        ).grid(row=2, column=0, sticky="w", padx=5)

        method_desc = {"copy": "Copiar", "move": "Mover", "sync": "Sincronizar"}
        ttk.Label(
            info_frame,
            text=method_desc.get(method, method)
        ).grid(row=2, column=1, sticky="w", padx=5)

        # Separador
        ttk.Separator(progress_window, orient="horizontal").pack(fill="x", padx=10, pady=10)

        # Indicadores de progreso
        progress_frame = ttk.Frame(progress_window, padding=10)
        progress_frame.pack(fill="x", padx=10)

        progress_metrics = ttk.Frame(progress_frame)
        progress_metrics.pack(fill="x", pady=5)

        # Total
        ttk.Label(
            progress_metrics,
            text="Transferido:",
            font=("", 9, "bold")
        ).grid(row=0, column=0, sticky="w", padx=(0, 5))

        self.progress_transferred = ttk.StringVar(value="0 B / 0 B")
        ttk.Label(
            progress_metrics,
            textvariable=self.progress_transferred
        ).grid(row=0, column=1, sticky="w", padx=5)

        # Velocidad
        ttk.Label(
            progress_metrics,
            text="Velocidad:",
            font=("", 9, "bold")
        ).grid(row=0, column=2, sticky="w", padx=(20, 5))

        self.progress_speed = ttk.StringVar(value="0 B/s")
        ttk.Label(
            progress_metrics,
            textvariable=self.progress_speed
        ).grid(row=0, column=3, sticky="w", padx=5)

        # ETA
        ttk.Label(
            progress_metrics,
            text="Tiempo restante:",
            font=("", 9, "bold")
        ).grid(row=1, column=0, sticky="w", padx=(0, 5))

        self.progress_eta = ttk.StringVar(value="-")
        ttk.Label(
            progress_metrics,
            textvariable=self.progress_eta
        ).grid(row=1, column=1, sticky="w", padx=5)

        # Archivos
        ttk.Label(
            progress_metrics,
            text="Archivos:",
            font=("", 9, "bold")
        ).grid(row=1, column=2, sticky="w", padx=(20, 5))

        self.progress_files = ttk.StringVar(value="0 / 0")
        ttk.Label(
            progress_metrics,
            textvariable=self.progress_files
        ).grid(row=1, column=3, sticky="w", padx=5)

        # Barra de progreso
        self.progress_bar = ttk.Progressbar(progress_frame, mode="indeterminate")
        self.progress_bar.pack(fill="x", pady=10)
        self.progress_bar.start()

        # Salida de texto
        output_frame = ttk.Frame(progress_window)
        output_frame.pack(expand=True, fill="both", padx=10, pady=10)

        self.output_text = tk.Text(output_frame, wrap="word")
        self.output_text.pack(expand=True, fill="both", side=LEFT)

        scrollbar = ttk.Scrollbar(output_frame, command=self.output_text.yview)
        scrollbar.pack(side=RIGHT, fill="y")
        self.output_text.config(yscrollcommand=scrollbar.set)

        # Panel de estado y botón
        status_frame = ttk.Frame(progress_window, padding=10)
        status_frame.pack(fill="x")

        # Estado
        self.transfer_status = ttk.StringVar(value="Iniciando transferencia...")
        ttk.Label(
            status_frame,
            textvariable=self.transfer_status
        ).pack(side=LEFT, padx=10)

        # Botón de cancelar
        self.cancel_btn = ttk.Button(
            status_frame,
            text="Cancelar",
            command=lambda: self._cancel_transfer(progress_window)
        )
        self.cancel_btn.pack(side=RIGHT, padx=5)

        # Iniciar transferencia
        self._start_transfer(source, dest, method, options, progress_window)

    def _start_transfer(self, source, dest, method, options, progress_window):
        """
        Inicia la transferencia en un hilo separado.

        Args:
            source (str): Ruta de origen.
            dest (str): Ruta de destino.
            method (str): Método de transferencia.
            options (dict): Opciones adicionales.
            progress_window (ttk.Toplevel): Ventana de progreso.
        """

        # Función para procesar cada línea de salida
        def process_output(line):
            # Marcar ventana como cerrada si ya no existe
            if not progress_window.winfo_exists():
                return

            # Línea especial para código de retorno
            if line.startswith("__RETURN_CODE:"):
                try:
                    code = int(line.split(":")[-1].strip("__ \n"))

                    # Actualizar interfaz desde el hilo principal
                    self.app.root.after(0, lambda: self._update_progress_finished(code, progress_window))
                except:
                    pass
                return

            # Línea especial para error
            if line.startswith("__ERROR:"):
                error_msg = line.split(":")[-1].strip("__ \n")

                # Actualizar interfaz desde el hilo principal
                self.app.root.after(0, lambda: self._update_progress_error(error_msg, progress_window))
                return

            # Descartar líneas vacías
            if not line.strip():
                return

            # Actualizar consola de salida
            self.app.root.after(0, lambda: self._append_output(line, progress_window))

            # Procesar métricas de progreso
            if "Transferred:" in line:
                self.app.root.after(0, lambda: self._update_progress_metrics(line, progress_window))

        # Iniciar transferencia
        def transfer_task():
            try:
                # Mostrar comando
                cmd_str = f"{self.app.rclone_path} {method} {source} {dest}"
                for key, value in options.items():
                    if value is True:
                        cmd_str += f" --{key}"
                    elif value is not False and value is not None:
                        cmd_str += f" --{key} {value}"

                self.app.root.after(0, lambda: self._append_output(f"Ejecutando: {cmd_str}\n\n", progress_window))

                # Iniciar transferencia
                result = self.rclone_runner.transfer(
                    source=source,
                    destination=dest,
                    method=method,
                    options=options,
                    callback=process_output
                )

                # Guardar ID del proceso
                self.transfer_process_id = result.get("process_id")

            except Exception as e:
                # Notificar error
                self.app.root.after(0, lambda: self._update_progress_error(str(e), progress_window))

        # Ejecutar en un hilo separado
        threading.Thread(target=transfer_task, daemon=True).start()

    def _append_output(self, text, progress_window):
        """
        Añade texto a la salida.

        Args:
            text (str): Texto a añadir.
            progress_window (ttk.Toplevel): Ventana de progreso.
        """
        if not progress_window.winfo_exists():
            return

        self.output_text.insert("end", text)
        self.output_text.see("end")

    def _update_progress_metrics(self, line, progress_window):
        """
        Actualiza las métricas de progreso.

        Args:
            line (str): Línea de salida con métricas.
            progress_window (ttk.Toplevel): Ventana de progreso.
        """
        if not progress_window.winfo_exists():
            return

        try:
            # Obtener partes de la línea
            parts = line.strip().split(",")

            # Transferido
            if "Transferred:" in parts[0]:
                transferred = parts[0].split(":")[1].strip()
                self.progress_transferred.set(transferred)

            # Velocidad
            if len(parts) > 1 and "Speed:" in parts[1]:
                speed = parts[1].split(":")[1].strip()
                self.progress_speed.set(speed)

            # ETA
            if len(parts) > 2 and "ETA:" in parts[2]:
                eta = parts[2].split(":")[1].strip()
                self.progress_eta.set(eta)

            # Archivos
            for part in parts:
                if "Files:" in part:
                    files = part.split(":")[1].strip()
                    self.progress_files.set(files)
                    break

            # Actualizar estado
            self.transfer_status.set(f"{transferred} a {speed}")

            # Intentar convertir a porcentaje para la barra de progreso
            for part in parts:
                if "%" in part:
                    try:
                        percent = float(part.strip().rstrip("%"))
                        if self.progress_bar["mode"] == "indeterminate":
                            self.progress_bar.stop()
                            self.progress_bar["mode"] = "determinate"

                        self.progress_bar["value"] = percent
                    except:
                        pass
                    break

        except Exception:
            # Ignorar errores al procesar la línea
            pass

    def _update_progress_finished(self, return_code, progress_window):
        """
        Actualiza la interfaz cuando la transferencia finaliza.

        Args:
            return_code (int): Código de retorno.
            progress_window (ttk.Toplevel): Ventana de progreso.
        """
        if not progress_window.winfo_exists():
            return

        # Detener barra de progreso
        self.progress_bar.stop()

        if self.progress_bar["mode"] == "indeterminate":
            self.progress_bar["mode"] = "determinate"

        # Actualizar según el código de retorno
        if return_code == 0:
            # Éxito
            if self.dry_run_var.get():
                self.progress_bar["value"] = 100
                self.transfer_status.set("Simulación completada (sin cambios)")
                self._append_output("\n✅ Simulación completada correctamente. No se realizaron cambios.\n",
                                    progress_window)
            else:
                self.progress_bar["value"] = 100
                self.transfer_status.set("¡Transferencia completada con éxito!")
                self._append_output("\n✅ ¡Transferencia completada con éxito!\n", progress_window)
        else:
            # Error
            self.progress_bar["value"] = 0
            self.transfer_status.set(f"Error en transferencia (código {return_code})")
            self._append_output(f"\n❌ La transferencia falló con código de error: {return_code}\n", progress_window)

        # Cambiar botón a "Cerrar"
        self.cancel_btn.config(text="Cerrar", command=progress_window.destroy)

        # Limpiar proceso
        self.transfer_process_id = None

    def _update_progress_error(self, error_msg, progress_window):
        """
        Actualiza la interfaz cuando hay un error.

        Args:
            error_msg (str): Mensaje de error.
            progress_window (ttk.Toplevel): Ventana de progreso.
        """
        if not progress_window.winfo_exists():
            return

        # Detener barra de progreso
        self.progress_bar.stop()

        if self.progress_bar["mode"] == "indeterminate":
            self.progress_bar["mode"] = "determinate"

        self.progress_bar["value"] = 0

        # Actualizar estado y añadir error a la salida
        self.transfer_status.set(f"Error: {error_msg}")
        self._append_output(f"\n❌ Error durante la transferencia: {error_msg}\n", progress_window)

        # Cambiar botón a "Cerrar"
        self.cancel_btn.config(text="Cerrar", command=progress_window.destroy)

        # Limpiar proceso
        self.transfer_process_id = None

    def _cancel_transfer(self, progress_window):
        """
        Cancela la transferencia en curso.

        Args:
            progress_window (ttk.Toplevel): Ventana de progreso.
        """
        if self.transfer_process_id:
            # Cancelar transferencia
            result = self.rclone_runner.cancel_transfer(self.transfer_process_id)

            # Notificar
            if result.get('success', False):
                self._append_output("\n🛑 Transferencia cancelada por el usuario.\n", progress_window)
                self.transfer_status.set("Transferencia cancelada")
            else:
                self._append_output(f"\n❌ Error al cancelar: {result.get('error', 'Error desconocido')}\n",
                                    progress_window)
                self.transfer_status.set("Error al cancelar transferencia")

            # Limpiar proceso
            self.transfer_process_id = None

            # Cambiar botón a "Cerrar"
            self.cancel_btn.config(text="Cerrar", command=progress_window.destroy)
        else:
            # Si no hay proceso, simplemente cerrar
            progress_window.destroy()