import argparse
import sys
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
# Import other controllers as you implement them
# from core.controllers.scroll_controller import ScrollController
# etc.

def main():
    """Main entry point for the GestureControl system."""
    parser = argparse.ArgumentParser(description='GestureControl - Control your computer with hand gestures')
    parser.add_argument('--mode', type=str, default='volume',
                        choices=['volume', 'brightness', 'app', 'shortcuts', 'keyboard', 'navigation', 
                                'system', 'multimedia', 'zoom', 'paint', 'mouse', 'scroll', 'presentation'],
                        help='The control mode to run')
    parser.add_argument('--camera', type=int, default=0,
                        help='Camera device ID (default: 0)')
    
    args = parser.parse_args()
    
    # Select the appropriate controller based on the mode
    if args.mode == 'volume':
        controller = VolumeController()
    elif args.mode == 'brightness':
        controller = BrightnessController()
    elif args.mode == 'app':
        controller = AppController()
    elif args.mode == 'shortcuts':
        controller = ShortcutsController()
    elif args.mode == 'keyboard':
        controller = KeyboardController()
    elif args.mode == 'navigation':
        controller = NavigationController()
    elif args.mode == 'system':
        controller = SystemController()
    elif args.mode == 'multimedia':
        controller = MultimediaController()
    elif args.mode == 'zoom':
        controller = ZoomController()
    elif args.mode == 'paint':
        controller = PaintController()
    elif args.mode == 'mouse':
        controller = MouseController()
    # Add other controllers as you implement them
    # elif args.mode == 'scroll':
    #     controller = ScrollController()
    else:
        print(f"Mode '{args.mode}' is not implemented yet.")
        return
    
    try:
        # Run the selected controller
        controller.run()
    except KeyboardInterrupt:
        print("\nExiting GestureControl...")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())