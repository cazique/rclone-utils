"""
Pestaña de montaje para Rclone Manager.

Este módulo gestiona la pestaña de montaje donde el usuario puede
montar y desmontar remotos como unidades locales.
"""
import os
import platform
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from tkinter import filedialog
import threading
import time

from core.rclone import RcloneRunner
from core.system import check_winfsp_installed


class MountTab:
    """Clase que maneja la pestaña de montaje."""

    def __init__(self, app):
        """
        Inicializa la pestaña de montaje.

        Args:
            app (RcloneManagerApp): Referencia a la aplicación principal.
        """
        self.app = app
        self.rclone_runner = RcloneRunner(app.rclone_path)
        self.mount_process_id = None

        # Crear el frame principal de la pestaña
        self.frame = ttk.Frame(app.notebook, padding=10)

        # Configurar componentes de la interfaz
        self.setup_ui()

        # Cargar configuración guardada
        self.load_config()

    def setup_ui(self):
        """Configura los componentes de la interfaz de usuario."""
        # Panel de selección de remoto y punto de montaje
        self.setup_remote_panel()

        # Panel de opciones de VFS
        self.setup_vfs_panel()

        # Panel de rendimiento
        self.setup_performance_panel()

        # Panel de opciones adicionales
        self.setup_options_panel()

        # Panel de botones
        self.setup_buttons_panel()

        # Estado
        self.mount_status_var = ttk.StringVar(value="No montado")
        ttk.Label(
            self.frame,
            textvariable=self.mount_status_var,
            font=("Arial", 10)
        ).pack(anchor="w", pady=5)

        # Consola
        ttk.Label(self.frame, text="Salida:").pack(anchor="w")
        console_frame = ttk.Frame(self.frame)
        console_frame.pack(fill="both", expand=True, pady=5)

        self.mount_console = tk.Text(console_frame, height=6, wrap="word")
        self.mount_console.pack(side=LEFT, fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            console_frame,
            command=self.mount_console.yview
        )
        scrollbar.pack(side=RIGHT, fill="y")
        self.mount_console.config(yscrollcommand=scrollbar.set)

    def setup_remote_panel(self):
        """Configura el panel de selección de remoto y punto de montaje."""
        remote_frame = ttk.Frame(self.frame)
        remote_frame.pack(fill="x", pady=10)

        ttk.Label(remote_frame, text="Remoto:").pack(side=LEFT, padx=5)

        self.mount_remote_var = ttk.StringVar()
        self.mount_remote_combo = ttk.Combobox(
            remote_frame,
            textvariable=self.mount_remote_var,
            state="readonly",
            width=20
        )
        self.mount_remote_combo.pack(side=LEFT, padx=5, fill="x", expand=True)

        ttk.Label(remote_frame, text="Punto de montaje:").pack(side=LEFT, padx=(15, 5))

        # Punto de montaje según el sistema operativo
        if platform.system() == "Windows":
            self.mount_point_var = ttk.StringVar(value="Z:")
            mount_point_combo = ttk.Combobox(
                remote_frame,
                textvariable=self.mount_point_var,
                values=[f"{chr(i)}:" for i in range(67, 91)],
                width=5
            )
            mount_point_combo.pack(side=LEFT, padx=5)
        else:
            self.mount_point_var = ttk.StringVar(value=os.path.join(os.path.expanduser("~"), "mnt"))
            mount_point_entry = ttk.Entry(
                remote_frame,
                textvariable=self.mount_point_var,
                width=30
            )
            mount_point_entry.pack(side=LEFT, padx=5, fill="x", expand=True)

            ttk.Button(
                remote_frame,
                text="...",
                width=3,
                command=lambda: self.mount_point_var.set(
                    filedialog.askdirectory(title="Seleccionar punto de montaje") or self.mount_point_var.get()
                )
            ).pack(side=LEFT, padx=5)

    def setup_vfs_panel(self):
        """Configura el panel de opciones de VFS."""
        vfs_frame = ttk.Labelframe(self.frame, text="Opciones de VFS")
        vfs_frame.pack(fill="x", pady=10)

        # Modo de caché
        ttk.Label(vfs_frame, text="Modo de caché:").grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.cache_mode_var = ttk.StringVar(value=self.app.config.get("cache_mode", "writes"))

        cache_modes = [
            ("off", "Desactivado - Sin caché local (más lento, menos espacio)"),
            ("minimal", "Mínimo - Solo metadatos (equilibrado)"),
            ("writes", "Escrituras - Archivos recién escritos (recomendado)"),
            ("full", "Completo - Todos los archivos (más rápido, más espacio)")
        ]

        for i, (mode, desc) in enumerate(cache_modes):
            ttk.Radiobutton(
                vfs_frame,
                text=desc,
                variable=self.cache_mode_var,
                value=mode
            ).grid(row=i + 1, column=0, padx=25, pady=2, sticky="w")

        # Opciones de caché
        cache_options_frame = ttk.Frame(vfs_frame)
        cache_options_frame.grid(row=0, column=1, rowspan=5, padx=15, pady=5, sticky="nsew")

        ttk.Label(
            cache_options_frame,
            text="Tamaño máximo de caché (MB):"
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.cache_max_size_var = ttk.StringVar(value="10000")  # 10 GB por defecto
        ttk.Entry(
            cache_options_frame,
            textvariable=self.cache_max_size_var,
            width=10
        ).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(
            cache_options_frame,
            text="Directorio de caché:"
        ).grid(row=1, column=0, padx=5, pady=5, sticky="w")

        self.cache_dir_var = ttk.StringVar(value=os.path.join(os.path.expanduser("~"), ".rclone-cache"))
        cache_dir_entry = ttk.Entry(
            cache_options_frame,
            textvariable=self.cache_dir_var,
            width=30
        )
        cache_dir_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttk.Button(
            cache_options_frame,
            text="...",
            width=3,
            command=lambda: self.cache_dir_var.set(
                filedialog.askdirectory(title="Seleccionar directorio de caché") or self.cache_dir_var.get()
            )
        ).grid(row=1, column=2, padx=0, pady=5, sticky="w")

    def setup_performance_panel(self):
        """Configura el panel de rendimiento."""
        perf_frame = ttk.Labelframe(self.frame, text="Rendimiento")
        perf_frame.pack(fill="x", pady=10)

        perf_grid = ttk.Frame(perf_frame)
        perf_grid.pack(padx=10, pady=10, fill="x")

        # Transferencias simultáneas
        ttk.Label(
            perf_grid,
            text="Transferencias simultáneas:"
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.mount_transfers_var = ttk.StringVar(value="8")
        ttk.Spinbox(
            perf_grid,
            from_=1,
            to=32,
            textvariable=self.mount_transfers_var,
            width=5
        ).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Tamaño de buffer
        ttk.Label(
            perf_grid,
            text="Tamaño de buffer (MB):"
        ).grid(row=0, column=2, padx=(15, 5), pady=5, sticky="w")

        self.mount_buffer_var = ttk.StringVar(value="256")
        ttk.Spinbox(
            perf_grid,
            from_=16,
            to=1024,
            textvariable=self.mount_buffer_var,
            width=5
        ).grid(row=0, column=3, padx=5, pady=5, sticky="w")

        # Chunk size
        ttk.Label(
            perf_grid,
            text="Chunk size (MB):"
        ).grid(row=1, column=0, padx=5, pady=5, sticky="w")

        self.mount_chunk_var = ttk.StringVar(value="32")
        ttk.Spinbox(
            perf_grid,
            from_=8,
            to=256,
            textvariable=self.mount_chunk_var,
            width=5
        ).grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Verificadores
        ttk.Label(
            perf_grid,
            text="Verificadores:"
        ).grid(row=1, column=2, padx=(15, 5), pady=5, sticky="w")

        self.mount_checkers_var = ttk.StringVar(value="16")
        ttk.Spinbox(
            perf_grid,
            from_=1,
            to=64,
            textvariable=self.mount_checkers_var,
            width=5
        ).grid(row=1, column=3, padx=5, pady=5, sticky="w")

    def setup_options_panel(self):
        """Configura el panel de opciones adicionales."""
        options_frame = ttk.Frame(self.frame)
        options_frame.pack(fill="x", pady=5)

        # Modo red
        self.mount_network_var = ttk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Modo red",
            variable=self.mount_network_var
        ).pack(side=LEFT, padx=5)

        # Solo lectura
        self.mount_read_only_var = ttk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame,
            text="Solo lectura",
            variable=self.mount_read_only_var
        ).pack(side=LEFT, padx=5)

        # No modificar fechas
        self.mount_no_modtime_var = ttk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame,
            text="No modificar fechas",
            variable=self.mount_no_modtime_var
        ).pack(side=LEFT, padx=5)

        # Permitir otros usuarios
        self.mount_allow_other_var = ttk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame,
            text="Permitir otros usuarios",
            variable=self.mount_allow_other_var
        ).pack(side=LEFT, padx=5)

    def setup_buttons_panel(self):
        """Configura el panel de botones."""
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill="x", pady=10)

        # Botón de montaje
        self.mount_btn = ttk.Button(
            btn_frame,
            text="Montar",
            command=self.mount_drive,
            style="Accent.TButton"
        )
        self.mount_btn.pack(side=LEFT, padx=5)

        # Botón de desmontaje
        self.unmount_btn = ttk.Button(
            btn_frame,
            text="Desmontar",
            command=self.unmount_drive
        )
        self.unmount_btn.pack(side=LEFT, padx=5)

        # Guardar configuración
        ttk.Button(
            btn_frame,
            text="Guardar configuración",
            command=self.save_mount_config
        ).pack(side=LEFT, padx=5)

        # Crear acceso directo
        ttk.Button(
            btn_frame,
            text="Crear acceso directo",
            command=self.create_mount_shortcut
        ).pack(side=LEFT, padx=5)

    def update_remotes(self, remotes):
        """
        Actualiza la lista de remotos disponibles.

        Args:
            remotes (list): Lista de nombres de remotos.
        """
        self.mount_remote_combo["values"] = remotes

        # Seleccionar el primer remoto si no hay ninguno seleccionado
        if remotes and not self.mount_remote_var.get():
            self.mount_remote_var.set(remotes[0])

    def load_config(self):
        """Carga la configuración guardada."""
        if "last_mount" in self.app.config:
            last = self.app.config["last_mount"]

            # Remoto
            if "remote" in last and last["remote"]:
                self.mount_remote_var.set(last["remote"])

            # Punto de montaje
            if "point" in last and last["point"]:
                self.mount_point_var.set(last["point"])

            # Modo de caché
            if "cache_mode" in last:
                self.cache_mode_var.set(last["cache_mode"])

            # Opciones de rendimiento
            if "transfers" in last:
                self.mount_transfers_var.set(last["transfers"])

            if "buffer" in last:
                self.mount_buffer_var.set(last["buffer"])

            if "chunk" in last:
                self.mount_chunk_var.set(last["chunk"])

            if "checkers" in last:
                self.mount_checkers_var.set(last["checkers"])

    def mount_drive(self):
        """Monta el remoto seleccionado como unidad local."""
        # Verificar WinFSP en Windows
        if platform.system() == "Windows" and not check_winfsp_installed():
            self.mount_console.insert("end", "⚠️ Es necesario instalar WinFSP para montar unidades en Windows.\n")
            self.mount_console.insert("end", "Instala WinFSP y reinicia la aplicación para continuar.\n")
            self.mount_console.see("end")
            return

        # Verificar selección de remoto
        remote = self.mount_remote_var.get()
        if not remote:
            Messagebox.show_error(
                title="Error",
                message="Selecciona un remoto para montar."
            )
            return

        # Punto de montaje
        mount_point = self.mount_point_var.get()

        # En sistemas Unix, verificar que el directorio exista
        if platform.system() != "Windows":
            if not os.path.exists(mount_point):
                try:
                    os.makedirs(mount_point, exist_ok=True)
                except Exception as e:
                    Messagebox.show_error(
                        title="Error",
                        message=f"No se pudo crear el directorio de montaje:\n{e}"
                    )
                    return

        # Guardar configuración actual
        self.save_mount_config()

        # Configurar opciones
        options = {
            "vfs-cache-mode": self.cache_mode_var.get(),
            "transfers": self.mount_transfers_var.get(),
            "buffer-size": f"{self.mount_buffer_var.get()}M",
            "vfs-cache-max-size": f"{self.cache_max_size_var.get()}M",
            "cache-dir": self.cache_dir_var.get(),
            "drive-chunk-size": f"{self.mount_chunk_var.get()}M",
            "checkers": self.mount_checkers_var.get()
        }

        # Opciones booleanas
        if self.mount_network_var.get():
            options["network-mode"] = True

        if self.mount_read_only_var.get():
            options["read-only"] = True

        if self.mount_no_modtime_var.get():
            options["no-modtime"] = True

        if self.mount_allow_other_var.get():
            options["allow-other"] = True

        # Limpiar consola y mostrar comando
        self.mount_console.delete("1.0", "end")

        # Mostrar información
        cmd_str = f"{self.app.rclone_path} mount {remote}: {mount_point}"
        for key, value in options.items():
            if value is True:
                cmd_str += f" --{key}"
            elif value is not False and value is not None:
                cmd_str += f" --{key} {value}"

        self.mount_console.insert("end", f"Ejecutando: {cmd_str}\n\n")
        self.mount_console.insert("end", "Montando remoto. Por favor espera...\n")
        self.mount_console.see("end")

        # Actualizar estado
        self.mount_status_var.set("Montando...")
        self.app.status_var.set(f"Montando {remote} en {mount_point}...")

        # Lanzar el proceso de montaje
        def mount_task():
            try:
                result = self.rclone_runner.mount(f"{remote}:", mount_point, options)

                # Guardar ID del proceso
                self.mount_process_id = result.get('process_id')

                # Actualizar estado desde el hilo principal
                self.app.root.after(0, lambda: self._update_mount_status("Montado"))
                self.app.root.after(0, lambda: self.mount_console.insert("end", "Remoto montado correctamente.\n"))
                self.app.root.after(0, lambda: self.mount_console.insert("end",
                                                                         "NOTA: No cierres esta aplicación mientras quieras mantener el montaje.\n"))
                self.app.root.after(0, lambda: self.mount_console.see("end"))
            except Exception as e:
                # Actualizar estado desde el hilo principal
                self.app.root.after(0, lambda: self._update_mount_status("Error"))
                self.app.root.after(0, lambda: self.mount_console.insert("end", f"Error al montar: {str(e)}\n"))
                self.app.root.after(0, lambda: self.mount_console.see("end"))

        # Ejecutar en un hilo separado
        threading.Thread(target=mount_task, daemon=True).start()

    def unmount_drive(self):
        """Desmonta el punto de montaje."""
        mount_point = self.mount_point_var.get()

        # Actualizar estado
        self.mount_status_var.set("Desmontando...")
        self.app.status_var.set(f"Desmontando {mount_point}...")

        # Limpiar consola
        self.mount_console.insert("end", f"Desmontando {mount_point}...\n")
        self.mount_console.see("end")

        # Función para desmontar
        def unmount_task():
            try:
                result = self.rclone_runner.unmount(mount_point, self.mount_process_id)

                # Actualizar interfaz desde el hilo principal
                if result.get('success', False):
                    self.app.root.after(0, lambda: self._update_mount_status("No montado"))
                    self.app.root.after(0,
                                        lambda: self.mount_console.insert("end", "Unidad desmontada correctamente.\n"))
                    self.app.root.after(0, lambda: self.mount_console.see("end"))
                    self.mount_process_id = None
                else:
                    self.app.root.after(0, lambda: self._update_mount_status("Error al desmontar"))
                    self.app.root.after(0, lambda: self.mount_console.insert("end",
                                                                             f"Error al desmontar: {result.get('error', 'Error desconocido')}\n"))
                    self.app.root.after(0, lambda: self.mount_console.see("end"))
            except Exception as e:
                self.app.root.after(0, lambda: self._update_mount_status("Error"))
                self.app.root.after(0, lambda: self.mount_console.insert("end", f"Error al desmontar: {str(e)}\n"))
                self.app.root.after(0, lambda: self.mount_console.see("end"))

        # Ejecutar en un hilo separado
        threading.Thread(target=unmount_task, daemon=True).start()

    def _update_mount_status(self, status):
        """
        Actualiza el estado de montaje.

        Args:
            status (str): Nuevo estado.
        """
        self.mount_status_var.set(f"Estado: {status}")
        self.app.status_var.set(status)

    def save_mount_config(self):
        """Guarda la configuración de montaje."""
        self.app.config["last_mount"] = {
            "remote": self.mount_remote_var.get(),
            "point": self.mount_point_var.get(),
            "cache_mode": self.cache_mode_var.get(),
            "transfers": self.mount_transfers_var.get(),
            "buffer": self.mount_buffer_var.get(),
            "chunk": self.mount_chunk_var.get(),
            "checkers": self.mount_checkers_var.get()
        }

        # Actualizar modo de caché global
        self.app.config["cache_mode"] = self.cache_mode_var.get()

        # Guardar configuración
        self.app.config_manager.save_config(self.app.config)

        # Notificar
        self.app.status_var.set("Configuración de montaje guardada")

    def create_mount_shortcut(self):
        """Crea un script para montar la unidad."""
        # Verificar selección de remoto
        remote = self.mount_remote_var.get()
        if not remote:
            Messagebox.show_error(
                title="Error",
                message="Selecciona un remoto primero."
            )
            return

        # Obtener punto de montaje
        mount_point = self.mount_point_var.get()

        # Determinar extensión según el sistema operativo
        is_windows = platform.system() == "Windows"
        extension = ".bat" if is_windows else ".sh"

        # Solicitar ubicación para guardar
        file_path = filedialog.asksaveasfilename(
            title="Guardar script de montaje",
            defaultextension=extension,
            filetypes=[
                (f"Script{extension}", f"*{extension}"),
                ("Todos los archivos", "*.*")
            ]
        )

        if not file_path:
            return

        try:
            # Construir opciones
            options = [
                f"--vfs-cache-mode {self.cache_mode_var.get()}",
                f"--transfers {self.mount_transfers_var.get()}",
                f"--buffer-size {self.mount_buffer_var.get()}M",
                f"--drive-chunk-size {self.mount_chunk_var.get()}M",
                f"--checkers {self.mount_checkers_var.get()}",
                f"--vfs-cache-max-size {self.cache_max_size_var.get()}M",
                f'--cache-dir "{self.cache_dir_var.get()}"'
            ]

            # Opciones booleanas
            if self.mount_network_var.get():
                options.append("--network-mode")

            if self.mount_read_only_var.get():
                options.append("--read-only")

            if self.mount_no_modtime_var.get():
                options.append("--no-modtime")

            if self.mount_allow_other_var.get():
                options.append("--allow-other")

            # Construir script según sistema operativo
            if is_windows:
                script_content = "@echo off\n"
                script_content += f'echo Montando {remote} en {mount_point}...\n'
                script_content += f'"{self.app.rclone_path}" mount "{remote}:" "{mount_point}" {" ".join(options)}\n'
                script_content += "pause\n"
            else:
                script_content = "#!/bin/bash\n\n"
                script_content += f'echo "Montando {remote} en {mount_point}..."\n'
                script_content += f'"{self.app.rclone_path}" mount "{remote}:" "{mount_point}" {" ".join(options)}\n'
                script_content += 'echo "Presiona Ctrl+C para desmontar"\n'
                script_content += 'read -p "Presiona Enter para salir" dummy\n'

            # Guardar script
            with open(file_path, 'w') as f:
                f.write(script_content)

            # En sistemas Unix, hacer el script ejecutable
            if not is_windows:
                os.chmod(file_path, 0o755)

            # Notificar
            Messagebox.show_info(
                title="Script creado",
                message=f"Script de montaje guardado en:\n{file_path}"
            )

            self.app.status_var.set("Script de montaje creado")
        except Exception as e:
            Messagebox.show_error(
                title="Error",
                message=f"No se pudo crear el script:\n{str(e)}"
            )