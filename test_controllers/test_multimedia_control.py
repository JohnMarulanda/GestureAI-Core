#!/usr/bin/env python3
"""
Script de prueba para el Control Multimedia por Gestos
Utiliza MediaPipe Gesture Recognizer para controlar funciones multimedia.

Gestos soportados:
1. Pulgar arriba (Thumb_Up) → Adelantar/Siguiente
2. Pulgar abajo (Thumb_Down) → Retroceder/Anterior
3. Puño cerrado (Closed_Fist) → Silenciar/Activar audio
4. Te amo (ILoveYou) → Pausar/Reproducir

Controles:
- ESC: Salir del programa
"""

import sys
import os

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.controllers.multimedia_controller import MultimediaController

def main():
    """Función principal para ejecutar la prueba de control multimedia."""
    print("="*60)
    print("🎵 PRUEBA DE CONTROL MULTIMEDIA POR GESTOS")
    print("="*60)
    print("🎯 OBJETIVO:")
    print("   Probar el control multimedia usando 3 gestos específicos")
    print("   con función dual para el puño cerrado.")
    print()
    print("🖐️ GESTOS DE CONTROL:")
    print("   👍 Pulgar arriba    → Adelantar/Siguiente pista")
    print("   👎 Pulgar abajo     → Retroceder/Anterior pista")
    print("   ✊ Puño             → Silenciar/Activar audio")
    print("   🤟 Te amo           → Pausar/Reproducir")
    print()
    print("🎮 GESTOS CON DELAYS INTELIGENTES:")
    print("   - Navegación rápida (0.4s): Adelantar/Retroceder")
    print("   - Controles lentos (1.5s): Silenciar/Pausar")
    print("   - Evita activaciones accidentales")
    print("   - Indicador visual de tiempo restante")
    print()
    print("📊 CARACTERÍSTICAS:")
    print("   - Control en tiempo real con alta precisión")
    print("   - Umbral de confianza: 70%")
    print("   - Delay navegación: 0.4 segundos")
    print("   - Delay silenciar/pausar: 1.5 segundos")
    print("   - Soporte para 1 mano optimizado")
    print("   - Control de volumen integrado con pycaw")
    print("   - Estadísticas de acciones ejecutadas")
    print("   - Interfaz visual con progreso y estado")
    print("   - Landmarks de mano dibujados")
    print("   - Barra de volumen con estado de silencio")
    print()
    print("🔧 CONFIGURACIÓN:")
    print("   - Gestos: Thumb_Up, Thumb_Down, Closed_Fist, ILoveYou")
    print("   - Delays específicos por tipo de acción")
    print("   - Threading para acciones no bloqueantes")
    print("   - Manejo robusto de errores")
    print("   - Indicadores visuales de disponibilidad")
    print()
    print("⌨️  CONTROLES:")
    print("   ESC      : Salir del programa")
    print()
    print("🎵 ACCIONES MULTIMEDIA:")
    print("   ⏭️ ADELANTAR: Envía tecla 'flecha derecha'")
    print("   ⏮️ RETROCEDER: Envía tecla 'flecha izquierda'")
    print("   🔇 SILENCIAR: Toggle del estado de mute del sistema")
    print("   ⏯️ PAUSAR: Envía tecla 'espacio' para play/pause")
    print()
    print("🔍 REQUISITOS:")
    print("   - Cámara web funcional")
    print("   - Modelo gesture_recognizer.task en models/")
    print("   - pycaw instalado para control de volumen")
    print("   - pyautogui para envío de teclas")
    print("   - Aplicación multimedia activa (reproductor, YouTube, etc.)")
    print()
    print("💡 RECOMENDACIONES:")
    print("   - Abre tu reproductor multimedia favorito")
    print("   - Reproduce algún contenido para probar")
    print("   - Mantén buena iluminación para detección")
    print("   - Usa gestos claros y definidos")
    print("   - El gesto 'Te amo' es meñique + índice + pulgar extendidos")
    print()
    print("🎯 CASOS DE USO:")
    print("   - Control de YouTube sin tocar el teclado")
    print("   - Navegación en Spotify o reproductores")
    print("   - Control de presentaciones multimedia")
    print("   - Accesibilidad para usuarios con limitaciones")
    print()
    
    try:
        input("Presiona ENTER para comenzar la prueba...")
    except KeyboardInterrupt:
        print("\n❌ Operación cancelada por el usuario")
        return
    
    # Crear y ejecutar el controlador
    try:
        print("\n🎵 Inicializando controlador multimedia...")
        controller = MultimediaController()
        controller.run()
    except Exception as e:
        print(f"❌ Error al ejecutar el controlador: {e}")
        print("   Verifica que:")
        print("   1. La cámara esté disponible")
        print("   2. El modelo gesture_recognizer.task exista en models/")
        print("   3. Las dependencias estén instaladas correctamente:")
        print("      pip install mediapipe opencv-python pyautogui pycaw comtypes")
        print("   4. Tu sistema tenga audio configurado")
        print("   5. Tengas una aplicación multimedia abierta")
    
    print("\n👋 ¡Gracias por probar el control multimedia por gestos!")
    print("   Recuerda: Los gestos naturales hacen la experiencia más fluida")

if __name__ == "__main__":
    main() 