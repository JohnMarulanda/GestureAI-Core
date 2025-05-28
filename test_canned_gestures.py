#!/usr/bin/env python3
"""
Script de prueba para el Controlador de Gestos Predefinidos
Utiliza MediaPipe Gesture Recognizer para detectar los 7 gestos estándar.

Gestos soportados:
1. Puño cerrado (Closed_Fist)
2. Palma abierta (Open_Palm)  
3. Señalando hacia arriba (Pointing_Up)
4. Pulgar hacia abajo (Thumb_Down)
5. Pulgar hacia arriba (Thumb_Up)
6. Victoria - V (Victory)
7. Te amo (ILoveYou)

Controles:
- ESC: Salir del programa
- ESPACIO: Mostrar estadísticas de detección
"""

import sys
import os

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.controllers.canned_gestures_controller import CannedGesturesController

def main():
    """Función principal para ejecutar la prueba de gestos predefinidos."""
    print("="*60)
    print("🖐️  PRUEBA DE RECONOCIMIENTO DE GESTOS PREDEFINIDOS")
    print("="*60)
    print("📋 Este programa utiliza MediaPipe Gesture Recognizer para")
    print("   detectar y rastrear 7 gestos de mano predefinidos.")
    print()
    print("🎯 OBJETIVO:")
    print("   Probar cada uno de los 7 gestos y verificar que el")
    print("   sistema los detecte correctamente con sus respectivas")
    print("   puntuaciones de confianza.")
    print()
    print("📊 CARACTERÍSTICAS:")
    print("   - Detección en tiempo real")
    print("   - Estadísticas de detección")
    print("   - Interfaz visual con información superpuesta")
    print("   - Soporte para hasta 2 manos simultáneamente")
    print()
    print("🔧 CONFIGURACIÓN:")
    print("   - Umbral de confianza: 70%")
    print("   - Delay entre detecciones: 0.5 segundos")
    print("   - Idioma de visualización: Español")
    print()
    print("⌨️  CONTROLES:")
    print("   ESC      : Salir del programa")
    print("   ESPACIO  : Mostrar estadísticas detalladas")
    print()
    
    # Crear y ejecutar el controlador
    try:
        controller = CannedGesturesController()
        controller.run()
    except Exception as e:
        print(f"❌ Error al ejecutar el controlador: {e}")
        print("   Verifica que:")
        print("   1. La cámara esté disponible")
        print("   2. El modelo gesture_recognizer.task exista en models/")
        print("   3. Las dependencias estén instaladas correctamente")
    
    print("\n👋 ¡Gracias por probar el reconocimiento de gestos!")

if __name__ == "__main__":
    main() 