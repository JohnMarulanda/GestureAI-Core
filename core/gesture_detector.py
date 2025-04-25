import cv2
import mediapipe as mp
import time

class GestureDetector:
    """Base class for gesture detection using MediaPipe."""
    
    def __init__(self):
        """Initialize the hand detection components."""
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands()
        self.drawing_utils = mp.solutions.drawing_utils
        self.webcam = None
        self.last_action_time = 0
    
    def start_camera(self, camera_id=0):
        """Start the webcam capture."""
        self.webcam = cv2.VideoCapture(camera_id)
        return self.webcam.isOpened()
    
    def stop_camera(self):
        """Release the webcam and destroy all windows."""
        if self.webcam:
            self.webcam.release()
        cv2.destroyAllWindows()
    
    def process_frame(self):
        """Process a single frame from the webcam."""
        if not self.webcam or not self.webcam.isOpened():
            return None, None
            
        success, image = self.webcam.read()
        if not success:
            return None, None
            
        # Flip the image horizontally for a mirror effect
        image = cv2.flip(image, 1)
        
        # Convert the BGR image to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Process the image and find hands
        results = self.hands.process(rgb_image)
        
        return image, results
    
    def get_landmark_coordinates(self, landmark, frame_width, frame_height):
        """Convert normalized landmark coordinates to pixel coordinates."""
        x = int(landmark.x * frame_width)
        y = int(landmark.y * frame_height)
        return x, y
    
    def calculate_distance(self, point1, point2):
        """Calculate Euclidean distance between two points."""
        x1, y1 = point1
        x2, y2 = point2
        return ((x2-x1)**2 + (y2-y1)**2)**(0.5)
    
    def can_perform_action(self, action_delay=0.3):
        """Check if enough time has passed since the last action."""
        current_time = time.time()
        if current_time - self.last_action_time > action_delay:
            self.last_action_time = current_time
            return True
        return False