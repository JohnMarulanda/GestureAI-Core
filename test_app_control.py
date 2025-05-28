#!/usr/bin/env python3
"""
Script de prueba para el Control de Aplicaciones por Gestos
Utiliza MediaPipe Gesture Recognizer para abrir y cerrar aplicaciones.

Gestos soportados:
1. Puño cerrado (Closed_Fist) → Chrome (abrir/cerrar)
2. Dedo índice arriba (Pointing_Up) → Notepad (abrir/cerrar)
3. Victoria (Victory) → Calculator (abrir/cerrar)
4. Te amo (ILoveYou) → Spotify (abrir/cerrar)

Controles:
- ESC: Salir del programa
"""

import sys
import os

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.controllers.app_controller import AppController

def main():
    """Función principal para ejecutar la prueba de control de aplicaciones."""
    print("="*60)
    print("🚀 PRUEBA DE CONTROL DE APLICACIONES POR GESTOS")
    print("="*60)
    print("🎯 OBJETIVO:")
    print("   Probar el control automático de aplicaciones usando")
    print("   4 gestos predefinidos con detección inteligente.")
    print()
    print("🖐️ GESTOS DE CONTROL:")
    print("   ✊ Puño cerrado       → Chrome (abrir/cerrar)")
    print("   ☝️ Dedo índice arriba → Notepad (abrir/cerrar)")
    print("   ✌️ Victoria (V)       → Calculator (abrir/cerrar)")
    print("   🤟 Te amo             → Spotify (abrir/cerrar)")
    print()
    print("🎮 FUNCIONAMIENTO INTELIGENTE:")
    print("   - Mismo gesto para abrir y cerrar cada aplicación")
    print("   - Detección automática del estado de la aplicación")
    print("   - Si la app está cerrada → la abre")
    print("   - Si la app está abierta → la cierra")
    print("   - Delays de seguridad para evitar cierres accidentales")
    print("   - Rastreo de procesos en tiempo real")
    print()
    print("📊 CARACTERÍSTICAS:")
    print("   - Control en tiempo real con alta precisión")
    print("   - Umbral de confianza: 75%")
    print("   - Delay general: 2.0 segundos")
    print("   - Delay cerrar: 5.0 segundos (seguridad)")
    print("   - Delay protección: 3.0 segundos (después de abrir)")
    print("   - Soporte para 1 mano optimizado")
    print("   - Detección automática de rutas de aplicaciones")
    print("   - Estadísticas de acciones ejecutadas")
    print("   - Interfaz visual con estado de aplicaciones")
    print("   - Landmarks de mano dibujados")
    print("   - Indicadores de tiempo de espera")
    print("   - Protección contra cierres accidentales")
    print()
    print("🔧 CONFIGURACIÓN:")
    print("   - Gestos: Closed_Fist, Pointing_Up, Victory, ILoveYou")
    print("   - Delays específicos por tipo de acción")
    print("   - Threading para acciones no bloqueantes")
    print("   - Manejo robusto de errores")
    print("   - Búsqueda automática de rutas de aplicaciones")
    print("   - Sistema de protección multicapa")
    print()
    print("⌨️  CONTROLES:")
    print("   ESC      : Salir del programa")
    print()
    print("🚀 APLICACIONES CONTROLADAS:")
    print("   🌐 CHROME: Navegador web principal")
    print("   📝 NOTEPAD: Editor de texto básico")
    print("   🧮 CALCULATOR: Calculadora del sistema")
    print("   🎵 SPOTIFY: Reproductor de música")
    print()
    print("🔍 REQUISITOS:")
    print("   - Cámara web funcional")
    print("   - Modelo gesture_recognizer.task en models/")
    print("   - psutil instalado para manejo de procesos")
    print("   - Aplicaciones instaladas en el sistema")
    print("   - Permisos para abrir/cerrar aplicaciones")
    print()
    print("💡 RECOMENDACIONES:")
    print("   - Cierra aplicaciones importantes antes de probar")
    print("   - Mantén buena iluminación para detección")
    print("   - Usa gestos claros y definidos")
    print("   - 'Dedo índice arriba' es más confiable que palma abierta")
    print("   - El gesto 'Te amo' es meñique + índice + pulgar extendidos")
    print("   - Espera los delays de seguridad para cerrar aplicaciones")
    print("   - Las apps recién abiertas tienen protección de 3 segundos")
    print()
    print("🎯 CASOS DE USO:")
    print("   - Apertura rápida de aplicaciones frecuentes")
    print("   - Control sin tocar teclado o mouse")
    print("   - Demostraciones y presentaciones")
    print("   - Accesibilidad para usuarios con limitaciones")
    print("   - Automatización de flujos de trabajo")
    print()
    print("⚠️  ADVERTENCIAS:")
    print("   - Las aplicaciones se cerrarán realmente")
    print("   - Guarda tu trabajo antes de probar")
    print("   - Delay de 5 segundos para cerrar por seguridad")
    print("   - Protección de 3 segundos después de abrir")
    print("   - Chrome puede tener múltiples procesos")
    print("   - Spotify puede requerir instalación específica")
    print("   - Los delays son más largos para mayor seguridad")
    print()
    
    try:
        input("Presiona ENTER para comenzar la prueba...")
    except KeyboardInterrupt:
        print("\n❌ Operación cancelada por el usuario")
        return
    
    # Crear y ejecutar el controlador
    try:
        print("\n🚀 Inicializando controlador de aplicaciones...")
        controller = AppController()
        controller.run()
    except Exception as e:
        print(f"❌ Error al ejecutar el controlador: {e}")
        print("   Verifica que:")
        print("   1. La cámara esté disponible")
        print("   2. El modelo gesture_recognizer.task exista en models/")
        print("   3. Las dependencias estén instaladas correctamente:")
        print("      pip install mediapipe opencv-python psutil")
        print("   4. Las aplicaciones estén instaladas:")
        print("      - Chrome: Navegador web")
        print("      - Notepad: Incluido en Windows")
        print("      - Calculator: Incluido en Windows")
        print("      - Spotify: Descargable desde spotify.com")
        print("   5. Tengas permisos para ejecutar aplicaciones")
    
    print("\n👋 ¡Gracias por probar el control de aplicaciones por gestos!")
    print("   Recuerda: Los gestos naturales hacen la experiencia más fluida")

if __name__ == "__main__":
    main() 