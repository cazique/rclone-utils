# Rclone Manager

Una interfaz gráfica moderna y fácil de usar para gestionar rclone, la herramienta de sincronización y transferencia de archivos en la nube.

![Rclone Manager Screenshot](screenshot.png)

## Características

- **Interfaz Moderna**: Diseño agradable con temas claros y oscuros gracias a ttkbootstrap
- **Gestión de Configuraciones**: Visualiza, crea y elimina tus configuraciones de rclone
- **Montaje Simplificado**: Monta tus unidades en la nube con opciones optimizadas
- **Transferencias Eficientes**: Copia, mueve y sincroniza archivos con monitoreo en tiempo real
- **Herramientas Útiles**: Verificación de integridad, limpieza de caché y análisis de uso de espacio
- **Multiplataforma**: Funciona en Windows, macOS y Linux

## Requisitos

- Python 3.8 o superior
- rclone instalado en tu sistema ([download rclone](https://rclone.org/downloads/))
- En Windows: WinFSP para montar unidades ([download WinFSP](https://winfsp.dev/rel/))

## Instalación

### Desde PyPI (recomendado)

```bash
pip install rclone-manager
```

### Desde el código fuente

```bash
git clone https://github.com/yourusername/rclone-manager.git
cd rclone-manager
pip install .
```

## Uso

Simplemente ejecuta:

```bash
rclone-manager
```

O desde el código fuente:

```bash
python main.py
```

## Estructura del Proyecto

```
rclone_manager/
├── __init__.py
├── main.py                  # Punto de entrada principal
├── gui/
│   ├── __init__.py
│   ├── app.py               # Clase RcloneManager principal
│   ├── config_tab.py        # Pestaña de configuración
│   ├── mount_tab.py         # Pestaña de montaje
│   ├── transfer_tab.py      # Pestaña de transferencia
│   └── tools_tab.py         # Pestaña de herramientas
└── core/
    ├── __init__.py
    ├── config.py            # Manejo de configuración
    ├── rclone.py            # Operaciones de rclone
    └── system.py            # Utilidades de sistema
```

## Contribuir

Las contribuciones son bienvenidas. Por favor, siente libre de enviar un Pull Request o abrir un Issue para discutir cambios o mejoras.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - vea el archivo LICENSE para más detalles.

## Agradecimientos

- Al equipo de [rclone](https://rclone.org/) por su increíble herramienta
- A [ttkbootstrap](https://ttkbootstrap.readthedocs.io/) por el moderno tema visual
