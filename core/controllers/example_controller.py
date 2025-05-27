import cv2
import time
import threading
from core.gesture_recognition_manager import GestureRecognitionManager

class ExampleController:
    """Example controller using the centralized GestureRecognitionManager.

    This controller demonstrates how to use the GestureRecognitionManager
    to subscribe to specific gestures without implementing detection logic.
    """

    def __init__(self):
        """Initializes the example controller."""
        # Get the singleton instance of the gesture recognition manager
        self.gesture_manager = GestureRecognitionManager()

        # State variables
        self.running = False
        self.display_thread = None
        self.lock = threading.Lock()

        # Gesture state
        self.active_gestures = {}
        self.gesture_messages = {}

        print("Example Controller initialized")

    def start(self):
        """Starts the controller and subscribes to gestures."""
        # Start the camera if not already started
        camera_status = self.gesture_manager.get_camera_status()
        if not camera_status["connected"]:
            self.gesture_manager.start_camera_with_settings(width=640, height=480)

        # Subscribe to the gestures of interest
        self.gesture_manager.subscribe_to_gesture("pinch", self.handle_gesture)
        self.gesture_manager.subscribe_to_gesture("palm", self.handle_gesture)
        self.gesture_manager.subscribe_to_gesture("fist", self.handle_gesture)
        self.gesture_manager.subscribe_to_gesture("point", self.handle_gesture)
        self.gesture_manager.subscribe_to_gesture("victory", self.handle_gesture)

        # Start gesture processing if not running
        if not self.gesture_manager._running:
            self.gesture_manager.start_processing()

        # Start the display thread for UI
        self.running = True
        self.display_thread = threading.Thread(target=self.display_loop)
        self.display_thread.daemon = True
        self.display_thread.start()

        print("Example Controller started")
        print("Press 'q' to quit")

    def stop(self):
        """Stops the controller and unsubscribes from gestures."""
        self.running = False

        if self.display_thread and self.display_thread.is_alive():
            self.display_thread.join(timeout=1.0)

        # Unsubscribe from gestures
        self.gesture_manager.unsubscribe_from_gesture("pinch")
        self.gesture_manager.unsubscribe_from_gesture("palm")
        self.gesture_manager.unsubscribe_from_gesture("fist")
        self.gesture_manager.unsubscribe_from_gesture("point")
        self.gesture_manager.unsubscribe_from_gesture("victory")

        print("Example Controller stopped")

    def handle_gesture(self, event_type, gesture_data):
        """Handles gesture events received from the manager.

        Args:
            event_type (str): The event type ('detected', 'updated', 'ended').
            gesture_data (dict): The gesture data.
        """
        gesture_id = gesture_data.get("id")

        with self.lock:
            if event_type == "detected":
                # New gesture detected
                self.active_gestures[gesture_id] = gesture_data
                self.gesture_messages[gesture_id] = f"{gesture_data.get('name')} detected!"
                print(f"Gesture detected: {gesture_data.get('name')}")

            elif event_type == "updated":
                # Gesture updated
                self.active_gestures[gesture_id] = gesture_data

            elif event_type == "ended":
                # Gesture ended
                if gesture_id in self.active_gestures:
                    print(f"Gesture ended: {self.active_gestures[gesture_id].get('name')}")
                    del self.active_gestures[gesture_id]

                    # Keep the message for some time before removing
                    self.gesture_messages[gesture_id] = f"{gesture_id} ended"
                    threading.Timer(2.0, lambda: self.remove_message(gesture_id)).start()

    def remove_message(self, gesture_id):
        """Removes a gesture message after a delay.

        Args:
            gesture_id (str): The gesture ID whose message should be removed.
        """
        with self.lock:
            if gesture_id in self.gesture_messages:
                del self.gesture_messages[gesture_id]

    def display_loop(self):
        """Main loop to display the user interface."""
        while self.running:
            # Get the current frame from the gesture manager
            image, _ = self.gesture_manager.process_frame()
            if image is None:
                time.sleep(0.01)
                continue

            # Display active gesture information on the frame
            self.display_active_gestures(image)

            # Display gesture event messages
            self.display_messages(image)

            # Display usage instructions
            self.display_instructions(image)

            # Show the frame in a window
            cv2.imshow('Example Controller with GestureRecognitionManager', image)

            # Exit if 'q' is pressed
            if cv2.waitKey(5) & 0xFF == ord('q'):
                break

        # Close all OpenCV windows after exit
        cv2.destroyAllWindows()

    def display_active_gestures(self, image):
        """Displays information about active gestures on the frame.

        Args:
            image (numpy.ndarray): The current video frame.
        """
        with self.lock:
            y_pos = 30
            cv2.putText(image, "ACTIVE GESTURES:", (10, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            y_pos += 30
            for gesture_id, gesture_data in self.active_gestures.items():
                confidence = gesture_data.get("confidence", 0) * 100
                text = f"{gesture_data.get('name')}: {confidence:.1f}%"
                cv2.putText(image, text, (10, y_pos),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                y_pos += 25

    def display_messages(self, image):
        """Displays gesture event messages on the frame.

        Args:
            image (numpy.ndarray): The current video frame.
        """
        with self.lock:
            y_pos = image.shape[0] - 60
            for message in self.gesture_messages.values():
                cv2.putText(image, message, (10, y_pos),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                y_pos -= 30

    def display_instructions(self, image):
        """Displays usage instructions on the frame.

        Args:
            image (numpy.ndarray): The current video frame.
        """
        y_pos = 30
        x_pos = image.shape[1] - 250

        cv2.putText(image, "INSTRUCTIONS:", (x_pos, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        y_pos += 30
        instructions = [
            "Pinch: Thumb and index finger together",
            "Palm: Open hand",
            "Fist: Closed fist",
            "Point: Pointing with index finger",
            "Victory: Victory sign"
        ]

        for instruction in instructions:
            cv2.putText(image, instruction, (x_pos, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_pos += 25

# Example usage
def main():
    controller = ExampleController()
    try:
        controller.start()
        # Main thread runs while display thread shows UI
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Program interrupted by user")
    finally:
        controller.stop()

if __name__ == "__main__":
    main()
