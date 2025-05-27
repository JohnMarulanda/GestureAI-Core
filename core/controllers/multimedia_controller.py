import cv2
import pyautogui
import time
import threading
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from core.gesture_recognition_manager import GestureRecognitionManager
from config import settings

class MultimediaController:
    """
    Controlador multimedia para realizar operaciones de medios usando gestos.
    
    Este controlador permite controlar la reproducción de medios, volumen,
    navegación y silencio mediante gestos de la mano.
    """
    
    def __init__(self):
        """
        Inicializa el controlador multimedia y prepara la configuración necesaria.
        """
        # Obtener la instancia del gesture manager
        self.gesture_manager = GestureRecognitionManager()
        
        # Variables de estado
        self.running = False
        self.display_thread = None
        self.lock = threading.Lock()
        
        # Estado de gestos
        self.active_gestures = {}
        self.gesture_messages = {}
        self.current_gesture = None
        self.gesture_start_time = 0
        self.gesture_duration = 0
        
        # Configuración desde settings
        self.required_duration = settings.MULTIMEDIA_GESTURE_DURATION
        self.action_cooldown = settings.MULTIMEDIA_ACTION_COOLDOWN
        self.volume_change_threshold = settings.MULTIMEDIA_VOLUME_CHANGE_THRESHOLD
        self.swipe_threshold = settings.MULTIMEDIA_SWIPE_THRESHOLD
        self.message_duration = settings.MULTIMEDIA_MESSAGE_DURATION
        
        # Inicializar control de volumen del sistema
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(interface, POINTER(IAudioEndpointVolume))
        
        # Seguimiento de posiciones de la mano
        self.hand_positions = []
        self.position_history_size = 10
        self.last_action_time = 0
        
        # Definir gestos y sus acciones correspondientes
        self.gestures = {
            "Play/Pause": "Palm (mano abierta)",
            "Volume": "Point (dedo índice)",
            "Navigation": "Victory (dedos V)",
            "Mute": "Fist (puño cerrado)"
        }
        
        print("Multimedia controller initialized")
    
    def detect_finger_states(self, hand_landmarks):
        """
        Detecta el estado de los dedos (extendido o no) y devuelve una lista de 0s y 1s.
        
        Args:
            hand_landmarks: Los landmarks de la mano detectada.
            
        Returns:
            list: Lista de 5 valores (0 o 1) representando el estado de cada dedo.
        """
        fingertips = [4, 8, 12, 16, 20]  # Thumb, index, middle, ring, pinky
        finger_states = []
        
        # Verificar cada dedo
        for tip_id in fingertips:
            # Para el pulgar, comparar coordenada x con la base del pulgar
            if tip_id == 4:
                if hand_landmarks.landmark[tip_id].x < hand_landmarks.landmark[tip_id - 2].x:
                    finger_states.append(1)  # Extendido
                else:
                    finger_states.append(0)  # No extendido
            # Para otros dedos, comparar coordenada y con la articulación media
            else:
                if hand_landmarks.landmark[tip_id].y < hand_landmarks.landmark[tip_id - 2].y:
                    finger_states.append(1)  # Extendido
                else:
                    finger_states.append(0)  # No extendido
        
        return finger_states
    
    def identify_gesture(self, finger_states):
        """
        Identifica qué gesto se está realizando basado en los estados de los dedos.
        
        Args:
            finger_states: Lista de estados de los dedos.
            
        Returns:
            str: Nombre del gesto identificado o None si no se reconoce.
        """
        if finger_states == [1, 1, 1, 1, 1]:  # Palm
            return "Play/Pause"
        elif finger_states == [0, 1, 0, 0, 0]:  # Point
            return "Volume"
        elif finger_states == [0, 1, 1, 0, 0]:  # Victory
            return "Navigation"
        elif finger_states == [0, 0, 0, 0, 0]:  # Fist
            return "Mute"
        return None
    
    def detect_vertical_movement(self):
        """
        Detecta movimiento vertical de la mano para control de volumen.
        
        Returns:
            str o None: 'volume_up', 'volume_down', o None si no hay movimiento significativo.
        """
        if len(self.hand_positions) < self.position_history_size:
            return None
        
        start_y = self.hand_positions[0][1]
        end_y = self.hand_positions[-1][1]
        movement_y = end_y - start_y
        
        if movement_y > self.volume_change_threshold:
            return "volume_down"
        elif movement_y < -self.volume_change_threshold:
            return "volume_up"
        
        return None
    
    def detect_swipe(self):
        """
        Detecta gestos de deslizamiento horizontal para navegación.
        
        Returns:
            str o None: 'swipe_right', 'swipe_left', o None si no hay movimiento significativo.
        """
        if len(self.hand_positions) < self.position_history_size:
            return None
        
        start_x = self.hand_positions[0][0]
        end_x = self.hand_positions[-1][0]
        movement_x = end_x - start_x
        
        if movement_x > self.swipe_threshold:
            return "swipe_right"
        elif movement_x < -self.swipe_threshold:
            return "swipe_left"
        
        return None
    
    def perform_action(self, action):
        """
        Ejecuta la acción multimedia correspondiente.
        
        Args:
            action: Nombre de la acción a ejecutar.
        """
        if action == "play_pause":
            pyautogui.press('space')
            self.set_message("Play/Pause")
        elif action == "swipe_right":
            pyautogui.press('right')
            self.set_message("Siguiente/Adelante")
        elif action == "swipe_left":
            pyautogui.press('left')
            self.set_message("Anterior/Atrás")
        elif action == "volume_up":
            current_volume = self.volume.GetMasterVolumeLevelScalar()
            new_volume = min(1.0, current_volume + 0.05)
            self.volume.SetMasterVolumeLevelScalar(new_volume, None)
            volume_percent = int(new_volume * 100)
            self.set_message(f"Volumen: {volume_percent}%")
        elif action == "volume_down":
            current_volume = self.volume.GetMasterVolumeLevelScalar()
            new_volume = max(0.0, current_volume - 0.05)
            self.volume.SetMasterVolumeLevelScalar(new_volume, None)
            volume_percent = int(new_volume * 100)
            self.set_message(f"Volumen: {volume_percent}%")
        elif action == "mute":
            is_muted = self.volume.GetMute()
            self.volume.SetMute(not is_muted, None)
            self.set_message("Silencio Activado" if not is_muted else "Silencio Desactivado")
        
        self.last_action_time = time.time()
    
    def set_message(self, message):
        """
        Establece un mensaje temporal para mostrar en pantalla.
        
        Args:
            message: Mensaje a mostrar.
        """
        with self.lock:
            self.gesture_messages["action"] = message
            threading.Timer(self.message_duration, lambda: self.remove_message("action")).start()
        print(message)
    
    def remove_message(self, message_id):
        """
        Elimina un mensaje específico.
        
        Args:
            message_id: Identificador del mensaje a eliminar.
        """
        with self.lock:
            if message_id in self.gesture_messages:
                del self.gesture_messages[message_id]
    
    def display_instructions(self, frame):
        """
        Muestra la lista de gestos disponibles y sus funciones.
        
        Args:
            frame: Frame donde mostrar las instrucciones.
        """
        y_pos = 30
        cv2.putText(frame, "CONTROLES MULTIMEDIA:", (10, y_pos), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        y_pos += 30
        for action, description in self.gestures.items():
            cv2.putText(frame, f"{action}: {description}", (10, y_pos), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_pos += 25
    
    def display_landmarks(self, frame):
        """
        Muestra los landmarks de la mano y el estado de los dedos.
        
        Args:
            frame: Frame donde mostrar los landmarks.
        """
        with self.lock:
            # Obtener el frame actual y los resultados de MediaPipe
            _, results = self.gesture_manager.process_frame()
            
            if results and results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Dibujar las conexiones entre landmarks
                    self.gesture_manager.drawing_utils.draw_landmarks(
                        frame,
                        hand_landmarks,
                        self.gesture_manager.mp_hands.HAND_CONNECTIONS)
                    
                    # Detectar y mostrar estados de los dedos
                    finger_states = self.detect_finger_states(hand_landmarks)
                    finger_state_str = "".join([str(s) for s in finger_states])
                    cv2.putText(frame, f"Gesture: {finger_state_str}", 
                                (10, frame.shape[0] - 90), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    
                    # Identificar gesto
                    gesture = self.identify_gesture(finger_states)
                    if gesture:
                        cv2.putText(frame, f"Detected: {gesture}", 
                                    (10, frame.shape[0] - 60), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
                    # Dibujar los puntos de los landmarks
                    for i, landmark in enumerate(hand_landmarks.landmark):
                        x = int(landmark.x * frame.shape[1])
                        y = int(landmark.y * frame.shape[0])
                        
                        # Dibujar círculo para cada landmark
                        cv2.circle(frame, (x, y), 3, (0, 255, 0), -1)
                        
                        # Resaltar las puntas de los dedos
                        if i in [4, 8, 12, 16, 20]:  # Thumb, Index, Middle, Ring, Pinky tips
                            cv2.circle(frame, (x, y), 6, (255, 0, 0), -1)
                            cv2.putText(frame, str(i), (x + 10, y), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
    
    def display_volume_bar(self, frame):
        """
        Muestra la barra de volumen en el frame.
        
        Args:
            frame: Frame donde mostrar la barra de volumen.
        """
        try:
            current_volume = self.volume.GetMasterVolumeLevelScalar()
            volume_percent = int(current_volume * 100)
            
            bar_width = 200
            bar_height = 20
            bar_x = frame.shape[1] - bar_width - 20
            bar_y = 50
            
            # Dibujar barra de fondo
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), 
                          (100, 100, 100), -1)
            
            # Dibujar barra de volumen
            filled_width = int(bar_width * current_volume)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + filled_width, bar_y + bar_height), 
                          (0, 255, 0), -1)
            
            # Mostrar porcentaje de volumen
            cv2.putText(frame, f"Volumen: {volume_percent}%", (bar_x, bar_y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        except:
            pass
    
    def handle_gesture(self, event_type, gesture_data):
        """
        Maneja los eventos de gestos del gesture manager.
        
        Args:
            event_type: Tipo de evento ('detected', 'updated', 'ended').
            gesture_data: Datos asociados al gesto.
        """
        gesture_id = gesture_data.get("id")
        
        with self.lock:
            if event_type == "detected":
                # Nuevo gesto detectado
                self.active_gestures[gesture_id] = gesture_data
                self.current_gesture = gesture_id
                self.gesture_start_time = time.time()
                self.gesture_duration = 0
                
                # Reiniciar seguimiento de posiciones para gestos relevantes
                if gesture_id in ["volume", "navigation"]:
                    self.hand_positions = []
                
            elif event_type == "updated":
                # Gesto actualizado
                self.active_gestures[gesture_id] = gesture_data
                if self.current_gesture == gesture_id:
                    self.gesture_duration = time.time() - self.gesture_start_time
                    
                    # Seguir posición de la mano para volumen/navegación
                    if gesture_id in ["volume", "navigation"]:
                        landmarks = gesture_data.get("landmarks")
                        if landmarks:
                            hand_x = int(landmarks.landmark[0].x * settings.CAMERA_WIDTH)
                            hand_y = int(landmarks.landmark[0].y * settings.CAMERA_HEIGHT)
                            self.hand_positions.append((hand_x, hand_y))
                            if len(self.hand_positions) > self.position_history_size:
                                self.hand_positions.pop(0)
                    
                    # Ejecutar acción si el gesto se mantiene suficiente tiempo
                    if self.gesture_duration >= self.required_duration:
                        self.process_gesture_action(gesture_id)
                
            elif event_type == "ended":
                # Gesto terminado
                if gesture_id in self.active_gestures:
                    del self.active_gestures[gesture_id]
                    if self.current_gesture == gesture_id:
                        self.current_gesture = None
                        self.gesture_duration = 0
                        self.hand_positions = []
    
    def process_gesture_action(self, gesture_id):
        """
        Procesa y ejecuta la acción multimedia correspondiente al gesto reconocido.
        
        Args:
            gesture_id: Identificador del gesto.
        """
        current_time = time.time()
        
        # Verificar cooldown para prevenir activaciones múltiples
        if current_time - self.last_action_time < self.action_cooldown:
            return
        
        if gesture_id == "palm":
            self.perform_action("play_pause")
        elif gesture_id == "point":
            vertical_action = self.detect_vertical_movement()
            if vertical_action:
                self.perform_action(vertical_action)
        elif gesture_id == "victory":
            swipe_action = self.detect_swipe()
            if swipe_action:
                self.perform_action(swipe_action)
        elif gesture_id == "fist":
            self.perform_action("mute")
    
    def start(self):
        """
        Inicia el controlador y la suscripción a eventos de gestos.
        """
        # Inicializar cámara si es necesario
        camera_status = self.gesture_manager.get_camera_status()
        if not camera_status["connected"]:
            self.gesture_manager.start_camera_with_settings(
                camera_id=settings.DEFAULT_CAMERA_ID,
                width=settings.CAMERA_WIDTH,
                height=settings.CAMERA_HEIGHT
            )
        
        # Asegurarse de que el procesamiento de gestos esté activo
        if not self.gesture_manager._running:
            self.gesture_manager.start_processing()
        
        # Suscribirse a los gestos
        for gesture_name in self.gestures:
            gesture_id = f"multimedia_{gesture_name.lower()}"
            self.gesture_manager.subscribe_to_gesture(gesture_id, self.handle_gesture)
        
        # Iniciar thread de display
        self.running = True
        self.display_thread = threading.Thread(target=self.display_loop)
        self.display_thread.daemon = True
        self.display_thread.start()
        
        print("Multimedia controller started")
        print("Press 'q' to quit")
    
    def stop(self):
        """
        Detiene el controlador y limpia los recursos.
        """
        self.running = False
        
        if self.display_thread and self.display_thread.is_alive():
            self.display_thread.join(timeout=1.0)
        
        # Desuscribirse de los gestos
        for gesture_name in self.gestures:
            gesture_id = f"multimedia_{gesture_name.lower()}"
            self.gesture_manager.unsubscribe_from_gesture(gesture_id)
        
        print("Multimedia controller stopped")
    
    def display_loop(self):
        """
        Loop principal para mostrar la interfaz de usuario.
        """
        while self.running:
            # Obtener frame actual del gesture manager
            image, _ = self.gesture_manager.process_frame()
            if image is None:
                time.sleep(0.01)
                continue
            
            # Dibujar elementos de UI
            self.display_instructions(image)
            self.display_landmarks(image)
            self.display_volume_bar(image)
            
            # Mostrar el frame
            cv2.imshow('Multimedia Control with Hand Gestures', image)
            
            # Salir con 'q'
            if cv2.waitKey(5) & 0xFF == ord('q'):
                break
        
        # Limpiar ventanas de OpenCV
        cv2.destroyAllWindows()

# Ejemplo de uso
def main():
    controller = MultimediaController()
    try:
        controller.start()
        # El loop principal corre en el thread de display
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Program interrupted by user")
    finally:
        controller.stop()

if __name__ == "__main__":
    main()
