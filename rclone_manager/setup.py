"""
Script de instalación para Rclone Manager.

Este script permite instalar Rclone Manager como un paquete de Python,
lo que facilita su ejecución desde cualquier ubicación.
"""
from setuptools import setup, find_packages

setup(
    name="rclone-manager",
    version="1.0.0",
    description="Interfaz gráfica para gestionar rclone",
    author="Rclone Manager Team",
    packages=find_packages(),
    install_requires=[
        "ttkbootstrap>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "rclone-manager=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: GUI",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
)
