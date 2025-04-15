"""
Operaciones con Rclone para RcloneManager.

Este módulo abstrae las operaciones de Rclone como listar remotos,
verificar la versión, ejecutar comandos, etc.
"""
import os
import subprocess
import json
import threading
import time
import platform
from datetime import datetime

class RcloneRunner:
    """Clase para ejecutar operaciones de Rclone."""

    def __init__(self, rclone_path=""):
        """
        Inicializa el ejecutor de Rclone.

        Args:
            rclone_path (str): Ruta al ejecutable de rclone.
        """
        self.rclone_path = rclone_path
        self._running_processes = {}

    def set_rclone_path(self, path):
        """
        Actualiza la ruta al ejecutable de rclone.

        Args:
            path (str): Nueva ruta al ejecutable.
        """
        self.rclone_path = path

    def get_version(self):
        """
        Obtiene la versión de rclone.

        Returns:
            str: La versión de rclone, o mensaje de error si falla.
        """
        try:
            result = self._run_command(["version"], timeout=5)
            if result['success']:
                # Extraer la primera línea que contiene la versión
                return result['stdout'].splitlines()[0]
            return f"Error: {result['error']}"
        except Exception as e:
            return f"Error: {str(e)}"

    def list_remotes(self):
        """
        Lista los remotos configurados.

        Returns:
            list: Lista de nombres de remotos, o lista vacía si hay error.
        """
        try:
            result = self._run_command(["listremotes"], timeout=10)
            if result['success'] and result['stdout']:
                # Limpiar los nombres (quitar los : al final)
                return [r.strip(':') for r in result['stdout'].splitlines() if r.strip()]
            return []
        except Exception:
            return []

    def get_remote_details(self, remote_name):
        """
        Obtiene los detalles de un remoto.

        Args:
            remote_name (str): Nombre del remoto.

        Returns:
            str: Detalles del remoto, o mensaje de error.
        """
        try:
            result = self._run_command(["config", "show", remote_name], timeout=10)
            if result['success']:
                return result['stdout'] or f"No se encontraron detalles para {remote_name}"
            return f"Error: {result['error']}"
        except Exception as e:
            return f"Error: {str(e)}"

    def create_remote(self, remote_name, remote_type, config_params=None):
        """
        Crea un nuevo remoto (sin implementar completamente).

        Args:
            remote_name (str): Nombre del nuevo remoto.
            remote_type (str): Tipo de remoto (drive, sftp, etc).
            config_params (dict): Parámetros de configuración.

        Returns:
            dict: Resultado de la operación.

        Note:
            Esta función no está completamente implementada porque la creación
            de remotos generalmente requiere interacción del usuario para autenticación.
        """
        # Este es un placeholder. La creación de remotos generalmente requiere
        # interacción del usuario para autenticación, lo que es difícil de automatizar.
        return {
            'success': False,
            'error': "Función no implementada completamente. Use 'rclone config' manualmente."
        }

    def delete_remote(self, remote_name):
        """
        Elimina un remoto.

        Args:
            remote_name (str): Nombre del remoto a eliminar.

        Returns:
            dict: Resultado de la operación.
        """
        try:
            result = self._run_command(["config", "delete", remote_name], timeout=10)
            return {
                'success': result['success'],
                'error': result['error'] if not result['success'] else ""
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def mount(self, remote_path, mount_point, options=None):
        """
        Monta un remoto en un punto de montaje.

        Args:
            remote_path (str): Ruta del remoto (ej: "gdrive:").
            mount_point (str): Punto de montaje local.
            options (dict): Opciones de montaje.

        Returns:
            dict: Información del proceso de montaje.
        """
        if not options:
            options = {}

        # Construir comando base
        cmd = ["mount", remote_path, mount_point]

        # Añadir opciones
        for key, value in options.items():
            if value is True:
                cmd.append(f"--{key}")
            elif value is not False and value is not None:
                cmd.append(f"--{key}")
                cmd.append(str(value))

        # Generar ID único para este proceso
        process_id = f"mount_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Iniciar proceso en un hilo separado
        thread = threading.Thread(
            target=self._run_long_process,
            args=(cmd, process_id),
            daemon=True
        )
        thread.start()

        # Dar tiempo para que inicie el proceso
        time.sleep(1)

        return {
            'process_id': process_id,
            'command': [self.rclone_path] + cmd,
            'status': "iniciado"
        }

    def unmount(self, mount_point, process_id=None):
        """
        Desmonta un punto de montaje.

        Args:
            mount_point (str): Punto de montaje a desmontar.
            process_id (str, opcional): ID del proceso de montaje.

        Returns:
            dict: Resultado de la operación.
        """
        # Si tenemos el ID del proceso, intentar terminarlo
        if process_id and process_id in self._running_processes:
            process = self._running_processes[process_id]
            try:
                process.terminate()
                del self._running_processes[process_id]
                return {
                    'success': True,
                    'message': f"Proceso de montaje terminado: {process_id}"
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Error al terminar proceso: {str(e)}"
                }

        # Si no tenemos el proceso o falló lo anterior, intentar desmontar usando el sistema
        try:
            if platform.system() == "Windows":
                # En Windows podemos intentar usar el comando 'net use'
                drive_letter = mount_point.rstrip("\\:")
                if len(drive_letter) == 1:  # Es una letra de unidad
                    result = subprocess.run(
                        ["net", "use", f"{drive_letter}:", "/delete", "/y"],
                        capture_output=True,
                        text=True
                    )
                    return {
                        'success': result.returncode == 0,
                        'error': result.stderr if result.returncode != 0 else ""
                    }
            else:
                # En Linux/Mac podemos usar fusermount
                unmount_cmd = ["fusermount", "-u", mount_point]
                result = subprocess.run(
                    unmount_cmd,
                    capture_output=True,
                    text=True
                )
                return {
                    'success': result.returncode == 0,
                    'error': result.stderr if result.returncode != 0 else ""
                }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error al desmontar: {str(e)}"
            }

        return {
            'success': False,
            'error': "No se pudo desmontar el punto de montaje"
        }

    def transfer(self, source, destination, method="copy", options=None, callback=None):
        """
        Transfiere archivos entre origen y destino.

        Args:
            source (str): Ruta de origen.
            destination (str): Ruta de destino.
            method (str): Método de transferencia ('copy', 'move', 'sync').
            options (dict): Opciones adicionales.
            callback (callable): Función para recibir actualizaciones de progreso.

        Returns:
            dict: Información del proceso de transferencia.
        """
        if method not in ["copy", "move", "sync"]:
            return {
                'success': False,
                'error': f"Método no válido: {method}"
            }

        if not options:
            options = {}

        # Construir comando base
        cmd = [method, source, destination]

        # Añadir opciones
        for key, value in options.items():
            if value is True:
                cmd.append(f"--{key}")
            elif value is not False and value is not None:
                cmd.append(f"--{key}")
                cmd.append(str(value))

        # Siempre mostrar progreso
        if "--progress" not in cmd and "-P" not in cmd:
            cmd.append("--progress")

        # Generar ID único para este proceso
        process_id = f"transfer_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Iniciar proceso en un hilo separado
        thread = threading.Thread(
            target=self._run_process_with_output,
            args=(cmd, process_id, callback),
            daemon=True
        )
        thread.start()

        return {
            'process_id': process_id,
            'command': [self.rclone_path] + cmd,
            'status': "iniciado"
        }

    def cancel_transfer(self, process_id):
        """
        Cancela una transferencia en curso.

        Args:
            process_id (str): ID del proceso a cancelar.

        Returns:
            dict: Resultado de la operación.
        """
        if process_id in self._running_processes:
            process = self._running_processes[process_id]
            try:
                process.terminate()
                del self._running_processes[process_id]
                return {
                    'success': True,
                    'message': f"Proceso cancelado: {process_id}"
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Error al cancelar proceso: {str(e)}"
                }

        return {
            'success': False,
            'error': f"No se encontró el proceso: {process_id}"
        }

    def check_files(self, path, options=None):
        """
        Verifica la integridad de los archivos.

        Args:
            path (str): Ruta a verificar.
            options (dict): Opciones adicionales.

        Returns:
            dict: Resultado de la verificación.
        """
        if not options:
            options = {}

        cmd = ["check", path, path]  # Comprobar contra sí mismo

        # Añadir opciones
        for key, value in options.items():
            if value is True:
                cmd.append(f"--{key}")
            elif value is not False and value is not None:
                cmd.append(f"--{key}")
                cmd.append(str(value))

        return self._run_command(cmd, timeout=None)

    def clean_cache(self, cache_dir):
        """
        Limpia el directorio de caché.

        Args:
            cache_dir (str): Directorio de caché a limpiar.

        Returns:
            dict: Resultado de la operación.
        """
        if not os.path.exists(cache_dir):
            return {
                'success': False,
                'error': f"El directorio no existe: {cache_dir}"
            }

        # Primero intentar con rclone
        try:
            result = self._run_command(["rc", "vfs/forget"], timeout=10)
            if result['success']:
                return {
                    'success': True,
                    'message': "Caché limpiada a través de rclone RC"
                }
        except:
            pass  # Ignorar errores y continuar con el método manual

        # Método manual: eliminar archivos del directorio
        try:
            files_removed = 0
            dirs_removed = 0

            for root, dirs, files in os.walk(cache_dir, topdown=False):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        os.unlink(file_path)
                        files_removed += 1
                    except:
                        pass

                for dir_name in dirs:
                    try:
                        dir_path = os.path.join(root, dir_name)
                        os.rmdir(dir_path)
                        dirs_removed += 1
                    except:
                        pass

            return {
                'success': True,
                'message': f"Caché limpiada manualmente: {files_removed} archivos y {dirs_removed} directorios eliminados"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error al limpiar caché manualmente: {str(e)}"
            }

    def run_ncdu(self, remote_path):
        """
        Ejecuta NCDU en una ruta remota.

        Args:
            remote_path (str): Ruta remota a analizar.

        Returns:
            dict: Información del proceso.
        """
        cmd = ["ncdu", remote_path]

        # Generar ID único para este proceso
        process_id = f"ncdu_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        try:
            process = subprocess.Popen([self.rclone_path] + cmd)
            self._running_processes[process_id] = process

            return {
                'process_id': process_id,
                'command': [self.rclone_path] + cmd,
                'status': "iniciado"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error al iniciar NCDU: {str(e)}"
            }

    def _run_command(self, args, timeout=None):
        """
        Ejecuta un comando de rclone y devuelve el resultado.

        Args:
            args (list): Argumentos del comando.
            timeout (int, opcional): Tiempo máximo de espera en segundos.

        Returns:
            dict: Resultado del comando.
        """
        if not self.rclone_path:
            return {
                'success': False,
                'error': "Ruta de rclone no configurada",
                'stdout': "",
                'stderr': ""
            }

        cmd = [self.rclone_path] + args

        try:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            return {
                'success': process.returncode == 0,
                'error': process.stderr if process.returncode != 0 else "",
                'stdout': process.stdout,
                'stderr': process.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f"Tiempo de espera agotado ({timeout}s)",
                'stdout': "",
                'stderr': ""
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stdout': "",
                'stderr': ""
            }

    def _run_long_process(self, args, process_id):
        """
        Ejecuta un proceso de larga duración.

        Args:
            args (list): Argumentos del comando.
            process_id (str): ID único para este proceso.
        """
        if not self.rclone_path:
            return

        cmd = [self.rclone_path] + args

        try:
            process = subprocess.Popen(cmd)
            self._running_processes[process_id] = process

            # Esperar a que termine
            process.wait()

            # Eliminar del diccionario cuando termine
            if process_id in self._running_processes:
                del self._running_processes[process_id]
        except Exception:
            # En caso de error, asegurar que se elimina del diccionario
            if process_id in self._running_processes:
                del self._running_processes[process_id]

    def _run_process_with_output(self, args, process_id, callback=None):
        """
        Ejecuta un proceso y captura su salida.

        Args:
            args (list): Argumentos del comando.
            process_id (str): ID único para este proceso.
            callback (callable, opcional): Función a llamar con cada línea de salida.
        """
        if not self.rclone_path:
            return

        cmd = [self.rclone_path] + args

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            self._running_processes[process_id] = process

            # Leer la salida
            for line in iter(process.stdout.readline, ''):
                if callback:
                    callback(line)

            # Esperar a que termine
            process.wait()

            # Llamar al callback con el código de retorno
            if callback:
                callback(f"__RETURN_CODE:{process.returncode}__")

            # Eliminar del diccionario cuando termine
            if process_id in self._running_processes:
                del self._running_processes[process_id]
        except Exception as e:
            # En caso de error, informar al callback
            if callback:
                callback(f"__ERROR:{str(e)}__")

            # Asegurar que se elimina del diccionario
            if process_id in self._running_processes:
                del self._running_processes[process_id]
