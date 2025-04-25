import cv2
import pyautogui
import time
import json
import os
from core.gesture_detector import GestureDetector

class ShortcutsController(GestureDetector):
    """Controller for executing keyboard shortcuts using hand gestures."""
    
    def __init__(self):
        """Initialize the shortcuts controller."""
        super().__init__()
        
        # Gesture tracking variables
        self.current_gesture = None
        self.gesture_start_time = 0
        self.gesture_duration = 0
        self.required_duration = 1.0  # Seconds to hold gesture before action
        
        # Action status
        self.action_message = ""
        self.action_message_time = 0
        self.action_message_duration = 3.0  # Seconds to display action message
        
        # Load configuration
        self.config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                       "config", "keyboard_gestures.json")
        self.load_config()
    
    def load_config(self):
        """Load gesture-to-shortcut mappings from config file"""
        default_config = {
            "gestures": {
                "copy": {
                    "shortcut": ["ctrl", "c"],
                    "gesture": [0, 1, 1, 0, 0]  # Index and middle finger extended
                },
                "paste": {
                    "shortcut": ["ctrl", "v"],
                    "gesture": [1, 1, 0, 0, 0]  # Thumb and index finger extended
                },
                "alt_tab": {
                    "shortcut": ["alt", "tab"],
                    "gesture": [0, 1, 1, 1, 0]  # Index, middle, and ring finger extended
                },
                "task_manager": {
                    "shortcut": ["ctrl", "shift", "esc"],
                    "gesture": [1, 1, 1, 0, 0]  # Thumb, index, and middle finger extended
                },
                "refresh": {
                    "shortcut": ["f5"],
                    "gesture": [0, 0, 0, 0, 1]  # Pinky finger extended
                },
                "escape": {
                    "shortcut": ["esc"],
                    "gesture": [0, 0, 0, 0, 0]  # Closed fist
                }
            }
        }
        
        try:
            # Create config directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = default_config
                self.save_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            print(f"Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def detect_gesture(self, hand_landmarks):
        """Detect finger positions and return as a list of 0s and 1s"""
        # Get fingertip landmarks
        fingertips = [4, 8, 12, 16, 20]  # Thumb, index, middle, ring, pinky
        finger_states = []
        
        # Check if fingers are extended
        for tip_id in fingertips:
            # For thumb, compare x-coordinate with the base of the thumb
            if tip_id == 4:
                if hand_landmarks.landmark[tip_id].x < hand_landmarks.landmark[tip_id - 2].x:
                    finger_states.append(1)  # Extended
                else:
                    finger_states.append(0)  # Not extended
            # For other fingers, compare y-coordinate with the middle joint
            else:
                if hand_landmarks.landmark[tip_id].y < hand_landmarks.landmark[tip_id - 2].y:
                    finger_states.append(1)  # Extended
                else:
                    finger_states.append(0)  # Not extended
        
        return finger_states
    
    def identify_shortcut(self, finger_states):
        """Identify which shortcut to execute based on the detected gesture"""
        for shortcut_name, config in self.config["gestures"].items():
            if finger_states == config["gesture"]:
                return shortcut_name, config["shortcut"]
        
        return None, None
    
    def execute_shortcut(self, keys):
        """Execute the keyboard shortcut using pyautogui"""
        try:
            pyautogui.hotkey(*keys)
            return True
        except Exception as e:
            print(f"Error executing shortcut: {e}")
            return False
    
    def set_action_message(self, message):
        """Set the action message to display on screen"""
        self.action_message = message
        self.action_message_time = time.time()
        print(message)
    
    def display_instructions(self, frame):
        """Display the list of configured gestures and their shortcuts"""
        y_pos = 30
        cv2.putText(frame, "KEYBOARD SHORTCUT GESTURES:", (10, y_pos), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        y_pos += 30
        for shortcut_name, config in self.config["gestures"].items():
            shortcut_str = "+".join(config["shortcut"])
            gesture_str = "".join([str(g) for g in config["gesture"]])
            cv2.putText(frame, f"{shortcut_name} ({shortcut_str}): {gesture_str}", (10, y_pos), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_pos += 25
    
    def display_action_message(self, frame):
        """Display the current action message"""
        if time.time() - self.action_message_time < self.action_message_duration:
            cv2.putText(frame, self.action_message, (10, frame.shape[0] - 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    def display_gesture_progress(self, frame, shortcut_name, keys):
        """Display progress bar for gesture duration"""
        if self.gesture_duration > 0:
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
            
            # Draw text
            shortcut_str = "+".join(keys)
            cv2.putText(frame, f"Detecting: {shortcut_name} ({shortcut_str}) ({int(progress * 100)}%)", 
                        (bar_x, bar_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def add_shortcut_config(self, shortcut_name, keys, gesture):
        """Add or update a shortcut configuration"""
        self.config["gestures"][shortcut_name] = {
            "shortcut": keys,
            "gesture": gesture
        }
        
        # Save the updated configuration
        self.save_config()
        return True
    
    def remove_shortcut_config(self, shortcut_name):
        """Remove a shortcut configuration"""
        if shortcut_name in self.config["gestures"]:
            del self.config["gestures"][shortcut_name]
            
            # Save the updated configuration
            self.save_config()
            return True
        
        return False
    
    def run(self):
        """Main loop to capture video and process hand gestures"""
        print("Starting Keyboard Shortcut Gesture Controller...")
        print("Press 'q' to quit, 's' to save current hand position as a new shortcut")
        
        if not self.start_camera():
            print("Failed to open webcam")
            return
            
        add_mode = False
        new_gesture = None
        new_shortcut_name = None
        new_keys = None
        
        try:
            while True:
                image, results = self.process_frame()
                if image is None:
                    break
                
                # Display instructions
                self.display_instructions(image)
                
                # Display action message if any
                self.display_action_message(image)
                
                # If in add mode, display instructions for adding a new shortcut
                if add_mode:
                    cv2.putText(image, "ADD NEW SHORTCUT", (image.shape[1] // 2 - 100, 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    
                    if new_shortcut_name and new_keys:
                        cv2.putText(image, f"Position hand for {new_shortcut_name} ({'+'.join(new_keys)})", 
                                    (image.shape[1] // 2 - 150, 60), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                        cv2.putText(image, "Press 's' to save, 'q' to cancel", 
                                    (image.shape[1] // 2 - 150, 90), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                
                # If hands are detected
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        # Draw hand landmarks
                        self.drawing_utils.draw_landmarks(
                            image, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                        
                        # Detect finger states
                        finger_states = self.detect_gesture(hand_landmarks)
                        
                        # Display finger states
                        finger_state_str = "".join([str(s) for s in finger_states])
                        cv2.putText(image, f"Gesture: {finger_state_str}", 
                                    (10, image.shape[0] - 90), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                        
                        # If in add mode, store the current gesture
                        if add_mode and new_shortcut_name and new_keys:
                            new_gesture = finger_states
                        else:
                            # Identify shortcut based on gesture
                            shortcut_name, keys = self.identify_shortcut(finger_states)
                            
                            # Track gesture duration
                            current_time = time.time()
                            if shortcut_name and keys:
                                if (shortcut_name, tuple(keys)) == self.current_gesture:
                                    self.gesture_duration = current_time - self.gesture_start_time
                                else:
                                    self.current_gesture = (shortcut_name, tuple(keys))
                                    self.gesture_start_time = current_time
                                    self.gesture_duration = 0
                                
                                # Display gesture progress
                                self.display_gesture_progress(image, shortcut_name, keys)
                                
                                # If gesture held long enough, execute the shortcut
                                if self.gesture_duration >= self.required_duration:
                                    if self.execute_shortcut(keys):
                                        self.set_action_message(f"Executed: {shortcut_name} ({'+'.join(keys)})")
                                    else:
                                        self.set_action_message(f"Failed to execute: {shortcut_name}")
                                    
                                    self.current_gesture = None
                                    self.gesture_duration = 0
                            else:
                                self.current_gesture = None
                                self.gesture_duration = 0
                else:
                    self.current_gesture = None
                    self.gesture_duration = 0
                
                # Display the frame
                cv2.imshow('Keyboard Shortcut Gesture Controller', image)
                
                # Handle key presses
                key = cv2.waitKey(5) & 0xFF
                if key == ord('q'):
                    if add_mode:
                        add_mode = False
                        new_gesture = None
                        new_shortcut_name = None
                        new_keys = None
                    else:
                        break
                elif key == ord('s'):
                    if add_mode and new_gesture and new_shortcut_name and new_keys:
                        # Add the new shortcut configuration
                        self.add_shortcut_config(new_shortcut_name, new_keys, new_gesture)
                        self.set_action_message(f"Added shortcut: {new_shortcut_name} ({'+'.join(new_keys)})")
                        
                        add_mode = False
                        new_gesture = None
                        new_shortcut_name = None
                        new_keys = None
                    else:
                        add_mode = True
                        new_shortcut_name = input("Enter shortcut name (e.g., 'copy', 'paste'): ")
                        if not new_shortcut_name:
                            print("Shortcut name cannot be empty.")
                            add_mode = False
                            continue
                        
                        keys_input = input("Enter keys separated by commas (e.g., 'ctrl,c' or 'alt,tab'): ")
                        new_keys = [key.strip() for key in keys_input.split(',')]
                        if not new_keys:
                            print("Keys cannot be empty.")
                            add_mode = False
                            continue
                
        finally:
            self.stop_camera()