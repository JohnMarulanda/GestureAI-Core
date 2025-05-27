import cv2
import mediapipe as mp
import time

class GestureDetector:
    """Base class for gesture detection using MediaPipe."""

    def __init__(self):
        """Initialize the MediaPipe hands detector and related utilities."""
        self.mp_hands = mp.solutions.hands  # Reference to MediaPipe hands module
        self.hands = self.mp_hands.Hands()  # Create a Hands object for hand detection
        self.drawing_utils = mp.solutions.drawing_utils  # Utility for drawing landmarks
        self.webcam = None  # Placeholder for webcam capture object
        self.last_action_time = 0  # Timestamp of last performed action to control timing

    def start_camera(self, camera_id=0):
        """Start the webcam capture.

        Args:
            camera_id (int): The ID of the camera to use (default 0).

        Returns:
            bool: True if the camera was successfully opened, False otherwise.
        """
        self.webcam = cv2.VideoCapture(camera_id)
        return self.webcam.isOpened()

    def stop_camera(self):
        """Release the webcam and close any OpenCV windows."""
        if self.webcam:
            self.webcam.release()
        cv2.destroyAllWindows()

    def process_frame(self):
        """Capture and process a single frame from the webcam.

        Returns:
            tuple:
                image (numpy.ndarray or None): The captured frame (flipped horizontally),
                results (mediapipe.framework.formats.landmark_pb2.NormalizedLandmarkList or None): 
                    The hand detection results from MediaPipe.
        """
        # Check if webcam is opened
        if not self.webcam or not self.webcam.isOpened():
            return None, None

        success, image = self.webcam.read()
        if not success:
            return None, None

        # Flip the image horizontally for a mirror effect
        image = cv2.flip(image, 1)

        # Convert the BGR image (OpenCV format) to RGB (MediaPipe format)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Process the RGB image to detect hands and landmarks
        results = self.hands.process(rgb_image)

        return image, results

    def get_landmark_coordinates(self, landmark, frame_width, frame_height):
        """Convert normalized landmark coordinates to pixel coordinates.

        Args:
            landmark (mediapipe.framework.formats.landmark_pb2.NormalizedLandmark): 
                A single landmark with x,y normalized coordinates.
            frame_width (int): Width of the image frame in pixels.
            frame_height (int): Height of the image frame in pixels.

        Returns:
            tuple: (x, y) coordinates in pixels corresponding to the landmark position.
        """
        x = int(landmark.x * frame_width)
        y = int(landmark.y * frame_height)
        return x, y

    def calculate_distance(self, point1, point2):
        """Calculate the Euclidean distance between two points.

        Args:
            point1 (tuple): (x, y) coordinates of the first point.
            point2 (tuple): (x, y) coordinates of the second point.

        Returns:
            float: The Euclidean distance between point1 and point2.
        """
        x1, y1 = point1
        x2, y2 = point2
        return ((x2 - x1)**2 + (y2 - y1)**2) ** 0.5

    def can_perform_action(self, action_delay=0.3):
        """Determine if enough time has elapsed since the last action to perform a new one.

        This helps to prevent repeated triggering of actions in rapid succession.

        Args:
            action_delay (float): Minimum time delay (in seconds) required between actions.

        Returns:
            bool: True if enough time has passed and action can be performed; False otherwise.
        """
        current_time = time.time()
        if current_time - self.last_action_time > action_delay:
            self.last_action_time = current_time
            return True
        return False
