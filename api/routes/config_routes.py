from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
import json
import os
from config import settings

# Define the API router with a prefix and tag for configuration-related endpoints
router = APIRouter(prefix="/config", tags=["configuration"])

# Path to the gesture configuration file
GESTURE_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                   settings.GESTURE_CONFIG_PATH)

@router.get("/gestures")
async def get_gestures():
    """
    Retrieve the current hand gesture configuration from the gesture config file.

    Returns:
        JSON object containing the list of configured hand gestures.
    Raises:
        HTTPException: If the configuration file cannot be read.
    """
    try:
        with open(GESTURE_CONFIG_PATH, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read configuration: {str(e)}")

@router.post("/gestures/hand")
async def add_hand_gesture(gesture: Dict):
    """
    Add a new hand gesture to the configuration.

    Args:
        gesture (Dict): A dictionary representing the gesture with required fields.

    Returns:
        Confirmation message and the added gesture.
    Raises:
        HTTPException: If required fields are missing or file operations fail.
    """
    try:
        with open(GESTURE_CONFIG_PATH, 'r') as f:
            config = json.load(f)
        
        # Validate the gesture contains all required fields
        required_fields = ["id", "name", "landmarks", "threshold", "action"]
        if not all(field in gesture for field in required_fields):
            raise HTTPException(status_code=400, detail="Missing required gesture fields")
        
        # Add the gesture to the configuration
        config["hand_gestures"].append(gesture)
        
        # Save updated configuration
        with open(GESTURE_CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=4)
        
        return {"message": "Gesture successfully added", "gesture": gesture}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add gesture: {str(e)}")

@router.put("/gestures/hand/{gesture_id}")
async def update_hand_gesture(gesture_id: str, gesture: Dict):
    """
    Update an existing hand gesture by its ID.

    Args:
        gesture_id (str): The ID of the gesture to update.
        gesture (Dict): The new gesture data.

    Returns:
        Confirmation message and the updated gesture.
    Raises:
        HTTPException: If the gesture is not found or file operations fail.
    """
    try:
        with open(GESTURE_CONFIG_PATH, 'r') as f:
            config = json.load(f)
        
        # Find and update the gesture
        for i, g in enumerate(config["hand_gestures"]):
            if g["id"] == gesture_id:
                config["hand_gestures"][i] = gesture
                break
        else:
            raise HTTPException(status_code=404, detail="Gesture not found")
        
        # Save updated configuration
        with open(GESTURE_CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=4)
        
        return {"message": "Gesture successfully updated", "gesture": gesture}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update gesture: {str(e)}")

@router.delete("/gestures/hand/{gesture_id}")
async def delete_hand_gesture(gesture_id: str):
    """
    Delete a hand gesture from the configuration by its ID.

    Args:
        gesture_id (str): The ID of the gesture to delete.

    Returns:
        Confirmation message.
    Raises:
        HTTPException: If file operations fail.
    """
    try:
        with open(GESTURE_CONFIG_PATH, 'r') as f:
            config = json.load(f)
        
        # Filter out the gesture to delete
        config["hand_gestures"] = [g for g in config["hand_gestures"] if g["id"] != gesture_id]
        
        # Save updated configuration
        with open(GESTURE_CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=4)
        
        return {"message": "Gesture successfully deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete gesture: {str(e)}")

@router.get("/settings")
async def get_settings():
    """
    Retrieve the current system settings from the settings module.

    Returns:
        Dictionary with system configuration for camera, gesture detection,
        and various controllers (volume, brightness, mouse).
    """
    config_dict = {
        "camera": {
            "default_id": settings.DEFAULT_CAMERA_ID,
            "width": settings.CAMERA_WIDTH,
            "height": settings.CAMERA_HEIGHT,
            "fps": settings.CAMERA_FPS
        },
        "gesture_detection": {
            "confidence_threshold": settings.CONFIDENCE_THRESHOLD,
            "min_detection_confidence": settings.MIN_DETECTION_CONFIDENCE,
            "min_tracking_confidence": settings.MIN_TRACKING_CONFIDENCE
        },
        "controllers": {
            "action_delay": settings.ACTION_DELAY,
            "volume": {
                "upper_threshold": settings.VOLUME_UPPER_THRESHOLD,
                "lower_threshold": settings.VOLUME_LOWER_THRESHOLD,
                "scaling_factor": settings.VOLUME_SCALING_FACTOR
            },
            "brightness": {
                "upper_threshold": settings.BRIGHTNESS_UPPER_THRESHOLD,
                "lower_threshold": settings.BRIGHTNESS_LOWER_THRESHOLD,
                "scaling_factor": settings.BRIGHTNESS_SCALING_FACTOR
            },
            "mouse": {
                "frame_reduction": settings.MOUSE_FRAME_REDUCTION,
                "smoothening": settings.MOUSE_SMOOTHENING
            }
        }
    }
    return config_dict

@router.put("/settings/{category}")
async def update_settings(category: str, settings_update: Dict):
    """
    Update the system settings for a specific category.

    Args:
        category (str): The settings category to update (e.g., 'camera', 'gesture_detection').
        settings_update (Dict): Dictionary with new settings values.

    Returns:
        Placeholder message indicating the feature is not yet implemented.
    """
    # Placeholder: actual update logic for settings should be implemented
    return {
        "message": "Settings update not implemented",
        "category": category,
        "settings": settings_update
    }
