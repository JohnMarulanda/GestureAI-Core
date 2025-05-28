#!/usr/bin/env python3
"""
Script de prueba para el Control de Volumen por Gestos
Utiliza MediaPipe Gesture Recognizer para controlar el volumen del sistema.

Gestos soportados:
1. Pulgar hacia arriba (Thumb_Up) → Subir volumen
2. Pulgar hacia abajo (Thumb_Down) → Bajar volumen  
3. Puño cerrado (Closed_Fist) → Silenciar/Activar audio

Controles:
- ESC: Salir del programa
"""

import sys
import os

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.controllers.volume_controller import VolumeController

def main():
    """Función principal para ejecutar la prueba de control de volumen."""
    print("="*60)
    print("🔊 PRUEBA DE CONTROL DE VOLUMEN POR GESTOS")
    print("="*60)
    print("📋 Este programa utiliza MediaPipe Gesture Recognizer para")
    print("   controlar el volumen del sistema operativo mediante gestos.")
    print()
    print("🎯 OBJETIVO:")
    print("   Probar el control de volumen usando 3 gestos específicos")
    print("   y verificar que las acciones se ejecuten correctamente.")
    print()
    print("🖐️ GESTOS DE CONTROL:")
    print("   👍 Pulgar hacia arriba  → Subir volumen (+2 niveles)")
    print("   👎 Pulgar hacia abajo   → Bajar volumen (-2 niveles)")
    print("   ✊ Puño cerrado         → Silenciar/Activar audio")
    print()
    print("📊 CARACTERÍSTICAS:")
    print("   - Control en tiempo real")
    print("   - Respuesta más rápida (2 niveles por gesto)")
    print("   - Estadísticas de acciones")
    print("   - Interfaz visual con estado actual")
    print("   - Soporte para 1 mano optimizado")
    print()
    print("🔧 CONFIGURACIÓN:")
    print("   - Umbral de confianza: 70% (más sensible)")
    print("   - Delay entre acciones: 0.4 segundos (más rápido)")
    print("   - Pasos de volumen: 2 niveles por gesto")
    print("   - Detección optimizada para gestos de volumen")
    print()
    print("⌨️  CONTROLES:")
    print("   ESC      : Salir del programa")
    print()
    print("⚠️  NOTA IMPORTANTE:")
    print("   Este programa controlará el volumen real de tu sistema.")
    print("   Asegúrate de tener un volumen moderado antes de comenzar.")
    print()
    
    # Confirmación del usuario
    try:
        input("Presiona ENTER para continuar o Ctrl+C para cancelar...")
    except KeyboardInterrupt:
        print("\n❌ Operación cancelada por el usuario")
        return
    
    # Crear y ejecutar el controlador
    try:
        controller = VolumeController()
        controller.run()
    except Exception as e:
        print(f"❌ Error al ejecutar el controlador: {e}")
        print("   Verifica que:")
        print("   1. La cámara esté disponible")
        print("   2. El modelo gesture_recognizer.task exista en models/")
        print("   3. Las dependencias estén instaladas correctamente")
        print("   4. Tengas permisos para controlar el volumen del sistema")
    
    print("\n👋 ¡Gracias por probar el control de volumen por gestos!")

if __name__ == "__main__":
    main() 