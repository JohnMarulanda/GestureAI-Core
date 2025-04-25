import cv2
import screen_brightness_control as sbc
from core.gesture_detector import GestureDetector

class BrightnessController(GestureDetector):
    """Controller for adjusting screen brightness using hand gestures."""
    
    def __init__(self):
        """Initialize the brightness controller with specific thresholds."""
        super().__init__()
        # Thresholds for brightness control
        self.TOLERANCE_UPPER = 20  # Threshold to increase brightness
        self.TOLERANCE_LOWER = 40  # Threshold to decrease brightness
        self.action_delay = 0.3    # Time between brightness adjustments
        
        # Get initial brightness
        self.current_brightness = sbc.get_brightness()[0]  # Get brightness of first monitor
    
    def adjust_brightness(self, distance):
        """
        Adjust brightness based on the distance between thumb and index finger.
        
        Args:
            distance: The scaled distance between thumb and index finger
        """
        if distance > self.TOLERANCE_UPPER:
            # Calculate how much to increase brightness based on distance
            increment = int((distance - self.TOLERANCE_UPPER) / 2)
            increment = max(1, min(increment, 5))  # Limit between 1 and 5
            
            # Ensure brightness doesn't exceed 100%
            new_brightness = min(100, self.current_brightness + increment)
            if new_brightness != self.current_brightness:
                sbc.set_brightness(new_brightness)
                self.current_brightness = new_brightness
                
        elif distance < self.TOLERANCE_LOWER:
            # Calculate how much to decrease brightness based on distance
            decrement = int((self.TOLERANCE_LOWER - distance) / 2)
            decrement = max(1, min(decrement, 5))  # Limit between 1 and 5
            
            # Ensure brightness doesn't go below 0%
            new_brightness = max(0, self.current_brightness - decrement)
            if new_brightness != self.current_brightness:
                sbc.set_brightness(new_brightness)
                self.current_brightness = new_brightness
    
    def draw_brightness_bar(self, image):
        """
        Draw a bar representing the current brightness level on the image.
        
        Args:
            image: The image to draw on
        """
        # Bar dimensions and position
        bar_width = 200
        bar_height = 30
        bar_x = 50
        bar_y = 50
        
        # Draw bar outline
        cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (255, 255, 255), 2)
        
        # Draw bar fill based on brightness level
        filled_width = int(bar_width * self.current_brightness / 100)
        cv2.rectangle(image, (bar_x, bar_y), (bar_x + filled_width, bar_y + bar_height), (0, 255, 255), -1)
        
        # Add text with brightness percentage
        cv2.putText(image, f"Brightness: {self.current_brightness}%", (bar_x, bar_y - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    def run(self):
        """Run the brightness control loop."""
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
                
                # Draw brightness bar
                self.draw_brightness_bar(image)
                
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
                            
                            # Adjust brightness if enough time has passed since last adjustment
                            if self.can_perform_action(self.action_delay):
                                self.adjust_brightness(distance)
                
                # Display the image
                cv2.imshow('Brightness Control Gestures', image)
                
                # Exit on ESC key
                if cv2.waitKey(10) == 27:
                    break
                    
        finally:
            self.stop_camera()