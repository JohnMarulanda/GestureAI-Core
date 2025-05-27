#!/usr/bin/env python3
"""
Script de prueba para el App Controller
Este script verifica que el controlador de aplicaciones funcione correctamente
"""

import os
import sys
import time

# Agregar el directorio padre al path para importar los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.controllers.app_controller import AppController

def test_app_controller():
    """Función principal de prueba"""
    print("=== PRUEBA DEL CONTROLADOR DE APLICACIONES ===")
    print()
    
    # Crear instancia del controlador
    print("1. Creando instancia del controlador...")
    controller = AppController()
    
    # Verificar configuración cargada
    print("2. Verificando configuración...")
    print(f"   - Gestos de apertura: {len(controller.config['gestures'].get('open', {}))}")
    print(f"   - Gestos de cierre: {len(controller.config['gestures'].get('close', {}))}")
    print(f"   - Rutas de aplicaciones: {len(controller.config['paths'])}")
    print(f"   - Gestos de botones: {len(controller.config['button_gestures'])}")
    
    # Verificar rutas de aplicaciones
    print("3. Verificando rutas de aplicaciones...")
    for app_name, app_path in controller.config['paths'].items():
        exists = os.path.exists(app_path)
        status = "✓" if exists else "✗"
        print(f"   {status} {app_name}: {app_path}")
    
    print()
    print("4. Iniciando controlador...")
    
    try:
        success = controller.start()
        if success:
            print("✓ Controlador iniciado exitosamente")
            print()
            print("=== INSTRUCCIONES DE USO ===")
            print("1. Asegúrate de que tu mano esté visible en la cámara")
            print("2. Usa los gestos configurados para controlar las aplicaciones:")
            print()
            
            # Mostrar gestos configurados
            print("GESTOS PARA ABRIR APLICACIONES:")
            for app_name, gesture in controller.config["gestures"].get("open", {}).items():
                gesture_str = "".join(map(str, gesture))
                print(f"   • {app_name}: [{gesture_str}]")
            
            print()
            print("GESTOS PARA CERRAR APLICACIONES:")
            for app_name, gesture in controller.config["gestures"].get("close", {}).items():
                gesture_str = "".join(map(str, gesture))
                print(f"   • {app_name}: [{gesture_str}]")
            
            print()
            print("CONTROLES ESPECIALES:")
            for button_name, gesture in controller.config["button_gestures"].items():
                if button_name in ["quit_controller", "quit_app"]:
                    gesture_str = "".join(map(str, gesture))
                    action = "Salir del controlador" if button_name == "quit_controller" else "Salir de la aplicación"
                    print(f"   • {action}: [{gesture_str}]")
            
            print()
            print("3. Los números representan el estado de cada dedo:")
            print("   [Pulgar, Índice, Medio, Anular, Meñique]")
            print("   1 = dedo extendido, 0 = dedo cerrado")
            print()
            print("4. Presiona 'q' en la ventana de video para salir")
            print("="*50)
            
            # Mantener el programa ejecutándose
            try:
                while controller.running:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                print("\nInterrumpiendo...")
                
        else:
            print("✗ Error al iniciar el controlador")
            return False
            
    except Exception as e:
        print(f"✗ Error durante la ejecución: {e}")
        return False
        
    finally:
        print("5. Deteniendo controlador...")
        controller.stop()
        print("✓ Controlador detenido")
    
    return True

def verify_dependencies():
    """Verifica que todas las dependencias estén instaladas"""
    print("=== VERIFICACIÓN DE DEPENDENCIAS ===")
    
    required_modules = [
        'cv2', 'mediapipe', 'psutil', 'numpy'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError:
            print(f"✗ {module} - NO ENCONTRADO")
            missing_modules.append(module)
    
    if missing_modules:
        print()
        print("Módulos faltantes. Instala con:")
        print("pip install", " ".join(missing_modules))
        return False
    
    print("✓ Todas las dependencias están instaladas")
    return True

if __name__ == "__main__":
    print("SCRIPT DE PRUEBA - CONTROLADOR DE APLICACIONES")
    print("=" * 50)
    
    # Verificar dependencias
    if not verify_dependencies():
        sys.exit(1)
    
    print()
    
    # Ejecutar prueba
    success = test_app_controller()
    
    if success:
        print("\n✓ Prueba completada exitosamente")
    else:
        print("\n✗ La prueba falló")
        sys.exit(1) 