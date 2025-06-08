import os
import sys
import shutil
import PyInstaller.__main__
from pathlib import Path

def copy_model_file():
    """Copiar el archivo del modelo a la carpeta de destino."""
    try:
        # Rutas posibles del modelo
        possible_model_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models', 'gesture_recognizer.task'),
            os.path.join(os.getcwd(), 'models', 'gesture_recognizer.task'),
            'models/gesture_recognizer.task',
            'gesture_recognizer.task'
        ]
        
        # Encontrar el modelo
        model_path = None
        for path in possible_model_paths:
            if os.path.exists(path):
                model_path = path
                break
        
        if model_path is None:
            print("Error: No se encontró el archivo del modelo gesture_recognizer.task")
            return False
            
        # Crear directorio models en dist si no existe
        dist_models_dir = os.path.join('dist', 'AppControllerEnhanced', 'models')
        os.makedirs(dist_models_dir, exist_ok=True)
        
        # Copiar el modelo
        shutil.copy2(model_path, os.path.join(dist_models_dir, 'gesture_recognizer.task'))
        return True
        
    except Exception as e:
        print(f"Error al copiar el modelo: {str(e)}")
        return False

def build_executable():
    """Construir el ejecutable usando PyInstaller."""
    try:
        # Limpiar directorios anteriores
        dirs_to_clean = ['build', 'dist']
        files_to_clean = ['AppController.spec']
        
        for dir_name in dirs_to_clean:
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name)
                
        for file_name in files_to_clean:
            if os.path.exists(file_name):
                os.remove(file_name)
        
        # Configurar opciones de PyInstaller
        options = [
            'app_controller_enhanced.py',  # Script principal
            '--name=AppControllerEnhanced',       # Nombre del ejecutable
            '--onedir',                              # Crear un directorio con el ejecutable
            '--windowed',                            # Sin consola
            '--noconfirm',                           # No confirmar sobrescritura
            '--clean',                               # Limpiar caché
            '--log-level=ERROR',                     # Nivel de log
            # Rutas de datos adicionales
            '--add-data=models/gesture_recognizer.task;models',
            # Icono personalizado (si existe)
            '--icon=assets/icons/app_controller.ico' if os.path.exists('assets/icons/app_controller.ico') else None,
            # Ocultar imports
            '--hidden-import=mediapipe',
            '--hidden-import=cv2',
            '--hidden-import=numpy',
            '--hidden-import=psutil',
            '--hidden-import=subprocess',
            '--hidden-import=threading',
            '--hidden-import=win32api',
            '--hidden-import=win32con',
        ]
        
        # Filtrar opciones None
        options = [opt for opt in options if opt is not None]
        
        # Ejecutar PyInstaller
        PyInstaller.__main__.run(options)
        
        # Copiar el modelo después de la construcción
        if not copy_model_file():
            return False
            
        print("\nConstrucción completada con éxito!")
        print("\nEl ejecutable se encuentra en: dist/AppControllerEnhanced/AppControllerEnhanced.exe")
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