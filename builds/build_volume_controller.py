#!/usr/bin/env python3
"""
Script para construir el ejecutable de Volume Controller usando PyInstaller
Específicamente diseñado para Windows
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_volume_controller():
    """Construye el ejecutable del Volume Controller"""
    
    print("🚀 Iniciando construcción del ejecutable Volume Controller...")
    
    # Verificar que estamos en Windows
    if sys.platform != "win32":
        print("❌ Este script está diseñado específicamente para Windows")
        return False
    
    # Obtener rutas del proyecto
    project_root = Path(__file__).parent
    models_dir = project_root / "models"
    controller_file = project_root / "core" / "controllers" / "volume_controller.py"
    
    # Verificar archivos necesarios
    if not controller_file.exists():
        print(f"❌ No se encontró el archivo: {controller_file}")
        return False
    
    if not models_dir.exists():
        print(f"❌ No se encontró el directorio de modelos: {models_dir}")
        return False
    
    gesture_model = models_dir / "gesture_recognizer.task"
    if not gesture_model.exists():
        print(f"❌ No se encontró el modelo: {gesture_model}")
        return False
    
    print("✅ Archivos verificados correctamente")
    
    # Limpiar construcciones anteriores
    build_dir = project_root / "build"
    dist_dir = project_root / "dist"
    
    if build_dir.exists():
        print("🧹 Limpiando directorio build...")
        shutil.rmtree(build_dir)
    
    if dist_dir.exists():
        print("🧹 Limpiando directorio dist...")
        shutil.rmtree(dist_dir)
    
    # Comando PyInstaller
    pyinstaller_cmd = [
        "pyinstaller",
        "--onefile",                                    # Un solo archivo ejecutable
        "--windowed",                                   # Sin ventana de consola
        "--name=VolumeController",                      # Nombre del ejecutable
        "--icon=NONE",                                  # Sin icono por ahora
        f"--add-data={gesture_model};models",           # Incluir modelo
        "--hidden-import=cv2",                          # Importaciones ocultas
        "--hidden-import=mediapipe",
        "--hidden-import=numpy",
        "--hidden-import=pyautogui",
        "--hidden-import=mediapipe.tasks",
        "--hidden-import=mediapipe.tasks.python",
        "--hidden-import=mediapipe.tasks.python.vision",
        "--hidden-import=mediapipe.python.solutions",
        "--hidden-import=mediapipe.python.solutions.drawing_utils",
        "--hidden-import=mediapipe.python.solutions.drawing_styles",
        "--hidden-import=matplotlib",
        "--hidden-import=matplotlib.pyplot",
        "--collect-all=mediapipe",                      # Recopilar todos los archivos de mediapipe
        "--collect-all=cv2",                            # Recopilar todos los archivos de opencv
        "--collect-all=matplotlib",                     # Recopilar todos los archivos de matplotlib
        "--exclude-module=tkinter",                     # Excluir módulos innecesarios
        "--exclude-module=PIL.ImageTk",
        "--distpath=dist",                              # Directorio de salida
        "--workpath=build",                             # Directorio de trabajo
        "--clean",                                      # Limpiar cache
        str(controller_file)                            # Archivo principal
    ]
    
    print("🔨 Ejecutando PyInstaller...")
    print(f"Comando: {' '.join(pyinstaller_cmd)}")
    
    try:
        # Ejecutar PyInstaller
        result = subprocess.run(pyinstaller_cmd, 
                              cwd=project_root, 
                              capture_output=True, 
                              text=True)
        
        if result.returncode == 0:
            print("✅ Construcción exitosa!")
            
            # Verificar que el ejecutable se creó
            exe_path = dist_dir / "VolumeController.exe"
            if exe_path.exists():
                print(f"📦 Ejecutable creado en: {exe_path}")
                print(f"📏 Tamaño del archivo: {exe_path.stat().st_size / (1024*1024):.1f} MB")
                
                # Crear directorio de distribución
                release_dir = project_root / "release"
                release_dir.mkdir(exist_ok=True)
                
                # Copiar ejecutable a release
                release_exe = release_dir / "VolumeController.exe"
                shutil.copy2(exe_path, release_exe)
                
                print(f"📁 Ejecutable copiado a: {release_exe}")
                print("\n🎉 ¡Construcción completada exitosamente!")
                print("\n📋 Instrucciones de uso:")
                print("1. Ejecuta VolumeController.exe")
                print("2. Permite el acceso a la cámara cuando se solicite")
                print("3. Usa estos gestos para controlar el volumen:")
                print("   👍 Pulgar arriba: Subir volumen")
                print("   👎 Pulgar abajo: Bajar volumen")
                print("   ✊ Puño cerrado: Silenciar/Activar")
                print("4. Presiona ESC para salir")
                
                return True
            else:
                print("❌ El ejecutable no se creó correctamente")
                return False
        else:
            print("❌ Error durante la construcción:")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando PyInstaller: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def check_dependencies():
    """Verifica que las dependencias necesarias estén instaladas"""
    print("🔍 Verificando dependencias...")
    
    # Mapeo de nombres de paquetes a nombres de módulos
    package_module_map = {
        "pyinstaller": "PyInstaller",
        "opencv-python": "cv2", 
        "mediapipe": "mediapipe",
        "numpy": "numpy",
        "pyautogui": "pyautogui",
        "matplotlib": "matplotlib"
    }
    
    missing_packages = []
    
    for package, module in package_module_map.items():
        try:
            __import__(module)
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n⚠️  Faltan las siguientes dependencias:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n💡 Instálalas con:")
        print(f"python -m pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ Todas las dependencias están instaladas")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🎯 CONSTRUCTOR DE EJECUTABLE - VOLUME CONTROLLER")
    print("=" * 60)
    
    # Verificar dependencias
    if not check_dependencies():
        sys.exit(1)
    
    # Construir ejecutable
    if build_volume_controller():
        print("\n🎊 ¡Proceso completado exitosamente!")
        sys.exit(0)
    else:
        print("\n💥 Proceso falló")
        sys.exit(1) 