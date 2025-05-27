import cv2
import time
import subprocess
import ctypes
import threading
from core.gesture_recognition_manager import GestureRecognitionManager
from config import settings

class SystemController:
    """Controller for system operations using hand gestures.
    
    This controller uses a centralized GestureRecognitionManager to detect gestures 
    and execute system actions such as locking, shutdown, restart, and sleep.
    """
    
    def __init__(self):
        """Initialize the system controller."""
        # Get the singleton instance of gesture recognition manager
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
        
        # Configuration durations from settings
        self.required_duration = settings.SYSTEM_GESTURE_DURATION
        self.confirmation_duration = settings.SYSTEM_CONFIRMATION_DURATION
        self.message_duration = settings.SYSTEM_MESSAGE_DURATION
        
        # Confirmation state
        self.confirmation_active = False
        self.confirmation_action = None
        self.countdown_active = False
        self.countdown_start_time = 0
        
        # Gesture definitions mapped to human-readable descriptions
        self.gestures = {
            "Lock": "L shape (thumb and index extended)",
            "Shutdown": "Closed fist",
            "Restart": "Index and middle fingers extended",
            "Sleep": "All fingers extended"
        }
        
        print("System Controller initialized")
        print("Press 'q' to quit")
    
    def start(self):
        """Start the controller and subscribe to gestures."""
        # Start camera if not already running
        camera_status = self.gesture_manager.get_camera_status()
        if not camera_status["connected"]:
            self.gesture_manager.start_camera_with_settings(
                camera_id=settings.DEFAULT_CAMERA_ID,
                width=settings.CAMERA_WIDTH,
                height=settings.CAMERA_HEIGHT
            )
        
        # Subscribe to relevant gestures with their handler
        self.gesture_manager.subscribe_to_gesture("fist", self.handle_gesture)    # Shutdown
        self.gesture_manager.subscribe_to_gesture("palm", self.handle_gesture)    # Sleep
        self.gesture_manager.subscribe_to_gesture("victory", self.handle_gesture) # Restart
        self.gesture_manager.subscribe_to_gesture("pinch", self.handle_gesture)   # Lock
        
        # Start gesture processing if not already running
        if not self.gesture_manager._running:
            self.gesture_manager.start_processing()
        
        # Start the display thread for UI feedback
        self.running = True
        self.display_thread = threading.Thread(target=self.display_loop)
        self.display_thread.daemon = True
        self.display_thread.start()
        
        print("System Controller started")
    
    def stop(self):
        """Stop the controller and unsubscribe from gestures."""
        self.running = False
        
        if self.display_thread and self.display_thread.is_alive():
            self.display_thread.join(timeout=1.0)
        
        # Unsubscribe from all gestures
        self.gesture_manager.unsubscribe_from_gesture("fist")
        self.gesture_manager.unsubscribe_from_gesture("palm")
        self.gesture_manager.unsubscribe_from_gesture("victory")
        self.gesture_manager.unsubscribe_from_gesture("pinch")
        
        print("System Controller stopped")
    
    def handle_gesture(self, event_type, gesture_data):
        """Handle gesture events received from the manager.
        
        Args:
            event_type (str): Type of event ('detected', 'updated', 'ended').
            gesture_data (dict): Data related to the detected gesture.
        """
        gesture_id = gesture_data.get("id")
        
        with self.lock:
            if self.confirmation_active:
                if event_type == "detected":
                    # If the same gesture is detected during confirmation, perform action
                    if gesture_id == self.confirmation_action:
                        self.perform_action(gesture_id)
                        self.cancel_confirmation()
                    # If a different gesture is detected, cancel confirmation
                    else:
                        self.cancel_confirmation()
            else:
                if event_type == "detected":
                    # New gesture detected, start tracking
                    self.active_gestures[gesture_id] = gesture_data
                    self.gesture_messages[gesture_id] = f"Detecting: {gesture_id}"
                    
                    self.current_gesture = gesture_id
                    self.gesture_start_time = time.time()
                    self.gesture_duration = 0
                    
                elif event_type == "updated":
                    # Gesture updated, update duration and check if threshold met
                    self.active_gestures[gesture_id] = gesture_data
                    if self.current_gesture:
                        self.gesture_duration = time.time() - self.gesture_start_time
                        
                        if self.gesture_duration >= self.required_duration:
                            self.start_confirmation(gesture_id)
                            self.current_gesture = None
                            self.gesture_duration = 0
                
                elif event_type == "ended":
                    # Gesture ended, clear tracking
                    if gesture_id in self.active_gestures:
                        del self.active_gestures[gesture_id]
                        self.current_gesture = None
                        self.gesture_duration = 0
    
    def perform_action(self, gesture_id):
        """Execute the system action corresponding to the gesture."""
        try:
            if gesture_id == "pinch":
                self.lock_computer()
            elif gesture_id == "fist":
                self.shutdown_computer()
            elif gesture_id == "victory":
                self.restart_computer()
            elif gesture_id == "palm":
                self.sleep_computer()
        except Exception as e:
            self.set_action_message(f"Error executing action: {e}")
    
    def lock_computer(self):
        """Lock the computer."""
        self.set_action_message("Locking computer")
        ctypes.windll.user32.LockWorkStation()
    
    def shutdown_computer(self):
        """Shutdown the computer."""
        self.set_action_message("Shutting down computer")
        subprocess.call(['shutdown', '/s', '/t', '1'])
    
    def restart_computer(self):
        """Restart the computer."""
        self.set_action_message("Restarting computer")
        subprocess.call(['shutdown', '/r', '/t', '1'])
    
    def sleep_computer(self):
        """Put the computer into sleep mode."""
        self.set_action_message("Entering sleep mode")
        subprocess.call(['powershell', '-Command', 
                       'Add-Type -AssemblyName System.Windows.Forms; '
                       '[System.Windows.Forms.Application]::SetSuspendState("Suspend", $false, $false)'])
    
    def start_confirmation(self, action):
        """Start confirmation process for critical actions.
        
        Args:
            action (str): The action requiring confirmation.
        """
        with self.lock:
            self.confirmation_active = True
            self.confirmation_action = action
            self.countdown_active = True
            self.countdown_start_time = time.time()
            self.set_action_message(f"Confirm {action}? Repeat gesture to confirm")
    
    def cancel_confirmation(self):
        """Cancel the confirmation process."""
        with self.lock:
            self.confirmation_active = False
            self.confirmation_action = None
            self.countdown_active = False
            self.set_action_message("Action cancelled")
    
    def set_action_message(self, message):
        """Set the action message to display on screen.
        
        Args:
            message (str): The message text.
        """
        with self.lock:
            self.gesture_messages["action"] = message
            # Schedule message removal after duration
            threading.Timer(self.message_duration, 
                          lambda: self.remove_message("action")).start()
        print(message)
    
    def remove_message(self, message_id):
        """Remove a message after a timeout.
        
        Args:
            message_id (str): The message identifier to remove.
        """
        with self.lock:
            if message_id in self.gesture_messages:
                del self.gesture_messages[message_id]
    
    def display_instructions(self, frame):
        """Display available gestures and their functions on the frame.
        
        Args:
            frame (ndarray): The image frame to draw on.
        """
        y_pos = 30
        cv2.putText(frame, "SYSTEM CONTROLS:", (10, y_pos), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        y_pos += 30
        for action, description in self.gestures.items():
            cv2.putText(frame, f"{action}: {description}", (10, y_pos), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_pos += 25
    
    def display_gesture_progress(self, frame):
        """Display progress bar indicating the duration of the detected gesture.
        
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
            
            # Draw progress portion
            progress_width = int(bar_width * progress)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + progress_width, bar_y + bar_height), 
                          (0, 255, 0), -1)
            
            # Draw progress text
            cv2.putText(frame, f"Detecting: {self.current_gesture} ({int(progress * 100)}%)", 
                        (bar_x, bar_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def display_confirmation(self, frame):
        """Display confirmation dialog for critical actions.
        
        Args:
            frame (ndarray): The image frame to draw on.
        """
        if self.confirmation_active:
            # Create semi-transparent overlay
            overlay = frame.copy()
            cv2.rectangle(overlay, (50, 50), (frame.shape[1] - 50, frame.shape[0] - 50), 
                          (0, 0, 0), -1)
            alpha = 0.7
            frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
            
            # Display confirmation message
            cv2.putText(frame, f"Confirm {self.confirmation_action}?", 
                        (100, frame.shape[0] // 2 - 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
            
            # Display instructions
            cv2.putText(frame, "Repeat gesture to confirm", 
                        (100, frame.shape[0] // 2), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
            
            cv2.putText(frame, "Any other gesture to cancel", 
                        (100, frame.shape[0] // 2 + 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
            
            # Show countdown timer
            if self.countdown_active:
                elapsed = time.time() - self.countdown_start_time
                remaining = max(0, self.confirmation_duration - elapsed)
                
                if remaining == 0:
                    self.cancel_confirmation()
                else:
                    cv2.putText(frame, f"Cancelling in {int(remaining)}s", 
                                (100, frame.shape[0] // 2 + 70), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    def display_messages(self, frame):
        """Display action messages on the frame.
        
        Args:
            frame (ndarray): The image frame to draw on.
        """
        with self.lock:
            y_pos = frame.shape[0] - 30
            for message in self.gesture_messages.values():
                cv2.putText(frame, message, (10, y_pos), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                y_pos -= 30
    
    def display_landmarks(self, frame):
        """Display hand landmarks on the frame.
        
        Args:
            frame (ndarray): The image frame to draw on.
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
        """Determine which fingers are up based on landmarks.
        
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
        """Display current gesture information including finger states.
        
        Args:
            frame (ndarray): The image frame to draw on.
        """
        with self.lock:
            y_pos = frame.shape[0] - 180
            
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
        """Main loop to display the user interface."""
        while self.running:
            # Get current frame from gesture manager
            image, _ = self.gesture_manager.process_frame()
            if image is None:
                time.sleep(0.01)
                continue
            
            # Overlay UI elements on the frame
            self.display_instructions(image)
            self.display_landmarks(image)
            self.display_gesture_info(image)
            self.display_gesture_progress(image)
            self.display_confirmation(image)
            self.display_messages(image)
            
            # Show the frame in a window
            cv2.imshow('Gesture-based System Control', image)
            
            # Exit on 'q' key press
            if cv2.waitKey(5) & 0xFF == ord('q'):
                break
        
        # Cleanup OpenCV windows
        cv2.destroyAllWindows()

# Example usage
def main():
    """Example main function to run the SystemController."""
    controller = SystemController()
    try:
        controller.start()
        # Main loop runs in the display thread
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Program interrupted by user")
    finally:
        controller.stop()

if __name__ == "__main__":
    main()
