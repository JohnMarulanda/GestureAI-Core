import cv2
import pyautogui
from core.gesture_detector import GestureDetector

class VolumeController(GestureDetector):
    """Controller for adjusting system volume using hand gestures."""
    
    def __init__(self):
        """Initialize the volume controller with specific thresholds."""
        super().__init__()
        # Thresholds for volume control
        self.TOLERANCE_UPPER = 20  # Threshold to increase volume
        self.TOLERANCE_LOWER = 40  # Threshold to decrease volume
        self.action_delay = 0.3    # Time between volume adjustments
    
    def adjust_volume(self, distance):
        """
        Adjust volume based on the distance between thumb and index finger.
        
        Args:
            distance: The scaled distance between thumb and index finger
        """
        if distance > self.TOLERANCE_UPPER:
            # Calculate how many times to increase volume based on distance
            times_to_increase = int((distance - self.TOLERANCE_UPPER) / 2)
            times_to_increase = max(1, min(times_to_increase, 5))  # Limit between 1 and 5
            for _ in range(times_to_increase):
                pyautogui.press('volumeup')
                
        elif distance < self.TOLERANCE_LOWER:
            # Calculate how many times to decrease volume based on distance
            times_to_decrease = int((self.TOLERANCE_LOWER - distance) / 2)
            times_to_decrease = max(1, min(times_to_decrease, 5))  # Limit between 1 and 5
            for _ in range(times_to_decrease):
                pyautogui.press('volumedown')
    
    def run(self):
        """Run the volume control loop."""
        if not self.start_camera():
            print("Failed to open webcam")
            return
            
        try:
            while True:
                image, results = self.process_frame()
                if image is None:
                    break
                
                # Get image dimensions
                frame_height, frame_width, _ = image.shape
                
                # Initialize finger positions
                thumb_pos = index_pos = None
                
                # Process hand landmarks if hands are detected
                if results.multi_hand_landmarks:
                    for hand in results.multi_hand_landmarks:
                        self.drawing_utils.draw_landmarks(image, hand)
                        landmarks = hand.landmark
                        
                        # Get thumb and index finger positions
                        for id, landmark in enumerate(landmarks):
                            x, y = self.get_landmark_coordinates(landmark, frame_width, frame_height)
                            
                            if id == 8:  # Index finger tip
                                cv2.circle(image, (x, y), 8, (0, 255, 255), 3)
                                index_pos = (x, y)
                                
                            if id == 4:  # Thumb tip
                                cv2.circle(image, (x, y), 8, (0, 0, 255), 3)
                                thumb_pos = (x, y)
                        
                        # If both thumb and index are detected
                        if thumb_pos and index_pos:
                            # Draw line between fingers
                            cv2.line(image, index_pos, thumb_pos, (0, 0, 255), 5)
                            
                            # Calculate distance and scale it
                            distance = self.calculate_distance(index_pos, thumb_pos) // 4
                            
                            # Adjust volume if enough time has passed since last adjustment
                            if self.can_perform_action(self.action_delay):
                                self.adjust_volume(distance)
                
                # Display the image
                cv2.imshow('Volume Control Gestures', image)
                
                # Exit on ESC key
                if cv2.waitKey(10) == 27:
                    break
                    
        finally:
            self.stop_camera()