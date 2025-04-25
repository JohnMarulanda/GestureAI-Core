import cv2
import pyautogui
import time
from core.gesture_detector import GestureDetector

class NavigationController(GestureDetector):
    """Controller for window navigation using hand gestures."""
    
    def __init__(self):
        """Initialize the window navigation controller."""
        super().__init__()
        
        # Gesture cooldown to prevent multiple triggers
        self.last_action_time = time.time()
        self.cooldown = 1.0  # seconds
        
        # Current action being performed
        self.current_action = "None"
        self.action_display_time = 0
        
        # Gesture definitions
        self.gestures = {
            "Alt+Tab": "Index and middle finger extended",
            "Minimize": "Closed fist",
            "Maximize": "All fingers extended",
            "Close Window": "Thumb and pinky extended"
        }
        
        print("Window Navigation Controller initialized")
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
        if finger_states == [0, 0, 0, 0, 0]:  # Closed fist
            return "Minimize"
        elif finger_states == [0, 1, 1, 0, 0]:  # Index and middle finger extended
            return "Alt+Tab"
        elif finger_states == [1, 1, 1, 1, 1]:  # All fingers extended
            return "Maximize"
        elif finger_states == [1, 0, 0, 0, 1]:  # Thumb and pinky extended
            return "Close Window"
        else:
            return None
    
    def perform_action(self, gesture):
        """Execute the corresponding window action based on the detected gesture"""
        current_time = time.time()
        
        # Check cooldown to prevent multiple triggers
        if current_time - self.last_action_time < self.cooldown:
            return
        
        if gesture == "Alt+Tab":
            pyautogui.hotkey('alt', 'tab')
            self.current_action = "Switching Applications"
        elif gesture == "Minimize":
            pyautogui.hotkey('win', 'down')
            self.current_action = "Minimizing Window"
        elif gesture == "Maximize":
            pyautogui.hotkey('win', 'up')
            self.current_action = "Maximizing Window"
        elif gesture == "Close Window":
            pyautogui.hotkey('alt', 'f4')
            self.current_action = "Closing Window"
        else:
            return
        
        self.last_action_time = current_time
        self.action_display_time = current_time
    
    def display_instructions(self, frame):
        """Display the list of available gestures and their functions"""
        y_pos = 30
        cv2.putText(frame, "GESTURE CONTROLS:", (10, y_pos), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        y_pos += 30
        for action, description in self.gestures.items():
            cv2.putText(frame, f"{action}: {description}", (10, y_pos), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_pos += 25
    
    def display_current_action(self, frame):
        """Display the current action being performed"""
        if time.time() - self.action_display_time < 2.0:  # Show for 2 seconds
            cv2.putText(frame, f"Action: {self.current_action}", (10, frame.shape[0] - 20), 
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
                
                # Display current action
                self.display_current_action(image)
                
                # If hands are detected
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        # Draw hand landmarks
                        self.drawing_utils.draw_landmarks(
                            image, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                        
                        # Detect gesture
                        gesture = self.detect_gesture(hand_landmarks)
                        
                        # Display detected gesture
                        if gesture:
                            cv2.putText(image, f"Detected: {gesture}", (10, image.shape[0] - 50), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                            
                            # Perform the corresponding action
                            self.perform_action(gesture)
                
                # Display the frame
                cv2.imshow('Window Navigation with Hand Gestures', image)
                
                # Exit on 'q' key press
                if cv2.waitKey(5) & 0xFF == ord('q'):
                    break
        
        finally:
            self.stop_camera()