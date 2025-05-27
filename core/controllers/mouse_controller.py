import cv2
import numpy as np
import time
import math
import pyautogui
import autopy
import threading
from pynput.mouse import Button, Controller
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from core.gesture_recognition_manager import GestureRecognitionManager
from config import settings

# Initialize mouse controller
mouse = Controller()

# Get screen dimensions
screen_width, screen_height = pyautogui.size()

# Disable pyautogui failsafe
pyautogui.FAILSAFE = False

class MouseController:
    """Controller for mouse operations using gestures.
    
    This controller uses a centralized GestureRecognitionManager for gesture
    recognition, removing duplicated detection logic.
    """
    
    def __init__(self):
        """Initialize the mouse controller.
        
        Sets up gesture manager, state variables, volume control interface,
        smoothing parameters, and mode initialization.
        """
        # Get the singleton instance of the gesture recognition manager
        self.gesture_manager = GestureRecognitionManager()
        
        # State variables
        self.running = False
        self.display_thread = None
        self.lock = threading.Lock()
        
        # Gesture state
        self.active_gestures = {}
        self.gesture_messages = {}
        self.current_mode = 'N'  # N = Normal, Scroll, Volume, Cursor, Screenshot
        
        # Camera settings
        self.wCam = settings.CAMERA_WIDTH
        self.hCam = settings.CAMERA_HEIGHT
        
        # Volume control setup using pycaw
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(interface, POINTER(IAudioEndpointVolume))
        self.volRange = self.volume.GetVolumeRange()
        self.minVol, self.maxVol = self.volRange[0], self.volRange[1]
        
        # Mouse control parameters
        self.frameR = settings.MOUSE_FRAME_REDUCTION
        self.smoothening = settings.MOUSE_SMOOTHENING
        self.plocX, self.plocY = 0, 0  # Previous location of mouse
        self.clocX, self.clocY = 0, 0  # Current location of mouse
        
        # Volume control boundaries
        self.hmin, self.hmax = settings.MOUSE_VOLUME_MIN, settings.MOUSE_VOLUME_MAX
        self.volBar = 400
        self.volPer = 0
        
        # Gesture cooldowns and drag state
        self.clickCooldown = 0
        self.screenshotCooldown = 0
        self.dragActive = False
        
        print("Mouse controller initialized")
        print("Press 'q' to quit")
    
    def start(self):
        """Start the mouse controller and subscribe to gesture events.
        
        Ensures the camera is started and subscribes to relevant gestures.
        Starts a separate thread for UI display and gesture processing.
        """
        # Start camera if not running
        camera_status = self.gesture_manager.get_camera_status()
        if not camera_status["connected"]:
            self.gesture_manager.start_camera_with_settings(
                width=self.wCam,
                height=self.hCam
            )
        
        # Subscribe to relevant gestures
        self.gesture_manager.subscribe_to_gesture("palm", self.handle_gesture)
        self.gesture_manager.subscribe_to_gesture("point", self.handle_gesture)
        self.gesture_manager.subscribe_to_gesture("fist", self.handle_gesture)
        self.gesture_manager.subscribe_to_gesture("pinch", self.handle_gesture)
        self.gesture_manager.subscribe_to_gesture("victory", self.handle_gesture)
        
        # Start processing gestures if not already running
        if not self.gesture_manager._running:
            self.gesture_manager.start_processing()
        
        # Start UI and processing thread
        self.running = True
        self.display_thread = threading.Thread(target=self.display_loop)
        self.display_thread.daemon = True
        self.display_thread.start()
        
        print("Mouse controller started")
    
    def stop(self):
        """Stop the mouse controller and unsubscribe from gestures.
        
        Stops the display thread and cancels all gesture subscriptions.
        """
        self.running = False
        
        if self.display_thread and self.display_thread.is_alive():
            self.display_thread.join(timeout=1.0)
        
        # Unsubscribe from all gestures
        self.gesture_manager.unsubscribe_from_gesture("palm")
        self.gesture_manager.unsubscribe_from_gesture("point")
        self.gesture_manager.unsubscribe_from_gesture("fist")
        self.gesture_manager.unsubscribe_from_gesture("pinch")
        self.gesture_manager.unsubscribe_from_gesture("victory")
        
        print("Mouse controller stopped")
    
    def handle_gesture(self, event_type, gesture_data):
        """Handle gesture events received from the gesture manager.
        
        Args:
            event_type (str): Type of gesture event ('detected', 'updated', 'ended').
            gesture_data (dict): Data related to the gesture, including landmarks and id.
        """
        gesture_id = gesture_data.get("id")
        landmarks = gesture_data.get("landmarks")
        
        with self.lock:
            if event_type == "detected":
                # New gesture detected
                self.active_gestures[gesture_id] = gesture_data
                self.gesture_messages[gesture_id] = f"{gesture_data.get('name')} detected!"
                
                # Set current mode based on gesture if in Normal mode
                if gesture_id == "fist" and self.current_mode == 'N':
                    self.current_mode = 'N'
                elif gesture_id == "point" and self.current_mode == 'N':
                    self.current_mode = 'Scroll'
                elif gesture_id == "pinch" and self.current_mode == 'N':
                    self.current_mode = 'Volume'
                elif gesture_id == "palm" and self.current_mode == 'N':
                    self.current_mode = 'Cursor'
                elif gesture_id == "victory" and self.current_mode == 'N':
                    self.current_mode = 'Screenshot'
                
            elif event_type == "updated":
                # Gesture updated - update state and perform action based on mode
                self.active_gestures[gesture_id] = gesture_data
                
                if landmarks and self.current_mode != 'N':
                    # Get index finger tip position (landmark 8)
                    x1 = int(landmarks.landmark[8].x * self.wCam)
                    y1 = int(landmarks.landmark[8].y * self.hCam)
                    
                    if self.current_mode == 'Cursor':
                        self._handle_cursor_mode(x1, y1, gesture_data)
                    elif self.current_mode == 'Scroll':
                        self._handle_scroll_mode(gesture_data)
                    elif self.current_mode == 'Volume':
                        self._handle_volume_mode(gesture_data)
                    elif self.current_mode == 'Screenshot':
                        self._handle_screenshot_mode(gesture_data)
                
            elif event_type == "ended":
                # Gesture ended - remove from active gestures
                if gesture_id in self.active_gestures:
                    del self.active_gestures[gesture_id]
                    
                    # Reset mode if no active gestures remain
                    if len(self.active_gestures) == 0:
                        self.current_mode = 'N'
                        if self.dragActive:
                            mouse.release(Button.left)
                            self.dragActive = False
                    
                    # Keep message visible for a short time
                    self.gesture_messages[gesture_id] = f"{gesture_id} ended"
                    threading.Timer(2.0, lambda: self.remove_message(gesture_id)).start()
    
    def _handle_cursor_mode(self, x1, y1, gesture_data):
        """Handle the cursor control mode.
        
        Moves the mouse cursor based on index finger position and handles click
        and drag gestures with cooldown logic.
        """
        # Map camera coordinates to screen coordinates
        x = np.interp(x1, [self.frameR, self.wCam - self.frameR], [0, screen_width])
        y = np.interp(y1, [self.frameR, self.hCam - self.frameR], [0, screen_height])
        
        # Smooth mouse movement
        self.clocX = self.plocX + (x - self.plocX) / self.smoothening
        self.clocY = self.plocY + (y - self.plocY) / self.smoothening
        
        # Move mouse using autopy, fallback to pyautogui
        try:
            autopy.mouse.move(min(screen_width-1, max(0, self.clocX)),
                            min(screen_height-1, max(0, self.clocY)))
        except Exception:
            pyautogui.moveTo(min(screen_width-1, max(0, self.clocX)),
                          min(screen_height-1, max(0, self.clocY)))
        
        self.plocX, self.plocY = self.clocX, self.clocY
        
        # Get which fingers are up
        fingers = self._get_fingers_up(gesture_data)
        if fingers:
            if fingers == [0, 1, 0, 0, 0] and self.clickCooldown == 0:
                # Left click
                mouse.click(Button.left)
                self.clickCooldown = 10
            elif fingers == [0, 1, 1, 0, 0] and self.clickCooldown == 0:
                # Right click
                mouse.click(Button.right)
                self.clickCooldown = 10
            elif fingers == [1, 1, 0, 0, 0]:
                # Drag (hold left button)
                if not self.dragActive:
                    mouse.press(Button.left)
                    self.dragActive = True
            elif fingers == [1, 1, 1, 0, 0] and self.clickCooldown == 0:
                # Double click
                pyautogui.doubleClick()
                self.clickCooldown = 15
        
        # Reduce cooldown timers
        if self.clickCooldown > 0:
            self.clickCooldown -= 1
    
    def _handle_scroll_mode(self, gesture_data):
        """Handle the scroll mode.
        
        Scrolls the screen up or down based on finger gestures.
        """
        fingers = self._get_fingers_up(gesture_data)
        if fingers:
            if fingers == [0, 1, 0, 0, 0]:
                pyautogui.scroll(300)  # Scroll up
            elif fingers == [0, 1, 1, 0, 0]:
                pyautogui.scroll(-300)  # Scroll down
    
    def _handle_volume_mode(self, gesture_data):
        """Handle the volume control mode.
        
        Adjusts system volume based on distance between thumb and index finger.
        """
        landmarks = gesture_data.get("landmarks")
        if landmarks:
            # Calculate distance between thumb tip (4) and index tip (8)
            x1, y1 = int(landmarks.landmark[4].x * self.wCam), int(landmarks.landmark[4].y * self.hCam)
            x2, y2 = int(landmarks.landmark[8].x * self.wCam), int(landmarks.landmark[8].y * self.hCam)
            length = math.hypot(x2 - x1, y2 - y1)
            
            # Map distance to volume range
            vol = np.interp(length, [self.hmin, self.hmax], [self.minVol, self.maxVol])
            self.volBar = np.interp(vol, [self.minVol, self.maxVol], [400, 150])
            self.volPer = np.interp(vol, [self.minVol, self.maxVol], [0, 100])
            
            # Volume adjustment with some thresholds
            volN = int(vol)
            if volN % 4 != 0:
                volN = volN - volN % 4
                if volN >= 0:
                    volN = 0
                elif volN <= -64:
                    volN = -64
                elif vol >= -11:
                    volN = vol
            
            self.volume.SetMasterVolumeLevel(vol, None)
    
    def _handle_screenshot_mode(self, gesture_data):
        """Handle screenshot mode.
        
        Captures and saves a screenshot when the specific gesture is detected,
        with cooldown to avoid multiple captures.
        """
        fingers = self._get_fingers_up(gesture_data)
        if fingers == [0, 1, 1, 1, 1] and self.screenshotCooldown == 0:
            # Take screenshot
            screenshot = pyautogui.screenshot()
            timestamp = int(time.time())
            filename = f'screenshot_{timestamp}.png'
            screenshot.save(filename)
            self.set_message(f"Screenshot saved: {filename}", duration=2.0)
            self.screenshotCooldown = 30
        
        if self.screenshotCooldown > 0:
            self.screenshotCooldown -= 1
    
    def _get_fingers_up(self, gesture_data):
        """Determine which fingers are up based on landmarks.
        
        Returns a list of 0s and 1s indicating finger states:
        [thumb, index, middle, ring, pinky]
        
        Args:
            gesture_data (dict): Gesture data containing landmarks.
        
        Returns:
            list or None: Finger states or None if no landmarks.
        """
        landmarks = gesture_data.get("landmarks")
        if not landmarks:
            return None
        
        fingers = []
        # Thumb: compare landmark 4 and 3 x positions
        if landmarks.landmark[4].x > landmarks.landmark[3].x:
            fingers.append(1)
        else:
            fingers.append(0)
        
        # Other fingers: tip landmark y < pip landmark y means finger is up
        for id in range(1, 5):
            if landmarks.landmark[4*id+4].y < landmarks.landmark[4*id+2].y:
                fingers.append(1)
            else:
                fingers.append(0)
        
        return fingers
    
    def set_message(self, message, duration=2.0):
        """Set a temporary message to display.
        
        Args:
            message (str): Message text.
            duration (float): Duration in seconds to display the message.
        """
        with self.lock:
            self.gesture_messages["temp"] = message
            threading.Timer(duration, lambda: self.remove_message("temp")).start()
    
    def remove_message(self, message_id):
        """Remove a message by its ID.
        
        Args:
            message_id (str): Identifier of the message to remove.
        """
        with self.lock:
            if message_id in self.gesture_messages:
                del self.gesture_messages[message_id]
    
    def display_loop(self):
        """Main loop to display UI and gesture feedback.
        
        Continuously captures frames, overlays gesture info, and listens for quit key.
        """
        while self.running:
            # Get the current frame from the gesture manager
            image, _ = self.gesture_manager.process_frame()
            if image is None:
                time.sleep(0.01)
                continue
            
            # Overlay gesture messages
            y0, dy = 30, 30
            with self.lock:
                for i, (key, msg) in enumerate(self.gesture_messages.items()):
                    y = y0 + i * dy
                    cv2.putText(image, msg, (10, y), cv2.FONT_HERSHEY_SIMPLEX,
                                1, (255, 255, 255), 2)
            
            # Show frame
            cv2.imshow("Gesture Mouse Controller", image)
            
            # Quit on 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.stop()
                break
        
        cv2.destroyAllWindows()
