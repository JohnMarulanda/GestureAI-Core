import cv2
import screen_brightness_control as sbc
import mediapipe as mp
import os
import time
import threading
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class BrightnessController:
    """Controller for adjusting screen brightness using MediaPipe predefined hand gestures."""
    
    def __init__(self, model_path=None):
        """Initialize the brightness controller with gesture recognition."""
        # Set default model path if not provided
        if model_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            model_path = os.path.join(project_root, 'models', 'gesture_recognizer.task')
        
        self.model_path = model_path
        self.webcam = None
        self.gesture_recognizer = None
        self.last_action_time = 0
        self.action_delay = 0.3  # Reduced delay for faster response (was 0.5)
        
        # Brightness control state
        self.last_gesture = None
        self.current_result = None
        self.confidence_threshold = 0.7  # Slightly lower threshold for more responsive detection (was 0.75)
        
        # Initialize brightness system
        self.brightness_available = self._initialize_brightness()
        
        # Gesture mapping for brightness control
        self.gesture_actions = {
            'Thumb_Up': 'brightness_up',
            'Thumb_Down': 'brightness_down'
        }
        
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
        
        # Brightness control configuration - Increased steps for faster changes
        self.brightness_steps = 15  # Increased from 10 to 15 for faster changes
        
        # Thread safety
        self.brightness_lock = threading.Lock()
        
        self._initialize_recognizer()
    
    def _initialize_brightness(self):
        """Initialize and test brightness control system."""
        try:
            # Test if we can get brightness
            monitors = sbc.list_monitors()
            print(f"📺 Monitores detectados: {len(monitors)}")
            
            if not monitors:
                print("⚠️ No se detectaron monitores compatibles")
                self.current_brightness = 50
                return False
            
            # Try to get current brightness
            brightness_values = sbc.get_brightness()
            if brightness_values:
                self.current_brightness = brightness_values[0]
                print(f"✅ Brillo actual: {self.current_brightness}%")
                
                # Test if we can set brightness
                test_brightness = self.current_brightness
                sbc.set_brightness(test_brightness)
                print("✅ Control de brillo funcional")
                return True
            else:
                print("⚠️ No se pudo obtener el brillo actual")
                self.current_brightness = 50
                return False
                
        except Exception as e:
            print(f"❌ Error al inicializar control de brillo: {e}")
            print("💡 Intentando método alternativo...")
            
            # Try alternative method
            try:
                import subprocess
                # For Windows, try using powershell
                result = subprocess.run([
                    'powershell', 
                    '(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness'
                ], capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0 and result.stdout.strip():
                    self.current_brightness = int(result.stdout.strip())
                    print(f"✅ Brillo obtenido via WMI: {self.current_brightness}%")
                    return True
                else:
                    self.current_brightness = 50
                    return False
            except Exception as e2:
                print(f"❌ Método alternativo falló: {e2}")
                self.current_brightness = 50
                return False
    
    def _initialize_recognizer(self):
        """Initialize the MediaPipe Gesture Recognizer."""
        try:
            if not os.path.exists(self.model_path):
                print(f"❌ Modelo no encontrado: {self.model_path}")
                self.gesture_recognizer = None
                return
            
            # Configure base options
            base_options = python.BaseOptions(model_asset_path=self.model_path)
            
            # Configure gesture recognizer options
            options = vision.GestureRecognizerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.LIVE_STREAM,
                result_callback=self._gesture_result_callback,
                num_hands=1,  # Only one hand for brightness control
                min_hand_detection_confidence=0.7,
                min_hand_presence_confidence=0.7,
                min_tracking_confidence=0.7
            )
            
            # Create the gesture recognizer
            self.gesture_recognizer = vision.GestureRecognizer.create_from_options(options)
            print("✅ Gesture Recognizer para control de brillo inicializado")
            
        except Exception as e:
            print(f"❌ Error al inicializar Gesture Recognizer: {e}")
            self.gesture_recognizer = None
    
    def _gesture_result_callback(self, result: vision.GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int):
        """Callback function to handle gesture recognition results."""
        try:
            self.current_result = result
            
            if result.gestures:
                for hand_gesture in result.gestures:
                    if hand_gesture:
                        gesture = hand_gesture[0]  # Get the top gesture
                        gesture_name = gesture.category_name
                        confidence = gesture.score
                        
                        # Only process brightness control gestures with high confidence
                        if (gesture_name in self.gesture_actions and 
                            confidence >= self.confidence_threshold):
                            
                            current_time = time.time()
                            if current_time - self.last_action_time > self.action_delay:
                                self.last_gesture = gesture_name
                                # Use threading to avoid blocking the callback
                                threading.Thread(
                                    target=self._perform_brightness_action,
                                    args=(gesture_name, confidence),
                                    daemon=True
                                ).start()
                                self.last_action_time = current_time
        except Exception as e:
            print(f"⚠️ Error en callback de gestos: {e}")
    
    def _perform_brightness_action(self, gesture_name, confidence):
        """Perform the brightness action based on the detected gesture."""
        with self.brightness_lock:
            try:
                action = self.gesture_actions[gesture_name]
                gesture_display = self.gesture_names[gesture_name]
                
                if not self.brightness_available:
                    print(f"⚠️ {gesture_display} detectado pero control de brillo no disponible")
                    return
                
                if action == 'brightness_up':
                    # Increase brightness
                    new_brightness = min(100, self.current_brightness + self.brightness_steps)
                    if new_brightness != self.current_brightness:
                        if self._set_brightness_safe(new_brightness):
                            self.current_brightness = new_brightness
                            self.action_counts['brightness_up'] += 1
                            print(f"☀️ {gesture_display} (Confianza: {confidence:.2f}) - Brillo: ↑ (+{self.brightness_steps}%) → {self.current_brightness}%")
                        else:
                            print(f"❌ Error al subir brillo")
                
                elif action == 'brightness_down':
                    # Decrease brightness
                    new_brightness = max(10, self.current_brightness - self.brightness_steps)  # Minimum 10% to avoid black screen
            if new_brightness != self.current_brightness:
                        if self._set_brightness_safe(new_brightness):
                self.current_brightness = new_brightness
                            self.action_counts['brightness_down'] += 1
                            print(f"🌙 {gesture_display} (Confianza: {confidence:.2f}) - Brillo: ↓ (-{self.brightness_steps}%) → {self.current_brightness}%")
                        else:
                            print(f"❌ Error al bajar brillo")
                            
            except Exception as e:
                print(f"❌ Error al ejecutar acción de brillo: {e}")
    
    def _set_brightness_safe(self, brightness_value):
        """Safely set brightness with error handling."""
        try:
            # Method 1: Try screen_brightness_control
            sbc.set_brightness(brightness_value)
            return True
        except Exception as e1:
            print(f"⚠️ Método 1 falló: {e1}")
            
            try:
                # Method 2: Try with specific monitor
                monitors = sbc.list_monitors()
                if monitors:
                    sbc.set_brightness(brightness_value, display=monitors[0])
                    return True
            except Exception as e2:
                print(f"⚠️ Método 2 falló: {e2}")
                
                try:
                    # Method 3: Try Windows WMI (for Windows only)
                    import subprocess
                    subprocess.run([
                        'powershell', 
                        f'(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{brightness_value})'
                    ], capture_output=True, timeout=3)
                    return True
                except Exception as e3:
                    print(f"⚠️ Método 3 falló: {e3}")
                    return False
    
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
            self.webcam.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for lower latency
            
            print("✅ Cámara iniciada correctamente")
            return True
        except Exception as e:
            print(f"❌ Error al iniciar la cámara: {e}")
            return False
    
    def stop_camera(self):
        """Release the webcam and close windows."""
        try:
            if self.webcam:
                self.webcam.release()
            cv2.destroyAllWindows()
            print("📷 Cámara cerrada")
        except Exception as e:
            print(f"⚠️ Error al cerrar cámara: {e}")
    
    def process_frame(self):
        """Process a single frame from the webcam."""
        try:
            if not self.webcam or not self.webcam.isOpened():
                return None
                
            success, image = self.webcam.read()
            if not success:
                return None
                
            # Flip the image horizontally for a mirror effect
            image = cv2.flip(image, 1)
            
            return image
        except Exception as e:
            print(f"⚠️ Error al procesar frame: {e}")
            return None
    
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
            status_color = (0, 255, 0) if self.brightness_available else (0, 0, 255)
            status_text = "ACTIVO" if self.brightness_available else "NO DISPONIBLE"
            cv2.putText(image, f"Estado: {status_text}", 
                       (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 2)
            
            # Draw current brightness with visual bar
            cv2.putText(image, f"Brillo actual: {self.current_brightness}%", 
                       (20, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Draw brightness bar
        bar_width = 200
            bar_height = 15
            bar_x = 20
            bar_y = 95
        
            # Bar outline
            cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (255, 255, 255), 1)
        
            # Bar fill based on brightness level
        filled_width = int(bar_width * self.current_brightness / 100)
            bar_color = (0, 255, 255) if self.brightness_available else (100, 100, 100)
            cv2.rectangle(image, (bar_x, bar_y), (bar_x + filled_width, bar_y + bar_height), bar_color, -1)
            
            # Draw last detected gesture
            if self.last_gesture:
                gesture_display = self.gesture_names.get(self.last_gesture, self.last_gesture)
                cv2.putText(image, f"Ultimo gesto: {gesture_display}", 
                           (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
            # Draw hands detected count
            hands_count = len(self.current_result.hand_landmarks) if self.current_result and self.current_result.hand_landmarks else 0
            cv2.putText(image, f"Manos detectadas: {hands_count}", 
                       (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Draw gesture instructions
            y_pos = 175
            instructions = [
                f"👍 Pulgar arriba: Subir brillo (+{self.brightness_steps}%)",
                f"👎 Pulgar abajo: Bajar brillo (-{self.brightness_steps}%)"
            ]
            
            for instruction in instructions:
                cv2.putText(image, instruction, (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                y_pos += 20
            
            # Draw exit instruction
            cv2.putText(image, "Presiona ESC para salir", 
                       (20, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
                       
        except Exception as e:
            print(f"⚠️ Error al dibujar información: {e}")
    
    def draw_hand_landmarks(self, image):
        """Draw hand landmarks on the image."""
        try:
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
                    
                    # Draw key connections (simplified for performance)
                    key_connections = [
                        (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
                        (0, 5), (5, 6), (6, 7), (7, 8),  # Index finger
                        (0, 17), (5, 9), (9, 13), (13, 17)  # Key palm connections
                    ]
                    
                    for connection in key_connections:
                        if connection[0] < len(hand_landmarks_pixel) and connection[1] < len(hand_landmarks_pixel):
                            cv2.line(image, hand_landmarks_pixel[connection[0]], 
                                    hand_landmarks_pixel[connection[1]], (255, 0, 0), 2)
        except Exception as e:
            print(f"⚠️ Error al dibujar landmarks: {e}")
    
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
        print(f"{'Brillo final':<20} | {self.current_brightness:>3}%")
        print(f"{'Control disponible':<20} | {'SÍ' if self.brightness_available else 'NO':>3}")
        print("="*50 + "\n")
    
    def run(self):
        """Run the brightness control loop."""
        if not self.gesture_recognizer:
            print("❌ Error: Gesture Recognizer no está inicializado")
            return
            
        if not self.start_camera():
            print("❌ Error: No se pudo iniciar la cámara")
            return
            
        print("\n☀️ Iniciando control de brillo por gestos...")
        print("Gestos disponibles:")
        print("  👍 Pulgar hacia arriba → Subir brillo")
        print("  👎 Pulgar hacia abajo → Bajar brillo")
        
        if not self.brightness_available:
            print("\n⚠️ ADVERTENCIA: Control de brillo no disponible")
            print("   Los gestos se detectarán pero no cambiarán el brillo")
        
        print("\n💡 Usa los gestos frente a la cámara para controlar el brillo")
        print("   Presiona ESC para salir\n")
        
        try:
            frame_timestamp = 0
            frame_count = 0
            
            while True:
                image = self.process_frame()
                if image is None:
                    break
                
                frame_count += 1
                
                # Process every 2nd frame for better performance
                if frame_count % 2 == 0:
                    # Convert BGR to RGB for MediaPipe
                    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
                    
                    # Process the frame with gesture recognizer
                    if self.gesture_recognizer:
                        frame_timestamp += 66  # Approximately 15 FPS for gesture processing
                        try:
                            self.gesture_recognizer.recognize_async(mp_image, frame_timestamp)
                        except Exception as e:
                            print(f"⚠️ Error en reconocimiento: {e}")
                
                # Draw brightness control information on the image
                self.draw_brightness_info(image)
                
                # Draw hand landmarks
                self.draw_hand_landmarks(image)
                
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
            self.stop_camera()
            self.print_statistics()
            print("👋 Control de brillo finalizado")


def main():
    """Main function to run the brightness controller."""
    print("="*50)
    print("☀️ CONTROL DE BRILLO POR GESTOS")
    print("="*50)
    print("📋 Este programa usa gestos de mano para controlar")
    print("   el brillo de la pantalla.")
    print()
    print("🖐️ GESTOS DISPONIBLES:")
    print("   👍 Pulgar arriba   → Subir brillo")
    print("   👎 Pulgar abajo    → Bajar brillo")
    print()
    print("⚙️ CONFIGURACIÓN:")
    print("   - Umbral de confianza: 70%")
    print("   - Delay entre acciones: 0.3 segundos")
    print("   - Soporte para 1 mano")
    print("   - Pasos de brillo: 15% por gesto")
    print("   - Brillo mínimo: 10% (evita pantalla negra)")
    print()
    
    try:
        controller = BrightnessController()
        controller.run()
    except Exception as e:
        print(f"❌ Error al ejecutar el controlador: {e}")
        print("   Verifica que:")
        print("   1. La cámara esté disponible")
        print("   2. El modelo gesture_recognizer.task exista en models/")
        print("   3. Las dependencias estén instaladas correctamente")
        print("   4. screen_brightness_control esté instalado")
        print("   5. Tu sistema soporte control de brillo por software")
    
    print("\n👋 ¡Gracias por usar el control de brillo!")


if __name__ == "__main__":
    main()