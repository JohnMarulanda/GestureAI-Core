import cv2
import screen_brightness_control as sbc
import mediapipe as mp
import os
import time
import threading
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class BrightnessControllerEnhanced:
    """Controlador mejorado para ajustar el brillo de la pantalla usando gestos predefinidos de MediaPipe."""
    
    def __init__(self, model_path=None):
        """Inicializar el controlador de brillo con reconocimiento de gestos."""
        # Establecer ruta del modelo por defecto si no se proporciona
        if model_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            model_path = os.path.join(project_root, 'models', 'gesture_recognizer.task')
        
        self.model_path = model_path
        self.webcam = None
        self.gesture_recognizer = None
        
        # Temporización y retrasos
        self.last_action_time = 0
        self.action_delay = 0.3
        
        # Estado del control de brillo
        self.last_gesture = None
        self.current_result = None
        self.confidence_threshold = 0.7
        
        # Inicializar sistema de brillo
        self.brightness_available = self._initialize_brightness()
        
        # Mapeo de gestos para control de brillo
        self.gesture_actions = {
            'Thumb_Up': 'subir_brillo',
            'Thumb_Down': 'bajar_brillo'
        }
        
        # Configuración de control de brillo
        self.brightness_steps = 15
        
        # Seguridad de hilos
        self.brightness_lock = threading.Lock()
        
        # Configuración de ventana
        self.window_width = 480
        self.window_height = 360
        self.window_name = 'Control de Brillo'
        
        # Colores para visualización
        self.landmark_color = (0, 255, 0)  # Verde
        self.connection_color = (255, 0, 0)  # Azul
        self.text_color = (86, 185, 157)  # Azul verdoso
        
        self._initialize_recognizer()
    
    def _initialize_brightness(self):
        """Inicializar y probar el sistema de control de brillo."""
        try:
            # Probar si podemos obtener el brillo
            monitors = sbc.list_monitors()
            
            if not monitors:
                self.current_brightness = 50
                return False
            
            # Intentar obtener el brillo actual
            brightness_values = sbc.get_brightness()
            if brightness_values:
                self.current_brightness = brightness_values[0]
                
                # Probar si podemos establecer el brillo
                test_brightness = self.current_brightness
                sbc.set_brightness(test_brightness)
                return True
            else:
                self.current_brightness = 50
                return False
                
        except Exception as e:
            # Intentar método alternativo
            try:
                import subprocess
                # Para Windows, intentar usar powershell
                result = subprocess.run([
                    'powershell', 
                    '(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness'
                ], capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0 and result.stdout.strip():
                    self.current_brightness = int(result.stdout.strip())
                    return True
                else:
                    self.current_brightness = 50
                    return False
            except Exception as e2:
                self.current_brightness = 50
                return False
    
    def _initialize_recognizer(self):
        """Inicializar el MediaPipe Gesture Recognizer."""
        try:
            if not os.path.exists(self.model_path):
                self.gesture_recognizer = None
                return
            
            # Configurar opciones base
            base_options = python.BaseOptions(model_asset_path=self.model_path)
            
            # Configurar opciones del reconocedor de gestos
            options = vision.GestureRecognizerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.LIVE_STREAM,
                result_callback=self._gesture_result_callback,
                num_hands=1,
                min_hand_detection_confidence=0.7,
                min_hand_presence_confidence=0.7,
                min_tracking_confidence=0.7
            )
            
            # Crear el reconocedor de gestos
            self.gesture_recognizer = vision.GestureRecognizer.create_from_options(options)
            
        except Exception as e:
            self.gesture_recognizer = None
    
    def _gesture_result_callback(self, result: vision.GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int):
        """Función de callback para manejar resultados del reconocimiento de gestos."""
        try:
            self.current_result = result
            
            if result.gestures:
                for hand_gesture in result.gestures:
                    if hand_gesture:
                        gesture = hand_gesture[0]
                        gesture_name = gesture.category_name
                        confidence = gesture.score
                        
                        # Solo procesar gestos de control de brillo con alta confianza
                        if (gesture_name in self.gesture_actions and 
                            confidence >= self.confidence_threshold):
                            
                            current_time = time.time()
                            if current_time - self.last_action_time > self.action_delay:
                                self.last_gesture = gesture_name
                                # Usar threading para evitar bloquear el callback
                                threading.Thread(
                                    target=self._perform_brightness_action,
                                    args=(gesture_name, confidence),
                                    daemon=True
                                ).start()
                                self.last_action_time = current_time
        except Exception as e:
            pass
    
    def _perform_brightness_action(self, gesture_name, confidence):
        """Ejecutar la acción de brillo basada en el gesto detectado."""
        with self.brightness_lock:
            try:
                action = self.gesture_actions[gesture_name]
                
                if not self.brightness_available:
                    return
                
                if action == 'subir_brillo':
                    # Aumentar brillo
                    new_brightness = min(100, self.current_brightness + self.brightness_steps)
                    if new_brightness != self.current_brightness:
                        if self._set_brightness_safe(new_brightness):
                            self.current_brightness = new_brightness
                
                elif action == 'bajar_brillo':
                    # Disminuir brillo
                    new_brightness = max(10, self.current_brightness - self.brightness_steps)
                    if new_brightness != self.current_brightness:
                        if self._set_brightness_safe(new_brightness):
                            self.current_brightness = new_brightness
                            
            except Exception as e:
                pass
    
    def _set_brightness_safe(self, brightness_value):
        """Establecer el brillo de forma segura con manejo de errores."""
        try:
            # Método 1: Intentar screen_brightness_control
            sbc.set_brightness(brightness_value)
            return True
        except Exception as e1:
            try:
                # Método 2: Intentar con monitor específico
                monitors = sbc.list_monitors()
                if monitors:
                    sbc.set_brightness(brightness_value, display=monitors[0])
                    return True
            except Exception as e2:
                try:
                    # Método 3: Intentar Windows WMI (solo para Windows)
                    import subprocess
                    subprocess.run([
                        'powershell', 
                        f'(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{brightness_value})'
                    ], capture_output=True, timeout=3)
                    return True
                except Exception as e3:
                    return False
    
    def start_camera(self, camera_id=0):
        """Iniciar la captura de la cámara."""
        try:
            self.webcam = cv2.VideoCapture(camera_id)
            if not self.webcam.isOpened():
                return False
            
            # Configurar propiedades de la cámara
            self.webcam.set(cv2.CAP_PROP_FRAME_WIDTH, self.window_width)
            self.webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, self.window_height)
            self.webcam.set(cv2.CAP_PROP_FPS, 30)
            self.webcam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            return True
        except Exception as e:
            return False
    
    def stop_camera(self):
        """Detener la cámara y limpiar recursos."""
        try:
            if self.webcam:
                self.webcam.release()
            cv2.destroyAllWindows()
        except Exception as e:
            pass
    
    def process_frame(self):
        """Procesar un solo frame de la webcam."""
        try:
            if not self.webcam or not self.webcam.isOpened():
                return None
                
            success, image = self.webcam.read()
            if not success:
                return None
                
            # Voltear la imagen horizontalmente para efecto espejo
            image = cv2.flip(image, 1)
            
            return image
        except Exception as e:
            return None
    
    def draw_hand_landmarks(self, image):
        """Dibujar landmarks de la mano en la imagen."""
        try:
            if self.current_result and self.current_result.hand_landmarks:
                for hand_landmarks in self.current_result.hand_landmarks:
                    # Convertir landmarks normalizados a coordenadas de píxeles
                    hand_landmarks_pixel = []
                    for landmark in hand_landmarks:
                        x = int(landmark.x * image.shape[1])
                        y = int(landmark.y * image.shape[0])
                        hand_landmarks_pixel.append((x, y))
                    
                    # Dibujar landmarks con mejor estilo
                    for i, point in enumerate(hand_landmarks_pixel):
                        if i == 0:  # Muñeca más grande
                            cv2.circle(image, point, 8, self.landmark_color, -1)
                            cv2.circle(image, point, 10, (255, 255, 255), 2)
                        else:
                            cv2.circle(image, point, 4, self.landmark_color, -1)
                            cv2.circle(image, point, 6, (255, 255, 255), 1)
                    
                    # Dibujar conexiones mejoradas
                    connections = [
                        # Pulgar
                        (0, 1), (1, 2), (2, 3), (3, 4),
                        # Índice
                        (0, 5), (5, 6), (6, 7), (7, 8),
                        # Medio
                        (0, 9), (9, 10), (10, 11), (11, 12),
                        # Anular
                        (0, 13), (13, 14), (14, 15), (15, 16),
                        # Meñique
                        (0, 17), (17, 18), (18, 19), (19, 20),
                        # Conexiones de la palma
                        (5, 9), (9, 13), (13, 17), (17, 5)
                    ]
                    
                    for connection in connections:
                        if connection[0] < len(hand_landmarks_pixel) and connection[1] < len(hand_landmarks_pixel):
                            cv2.line(image, hand_landmarks_pixel[connection[0]], 
                                    hand_landmarks_pixel[connection[1]], self.connection_color, 2)
        except Exception as e:
            pass
    
    def draw_minimal_info(self, image):
        """Dibujar información mínima en la imagen."""
        # Dibujar instrucciones y estado actual
        instructions = [
            "Control de Brillo:",
            f"Brillo actual: {self.current_brightness}%",
            "",
            "Gestos disponibles:",
            "👍 Pulgar arriba: Subir brillo",
            "👎 Pulgar abajo: Bajar brillo"
        ]
        
        y_pos = 30
        for instruction in instructions:
            # Borde negro para mejor contraste
            cv2.putText(image, instruction, (10, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            # Texto en color azul verdoso
            cv2.putText(image, instruction, (10, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.text_color, 1)
            y_pos += 25
        
        # Mostrar gesto actual si existe
        if self.last_gesture:
            action = self.gesture_actions.get(self.last_gesture, '')
            if action == 'subir_brillo':
                text = "Subiendo brillo..."
            elif action == 'bajar_brillo':
                text = "Bajando brillo..."
            else:
                text = ""
                
            if text:
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                x = image.shape[1] - text_size[0] - 10
                y = 25
                
                # Fondo semitransparente
                cv2.rectangle(image, (x-5, y-20), (x+text_size[0]+5, y+5), (0, 0, 0), -1)
                cv2.putText(image, text, (x, y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.text_color, 2)
        
        # Indicador ESC en la esquina inferior izquierda
        cv2.putText(image, "ESC: Salir", (10, image.shape[0] - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def run(self):
        """Ejecutar el bucle principal del controlador."""
        if not self.gesture_recognizer:
            return False
            
        if not self.start_camera():
            return False
        
        try:
            frame_timestamp = 0
            frame_count = 0
            
            while True:
                image = self.process_frame()
                if image is None:
                    break
                
                frame_count += 1
                
                # Procesar cada segundo frame para mejor rendimiento
                if frame_count % 2 == 0:
                    # Convertir BGR a RGB para MediaPipe
                    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
                    
                    # Procesar el frame con el reconocedor de gestos
                    if self.gesture_recognizer:
                        frame_timestamp += 66
                        try:
                            self.gesture_recognizer.recognize_async(mp_image, frame_timestamp)
                        except Exception as e:
                            pass
                
                # Dibujar landmarks de la mano
                self.draw_hand_landmarks(image)
                
                # Dibujar información mínima
                self.draw_minimal_info(image)
                
                # Mostrar imagen
                cv2.imshow(self.window_name, image)
                
                # Salir con ESC o al cerrar la ventana
                key = cv2.waitKey(1) & 0xFF
                if key == 27 or cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) < 1:
                    break
                    
        except KeyboardInterrupt:
            pass
        except Exception as e:
            pass
        finally:
            self.stop_camera()
            return True

def main():
    """Función principal silenciosa."""
    try:
        controller = BrightnessControllerEnhanced()
        controller.run()
    except Exception as e:
        pass

if __name__ == "__main__":
    main() 