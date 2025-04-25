import cv2
import pyautogui
import time
import numpy as np
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from core.gesture_detector import GestureDetector

class MultimediaController(GestureDetector):
    """Controller for multimedia operations using hand gestures."""
    
    def __init__(self):
        """Initialize the multimedia controller."""
        super().__init__()
        
        # Initialize volume control using pycaw
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(interface, POINTER(IAudioEndpointVolume))
        self.volume_range = self.volume.GetVolumeRange()
        
        # Gesture tracking variables
        self.last_gesture = None
        self.gesture_start_time = 0
        self.gesture_duration = 0
        self.required_duration = 0.5  # Seconds to hold gesture before action
        
        # Hand position tracking for swipe gestures
        self.prev_hand_x = None
        self.prev_hand_y = None
        self.hand_positions = []  # Store recent hand positions for swipe detection
        self.position_history_size = 10
        
        # Action status
        self.action_message = ""
        self.action_message_time = 0
        self.action_message_duration = 2.0  # Seconds to display action message
        
        # Cooldown to prevent rapid repeated actions
        self.last_action_time = 0
        self.action_cooldown = 1.0  # Seconds between actions
        
        # Define gesture thresholds
        self.volume_change_threshold = 30  # Vertical movement threshold for volume change
        self.swipe_threshold = 50  # Horizontal movement threshold for next/previous track
        
        print("Multimedia Controller initialized")
        print("Press 'q' to quit")
    
    def detect_hand_gesture(self, hand_landmarks, frame_width, frame_height):
        """Detect which gesture is being performed based on hand landmarks"""
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
        
        # Calculate hand center position
        hand_x = int(hand_landmarks.landmark[0].x * frame_width)
        hand_y = int(hand_landmarks.landmark[0].y * frame_height)
        
        # Update hand position history
        self.hand_positions.append((hand_x, hand_y))
        if len(self.hand_positions) > self.position_history_size:
            self.hand_positions.pop(0)
        
        # Identify gestures based on finger states
        if finger_states == [1, 1, 1, 1, 1]:  # All fingers extended (open palm)
            return "play_pause", hand_x, hand_y
        elif finger_states == [0, 1, 0, 0, 0]:  # Only index finger extended
            return "volume_control", hand_x, hand_y
        elif finger_states == [0, 1, 1, 0, 0]:  # Index and middle finger extended
            return "seek_control", hand_x, hand_y
        elif finger_states == [0, 0, 0, 0, 0]:  # Closed fist
            return "mute", hand_x, hand_y
        else:
            return None, hand_x, hand_y
    
    def detect_swipe(self):
        """Detect horizontal swipe gestures based on hand position history"""
        if len(self.hand_positions) < self.position_history_size:
            return None
        
        # Calculate horizontal movement
        start_x = self.hand_positions[0][0]
        end_x = self.hand_positions[-1][0]
        movement_x = end_x - start_x
        
        # Check if movement exceeds threshold
        if movement_x > self.swipe_threshold:
            return "swipe_right"
        elif movement_x < -self.swipe_threshold:
            return "swipe_left"
        
        return None
    
    def detect_vertical_movement(self):
        """Detect vertical movement for volume control"""
        if len(self.hand_positions) < self.position_history_size:
            return None
        
        # Calculate vertical movement
        start_y = self.hand_positions[0][1]
        end_y = self.hand_positions[-1][1]
        movement_y = end_y - start_y
        
        # Check if movement exceeds threshold
        if movement_y > self.volume_change_threshold:
            return "volume_down"
        elif movement_y < -self.volume_change_threshold:
            return "volume_up"
        
        return None
    
    def perform_action(self, action):
        """Execute the corresponding multimedia action"""
        current_time = time.time()
        
        # Check cooldown to prevent multiple triggers
        if current_time - self.last_action_time < self.action_cooldown:
            return
        
        if action == "play_pause":
            pyautogui.press('space')
            self.set_action_message("Play/Pause")
        elif action == "swipe_right":
            pyautogui.press('right')
            self.set_action_message("Next/Forward")
        elif action == "swipe_left":
            pyautogui.press('left')
            self.set_action_message("Previous/Rewind")
        elif action == "volume_up":
            # Get current volume and increase it
            current_volume = self.volume.GetMasterVolumeLevelScalar()
            new_volume = min(1.0, current_volume + 0.05)
            self.volume.SetMasterVolumeLevelScalar(new_volume, None)
            volume_percent = int(new_volume * 100)
            self.set_action_message(f"Volume Up: {volume_percent}%")
        elif action == "volume_down":
            # Get current volume and decrease it
            current_volume = self.volume.GetMasterVolumeLevelScalar()
            new_volume = max(0.0, current_volume - 0.05)
            self.volume.SetMasterVolumeLevelScalar(new_volume, None)
            volume_percent = int(new_volume * 100)
            self.set_action_message(f"Volume Down: {volume_percent}%")
        elif action == "mute":
            # Toggle mute state
            is_muted = self.volume.GetMute()
            self.volume.SetMute(not is_muted, None)
            self.set_action_message("Mute Toggled")
        
        self.last_action_time = current_time
    
    def set_action_message(self, message):
        """Set the action message to display on screen"""
        self.action_message = message
        self.action_message_time = time.time()
        print(f"Action: {message}")
    
    def display_action_message(self, frame):
        """Display the current action message"""
        if time.time() - self.action_message_time < self.action_message_duration:
            cv2.putText(frame, f"Action: {self.action_message}", (10, frame.shape[0] - 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    def display_instructions(self, frame):
        """Display the list of available gestures and their functions"""
        instructions = [
            "MULTIMEDIA CONTROL GESTURES:",
            "Open Palm: Play/Pause",
            "Index Finger: Volume Control (Move Up/Down)",
            "Index+Middle Fingers: Seek Control (Swipe Left/Right)",
            "Closed Fist: Mute Toggle"
        ]
        
        y_pos = 30
        for instruction in instructions:
            cv2.putText(frame, instruction, (10, y_pos), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            y_pos += 30
    
    def display_volume_bar(self, frame):
        """Display a volume level bar"""
        try:
            current_volume = self.volume.GetMasterVolumeLevelScalar()
            volume_percent = int(current_volume * 100)
            
            bar_width = 200
            bar_height = 20
            bar_x = frame.shape[1] - bar_width - 20
            bar_y = 50
            
            # Draw background bar
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), 
                          (100, 100, 100), -1)
            
            # Draw filled volume bar
            filled_width = int(bar_width * current_volume)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + filled_width, bar_y + bar_height), 
                          (0, 255, 0), -1)
            
            # Draw volume percentage text
            cv2.putText(frame, f"Volume: {volume_percent}%", (bar_x, bar_y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        except:
            pass
    
    def run(self):
        """Main loop to capture video and process hand gestures"""
        if not self.start_camera():
            print("Failed to open webcam")
            return
        
        try:
            while True:
                image, results = self.process_frame()
                if image is None:
                    break
                
                # Display instructions and volume bar
                self.display_instructions(image)
                self.display_volume_bar(image)
                
                # Display action message if any
                self.display_action_message(image)
                
                # Get frame dimensions
                frame_height, frame_width, _ = image.shape
                
                # If hands are detected
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        # Draw hand landmarks
                        self.drawing_utils.draw_landmarks(
                            image, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                        
                        # Detect gesture
                        gesture, hand_x, hand_y = self.detect_hand_gesture(hand_landmarks, frame_width, frame_height)
                        
                        # Track gesture duration
                        current_time = time.time()
                        if gesture:
                            if gesture == self.last_gesture:
                                self.gesture_duration = current_time - self.gesture_start_time
                            else:
                                self.last_gesture = gesture
                                self.gesture_start_time = current_time
                                self.gesture_duration = 0
                            
                            # Display detected gesture
                            cv2.putText(image, f"Gesture: {gesture}", (10, image.shape[0] - 50), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                            
                            # If gesture held long enough, perform corresponding action
                            if self.gesture_duration >= self.required_duration:
                                if gesture == "play_pause":
                                    self.perform_action("play_pause")
                                elif gesture == "volume_control":
                                    # Check for vertical movement
                                    vertical_action = self.detect_vertical_movement()
                                    if vertical_action:
                                        self.perform_action(vertical_action)
                                        # Reset hand positions after action
                                        self.hand_positions = []
                                elif gesture == "seek_control":
                                    # Check for horizontal swipe
                                    swipe_action = self.detect_swipe()
                                    if swipe_action:
                                        self.perform_action(swipe_action)
                                        # Reset hand positions after action
                                        self.hand_positions = []
                                elif gesture == "mute":
                                    self.perform_action("mute")
                        else:
                            self.last_gesture = None
                            self.gesture_duration = 0
                else:
                    self.last_gesture = None
                    self.gesture_duration = 0
                    self.hand_positions = []
                
                # Display the frame
                cv2.imshow('Multimedia Control with Hand Gestures', image)
                
                # Exit on 'q' key press
                if cv2.waitKey(5) & 0xFF == ord('q'):
                    break
        
        finally:
            self.stop_camera()