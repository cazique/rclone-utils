"""
Pestaña de herramientas para Rclone Manager.

Este módulo gestiona la pestaña de herramientas donde el usuario puede
ejecutar operaciones como verificación de archivos, limpieza de caché, etc.
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
from core.system import calculate_directory_size, format_size


class ToolsTab:
    """Clase que maneja la pestaña de herramientas."""

    def __init__(self, app):
        """
        Inicializa la pestaña de herramientas.

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
        # Panel de verificación de archivos
        self.setup_check_panel()

        # Panel de caché
        self.setup_cache_panel()

        # Panel NCDU
        self.setup_ncdu_panel()

    def setup_check_panel(self):
        """Configura el panel de verificación de archivos."""
        check_frame = ttk.Labelframe(self.frame, text="Verificar integridad de archivos", padding=10)
        check_frame.pack(fill="x", pady=10)

        # Ruta a verificar
        ttk.Label(check_frame, text="Ruta a verificar:").grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self.check_path_var = ttk.StringVar()
        ttk.Entry(check_frame, textvariable=self.check_path_var, width=50).grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(
            check_frame,
            text="Examinar",
            command=lambda: self.check_path_var.set(
                filedialog.askdirectory(title="Seleccionar ruta a verificar") or self.check_path_var.get()
            )
        ).grid(row=0, column=2, padx=5, pady=5)

        # Botón de verificación
        ttk.Button(
            check_frame,
            text="Verificar integridad",
            command=self.check_files,
            style="Accent.TButton"
        ).grid(row=1, column=1, padx=5, pady=5)

        # Descripción
        ttk.Label(
            check_frame,
            text="Esta herramienta comprueba la integridad de los archivos, verificando posibles corrupciones.",
            font=("", 9),
            foreground="gray"
        ).grid(row=2, column=0, columnspan=3, sticky="w", padx=5, pady=5)

    def setup_cache_panel(self):
        """Configura el panel de limpieza de caché."""
        cache_frame = ttk.Labelframe(self.frame, text="Limpiar caché", padding=10)
        cache_frame.pack(fill="x", pady=10)

        # Directorio de caché
        ttk.Label(cache_frame, text="Directorio de caché:").grid(row=0, column=0, sticky="w", padx=5, pady=5)

        # Referencia a la variable de la pestaña de montaje
        if "mount" in self.app.tabs:
            self.cache_dir_var = self.app.tabs["mount"].cache_dir_var
        else:
            self.cache_dir_var = ttk.StringVar(value=os.path.join(os.path.expanduser("~"), ".rclone-cache"))

        ttk.Label(cache_frame, textvariable=self.cache_dir_var).grid(row=0, column=1, sticky="w", padx=5, pady=5)

        # Estado del caché
        ttk.Label(cache_frame, text="Tamaño actual:").grid(row=1, column=0, sticky="w", padx=5, pady=5)

        self.cache_size_var = ttk.StringVar(value="Calculando...")
        ttk.Label(cache_frame, textvariable=self.cache_size_var).grid(row=1, column=1, sticky="w", padx=5, pady=5)

        # Botones
        btn_frame = ttk.Frame(cache_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        ttk.Button(
            btn_frame,
            text="Calcular tamaño",
            command=self.calculate_cache_size
        ).grid(row=0, column=0, padx=5, pady=5)

        ttk.Button(
            btn_frame,
            text="Limpiar caché",
            command=self.clean_cache,
            style="Accent.TButton"
        ).grid(row=0, column=1, padx=5, pady=5)

        # Ejecutar cálculo inicial en segundo plano
        threading.Thread(target=self.calculate_cache_size, daemon=True).start()

    def setup_ncdu_panel(self):
        """Configura el panel de NCDU (navegador de uso de disco)."""
        ncdu_frame = ttk.Labelframe(self.frame, text="Explorador de uso de disco (NCDU)", padding=10)
        ncdu_frame.pack(fill="x", pady=10)

        # Remoto a analizar
        ttk.Label(ncdu_frame, text="Remoto a analizar:").grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self.ncdu_remote_var = ttk.StringVar()
        self.ncdu_remote_combo = ttk.Combobox(ncdu_frame, textvariable=self.ncdu_remote_var, state="readonly")
        self.ncdu_remote_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Actualizar valores desde la pestaña de configuración
        if "config" in self.app.tabs:
            remotes = self.app.tabs["config"].remotes_list.get(0, "end")
            if remotes:
                self.ncdu_remote_combo["values"] = remotes
                if not self.ncdu_remote_var.get() and remotes:
                    self.ncdu_remote_var.set(remotes[0])

        # Botón para analizar
        ttk.Button(
            ncdu_frame,
            text="Analizar espacio",
            command=self.run_ncdu,
            style="Accent.TButton"
        ).grid(row=1, column=1, padx=5, pady=5)

        # Descripción
        ttk.Label(
            ncdu_frame,
            text="NCDU permite explorar visualmente el uso de espacio en un remoto.",
            font=("", 9),
            foreground="gray"
        ).grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=5)

    def update_remotes(self, remotes):
        """
        Actualiza la lista de remotos disponibles.

        Args:
            remotes (list): Lista de nombres de remotos.
        """
        self.ncdu_remote_combo["values"] = remotes

        # Seleccionar el primer remoto si no hay ninguno seleccionado
        if remotes and not self.ncdu_remote_var.get():
            self.ncdu_remote_var.set(remotes[0])

    def check_files(self):
        """Verifica la integridad de los archivos."""
        # Obtener ruta a verificar
        path = self.check_path_var.get()

        if not path:
            Messagebox.show_error(
                title="Error",
                message="Selecciona una ruta para verificar."
            )
            return

        # Verificar que la ruta existe
        if not os.path.exists(path):
            Messagebox.show_error(
                title="Error",
                message=f"La ruta no existe: {path}"
            )
            return

        # Crear ventana para mostrar resultados
        self._create_check_window(path)

    def _create_check_window(self, path):
        """
        Crea una ventana para mostrar resultados de verificación.

        Args:
            path (str): Ruta a verificar.
        """
        # Crear ventana
        check_window = ttk.Toplevel(self.app.root)
        check_window.title(f"Verificación de archivos: {os.path.basename(path)}")
        check_window.geometry("600x400")
        check_window.grab_set()  # Modal

        # Panel de información
        info_frame = ttk.Frame(check_window, padding=10)
        info_frame.pack(fill="x")

        ttk.Label(
            info_frame,
            text="Verificando integridad de archivos en:",
            font=("", 10, "bold")
        ).pack(side=TOP, anchor="w")

        ttk.Label(
            info_frame,
            text=path
        ).pack(side=TOP, anchor="w", pady=(0, 10))

        # Barra de progreso
        progress_frame = ttk.Frame(check_window, padding=(10, 0))
        progress_frame.pack(fill="x")

        self.check_status_var = ttk.StringVar(value="Iniciando verificación...")
        ttk.Label(
            progress_frame,
            textvariable=self.check_status_var
        ).pack(side=TOP, anchor="w", pady=(0, 5))

        self.check_progress = ttk.Progressbar(progress_frame, mode="indeterminate")
        self.check_progress.pack(fill="x", pady=(0, 10))
        self.check_progress.start()

        # Área de resultados
        result_frame = ttk.Frame(check_window)
        result_frame.pack(expand=True, fill="both", padx=10, pady=5)

        self.check_result_text = tk.Text(result_frame, wrap="word")
        self.check_result_text.pack(side=LEFT, expand=True, fill="both")

        scrollbar = ttk.Scrollbar(result_frame, command=self.check_result_text.yview)
        scrollbar.pack(side=RIGHT, fill="y")
        self.check_result_text.config(yscrollcommand=scrollbar.set)

        # Botones
        btn_frame = ttk.Frame(check_window, padding=10)
        btn_frame.pack(fill="x")

        self.check_close_btn = ttk.Button(
            btn_frame,
            text="Cancelar",
            command=check_window.destroy
        )
        self.check_close_btn.pack(side=RIGHT, padx=5)

        # Iniciar verificación
        self._run_check(path, check_window)

    def _run_check(self, path, check_window):
        """
        Ejecuta la verificación de archivos.

        Args:
            path (str): Ruta a verificar.
            check_window (ttk.Toplevel): Ventana de resultados.
        """

        def check_task():
            try:
                # Ejecutar verificación
                result = self.rclone_runner.check_files(path)

                # Actualizar interfaz desde el hilo principal
                if result.get('success', False):
                    message = "Verificación completada sin errores. Todos los archivos están en buen estado." if not result.get(
                        'stdout', '').strip() else result.get('stdout', '')
                    self.app.root.after(0, lambda: self._update_check_result(message, True, check_window))
                else:
                    self.app.root.after(0, lambda: self._update_check_result(result.get('error', 'Error desconocido'),
                                                                             False, check_window))
            except Exception as e:
                self.app.root.after(0, lambda: self._update_check_result(str(e), False, check_window))

        # Ejecutar en un hilo separado
        threading.Thread(target=check_task, daemon=True).start()

    def _update_check_result(self, message, success, check_window):
        """
        Actualiza el resultado de la verificación.

        Args:
            message (str): Mensaje de resultado.
            success (bool): Si la verificación fue exitosa.
            check_window (ttk.Toplevel): Ventana de resultados.
        """
        if not check_window.winfo_exists():
            return

        # Detener progreso
        self.check_progress.stop()

        # Cambiar a determinado
        self.check_progress["mode"] = "determinate"
        self.check_progress["value"] = 100 if success else 0

        # Actualizar estado
        self.check_status_var.set("Verificación completada" if success else "Error en la verificación")

        # Mostrar resultado
        self.check_result_text.delete("1.0", "end")
        if success:
            self.check_result_text.insert("end", "✅ " if "sin errores" in message else "")
        else:
            self.check_result_text.insert("end", "❌ ")

        self.check_result_text.insert("end", message)

        # Cambiar botón
        self.check_close_btn.config(text="Cerrar")

    def calculate_cache_size(self):
        """Calcula el tamaño del directorio de caché."""

        def task():
            try:
                cache_dir = self.cache_dir_var.get()

                # Verificar si el directorio existe
                if not os.path.exists(cache_dir):
                    self.app.root.after(0, lambda: self.cache_size_var.set("El directorio no existe"))
                    return

                # Calcular tamaño
                self.app.root.after(0, lambda: self.cache_size_var.set("Calculando..."))

                size = calculate_directory_size(cache_dir)
                formatted_size = format_size(size)

                self.app.root.after(0, lambda: self.cache_size_var.set(formatted_size))
            except Exception as e:
                self.app.root.after(0, lambda: self.cache_size_var.set(f"Error: {str(e)}"))

        # Ejecutar en un hilo separado
        threading.Thread(target=task, daemon=True).start()

    def clean_cache(self):
        """Limpia el directorio de caché."""
        cache_dir = self.cache_dir_var.get()

        # Verificar si el directorio existe
        if not os.path.exists(cache_dir):
            Messagebox.show_warning(
                title="Aviso",
                message="El directorio de caché no existe."
            )
            return

        # Confirmar limpieza
        if not Messagebox.yesno(
                title="Confirmar limpieza",
                message=f"¿Estás seguro de limpiar la caché de rclone en:\n\n{cache_dir}?\n\n"
                        f"Esto eliminará todos los archivos en caché y podría ralentizar"
                        f" las próximas operaciones de montaje."
        ):
            return

        # Limpiar caché
        def task():
            try:
                self.app.root.after(0, lambda: self.app.status_var.set("Limpiando caché..."))

                # Limpiar caché usando rclone
                result = self.rclone_runner.clean_cache(cache_dir)

                # Actualizar interfaz desde el hilo principal
                if result.get('success', False):
                    self.app.root.after(0, lambda: self.app.status_var.set("Caché limpiada correctamente"))
                    self.app.root.after(0, lambda: Messagebox.show_info(
                        title="Caché limpiada",
                        message="El directorio de caché se ha limpiado correctamente."
                    ))

                    # Actualizar tamaño
                    self.app.root.after(100, self.calculate_cache_size)
                else:
                    self.app.root.after(0, lambda: self.app.status_var.set("Error al limpiar caché"))
                    self.app.root.after(0, lambda: Messagebox.show_error(
                        title="Error",
                        message=f"No se pudo limpiar el caché:\n{result.get('error', 'Error desconocido')}"
                    ))
            except Exception as e:
                self.app.root.after(0, lambda: self.app.status_var.set("Error al limpiar caché"))
                self.app.root.after(0, lambda: Messagebox.show_error(
                    title="Error",
                    message=f"Error al limpiar caché:\n{str(e)}"
                ))

        # Ejecutar en un hilo separado
        threading.Thread(target=task, daemon=True).start()

    def run_ncdu(self):
        """Ejecuta NCDU para analizar espacio en un remoto."""
        remote = self.ncdu_remote_var.get()

        if not remote:
            Messagebox.show_error(
                title="Error",
                message="Selecciona un remoto para analizar."
            )
            return

        # Ejecutar NCDU
        try:
            result = self.rclone_runner.run_ncdu(f"{remote}:")

            if "process_id" in result:
                self.app.status_var.set(f"Analizando espacio en {remote}...")
            else:
                Messagebox.show_error(
                    title="Error",
                    message=f"No se pudo iniciar NCDU:\n{result.get('error', 'Error desconocido')}"
                )
        except Exception as e:
            Messagebox.show_error(
                title="Error",
                message=f"Error al iniciar NCDU:\n{str(e)}"
            )