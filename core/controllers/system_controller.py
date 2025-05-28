import cv2
import time
import subprocess
import ctypes
import threading
import mediapipe as mp
import os
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class SystemController:
    """Controller for system operations using MediaPipe predefined hand gestures."""
    
    def __init__(self, model_path=None):
        """Initialize the system control controller with gesture recognition."""
        # Set default model path if not provided
        if model_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            model_path = os.path.join(project_root, 'models', 'gesture_recognizer.task')
        
        self.model_path = model_path
        self.webcam = None
        self.gesture_recognizer = None
        self.last_action_time = 0
        self.action_delay = 1.0  # Longer delay for system actions (safety)
        
        # System control state
        self.last_gesture = None
        self.current_result = None
        self.confidence_threshold = 0.8  # Higher threshold for system actions (safety)
        
        # Special thresholds for specific gestures
        self.gesture_thresholds = {
            'Victory': 0.8,      # High threshold for lock
            'Closed_Fist': 0.85, # Highest threshold for shutdown
            'Open_Palm': 0.6,    # Lower threshold for better palm detection
            'Pointing_Up': 0.75  # Medium-high threshold for restart
        }
        
        # Gesture tracking for confirmation
        self.gesture_hold_time = {}
        self.required_hold_duration = 3.0  # 3 seconds to hold gesture before action
        self.confirmation_active = False
        self.confirmation_action = None
        self.confirmation_gesture = None
        self.countdown_start_time = 0
        self.countdown_duration = 5.0  # 5 seconds countdown for confirmation
        
        # Action status
        self.action_message = ""
        self.action_message_time = 0
        self.action_message_duration = 3.0
        
        # Gesture mapping for system control
        self.gesture_actions = {
            'Victory': 'lock',        # Victory gesture for lock
            'Closed_Fist': 'shutdown', # Closed fist for shutdown
            'Open_Palm': 'sleep',     # Open palm for sleep
            'Pointing_Up': 'restart'  # Pointing up for restart
        }
        
        # Spanish translations for display
        self.gesture_names = {
            'Victory': 'Bloquear (Victoria)',
            'Closed_Fist': 'Apagar (Puño)',
            'Open_Palm': 'Suspender (Palma)',
            'Pointing_Up': 'Reiniciar (Señalar)'
        }
        
        # Action descriptions
        self.action_descriptions = {
            'lock': 'Bloquear pantalla',
            'shutdown': 'Apagar sistema',
            'sleep': 'Suspender sistema',
            'restart': 'Reiniciar sistema'
        }
        
        # System action counters
        self.action_counts = {
            'lock': 0,
            'shutdown': 0,
            'sleep': 0,
            'restart': 0
        }
        
        # Thread safety
        self.system_lock = threading.Lock()
        
        self._initialize_recognizer()
        print("✅ Controlador de Sistema inicializado")
    
    def _initialize_recognizer(self):
        """Initialize the MediaPipe Gesture Recognizer."""
        try:
            if not os.path.exists(self.model_path):
                print(f"❌ Modelo no encontrado: {self.model_path}")
                self.gesture_recognizer = None
                return
            
            # Configure base options
            base_options = python.BaseOptions(model_asset_path=self.model_path)
            
            # Configure gesture recognizer options with optimized settings
            options = vision.GestureRecognizerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.LIVE_STREAM,
                result_callback=self._gesture_result_callback,
                num_hands=1,  # Only one hand for system control
                min_hand_detection_confidence=0.7,  # Slightly lower for better detection
                min_hand_presence_confidence=0.7,   # Slightly lower for better detection
                min_tracking_confidence=0.7         # Slightly lower for better detection
            )
            
            # Create the gesture recognizer
            self.gesture_recognizer = vision.GestureRecognizer.create_from_options(options)
            print("✅ Gesture Recognizer para control de sistema inicializado")
            print(f"📊 Umbrales configurados:")
            for gesture, threshold in self.gesture_thresholds.items():
                action = self.gesture_actions[gesture]
                print(f"   {gesture}: {threshold*100:.0f}% → {self.action_descriptions[action]}")
            
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
                        
                        # Use specific threshold for each gesture
                        required_confidence = self.gesture_thresholds.get(gesture_name, self.confidence_threshold)
                        
                        # Only process system control gestures with appropriate confidence
                        if (gesture_name in self.gesture_actions and 
                            confidence >= required_confidence):
                            
                            current_time = time.time()
                            self.last_gesture = gesture_name
                            
                            # Track gesture hold time
                            if gesture_name not in self.gesture_hold_time:
                                self.gesture_hold_time[gesture_name] = current_time
                            
                            hold_duration = current_time - self.gesture_hold_time[gesture_name]
                            
                            # If gesture held long enough and not in confirmation, start confirmation
                            if (hold_duration >= self.required_hold_duration and 
                                not self.confirmation_active and
                                current_time - self.last_action_time > self.action_delay):
                                
                                self._start_confirmation(gesture_name, confidence)
                                self.gesture_hold_time[gesture_name] = current_time  # Reset hold time
                            
                            # If in confirmation and same gesture detected, execute action
                            elif (self.confirmation_active and 
                                  gesture_name == self.confirmation_gesture and
                                  hold_duration >= 1.0):  # 1 second confirmation hold
                                
                                threading.Thread(
                                    target=self._perform_system_action,
                                    args=(gesture_name, confidence),
                                    daemon=True
                                ).start()
                                self._cancel_confirmation()
                                self.last_action_time = current_time
                        else:
                            # Reset hold time for gestures not being held
                            if gesture_name in self.gesture_hold_time:
                                del self.gesture_hold_time[gesture_name]
            else:
                # No gestures detected, reset all hold times
                self.gesture_hold_time.clear()
                
        except Exception as e:
            print(f"⚠️ Error en callback de gestos: {e}")
    
    def _start_confirmation(self, gesture_name, confidence):
        """Start the confirmation process for system actions."""
        with self.system_lock:
            self.confirmation_active = True
            self.confirmation_gesture = gesture_name
            self.confirmation_action = self.gesture_actions[gesture_name]
            self.countdown_start_time = time.time()
            
            action_name = self.action_descriptions[self.confirmation_action]
            gesture_display = self.gesture_names[gesture_name]
            print(f"⚠️ CONFIRMACIÓN: {action_name}")
            print(f"   Mantén el gesto {gesture_display} para confirmar")
            print(f"   Confianza: {confidence:.2f}")
    
    def _cancel_confirmation(self):
        """Cancel the confirmation process."""
        with self.system_lock:
            if self.confirmation_active:
                print("❌ Confirmación cancelada")
            self.confirmation_active = False
            self.confirmation_gesture = None
            self.confirmation_action = None
    
    def _perform_system_action(self, gesture_name, confidence):
        """Perform the system action based on the detected gesture."""
        with self.system_lock:
            try:
                action = self.gesture_actions[gesture_name]
                gesture_display = self.gesture_names[gesture_name]
                action_name = self.action_descriptions[action]
                
                print(f"🔧 Ejecutando: {action_name}")
                print(f"   Gesto: {gesture_display} (Confianza: {confidence:.2f})")
                
                self.action_message = f"Ejecutando: {action_name}"
                self.action_message_time = time.time()
                
                if action == 'lock':
                    self._lock_computer()
                    self.action_counts['lock'] += 1
                    
                elif action == 'shutdown':
                    self._shutdown_computer()
                    self.action_counts['shutdown'] += 1
                    
                elif action == 'sleep':
                    self._sleep_computer()
                    self.action_counts['sleep'] += 1
                    
                elif action == 'restart':
                    self._restart_computer()
                    self.action_counts['restart'] += 1
                    
            except Exception as e:
                print(f"❌ Error al ejecutar acción del sistema: {e}")
                self.action_message = f"Error: {e}"
                self.action_message_time = time.time()
    
    def _lock_computer(self):
        """Lock the computer screen."""
        try:
            print("🔒 Bloqueando pantalla...")
            ctypes.windll.user32.LockWorkStation()
            print("✅ Pantalla bloqueada")
        except Exception as e:
            print(f"❌ Error al bloquear pantalla: {e}")
    
    def _shutdown_computer(self):
        """Shutdown the computer."""
        try:
            print("⚡ Apagando sistema en 5 segundos...")
            subprocess.call(['shutdown', '/s', '/t', '5'])
            print("✅ Comando de apagado enviado")
        except Exception as e:
            print(f"❌ Error al apagar sistema: {e}")
    
    def _sleep_computer(self):
        """Put the computer to sleep mode."""
        try:
            print("😴 Suspendiendo sistema...")
            subprocess.call([
                'powershell', '-Command', 
                'Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState("Suspend", $false, $false)'
            ])
            print("✅ Sistema suspendido")
        except Exception as e:
            print(f"❌ Error al suspender sistema: {e}")
    
    def _restart_computer(self):
        """Restart the computer."""
        try:
            print("🔄 Reiniciando sistema...")
            subprocess.call(['shutdown', '/r', '/t', '0'])
            print("✅ Comando de reinicio enviado")
        except Exception as e:
            print(f"❌ Error al reiniciar sistema: {e}")
    
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
    
    def draw_system_info(self, image):
        """Draw system control information on the image."""
        try:
            height, width, _ = image.shape
            
            # Draw background rectangle for text
            cv2.rectangle(image, (10, 10), (width - 10, 280), (0, 0, 0), -1)
            cv2.rectangle(image, (10, 10), (width - 10, 280), (255, 255, 255), 2)
            
            # Draw title
            cv2.putText(image, "Control de Sistema por Gestos", 
                       (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Draw gesture instructions
            y_pos = 65
            instructions = [
                "✌️ Victoria: Bloquear pantalla (3s)",
                "✊ Puño: Apagar sistema (3s)",
                "🖐️ Palma: Suspender sistema (3s)",
                "👆 Señalar: Reiniciar sistema (3s)"
            ]
            
            for instruction in instructions:
                cv2.putText(image, instruction, (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                y_pos += 25
            
            # Draw current gesture and hold progress
            if self.last_gesture and self.last_gesture in self.gesture_hold_time:
                current_time = time.time()
                hold_duration = current_time - self.gesture_hold_time[self.last_gesture]
                progress = min(hold_duration / self.required_hold_duration, 1.0)
                
                gesture_display = self.gesture_names.get(self.last_gesture, self.last_gesture)
                cv2.putText(image, f"Detectando: {gesture_display}", 
                           (20, y_pos + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
                
                # Draw progress bar
                bar_width = 200
                bar_height = 15
                bar_x = 20
                bar_y = y_pos + 35
                
                # Bar outline
                cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (255, 255, 255), 1)
                
                # Bar fill
                filled_width = int(bar_width * progress)
                bar_color = (0, 255, 0) if progress < 1.0 else (0, 255, 255)
                cv2.rectangle(image, (bar_x, bar_y), (bar_x + filled_width, bar_y + bar_height), bar_color, -1)
                
                # Progress text
                cv2.putText(image, f"Progreso: {int(progress * 100)}%", 
                           (bar_x, bar_y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            
            # Draw hands detected count
            hands_count = len(self.current_result.hand_landmarks) if self.current_result and self.current_result.hand_landmarks else 0
            cv2.putText(image, f"Manos detectadas: {hands_count}", 
                       (20, y_pos + 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Draw action message
            if self.action_message and time.time() - self.action_message_time < self.action_message_duration:
                cv2.putText(image, self.action_message, 
                           (20, y_pos + 95), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
            
            # Draw exit instruction
            cv2.putText(image, "Presiona ESC para salir", 
                       (20, y_pos + 120), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
                       
        except Exception as e:
            print(f"⚠️ Error al dibujar información: {e}")
    
    def draw_confirmation_dialog(self, image):
        """Draw confirmation dialog for system actions."""
        try:
            if self.confirmation_active:
                height, width, _ = image.shape
                
                # Create semi-transparent overlay
                overlay = image.copy()
                cv2.rectangle(overlay, (50, 50), (width - 50, height - 50), (0, 0, 0), -1)
                alpha = 0.8
                cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0, image)
                
                # Draw confirmation border
                cv2.rectangle(image, (50, 50), (width - 50, height - 50), (0, 0, 255), 3)
                
                # Display confirmation message
                action_name = self.action_descriptions[self.confirmation_action]
                gesture_display = self.gesture_names[self.confirmation_gesture]
                
                cv2.putText(image, f"CONFIRMAR: {action_name.upper()}", 
                           (100, height // 2 - 80), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
                
                cv2.putText(image, f"Mantén el gesto {gesture_display}", 
                           (100, height // 2 - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                cv2.putText(image, "por 1 segundo para confirmar", 
                           (100, height // 2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                cv2.putText(image, "Cualquier otro gesto cancela", 
                           (100, height // 2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            
            # Display countdown
                elapsed = time.time() - self.countdown_start_time
                remaining = max(0, self.countdown_duration - elapsed)
                
                if remaining <= 0:
                    self._cancel_confirmation()
                else:
                    cv2.putText(image, f"Auto-cancelar en: {int(remaining)}s", 
                               (100, height // 2 + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    
        except Exception as e:
            print(f"⚠️ Error al dibujar confirmación: {e}")
    
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
        """Print system control statistics."""
        print("\n" + "="*50)
        print("📊 ESTADÍSTICAS DE CONTROL DE SISTEMA")
        print("="*50)
        total_actions = sum(self.action_counts.values())
        
        print(f"{'Bloqueos':<20} | {self.action_counts['lock']:>3} veces")
        print(f"{'Apagados':<20} | {self.action_counts['shutdown']:>3} veces")
        print(f"{'Suspensiones':<20} | {self.action_counts['sleep']:>3} veces")
        print(f"{'Reinicios':<20} | {self.action_counts['restart']:>3} veces")
        
        print("-"*50)
        print(f"{'Total de acciones':<20} | {total_actions:>3}")
        print("="*50 + "\n")
    
    def run(self):
        """Run the system control loop."""
        if not self.gesture_recognizer:
            print("❌ Error: Gesture Recognizer no está inicializado")
            return
            
        if not self.start_camera():
            print("❌ Error: No se pudo iniciar la cámara")
            return
        
        print("\n🔧 Iniciando control de sistema por gestos...")
        print("⚠️ ADVERTENCIA: Este programa puede ejecutar acciones del sistema")
        print("Gestos disponibles:")
        print("  ✌️ Victoria → Bloquear pantalla")
        print("  ✊ Puño cerrado → Apagar sistema")
        print("  🖐️ Palma abierta → Suspender sistema")
        print("  👆 Señalar: Reiniciar sistema")
        print("\n🔒 Mantén cada gesto por 3 segundos para activar")
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
                
                # Draw system control information
                self.draw_system_info(image)
                
                # Draw confirmation dialog if active
                self.draw_confirmation_dialog(image)
                
                            # Draw hand landmarks
                self.draw_hand_landmarks(image)
                
                # Display the image
                cv2.imshow('Control de Sistema por Gestos', image)
                
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
            print("👋 Control de sistema finalizado")


def main():
    """Main function to run the system controller."""
    print("="*50)
    print("🔧 CONTROL DE SISTEMA POR GESTOS")
    print("="*50)
    print("⚠️ ADVERTENCIA: Este programa puede ejecutar acciones")
    print("   críticas del sistema como apagar o bloquear.")
    print()
    print("🖐️ GESTOS DISPONIBLES:")
    print("   ✌️ Victoria      → Bloquear pantalla")
    print("   ✊ Puño cerrado  → Apagar sistema")
    print("   🖐️ Palma abierta → Suspender sistema")
    print("   👆 Señalar: Reiniciar sistema")
    print()
    print("🔒 SISTEMA DE SEGURIDAD:")
    print("   - Mantén el gesto por 3 segundos")
    print("   - Confirmación visual requerida")
    print("   - Auto-cancelación en 5 segundos")
    print("   - Umbral de confianza: 80%")
    print()
    print("⚙️ CONFIGURACIÓN:")
    print("   - Soporte para 1 mano")
    print("   - Detección de alta precisión")
    print("   - Confirmación obligatoria")
    print()
    
    try:
        controller = SystemController()
        controller.run()
    except Exception as e:
        print(f"❌ Error al ejecutar el controlador: {e}")
        print("   Verifica que:")
        print("   1. La cámara esté disponible")
        print("   2. El modelo gesture_recognizer.task exista en models/")
        print("   3. Las dependencias estén instaladas correctamente")
        print("   4. Tengas permisos de administrador si es necesario")
    
    print("\n👋 ¡Gracias por usar el control de sistema!")


if __name__ == "__main__":
    main() 