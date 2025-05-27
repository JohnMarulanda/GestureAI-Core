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
    Multimedia controller for performing media operations using hand gestures.

    This controller uses a centralized GestureRecognitionManager to handle gesture detection,
    avoiding duplicated detection logic.

    It supports gestures for play/pause, volume control, navigation, and mute.
    """
    
    def __init__(self):
        """Initialize the multimedia controller and prepare required settings."""
        # Obtain the singleton instance of the gesture recognition manager
        self.gesture_manager = GestureRecognitionManager()
        
        # Controller state variables
        self.running = False
        self.display_thread = None
        self.lock = threading.Lock()
        
        # Gesture tracking state
        self.active_gestures = {}           # Currently detected gestures
        self.gesture_messages = {}          # Messages to display for gestures
        self.current_gesture = None         # ID of the gesture being tracked for duration
        self.gesture_start_time = 0         # When the current gesture started
        self.gesture_duration = 0           # How long the current gesture has lasted
        
        # Settings loaded from configuration
        self.required_duration = settings.MULTIMEDIA_GESTURE_DURATION      # Seconds gesture must be held
        self.action_cooldown = settings.MULTIMEDIA_ACTION_COOLDOWN          # Minimum delay between actions
        self.volume_change_threshold = settings.MULTIMEDIA_VOLUME_CHANGE_THRESHOLD
        self.swipe_threshold = settings.MULTIMEDIA_SWIPE_THRESHOLD
        self.message_duration = settings.MULTIMEDIA_MESSAGE_DURATION        # How long to show messages
        
        # Initialize system volume control interface
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(interface, POINTER(IAudioEndpointVolume))
        
        # Track hand positions to detect movements
        self.hand_positions = []
        self.position_history_size = 10    # Number of frames to keep for movement detection
        
        # Last time an action was performed to enforce cooldown
        self.last_action_time = 0
        
        print("Multimedia controller initialized")
    
    def start(self):
        """
        Start the controller: start the camera if needed, subscribe to gestures,
        and start the display thread.
        """
        # Start camera if not connected
        camera_status = self.gesture_manager.get_camera_status()
        if not camera_status["connected"]:
            self.gesture_manager.start_camera_with_settings(
                width=settings.CAMERA_WIDTH,
                height=settings.CAMERA_HEIGHT
            )
        
        # Subscribe to relevant gestures with the event handler
        self.gesture_manager.subscribe_to_gesture("palm", self.handle_gesture)    # Play/Pause
        self.gesture_manager.subscribe_to_gesture("point", self.handle_gesture)   # Volume control
        self.gesture_manager.subscribe_to_gesture("victory", self.handle_gesture) # Navigation
        self.gesture_manager.subscribe_to_gesture("fist", self.handle_gesture)    # Mute
        
        # Start processing if not already running
        if not self.gesture_manager._running:
            self.gesture_manager.start_processing()
        
        # Start the display and processing loop in a background thread
        self.running = True
        self.display_thread = threading.Thread(target=self.display_loop)
        self.display_thread.daemon = True
        self.display_thread.start()
        
        print("Multimedia controller started")
        print("Press 'q' to quit")
    
    def stop(self):
        """
        Stop the controller, unsubscribe from gestures,
        and stop the display thread.
        """
        self.running = False
        
        if self.display_thread and self.display_thread.is_alive():
            self.display_thread.join(timeout=1.0)
        
        # Unsubscribe from all gestures
        self.gesture_manager.unsubscribe_from_gesture("palm")
        self.gesture_manager.unsubscribe_from_gesture("point")
        self.gesture_manager.unsubscribe_from_gesture("victory")
        self.gesture_manager.unsubscribe_from_gesture("fist")
        
        print("Multimedia controller stopped")
    
    def handle_gesture(self, event_type, gesture_data):
        """
        Handle gesture events emitted by the gesture manager.
        
        Args:
            event_type (str): Type of gesture event ('detected', 'updated', 'ended').
            gesture_data (dict): Data related to the gesture.
        """
        gesture_id = gesture_data.get("id")
        
        with self.lock:
            if event_type == "detected":
                # New gesture detected: track it and start timer
                self.active_gestures[gesture_id] = gesture_data
                self.gesture_messages[gesture_id] = f"{gesture_data.get('name')} detected!"
                
                self.current_gesture = gesture_id
                self.gesture_start_time = time.time()
                self.gesture_duration = 0
                
                # Reset hand positions tracking for relevant gestures
                if gesture_id in ["point", "victory"]:
                    self.hand_positions = []
                
            elif event_type == "updated":
                # Update gesture info and duration
                self.active_gestures[gesture_id] = gesture_data
                if self.current_gesture == gesture_id:
                    self.gesture_duration = time.time() - self.gesture_start_time
                    
                    # Track hand position for volume/navigation gestures
                    if gesture_id in ["point", "victory"]:
                        landmarks = gesture_data.get("landmarks")
                        if landmarks:
                            hand_x = int(landmarks.landmark[0].x * settings.CAMERA_WIDTH)
                            hand_y = int(landmarks.landmark[0].y * settings.CAMERA_HEIGHT)
                            self.hand_positions.append((hand_x, hand_y))
                            # Limit history size
                            if len(self.hand_positions) > self.position_history_size:
                                self.hand_positions.pop(0)
                    
                    # Trigger action if gesture held long enough
                    if self.gesture_duration >= self.required_duration:
                        self.process_gesture_action(gesture_id)
                
            elif event_type == "ended":
                # Gesture ended: clean up
                if gesture_id in self.active_gestures:
                    del self.active_gestures[gesture_id]
                    if self.current_gesture == gesture_id:
                        self.current_gesture = None
                        self.gesture_duration = 0
                        self.hand_positions = []
                    
                    # Show a brief message indicating gesture ended
                    self.gesture_messages[gesture_id] = f"{gesture_id} ended"
                    threading.Timer(2.0, lambda: self.remove_message(gesture_id)).start()
    
    def process_gesture_action(self, gesture_id):
        """
        Process and execute the media action corresponding to the recognized gesture.
        
        Args:
            gesture_id (str): The gesture identifier.
        """
        current_time = time.time()
        
        # Enforce cooldown to avoid repeated triggers
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
    
    def detect_vertical_movement(self):
        """
        Detect vertical hand movement to control volume.
        
        Returns:
            str or None: 'volume_up', 'volume_down', or None if no significant movement.
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
        Detect horizontal swipe gestures for navigation.
        
        Returns:
            str or None: 'swipe_right', 'swipe_left', or None if no significant movement.
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
        Execute the multimedia action triggered by a gesture.
        
        Args:
            action (str): The action to perform.
        """
        if action == "play_pause":
            pyautogui.press('space')
            self.set_action_message("Play/Pause")
        elif action == "swipe_right":
            pyautogui.press('right')
            self.set_action_message("Next/Forward")
        elif action == "swipe_left":
            pyautogui.press('left')
            self.set_action_message("Previous/Back")
        elif action == "volume_up":
            current_volume = self.volume.GetMasterVolumeLevelScalar()
            new_volume = min(1.0, current_volume + 0.05)
            self.volume.SetMasterVolumeLevelScalar(new_volume, None)
            volume_percent = int(new_volume * 100)
            self.set_action_message(f"Volume: {volume_percent}%")
        elif action == "volume_down":
            current_volume = self.volume.GetMasterVolumeLevelScalar()
            new_volume = max(0.0, current_volume - 0.05)
            self.volume.SetMasterVolumeLevelScalar(new_volume, None)
            volume_percent = int(new_volume * 100)
            self.set_action_message(f"Volume: {volume_percent}%")
        elif action == "mute":
            is_muted = self.volume.GetMute()
            self.volume.SetMute(not is_muted, None)
            self.set_action_message("Mute On" if not is_muted else "Mute Off")
        
        self.last_action_time = time.time()
    
    def set_action_message(self, message):
        """
        Set the message to be displayed on screen for the action performed.
        
        Args:
            message (str): The message to display.
        """
        with self.lock:
            self.gesture_messages["action"] = message
            threading.Timer(self.message_duration, lambda: self.remove_message("action")).start()
    
    def remove_message(self, message_id):
        """
        Remove a message after a delay.
        
        Args:
            message_id (str): Identifier of the message to remove.
        """
        with self.lock:
            if message_id in self.gesture_messages:
                del self.gesture_messages[message_id]
    
    def display_loop(self):
        """
        Main loop running in a thread to process frames, display UI,
        and handle quit key press.
        """
        while self.running:
            # Get the current video frame and any other info
            image, _ = self.gesture_manager.process_frame()
            if image is None:
                time.sleep(0.01)
                continue
            
            # Display various UI elements
            self.display_active_gestures(image)
            self.display_messages(image)
            self.display_instructions(image)
            self.display_volume_bar(image)
            
            # Show the frame window
            cv2.imshow('Gesture Multimedia Controller', image)
            
            # Quit on 'q' key press
            if cv2.waitKey(5) & 0xFF == ord('q'):
                break
        
        # Close all OpenCV windows
        cv2.destroyAllWindows()
    
    def display_active_gestures(self, image):
        """
        Display currently active gestures and their confidence scores.
        
        Args:
            image (np.ndarray): The image/frame to draw on.
        """
        with self.lock:
            y_pos = 30
            cv2.putText(image, "ACTIVE GESTURES:", (10, y_pos), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            y_pos += 30
            for gesture_id, gesture_data in self.active_gestures.items():
                confidence = gesture_data.get("confidence", 0) * 100
                text = f"{gesture_data.get('name')}: {confidence:.1f}%"
                cv2.putText(image, text, (10, y_pos), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                y_pos += 25
    
    def display_messages(self, image):
        """
        Display gesture event messages on the image.
        
        Args:
            image (np.ndarray): The image/frame to draw on.
        """
        with self.lock:
            y_pos = image.shape[0] - 60
            for message in self.gesture_messages.values():
                cv2.putText(image, message, (10, y_pos), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                y_pos -= 30
    
    def display_instructions(self, image):
        """
        Display usage instructions on the image.
        
        Args:
            image (np.ndarray): The image/frame to draw on.
        """
        y_pos = 30
        x_pos = image.shape[1] - 250
        
        cv2.putText(image, "INSTRUCTIONS:", (x_pos, y_pos), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        y_pos += 30
        instructions = [
            "Palm: Play/Pause",
            "Point: Volume Control",
            "Victory: Previous/Next",
            "Fist: Mute"
        ]
        
        for instruction in instructions:
            cv2.putText(image, instruction, (x_pos, y_pos), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_pos += 25
    
    def display_volume_bar(self, image):
        """
        Display a volume level bar on the image.
        
        Args:
            image (np.ndarray): The image/frame to draw on.
        """
        try:
            current_volume = self.volume.GetMasterVolumeLevelScalar()
            volume_percent = int(current_volume * 100)
            
            bar_width = 200
            bar_height = 20
            bar_x = image.shape[1] - bar_width - 20
            bar_y = 50
            
            # Draw background bar
            cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), 
                          (100, 100, 100), -1)
            
            # Draw volume fill bar
            filled_width = int(bar_width * current_volume)
            cv2.rectangle(image, (bar_x, bar_y), (bar_x + filled_width, bar_y + bar_height), 
                          (0, 255, 0), -1)
            
            # Draw volume percentage text
            cv2.putText(image, f"Volume: {volume_percent}%", (bar_x, bar_y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        except:
            # Fail silently if volume API unavailable
            pass

# Example usage
def main():
    """
    Entry point of the program: instantiate the controller and start it.
    Runs the main loop until interrupted.
    """
    controller = MultimediaController()
    try:
        controller.start()
        # Main thread sleeps; display runs in its own thread
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Program interrupted by user")
    finally:
        controller.stop()

if __name__ == "__main__":
    main()
