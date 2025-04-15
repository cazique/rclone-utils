"""
Utilidades del sistema para RcloneManager.

Este módulo contiene funciones relacionadas con el sistema operativo,
como la detección de rutas, verificación de dependencias, etc.
"""
import os
import platform
import subprocess
import shutil
import tempfile
import webbrowser
import tkinter as tk
from tkinter import filedialog
from ttkbootstrap.dialogs import Messagebox


def find_rclone_path():
    """
    Busca la ruta del ejecutable de rclone en ubicaciones comunes.

    Returns:
        str: La ruta al ejecutable de rclone, o una cadena vacía si no se encuentra.
    """
    is_windows = platform.system() == "Windows"

    # Determinar extensión y posibles ubicaciones según el sistema operativo
    if is_windows:
        executable = "rclone.exe"
        common_paths = [
            "C:\\rclone\\rclone.exe",
            "C:\\Program Files\\rclone\\rclone.exe",
            os.path.join(os.path.expanduser("~"), "rclone", "rclone.exe"),
            "rclone.exe"  # Si está en PATH
        ]
    else:
        executable = "rclone"
        common_paths = [
            "/usr/bin/rclone",
            "/usr/local/bin/rclone",
            "/opt/homebrew/bin/rclone",  # Para Mac con Homebrew
            os.path.join(os.path.expanduser("~"), "rclone"),
            "rclone"  # Si está en PATH
        ]

    # Verificar rutas comunes
    for path in common_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path

    # Buscar en PATH
    try:
        if is_windows:
            result = subprocess.run(["where", executable],
                                    capture_output=True, text=True, check=True)
        else:
            result = subprocess.run(["which", executable],
                                    capture_output=True, text=True, check=True)

        if result.returncode == 0:
            # Tomar la primera línea (puede haber múltiples coincidencias)
            path = result.stdout.strip().split('\n')[0]
            if path and os.path.exists(path):
                return path
    except (subprocess.SubprocessError, FileNotFoundError):
        # Error ejecutando where/which, o comando no encontrado
        pass

    # No se encontró automáticamente
    return prompt_for_rclone_path(is_windows)


def prompt_for_rclone_path(is_windows=None):
    """
    Solicita al usuario la ubicación del ejecutable de rclone.

    Args:
        is_windows (bool, opcional): Si el sistema es Windows.
            Si es None, se detecta automáticamente.

    Returns:
        str: La ruta seleccionada, o una cadena vacía si se cancela.
    """
    if is_windows is None:
        is_windows = platform.system() == "Windows"

    executable = "rclone.exe" if is_windows else "rclone"

    Messagebox.show_info(
        title="Rclone no encontrado",
        message=f"No se ha encontrado {executable} automáticamente.\n"
                f"Por favor, selecciona la ubicación del ejecutable."
    )

    # Configurar filtros para el diálogo de archivo
    if is_windows:
        filetypes = [("Ejecutable", "*.exe"), ("Todos los archivos", "*.*")]
    else:
        filetypes = [("Todos los archivos", "*.*")]

    # Mostrar diálogo para seleccionar archivo
    path = filedialog.askopenfilename(
        title=f"Seleccionar {executable}",
        filetypes=filetypes
    )

    return path if path else ""


def check_winfsp_installed():
    """
    Verifica si WinFSP está instalado en sistemas Windows.

    Returns:
        bool: True si está instalado o si no es Windows, False en caso contrario.
    """
    if platform.system() != "Windows":
        return True

    try:
        # Verificar en el registro de Windows
        import winreg
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Services\WinFsp.Launcher"
            )
            winreg.CloseKey(key)
            return True
        except:
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\WOW6432Node\WinFsp"
                )
                winreg.CloseKey(key)
                return True
            except:
                # No se encontró en el registro
                return prompt_winfsp_install()
    except ImportError:
        # winreg no está disponible (no debería ocurrir en Windows)
        return True


def prompt_winfsp_install():
    """
    Pregunta al usuario si desea instalar WinFSP y abre el navegador.

    Returns:
        bool: False siempre, ya que el usuario necesita instalar WinFSP.
    """
    result = Messagebox.show_question(
        "WinFSP no encontrado",
        "Para montar unidades en Windows es necesario instalar WinFSP.\n"
        "¿Deseas descargarlo ahora?",
        buttons=["Descargar", "Cancelar"]
    )

    if result == "Descargar":
        webbrowser.open("https://winfsp.dev/rel/")

    return False


def download_file(url, destination):
    """
    Descarga un archivo desde una URL.

    Args:
        url (str): URL del archivo a descargar.
        destination (str): Ruta donde guardar el archivo.

    Returns:
        bool: True si se descargó correctamente, False en caso contrario.
    """
    try:
        import urllib.request
        urllib.request.urlretrieve(url, destination)
        return True
    except Exception as e:
        print(f"Error descargando {url}: {e}")
        return False


def get_temp_file(prefix="rclonemanager_", suffix=".tmp"):
    """
    Crea un archivo temporal.

    Args:
        prefix (str): Prefijo para el nombre del archivo.
        suffix (str): Sufijo para el nombre del archivo.

    Returns:
        str: Ruta al archivo temporal.
    """
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
    os.close(fd)  # Cerrar el descriptor de archivo
    return path


def get_temp_dir(prefix="rclonemanager_"):
    """
    Crea un directorio temporal.

    Args:
        prefix (str): Prefijo para el nombre del directorio.

    Returns:
        str: Ruta al directorio temporal.
    """
    return tempfile.mkdtemp(prefix=prefix)


def clean_temp_file(path):
    """
    Elimina un archivo temporal.

    Args:
        path (str): Ruta al archivo a eliminar.

    Returns:
        bool: True si se eliminó correctamente, False en caso contrario.
    """
    try:
        if os.path.exists(path):
            os.unlink(path)
        return True
    except Exception as e:
        print(f"Error eliminando archivo temporal {path}: {e}")
        return False


def clean_temp_dir(path):
    """
    Elimina un directorio temporal y su contenido.

    Args:
        path (str): Ruta al directorio a eliminar.

    Returns:
        bool: True si se eliminó correctamente, False en caso contrario.
    """
    try:
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
        return True
    except Exception as e:
        print(f"Error eliminando directorio temporal {path}: {e}")
        return False


def calculate_directory_size(path):
    """
    Calcula el tamaño total de un directorio.

    Args:
        path (str): Ruta al directorio.

    Returns:
        int: Tamaño en bytes, o 0 si hay un error.
    """
    try:
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp) and not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        return total_size
    except Exception:
        return 0


def format_size(size_bytes):
    """
    Formatea un tamaño en bytes a una representación legible.

    Args:
        size_bytes (int): Tamaño en bytes.

    Returns:
        str: Tamaño formateado (ej: "1.23 MB").
    """
    if size_bytes == 0:
        return "0 B"

    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    i = 0
    while size_bytes >= 1024 and i < len(suffixes) - 1:
        size_bytes /= 1024
        i += 1

    return f"{size_bytes:.2f} {suffixes[i]}"