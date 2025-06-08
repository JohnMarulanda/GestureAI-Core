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
import cv2
import time

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.controllers.canned_gestures_controller import CannedGesturesController

class CannedGesturesControllerTest:
    """Test wrapper for CannedGesturesController with enhanced UI and statistics."""
    
    def __init__(self):
        """Initialize the test wrapper."""
        self.controller = CannedGesturesController()
        
        # Gesture mapping for better display
        self.gesture_mapping = {
            'None': 'Sin gesto detectado',
            'Closed_Fist': 'Puño cerrado',
            'Open_Palm': 'Palma abierta',
            'Pointing_Up': 'Señalando hacia arriba',
            'Thumb_Down': 'Pulgar hacia abajo',
            'Thumb_Up': 'Pulgar hacia arriba',
            'Victory': 'Victoria (V)',
            'ILoveYou': 'Te amo (I Love You)'
        }
        
        # Gesture statistics
        self.gesture_counts = {gesture: 0 for gesture in self.gesture_mapping.keys()}
        
        # Override controller methods to add logging and statistics
        self._override_controller_methods()
        
        if self.controller.gesture_recognizer:
            print("✅ Gesture Recognizer inicializado correctamente")
        else:
            print(f"❌ Modelo no encontrado: {self.controller.model_path}")
    
    def _override_controller_methods(self):
        """Override controller methods to add logging and statistics."""
        # Store original callback
        original_callback = self.controller._gesture_result_callback
        
        def enhanced_gesture_result_callback(result, output_image, timestamp_ms):
            # Call original callback first
            original_callback(result, output_image, timestamp_ms)
            
            # Add our enhanced logging
            if result.gestures:
                for hand_gesture in result.gestures:
                    if hand_gesture:
                        gesture = hand_gesture[0]
                        gesture_name = gesture.category_name
                        confidence = gesture.score
                        
                        # Only process if confidence is above threshold
                        if confidence >= self.controller.confidence_threshold:
                            current_time = time.time()
                            if current_time - self.controller.last_action_time > self.controller.action_delay:
                                # Update our statistics
                                self.gesture_counts[gesture_name] += 1
                                
                                # Print detected gesture
                                spanish_name = self.gesture_mapping.get(gesture_name, gesture_name)
                                print(f"🖐️ Gesto detectado: {spanish_name} (Confianza: {confidence:.2f})")
        
        # Replace callback
        self.controller._gesture_result_callback = enhanced_gesture_result_callback
    
    def draw_gesture_info(self, image):
        """Draw gesture information on the image."""
        height, width, _ = image.shape
        
        # Draw background rectangle for text
        cv2.rectangle(image, (10, 10), (width - 10, 180), (0, 0, 0), -1)
        cv2.rectangle(image, (10, 10), (width - 10, 180), (255, 255, 255), 2)
        
        # Draw title
        cv2.putText(image, "Reconocimiento de Gestos Predefinidos", 
                   (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Draw last detected gesture
        if self.controller.last_detected_gesture:
            spanish_name = self.gesture_mapping.get(self.controller.last_detected_gesture, self.controller.last_detected_gesture)
            cv2.putText(image, f"Ultimo gesto: {spanish_name}", 
                       (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Draw hands detected count
        hands_count = len(self.controller.current_result.hand_landmarks) if self.controller.current_result and self.controller.current_result.hand_landmarks else 0
        cv2.putText(image, f"Manos detectadas: {hands_count}", 
                   (20, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Draw gesture counts in a compact format
        y_pos = 110
        line1 = f"Puno: {self.gesture_counts['Closed_Fist']} | Palma: {self.gesture_counts['Open_Palm']} | Arriba: {self.gesture_counts['Pointing_Up']}"
        line2 = f"Pulgar-: {self.gesture_counts['Thumb_Down']} | Pulgar+: {self.gesture_counts['Thumb_Up']} | Victoria: {self.gesture_counts['Victory']} | Love: {self.gesture_counts['ILoveYou']}"
        
        cv2.putText(image, line1, (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        cv2.putText(image, line2, (20, y_pos + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        # Draw instructions
        cv2.putText(image, "Presiona ESC para salir | Espacio para estadisticas", 
                   (20, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
    
    def print_statistics(self):
        """Print gesture detection statistics."""
        print("\n" + "="*50)
        print("📊 ESTADÍSTICAS DE DETECCIÓN DE GESTOS")
        print("="*50)
        total_gestures = sum(self.gesture_counts.values())
        
        for gesture_en, count in self.gesture_counts.items():
            gesture_es = self.gesture_mapping[gesture_en]
            percentage = (count / total_gestures * 100) if total_gestures > 0 else 0
            print(f"{gesture_es:<25} | {count:>3} veces ({percentage:>5.1f}%)")
        
        print("-"*50)
        print(f"{'Total de gestos detectados':<25} | {total_gestures:>3}")
        print("="*50 + "\n")
    
    def run(self):
        """Run the enhanced canned gestures recognition loop."""
        if not self.controller.gesture_recognizer:
            print("❌ Error: Gesture Recognizer no está inicializado")
            return
            
        if not self.controller.start_camera():
            print("❌ Error: No se pudo iniciar la cámara")
            return
        
        print("\n🚀 Iniciando reconocimiento de gestos predefinidos...")
        print("Gestos disponibles:")
        for i, (gesture_en, gesture_es) in enumerate(self.gesture_mapping.items(), 1):
            if gesture_en != 'None':
                print(f"  {i}. {gesture_es}")
        print("\n💡 Muestra diferentes gestos frente a la cámara para probarlos")
        print("   Presiona ESC para salir o ESPACIO para ver estadísticas\n")
        
        try:
            frame_timestamp = 0
            while True:
                image = self.controller.process_frame()
                if image is None:
                    break
                
                # Convert BGR to RGB for MediaPipe
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
                
                # Process the frame with gesture recognizer
                if self.controller.gesture_recognizer:
                    frame_timestamp += 33
                    try:
                        self.controller.gesture_recognizer.recognize_async(mp_image, frame_timestamp)
                    except Exception as e:
                        print(f"⚠️ Error en reconocimiento: {e}")
                
                # Draw gesture information on the image
                self.draw_gesture_info(image)
                
                # Draw hand landmarks
                self.controller.draw_hand_landmarks(image)
                
                # Display the image
                cv2.imshow('Reconocimiento de Gestos Predefinidos', image)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC key
                    break
                elif key == 32:  # Space key
                    self.print_statistics()
                    
        except KeyboardInterrupt:
            print("\n⚠️ Interrupción por teclado detectada")
        except Exception as e:
            print(f"❌ Error durante la ejecución: {e}")
        finally:
            self.controller.stop_camera()
            self.print_statistics()
            print("👋 Programa finalizado")

def main():
    """Función principal para ejecutar la prueba de gestos predefinidos."""
    print("="*60)
    print("🖐️  PRUEBA DE RECONOCIMIENTO DE GESTOS PREDEFINIDOS")
    print("="*60)
    print("🎯 OBJETIVO:")
    print("   Probar el reconocimiento de los 7 gestos predefinidos")
    print("   de MediaPipe con estadísticas detalladas y visualización.")
    print()
    print("🖐️ GESTOS DISPONIBLES:")
    print("   1. 🤛 Puño cerrado (Closed_Fist)")
    print("   2. ✋ Palma abierta (Open_Palm)")
    print("   3. ☝️ Señalando hacia arriba (Pointing_Up)")
    print("   4. 👎 Pulgar hacia abajo (Thumb_Down)")
    print("   5. 👍 Pulgar hacia arriba (Thumb_Up)")
    print("   6. ✌️ Victoria - V (Victory)")
    print("   7. 🤟 Te amo (ILoveYou)")
    print()
    print("📊 CARACTERÍSTICAS:")
    print("   - Detección en tiempo real con MediaPipe")
    print("   - Estadísticas de detección por gesto")
    print("   - Interfaz visual con información superpuesta")
    print("   - Soporte para hasta 2 manos simultáneamente")
    print("   - Landmarks de mano dibujados en tiempo real")
    print("   - Contador de gestos detectados")
    print("   - Porcentajes de uso por gesto")
    print()
    print("🔧 CONFIGURACIÓN:")
    print("   - Umbral de confianza: 70%")
    print("   - Delay entre detecciones: 0.5 segundos")
    print("   - Resolución: 640x480 a 30 FPS")
    print("   - Detección de manos: Hasta 2 manos")
    print("   - Idioma de visualización: Español")
    print("   - Modelo: gesture_recognizer.task")
    print()
    print("⌨️  CONTROLES:")
    print("   ESC      : Salir del programa")
    print("   ESPACIO  : Mostrar estadísticas detalladas")
    print()
    print("💡 RECOMENDACIONES:")
    print("   - Usa buena iluminación para mejor detección")
    print("   - Mantén las manos dentro del campo de visión")
    print("   - Haz gestos claros y definidos")
    print("   - Espera 0.5 segundos entre gestos")
    print("   - Prueba cada gesto varias veces")
    print()
    print("🔍 REQUISITOS:")
    print("   - Cámara web funcional")
    print("   - Modelo gesture_recognizer.task en models/")
    print("   - Dependencias instaladas:")
    print("     pip install mediapipe opencv-python")
    print()
    print("🎯 CASOS DE USO:")
    print("   - Validación de gestos predefinidos")
    print("   - Testing de precisión del modelo")
    print("   - Calibración de umbrales de confianza")
    print("   - Análisis de rendimiento por gesto")
    print("   - Desarrollo de aplicaciones basadas en gestos")
    print()
    
    try:
        input("Presiona ENTER para comenzar la prueba...")
    except KeyboardInterrupt:
        print("\n❌ Operación cancelada por el usuario")
        return
    
    # Crear y ejecutar el controlador de prueba
    try:
        print("\n🚀 Inicializando controlador de gestos predefinidos...")
        test_controller = CannedGesturesControllerTest()
        test_controller.run()
    except Exception as e:
        print(f"❌ Error al ejecutar el controlador: {e}")
        print("   Verifica que:")
        print("   1. La cámara esté disponible")
        print("   2. El modelo gesture_recognizer.task exista en models/")
        print("   3. Las dependencias estén instaladas correctamente:")
        print("      pip install mediapipe opencv-python")
        print("   4. Tengas permisos para acceder a la cámara")
    
    print("\n👋 ¡Gracias por probar el reconocimiento de gestos predefinidos!")
    print("   Los gestos predefinidos son la base para aplicaciones más complejas")

if __name__ == "__main__":
    main() 