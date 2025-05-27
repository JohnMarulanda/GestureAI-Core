import cv2
import pyautogui
import time
import json
import os
import threading
from core.gesture_recognition_manager import GestureRecognitionManager
from config import settings

class ShortcutsController:
    """
    Controller for executing keyboard shortcuts using hand gestures.
    
    This controller uses a centralized GestureRecognitionManager to detect gestures
    and execute configured keyboard shortcuts.
    """
    
    def __init__(self):
        """
        Initializes the shortcuts controller.
        
        Sets up gesture manager instance, state variables, loads configuration,
        and prepares threading and locking mechanisms.
        """
        # Get the singleton instance of the gesture recognition manager
        self.gesture_manager = GestureRecognitionManager()
        
        # State variables
        self.running = False
        self.display_thread = None
        self.lock = threading.Lock()
        
        # Gesture state
        self.active_gestures = {}
        self.gesture_messages = {}
        self.current_gesture = None
        self.gesture_start_time = 0
        self.gesture_duration = 0
        
        # Configuration parameters from settings
        self.required_duration = settings.SHORTCUTS_GESTURE_DURATION
        self.message_duration = settings.SHORTCUTS_MESSAGE_DURATION
        
        # Load gesture shortcut configuration from JSON file
        self.config_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            settings.GESTURE_CONFIG_PATH
        )
        self.load_config()
        
        print("Shortcuts controller initialized")
    
    def load_config(self):
        """
        Loads gesture configuration from the JSON file.
        
        The JSON file contains a mapping of shortcut names to their respective
        keyboard shortcuts and associated gestures.
        """
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.config = config.get("keyboard_gestures", {})
        except Exception as e:
            print(f"Error loading configuration: {e}")
            self.config = {}
    
    def start(self):
        """
        Starts the controller and subscribes to gesture events.
        
        Initializes the camera if not connected, subscribes to the gestures
        defined in the config, starts gesture processing, and launches the
        UI display thread.
        """
        # Initialize camera if needed
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
        
        # Subscribe to gestures from configuration
        for shortcut_name in self.config:
            gesture_id = f"shortcut_{shortcut_name}"
            self.gesture_manager.subscribe_to_gesture(gesture_id, self.handle_gesture)
        
        # Start display thread for UI
        self.running = True
        self.display_thread = threading.Thread(target=self.display_loop)
        self.display_thread.daemon = True
        self.display_thread.start()
        
        print("Shortcuts controller started")
        print("Press 'q' to quit")
    
    def stop(self):
        """
        Stops the controller and unsubscribes from gestures.
        
        Stops the UI thread and unsubscribes from all gesture events.
        """
        self.running = False
        
        if self.display_thread and self.display_thread.is_alive():
            self.display_thread.join(timeout=1.0)
        
        # Unsubscribe from all configured gestures
        for shortcut_name in self.config:
            gesture_id = f"shortcut_{shortcut_name}"
            self.gesture_manager.unsubscribe_from_gesture(gesture_id)
        
        print("Shortcuts controller stopped")
    
    def handle_gesture(self, event_type, gesture_data):
        """
        Handles gesture events from the gesture manager.
        
        Args:
            event_type (str): Event type ('detected', 'updated', 'ended').
            gesture_data (dict): Data associated with the gesture.
        """
        gesture_id = gesture_data.get("id")
        
        with self.lock:
            if event_type == "detected":
                # New gesture detected: start tracking it
                self.active_gestures[gesture_id] = gesture_data
                shortcut_name = gesture_id.split("_", 1)[1]
                self.gesture_messages[gesture_id] = f"Detecting: {shortcut_name}"
                
                # Start timing the gesture duration
                self.current_gesture = shortcut_name
                self.gesture_start_time = time.time()
                self.gesture_duration = 0
                
            elif event_type == "updated":
                # Gesture updated: track duration and trigger shortcut if long enough
                self.active_gestures[gesture_id] = gesture_data
                if self.current_gesture:
                    self.gesture_duration = time.time() - self.gesture_start_time
                    
                    # Check if gesture held long enough to trigger shortcut
                    if self.gesture_duration >= self.required_duration:
                        shortcut_name = gesture_id.split("_", 1)[1]
                        if shortcut_name in self.config:
                            self.execute_shortcut(shortcut_name)
                            self.current_gesture = None
                
            elif event_type == "ended":
                # Gesture ended: clean up
                if gesture_id in self.active_gestures:
                    del self.active_gestures[gesture_id]
                    self.current_gesture = None
                    self.gesture_duration = 0
    
    def execute_shortcut(self, shortcut_name):
        """
        Executes the keyboard shortcut associated with the gesture using pyautogui.
        
        Args:
            shortcut_name (str): The name of the shortcut to execute.
        
        Returns:
            bool: True if the shortcut was executed successfully, False otherwise.
        """
        try:
            keys = self.config[shortcut_name]["shortcut"]
            pyautogui.hotkey(*keys)
            self.set_action_message(f"Executed: {shortcut_name} ({'+'.join(keys)})")
            return True
        except Exception as e:
            self.set_action_message(f"Error executing {shortcut_name}: {e}")
            return False
    
    def set_action_message(self, message):
        """
        Sets a temporary action message to be displayed on screen.
        
        Args:
            message (str): The message to display.
        """
        with self.lock:
            self.gesture_messages["action"] = message
            # Schedule message removal after configured duration
            threading.Timer(self.message_duration, 
                          lambda: self.remove_message("action")).start()
        print(message)
    
    def remove_message(self, message_id):
        """
        Removes a message from the display after its duration expires.
        
        Args:
            message_id (str): Identifier of the message to remove.
        """
        with self.lock:
            if message_id in self.gesture_messages:
                del self.gesture_messages[message_id]
    
    def display_instructions(self, frame):
        """
        Displays the list of configured keyboard shortcuts and their gestures on the frame.
        
        Args:
            frame (ndarray): The image frame to draw on.
        """
        y_pos = 30
        cv2.putText(frame, "KEYBOARD SHORTCUTS:", (10, y_pos), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        y_pos += 30
        for shortcut_name, config in self.config.items():
            shortcut_str = "+".join(config["shortcut"])
            gesture_str = "".join([str(g) for g in config["gesture"]])
            cv2.putText(frame, f"{shortcut_name} ({shortcut_str}): {gesture_str}", (10, y_pos), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_pos += 25
    
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

    def display_landmarks(self, frame):
        """
        Displays hand landmarks on the frame.
        
        Args:
            frame (ndarray): The image frame to draw on.
        """
        with self.lock:
            # Obtener el frame actual y los resultados de MediaPipe directamente del gesture_manager
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
    
    def display_gesture_progress(self, frame):
        """
        Displays a progress bar representing how long the current gesture has been held.
        
        Args:
            frame (ndarray): The image frame to draw on.
        """
        if self.current_gesture and self.gesture_duration > 0:
            progress = min(self.gesture_duration / self.required_duration, 1.0)
            bar_width = int(frame.shape[1] * 0.6)
            bar_height = 20
            bar_x = int((frame.shape[1] - bar_width) / 2)
            bar_y = frame.shape[0] - 60
            
            # Draw background bar
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), 
                          (100, 100, 100), -1)
            
            # Draw progress bar
            progress_width = int(bar_width * progress)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + progress_width, bar_y + bar_height), 
                          (0, 255, 0), -1)
            
            # Draw progress text
            shortcut_config = self.config.get(self.current_gesture, {})
            if shortcut_config:
                shortcut_str = "+".join(shortcut_config["shortcut"])
                cv2.putText(frame, f"Detecting: {self.current_gesture} ({shortcut_str}) ({int(progress * 100)}%)", 
                            (bar_x, bar_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def display_messages(self, frame):
        """
        Displays current action messages on the frame.
        
        Args:
            frame (ndarray): The image frame to draw on.
        """
        with self.lock:
            y_pos = frame.shape[0] - 30
            for message in self.gesture_messages.values():
                cv2.putText(frame, message, (10, y_pos), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                y_pos -= 30
    
    def display_loop(self):
        """
        Main loop for displaying the UI interface.
        
        Continuously captures frames, displays instructions, gesture progress,
        and messages until stopped or user presses 'q'.
        """
        while self.running:
            # Get current frame from gesture manager
            image, results = self.gesture_manager.process_frame()
            if image is None:
                time.sleep(0.01)
                continue
            
            # Draw UI overlays on frame
            self.display_instructions(image)
            self.display_landmarks(image)  # Mostrar landmarks
            self.display_gesture_progress(image)
            self.display_messages(image)
            
            # Show the frame in a window
            cv2.imshow('Keyboard Shortcuts Control with Gestures', image)
            
            # Exit loop on 'q' key press
            if cv2.waitKey(5) & 0xFF == ord('q'):
                break
        
        # Cleanup OpenCV windows
        cv2.destroyAllWindows()

# Example usage
def main():
    controller = ShortcutsController()
    try:
        controller.start()
        # The main loop runs in the display thread, keep main thread alive
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Program interrupted by user")
    finally:
        controller.stop()

if __name__ == "__main__":
    main()
