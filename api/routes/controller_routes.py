from fastapi import APIRouter, HTTPException
from typing import Dict, List
import threading

# Import controller classes
from core.controllers.volume_controller import VolumeController
from core.controllers.brightness_controller import BrightnessController
from core.controllers.app_controller import AppController
from core.controllers.shortcuts_controller import ShortcutsController
from core.controllers.keyboard_controller import KeyboardController
from core.controllers.navigation_controller import NavigationController
from core.controllers.system_controller import SystemController
from core.controllers.multimedia_controller import MultimediaController
from core.controllers.zoom_controller import ZoomController
from core.controllers.paint_controller import PaintController
from core.controllers.mouse_controller import MouseController

# Define the API router for controller operations
router = APIRouter(prefix="/controller", tags=["controllers"])

# Dictionary to store active controller instances and their threads
active_controllers = {}

# Mapping of available controllers by name to their respective classes
controllers = {
    "volume": VolumeController,
    "brightness": BrightnessController,
    "app": AppController,
    "shortcuts": ShortcutsController,
    "keyboard": KeyboardController,
    "navigation": NavigationController,
    "system": SystemController,
    "multimedia": MultimediaController,
    "zoom": ZoomController,
    "paint": PaintController,
    "mouse": MouseController
}

@router.get("/")
async def list_controllers():
    """
    List all available controllers and indicate whether each one is currently active.

    Returns:
        A dictionary with controller names and their active status.
    """
    return {
        "controllers": [
            {
                "name": name,
                "active": name in active_controllers
            } for name in controllers.keys()
        ]
    }

@router.post("/{name}/start")
async def start_controller(name: str):
    """
    Start a specific controller by name.

    Args:
        name (str): The name of the controller to start.

    Returns:
        Success message if started correctly.
    Raises:
        HTTPException: If the controller is not found or already active,
        or if an error occurs during startup.
    """
    if name not in controllers:
        raise HTTPException(status_code=404, detail="Controller not found")
    
    if name in active_controllers:
        raise HTTPException(status_code=400, detail="Controller is already active")
    
    try:
        # Instantiate the controller
        controller = controllers[name]()
        
        # Start the controller in a separate daemon thread
        controller_thread = threading.Thread(target=controller.start)
        controller_thread.daemon = True
        controller_thread.start()
        
        # Store the controller instance and thread reference
        active_controllers[name] = {
            "instance": controller,
            "thread": controller_thread
        }
        
        return {"status": "success", "message": f"Controller '{name}' started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start controller: {str(e)}")

@router.post("/{name}/stop")
async def stop_controller(name: str):
    """
    Stop a specific active controller by name.

    Args:
        name (str): The name of the controller to stop.

    Returns:
        Success message if stopped correctly.
    Raises:
        HTTPException: If the controller is not active or an error occurs during shutdown.
    """
    if name not in active_controllers:
        raise HTTPException(status_code=404, detail="Controller not found or not active")
    
    try:
        # Stop the controller
        controller_data = active_controllers[name]
        controller_data["instance"].stop()
        
        # Wait for the controller's thread to terminate
        controller_data["thread"].join(timeout=2.0)
        
        # Remove controller from active registry
        del active_controllers[name]
        
        return {"status": "success", "message": f"Controller '{name}' stopped successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop controller: {str(e)}")

@router.get("/{name}/status")
async def controller_status(name: str):
    """
    Get the current status of a specific controller.

    Args:
        name (str): The name of the controller.

    Returns:
        A dictionary containing controller name, whether it's active,
        and whether its thread is currently running.
    Raises:
        HTTPException: If the controller is not found.
    """
    if name not in controllers:
        raise HTTPException(status_code=404, detail="Controller not found")
    
    is_active = name in active_controllers
    status_info = {
        "name": name,
        "active": is_active,
        "running": False
    }
    
    # If active, check if the controller's thread is alive
    if is_active:
        controller_data = active_controllers[name]
        status_info["running"] = controller_data["thread"].is_alive()
    
    return status_info
