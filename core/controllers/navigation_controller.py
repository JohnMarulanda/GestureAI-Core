import cv2
import pyautogui
import time
import threading
from core.gesture_recognition_manager import GestureRecognitionManager
from config import settings

class NavigationController:
    """
    Controlador para navegación de ventanas usando gestos.
    
    Este controlador permite realizar acciones de navegación como Alt+Tab,
    minimizar, maximizar y cerrar ventanas mediante gestos.
    """
    
    def __init__(self):
        """
        Inicializa el controlador de navegación.
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
        self.last_action_time = time.time()
        self.cooldown = 1.0  # segundos
        
        # Definir gestos y sus acciones correspondientes
        self.gestures = {
            "Alt+Tab": "Index and middle finger extended",
            "Minimize": "Closed fist",
            "Maximize": "All fingers extended",
            "Close Window": "Thumb and pinky extended"
        }
        
        print("Navigation controller initialized")
    
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
        if finger_states == [0, 1, 1, 0, 0]:  # Index and middle finger extended
            return "Alt+Tab"
        elif finger_states == [0, 0, 0, 0, 0]:  # Closed fist
            return "Minimize"
        elif finger_states == [1, 1, 1, 1, 1]:  # All fingers extended
            return "Maximize"
        elif finger_states == [1, 0, 0, 0, 1]:  # Thumb and pinky extended
            return "Close Window"
        return None
    
    def perform_action(self, action):
        """
        Ejecuta la acción de navegación correspondiente.
        
        Args:
            action: Nombre de la acción a ejecutar.
        """
        current_time = time.time()
        
        # Verificar cooldown para prevenir múltiples activaciones
        if current_time - self.last_action_time < self.cooldown:
            return
        
        if action == "Alt+Tab":
            pyautogui.hotkey('alt', 'tab')
            self.set_message("Switching Applications")
        elif action == "Minimize":
            pyautogui.hotkey('win', 'down')
            self.set_message("Minimizing Window")
        elif action == "Maximize":
            pyautogui.hotkey('win', 'up')
            self.set_message("Maximizing Window")
        elif action == "Close Window":
            pyautogui.hotkey('alt', 'f4')
            self.set_message("Closing Window")
        
        self.last_action_time = current_time
    
    def set_message(self, message, duration=2.0):
        """
        Establece un mensaje temporal para mostrar en pantalla.
        
        Args:
            message: Mensaje a mostrar.
            duration: Duración en segundos (opcional).
        """
        with self.lock:
            self.gesture_messages["action"] = message
            # Programar eliminación del mensaje
            threading.Timer(duration, lambda: self.remove_message("action")).start()
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
        cv2.putText(frame, "WINDOW NAVIGATION GESTURES:", (10, y_pos), 
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
    
    def display_messages(self, frame):
        """
        Muestra los mensajes actuales en el frame.
        
        Args:
            frame: Frame donde mostrar los mensajes.
        """
        with self.lock:
            y_pos = frame.shape[0] - 30
            for message in self.gesture_messages.values():
                cv2.putText(frame, message, (10, y_pos), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                y_pos -= 30
    
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
                
                # Identificar y ejecutar acción
                finger_states = gesture_data.get("finger_states", [])
                gesture = self.identify_gesture(finger_states)
                if gesture:
                    self.perform_action(gesture)
                
            elif event_type == "updated":
                # Gesto actualizado
                self.active_gestures[gesture_id] = gesture_data
                
            elif event_type == "ended":
                # Gesto terminado
                if gesture_id in self.active_gestures:
                    del self.active_gestures[gesture_id]
    
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
            gesture_id = f"navigation_{gesture_name.lower()}"
            self.gesture_manager.subscribe_to_gesture(gesture_id, self.handle_gesture)
        
        # Iniciar thread de display
        self.running = True
        self.display_thread = threading.Thread(target=self.display_loop)
        self.display_thread.daemon = True
        self.display_thread.start()
        
        print("Navigation controller started")
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
            gesture_id = f"navigation_{gesture_name.lower()}"
            self.gesture_manager.unsubscribe_from_gesture(gesture_id)
        
        print("Navigation controller stopped")
    
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
            self.display_messages(image)
            
            # Mostrar el frame
            cv2.imshow('Window Navigation with Hand Gestures', image)
            
            # Salir con 'q'
            if cv2.waitKey(5) & 0xFF == ord('q'):
                break
        
        # Limpiar ventanas de OpenCV
        cv2.destroyAllWindows()

# Ejemplo de uso
def main():
    controller = NavigationController()
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
