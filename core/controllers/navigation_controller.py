import cv2
import pyautogui
import time
import threading
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import os

class NavigationController:
    """Controller for window navigation using MediaPipe predefined hand gestures."""
    
    def __init__(self, model_path=None):
        """Initialize the navigation controller with gesture recognition."""
        # Set default model path if not provided
        if model_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            model_path = os.path.join(project_root, 'models', 'gesture_recognizer.task')
        
        self.model_path = model_path
        self.webcam = None
        self.gesture_recognizer = None
        
        # Gesture timing and delays
        self.last_action_time = 0
        self.action_delay = 1.0  # Delay between navigation actions
        
        # Current gesture state
        self.last_gesture = None
        self.current_result = None
        self.confidence_threshold = 0.75  # High threshold for navigation
        
        # Action status
        self.action_message = ""
        self.action_message_time = 0
        self.action_message_duration = 2.0
        
        # Gesture mapping for navigation
        self.gesture_actions = {
            'Victory': 'win_tab_open',         # Victoria (V) → Abrir Win+Tab
            'ILoveYou': 'minimize',            # Te amo → Minimizar
            'Closed_Fist': 'maximize',         # Puño cerrado → Maximizar
            'Pointing_Up': 'close_window',     # Señalando arriba → Cerrar ventana
            'Thumb_Up': 'switch_desktop'       # Pulgar arriba → Cambiar escritorio
        }
        
        # Special gesture detection for Victory + Thumb (custom detection)
        self.victory_with_thumb_detected = False
        self.last_victory_with_thumb_time = 0
        
        # Spanish translations for display
        self.gesture_names = {
            'Victory': 'Victoria (V)',
            'ILoveYou': 'Te amo (I Love You)',
            'Closed_Fist': 'Puño cerrado',
            'Pointing_Up': 'Señalando hacia arriba',
            'Thumb_Up': 'Pulgar hacia arriba'
        }
        
        # Action descriptions
        self.action_descriptions = {
            'win_tab_open': 'Abrir Win+Tab',
            'win_tab_navigate': 'Navegar Win+Tab',
            'minimize': 'Minimizar ventana',
            'maximize': 'Maximizar ventana',
            'close_window': 'Cerrar ventana',
            'switch_desktop': 'Cambiar escritorio'
        }
        
        # Navigation action counters
        self.action_counts = {
            'win_tab_open': 0,
            'win_tab_navigate': 0,
            'minimize': 0,
            'maximize': 0,
            'close_window': 0,
            'switch_desktop': 0
        }
        
        # Thread safety
        self.navigation_lock = threading.Lock()
        
        self._initialize_recognizer()
        print("✅ Controlador de Navegación inicializado")
    
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
                num_hands=1,  # Only one hand for navigation
                min_hand_detection_confidence=0.7,
                min_hand_presence_confidence=0.7,
                min_tracking_confidence=0.7
            )
            
            # Create the gesture recognizer
            self.gesture_recognizer = vision.GestureRecognizer.create_from_options(options)
            print("✅ Gesture Recognizer para navegación inicializado")
            
        except Exception as e:
            print(f"❌ Error al inicializar Gesture Recognizer: {e}")
            self.gesture_recognizer = None
    
    def _detect_victory_with_thumb(self, hand_landmarks):
        """Detect if Victory gesture has thumb extended (custom detection)."""
        try:
            if not hand_landmarks:
                return False
            
            # Get landmark positions
            landmarks = hand_landmarks[0]  # First hand
            
            # Check if index and middle fingers are extended (Victory base)
            index_tip = landmarks[8]
            index_pip = landmarks[6]
            middle_tip = landmarks[12]
            middle_pip = landmarks[10]
            
            # Check if ring and pinky are folded
            ring_tip = landmarks[16]
            ring_pip = landmarks[14]
            pinky_tip = landmarks[20]
            pinky_pip = landmarks[18]
            
            # Check if thumb is extended
            thumb_tip = landmarks[4]
            thumb_ip = landmarks[3]
            
            # Victory conditions: index and middle up, ring and pinky down
            index_up = index_tip.y < index_pip.y
            middle_up = middle_tip.y < middle_pip.y
            ring_down = ring_tip.y > ring_pip.y
            pinky_down = pinky_tip.y > pinky_pip.y
            
            # Thumb extended condition (compare with thumb IP joint)
            thumb_extended = thumb_tip.x > thumb_ip.x  # Assuming right hand
            
            # Victory + Thumb = all conditions met
            return index_up and middle_up and ring_down and pinky_down and thumb_extended
            
        except Exception as e:
            return False
    
    def _gesture_result_callback(self, result: vision.GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int):
        """Callback function to handle gesture recognition results."""
        try:
            self.current_result = result
            
            if result.gestures and result.hand_landmarks:
                for hand_gesture in result.gestures:
                    if hand_gesture:
                        gesture = hand_gesture[0]  # Get the top gesture
                        gesture_name = gesture.category_name
                        confidence = gesture.score
                        
                        current_time = time.time()
                        
                        # Special handling for Victory gesture
                        if gesture_name == 'Victory' and confidence >= self.confidence_threshold:
                            # Check if it's Victory + Thumb
                            if self._detect_victory_with_thumb(result.hand_landmarks):
                                # Victory + Thumb detected
                                if current_time - self.last_victory_with_thumb_time > self.action_delay:
                                    threading.Thread(
                                        target=self._perform_navigation_action,
                                        args=('Victory_Thumb', confidence),
                                        daemon=True
                                    ).start()
                                    self.last_victory_with_thumb_time = current_time
                                    self.last_action_time = current_time
                                self.last_gesture = 'Victory_Thumb'
                            else:
                                # Regular Victory
                                if current_time - self.last_action_time > self.action_delay:
                                    threading.Thread(
                                        target=self._perform_navigation_action,
                                        args=(gesture_name, confidence),
                                        daemon=True
                                    ).start()
                                    self.last_action_time = current_time
                                self.last_gesture = gesture_name
                        
                        # Handle other gestures normally
                        elif (gesture_name in self.gesture_actions and 
                              confidence >= self.confidence_threshold):
                            
                            self.last_gesture = gesture_name
                            
                            # Check if enough time has passed since last action
                            if current_time - self.last_action_time > self.action_delay:
                                threading.Thread(
                                    target=self._perform_navigation_action,
                                    args=(gesture_name, confidence),
                                    daemon=True
                                ).start()
                                self.last_action_time = current_time
                
        except Exception as e:
            print(f"⚠️ Error en callback de gestos: {e}")
    
    def _perform_navigation_action(self, gesture_name, confidence):
        """Perform the navigation action based on the detected gesture."""
        with self.navigation_lock:
            try:
                # Handle special Victory + Thumb gesture
                if gesture_name == 'Victory_Thumb':
                    # Victory + Thumb → Navigate Task View
                    pyautogui.hotkey('win', 'tab')
                    time.sleep(0.1)  # Small delay to ensure Win+Tab opens
                    pyautogui.press('right')
                    self.action_counts['win_tab_navigate'] += 1
                    self._set_action_message("🔄 Navegar Win+Tab")
                    print(f"🔄 Victoria + Pulgar (Confianza: {confidence:.2f}) - Navegar Win+Tab")
                    return
                
                # Handle regular gestures
                action = self.gesture_actions[gesture_name]
                gesture_display = self.gesture_names[gesture_name]
                action_description = self.action_descriptions[action]
                
                if action == 'win_tab_open':
                    # Regular Victory → Open Task View only
                    pyautogui.hotkey('win', 'tab')
                    self.action_counts['win_tab_open'] += 1
                    self._set_action_message("📋 Abrir Win+Tab")
                    print(f"📋 {gesture_display} (Confianza: {confidence:.2f}) - {action_description}")
                    
                elif action == 'minimize':
                    # Minimize window
                    pyautogui.hotkey('win', 'down')
                    self.action_counts['minimize'] += 1
                    self._set_action_message("⬇️ Minimizar ventana")
                    print(f"⬇️ {gesture_display} (Confianza: {confidence:.2f}) - {action_description}")
                    
                elif action == 'maximize':
                    # Maximize window
                    pyautogui.hotkey('win', 'up')
                    self.action_counts['maximize'] += 1
                    self._set_action_message("⬆️ Maximizar ventana")
                    print(f"⬆️ {gesture_display} (Confianza: {confidence:.2f}) - {action_description}")
                    
                elif action == 'close_window':
                    # Close window
                    pyautogui.hotkey('alt', 'f4')
                    self.action_counts['close_window'] += 1
                    self._set_action_message("❌ Cerrar ventana")
                    print(f"❌ {gesture_display} (Confianza: {confidence:.2f}) - {action_description}")
                    
                elif action == 'switch_desktop':
                    # Switch desktop (Virtual Desktop)
                    pyautogui.hotkey('ctrl', 'win', 'right')
                    self.action_counts['switch_desktop'] += 1
                    self._set_action_message("🖥️ Cambiar escritorio")
                    print(f"🖥️ {gesture_display} (Confianza: {confidence:.2f}) - {action_description}")
                    
            except Exception as e:
                print(f"❌ Error al ejecutar acción de navegación: {e}")
    
    def _set_action_message(self, message):
        """Set the action message to display on screen."""
        self.action_message = message
        self.action_message_time = time.time()
    
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
            self.webcam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
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
    
    def draw_navigation_info(self, image):
        """Draw navigation control information on the image."""
        try:
            height, width, _ = image.shape
            
            # Draw background rectangle for text
            cv2.rectangle(image, (10, 10), (width - 10, 280), (0, 0, 0), -1)
            cv2.rectangle(image, (10, 10), (width - 10, 280), (255, 255, 255), 2)
            
            # Draw title
            cv2.putText(image, "Control de Navegacion por Gestos", 
                       (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Draw gesture instructions
            y_pos = 65
            instructions = [
                "✌️ Victoria (V): Abrir Win+Tab",
                "✌️👍 Victoria + Pulgar: Navegar Win+Tab",
                "🤟 Te amo: Minimizar ventana",
                "✊ Puño cerrado: Maximizar ventana",
                "☝️ Señalar arriba: Cerrar ventana",
                "👍 Pulgar arriba: Cambiar escritorio"
            ]
            
            for instruction in instructions:
                cv2.putText(image, instruction, (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                y_pos += 25
            
            # Draw current gesture
            if self.last_gesture:
                if self.last_gesture == 'Victory_Thumb':
                    gesture_display = "Victoria + Pulgar"
                    action_desc = "Navegar Win+Tab"
                else:
                    gesture_display = self.gesture_names.get(self.last_gesture, self.last_gesture)
                    action = self.gesture_actions.get(self.last_gesture, "Desconocida")
                    action_desc = self.action_descriptions.get(action, "Desconocida")
                cv2.putText(image, f"Gesto: {gesture_display} -> {action_desc}", 
                           (20, y_pos + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            
            # Draw delay status
            current_time = time.time()
            y_delay_pos = y_pos + 60
            
            # Action delay
            action_remaining = max(0, self.action_delay - (current_time - self.last_action_time))
            if action_remaining > 0:
                cv2.putText(image, f"Accion disponible en: {action_remaining:.1f}s", 
                           (20, y_delay_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 100, 100), 1)
                y_delay_pos += 20
            
            # Draw hands detected count
            hands_count = len(self.current_result.hand_landmarks) if self.current_result and self.current_result.hand_landmarks else 0
            cv2.putText(image, f"Manos detectadas: {hands_count}", 
                       (20, y_delay_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Draw action message
            if self.action_message and time.time() - self.action_message_time < self.action_message_duration:
                cv2.putText(image, self.action_message, 
                           (20, y_delay_pos + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # Draw exit instruction
            cv2.putText(image, "Presiona ESC para salir", 
                       (20, y_delay_pos + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
                       
        except Exception as e:
            print(f"⚠️ Error al dibujar información: {e}")
    
    def draw_statistics(self, image):
        """Display navigation statistics on the right side."""
        try:
            height, width, _ = image.shape
            
            # Draw background for statistics
            stats_x = width - 280
            cv2.rectangle(image, (stats_x, 10), (width - 10, 200), (0, 0, 0), -1)
            cv2.rectangle(image, (stats_x, 10), (width - 10, 200), (255, 255, 255), 2)
            
            # Draw statistics title
            cv2.putText(image, "Estadisticas", 
                       (stats_x + 10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            y_pos = 60
            for action, count in self.action_counts.items():
                if action in self.action_descriptions:
                    action_name = self.action_descriptions[action]
                else:
                    action_name = action.replace('_', ' ').title()
                cv2.putText(image, f"{action_name}: {count}", 
                           (stats_x + 10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                y_pos += 20
            
            # Total actions
            total_actions = sum(self.action_counts.values())
            cv2.putText(image, f"Total: {total_actions}", 
                       (stats_x + 10, y_pos + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
            
        except Exception as e:
            print(f"⚠️ Error al dibujar estadísticas: {e}")
    
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
                    
                    # Draw key connections
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
        """Print navigation control statistics."""
        print("\n" + "="*50)
        print("📊 ESTADÍSTICAS DE CONTROL DE NAVEGACIÓN")
        print("="*50)
        
        total_actions = sum(self.action_counts.values())
        
        for action, count in self.action_counts.items():
            action_name = self.action_descriptions[action]
            percentage = (count / total_actions * 100) if total_actions > 0 else 0
            print(f"{action_name:<25} | {count:>3} veces ({percentage:>5.1f}%)")
        
        print("-"*50)
        print(f"{'Total de acciones':<25} | {total_actions:>3}")
        print("="*50 + "\n")
    
    def run(self):
        """Run the navigation control loop."""
        if not self.gesture_recognizer:
            print("❌ Error: Gesture Recognizer no está inicializado")
            return
            
        if not self.start_camera():
            print("❌ Error: No se pudo iniciar la cámara")
            return
        
        print("\n🧭 Iniciando control de navegación por gestos...")
        print("Gestos disponibles:")
        print("  ✌️ Victoria (V) → Abrir Win+Tab")
        print("  ✌️👍 Victoria + Pulgar → Navegar Win+Tab")
        print("  🤟 Te amo → Minimizar ventana")
        print("  ✊ Puño cerrado → Maximizar ventana")
        print("  ☝️ Señalar arriba → Cerrar ventana")
        print("  👍 Pulgar arriba → Cambiar escritorio")
        print("\n🎮 Controla tu navegación con gestos naturales")
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
                
                # Draw navigation control information
                self.draw_navigation_info(image)
                
                # Draw statistics
                self.draw_statistics(image)
                
                # Draw hand landmarks
                self.draw_hand_landmarks(image)
                
                # Display the image
                cv2.imshow('Control de Navegacion por Gestos', image)
                
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
            print("👋 Control de navegación finalizado")


def main():
    """Main function to run the navigation controller."""
    print("="*50)
    print("🧭 CONTROL DE NAVEGACIÓN POR GESTOS")
    print("="*50)
    print("📋 Este programa usa gestos de mano para controlar")
    print("   la navegación de ventanas y escritorios.")
    print()
    print("🖐️ GESTOS DISPONIBLES:")
    print("   ✌️ Victoria (V)         → Abrir Win+Tab")
    print("   ✌️👍 Victoria + Pulgar   → Navegar Win+Tab")
    print("   🤟 Te amo               → Minimizar ventana")
    print("   ✊ Puño cerrado         → Maximizar ventana")
    print("   ☝️ Señalar arriba       → Cerrar ventana")
    print("   👍 Pulgar arriba        → Cambiar escritorio")
    print()
    print("⚙️ CONFIGURACIÓN:")
    print("   - Umbral de confianza: 75%")
    print("   - Delay entre acciones: 1.0 segundos")
    print("   - Soporte para 1 mano")
    print("   - Gestos naturales y precisos")
    print("   - Estadísticas en tiempo real")
    print()
    
    try:
        controller = NavigationController()
        controller.run()
    except Exception as e:
        print(f"❌ Error al ejecutar el controlador: {e}")
        print("   Verifica que:")
        print("   1. La cámara esté disponible")
        print("   2. El modelo gesture_recognizer.task exista en models/")
        print("   3. Las dependencias estén instaladas correctamente")
        print("   4. pyautogui esté instalado para control de ventanas")
    
    print("\n👋 ¡Gracias por usar el control de navegación!")


if __name__ == "__main__":
    main()