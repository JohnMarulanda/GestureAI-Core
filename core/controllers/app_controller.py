import cv2
import time
import subprocess
import psutil
import os
import threading
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class AppController:
    """Controller for opening and closing applications using MediaPipe predefined hand gestures."""
    
    def __init__(self, model_path=None):
        """Initialize the application controller with gesture recognition."""
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
        self.action_delay = 2.0  # General delay between actions (increased)
        self.close_delay = 5.0   # Longer delay for closing apps (safety)
        self.open_delay = 3.0    # Delay after opening before allowing close
        self.last_close_time = {}  # Track last close time per app
        self.last_open_time = {}   # Track last open time per app
        
        # Current gesture state
        self.last_gesture = None
        self.current_result = None
        self.confidence_threshold = 0.75  # Higher threshold for app control
        
        # Action status
        self.action_message = ""
        self.action_message_time = 0
        self.action_message_duration = 3.0
        
        # Application tracking
        self.running_apps = {}  # {app_name: process}
        
        # Gesture mapping for applications
        self.gesture_apps = {
            'Closed_Fist': 'Chrome',      # Puño cerrado → Chrome
            'Pointing_Up': 'Notepad',     # Dedo índice arriba → Notepad (más confiable que palma)
            'Victory': 'Calculator',      # Victoria (V) → Calculator
            'ILoveYou': 'Spotify'         # Te amo → Spotify
        }
        
        # Spanish translations for display
        self.gesture_names = {
            'Closed_Fist': 'Puño cerrado',
            'Pointing_Up': 'Dedo índice arriba',
            'Victory': 'Victoria (V)',
            'ILoveYou': 'Te amo (I Love You)'
        }
        
        # Application paths
        self.app_paths = {
            'Chrome': self._find_chrome_path(),
            'Notepad': 'notepad.exe',
            'Calculator': 'calc.exe',
            'Spotify': self._find_spotify_path()
        }
        
        # Application action counters
        self.action_counts = {
            'Chrome': {'opened': 0, 'closed': 0},
            'Notepad': {'opened': 0, 'closed': 0},
            'Calculator': {'opened': 0, 'closed': 0},
            'Spotify': {'opened': 0, 'closed': 0}
        }
        
        # Thread safety
        self.app_lock = threading.Lock()
        
        self._initialize_recognizer()
        print("✅ Controlador de Aplicaciones inicializado")
    
    def _find_chrome_path(self):
        """Find Chrome installation path."""
        possible_paths = [
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
            "chrome.exe"  # If in PATH
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return "chrome.exe"  # Fallback
    
    def _find_spotify_path(self):
        """Find Spotify installation path."""
        possible_paths = [
            os.path.expanduser("~\\AppData\\Roaming\\Spotify\\Spotify.exe"),
            "C:\\Users\\%USERNAME%\\AppData\\Roaming\\Spotify\\Spotify.exe",
            "spotify.exe"  # If in PATH
        ]
        
        for path in possible_paths:
            expanded_path = os.path.expandvars(path)
            if os.path.exists(expanded_path):
                return expanded_path
        
        return "spotify.exe"  # Fallback
    
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
                num_hands=1,  # Only one hand for app control
                min_hand_detection_confidence=0.7,
                min_hand_presence_confidence=0.7,
                min_tracking_confidence=0.7
            )
            
            # Create the gesture recognizer
            self.gesture_recognizer = vision.GestureRecognizer.create_from_options(options)
            print("✅ Gesture Recognizer para control de aplicaciones inicializado")
            
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
                        
                        # Only process app control gestures with good confidence
                        if (gesture_name in self.gesture_apps and 
                            confidence >= self.confidence_threshold):
                            
                            current_time = time.time()
                            self.last_gesture = gesture_name
                            
                            # Check if enough time has passed since last action
                            if current_time - self.last_action_time > self.action_delay:
                                app_name = self.gesture_apps[gesture_name]
                                
                                # Check if app is running to determine action
                                is_running = self._is_app_running(app_name)
                                
                                if is_running:
                                    # App is running, try to close it
                                    # Check close delay for this specific app
                                    last_close = self.last_close_time.get(app_name, 0)
                                    last_open = self.last_open_time.get(app_name, 0)
                                    
                                    # Ensure enough time has passed since opening AND since last close
                                    if (current_time - last_close > self.close_delay and 
                                        current_time - last_open > self.open_delay):
                                        threading.Thread(
                                            target=self._close_application,
                                            args=(app_name, gesture_name, confidence),
                                            daemon=True
                                        ).start()
                                        self.last_close_time[app_name] = current_time
                                        self.last_action_time = current_time
                                else:
                                    # App is not running, open it
                                    threading.Thread(
                                        target=self._open_application,
                                        args=(app_name, gesture_name, confidence),
                                        daemon=True
                                    ).start()
                                    self.last_open_time[app_name] = current_time
                                    self.last_action_time = current_time
                
        except Exception as e:
            print(f"⚠️ Error en callback de gestos: {e}")
    
    def _is_app_running(self, app_name):
        """Check if an application is currently running."""
        try:
            # Check our tracked processes first
            if app_name in self.running_apps:
                try:
                    process = self.running_apps[app_name]
                    if process.is_running():
                        return True
                    else:
                        del self.running_apps[app_name]
                except:
                    del self.running_apps[app_name]
            
            # Check system processes
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    proc_name = proc.info['name'].lower()
                    if app_name.lower() in proc_name:
                        return True
                except:
                    continue
            
            return False
        except Exception as e:
            print(f"⚠️ Error verificando si {app_name} está ejecutándose: {e}")
            return False
    
    def _open_application(self, app_name, gesture_name, confidence):
        """Open the specified application."""
        with self.app_lock:
            try:
                app_path = self.app_paths.get(app_name)
                if not app_path:
                    self._set_action_message(f"❌ Ruta no configurada para {app_name}")
                    return False
                
                # Check if app is already running
                if self._is_app_running(app_name):
                    self._set_action_message(f"ℹ️ {app_name} ya está ejecutándose")
                    return True
                
                # Open the application
                process = subprocess.Popen(app_path, shell=True)
                self.running_apps[app_name] = psutil.Process(process.pid)
                
                # Update counters
                self.action_counts[app_name]['opened'] += 1
                
                gesture_display = self.gesture_names[gesture_name]
                self._set_action_message(f"✅ Abriendo {app_name}")
                print(f"🚀 {gesture_display} (Confianza: {confidence:.2f}) - Abriendo {app_name}")
                return True
                
            except Exception as e:
                self._set_action_message(f"❌ Error abriendo {app_name}: {str(e)}")
                print(f"❌ Error abriendo {app_name}: {e}")
                return False
    
    def _close_application(self, app_name, gesture_name, confidence):
        """Close the specified application."""
        with self.app_lock:
            try:
                # Try to close tracked process first
                if app_name in self.running_apps:
                    try:
                        process = self.running_apps[app_name]
                        if process.is_running():
                            process.terminate()
                            time.sleep(0.5)  # Give it time to close
                            if process.is_running():
                                process.kill()  # Force kill if needed
                        del self.running_apps[app_name]
                    except Exception as e:
                        print(f"⚠️ Error cerrando proceso rastreado: {e}")
                        del self.running_apps[app_name]
                
                # Try to find and close by process name
                found = False
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        proc_name = proc.info['name'].lower()
                        if app_name.lower() in proc_name:
                            proc.terminate()
                            found = True
                    except Exception as e:
                        continue
                
                if found:
                    # Update counters
                    self.action_counts[app_name]['closed'] += 1
                    
                    gesture_display = self.gesture_names[gesture_name]
                    self._set_action_message(f"🔴 Cerrando {app_name}")
                    print(f"🔴 {gesture_display} (Confianza: {confidence:.2f}) - Cerrando {app_name}")
                    return True
                else:
                    self._set_action_message(f"ℹ️ {app_name} no está ejecutándose")
                    return False
                    
            except Exception as e:
                self._set_action_message(f"❌ Error cerrando {app_name}: {str(e)}")
                print(f"❌ Error cerrando {app_name}: {e}")
                return False
    
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
    
    def draw_app_info(self, image):
        """Draw application control information on the image."""
        try:
            height, width, _ = image.shape
            
            # Draw background rectangle for text
            cv2.rectangle(image, (10, 10), (width - 10, 280), (0, 0, 0), -1)
            cv2.rectangle(image, (10, 10), (width - 10, 280), (255, 255, 255), 2)
            
            # Draw title
            cv2.putText(image, "Control de Aplicaciones por Gestos", 
                       (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Draw gesture instructions
            y_pos = 65
            instructions = [
                "✊ Puño cerrado: Chrome (abrir/cerrar)",
                "☝️ Dedo índice arriba: Notepad (abrir/cerrar)",
                "✌️ Victoria (V): Calculator (abrir/cerrar)",
                "🤟 Te amo: Spotify (abrir/cerrar)"
            ]
            
            for instruction in instructions:
                cv2.putText(image, instruction, (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                y_pos += 25
            
            # Draw current gesture
            if self.last_gesture:
                gesture_display = self.gesture_names.get(self.last_gesture, self.last_gesture)
                app_name = self.gesture_apps.get(self.last_gesture, "Desconocida")
                cv2.putText(image, f"Gesto: {gesture_display} -> {app_name}", 
                           (20, y_pos + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            
            # Draw delay status
            current_time = time.time()
            y_delay_pos = y_pos + 50
            
            # General action delay
            action_remaining = max(0, self.action_delay - (current_time - self.last_action_time))
            if action_remaining > 0:
                cv2.putText(image, f"Accion disponible en: {action_remaining:.1f}s", 
                           (20, y_delay_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 100, 100), 1)
                y_delay_pos += 20
            
            # Close delays for each app
            for app_name in self.gesture_apps.values():
                if app_name in self.last_close_time:
                    close_remaining = max(0, self.close_delay - (current_time - self.last_close_time[app_name]))
                    if close_remaining > 0:
                        cv2.putText(image, f"Cerrar {app_name} en: {close_remaining:.1f}s", 
                                   (20, y_delay_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 100, 100), 1)
                        y_delay_pos += 20
                
                # Show open delay (prevents immediate closing after opening)
                if app_name in self.last_open_time:
                    open_remaining = max(0, self.open_delay - (current_time - self.last_open_time[app_name]))
                    if open_remaining > 0:
                        cv2.putText(image, f"Protección {app_name}: {open_remaining:.1f}s", 
                                   (20, y_delay_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 255, 100), 1)
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
    
    def draw_app_status(self, image):
        """Display application status on the right side."""
        try:
            height, width, _ = image.shape
            
            # Draw background for status
            status_x = width - 250
            cv2.rectangle(image, (status_x, 10), (width - 10, 200), (0, 0, 0), -1)
            cv2.rectangle(image, (status_x, 10), (width - 10, 200), (255, 255, 255), 2)
            
            # Draw status title
            cv2.putText(image, "Estado de Apps", 
                       (status_x + 10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            y_pos = 60
            for app_name in self.gesture_apps.values():
                is_running = self._is_app_running(app_name)
                status_text = "ACTIVA" if is_running else "CERRADA"
                status_color = (0, 255, 0) if is_running else (0, 0, 255)
                
                cv2.putText(image, f"{app_name}: {status_text}", 
                           (status_x + 10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, status_color, 1)
                y_pos += 25
            
        except Exception as e:
            print(f"⚠️ Error al dibujar estado de apps: {e}")
    
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
        """Print application control statistics."""
        print("\n" + "="*50)
        print("📊 ESTADÍSTICAS DE CONTROL DE APLICACIONES")
        print("="*50)
        
        total_opened = sum(app['opened'] for app in self.action_counts.values())
        total_closed = sum(app['closed'] for app in self.action_counts.values())
        
        for app_name, counts in self.action_counts.items():
            print(f"{app_name:<12} | Abierta: {counts['opened']:>2} | Cerrada: {counts['closed']:>2}")
        
        print("-"*50)
        print(f"{'Total abierto':<12} | {total_opened:>2}")
        print(f"{'Total cerrado':<12} | {total_closed:>2}")
        print(f"{'Apps rastreadas':<12} | {len(self.running_apps):>2}")
        print("="*50 + "\n")
    
    def run(self):
        """Run the application control loop."""
        if not self.gesture_recognizer:
            print("❌ Error: Gesture Recognizer no está inicializado")
            return
            
        if not self.start_camera():
            print("❌ Error: No se pudo iniciar la cámara")
            return
        
        print("\n🚀 Iniciando control de aplicaciones por gestos...")
        print("Gestos disponibles:")
        print("  ✊ Puño cerrado → Chrome (abrir/cerrar)")
        print("  ☝️ Dedo índice arriba → Notepad (abrir/cerrar)")
        print("  ✌️ Victoria (V) → Calculator (abrir/cerrar)")
        print("  🤟 Te amo → Spotify (abrir/cerrar)")
        print("\n🎮 Controla tus aplicaciones con gestos naturales")
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
                
                # Draw application control information
                self.draw_app_info(image)
                
                # Draw application status
                self.draw_app_status(image)
                
                # Draw hand landmarks
                self.draw_hand_landmarks(image)
                
                # Display the image
                cv2.imshow('Control de Aplicaciones por Gestos', image)
                
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
            print("👋 Control de aplicaciones finalizado")


def main():
    """Main function to run the application controller."""
    print("="*50)
    print("🚀 CONTROL DE APLICACIONES POR GESTOS")
    print("="*50)
    print("📋 Este programa usa gestos de mano para abrir y")
    print("   cerrar aplicaciones automáticamente.")
    print()
    print("🖐️ GESTOS DISPONIBLES:")
    print("   ✊ Puño cerrado      → Chrome (abrir/cerrar)")
    print("   ☝️ Dedo índice arriba → Notepad (abrir/cerrar)")
    print("   ✌️ Victoria (V)      → Calculator (abrir/cerrar)")
    print("   🤟 Te amo            → Spotify (abrir/cerrar)")
    print()
    print("⚙️ CONFIGURACIÓN:")
    print("   - Umbral de confianza: 75%")
    print("   - Delay general: 2.0 segundos")
    print("   - Delay cerrar: 5.0 segundos (seguridad)")
    print("   - Delay protección: 3.0 segundos (después de abrir)")
    print("   - Soporte para 1 mano")
    print("   - Detección automática de estado de apps")
    print("   - Mismo gesto para abrir y cerrar")
    print("   - Protección contra cierres accidentales")
    print()
    
    try:
        controller = AppController()
        controller.run()
    except Exception as e:
        print(f"❌ Error al ejecutar el controlador: {e}")
        print("   Verifica que:")
        print("   1. La cámara esté disponible")
        print("   2. El modelo gesture_recognizer.task exista en models/")
        print("   3. Las dependencias estén instaladas correctamente")
        print("   4. Las aplicaciones estén instaladas en el sistema")
    
    print("\n👋 ¡Gracias por usar el control de aplicaciones!")


if __name__ == "__main__":
    main()