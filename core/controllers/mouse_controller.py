import cv2
import numpy as np
import time
import math
import pyautogui
import autopy
from pynput.mouse import Button, Controller
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from core.gesture_detector import GestureDetector

# Initialize mouse controller
mouse = Controller()

# Get screen dimensions
screen_width, screen_height = pyautogui.size()

# Disable pyautogui failsafe
pyautogui.FAILSAFE = False

class MouseController(GestureDetector):
    """Controller for mouse operations using hand gestures."""
    
    def __init__(self):
        """Initialize the mouse controller."""
        super().__init__()
        
        # Camera setup
        self.wCam, self.hCam = 640, 480
        
        # Volume control setup
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(interface, POINTER(IAudioEndpointVolume))
        self.volRange = self.volume.GetVolumeRange()
        self.minVol = self.volRange[0]
        self.maxVol = self.volRange[1]
        
        # Mode settings
        self.mode = 'N'  # N = Normal, Scroll, Volume, Cursor
        self.active = 0
        
        # Frame settings
        self.pTime = 0
        self.color = (0, 215, 255)
        
        # Mouse control settings
        self.frameR = 100  # Frame Reduction
        self.smoothening = 7
        self.plocX, self.plocY = 0, 0
        self.clocX, self.clocY = 0, 0
        
        # Volume settings
        self.hmin, self.hmax = 50, 200
        self.volBar = 400
        self.volPer = 0
        
        # Gesture settings
        self.clickCooldown = 0
        self.screenshotCooldown = 0
        self.dragActive = False
        
        print("Mouse Controller initialized")
        print("Press 'q' to quit")
    
    def putText(self, img, text, loc=(250, 450), color=(0, 255, 255), size=3, thickness=3):
        """Helper method to put text on the image."""
        cv2.putText(img, str(text), loc, cv2.FONT_HERSHEY_COMPLEX_SMALL, size, color, thickness)
    
    def display_instructions(self, frame):
        """Display the list of available gestures and their functions"""
        instructions = [
            "MOUSE CONTROL GESTURES:",
            "All fingers closed: Normal mode",
            "Index finger up: Scroll mode (up/down)",
            "Thumb + Index up: Volume control",
            "All fingers up: Cursor mode",
            "Index-Pinky up (no thumb): Screenshot mode"
        ]
        
        y_pos = 70
        for instruction in instructions:
            cv2.putText(frame, instruction, (10, y_pos), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_pos += 25
    
    def fingersUp(self, lmList):
        """Detect which fingers are up."""
        fingers = []
        
        # Check if lmList has enough points
        if len(lmList) < 21:
            return [0, 0, 0, 0, 0]
            
        # Thumb
        if lmList[4][1] > lmList[3][1]:
            if lmList[4][1] >= lmList[3][1]:
                fingers.append(1)
            else:
                fingers.append(0)
        elif lmList[4][1] < lmList[3][1]:
            if lmList[4][1] <= lmList[3][1]:
                fingers.append(1)
            else:
                fingers.append(0)

        # Other fingers
        for id in range(1, 5):
            if lmList[4*id+4][2] < lmList[4*id+2][2]:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers
    
    def run(self):
        """Main loop to capture video and process hand gestures for mouse control."""
        if not self.start_camera():
            print("Failed to open webcam")
            return
        
        try:
            while True:
                # Get the frame
                success, img = self.cap.read()
                if not success:
                    print("Failed to get frame from camera.")
                    break
                
                # Flip the frame horizontally for a more intuitive mirror view
                img = cv2.flip(img, 1)
                
                # Process the frame with MediaPipe
                results = self.hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                
                # Display instructions
                self.display_instructions(img)
                
                # Initialize empty landmarks list
                lmList = []
                
                # If hands are detected
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        # Draw hand landmarks
                        self.drawing_utils.draw_landmarks(
                            img, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                        
                        # Extract landmark positions
                        for id, lm in enumerate(hand_landmarks.landmark):
                            h, w, c = img.shape
                            cx, cy = int(lm.x * w), int(lm.y * h)
                            lmList.append([id, cx, cy])
                
                # Check which fingers are up
                fingers = []
                if len(lmList) != 0:
                    fingers = self.fingersUp(lmList)
                    
                    # Mode Selection
                    if (fingers == [0, 0, 0, 0, 0]) and (self.active == 0):
                        self.mode = 'N'
                    elif (fingers == [0, 1, 0, 0, 0] or fingers == [0, 1, 1, 0, 0]) and (self.active == 0):
                        self.mode = 'Scroll'
                        self.active = 1
                    elif (fingers == [1, 1, 0, 0, 0]) and (self.active == 0):
                        self.mode = 'Volume'
                        self.active = 1
                    elif (fingers == [1, 1, 1, 1, 1]) and (self.active == 0):
                        self.mode = 'Cursor'
                        self.active = 1
                    elif (fingers == [0, 1, 1, 1, 1]) and (self.active == 0):
                        self.mode = 'Screenshot'
                        self.active = 1
                
                # Execute mode functionality
                if self.mode == 'Scroll':
                    self._handleScrollMode(img, fingers)
                elif self.mode == 'Volume':
                    self._handleVolumeMode(img, lmList, fingers)
                elif self.mode == 'Cursor':
                    self._handleCursorMode(img, lmList, fingers)
                elif self.mode == 'Screenshot':
                    self._handleScreenshotMode(img, fingers)
                
                # Frame rate
                cTime = time.time()
                fps = 1 / ((cTime + 0.01) - self.pTime)
                self.pTime = cTime
                
                # Display
                cv2.putText(img, f'FPS:{int(fps)}', (480, 50), cv2.FONT_ITALIC, 1, (255, 0, 0), 2)
                cv2.putText(img, f'Mode: {self.mode}', (20, 50), cv2.FONT_ITALIC, 1, (255, 0, 0), 2)
                cv2.imshow('Mouse Control with Hand Gestures', img)
                
                # Exit on 'q' key press
                if cv2.waitKey(5) & 0xFF == ord('q'):
                    break
        
        finally:
            self.stop_camera()

    def _handleScrollMode(self, img, fingers):
        """Handle scroll mode functionality."""
        self.active = 1
        self.putText(img, self.mode)
        cv2.rectangle(img, (200, 410), (245, 460), (255, 255, 255), cv2.FILLED)
        
        if fingers == [0, 1, 0, 0, 0]:
            self.putText(img, 'U', loc=(200, 455), color=(0, 255, 0))
            pyautogui.scroll(300)
        elif fingers == [0, 1, 1, 0, 0]:
            self.putText(img, 'D', loc=(200, 455), color=(0, 0, 255))
            pyautogui.scroll(-300)
        elif fingers == [0, 0, 0, 0, 0]:
            self.active = 0
            self.mode = 'N'

    def _handleVolumeMode(self, img, lmList, fingers):
        """Handle volume control mode functionality."""
        self.active = 1
        self.putText(img, self.mode)
        
        if len(lmList) != 0:
            if fingers[-1] == 1:
                self.active = 0
                self.mode = 'N'
            else:
                # Find distance between index and thumb
                x1, y1 = lmList[4][1], lmList[4][2]
                x2, y2 = lmList[8][1], lmList[8][2]
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                
                # Draw circles and line
                cv2.circle(img, (x1, y1), 10, self.color, cv2.FILLED)
                cv2.circle(img, (x2, y2), 10, self.color, cv2.FILLED)
                cv2.line(img, (x1, y1), (x2, y2), self.color, 3)
                cv2.circle(img, (cx, cy), 8, self.color, cv2.FILLED)
                
                # Calculate distance and convert to volume
                length = math.hypot(x2 - x1, y2 - y1)
                vol = np.interp(length, [self.hmin, self.hmax], [self.minVol, self.maxVol])
                volBar = np.interp(vol, [self.minVol, self.maxVol], [400, 150])
                volPer = np.interp(vol, [self.minVol, self.maxVol], [0, 100])
                
                # Smooth volume changes
                volN = int(vol)
                if volN % 4 != 0:
                    volN = volN - volN % 4
                    if volN >= 0:
                        volN = 0
                    elif volN <= -64:
                        volN = -64
                    elif vol >= -11:
                        volN = vol
                
                # Set volume
                self.volume.SetMasterVolumeLevel(vol, None)
                
                # Visual feedback
                if length < 50:
                    cv2.circle(img, (cx, cy), 11, (0, 0, 255), cv2.FILLED)
                
                cv2.rectangle(img, (30, 150), (55, 400), (209, 206, 0), 3)
                cv2.rectangle(img, (30, int(volBar)), (55, 400), (215, 255, 127), cv2.FILLED)
                cv2.putText(img, f'{int(volPer)}%', (25, 430), cv2.FONT_HERSHEY_COMPLEX, 0.9, (209, 206, 0), 3)

    def _handleCursorMode(self, img, lmList, fingers):
        """Handle cursor control mode functionality."""
        self.active = 1
        self.putText(img, self.mode)
        
        # Define cursor control area
        cv2.rectangle(img, (self.frameR, self.frameR), (self.wCam - self.frameR, self.hCam - self.frameR), (255, 255, 255), 3)
        
        if fingers[1:] == [0, 0, 0, 0]:  # thumb excluded
            self.active = 0
            self.mode = 'N'
            if self.dragActive:
                mouse.release(Button.left)
                self.dragActive = False
        else:
            if len(lmList) != 0:
                # Get index finger position
                x1, y1 = lmList[8][1], lmList[8][2]
                
                # Convert coordinates to screen position
                x = np.interp(x1, [self.frameR, self.wCam - self.frameR], [0, screen_width])
                y = np.interp(y1, [self.frameR, self.hCam - self.frameR], [0, screen_height])
                
                # Smoothen values
                self.clocX = self.plocX + (x - self.plocX) / self.smoothening
                self.clocY = self.plocY + (y - self.plocY) / self.smoothening
                
                # Move mouse
                try:
                    autopy.mouse.move(min(screen_width-1, max(0, self.clocX)), min(screen_height-1, max(0, self.clocY)))
                except Exception as e:
                    # Fallback to pyautogui if autopy fails
                    pyautogui.moveTo(min(screen_width-1, max(0, self.clocX)), min(screen_height-1, max(0, self.clocY)))
                
                self.plocX, self.plocY = self.clocX, self.clocY
                
                # Draw circle at index finger
                cv2.circle(img, (x1, y1), 7, (255, 255, 255), cv2.FILLED)
                
                # Click functionality
                if fingers[0] == 0 and fingers[1] == 1 and fingers[2:] == [0, 0, 0]:
                    # Left click (thumb down, index up, others down)
                    if self.clickCooldown == 0:
                        mouse.click(Button.left)
                        self.clickCooldown = 10
                        cv2.circle(img, (x1, y1), 15, (0, 255, 0), cv2.FILLED)
                
                # Right click
                elif fingers[0] == 0 and fingers[1:3] == [1, 1] and fingers[3:] == [0, 0]:
                    # Right click (thumb down, index and middle up, others down)
                    if self.clickCooldown == 0:
                        mouse.click(Button.right)
                        self.clickCooldown = 10
                        cv2.circle(img, (x1, y1), 15, (0, 0, 255), cv2.FILLED)
                
                # Drag functionality
                elif fingers[0] == 1 and fingers[1] == 1 and fingers[2:] == [0, 0, 0]:
                    # Drag (thumb up, index up, others down)
                    if not self.dragActive:
                        mouse.press(Button.left)
                        self.dragActive = True
                    cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
                elif self.dragActive and (fingers[0] != 1 or fingers[1] != 1 or fingers[2:] != [0, 0, 0]):
                    mouse.release(Button.left)
                    self.dragActive = False
                
                # Double click
                elif fingers[0] == 1 and fingers[1:3] == [1, 1] and fingers[3:] == [0, 0]:
                    # Double click (thumb up, index and middle up, others down)
                    if self.clickCooldown == 0:
                        pyautogui.doubleClick()
                        self.clickCooldown = 15
                        cv2.circle(img, (x1, y1), 15, (255, 255, 0), cv2.FILLED)
                
                # Cooldown counter
                if self.clickCooldown > 0:
                    self.clickCooldown -= 1

    def _handleScreenshotMode(self, img, fingers):
        """Handle screenshot mode functionality."""
        self.active = 1
        self.putText(img, "Screenshot")
        
        if fingers == [0, 1, 1, 1, 1]:
            if self.screenshotCooldown == 0:
                # Take screenshot
                screenshot = pyautogui.screenshot()
                timestamp = int(time.time())
                filename = f'screenshot_{timestamp}.png'
                screenshot.save(filename)
                cv2.putText(img, f"Saved: {filename}", (50, 100), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                self.screenshotCooldown = 30
        elif fingers == [0, 0, 0, 0, 0]:
            self.active = 0
            self.mode = 'N'
        
        if self.screenshotCooldown > 0:
            self.screenshotCooldown -= 1
            cv2.putText(img, "Screenshot taken!", (50, 100), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)