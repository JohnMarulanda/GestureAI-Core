import cv2
import mediapipe as mp
import os
import time
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class CannedGesturesController:
    """Controller for detecting and tracking canned gestures using MediaPipe Gesture Recognizer."""
    
    def __init__(self, model_path=None):
        """Initialize the canned gestures controller."""
        # Set default model path if not provided
        if model_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            model_path = os.path.join(project_root, 'models', 'gesture_recognizer.task')
        
        self.model_path = model_path
        self.webcam = None
        self.gesture_recognizer = None
        self.last_action_time = 0
        self.action_delay = 0.5  # Delay between gesture detections
        
        # Gesture mapping for better display
        self.gesture_mapping = {
            'None': 'Sin gesto detectado',
            'Closed_Fist': 'Puño cerrado',
            'Open_Palm': 'Palma abierta',
            'Pointing_Up': 'Señalando hacia arriba',
            'Thumb_Down': 'Pulgar hacia abajo',
            'Thumb_Up': 'Pulgar hacia arriba',
            'Victory': 'Victoria (V)',
            'ILoveYou': 'Te amo (I Love You)'
        }
        
        # Gesture statistics
        self.gesture_counts = {gesture: 0 for gesture in self.gesture_mapping.keys()}
        self.last_detected_gesture = None
        self.current_result = None
        self.confidence_threshold = 0.7
        
        self._initialize_recognizer()
    
    def _initialize_recognizer(self):
        """Initialize the MediaPipe Gesture Recognizer."""
        try:
            # Configure base options
            base_options = python.BaseOptions(model_asset_path=self.model_path)
            
            # Configure gesture recognizer options (versión simplificada compatible)
            options = vision.GestureRecognizerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.LIVE_STREAM,
                result_callback=self._gesture_result_callback,
                num_hands=2,  # Detect up to 2 hands
                min_hand_detection_confidence=0.5,
                min_hand_presence_confidence=0.5,
                min_tracking_confidence=0.5
            )
            
            # Create the gesture recognizer
            self.gesture_recognizer = vision.GestureRecognizer.create_from_options(options)
            print("✅ Gesture Recognizer inicializado correctamente")
            
        except Exception as e:
            print(f"❌ Error al inicializar Gesture Recognizer: {e}")
            self.gesture_recognizer = None
    
    def _gesture_result_callback(self, result: vision.GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int):
        """Callback function to handle gesture recognition results."""
        self.current_result = result
        
        if result.gestures:
            for hand_gesture in result.gestures:
                if hand_gesture:
                    gesture = hand_gesture[0]  # Get the top gesture
                    gesture_name = gesture.category_name
                    confidence = gesture.score
                    
                    # Only process if confidence is above threshold
                    if confidence >= self.confidence_threshold:
                        current_time = time.time()
                        if current_time - self.last_action_time > self.action_delay:
                            self.last_detected_gesture = gesture_name
                            self.gesture_counts[gesture_name] += 1
                            self.last_action_time = current_time
                            
                            # Print detected gesture
                            spanish_name = self.gesture_mapping.get(gesture_name, gesture_name)
                            print(f"🖐️ Gesto detectado: {spanish_name} (Confianza: {confidence:.2f})")
    
    def start_camera(self, camera_id=0):
        """Start the webcam capture."""
        try:
            self.webcam = cv2.VideoCapture(camera_id)
            if not self.webcam.isOpened():
                print("❌ Error: No se pudo abrir la cámara")
                return False
            
            # Set camera properties for better performance
            self.webcam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.webcam.set(cv2.CAP_PROP_FPS, 30)
            
            print("✅ Cámara iniciada correctamente")
            return True
        except Exception as e:
            print(f"❌ Error al iniciar la cámara: {e}")
            return False
    
    def stop_camera(self):
        """Release the webcam and close windows."""
        if self.webcam:
            self.webcam.release()
        cv2.destroyAllWindows()
        print("📷 Cámara cerrada")
    
    def process_frame(self):
        """Process a single frame from the webcam."""
        if not self.webcam or not self.webcam.isOpened():
            return None
            
        success, image = self.webcam.read()
        if not success:
            return None
            
        # Flip the image horizontally for a mirror effect
        image = cv2.flip(image, 1)
        
        return image
    
    def draw_gesture_info(self, image):
        """Draw gesture information on the image."""
        height, width, _ = image.shape
        
        # Draw background rectangle for text
        cv2.rectangle(image, (10, 10), (width - 10, 180), (0, 0, 0), -1)
        cv2.rectangle(image, (10, 10), (width - 10, 180), (255, 255, 255), 2)
        
        # Draw title
        cv2.putText(image, "Reconocimiento de Gestos Predefinidos", 
                   (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Draw last detected gesture
        if self.last_detected_gesture:
            spanish_name = self.gesture_mapping.get(self.last_detected_gesture, self.last_detected_gesture)
            cv2.putText(image, f"Ultimo gesto: {spanish_name}", 
                       (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Draw hands detected count
        hands_count = len(self.current_result.hand_landmarks) if self.current_result and self.current_result.hand_landmarks else 0
        cv2.putText(image, f"Manos detectadas: {hands_count}", 
                   (20, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Draw gesture counts in a compact format
        y_pos = 110
        line1 = f"Puno: {self.gesture_counts['Closed_Fist']} | Palma: {self.gesture_counts['Open_Palm']} | Arriba: {self.gesture_counts['Pointing_Up']}"
        line2 = f"Pulgar-: {self.gesture_counts['Thumb_Down']} | Pulgar+: {self.gesture_counts['Thumb_Up']} | Victoria: {self.gesture_counts['Victory']} | Love: {self.gesture_counts['ILoveYou']}"
        
        cv2.putText(image, line1, (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        cv2.putText(image, line2, (20, y_pos + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        # Draw instructions
        cv2.putText(image, "Presiona ESC para salir | Espacio para estadisticas", 
                   (20, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
    
    def draw_hand_landmarks(self, image):
        """Draw hand landmarks on the image."""
        if self.current_result and self.current_result.hand_landmarks:
            for hand_landmarks in self.current_result.hand_landmarks:
                # Convert normalized landmarks to pixel coordinates
                hand_landmarks_pixel = []
                for landmark in hand_landmarks:
                    x = int(landmark.x * image.shape[1])
                    y = int(landmark.y * image.shape[0])
                    hand_landmarks_pixel.append((x, y))
                
                # Draw landmarks
                for point in hand_landmarks_pixel:
                    cv2.circle(image, point, 3, (0, 255, 0), -1)
                
                # Draw connections between landmarks (simplified)
                connections = [
                    (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
                    (0, 5), (5, 6), (6, 7), (7, 8),  # Index finger
                    (0, 9), (9, 10), (10, 11), (11, 12),  # Middle finger
                    (0, 13), (13, 14), (14, 15), (15, 16),  # Ring finger
                    (0, 17), (17, 18), (18, 19), (19, 20),  # Pinky
                    (5, 9), (9, 13), (13, 17)  # Palm connections
                ]
                
                for connection in connections:
                    if connection[0] < len(hand_landmarks_pixel) and connection[1] < len(hand_landmarks_pixel):
                        cv2.line(image, hand_landmarks_pixel[connection[0]], 
                                hand_landmarks_pixel[connection[1]], (255, 0, 0), 2)
    
    def print_statistics(self):
        """Print gesture detection statistics."""
        print("\n" + "="*50)
        print("📊 ESTADÍSTICAS DE DETECCIÓN DE GESTOS")
        print("="*50)
        total_gestures = sum(self.gesture_counts.values())
        
        for gesture_en, count in self.gesture_counts.items():
            gesture_es = self.gesture_mapping[gesture_en]
            percentage = (count / total_gestures * 100) if total_gestures > 0 else 0
            print(f"{gesture_es:<25} | {count:>3} veces ({percentage:>5.1f}%)")
        
        print("-"*50)
        print(f"{'Total de gestos detectados':<25} | {total_gestures:>3}")
        print("="*50 + "\n")
    
    def run(self):
        """Run the canned gestures recognition loop."""
        if not self.gesture_recognizer:
            print("❌ Error: Gesture Recognizer no está inicializado")
            return
            
        if not self.start_camera():
            print("❌ Error: No se pudo iniciar la cámara")
            return
        
        print("\n🚀 Iniciando reconocimiento de gestos predefinidos...")
        print("Gestos disponibles:")
        for i, (gesture_en, gesture_es) in enumerate(self.gesture_mapping.items(), 1):
            if gesture_en != 'None':
                print(f"  {i}. {gesture_es}")
        print("\n💡 Muestra diferentes gestos frente a la cámara para probarlos")
        print("   Presiona ESC para salir o ESPACIO para ver estadísticas\n")
        
        try:
            frame_timestamp = 0
            while True:
                image = self.process_frame()
                if image is None:
                    break
                
                # Convert BGR to RGB for MediaPipe
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
                
                # Process the frame with gesture recognizer
                if self.gesture_recognizer:
                    frame_timestamp += 33  # Approximately 30 FPS
                    self.gesture_recognizer.recognize_async(mp_image, frame_timestamp)
                
                # Draw gesture information on the image
                self.draw_gesture_info(image)
                
                # Draw hand landmarks
                self.draw_hand_landmarks(image)
                
                # Display the image
                cv2.imshow('Reconocimiento de Gestos Predefinidos', image)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC key
                    break
                elif key == 32:  # Space key
                    self.print_statistics()
                    
        except KeyboardInterrupt:
            print("\n⚠️ Interrupción por teclado detectada")
        except Exception as e:
            print(f"❌ Error durante la ejecución: {e}")
        finally:
            self.stop_camera()
            self.print_statistics()
            print("👋 Programa finalizado")


def main():
    """Main function to run the canned gestures controller."""
    controller = CannedGesturesController()
    controller.run()


if __name__ == "__main__":
    main() 