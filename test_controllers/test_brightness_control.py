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
import cv2
import time

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.controllers.brightness_controller import BrightnessController

class BrightnessControllerTest:
    """Test wrapper for BrightnessController with enhanced UI and statistics."""
    
    def __init__(self):
        """Initialize the test wrapper."""
        self.controller = BrightnessController()
        
        # Spanish translations for display
        self.gesture_names = {
            'Thumb_Up': 'Subir brillo',
            'Thumb_Down': 'Bajar brillo'
        }
        
        # Brightness action counters
        self.action_counts = {
            'brightness_up': 0,
            'brightness_down': 0
        }
        
        # Override controller methods to add logging and statistics
        self._override_controller_methods()
        
        if self.controller.gesture_recognizer:
            print("✅ Gesture Recognizer para control de brillo inicializado")
            print(f"📺 Monitores detectados: {len(self._get_monitors())}")
            print(f"✅ Brillo actual: {self.controller.current_brightness}%")
            if self.controller.brightness_available:
                print("✅ Control de brillo funcional")
            else:
                print("⚠️ Control de brillo no disponible")
        else:
            print(f"❌ Modelo no encontrado: {self.controller.model_path}")
    
    def _get_monitors(self):
        """Get list of monitors for display purposes."""
        try:
            import screen_brightness_control as sbc
            return sbc.list_monitors()
        except:
            return []
    
    def _override_controller_methods(self):
        """Override controller methods to add logging and statistics."""
        # Store original method
        original_perform_action = self.controller._perform_brightness_action
        
        def enhanced_perform_brightness_action(gesture_name, confidence):
            # Call original method first
            original_perform_action(gesture_name, confidence)
            
            # Add our enhanced logging
            action = self.controller.gesture_actions[gesture_name]
            gesture_display = self.gesture_names[gesture_name]
            
            if not self.controller.brightness_available:
                print(f"⚠️ {gesture_display} detectado pero control de brillo no disponible")
                return
            
            if action == 'brightness_up':
                self.action_counts['brightness_up'] += 1
                print(f"☀️ {gesture_display} (Confianza: {confidence:.2f}) - Brillo: ↑ (+{self.controller.brightness_steps}%) → {self.controller.current_brightness}%")
            elif action == 'brightness_down':
                self.action_counts['brightness_down'] += 1
                print(f"🌙 {gesture_display} (Confianza: {confidence:.2f}) - Brillo: ↓ (-{self.controller.brightness_steps}%) → {self.controller.current_brightness}%")
        
        # Replace method
        self.controller._perform_brightness_action = enhanced_perform_brightness_action
    
    def draw_brightness_info(self, image):
        """Draw brightness control information on the image."""
        try:
            height, width, _ = image.shape
            
            # Draw background rectangle for text
            cv2.rectangle(image, (10, 10), (width - 10, 220), (0, 0, 0), -1)
            cv2.rectangle(image, (10, 10), (width - 10, 220), (255, 255, 255), 2)
            
            # Draw title
            cv2.putText(image, "Control de Brillo por Gestos", 
                       (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Draw brightness availability status
            status_color = (0, 255, 0) if self.controller.brightness_available else (0, 0, 255)
            status_text = "ACTIVO" if self.controller.brightness_available else "NO DISPONIBLE"
            cv2.putText(image, f"Estado: {status_text}", 
                       (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 2)
            
            # Draw current brightness with visual bar
            cv2.putText(image, f"Brillo actual: {self.controller.current_brightness}%", 
                       (20, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Draw brightness bar
            bar_width = 200
            bar_height = 15
            bar_x = 20
            bar_y = 95
        
            # Bar outline
            cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (255, 255, 255), 1)
        
            # Bar fill based on brightness level
            filled_width = int(bar_width * self.controller.current_brightness / 100)
            bar_color = (0, 255, 255) if self.controller.brightness_available else (100, 100, 100)
            cv2.rectangle(image, (bar_x, bar_y), (bar_x + filled_width, bar_y + bar_height), bar_color, -1)
            
            # Draw last detected gesture
            if self.controller.last_gesture:
                gesture_display = self.gesture_names.get(self.controller.last_gesture, self.controller.last_gesture)
                cv2.putText(image, f"Ultimo gesto: {gesture_display}", 
                           (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
            # Draw hands detected count
            hands_count = len(self.controller.current_result.hand_landmarks) if self.controller.current_result and self.controller.current_result.hand_landmarks else 0
            cv2.putText(image, f"Manos detectadas: {hands_count}", 
                       (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Draw gesture instructions
            y_pos = 175
            instructions = [
                f"👍 Pulgar arriba: Subir brillo (+{self.controller.brightness_steps}%)",
                f"👎 Pulgar abajo: Bajar brillo (-{self.controller.brightness_steps}%)"
            ]
            
            for instruction in instructions:
                cv2.putText(image, instruction, (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                y_pos += 20
            
            # Draw exit instruction
            cv2.putText(image, "Presiona ESC para salir", 
                       (20, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
                       
        except Exception as e:
            print(f"⚠️ Error al dibujar información: {e}")
    
    def print_statistics(self):
        """Print brightness control statistics."""
        print("\n" + "="*50)
        print("📊 ESTADÍSTICAS DE CONTROL DE BRILLO")
        print("="*50)
        total_actions = sum(self.action_counts.values())
        
        print(f"{'Subir brillo':<20} | {self.action_counts['brightness_up']:>3} veces")
        print(f"{'Bajar brillo':<20} | {self.action_counts['brightness_down']:>3} veces")
        
        print("-"*50)
        print(f"{'Total de acciones':<20} | {total_actions:>3}")
        print(f"{'Brillo final':<20} | {self.controller.current_brightness:>3}%")
        print(f"{'Control disponible':<20} | {'SÍ' if self.controller.brightness_available else 'NO':>3}")
        print("="*50 + "\n")
    
    def run(self):
        """Run the enhanced brightness control loop."""
        if not self.controller.gesture_recognizer:
            print("❌ Error: Gesture Recognizer no está inicializado")
            return
            
        if not self.controller.start_camera():
            print("❌ Error: No se pudo iniciar la cámara")
            return
        
        print("✅ Cámara iniciada correctamente")
        print("\n☀️ Iniciando control de brillo por gestos...")
        print("Gestos disponibles:")
        print("  👍 Pulgar hacia arriba → Subir brillo")
        print("  👎 Pulgar hacia abajo → Bajar brillo")
        
        if not self.controller.brightness_available:
            print("\n⚠️ ADVERTENCIA: Control de brillo no disponible")
            print("   Los gestos se detectarán pero no cambiarán el brillo")
        
        print("\n💡 Usa los gestos frente a la cámara para controlar el brillo")
        print("   Presiona ESC para salir\n")
        
        try:
            frame_timestamp = 0
            frame_count = 0
            
            while True:
                image = self.controller.process_frame()
                if image is None:
                    break
                
                frame_count += 1
                
                # Process every 2nd frame for better performance
                if frame_count % 2 == 0:
                    # Convert BGR to RGB for MediaPipe
                    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
                    
                    # Process the frame with gesture recognizer
                    if self.controller.gesture_recognizer:
                        frame_timestamp += 66  # Approximately 15 FPS for gesture processing
                        try:
                            self.controller.gesture_recognizer.recognize_async(mp_image, frame_timestamp)
                        except Exception as e:
                            print(f"⚠️ Error en reconocimiento: {e}")
                
                # Draw brightness control information on the image
                self.draw_brightness_info(image)
                
                # Draw hand landmarks
                self.controller.draw_hand_landmarks(image)
                
                # Display the image
                cv2.imshow('Control de Brillo por Gestos', image)
                
                # Exit on ESC key
                if cv2.waitKey(1) & 0xFF == 27:
                    break
                    
        except KeyboardInterrupt:
            print("\n⚠️ Interrupción por teclado detectada")
        except Exception as e:
            print(f"❌ Error durante la ejecución: {e}")
        finally:
            self.controller.stop_camera()
            print("📷 Cámara cerrada")
            self.print_statistics()
            print("👋 Control de brillo finalizado")

def main():
    """Función principal para ejecutar la prueba de control de brillo."""
    print("="*60)
    print("☀️ PRUEBA DE CONTROL DE BRILLO POR GESTOS")
    print("="*60)
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
    print("   - Detección automática de disponibilidad")
    print("   - Múltiples métodos de control de brillo")
    print("   - Brillo mínimo de 10% (evita pantalla negra)")
    print()
    print("🔧 CONFIGURACIÓN:")
    print("   - Umbral de confianza: 70%")
    print("   - Delay entre acciones: 0.3 segundos (RÁPIDO)")
    print("   - Pasos de brillo: 15% por gesto (RÁPIDO)")
    print("   - Detección optimizada para gestos de brillo")
    print("   - Threading para acciones no bloqueantes")
    print("   - Manejo robusto de errores")
    print()
    print("⌨️  CONTROLES:")
    print("   ESC      : Salir del programa")
    print()
    print("🔍 REQUISITOS:")
    print("   - Cámara web funcional")
    print("   - Modelo gesture_recognizer.task en models/")
    print("   - Librería screen_brightness_control instalada")
    print("   - Permisos para modificar brillo del sistema")
    print("   - Sistema compatible con control de brillo por software")
    print()
    print("💡 RECOMENDACIONES:")
    print("   - Usa buena iluminación para mejor detección")
    print("   - Haz gestos claros de pulgar arriba/abajo")
    print("   - Espera 0.3 segundos entre gestos")
    print("   - El brillo mínimo es 10% para evitar pantalla negra")
    print("   - Funciona mejor con monitores externos")
    print()
    print("🎯 CASOS DE USO:")
    print("   - Control de brillo sin tocar teclado")
    print("   - Ajuste rápido durante presentaciones")
    print("   - Accesibilidad para usuarios con limitaciones")
    print("   - Control remoto de brillo")
    print("   - Automatización de configuración de pantalla")
    print()
    print("⚠️  NOTA IMPORTANTE:")
    print("   Este programa controlará el brillo real de tu pantalla.")
    print("   Asegúrate de estar en un entorno cómodo antes de comenzar.")
    print("   Si el control no funciona, se mostrará una advertencia.")
    print()
    
    # Confirmación del usuario
    try:
        input("Presiona ENTER para continuar o Ctrl+C para cancelar...")
    except KeyboardInterrupt:
        print("\n❌ Operación cancelada por el usuario")
        return
    
    # Crear y ejecutar el controlador
    try:
        print("\n🚀 Inicializando controlador de brillo...")
        test_controller = BrightnessControllerTest()
        test_controller.run()
    except Exception as e:
        print(f"❌ Error al ejecutar el controlador: {e}")
        print("   Verifica que:")
        print("   1. La cámara esté disponible")
        print("   2. El modelo gesture_recognizer.task exista en models/")
        print("   3. Las dependencias estén instaladas correctamente:")
        print("      pip install mediapipe opencv-python screen-brightness-control")
        print("   4. Tengas permisos para controlar el brillo del sistema")
        print("   5. Tu sistema soporte control de brillo por software")
        print("   6. Los drivers de tu monitor estén actualizados")
    
    print("\n👋 ¡Gracias por probar el control de brillo por gestos!")
    print("   El control de brillo por gestos es útil para ajustes rápidos")

if __name__ == "__main__":
    main() 