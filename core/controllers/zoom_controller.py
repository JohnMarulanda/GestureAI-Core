import cv2
import os
import numpy as np
from cvzone.HandTrackingModule import HandDetector
from core.gesture_detector import GestureDetector

class ZoomController(GestureDetector):
    """Controller for virtual zoom operations using hand gestures."""
    
    def __init__(self):
        """Initialize the virtual zoom controller."""
        super().__init__()
        
        # Initialize cvzone hand detector for more advanced features
        self.cvzone_detector = HandDetector(detectionCon=0.7)
        
        # Zoom control variables
        self.start_dist = None
        self.scale = 0
        self.cx, self.cy = 500, 500  # Center position for the image
        
        # Load a default image
        self.image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                      "assets", "sample_image.jpg")
        self.load_image()
        
        print("Virtual Zoom Controller initialized")
        print("Press 'q' to quit")
    
    def load_image(self):
        """Load the image to be zoomed."""
        try:
            self.target_image = cv2.imread(self.image_path)
            if self.target_image is None:
                print(f"Warning: Could not load image from {self.image_path}")
                # Create a placeholder image
                self.target_image = np.ones((300, 300, 3), dtype=np.uint8) * 255
                cv2.putText(self.target_image, "Sample Image", (50, 150), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        except Exception as e:
            print(f"Error loading image: {e}")
            # Create a placeholder image
            self.target_image = np.ones((300, 300, 3), dtype=np.uint8) * 255
            cv2.putText(self.target_image, "Sample Image", (50, 150), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    def set_image(self, image_path):
        """Set a new image to be zoomed."""
        self.image_path = image_path
        self.load_image()
    
    def display_instructions(self, frame):
        """Display the list of available gestures and their functions"""
        instructions = [
            "VIRTUAL ZOOM GESTURES:",
            "Pinch with both hands (index + thumb): Zoom in/out",
            "Move hands: Pan the image"
        ]
        
        y_pos = 30
        for instruction in instructions:
            cv2.putText(frame, instruction, (10, y_pos), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            y_pos += 30
    
    def run(self):
        """Main loop to capture video and process hand gestures for zoom control."""
        if not self.start_camera(width=1280, height=720):
            print("Failed to open webcam")
            return
        
        try:
            while True:
                # Get the frame
                success, image = self.cap.read()
                if not success:
                    print("Failed to capture image from camera.")
                    break
                
                # Flip the frame horizontally for a more intuitive mirror view
                image = cv2.flip(image, 1)
                
                # Find hands using cvzone detector
                hands, image = self.cvzone_detector.findHands(image)
                
                # Display instructions
                self.display_instructions(image)
                
                # Process zoom gesture if two hands are detected
                if len(hands) == 2:
                    # Check if both hands are making the pinch gesture (thumb and index finger up)
                    if (self.cvzone_detector.fingersUp(hands[0]) == [1, 1, 0, 0, 0] and 
                            self.cvzone_detector.fingersUp(hands[1]) == [1, 1, 0, 0, 0]):
                        
                        # Calculate distance between hands
                        if self.start_dist is None:
                            length, info, image = self.cvzone_detector.findDistance(
                                hands[0]["center"], hands[1]["center"], image)
                            self.start_dist = length
                        
                        # Calculate new distance and scale
                        length, info, image = self.cvzone_detector.findDistance(
                            hands[0]["center"], hands[1]["center"], image)
                        
                        # Calculate scale based on the difference from starting distance
                        self.scale = int((length - self.start_dist) // 2)
                        
                        # Get center point between the two hands
                        self.cx, self.cy = info[4:]
                else:
                    # Reset starting distance if hands are not detected
                    self.start_dist = None
                
                # Apply the zoom effect to the image
                try:
                    h1, w1, _ = self.target_image.shape
                    
                    # Calculate new dimensions with scale
                    newH, newW = ((h1 + self.scale) // 2) * 2, ((w1 + self.scale) // 2) * 2
                    
                    # Ensure dimensions are positive
                    if newH > 0 and newW > 0:
                        # Resize the image
                        resized_img = cv2.resize(self.target_image, (newW, newH))
                        
                        # Calculate placement coordinates
                        y1 = max(0, self.cy - newH // 2)
                        y2 = min(image.shape[0], self.cy + newH // 2)
                        x1 = max(0, self.cx - newW // 2)
                        x2 = min(image.shape[1], self.cx + newW // 2)
                        
                        # Adjust resized image crop if needed
                        img_y1 = max(0, -self.cy + newH // 2)
                        img_y2 = img_y1 + (y2 - y1)
                        img_x1 = max(0, -self.cx + newW // 2)
                        img_x2 = img_x1 + (x2 - x1)
                        
                        # Ensure we're not exceeding the resized image dimensions
                        if (img_y2 <= resized_img.shape[0] and img_x2 <= resized_img.shape[1] and
                                img_y1 < img_y2 and img_x1 < img_x2):
                            # Place the resized image onto the frame
                            image[y1:y2, x1:x2] = resized_img[img_y1:img_y2, img_x1:img_x2]
                except Exception as e:
                    # Just continue if there's an error with the image placement
                    pass
                
                # Display the frame
                cv2.imshow('Virtual Zoom with Hand Gestures', image)
                
                # Exit on 'q' key press
                if cv2.waitKey(5) & 0xFF == ord('q'):
                    break
        
        finally:
            self.stop_camera()