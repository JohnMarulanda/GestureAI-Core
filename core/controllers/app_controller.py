import cv2
import time
import subprocess
import psutil
import os
import json
from core.gesture_detector import GestureDetector

class AppController(GestureDetector):
    """Controller for opening and closing applications using hand gestures."""
    
    def __init__(self):
        """Initialize the application controller."""
        super().__init__()
        
        # Gesture tracking variables
        self.current_gesture = None
        self.gesture_start_time = 0
        self.gesture_duration = 0
        self.required_duration = 2.0  # Seconds to hold gesture before action
        self.confirmation_required = True  # Whether to require confirmation for closing apps
        
        # Action status
        self.action_message = ""
        self.action_message_time = 0
        self.action_message_duration = 3.0  # Seconds to display action message
        
        # Load configuration
        self.config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                       "config", "app_gestures.json")
        self.load_config()
        
        # Running applications tracking
        self.running_apps = {}  # {app_name: process}
    
    def load_config(self):
        """Load gesture-to-application mappings from config file"""
        default_config = {
            "gestures": {
                "open": {
                    "Chrome": [0, 1, 1, 0, 0],  # Index and middle finger extended
                    "Notepad": [1, 1, 0, 0, 0],  # Thumb and index finger extended
                    "Calculator": [1, 1, 1, 0, 0]  # Thumb, index, and middle finger extended
                },
                "close": {
                    "Chrome": [0, 0, 0, 0, 0],  # Closed fist
                    "Notepad": [0, 0, 0, 0, 1],  # Pinky finger extended
                    "Calculator": [1, 0, 0, 0, 1]  # Thumb and pinky extended
                }
            },
            "paths": {
                "Chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "Notepad": "notepad.exe",
                "Calculator": "calc.exe"
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
    
    def identify_gesture_action(self, finger_states):
        """Identify which app to open or close based on the detected gesture"""
        # Check for open gestures
        for app_name, gesture in self.config["gestures"]["open"].items():
            if finger_states == gesture:
                return "open", app_name
        
        # Check for close gestures
        for app_name, gesture in self.config["gestures"]["close"].items():
            if finger_states == gesture:
                return "close", app_name
        
        return None, None
    
    def open_application(self, app_name):
        """Open the specified application"""
        app_path = self.config["paths"].get(app_name)
        if not app_path:
            self.set_action_message(f"Error: Path for {app_name} not configured")
            return False
        
        try:
            # Check if app is already running
            if app_name in self.running_apps and self.running_apps[app_name].is_running():
                self.set_action_message(f"{app_name} is already running")
                return True
            
            # Open the application
            process = subprocess.Popen(app_path)
            self.running_apps[app_name] = psutil.Process(process.pid)
            self.set_action_message(f"Opened: {app_name}")
            return True
        except Exception as e:
            self.set_action_message(f"Error opening {app_name}: {e}")
            return False
    
    def close_application(self, app_name):
        """Close the specified application"""
        # If we have a stored process, try to close it
        if app_name in self.running_apps:
            try:
                process = self.running_apps[app_name]
                if process.is_running():
                    process.terminate()
                    self.set_action_message(f"Closed: {app_name}")
                    del self.running_apps[app_name]
                    return True
                else:
                    del self.running_apps[app_name]
            except Exception as e:
                self.set_action_message(f"Error closing stored process for {app_name}: {e}")
        
        # Try to find the process by name
        try:
            found = False
            for proc in psutil.process_iter(['pid', 'name']):
                if app_name.lower() in proc.info['name'].lower():
                    proc.terminate()
                    found = True
            
            if found:
                self.set_action_message(f"Closed: {app_name}")
                return True
            else:
                self.set_action_message(f"{app_name} is not running")
                return False
        except Exception as e:
            self.set_action_message(f"Error closing {app_name}: {e}")
            return False
    
    def set_action_message(self, message):
        """Set the action message to display on screen"""
        self.action_message = message
        self.action_message_time = time.time()
        print(message)
    
    def display_instructions(self, frame):
        """Display the list of configured gestures and their functions"""
        y_pos = 30
        cv2.putText(frame, "APP CONTROL GESTURES:", (10, y_pos), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Display open gestures
        y_pos += 30
        cv2.putText(frame, "OPEN:", (10, y_pos), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        for app_name, gesture in self.config["gestures"]["open"].items():
            y_pos += 25
            gesture_str = "".join([str(g) for g in gesture])
            cv2.putText(frame, f"{app_name}: {gesture_str}", (30, y_pos), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Display close gestures
        y_pos += 35
        cv2.putText(frame, "CLOSE:", (10, y_pos), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        for app_name, gesture in self.config["gestures"]["close"].items():
            y_pos += 25
            gesture_str = "".join([str(g) for g in gesture])
            cv2.putText(frame, f"{app_name}: {gesture_str}", (30, y_pos), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def display_action_message(self, frame):
        """Display the current action message"""
        if time.time() - self.action_message_time < self.action_message_duration:
            cv2.putText(frame, self.action_message, (10, frame.shape[0] - 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    def display_gesture_progress(self, frame, action, app_name):
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
            cv2.putText(frame, f"Detecting: {action.capitalize()} {app_name} ({int(progress * 100)}%)", 
                        (bar_x, bar_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def add_gesture_config(self, action, app_name, app_path, gesture):
        """Add or update a gesture configuration"""
        # Ensure the action is valid
        if action not in ["open", "close"]:
            return False
        
        # Update the gesture configuration
        self.config["gestures"][action][app_name] = gesture
        
        # Update the path if provided
        if app_path and action == "open":
            self.config["paths"][app_name] = app_path
        
        # Save the updated configuration
        self.save_config()
        return True
    
    def remove_gesture_config(self, action, app_name):
        """Remove a gesture configuration"""
        # Ensure the action is valid
        if action not in ["open", "close"]:
            return False
        
        # Remove the gesture configuration
        if app_name in self.config["gestures"][action]:
            del self.config["gestures"][action][app_name]
            
            # If app is completely removed, also remove the path
            if (app_name not in self.config["gestures"]["open"] and 
                app_name not in self.config["gestures"]["close"] and
                app_name in self.config["paths"]):
                del self.config["paths"][app_name]
            
            # Save the updated configuration
            self.save_config()
            return True
        
        return False
    
    def run(self):
        """Main loop to capture video and process hand gestures"""
        print("Starting Application Control with Hand Gestures...")
        print("Press 'q' to quit, 'c' to toggle confirmation, 's' to save current hand position as a new gesture")
        
        if not self.start_camera():
            print("Failed to open webcam")
            return
        
        add_mode = False
        new_gesture = None
        new_action = None
        new_app_name = None
        
        try:
            while True:
                image, results = self.process_frame()
                if image is None:
                    break
                
                # Display instructions
                self.display_instructions(image)
                
                # Display action message if any
                self.display_action_message(image)
                
                # If in add mode, display instructions for adding a new gesture
                if add_mode:
                    cv2.putText(image, "ADD NEW GESTURE", (image.shape[1] // 2 - 100, 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    
                    if new_action and new_app_name:
                        cv2.putText(image, f"Position hand for {new_action} {new_app_name}", 
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
                        if add_mode and new_action and new_app_name:
                            new_gesture = finger_states
                        else:
                            # Identify action based on gesture
                            action, app_name = self.identify_gesture_action(finger_states)
                            
                            # Track gesture duration
                            current_time = time.time()
                            if action and app_name:
                                if (action, app_name) == self.current_gesture:
                                    self.gesture_duration = current_time - self.gesture_start_time
                                else:
                                    self.current_gesture = (action, app_name)
                                    self.gesture_start_time = current_time
                                    self.gesture_duration = 0
                                
                                # Display gesture progress
                                self.display_gesture_progress(image, action, app_name)
                                
                                # If gesture held long enough, perform the action
                                if self.gesture_duration >= self.required_duration:
                                    if action == "open":
                                        self.open_application(app_name)
                                    elif action == "close":
                                        if not self.confirmation_required or self.gesture_duration >= self.required_duration * 1.5:
                                            self.close_application(app_name)
                                    
                                    self.current_gesture = None
                                    self.gesture_duration = 0
                            else:
                                self.current_gesture = None
                                self.gesture_duration = 0
                else:
                    self.current_gesture = None
                    self.gesture_duration = 0
                
                # Display the frame
                cv2.imshow('Application Control with Hand Gestures', image)
                
                # Handle key presses
                key = cv2.waitKey(5) & 0xFF
                if key == ord('q'):
                    if add_mode:
                        add_mode = False
                        new_gesture = None
                        new_action = None
                        new_app_name = None
                    else:
                        break
                elif key == ord('c'):
                    self.confirmation_required = not self.confirmation_required
                    self.set_action_message(f"Confirmation {'enabled' if self.confirmation_required else 'disabled'}")
                elif key == ord('s'):
                    if add_mode and new_gesture and new_action and new_app_name:
                        # Add the new gesture configuration
                        app_path = input(f"Enter path for {new_app_name} (leave empty to use default): ")
                        if not app_path:
                            app_path = new_app_name + ".exe"
                        
                        self.add_gesture_config(new_action, new_app_name, app_path, new_gesture)
                        self.set_action_message(f"Added {new_action} gesture for {new_app_name}")
                        
                        add_mode = False
                        new_gesture = None
                        new_action = None
                        new_app_name = None
                    else:
                        add_mode = True
                        new_action = input("Enter action (open/close): ").lower()
                        if new_action not in ["open", "close"]:
                            print("Invalid action. Must be 'open' or 'close'.")
                            add_mode = False
                            continue
                        
                        new_app_name = input("Enter application name: ")
                        if not new_app_name:
                            print("Application name cannot be empty.")
                            add_mode = False
                            continue
        
        finally:
            self.stop_camera()