import cv2
import pyautogui
import time
import threading
import mediapipe as mp
import os
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class MultimediaController:
    """Controller for multimedia operations using MediaPipe predefined hand gestures."""
    
    def __init__(self, model_path=None):
        """Initialize the multimedia controller with gesture recognition."""
        # Set default model path if not provided
        if model_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            model_path = os.path.join(project_root, 'models', 'gesture_recognizer.task')
        
        self.model_path = model_path
        self.webcam = None
        self.gesture_recognizer = None
        self.last_action_time = 0
        self.action_delay = 0.4  # Delay between multimedia actions
        
        # Specific delays for different action types
        self.last_mute_time = 0
        self.last_play_pause_time = 0
        self.mute_delay = 1.5      # Longer delay for mute toggle
        self.play_pause_delay = 1.5 # Longer delay for play/pause toggle
        
        # Specific delays for different action types
        self.last_mute_time = 0
        self.last_play_pause_time = 0
        self.mute_delay = 1.5      # Longer delay for mute toggle
        self.play_pause_delay = 1.5 # Longer delay for play/pause toggle
        
        # Initialize volume control using pycaw
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.volume = cast(interface, POINTER(IAudioEndpointVolume))
            self.volume_range = self.volume.GetVolumeRange()
            self.volume_available = True
            print("✅ Control de volumen inicializado")
        except Exception as e:
            print(f"⚠️ Error al inicializar control de volumen: {e}")
            self.volume = None
            self.volume_available = False
        
        # Multimedia control state
        self.last_gesture = None
        self.current_result = None
        self.confidence_threshold = 0.7  # Threshold for multimedia gestures
        
        # Action status
        self.action_message = ""
        self.action_message_time = 0
        self.action_message_duration = 2.0
        
        # Gesture mapping for multimedia control
        self.gesture_actions = {
            'Thumb_Up': 'forward',      # Thumb up for forward/next
            'Thumb_Down': 'backward',   # Thumb down for backward/previous
            'Closed_Fist': 'mute',      # Closed fist for mute toggle
            'ILoveYou': 'play_pause'    # I Love You for play/pause
        }
        
        # Spanish translations for display
        self.gesture_names = {
            'Thumb_Up': 'Adelantar (Pulgar arriba)',
            'Thumb_Down': 'Retroceder (Pulgar abajo)',
            'Closed_Fist': 'Silenciar (Puño)',
            'ILoveYou': 'Pausar/Reproducir (Te amo)'
        }
        
        # Action descriptions
        self.action_descriptions = {
            'forward': 'Adelantar/Siguiente',
            'backward': 'Retroceder/Anterior',
            'mute': 'Silenciar/Activar',
            'play_pause': 'Pausar/Reproducir'
        }
        
        # Multimedia action counters
        self.action_counts = {
            'forward': 0,
            'backward': 0,
            'mute': 0,
            'play_pause': 0
        }
        
        # Thread safety
        self.multimedia_lock = threading.Lock()
        
        self._initialize_recognizer()
        print("✅ Controlador Multimedia inicializado")
    
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
                num_hands=1,  # Only one hand for multimedia control
                min_hand_detection_confidence=0.7,
                min_hand_presence_confidence=0.7,
                min_tracking_confidence=0.7
            )
            
            # Create the gesture recognizer
            self.gesture_recognizer = vision.GestureRecognizer.create_from_options(options)
            print("✅ Gesture Recognizer para control multimedia inicializado")
            
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
                        
                        # Only process multimedia control gestures with good confidence
                        if (gesture_name in self.gesture_actions and 
                            confidence >= self.confidence_threshold):
                            
                            current_time = time.time()
                            self.last_gesture = gesture_name
                            
                            # Handle gestures with specific delays
                            action = self.gesture_actions[gesture_name]
                            can_execute = False
                            
                            if action == 'mute':
                                # Check specific delay for mute
                                if current_time - self.last_mute_time > self.mute_delay:
                                    can_execute = True
                            elif action == 'play_pause':
                                # Check specific delay for play/pause
                                if current_time - self.last_play_pause_time > self.play_pause_delay:
                                    can_execute = True
                            else:
                                # Use general delay for other actions
                                if current_time - self.last_action_time > self.action_delay:
                                    can_execute = True
                            
                            if can_execute:
                                threading.Thread(
                                    target=self._perform_multimedia_action,
                                    args=(gesture_name, confidence),
                                    daemon=True
                                ).start()
                                
                                # Update specific timers
                                if action == 'mute':
                                    self.last_mute_time = current_time
                                elif action == 'play_pause':
                                    self.last_play_pause_time = current_time
                                else:
                                    self.last_action_time = current_time
                
        except Exception as e:
            print(f"⚠️ Error en callback de gestos: {e}")
    
    def _perform_multimedia_action(self, gesture_name, confidence):
        """Perform the multimedia action based on the detected gesture."""
        with self.multimedia_lock:
            try:
                action = self.gesture_actions[gesture_name]
                gesture_display = self.gesture_names[gesture_name]
                
                if action == 'forward':
                    # Forward/Next track
                    pyautogui.press('right')
                    self.action_counts['forward'] += 1
                    self._set_action_message("⏭️ Adelantar/Siguiente")
                    print(f"⏭️ {gesture_display} (Confianza: {confidence:.2f}) - Adelantar")
                    
                elif action == 'backward':
                    # Backward/Previous track
                    pyautogui.press('left')
                    self.action_counts['backward'] += 1
                    self._set_action_message("⏮️ Retroceder/Anterior")
                    print(f"⏮️ {gesture_display} (Confianza: {confidence:.2f}) - Retroceder")
                    
                elif action == 'mute':
                    # Mute toggle
                    if self.volume_available:
                        is_muted = self.volume.GetMute()
                        self.volume.SetMute(not is_muted, None)
                        mute_status = "Silenciado" if not is_muted else "Audio activado"
                        self.action_counts['mute'] += 1
                        self._set_action_message(f"🔇 {mute_status}")
                        print(f"🔇 {gesture_display} (Confianza: {confidence:.2f}) - {mute_status}")
                    else:
                        print("⚠️ Control de volumen no disponible")
                        
                elif action == 'play_pause':
                    # Play/Pause toggle
                    pyautogui.press('space')
                    self.action_counts['play_pause'] += 1
                    self._set_action_message("⏯️ Pausar/Reproducir")
                    print(f"⏯️ {gesture_display} (Confianza: {confidence:.2f}) - Pausar/Reproducir")
                    
            except Exception as e:
                print(f"❌ Error al ejecutar acción multimedia: {e}")
    
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
    
    def draw_multimedia_info(self, image):
        """Draw multimedia control information on the image."""
        try:
            height, width, _ = image.shape
            
            # Draw background rectangle for text
            cv2.rectangle(image, (10, 10), (width - 10, 240), (0, 0, 0), -1)
            cv2.rectangle(image, (10, 10), (width - 10, 240), (255, 255, 255), 2)
            
            # Draw title
            cv2.putText(image, "Control Multimedia por Gestos", 
                       (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Draw gesture instructions
            y_pos = 65
            instructions = [
                "👍 Pulgar arriba: Adelantar/Siguiente",
                "👎 Pulgar abajo: Retroceder/Anterior",
                "✊ Puño: Silenciar/Activar audio",
                "🤟 Te amo: Pausar/Reproducir"
            ]
            
            for instruction in instructions:
                cv2.putText(image, instruction, (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                y_pos += 25
            
            # Draw current gesture
            if self.last_gesture:
                gesture_display = self.gesture_names.get(self.last_gesture, self.last_gesture)
                cv2.putText(image, f"Gesto: {gesture_display}", 
                           (20, y_pos + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            
            # Draw delay status for mute and play/pause
            current_time = time.time()
            y_delay_pos = y_pos + 50
            
            # Mute delay status
            mute_remaining = max(0, self.mute_delay - (current_time - self.last_mute_time))
            if mute_remaining > 0:
                cv2.putText(image, f"Silenciar disponible en: {mute_remaining:.1f}s", 
                           (20, y_delay_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 100, 100), 1)
                y_delay_pos += 20
            
            # Play/pause delay status
            play_pause_remaining = max(0, self.play_pause_delay - (current_time - self.last_play_pause_time))
            if play_pause_remaining > 0:
                cv2.putText(image, f"Pausar disponible en: {play_pause_remaining:.1f}s", 
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
    
    def draw_volume_bar(self, image):
        """Display a volume level bar."""
        try:
            if not self.volume_available:
                return
                
            current_volume = self.volume.GetMasterVolumeLevelScalar()
            volume_percent = int(current_volume * 100)
            is_muted = self.volume.GetMute()
            
            bar_width = 200
            bar_height = 20
            bar_x = image.shape[1] - bar_width - 20
            bar_y = 50
            
            # Draw background bar
            cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), 
                          (100, 100, 100), -1)
            
            # Draw filled volume bar (red if muted, green if not)
            filled_width = int(bar_width * current_volume)
            bar_color = (0, 0, 255) if is_muted else (0, 255, 0)
            cv2.rectangle(image, (bar_x, bar_y), (bar_x + filled_width, bar_y + bar_height), 
                          bar_color, -1)
            
            # Draw volume percentage text
            mute_text = " (MUTE)" if is_muted else ""
            cv2.putText(image, f"Volumen: {volume_percent}%{mute_text}", (bar_x, bar_y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        except Exception as e:
            print(f"⚠️ Error al dibujar barra de volumen: {e}")
    
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
        """Print multimedia control statistics."""
        print("\n" + "="*50)
        print("📊 ESTADÍSTICAS DE CONTROL MULTIMEDIA")
        print("="*50)
        total_actions = sum(self.action_counts.values())
        
        print(f"{'Adelantar':<20} | {self.action_counts['forward']:>3} veces")
        print(f"{'Retroceder':<20} | {self.action_counts['backward']:>3} veces")
        print(f"{'Silenciar':<20} | {self.action_counts['mute']:>3} veces")
        print(f"{'Pausar/Reproducir':<20} | {self.action_counts['play_pause']:>3} veces")
        
        print("-"*50)
        print(f"{'Total de acciones':<20} | {total_actions:>3}")
        print(f"{'Audio disponible':<20} | {'SÍ' if self.volume_available else 'NO':>3}")
        print("="*50 + "\n")
    
    def run(self):
        """Run the multimedia control loop."""
        if not self.gesture_recognizer:
            print("❌ Error: Gesture Recognizer no está inicializado")
            return
            
        if not self.start_camera():
            print("❌ Error: No se pudo iniciar la cámara")
            return
        
        print("\n🎵 Iniciando control multimedia por gestos...")
        print("Gestos disponibles:")
        print("  👍 Pulgar arriba → Adelantar/Siguiente")
        print("  👎 Pulgar abajo → Retroceder/Anterior")
        print("  ✊ Puño → Silenciar/Activar audio")
        print("  🤟 Te amo → Pausar/Reproducir")
        print("\n🎮 Controla tu multimedia con gestos naturales")
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
                
                # Draw multimedia control information
                self.draw_multimedia_info(image)
                
                # Draw volume bar
                self.draw_volume_bar(image)
                
                # Draw hand landmarks
                self.draw_hand_landmarks(image)
                
                # Display the image
                cv2.imshow('Control Multimedia por Gestos', image)
                
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
            print("👋 Control multimedia finalizado")


def main():
    """Main function to run the multimedia controller."""
    print("="*50)
    print("🎵 CONTROL MULTIMEDIA POR GESTOS")
    print("="*50)
    print("📋 Este programa usa gestos de mano para controlar")
    print("   la reproducción multimedia.")
    print()
    print("🖐️ GESTOS DISPONIBLES:")
    print("   👍 Pulgar arriba   → Adelantar/Siguiente")
    print("   👎 Pulgar abajo    → Retroceder/Anterior")
    print("   ✊ Puño            → Silenciar/Activar audio")
    print("   🤟 Te amo          → Pausar/Reproducir")
    print()
    print("⚙️ CONFIGURACIÓN:")
    print("   - Umbral de confianza: 70%")
    print("   - Delay navegación: 0.4 segundos")
    print("   - Delay silenciar: 1.5 segundos")
    print("   - Delay pausar: 1.5 segundos")
    print("   - Soporte para 1 mano")
    print("   - Gestos simples y directos")
    print("   - Control de volumen integrado")
    print()
    
    try:
        controller = MultimediaController()
        controller.run()
    except Exception as e:
        print(f"❌ Error al ejecutar el controlador: {e}")
        print("   Verifica que:")
        print("   1. La cámara esté disponible")
        print("   2. El modelo gesture_recognizer.task exista en models/")
        print("   3. Las dependencias estén instaladas correctamente")
        print("   4. pycaw esté instalado para control de volumen")
    
    print("\n👋 ¡Gracias por usar el control multimedia!")


if __name__ == "__main__":
    main()