#!/usr/bin/env python3
"""
Script de prueba para el Control de Brillo por Gestos
Utiliza MediaPipe Gesture Recognizer para controlar el brillo de la pantalla.

Gestos soportados:
1. Pulgar hacia arriba (Thumb_Up) → Subir brillo
2. Pulgar hacia abajo (Thumb_Down) → Bajar brillo

Controles:
- ESC: Salir del programa
"""

import sys
import os

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.controllers.brightness_controller import BrightnessController

def main():
    """Función principal para ejecutar la prueba de control de brillo."""
    print("="*60)
    print("☀️ PRUEBA DE CONTROL DE BRILLO POR GESTOS")
    print("="*60)
    print("📋 Este programa utiliza MediaPipe Gesture Recognizer para")
    print("   controlar el brillo de la pantalla mediante gestos.")
    print()
    print("🎯 OBJETIVO:")
    print("   Probar el control de brillo usando 2 gestos específicos")
    print("   y verificar que las acciones se ejecuten correctamente.")
    print()
    print("🖐️ GESTOS DE CONTROL:")
    print("   👍 Pulgar hacia arriba  → Subir brillo (+15%)")
    print("   👎 Pulgar hacia abajo   → Bajar brillo (-15%)")
    print()
    print("📊 CARACTERÍSTICAS:")
    print("   - Control en tiempo real")
    print("   - Cambios de 15% por gesto detectado (RÁPIDO)")
    print("   - Estadísticas de acciones")
    print("   - Interfaz visual con barra de brillo")
    print("   - Soporte para 1 mano optimizado")
    print("   - Landmarks de mano dibujados")
    print()
    print("🔧 CONFIGURACIÓN:")
    print("   - Umbral de confianza: 70%")
    print("   - Delay entre acciones: 0.3 segundos (RÁPIDO)")
    print("   - Pasos de brillo: 15% por gesto (RÁPIDO)")
    print("   - Detección optimizada para gestos de brillo")
    print()
    print("⌨️  CONTROLES:")
    print("   ESC      : Salir del programa")
    print()
    print("⚠️  NOTA IMPORTANTE:")
    print("   Este programa controlará el brillo real de tu pantalla.")
    print("   Asegúrate de estar en un entorno cómodo antes de comenzar.")
    print()
    print("🔍 REQUISITOS:")
    print("   - Cámara web funcional")
    print("   - Modelo gesture_recognizer.task en models/")
    print("   - Librería screen_brightness_control instalada")
    print("   - Permisos para modificar brillo del sistema")
    print()
    
    # Confirmación del usuario
    try:
        input("Presiona ENTER para continuar o Ctrl+C para cancelar...")
    except KeyboardInterrupt:
        print("\n❌ Operación cancelada por el usuario")
        return
    
    # Crear y ejecutar el controlador
    try:
        controller = BrightnessController()
        controller.run()
    except Exception as e:
        print(f"❌ Error al ejecutar el controlador: {e}")
        print("   Verifica que:")
        print("   1. La cámara esté disponible")
        print("   2. El modelo gesture_recognizer.task exista en models/")
        print("   3. Las dependencias estén instaladas correctamente")
        print("   4. screen_brightness_control esté instalado:")
        print("      pip install screen-brightness-control")
        print("   5. Tengas permisos para controlar el brillo del sistema")
        print("   6. Tu sistema soporte control de brillo por software")
    
    print("\n👋 ¡Gracias por probar el control de brillo por gestos!")

if __name__ == "__main__":
    main() 