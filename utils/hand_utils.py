import cv2
import mediapipe as mp

def draw_hand_landmarks(image, hand_landmarks, drawing_utils=None):
    """
    Draw hand landmarks on the image.
    
    Args:
        image: The image to draw on
        hand_landmarks: MediaPipe hand landmarks
        drawing_utils: MediaPipe drawing utilities
    
    Returns:
        Image with landmarks drawn
    """
    if drawing_utils is None:
        drawing_utils = mp.solutions.drawing_utils
        
    if hand_landmarks:
        for hand in hand_landmarks:
            drawing_utils.draw_landmarks(image, hand)
    
    return image

def get_finger_positions(hand_landmarks, frame_width, frame_height):
    """
    Extract positions of key finger points from hand landmarks.
    
    Args:
        hand_landmarks: MediaPipe hand landmarks
        frame_width: Width of the frame
        frame_height: Height of the frame
    
    Returns:
        Dictionary with finger positions
    """
    if not hand_landmarks:
        return {}
    
    finger_positions = {}
    
    # Finger landmark indices in MediaPipe
    finger_indices = {
        'thumb_tip': 4,
        'index_tip': 8,
        'middle_tip': 12,
        'ring_tip': 16,
        'pinky_tip': 20,
        'wrist': 0,
        'thumb_mcp': 2,  # Metacarpophalangeal joint
        'index_mcp': 5,
        'middle_mcp': 9,
        'ring_mcp': 13,
        'pinky_mcp': 17
    }
    
    for hand in hand_landmarks:
        landmarks = hand.landmark
        for finger_name, idx in finger_indices.items():
            if idx < len(landmarks):
                landmark = landmarks[idx]
                x = int(landmark.x * frame_width)
                y = int(landmark.y * frame_height)
                finger_positions[finger_name] = (x, y)
    
    return finger_positions