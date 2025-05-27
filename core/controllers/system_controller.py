import cv2
import time
import subprocess
import ctypes
import threading
from core.gesture_recognition_manager import GestureRecognitionManager
from config import settings

class SystemController:
    """
    Controlador para operaciones del sistema usando gestos.
    
    Este controlador permite realizar acciones del sistema como bloquear,
    apagar, reiniciar y poner en suspensión el equipo mediante gestos.
    """
    
    def __init__(self):
        """
        Inicializa el controlador del sistema.
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
        
        # Parámetros de configuración
        self.required_duration = 3.0  # Segundos para mantener el gesto
        self.message_duration = 3.0
        self.confirmation_active = False
        self.confirmation_action = None
        self.countdown_active = False
        self.countdown_start_time = 0
        self.countdown_duration = 5  # 5 segundos de cuenta regresiva
        
        # Definir gestos y sus acciones correspondientes
        self.gestures = {
            "Lock": "L shape (thumb and index extended)",
            "Shutdown": "Closed fist",
            "Restart": "Two fingers extended (index and middle)",
            "Sleep": "Five fingers extended (open hand)"
        }
        
        print("System controller initialized")
    
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
        if finger_states == [1, 1, 0, 0, 0]:  # L shape (thumb and index extended)
            return "Lock"
        elif finger_states == [0, 0, 0, 0, 0]:  # Closed fist
            return "Shutdown"
        elif finger_states == [0, 1, 1, 0, 0]:  # Two fingers extended (index and middle)
            return "Restart"
        elif finger_states == [1, 1, 1, 1, 1]:  # Five fingers extended (open hand)
            return "Sleep"
        return None
    
    def perform_action(self, action):
        """
        Ejecuta la acción del sistema correspondiente.
        
        Args:
            action: Nombre de la acción a ejecutar.
        """
        if action == "Lock":
            self.lock_computer()
        elif action == "Shutdown":
            self.shutdown_computer()
        elif action == "Restart":
            self.restart_computer()
        elif action == "Sleep":
            self.sleep_computer()
    
    def lock_computer(self):
        """Bloquea la pantalla del ordenador."""
        with self.lock:
            self.set_message("Computer Locked")
        ctypes.windll.user32.LockWorkStation()
    
    def shutdown_computer(self):
        """Apaga el ordenador."""
        with self.lock:
            self.set_message("Computer Shutting Down")
        subprocess.call(['shutdown', '/s', '/t', '1'])
    
    def restart_computer(self):
        """Reinicia el ordenador."""
        with self.lock:
            self.set_message("Computer Restarting")
        subprocess.call(['shutdown', '/r', '/t', '1'])
    
    def sleep_computer(self):
        """Pone el ordenador en modo suspensión."""
        with self.lock:
            self.set_message("Computer Going to Sleep")
        subprocess.call(['powershell', '-Command', 
                       'Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState("Suspend", $false, $false)'])
    
    def start_confirmation(self, action):
        """
        Inicia el proceso de confirmación para acciones críticas.
        
        Args:
            action: Nombre de la acción a confirmar.
        """
        with self.lock:
            self.confirmation_active = True
            self.confirmation_action = action
            self.countdown_active = True
            self.countdown_start_time = time.time()
            self.set_message(f"Confirm {action}? Show same gesture again to confirm")
    
    def cancel_confirmation(self):
        """Cancela el proceso de confirmación."""
        with self.lock:
            self.confirmation_active = False
            self.confirmation_action = None
            self.countdown_active = False
            self.set_message("Action cancelled")
    
    def set_message(self, message, duration=None):
        """
        Establece un mensaje temporal para mostrar en pantalla.
        
        Args:
            message: Mensaje a mostrar.
            duration: Duración en segundos (opcional).
        """
        with self.lock:
            self.gesture_messages["action"] = message
            # Programar eliminación del mensaje
            duration = duration or self.message_duration
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
        cv2.putText(frame, "SYSTEM CONTROL GESTURES:", (10, y_pos), 
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
    
    def display_confirmation(self, frame):
        """
        Muestra el diálogo de confirmación para acciones críticas.
        
        Args:
            frame: Frame donde mostrar la confirmación.
        """
        if self.confirmation_active:
            # Crear overlay semitransparente
            overlay = frame.copy()
            cv2.rectangle(overlay, (50, 50), (frame.shape[1] - 50, frame.shape[0] - 50), 
                          (0, 0, 0), -1)
            alpha = 0.7
            frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
            
            # Mostrar mensaje de confirmación
            cv2.putText(frame, f"Confirm {self.confirmation_action}?", 
                        (100, frame.shape[0] // 2 - 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
            
            # Mostrar instrucciones
            cv2.putText(frame, "Show same gesture again to confirm", 
                        (100, frame.shape[0] // 2), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
            
            cv2.putText(frame, "Any other gesture or wait to cancel", 
                        (100, frame.shape[0] // 2 + 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
            
            # Mostrar cuenta regresiva
            if self.countdown_active:
                elapsed = time.time() - self.countdown_start_time
                remaining = max(0, self.countdown_duration - elapsed)
                
                if remaining == 0:
                    self.cancel_confirmation()
                else:
                    cv2.putText(frame, f"Canceling in {int(remaining)}s", 
                                (100, frame.shape[0] // 2 + 70), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
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
                
                # Si hay confirmación activa, verificar si es el mismo gesto
                if self.confirmation_active:
                    detected_gesture = self.identify_gesture(gesture_data.get("finger_states", []))
                    if detected_gesture == self.confirmation_action:
                        self.perform_action(detected_gesture)
                        self.cancel_confirmation()
                    elif detected_gesture:
                        self.cancel_confirmation()
                
            elif event_type == "updated":
                # Gesto actualizado
                self.active_gestures[gesture_id] = gesture_data
                
                # Actualizar duración del gesto actual
                if self.current_gesture:
                    self.gesture_duration = time.time() - self.gesture_start_time
                    
                    # Si se mantiene suficiente tiempo, iniciar confirmación
                    if self.gesture_duration >= self.required_duration:
                        self.start_confirmation(self.current_gesture)
                        self.current_gesture = None
                        self.gesture_duration = 0
                
            elif event_type == "ended":
                # Gesto terminado
                if gesture_id in self.active_gestures:
                    del self.active_gestures[gesture_id]
                    self.current_gesture = None
                    self.gesture_duration = 0
    
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
            gesture_id = f"system_{gesture_name.lower()}"
            self.gesture_manager.subscribe_to_gesture(gesture_id, self.handle_gesture)
        
        # Iniciar thread de display
        self.running = True
        self.display_thread = threading.Thread(target=self.display_loop)
        self.display_thread.daemon = True
        self.display_thread.start()
        
        print("System controller started")
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
            gesture_id = f"system_{gesture_name.lower()}"
            self.gesture_manager.unsubscribe_from_gesture(gesture_id)
        
        print("System controller stopped")
    
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
            self.display_confirmation(image)
            self.display_messages(image)
            
            # Mostrar el frame
            cv2.imshow('System Control with Hand Gestures', image)
            
            # Salir con 'q'
            if cv2.waitKey(5) & 0xFF == ord('q'):
                break
        
        # Limpiar ventanas de OpenCV
        cv2.destroyAllWindows()

# Ejemplo de uso
def main():
    controller = SystemController()
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
