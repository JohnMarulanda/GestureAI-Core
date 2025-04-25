import cv2
import time
import subprocess
import ctypes
import threading
from core.gesture_detector import GestureDetector

class SystemController(GestureDetector):
    """Controller for system operations using hand gestures."""
    
    def __init__(self):
        """Initialize the system control controller."""
        super().__init__()
        
        # Gesture tracking variables
        self.current_gesture = None
        self.gesture_start_time = 0
        self.gesture_duration = 0
        self.required_duration = 3.0  # Seconds to hold gesture before action
        self.confirmation_active = False
        self.confirmation_action = None
        
        # Action status
        self.action_message = ""
        self.action_message_time = 0
        self.action_message_duration = 3.0  # Seconds to display action message
        
        # Define gestures and their corresponding actions
        self.gestures = {
            "Lock": "L shape (thumb and index extended)",
            "Shutdown": "Closed fist",
            "Restart": "Two fingers extended (index and middle)",
            "Sleep": "Five fingers extended (open hand)"
        }
        
        # Countdown timer for confirmations
        self.countdown_active = False
        self.countdown_start_time = 0
        self.countdown_duration = 5  # 5 seconds countdown
        
        # Thread lock for safe access to shared variables
        self.lock = threading.Lock()
        
        print("System Control Controller initialized")
        print("Press 'q' to quit")
    
    def detect_gesture(self, hand_landmarks):
        """Detect which gesture is being performed based on finger positions"""
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
        
        # Identify gestures based on finger states
        if finger_states == [1, 1, 0, 0, 0]:  # L shape (thumb and index extended)
            return "Lock"
        elif finger_states == [0, 0, 0, 0, 0]:  # Closed fist
            return "Shutdown"
        elif finger_states == [0, 1, 1, 0, 0]:  # Two fingers extended (index and middle)
            return "Restart"
        elif finger_states == [1, 1, 1, 1, 1]:  # Five fingers extended (open hand)
            return "Sleep"
        else:
            return None
    
    def lock_computer(self):
        """Lock the computer screen"""
        with self.lock:
            self.action_message = "Computer Locked"
            self.action_message_time = time.time()
        
        # Use ctypes to lock Windows
        ctypes.windll.user32.LockWorkStation()
    
    def shutdown_computer(self):
        """Shutdown the computer"""
        with self.lock:
            self.action_message = "Computer Shutting Down"
            self.action_message_time = time.time()
        
        # Use subprocess to shutdown Windows
        subprocess.call(['shutdown', '/s', '/t', '1'])
    
    def restart_computer(self):
        """Restart the computer"""
        with self.lock:
            self.action_message = "Computer Restarting"
            self.action_message_time = time.time()
        
        # Use subprocess to restart Windows
        subprocess.call(['shutdown', '/r', '/t', '1'])
    
    def sleep_computer(self):
        """Put the computer to sleep mode"""
        with self.lock:
            self.action_message = "Computer Going to Sleep"
            self.action_message_time = time.time()
        
        # Use subprocess to put Windows to sleep
        subprocess.call(['powershell', '-Command', 'Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState("Suspend", $false, $false)'])
    
    def perform_action(self, gesture):
        """Execute the corresponding system action based on the detected gesture"""
        if gesture == "Lock":
            self.lock_computer()
        elif gesture == "Shutdown":
            self.shutdown_computer()
        elif gesture == "Restart":
            self.restart_computer()
        elif gesture == "Sleep":
            self.sleep_computer()
    
    def start_confirmation(self, action):
        """Start the confirmation process for critical actions"""
        with self.lock:
            self.confirmation_active = True
            self.confirmation_action = action
            self.countdown_active = True
            self.countdown_start_time = time.time()
    
    def cancel_confirmation(self):
        """Cancel the confirmation process"""
        with self.lock:
            self.confirmation_active = False
            self.confirmation_action = None
            self.countdown_active = False
    
    def display_instructions(self, frame):
        """Display the list of available gestures and their functions"""
        y_pos = 30
        cv2.putText(frame, "SYSTEM CONTROL GESTURES:", (10, y_pos), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        y_pos += 30
        for action, description in self.gestures.items():
            cv2.putText(frame, f"{action}: {description}", (10, y_pos), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_pos += 25
    
    def display_action_message(self, frame):
        """Display the current action message"""
        if time.time() - self.action_message_time < self.action_message_duration:
            cv2.putText(frame, self.action_message, (10, frame.shape[0] - 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    def display_gesture_progress(self, frame, gesture):
        """Display progress bar for gesture duration"""
        if gesture and self.gesture_duration > 0:
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
            cv2.putText(frame, f"Detecting: {gesture} ({int(progress * 100)}%)", 
                        (bar_x, bar_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def display_confirmation(self, frame):
        """Display confirmation dialog for critical actions"""
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
            cv2.putText(frame, "Show same gesture again to confirm", 
                        (100, frame.shape[0] // 2), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
            
            cv2.putText(frame, "Any other gesture or wait to cancel", 
                        (100, frame.shape[0] // 2 + 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
            
            # Display countdown
            if self.countdown_active:
                elapsed = time.time() - self.countdown_start_time
                remaining = max(0, self.countdown_duration - elapsed)
                
                if remaining == 0:
                    self.cancel_confirmation()
                else:
                    cv2.putText(frame, f"Canceling in {int(remaining)}s", 
                                (100, frame.shape[0] // 2 + 70), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
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
                
                # Display instructions
                self.display_instructions(image)
                
                # Display action message if any
                self.display_action_message(image)
                
                # Handle confirmation dialog if active
                if self.confirmation_active:
                    self.display_confirmation(image)
                    
                    # If hands are detected during confirmation
                    if results.multi_hand_landmarks:
                        for hand_landmarks in results.multi_hand_landmarks:
                            # Draw hand landmarks
                            self.drawing_utils.draw_landmarks(
                                image, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                            
                            # Detect gesture
                            detected_gesture = self.detect_gesture(hand_landmarks)
                            
                            # If the same gesture is detected, confirm the action
                            if detected_gesture == self.confirmation_action:
                                self.perform_action(detected_gesture)
                                self.cancel_confirmation()
                            # If a different gesture is detected, cancel the confirmation
                            elif detected_gesture is not None:
                                self.cancel_confirmation()
                else:
                    # If hands are detected
                    if results.multi_hand_landmarks:
                        for hand_landmarks in results.multi_hand_landmarks:
                            # Draw hand landmarks
                            self.drawing_utils.draw_landmarks(
                                image, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                            
                            # Detect gesture
                            detected_gesture = self.detect_gesture(hand_landmarks)
                            
                            # Track gesture duration
                            current_time = time.time()
                            if detected_gesture:
                                if detected_gesture == self.current_gesture:
                                    self.gesture_duration = current_time - self.gesture_start_time
                                else:
                                    self.current_gesture = detected_gesture
                                    self.gesture_start_time = current_time
                                    self.gesture_duration = 0
                                
                                # Display gesture progress
                                self.display_gesture_progress(image, detected_gesture)
                                
                                # If gesture held long enough, start confirmation for critical actions
                                if self.gesture_duration >= self.required_duration:
                                    self.start_confirmation(detected_gesture)
                                    self.current_gesture = None
                                    self.gesture_duration = 0
                            else:
                                self.current_gesture = None
                                self.gesture_duration = 0
                    else:
                        self.current_gesture = None
                        self.gesture_duration = 0
                
                # Display the frame
                cv2.imshow('System Control with Hand Gestures', image)
                
                # Exit on 'q' key press
                if cv2.waitKey(5) & 0xFF == ord('q'):
                    break
        
        finally:
            self.stop_camera()