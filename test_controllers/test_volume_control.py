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
import cv2
import time
import mediapipe as mp

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.controllers.volume_controller import VolumeController

class VolumeControllerTest(VolumeController):
    """Extended Volume Controller with test interface and statistics."""
    
    def __init__(self, model_path=None):
        """Initialize the test volume controller."""
        super().__init__(model_path)
        
        # Spanish translations for display
        self.gesture_names = {
            'Thumb_Up': 'Subir volumen',
            'Thumb_Down': 'Bajar volumen', 
            'Closed_Fist': 'Silenciar/Activar'
        }
    
    def _initialize_recognizer(self):
        """Initialize the MediaPipe Gesture Recognizer with console feedback."""
        super()._initialize_recognizer()
        if self.gesture_recognizer:
            print("✅ Gesture Recognizer para control de volumen inicializado")
        else:
            print("❌ Error al inicializar Gesture Recognizer")
    
    def _perform_volume_action(self, gesture_name, confidence):
        """Perform volume action with console feedback."""
        super()._perform_volume_action(gesture_name, confidence)
        
        action = self.gesture_actions[gesture_name]
        gesture_display = self.gesture_names[gesture_name]
        
        if action == 'volume_up':
            print(f"🔊 {gesture_display} (Confianza: {confidence:.2f}) - Volumen: ↑↑ (+{self.volume_steps})")
            
        elif action == 'volume_down':
            print(f"🔉 {gesture_display} (Confianza: {confidence:.2f}) - Volumen: ↓↓ (-{self.volume_steps})")
            
        elif action == 'toggle_mute':
            if self.is_muted:
                print(f"🔇 {gesture_display} (Confianza: {confidence:.2f}) - Audio: SILENCIADO")
            else:
                print(f"🔊 {gesture_display} (Confianza: {confidence:.2f}) - Audio: ACTIVADO")
    
    def start_camera(self, camera_id=0):
        """Start camera with console feedback."""
        result = super().start_camera(camera_id)
        if result:
            print("✅ Cámara iniciada correctamente")
        else:
            print("❌ Error: No se pudo abrir la cámara")
        return result
    
    def stop_camera(self):
        """Stop camera with console feedback."""
        super().stop_camera()
        print("📷 Cámara cerrada")
    
    def draw_volume_info(self, image):
        """Draw volume control information on the image."""
        height, width, _ = image.shape
        
        # Draw background rectangle for text
        cv2.rectangle(image, (10, 10), (width - 10, 200), (0, 0, 0), -1)
        cv2.rectangle(image, (10, 10), (width - 10, 200), (255, 255, 255), 2)
        
        # Draw title
        cv2.putText(image, "Control de Volumen por Gestos", 
                   (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Draw current status
        status_text = "SILENCIADO" if self.is_muted else "ACTIVO"
        status_color = (0, 0, 255) if self.is_muted else (0, 255, 0)
        cv2.putText(image, f"Estado: {status_text}", 
                   (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
        
        # Draw last detected gesture
        if self.last_gesture:
            gesture_display = self.gesture_names.get(self.last_gesture, self.last_gesture)
            cv2.putText(image, f"Ultimo gesto: {gesture_display}", 
                       (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Draw hands detected count
        hands_count = len(self.current_result.hand_landmarks) if self.current_result and self.current_result.hand_landmarks else 0
        cv2.putText(image, f"Manos detectadas: {hands_count}", 
                   (20, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Draw gesture instructions
        y_pos = 140
        instructions = [
            f"👍 Pulgar arriba: Subir volumen (+{self.volume_steps})",
            f"👎 Pulgar abajo: Bajar volumen (-{self.volume_steps})", 
            "✊ Puño cerrado: Silenciar/Activar"
        ]
        
        for instruction in instructions:
            cv2.putText(image, instruction, (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            y_pos += 20
        
        # Draw exit instruction
        cv2.putText(image, "Presiona ESC para salir", 
                   (20, 185), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
    
    def print_statistics(self):
        """Print volume control statistics."""
        print("\n" + "="*50)
        print("📊 ESTADÍSTICAS DE CONTROL DE VOLUMEN")
        print("="*50)
        total_actions = sum(self.action_counts.values())
        
        print(f"{'Subir volumen':<20} | {self.action_counts['volume_up']:>3} veces")
        print(f"{'Bajar volumen':<20} | {self.action_counts['volume_down']:>3} veces")
        print(f"{'Silenciar':<20} | {self.action_counts['mute']:>3} veces")
        print(f"{'Activar sonido':<20} | {self.action_counts['unmute']:>3} veces")
        
        print("-"*50)
        print(f"{'Total de acciones':<20} | {total_actions:>3}")
        print("="*50 + "\n")
    
    def run(self):
        """Run the volume control loop with full test interface."""
        if not self.gesture_recognizer:
            print("❌ Error: Gesture Recognizer no está inicializado")
            return False
            
        if not self.start_camera():
            print("❌ Error: No se pudo iniciar la cámara")
            return False
        
        print("\n🔊 Iniciando control de volumen por gestos...")
        print("Gestos disponibles:")
        print("  👍 Pulgar hacia arriba → Subir volumen")
        print("  👎 Pulgar hacia abajo → Bajar volumen")
        print("  ✊ Puño cerrado → Silenciar/Activar audio")
        print("\n💡 Usa los gestos frente a la cámara para controlar el volumen")
        print("   Presiona ESC para salir\n")
        
        try:
            frame_timestamp = 0
            while True:
                image = self.process_frame()
                if image is None:
                    break
                
                # Convert BGR to RGB for MediaPipe
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
                
                # Process the frame with gesture recognizer
                if self.gesture_recognizer:
                    frame_timestamp += 33  # Approximately 30 FPS
                    self.gesture_recognizer.recognize_async(mp_image, frame_timestamp)
                
                # Draw volume control information on the image
                self.draw_volume_info(image)
                
                # Draw hand landmarks
                self.draw_hand_landmarks(image)
                
                # Display the image
                cv2.imshow('Control de Volumen por Gestos - PRUEBA', image)
                
                # Exit on ESC key
                if cv2.waitKey(1) & 0xFF == 27:
                    break
                    
        except KeyboardInterrupt:
            print("\n⚠️ Interrupción por teclado detectada")
        except Exception as e:
            print(f"❌ Error durante la ejecución: {e}")
        finally:
            self.stop_camera()
            self.print_statistics()
            print("👋 Control de volumen finalizado")
            return True

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
    print("   - Visualización de landmarks de las manos")
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
    
    # Crear y ejecutar el controlador de prueba
    try:
        controller = VolumeControllerTest()
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