"""
Global settings for the GestureControl system.
"""

# Camera settings
DEFAULT_CAMERA_ID = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# Gesture detection settings
CONFIDENCE_THRESHOLD = 0.5
MIN_DETECTION_CONFIDENCE = 0.7
MIN_TRACKING_CONFIDENCE = 0.5

# GestureRecognitionManager settings
GESTURE_MANAGER_ENABLED = True
GESTURE_CONFIG_PATH = "config/GestureConfig.json"
GESTURE_POOL_SIZE = 10
GESTURE_DETECTION_INTERVAL = 0.01  # Seconds between detection attempts when below target FPS

# Controller settings
ACTION_DELAY = 0.3  # Minimum time between actions in seconds

# Volume controller settings
VOLUME_UPPER_THRESHOLD = 20
VOLUME_LOWER_THRESHOLD = 40
VOLUME_SCALING_FACTOR = 4  # Dividing factor for distance calculation

# Brightness controller settings
BRIGHTNESS_UPPER_THRESHOLD = 20
BRIGHTNESS_LOWER_THRESHOLD = 40
BRIGHTNESS_SCALING_FACTOR = 4  # Dividing factor for distance calculation
BRIGHTNESS_INCREMENT_STEP = 5
BRIGHTNESS_DECREMENT_STEP = 5

# App controller settings
APP_GESTURE_DURATION = 2.0  # Seconds to hold gesture before action
APP_CONFIRMATION_REQUIRED = True  # Whether to require confirmation for closing apps
APP_CONFIRMATION_MULTIPLIER = 1.5  # Multiplier for confirmation duration

# Shortcuts controller settings
SHORTCUTS_GESTURE_DURATION = 1.0  # Seconds to hold gesture before action
SHORTCUTS_MESSAGE_DURATION = 3.0  # Seconds to display action message

# Keyboard controller settings
KEYBOARD_PRESS_COOLDOWN = 0.15  # Seconds between key presses
KEYBOARD_PINCH_THRESHOLD = 30  # Distance threshold for pinch gesture

# Navigation controller settings
NAVIGATION_COOLDOWN = 1.0  # Seconds between navigation actions
NAVIGATION_MESSAGE_DURATION = 2.0  # Seconds to display action message

# System controller settings
SYSTEM_GESTURE_DURATION = 3.0  # Seconds to hold gesture before action
SYSTEM_CONFIRMATION_DURATION = 5.0  # Seconds for confirmation countdown
SYSTEM_MESSAGE_DURATION = 3.0  # Seconds to display action message

# Multimedia controller settings
MULTIMEDIA_GESTURE_DURATION = 0.5  # Seconds to hold gesture before action
MULTIMEDIA_ACTION_COOLDOWN = 1.0  # Seconds between multimedia actions
MULTIMEDIA_VOLUME_CHANGE_THRESHOLD = 30  # Vertical movement threshold for volume change
MULTIMEDIA_SWIPE_THRESHOLD = 50  # Horizontal movement threshold for next/previous track
MULTIMEDIA_MESSAGE_DURATION = 2.0  # Seconds to display action message

# Zoom controller settings
ZOOM_CAMERA_WIDTH = 1280
ZOOM_CAMERA_HEIGHT = 720
ZOOM_DEFAULT_IMAGE_PATH = "assets/sample_image.jpg"

# Paint controller settings
PAINT_TOOL_SELECTION_TIME = 0.8  # Seconds to hold for tool selection
PAINT_LINE_THICKNESS = 4  # Default line thickness
PAINT_ERASER_SIZE = 30  # Size of eraser circle

# Mouse controller settings
MOUSE_FRAME_REDUCTION = 100  # Frame reduction for cursor control area
MOUSE_SMOOTHENING = 7  # Smoothening factor for mouse movement
MOUSE_CLICK_COOLDOWN = 10  # Frames to wait between clicks
MOUSE_VOLUME_MIN = 50  # Minimum hand distance for volume control
MOUSE_VOLUME_MAX = 200  # Maximum hand distance for volume control
MOUSE_SCREENSHOT_COOLDOWN = 30  # Frames to wait between screenshots

# UI settings
WINDOW_TITLE = "Gesture Control System"
FONT = "Arial"
FONT_SIZE = 12
FONT_COLOR = (255, 255, 255)  # White
BACKGROUND_COLOR = (0, 0, 0)  # Black

# Paths
LOG_PATH = "logs/gesture_log.txt"
GESTURE_LOG_PATH = "logs/gesture_recognition.log"
MODEL_PATH = "models/hand_gesture_model.pkl"
GESTURE_MAPPINGS_PATH = "config/gesture_mappings.json"
APP_GESTURES_PATH = "config/app_gestures.json"
KEYBOARD_GESTURES_PATH = "config/keyboard_gestures.json"
GESTURE_CONFIG_PATH = "config/GestureConfig.json"