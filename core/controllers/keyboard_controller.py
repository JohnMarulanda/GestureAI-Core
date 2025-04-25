import cv2
import math
import time
from pynput.keyboard import Controller
import cvzone
from core.gesture_detector import GestureDetector

class KeyboardController(GestureDetector):
    """Controller for virtual keyboard using hand gestures."""
    
    def __init__(self):
        """Initialize the virtual keyboard controller."""
        super().__init__()
        
        # Initialize keyboard controller
        self.keyboard = Controller()
        
        # Text input
        self.final_text = ""
        
        # Define keyboard layout
        self.keys = [
            ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
            ["A", "S", "D", "F", "G", "H", "J", "K", "L", ";"],
            ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", "Del"]
        ]
        
        # Create button objects
        self.button_list = []
        self.create_buttons()
        
        # Gesture tracking
        self.last_press_time = 0
        self.press_cooldown = 0.15  # Seconds between key presses
        
        print("Virtual Keyboard Controller initialized")
        print("Press 'q' to quit")
    
    def create_buttons(self):
        """Create button objects for each key in the keyboard layout."""
        for i in range(len(self.keys)):
            for j, key in enumerate(self.keys[i]):
                self.button_list.append(self.Button([100 * j + 50, 100 * i + 50], key))
    
    class Button:
        """Button class for keyboard keys."""
        def __init__(self, pos, text, size=[85, 85]):
            self.pos = pos
            self.size = size
            self.text = text
    
    def calculate_distance(self, point1, point2):
        """Calculate Euclidean distance between two points."""
        x1, y1 = point1[0], point1[1]
        x2, y2 = point2[0], point2[1]
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    def draw_all_buttons(self, img):
        """Draw all keyboard buttons on the image."""
        for button in self.button_list:
            x, y = button.pos
            w, h = button.size
            cvzone.cornerRect(img, (x, y, w, h), 20, rt=0)
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 255), cv2.FILLED)
            cv2.putText(img, button.text, (x + 20, y + 65), 
                        cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)
        return img
    
    def draw_text_box(self, img):
        """Draw the text box showing the typed text."""
        cv2.rectangle(img, (50, 350), (700, 450), (175, 0, 175), cv2.FILLED)
        cv2.putText(img, self.final_text, (60, 430), 
                    cv2.FONT_HERSHEY_PLAIN, 5, (255, 255, 255), 5)
        return img
    
    def process_key_press(self, button_text):
        """Process a key press action."""
        current_time = time.time()
        
        # Check cooldown to prevent multiple triggers
        if current_time - self.last_press_time < self.press_cooldown:
            return
        
        if button_text == "Del":
            if self.final_text:
                self.final_text = self.final_text[:-1]  # Remove last character
                self.keyboard.press('\b')  # Backspace
        else:
            self.keyboard.press(button_text)
            self.final_text += button_text
        
        self.last_press_time = current_time
    
    def run(self):
        """Main loop to capture video and process hand gestures for keyboard control."""
        if not self.start_camera(width=1280, height=720):
            print("Failed to open webcam")
            return
        
        try:
            while True:
                image, results = self.process_frame()
                if image is None:
                    break
                
                # Draw keyboard buttons
                image = self.draw_all_buttons(image)
                
                # Draw text box
                image = self.draw_text_box(image)
                
                # Process hand landmarks if hands are detected
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        # Draw hand landmarks
                        self.drawing_utils.draw_landmarks(
                            image, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                        
                        # Get index finger and middle finger positions
                        index_finger = None
                        middle_finger = None
                        
                        for id, landmark in enumerate(hand_landmarks.landmark):
                            h, w, c = image.shape
                            cx, cy = int(landmark.x * w), int(landmark.y * h)
                            
                            if id == 8:  # Index finger tip
                                index_finger = [cx, cy]
                                cv2.circle(image, (cx, cy), 15, (255, 0, 255), cv2.FILLED)
                            
                            if id == 12:  # Middle finger tip
                                middle_finger = [cx, cy]
                                cv2.circle(image, (cx, cy), 15, (0, 255, 0), cv2.FILLED)
                        
                        # Check if fingers are detected
                        if index_finger and middle_finger:
                            # Check for button hover and press
                            for button in self.button_list:
                                x, y = button.pos
                                w, h = button.size
                                
                                # If index finger is over a button
                                if x < index_finger[0] < x + w and y < index_finger[1] < y + h:
                                    # Highlight the button
                                    cv2.rectangle(image, (x - 5, y - 5), (x + w + 5, y + h + 5), 
                                                 (175, 0, 175), cv2.FILLED)
                                    cv2.putText(image, button.text, (x + 20, y + 65), 
                                               cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)
                                    
                                    # Calculate distance between index and middle finger
                                    l = self.calculate_distance(index_finger, middle_finger)
                                    
                                    # If fingers are close (pinch gesture), press the key
                                    if l < 30:
                                        self.process_key_press(button.text)
                
                # Display the frame
                cv2.imshow('Virtual Keyboard with Hand Gestures', image)
                
                # Exit on 'q' key press
                if cv2.waitKey(5) & 0xFF == ord('q'):
                    break
        
        finally:
            self.stop_camera()