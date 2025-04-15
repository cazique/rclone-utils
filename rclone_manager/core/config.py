"""
Módulo de gestión de configuración para RcloneManager.

Este módulo maneja la carga y guardado de la configuración de la aplicación,
asegurando que las preferencias del usuario persistan entre sesiones.
"""
import os
import json
from pathlib import Path


class ConfigManager:
    """Gestiona la configuración de la aplicación."""

    def __init__(self, config_file=None):
        """
        Inicializa el gestor de configuración.

        Args:
            config_file (str, opcional): Ruta al archivo de configuración.
                Si no se proporciona, se usa la ubicación predeterminada.
        """
        if not config_file:
            # Usar la ubicación estándar en el directorio del usuario
            self.config_file = os.path.join(
                os.path.expanduser("~"),
                ".rclonemanager.json"
            )
        else:
            self.config_file = config_file

        # Configuración predeterminada
        self.default_config = {
            "rclone_path": "",
            "last_mount": {},
            "last_transfer": {},
            "cache_mode": "writes",
            "theme": "flatly"
        }

    def load_config(self):
        """
        Carga la configuración desde el archivo.

        Returns:
            dict: La configuración cargada, o la configuración predeterminada
                 si no se puede cargar.
        """
        config = self.default_config.copy()

        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    saved_config = json.load(f)
                    config.update(saved_config)

                    # Verificar que la ruta de rclone existe
                    if "rclone_path" in saved_config:
                        if not os.path.exists(saved_config["rclone_path"]):
                            # La ruta guardada ya no existe
                            config["rclone_path"] = ""
        except Exception as e:
            # Si hay un error, simplemente usar la configuración predeterminada
            print(f"Error al cargar la configuración: {e}")

        return config

    def save_config(self, config):
        """
        Guarda la configuración en el archivo.

        Args:
            config (dict): La configuración a guardar.

        Returns:
            bool: True si se guardó correctamente, False en caso contrario.
        """
        try:
            # Asegurar que el directorio existe
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error al guardar la configuración: {e}")
            return False