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
    
    def display_messages(self, frame):
        """Display action messages on the frame.
        
        Args:
            frame (ndarray): The image frame to draw on.
        """
        with self.lock:
            y_pos = frame.shape[0] - 30
            for message in self.gesture_messages.values():
                cv2.putText(frame, message, (10, y_pos), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                y_pos -= 30
    
    def display_landmarks(self, frame):
        """
        Muestra los landmarks de la mano y el estado de los dedos.
        
        Args:q
            frame: Frame donde mostrar los landmarks.
        """
        _, results = self.gesture_manager.process_frame()
        
        if results and results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Dibujar las conexiones entre landmarks
                self.gesture_manager.drawing_utils.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.gesture_manager.mp_hands.HAND_CONNECTIONS)
                
                # Detectar y mostrar estados de los dedos
                finger_states = self.detect_finger_states(hand_landmarks)
                if finger_states:
                    finger_state_str = "".join([str(s) for s in finger_states])
                    cv2.putText(frame, f"Estados: {finger_state_str}", 
                                (10, frame.shape[0] - 90), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    
                    # Mostrar estado individual de cada dedo
                    finger_names = ["Pulgar", "Índice", "Medio", "Anular", "Meñique"]
                    y_pos = frame.shape[0] - 60
                    for name, state in zip(finger_names, finger_states):
                        color = (0, 255, 0) if state == 1 else (0, 0, 255)
                        status = "Abierto" if state == 1 else "Cerrado"
                        cv2.putText(frame, f"{name}: {status}", 
                                    (10, y_pos), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
                        y_pos += 20
                
                # Dibujar los puntos de los landmarks
                for i, landmark in enumerate(hand_landmarks.landmark):
                    x = int(landmark.x * frame.shape[1])
                    y = int(landmark.y * frame.shape[0])
                    
                    # Dibujar círculo para cada landmark
                    cv2.circle(frame, (x, y), 3, (0, 255, 0), -1)
                    
                    # Resaltar las puntas de los dedos
                    if i in [4, 8, 12, 16, 20]:  # Pulgar, índice, medio, anular, meñique
                        cv2.circle(frame, (x, y), 6, (255, 0, 0), -1)
                        cv2.putText(frame, str(i), (x + 10, y), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
    
    def detect_finger_states(self, hand_landmarks):
        """
        Detecta el estado de los dedos (extendido o no) y devuelve una lista de 0s y 1s.
        
        Args:
            hand_landmarks: Los landmarks de la mano detectada.
            
        Returns:
            list: Lista de 5 valores (0 o 1) representando el estado de cada dedo.
        """
        if not hand_landmarks:
            return None
            
        fingertips = [4, 8, 12, 16, 20]  # Pulgar, índice, medio, anular, meñique
        finger_states = []
        
        # Verificar cada dedo
        for tip_id in fingertips:
            # Para el pulgar, comparar coordenada x con la base del pulgar
            if tip_id == 4:
                if hand_landmarks.landmark[tip_id].x < hand_landmarks.landmark[tip_id - 2].x:
                    finger_states.append(1)  # Extendido
                else:
                    finger_states.append(0)  # No extendido
            # Para otros dedos, comparar coordenada y con la articulación media
            else:
                if hand_landmarks.landmark[tip_id].y < hand_landmarks.landmark[tip_id - 2].y:
                    finger_states.append(1)  # Extendido
                else:
                    finger_states.append(0)  # No extendido
        
        return finger_states
    
    def display_gesture_info(self, frame):
        """Display current gesture information including finger states.
        
        Args:
            frame (ndarray): The image frame to draw on.
        """
        with self.lock:
            y_pos = frame.shape[0] - 180
            
            # Display current gesture as binary array
            for gesture_id, gesture_data in self.active_gestures.items():
                finger_states = self.detect_finger_states(gesture_data.get("landmarks"))
                if finger_states:
                    # Show gesture name and binary representation
                    gesture_text = f"Gesture: {gesture_data.get('name', gesture_id)}"
                    cv2.putText(frame, gesture_text, (10, y_pos), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    y_pos += 25
                    
                    # Show binary array
                    binary_text = f"Fingers: {finger_states}"
                    cv2.putText(frame, binary_text, (10, y_pos), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                    y_pos += 20
                    
                    # Show individual finger states with colors
                    finger_names = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
                    for i, (name, state) in enumerate(zip(finger_names, finger_states)):
                        color = (0, 255, 0) if state == 1 else (0, 0, 255)  # Green if open, red if closed
                        status = "Open" if state == 1 else "Closed"
                        finger_text = f"{name}: {status}"
                        cv2.putText(frame, finger_text, (10 + i * 100, y_pos), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
                    y_pos += 30
    
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
    
    def display_mode_info(self, frame):
        """
        Muestra información sobre el modo actual y sus controles.
        
        Args:
            frame: Frame donde mostrar la información.
        """
        mode_info = {
            'N': "Modo Normal - Selecciona un modo con un gesto",
            'Cursor': "Modo Cursor - Mueve el índice para controlar el mouse",
            'Scroll': "Modo Scroll - Índice arriba/abajo para desplazarte",
            'Volume': "Modo Volumen - Pinza para ajustar el volumen",
            'Screenshot': "Modo Captura - Gesto de victoria para capturar"
        }
        
        mode_controls = {
            'Cursor': [
                "• Un dedo: Mover cursor",
                "• Dos dedos: Click derecho",
                "• Pulgar + Índice: Arrastrar",
                "• Tres dedos: Doble click"
            ],
            'Scroll': [
                "• Índice arriba: Desplazar arriba",
                "• Índice abajo: Desplazar abajo"
            ],
            'Volume': [
                "• Pinza abierta: Subir volumen",
                "• Pinza cerrada: Bajar volumen"
            ],
            'Screenshot': [
                "• Victoria + Meñique: Capturar pantalla"
            ]
        }
        
        # Mostrar modo actual
        y_pos = 30
        cv2.putText(frame, f"MODO: {self.current_mode}", (10, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Mostrar descripción del modo
        y_pos += 30
        cv2.putText(frame, mode_info.get(self.current_mode, ""), (10, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Mostrar controles específicos del modo
        if self.current_mode in mode_controls:
            y_pos += 30
            cv2.putText(frame, "Controles:", (10, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
            y_pos += 20
            
            for control in mode_controls[self.current_mode]:
                cv2.putText(frame, control, (20, y_pos),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                y_pos += 20

    def display_loop(self):
        """Bucle principal para mostrar la interfaz de usuario y retroalimentación de gestos."""
        while self.running:
            # Obtener el frame actual del gesture manager
            image, _ = self.gesture_manager.process_frame()
            if image is None:
                time.sleep(0.01)
                continue
            
            # Mostrar elementos de UI
            self.display_mode_info(image)  # Primero el modo
            self.display_landmarks(image)   # Luego los landmarks
            self.display_messages(image)    # Finalmente los mensajes
            
            # Mostrar mensajes de gestos
            y0, dy = 200, 30  # Ajustado para no solapar con mode_info
            with self.lock:
                for i, (key, msg) in enumerate(self.gesture_messages.items()):
                    y = y0 + i * dy
                    cv2.putText(image, msg, (10, y), cv2.FONT_HERSHEY_SIMPLEX,
                                0.7, (0, 0, 255), 2)
            
            # Mostrar frame
            cv2.imshow("Control de Mouse por Gestos", image)
            
            # Salir con 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.stop()
                break
        
        cv2.destroyAllWindows()
