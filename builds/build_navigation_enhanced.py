import os
import sys
import shutil
import PyInstaller.__main__
from pathlib import Path

def build_executable():
    """Construir el ejecutable usando PyInstaller."""
    try:
        # Limpiar directorios anteriores
        dirs_to_clean = ['build', 'dist']
        files_to_clean = ['NavigationController.spec']
        
        for dir_name in dirs_to_clean:
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name)
                
        for file_name in files_to_clean:
            if os.path.exists(file_name):
                os.remove(file_name)
        
        # Configurar opciones de PyInstaller
        options = [
            'navigation_controller_enhanced.py',  # Script principal
            '--name=NavigationControllerEnhanced',  # Nombre del ejecutable
            '--onedir',                            # Crear un directorio con el ejecutable
            '--windowed',                          # Sin consola
            '--noconfirm',                         # No confirmar sobrescritura
            '--clean',                             # Limpiar caché
            '--log-level=ERROR',                   # Nivel de log
            # Icono personalizado (si existe)
            '--icon=assets/icons/navigation_controller.ico' if os.path.exists('assets/icons/navigation_controller.ico') else None,
            # Ocultar imports
            '--hidden-import=mediapipe',
            '--hidden-import=cv2',
            '--hidden-import=numpy',
            '--hidden-import=pyautogui',
            '--hidden-import=win32api',
            '--hidden-import=win32con',
        ]
        
        # Filtrar opciones None
        options = [opt for opt in options if opt is not None]
        
        # Ejecutar PyInstaller
        PyInstaller.__main__.run(options)
        
        print("\nConstrucción completada con éxito!")
        print("\nEl ejecutable se encuentra en: dist/NavigationControllerEnhanced/NavigationControllerEnhanced.exe")
        return True
        
    except Exception as e:
        print(f"\nError durante la construcción: {str(e)}")
        return False

def main():
    """Función principal."""
    try:
        # Verificar Python 3.8+
        if sys.version_info < (3, 8):
            print("Error: Se requiere Python 3.8 o superior")
            sys.exit(1)
            
        # Verificar existencia de requirements.txt
        if not os.path.exists('requirements.txt'):
            print("Error: No se encontró el archivo requirements.txt")
            sys.exit(1)
            
        # Construir el ejecutable
        if not build_executable():
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nProceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\nError inesperado: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 