import cv2
import time
import pyautogui
import threading
from core.gesture_recognition_manager import GestureRecognitionManager
from config import settings

class VolumeController:
    """Controller to adjust system volume using gestures.

    This controller uses the centralized GestureRecognitionManager to
    detect gestures and adjust the system volume based on the distance
    between the thumb and index finger.
    """

    def __init__(self):
        """Initializes the volume controller."""
        # Get the singleton instance of the gesture recognition manager
        self.gesture_manager = GestureRecognitionManager()

        # State variables
        self.running = False
        self.display_thread = None
        self.lock = threading.Lock()

        # Gesture-related state
        self.active_gestures = {}
        self.gesture_messages = {}
        self.current_distance = None
        self.last_volume_change = 0

        # Configuration parameters from settings
        self.upper_threshold = settings.VOLUME_UPPER_THRESHOLD
        self.lower_threshold = settings.VOLUME_LOWER_THRESHOLD
        self.scaling_factor = settings.VOLUME_SCALING_FACTOR
        self.action_delay = settings.ACTION_DELAY

        print("Volume Controller initialized")
        print("Press 'q' to quit")

    def start(self):
        """Starts the controller and subscribes to gestures."""
        # Start the camera if not already started
        camera_status = self.gesture_manager.get_camera_status()
        if not camera_status["connected"]:
            self.gesture_manager.start_camera_with_settings(
                camera_id=settings.DEFAULT_CAMERA_ID,
                width=settings.CAMERA_WIDTH,
                height=settings.CAMERA_HEIGHT
            )

        # Subscribe to the "pinch" gesture for volume control
        self.gesture_manager.subscribe_to_gesture("pinch", self.handle_gesture)

        # Start gesture processing if not already running
        if not self.gesture_manager._running:
            self.gesture_manager.start_processing()

        # Start the display thread to show UI
        self.running = True
        self.display_thread = threading.Thread(target=self.display_loop)
        self.display_thread.daemon = True
        self.display_thread.start()

        print("Volume Controller started")

    def stop(self):
        """Stops the controller and unsubscribes from gestures."""
        self.running = False

        if self.display_thread and self.display_thread.is_alive():
            self.display_thread.join(timeout=1.0)

        # Unsubscribe from the "pinch" gesture
        self.gesture_manager.unsubscribe_from_gesture("pinch")

        print("Volume Controller stopped")

    def handle_gesture(self, event_type, gesture_data):
        """Handles gesture events received from the manager.

        Args:
            event_type (str): Type of event ('detected', 'updated', 'ended').
            gesture_data (dict): Data about the gesture.
        """
        gesture_id = gesture_data.get("id")

        with self.lock:
            if event_type == "detected":
                # New gesture detected
                self.active_gestures[gesture_id] = gesture_data
                self.gesture_messages[gesture_id] = "Volume control activated"

            elif event_type == "updated":
                # Update gesture data and adjust volume accordingly
                self.active_gestures[gesture_id] = gesture_data
                landmarks = gesture_data.get("landmarks")
                if landmarks:
                    # Calculate distance between thumb (landmark 4) and index finger (landmark 8)
                    thumb = landmarks.landmark[4]
                    index = landmarks.landmark[8]
                    distance = ((thumb.x - index.x) ** 2 + (thumb.y - index.y) ** 2) ** 0.5

                    # Scale the distance for volume adjustment
                    scaled_distance = distance * 100 / self.scaling_factor
                    self.current_distance = scaled_distance

                    # Adjust volume only if enough time has passed since last change
                    current_time = time.time()
                    if current_time - self.last_volume_change >= self.action_delay:
                        self.adjust_volume(scaled_distance)
                        self.last_volume_change = current_time

            elif event_type == "ended":
                # Gesture ended
                if gesture_id in self.active_gestures:
                    del self.active_gestures[gesture_id]
                    self.current_distance = None
                    self.gesture_messages[gesture_id] = "Volume control deactivated"
                    # Remove message after 2 seconds
                    threading.Timer(2.0, lambda: self.remove_message(gesture_id)).start()

    def adjust_volume(self, distance):
        """Adjusts the system volume based on the distance between fingers.

        Args:
            distance (float): Scaled distance between thumb and index finger.
        """
        if distance > self.upper_threshold:
            # Increase volume
            times = min(int((distance - self.upper_threshold) / 2), 5)
            for _ in range(times):
                pyautogui.press('volumeup')
            self.set_action_message(f"Increasing volume ({times} steps)")

        elif distance < self.lower_threshold:
            # Decrease volume
            times = min(int((self.lower_threshold - distance) / 2), 5)
            for _ in range(times):
                pyautogui.press('volumedown')
            self.set_action_message(f"Decreasing volume ({times} steps)")

    def set_action_message(self, message):
        """Sets a temporary action message to display.

        Args:
            message (str): The message to display.
        """
        with self.lock:
            self.gesture_messages["action"] = message
            threading.Timer(2.0, lambda: self.remove_message("action")).start()

    def remove_message(self, message_id):
        """Removes a message after a delay.

        Args:
            message_id (str): The ID of the message to remove.
        """
        with self.lock:
            if message_id in self.gesture_messages:
                del self.gesture_messages[message_id]

    def display_volume_control(self, frame):
        """Displays the volume control UI on the video frame.

        Args:
            frame (numpy.ndarray): The current video frame.
        """
        if self.current_distance is not None:
            # Draw the volume bar background
            bar_width = int(frame.shape[1] * 0.3)
            bar_height = 20
            bar_x = int((frame.shape[1] - bar_width) / 2)
            bar_y = frame.shape[0] - 60

            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height),
                          (100, 100, 100), -1)

            # Draw the volume indicator bar proportionally to the current distance
            normalized_distance = max(0, min(100, self.current_distance))
            indicator_width = int(bar_width * normalized_distance / 100)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + indicator_width, bar_y + bar_height),
                          (0, 255, 0), -1)

            # Display volume percentage text above the bar
            cv2.putText(frame, f"Volume: {int(normalized_distance)}%",
                        (bar_x, bar_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    def display_instructions(self, frame):
        """Displays usage instructions on the video frame.

        Args:
            frame (numpy.ndarray): The current video frame.
        """
        y_pos = 30
        cv2.putText(frame, "VOLUME CONTROL:", (10, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        y_pos += 30
        instructions = [
            "Pinch thumb and index to activate",
            "Separate fingers to increase volume",
            "Bring fingers closer to decrease volume",
            "Hold distance to maintain current volume"
        ]

        for instruction in instructions:
            cv2.putText(frame, instruction, (10, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_pos += 25

    def display_messages(self, frame):
        """Displays status and action messages on the video frame.

        Args:
            frame (numpy.ndarray): The current video frame.
        """
        with self.lock:
            y_pos = frame.shape[0] - 30
            for message in self.gesture_messages.values():
                cv2.putText(frame, message, (10, y_pos),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                y_pos -= 30

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
        Muestra los landmarks de la mano y el estado de los dedos.
        
        Args:
            frame: Frame donde mostrar los landmarks.
        """
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
                cv2.putText(frame, f"Estados: {finger_state_str}", 
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

    def display_loop(self):
        """Main loop to display the user interface."""
        while self.running:
            # Get the current frame from gesture manager
            image, _ = self.gesture_manager.process_frame()
            if image is None:
                time.sleep(0.01)
                continue
            
            # Display UI elements on the frame
            self.display_instructions(image)
            self.display_volume_control(image)
            self.display_messages(image)
            self.display_landmarks(image)
            
            # Show the frame
            cv2.imshow('Gesture Volume Control', image)
            
            # Exit if 'q' is pressed
            if cv2.waitKey(5) & 0xFF == ord('q'):
                break
        
        # Clean up windows after exit
        cv2.destroyAllWindows()

# Example usage
def main():
    controller = VolumeController()
    try:
        controller.start()
        # Main thread stays alive while display runs in background
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Program interrupted by user")
    finally:
        controller.stop()

if __name__ == "__main__":
    main()
