#!/usr/bin/env python3
"""
Script para compilar el Mouse Controller Enhanced con todas las dependencias necesarias.
"""

import os
import sys
import subprocess
import importlib
import shutil
from pathlib import Path

def check_dependencies():
    """Verificar que todas las dependencias estén instaladas."""
    required_packages = [
        'cv2', 'mediapipe', 'numpy', 'pyautogui', 
        'autopy', 'pynput', 'PIL', 'PyInstaller'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'cv2':
                import cv2
            elif package == 'PIL':
                import PIL
            else:
                importlib.import_module(package)
            print(f"✓ {package} encontrado")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} NO encontrado")
    
    if missing_packages:
        print(f"\nFaltan los siguientes paquetes: {', '.join(missing_packages)}")
        print("Instálalos con: pip install -r requirements.txt")
        return False
    
    print("\n✓ Todas las dependencias están instaladas")
    return True

def clean_build_directories():
    """Limpiar directorios de construcción anteriores."""
    directories_to_clean = ['build', 'dist', '__pycache__']
    
    for directory in directories_to_clean:
        if os.path.exists(directory):
            shutil.rmtree(directory)
            print(f"✓ Limpiado directorio: {directory}")

def build_executable():
    """Compilar el ejecutable usando PyInstaller."""
    try:
        # Comando de PyInstaller
        cmd = [
            'pyinstaller',
            '--clean',
            '--noconfirm',
            'GestOS Mouse.spec'
        ]
        
        print("Iniciando compilación...")
        print(f"Comando: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("\n✓ Compilación exitosa!")
            
            # Verificar que el ejecutable se creó
            exe_path = Path('dist/GestOS Mouse.exe')
            if exe_path.exists():
                print(f"✓ Ejecutable creado: {exe_path.absolute()}")
                print(f"✓ Tamaño: {exe_path.stat().st_size / (1024*1024):.1f} MB")
                return True
            else:
                print("✗ El ejecutable no se encontró en la carpeta dist/")
                return False
        else:
            print("\n✗ Error en la compilación:")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"✗ Error al ejecutar PyInstaller: {e}")
        return False

def test_executable():
    """Probar que el ejecutable funciona."""
    exe_path = Path('dist/GestOS Mouse.exe')
    
    if not exe_path.exists():
        print("✗ No se puede probar: ejecutable no encontrado")
        return False
    
    print("\nPara probar el ejecutable, ejecuta:")
    print(f'"{exe_path.absolute()}"')
    print("\nNota: El ejecutable se ejecutará en modo debug para mostrar errores.")
    
    return True

def main():
    """Función principal."""
    print("=== Compilador de Mouse Controller Enhanced ===")
    print()
    
    # Verificar dependencias
    if not check_dependencies():
        sys.exit(1)
    
    # Limpiar directorios anteriores
    print("\nLimpiando directorios de construcción...")
    clean_build_directories()
    
    # Compilar
    print("\nCompilando ejecutable...")
    if not build_executable():
        print("\n✗ Error en la compilación. Revisa los mensajes anteriores.")
        sys.exit(1)
    
    # Probar
    print("\nVerificando ejecutable...")
    test_executable()
    
    print("\n=== Compilación completada ===")
    print("El ejecutable está en la carpeta 'dist/'")

if __name__ == "__main__":
    main() 