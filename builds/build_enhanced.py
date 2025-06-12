#!/usr/bin/env python3
"""
Script para construir VolumeController_Enhanced.exe
Versión mejorada con interfaz limpia y mejor detección de gestos
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_section(title):
    """Imprimir una sección con formato"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def check_dependencies():
    """Verificar que todas las dependencias estén instaladas"""
    print_section("VERIFICANDO DEPENDENCIAS")
    
    required_packages = [
        'opencv-python',
        'mediapipe', 
        'numpy',
        'pyautogui',
        'pyinstaller'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NO ENCONTRADO")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Paquetes faltantes: {', '.join(missing_packages)}")
        print("Instalando paquetes faltantes...")
        
        for package in missing_packages:
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                             check=True, capture_output=True)
                print(f"✅ {package} instalado")
            except subprocess.CalledProcessError:
                print(f"❌ Error instalando {package}")
                return False
    
    return True

def check_model():
    """Verificar que el modelo esté disponible"""
    print_section("VERIFICANDO MODELO")
    
    model_path = Path("models/gesture_recognizer.task")
    
    if model_path.exists():
        size_mb = model_path.stat().st_size / (1024 * 1024)
        print(f"✅ Modelo encontrado: {model_path}")
        print(f"📁 Tamaño: {size_mb:.1f} MB")
        return True
    else:
        print(f"❌ Modelo no encontrado en: {model_path}")
        print("Descarga el modelo desde MediaPipe y colócalo en la carpeta 'models/'")
        return False

def clean_build():
    """Limpiar archivos de construcción anteriores"""
    print_section("LIMPIANDO ARCHIVOS ANTERIORES")
    
    # Directorios a limpiar
    dirs_to_clean = ['build', 'dist']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"🗑️  Eliminado: {dir_name}/")
    
    # Archivos spec anteriores (mantener solo el enhanced)
    spec_files = ['VolumeController.spec', 'VolumeController_Fixed.spec', 'VolumeController_Debug.spec']
    for spec_file in spec_files:
        if os.path.exists(spec_file):
            os.remove(spec_file)
            print(f"🗑️  Eliminado: {spec_file}")

def build_executable():
    """Construir el ejecutable usando PyInstaller"""
    print_section("CONSTRUYENDO EJECUTABLE")
    
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name=VolumeController_Enhanced',
        '--add-data=models/gesture_recognizer.task;models',
        '--hidden-import=cv2',
        '--hidden-import=mediapipe',
        '--hidden-import=numpy', 
        '--hidden-import=pyautogui',
        '--hidden-import=mediapipe.tasks',
        '--hidden-import=mediapipe.tasks.python',
        '--hidden-import=mediapipe.tasks.python.vision',
        '--exclude-module=tkinter',
        '--exclude-module=PyQt5',
        '--exclude-module=PyQt6', 
        '--exclude-module=matplotlib.backends._backend_tk',
        '--upx-dir=.',
        'volume_controller_enhanced.py'
    ]
    
    try:
        print("🔨 Ejecutando PyInstaller...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Construcción exitosa!")
            return True
        else:
            print("❌ Error durante la construcción:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error ejecutando PyInstaller: {e}")
        return False

def copy_to_release():
    """Copiar el ejecutable a la carpeta release"""
    print_section("PREPARANDO RELEASE")
    
    # Crear carpeta release si no existe
    release_dir = Path("release")
    release_dir.mkdir(exist_ok=True)
    
    # Copiar ejecutable
    source_exe = Path("dist/VolumeController_Enhanced.exe")
    target_exe = release_dir / "VolumeController_Enhanced.exe"
    
    if source_exe.exists():
        shutil.copy2(source_exe, target_exe)
        size_mb = target_exe.stat().st_size / (1024 * 1024)
        print(f"✅ Ejecutable copiado: {target_exe}")
        print(f"📁 Tamaño: {size_mb:.1f} MB")
        
        # Crear archivo de información
        info_file = release_dir / "VolumeController_Enhanced_INFO.txt"
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write("🎯 VOLUME CONTROLLER ENHANCED v2.0\n")
            f.write("========================================\n\n")
            f.write("CARACTERÍSTICAS:\n")
            f.write("✨ Interfaz limpia - solo landmarks visibles\n")
            f.write("🚫 Sin consola - ejecución silenciosa\n")
            f.write("🎯 Detección optimizada basada en la versión funcional\n")
            f.write("🎨 Landmarks coloridos con conexiones mejoradas\n")
            f.write("⚡ Configuración original que garantiza funcionamiento\n\n")
            f.write("GESTOS:\n")
            f.write("👍 Pulgar arriba: Subir volumen\n")
            f.write("👎 Pulgar abajo: Bajar volumen\n")
            f.write("✊ Puño cerrado: Silenciar/Activar\n\n")
            f.write("INSTRUCCIONES:\n")
            f.write("1. Hacer doble clic en VolumeController_Enhanced.exe\n")
            f.write("2. Permitir acceso a la cámara\n")
            f.write("3. Hacer gestos frente a la cámara\n")
            f.write("4. Presionar ESC para salir\n\n")
            f.write("MEJORAS v2.0:\n")
            f.write("- Sin consola molesta\n")
            f.write("- Configuración original optimizada\n")
            f.write("- LIVE_STREAM mode para mejor detección\n")
            f.write("- Umbral de confianza 0.7 (óptimo)\n")
            f.write("- Delay de 0.4s (responsivo)\n")
            f.write("- Resolución 640x480 (estable)\n")
            f.write(f"- Tamaño del archivo: {size_mb:.1f} MB\n")
        
        print(f"📝 Información creada: {info_file}")
        return True
    else:
        print(f"❌ No se encontró el ejecutable en: {source_exe}")
        return False

def main():
    """Función principal de construcción"""
    print("🎯 CONSTRUYENDO VOLUME CONTROLLER ENHANCED v2.0")
    print("Versión sin consola con detección optimizada")
    print("="*60)
    
    # Verificar directorio actual
    if not os.path.exists("volume_controller_enhanced.py"):
        print("❌ No se encontró volume_controller_enhanced.py")
        print("Ejecuta este script desde el directorio del proyecto")
        return False
    
    # Verificar dependencias
    if not check_dependencies():
        print("❌ Error verificando dependencias")
        return False
    
    # Verificar modelo
    if not check_model():
        print("❌ Modelo no encontrado")
        return False
    
    # Limpiar construcción anterior
    clean_build()
    
    # Construir ejecutable
    if not build_executable():
        print("❌ Error construyendo ejecutable")
        return False
    
    # Copiar a release
    if not copy_to_release():
        print("❌ Error preparando release")
        return False
    
    print_section("CONSTRUCCIÓN COMPLETADA")
    print("✅ VolumeController_Enhanced.exe v2.0 está listo!")
    print("📁 Ubicación: release/VolumeController_Enhanced.exe")
    print("\n🎮 CARACTERÍSTICAS v2.0:")
    print("🚫 Sin consola - ejecución limpia")
    print("🎯 Configuración original optimizada (LIVE_STREAM)")
    print("✨ Interfaz visual minimalista")
    print("⚡ Detección responsiva (0.4s delay)")
    print("🔧 Umbral óptimo (0.7 confianza)")
    print("📱 Resolución estable (640x480)")
    
    return True

if __name__ == "__main__":
    success = main()
    
    print("\n" + "="*60)
    if success:
        print("🎉 ¡CONSTRUCCIÓN EXITOSA!")
        print("🚀 El ejecutable no mostrará consola al ejecutarse")
    else:
        print("❌ CONSTRUCCIÓN FALLIDA")
    print("="*60)
    
    input("\nPresiona Enter para continuar...") 