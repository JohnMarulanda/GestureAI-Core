import cv2
import pyautogui
import mediapipe as mp
import os
import time
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class VolumeController:
    """Controller for adjusting system volume using MediaPipe predefined hand gestures."""
    
    def __init__(self, model_path=None):
        """Initialize the volume controller with gesture recognition."""
        # Set default model path if not provided
        if model_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            model_path = os.path.join(project_root, 'models', 'gesture_recognizer.task')
        
        self.model_path = model_path
        self.webcam = None
        self.gesture_recognizer = None
        self.last_action_time = 0
        self.action_delay = 0.4  # Delay between volume actions (más rápido: era 0.8)
        
        # Volume control state
        self.is_muted = False
        self.last_gesture = None
        self.current_result = None
        self.confidence_threshold = 0.7  # Umbral más bajo para mayor sensibilidad (era 0.75)
        
        # Gesture mapping for volume control
        self.gesture_actions = {
            'Thumb_Up': 'volume_up',
            'Thumb_Down': 'volume_down',
            'Closed_Fist': 'toggle_mute'
        }
        
        # Spanish translations for display
        self.gesture_names = {
            'Thumb_Up': 'Subir volumen',
            'Thumb_Down': 'Bajar volumen', 
            'Closed_Fist': 'Silenciar/Activar'
        }
        
        # Volume action counters
        self.action_counts = {
            'volume_up': 0,
            'volume_down': 0,
            'mute': 0,
            'unmute': 0
        }
        
        # Volume control configuration
        self.volume_steps = 2  # Número de pasos de volumen por gesto detectado
        
        self._initialize_recognizer()
    
    def _initialize_recognizer(self):
        """Initialize the MediaPipe Gesture Recognizer."""
        try:
            # Configure base options
            base_options = python.BaseOptions(model_asset_path=self.model_path)
            
            # Configure gesture recognizer options
            options = vision.GestureRecognizerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.LIVE_STREAM,
                result_callback=self._gesture_result_callback,
                num_hands=1,  # Only one hand for volume control
                min_hand_detection_confidence=0.7,
                min_hand_presence_confidence=0.7,
                min_tracking_confidence=0.7
            )
            
            # Create the gesture recognizer
            self.gesture_recognizer = vision.GestureRecognizer.create_from_options(options)
            print("✅ Gesture Recognizer para control de volumen inicializado")
            
        except Exception as e:
            print(f"❌ Error al inicializar Gesture Recognizer: {e}")
            self.gesture_recognizer = None
    
    def _gesture_result_callback(self, result: vision.GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int):
        """Callback function to handle gesture recognition results."""
        self.current_result = result
        
        if result.gestures:
            for hand_gesture in result.gestures:
                if hand_gesture:
                    gesture = hand_gesture[0]  # Get the top gesture
                    gesture_name = gesture.category_name
                    confidence = gesture.score
                    
                    # Only process volume control gestures with high confidence
                    if (gesture_name in self.gesture_actions and 
                        confidence >= self.confidence_threshold):
                        
                        current_time = time.time()
                        if current_time - self.last_action_time > self.action_delay:
                            self.last_gesture = gesture_name
                            self._perform_volume_action(gesture_name, confidence)
                            self.last_action_time = current_time
    
    def _perform_volume_action(self, gesture_name, confidence):
        """Perform the volume action based on the detected gesture."""
        action = self.gesture_actions[gesture_name]
        gesture_display = self.gesture_names[gesture_name]
        
        if action == 'volume_up':
            # Increase volume multiple steps for faster response
            for _ in range(self.volume_steps):
                pyautogui.press('volumeup')
            self.action_counts['volume_up'] += 1
            print(f"🔊 {gesture_display} (Confianza: {confidence:.2f}) - Volumen: ↑↑ (+{self.volume_steps})")
            
        elif action == 'volume_down':
            # Decrease volume multiple steps for faster response
            for _ in range(self.volume_steps):
                pyautogui.press('volumedown')
            self.action_counts['volume_down'] += 1
            print(f"🔉 {gesture_display} (Confianza: {confidence:.2f}) - Volumen: ↓↓ (-{self.volume_steps})")
            
        elif action == 'toggle_mute':
            # Toggle mute/unmute
            pyautogui.press('volumemute')
            self.is_muted = not self.is_muted
            if self.is_muted:
                self.action_counts['mute'] += 1
                print(f"🔇 {gesture_display} (Confianza: {confidence:.2f}) - Audio: SILENCIADO")
            else:
                self.action_counts['unmute'] += 1
                print(f"🔊 {gesture_display} (Confianza: {confidence:.2f}) - Audio: ACTIVADO")
    
    def start_camera(self, camera_id=0):
        """Start the webcam capture."""
        try:
            self.webcam = cv2.VideoCapture(camera_id)
            if not self.webcam.isOpened():
                print("❌ Error: No se pudo abrir la cámara")
                return False
            
            # Set camera properties for better performance
            self.webcam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.webcam.set(cv2.CAP_PROP_FPS, 30)
            
            print("✅ Cámara iniciada correctamente")
            return True
        except Exception as e:
            print(f"❌ Error al iniciar la cámara: {e}")
            return False
    
    def stop_camera(self):
        """Release the webcam and close windows."""
        if self.webcam:
            self.webcam.release()
        cv2.destroyAllWindows()
        print("📷 Cámara cerrada")
    
    def process_frame(self):
        """Process a single frame from the webcam."""
        if not self.webcam or not self.webcam.isOpened():
            return None
            
        success, image = self.webcam.read()
        if not success:
            return None
            
        # Flip the image horizontally for a mirror effect
        image = cv2.flip(image, 1)
        
        return image
    
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
    
    def draw_hand_landmarks(self, image):
        """Draw hand landmarks on the image."""
        if self.current_result and self.current_result.hand_landmarks:
            for hand_landmarks in self.current_result.hand_landmarks:
                # Convert normalized landmarks to pixel coordinates
                hand_landmarks_pixel = []
                for landmark in hand_landmarks:
                    x = int(landmark.x * image.shape[1])
                    y = int(landmark.y * image.shape[0])
                    hand_landmarks_pixel.append((x, y))
                
                # Draw landmarks
                for point in hand_landmarks_pixel:
                    cv2.circle(image, point, 3, (0, 255, 0), -1)
                
                # Draw connections between landmarks (simplified)
                connections = [
                    (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
                    (0, 5), (5, 6), (6, 7), (7, 8),  # Index finger
                    (0, 9), (9, 10), (10, 11), (11, 12),  # Middle finger
                    (0, 13), (13, 14), (14, 15), (15, 16),  # Ring finger
                    (0, 17), (17, 18), (18, 19), (19, 20),  # Pinky
                    (5, 9), (9, 13), (13, 17)  # Palm connections
                ]
                
                for connection in connections:
                    if connection[0] < len(hand_landmarks_pixel) and connection[1] < len(hand_landmarks_pixel):
                        cv2.line(image, hand_landmarks_pixel[connection[0]], 
                                hand_landmarks_pixel[connection[1]], (255, 0, 0), 2)
    
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
        """Run the volume control loop."""
        if not self.gesture_recognizer:
            print("❌ Error: Gesture Recognizer no está inicializado")
            return
            
        if not self.start_camera():
            print("❌ Error: No se pudo iniciar la cámara")
            return
        
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
                cv2.imshow('Control de Volumen por Gestos', image)
                
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


def main():
    """Main function to run the volume controller."""
    print("="*50)
    print("🔊 CONTROL DE VOLUMEN POR GESTOS")
    print("="*50)
    print("📋 Este programa usa gestos de mano para controlar")
    print("   el volumen del sistema operativo.")
    print()
    print("🖐️ GESTOS DISPONIBLES:")
    print("   👍 Pulgar arriba   → Subir volumen")
    print("   👎 Pulgar abajo    → Bajar volumen")
    print("   ✊ Puño cerrado    → Silenciar/Activar")
    print()
    print("⚙️ CONFIGURACIÓN:")
    print("   - Umbral de confianza: 70%")
    print("   - Delay entre acciones: 0.4 segundos")
    print("   - Soporte para 1 mano")
    print()
    
    try:
        controller = VolumeController()
        controller.run()
    except Exception as e:
        print(f"❌ Error al ejecutar el controlador: {e}")
        print("   Verifica que:")
        print("   1. La cámara esté disponible")
        print("   2. El modelo gesture_recognizer.task exista en models/")
        print("   3. Las dependencias estén instaladas correctamente")
    
    print("\n👋 ¡Gracias por usar el control de volumen!")


if __name__ == "__main__":
    main()