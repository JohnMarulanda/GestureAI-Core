import cv2
import pyautogui
import time
import threading
from core.gesture_recognition_manager import GestureRecognitionManager

class NavigationController:
    """
    Controller for window navigation using hand gestures.
    
    This controller uses a centralized GestureRecognitionManager to detect hand gestures 
    and perform window navigation actions such as Alt+Tab, minimize, maximize, and close windows.
    """
    
    def __init__(self):
        """
        Initializes the NavigationController.
        
        Sets up the gesture recognition manager instance, state variables, and gesture-to-action mappings.
        """
        # Obtain the singleton instance of the gesture recognition manager
        self.gesture_manager = GestureRecognitionManager()
        
        # State variables
        self.running = False  # Flag to control the main loop
        self.display_thread = None  # Thread to handle display updates
        self.lock = threading.Lock()  # Lock to ensure thread-safe operations
        
        # Tracking active gestures and messages to show on screen
        self.active_gestures = {}
        self.gesture_messages = {}
        
        # Timing to enforce cooldown between actions (in seconds)
        self.last_action_time = time.time()
        self.cooldown = 1.0
        
        # Mapping of gesture IDs to their descriptions for display
        self.gestures = {
            "Alt+Tab": "Index and middle fingers extended",
            "Minimizar": "Closed fist",
            "Maximizar": "All fingers extended",
            "Cerrar Ventana": "Thumb and pinky extended"
        }
        
        print("Navigation Controller initialized")
        print("Press 'q' to quit")
    
    def start(self):
        """
        Starts the controller and subscribes to relevant gestures.
        
        Ensures the camera is active, subscribes to gesture events,
        starts gesture processing if not already running, and launches
        the display update thread.
        """
        # Start camera if not already running
        camera_status = self.gesture_manager.get_camera_status()
        if not camera_status["connected"]:
            self.gesture_manager.start_camera_with_settings(width=640, height=480)
        
        # Subscribe to gestures of interest with their handlers
        self.gesture_manager.subscribe_to_gesture("fist", self.handle_gesture)  # Minimize
        self.gesture_manager.subscribe_to_gesture("palm", self.handle_gesture)  # Maximize
        self.gesture_manager.subscribe_to_gesture("victory", self.handle_gesture)  # Alt+Tab
        self.gesture_manager.subscribe_to_gesture("thumbs_up", self.handle_gesture)  # Close window
        
        # Start processing gestures if not already running
        if not self.gesture_manager._running:
            self.gesture_manager.start_processing()
        
        # Start the display update loop in a daemon thread
        self.running = True
        self.display_thread = threading.Thread(target=self.display_loop)
        self.display_thread.daemon = True
        self.display_thread.start()
        
        print("Navigation Controller started")
    
    def stop(self):
        """
        Stops the controller and unsubscribes from gestures.
        
        Joins the display thread and cleans up gesture subscriptions.
        """
        self.running = False
        
        if self.display_thread and self.display_thread.is_alive():
            self.display_thread.join(timeout=1.0)
        
        # Unsubscribe from all gesture events
        self.gesture_manager.unsubscribe_from_gesture("fist")
        self.gesture_manager.unsubscribe_from_gesture("palm")
        self.gesture_manager.unsubscribe_from_gesture("victory")
        self.gesture_manager.unsubscribe_from_gesture("thumbs_up")
        
        print("Navigation Controller stopped")
    
    def handle_gesture(self, event_type, gesture_data):
        """
        Handles gesture events received from the gesture manager.
        
        Args:
            event_type (str): The type of the event ('detected', 'updated', 'ended').
            gesture_data (dict): Data related to the detected gesture.
            
        Behavior:
            - On 'detected' events, if cooldown time has passed, perform the corresponding action.
            - On 'ended' events, remove the gesture from active tracking.
        """
        gesture_id = gesture_data.get("id")
        current_time = time.time()
        
        with self.lock:
            # Perform action only if cooldown elapsed
            if event_type == "detected" and current_time - self.last_action_time >= self.cooldown:
                # Map gesture to window navigation action using pyautogui hotkeys
                if gesture_id == "fist":
                    pyautogui.hotkey('win', 'down')  # Minimize window
                    self.gesture_messages[gesture_id] = "Minimizing window"
                elif gesture_id == "palm":
                    pyautogui.hotkey('win', 'up')  # Maximize window
                    self.gesture_messages[gesture_id] = "Maximizing window"
                elif gesture_id == "victory":
                    pyautogui.hotkey('alt', 'tab')  # Alt+Tab to switch application
                    self.gesture_messages[gesture_id] = "Switching application"
                elif gesture_id == "thumbs_up":
                    pyautogui.hotkey('alt', 'f4')  # Close window
                    self.gesture_messages[gesture_id] = "Closing window"
                
                # Update last action timestamp and store active gesture
                self.last_action_time = current_time
                self.active_gestures[gesture_id] = gesture_data
                
                # Schedule removal of message after 2 seconds
                threading.Timer(2.0, lambda: self.remove_message(gesture_id)).start()
                
                print(f"Action executed: {self.gesture_messages[gesture_id]}")
            
            elif event_type == "ended":
                # Remove gesture from active list when it ends
                if gesture_id in self.active_gestures:
                    del self.active_gestures[gesture_id]
    
    def remove_message(self, gesture_id):
        """
        Removes a gesture message after a timeout to clean up UI.
        
        Args:
            gesture_id (str): The ID of the gesture message to remove.
        """
        with self.lock:
            if gesture_id in self.gesture_messages:
                del self.gesture_messages[gesture_id]
    
    def display_instructions(self, frame):
        """
        Displays the list of available gestures and their functions on the frame.
        
        Args:
            frame (np.ndarray): The image frame on which to draw instructions.
        """
        y_pos = 30
        cv2.putText(frame, "NAVIGATION CONTROLS:", (10, y_pos), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        y_pos += 30
        for action, description in self.gestures.items():
            cv2.putText(frame, f"{action}: {description}", (10, y_pos), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_pos += 25
    
    def display_current_action(self, frame):
        """
        Displays the current action(s) being executed based on gesture input.
        
        Args:
            frame (np.ndarray): The image frame on which to draw action messages.
        """
        with self.lock:
            y_pos = frame.shape[0] - 60
            for message in self.gesture_messages.values():
                cv2.putText(frame, message, (10, y_pos), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                y_pos -= 30
    
    def display_landmarks(self, frame):
        """
        Displays hand landmarks on the frame.
        
        Args:
            frame (np.ndarray): The image frame on which to draw landmarks.
        """
        with self.lock:
            for gesture_data in self.active_gestures.values():
                landmarks = gesture_data.get("landmarks")
                if landmarks:
                    # Draw all landmarks
                    for i, landmark in enumerate(landmarks.landmark):
                        x = int(landmark.x * frame.shape[1])
                        y = int(landmark.y * frame.shape[0])
                        cv2.circle(frame, (x, y), 3, (0, 255, 0), -1)
                        
                        # Highlight finger tips
                        if i in [4, 8, 12, 16, 20]:  # Thumb, Index, Middle, Ring, Pinky tips
                            cv2.circle(frame, (x, y), 6, (255, 0, 0), -1)
                            cv2.putText(frame, str(i), (x + 10, y), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
    
    def get_finger_states(self, gesture_data):
        """
        Determine which fingers are up based on landmarks.
        
        Returns a list of 0s and 1s indicating finger states:
        [thumb, index, middle, ring, pinky]
        
        Args:
            gesture_data (dict): Gesture data containing landmarks.
        
        Returns:
            list or None: Finger states or None if no landmarks.
        """
        landmarks = gesture_data.get("landmarks")
        if not landmarks:
            return None
        
        fingers = []
        # Thumb: compare landmark 4 and 3 x positions
        if landmarks.landmark[4].x > landmarks.landmark[3].x:
            fingers.append(1)
        else:
            fingers.append(0)
        
        # Other fingers: tip landmark y < pip landmark y means finger is up
        for id in range(1, 5):
            if landmarks.landmark[4*id+4].y < landmarks.landmark[4*id+2].y:
                fingers.append(1)
            else:
                fingers.append(0)
        
        return fingers
    
    def display_gesture_info(self, frame):
        """
        Displays current gesture information including finger states.
        
        Args:
            frame (np.ndarray): The image frame on which to draw gesture info.
        """
        with self.lock:
            y_pos = frame.shape[0] - 150
            
            # Display current gesture as binary array
            for gesture_id, gesture_data in self.active_gestures.items():
                finger_states = self.get_finger_states(gesture_data)
                if finger_states:
                    # Show gesture name and binary representation
                    gesture_text = f"Gesture: {gesture_data.get('name', gesture_id)}"
                    cv2.putText(frame, gesture_text, (10, y_pos), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    y_pos += 25
                    
                    # Show binary array
                    binary_text = f"Fingers: {finger_states}"
                    cv2.putText(frame, binary_text, (10, y_pos), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                    y_pos += 20
                    
                    # Show individual finger states with colors
                    finger_names = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
                    for i, (name, state) in enumerate(zip(finger_names, finger_states)):
                        color = (0, 255, 0) if state == 1 else (0, 0, 255)  # Green if open, red if closed
                        status = "Open" if state == 1 else "Closed"
                        finger_text = f"{name}: {status}"
                        cv2.putText(frame, finger_text, (10 + i * 100, y_pos), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
                    y_pos += 30
    
    def display_loop(self):
        """
        Main loop for updating the user interface display.
        
        Continuously fetches frames from the gesture manager, overlays instructions
        and current action messages, and handles quitting on 'q' key press.
        """
        while self.running:
            # Get current frame and metadata from gesture manager
            image, _ = self.gesture_manager.process_frame()
            if image is None:
                time.sleep(0.01)
                continue
            
            # Display gesture instructions, landmarks, gesture info and current action messages
            self.display_instructions(image)
            self.display_landmarks(image)
            self.display_gesture_info(image)
            self.display_current_action(image)
            
            # Show the frame in a window
            cv2.imshow('Window Navigation with Gestures', image)
            
            # Exit if 'q' is pressed
            if cv2.waitKey(5) & 0xFF == ord('q'):
                break
        
        # Clean up windows on exit
        cv2.destroyAllWindows()

# Example usage
def main():
    """
    Entry point for running the NavigationController.
    Starts the controller and maintains the main thread alive.
    """
    controller = NavigationController()
    try:
        controller.start()
        # Keep main thread alive while display thread runs
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Program interrupted by user")
    finally:
        controller.stop()

if __name__ == "__main__":
    main()
