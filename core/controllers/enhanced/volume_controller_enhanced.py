import cv2
import pyautogui
import mediapipe as mp
import os
import time
import sys
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class VolumeControllerEnhanced:
    """Controlador mejorado para ajustar el volumen del sistema usando gestos de MediaPipe."""
    
    def __init__(self, model_path=None):
        """Inicializar el controlador de volumen con reconocimiento de gestos."""
        # Buscar el modelo en varias ubicaciones
        if model_path is None:
            possible_paths = [
                os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models', 'gesture_recognizer.task'),
                os.path.join(os.path.dirname(sys.executable), 'models', 'gesture_recognizer.task'),
                os.path.join(os.getcwd(), 'models', 'gesture_recognizer.task'),
                'models/gesture_recognizer.task',
                'gesture_recognizer.task'
            ]
            
            model_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    model_path = path
                    break
            
            if model_path is None:
                sys.exit(1)
        
        self.model_path = model_path
        self.webcam = None
        self.gesture_recognizer = None
        self.last_action_time = 0
        self.action_delay = 0.4  # Volver al delay original que funciona bien
        
        # Estado del control de volumen
        self.is_muted = False
        self.last_gesture = None
        self.current_result = None
        self.confidence_threshold = 0.7  # Volver al umbral original
        
        # Delay específico para mute/unmute
        self.last_mute_time = 0
        self.mute_delay = 2.0  # 2 segundos de delay para silenciar
        
        # Variables para el gesto de cerrar script (Pointing_Up)
        self.close_gesture_start_time = None
        self.close_gesture_duration = 3.0  # 3 segundos para cerrar script
        self.is_showing_close_progress = False
        self.should_exit = False
        
        # Mapeo de gestos
        self.gesture_actions = {
            'Thumb_Up': 'volume_up',
            'Thumb_Down': 'volume_down',
            'Closed_Fist': 'toggle_mute'
        }
        
        # Mapeo de nombres de gestos para mostrar
        self.gesture_display_names = {
            'Thumb_Up': 'Subir volumen',
            'Thumb_Down': 'Bajar volumen',
            'Closed_Fist': 'Silenciar'
        }
        
        # Contadores de acciones
        self.action_counts = {
            'volume_up': 0,
            'volume_down': 0,
            'mute': 0,
            'unmute': 0
        }
        
        # Configuración de volumen
        self.volume_steps = 3  # Ajustado a 3 pasos
        
        # Colores para landmarks mejorados
        self.landmark_color = (0, 255, 0)  # Verde
        self.connection_color = (255, 0, 0)  # Azul
        self.gesture_color = (0, 255, 255)  # Amarillo
        
        # Deshabilitar failsafe de pyautogui
        pyautogui.FAILSAFE = False
        
        self._initialize_recognizer()
    
    def _initialize_recognizer(self):
        """Inicializar el reconocedor de gestos de MediaPipe."""
        try:
            base_options = python.BaseOptions(model_asset_path=self.model_path)
            
            # Usar LIVE_STREAM como en el original que funciona
            options = vision.GestureRecognizerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.LIVE_STREAM,
                result_callback=self._gesture_result_callback,
                num_hands=1,
                min_hand_detection_confidence=0.7,
                min_hand_presence_confidence=0.7,
                min_tracking_confidence=0.7
            )
            
            self.gesture_recognizer = vision.GestureRecognizer.create_from_options(options)
            
        except Exception as e:
            self.gesture_recognizer = None
    
    def _gesture_result_callback(self, result: vision.GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int):
        """Callback function to handle gesture recognition results."""
        self.current_result = result
        
        if result.gestures:
            for hand_gesture in result.gestures:
                if hand_gesture:
                    gesture = hand_gesture[0]
                    gesture_name = gesture.category_name
                    confidence = gesture.score
                    
                    # Manejar gesto especial para cerrar script (Pointing_Up)
                    if (gesture_name == 'Pointing_Up' and confidence >= self.confidence_threshold):
                        current_time = time.time()
                        
                        if self.close_gesture_start_time is None:
                            self.close_gesture_start_time = current_time
                            self.is_showing_close_progress = True
                        
                        # Verificar si se mantuvo el tiempo suficiente
                        elapsed_time = current_time - self.close_gesture_start_time
                        if elapsed_time >= self.close_gesture_duration:
                            # Cerrar el script
                            self.should_exit = True
                            self.close_gesture_start_time = None
                            self.is_showing_close_progress = False
                    
                    elif (gesture_name in self.gesture_actions and 
                          confidence >= self.confidence_threshold):
                        
                        # Reset del gesto de cerrar si se detecta otro gesto
                        self.close_gesture_start_time = None
                        self.is_showing_close_progress = False
                        
                        current_time = time.time()
                        action = self.gesture_actions[gesture_name]
                        
                        # Verificar delay específico para mute
                        if action == 'toggle_mute':
                            if current_time - self.last_mute_time > self.mute_delay:
                                self.last_gesture = gesture_name
                                self._perform_volume_action(gesture_name, confidence)
                                self.last_mute_time = current_time
                        else:
                            # Para otros gestos (volumen) usar el delay normal
                            if current_time - self.last_action_time > self.action_delay:
                                self.last_gesture = gesture_name
                                self._perform_volume_action(gesture_name, confidence)
                                self.last_action_time = current_time
                    else:
                        # Reset del gesto de cerrar si no se detecta gesto válido
                        self.close_gesture_start_time = None
                        self.is_showing_close_progress = False
        else:
            # Reset del gesto de cerrar si no hay gestos
            self.close_gesture_start_time = None
            self.is_showing_close_progress = False
    
    def _perform_volume_action(self, gesture_name, confidence):
        """Realizar la acción de volumen basada en el gesto detectado."""
        action = self.gesture_actions[gesture_name]
        
        try:
            if action == 'volume_up':
                for _ in range(self.volume_steps):
                    pyautogui.press('volumeup')
                self.action_counts['volume_up'] += 1
                
            elif action == 'volume_down':
                for _ in range(self.volume_steps):
                    pyautogui.press('volumedown')
                self.action_counts['volume_down'] += 1
                
            elif action == 'toggle_mute':
                pyautogui.press('volumemute')
                self.is_muted = not self.is_muted
                if self.is_muted:
                    self.action_counts['mute'] += 1
                else:
                    self.action_counts['unmute'] += 1
        except Exception as e:
            pass
    
    def start_camera(self, camera_id=0):
        """Iniciar la captura de la cámara web."""
        try:
            self.webcam = cv2.VideoCapture(camera_id)
            if not self.webcam.isOpened():
                return False
            
            # Usar la resolución original que funciona bien
            self.webcam.set(cv2.CAP_PROP_FRAME_WIDTH, 480)  # Reducido de 640
            self.webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)  # Reducido de 480
            self.webcam.set(cv2.CAP_PROP_FPS, 30)
            
            return True
        except Exception as e:
            return False
    
    def stop_camera(self):
        """Liberar la cámara web y cerrar ventanas."""
        if self.webcam:
            self.webcam.release()
        cv2.destroyAllWindows()
    
    def process_frame(self):
        """Procesar un frame de la cámara web."""
        if not self.webcam or not self.webcam.isOpened():
            return None
            
        success, image = self.webcam.read()
        if not success:
            return None
            
        # Voltear la imagen horizontalmente para efecto espejo
        image = cv2.flip(image, 1)
        
        return image

    def draw_hand_landmarks(self, image):
        """Dibujar landmarks de la mano con estilo mejorado."""
        if self.current_result and self.current_result.hand_landmarks:
            for hand_landmarks in self.current_result.hand_landmarks:
                # Convertir landmarks normalizados a coordenadas de píxeles
                hand_landmarks_pixel = []
                for landmark in hand_landmarks:
                    x = int(landmark.x * image.shape[1])
                    y = int(landmark.y * image.shape[0])
                    hand_landmarks_pixel.append((x, y))
                
                # Dibujar landmarks individuales con mejor estilo
                for i, point in enumerate(hand_landmarks_pixel):
                    if i == 0:  # Muñeca más grande
                        cv2.circle(image, point, 8, self.landmark_color, -1)
                        cv2.circle(image, point, 10, (255, 255, 255), 2)
                    else:
                        cv2.circle(image, point, 4, self.landmark_color, -1)
                        cv2.circle(image, point, 6, (255, 255, 255), 1)
                
                # Conexiones mejoradas
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
                
                # Dibujar conexiones
                for connection in connections:
                    if (connection[0] < len(hand_landmarks_pixel) and 
                        connection[1] < len(hand_landmarks_pixel)):
                        cv2.line(image, 
                                hand_landmarks_pixel[connection[0]], 
                                hand_landmarks_pixel[connection[1]], 
                                self.connection_color, 3)
    
    def draw_minimal_info(self, image, gesture_name=None, confidence=0.0):
        """Dibujar información mínima en la esquina."""
        # Dibujar instrucciones de gestos
        instructions = [
            "Gestos disponibles:",
            "Pulgar arriba para subir el volumen",
            "Pulgar abajo para bajar el volumen",
            "Mano cerrada para silenciar (delay 2s)",
            "Dedo arriba: Cerrar script (mantener 3s)"
        ]
        
        y_pos = 30
        for instruction in instructions:
            # Borde negro para mejor contraste
            cv2.putText(image, instruction, (10, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            # Texto en color azul verdoso
            cv2.putText(image, instruction, (10, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (86, 185, 157), 1)
            y_pos += 25

        # Mostrar progreso del gesto de cerrar script
        if self.is_showing_close_progress and self.close_gesture_start_time:
            elapsed_time = time.time() - self.close_gesture_start_time
            progress = min(elapsed_time / self.close_gesture_duration, 1.0)
            
            # Barra de progreso
            bar_width = 200
            bar_height = 10
            bar_x = (image.shape[1] - bar_width) // 2
            bar_y = 50
            
            # Fondo de la barra
            cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)
            # Progreso
            progress_width = int(bar_width * progress)
            color = (0, 255, 255) if progress < 1.0 else (0, 255, 0)
            cv2.rectangle(image, (bar_x, bar_y), (bar_x + progress_width, bar_y + bar_height), color, -1)
            
            # Texto de progreso
            progress_text = f"Cerrando script... {progress*100:.0f}%"
            text_size = cv2.getTextSize(progress_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            text_x = (image.shape[1] - text_size[0]) // 2
            text_y = bar_y - 10
            
            cv2.putText(image, progress_text, (text_x, text_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        # Solo mostrar el gesto actual en la esquina superior derecha (si no está en progreso de cerrar)
        if (gesture_name and confidence >= self.confidence_threshold and 
            not self.is_showing_close_progress and gesture_name != 'Pointing_Up'):
            display_name = self.gesture_display_names.get(gesture_name, gesture_name)
            text = f"{display_name}"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            x = image.shape[1] - text_size[0] - 10
            y = 25
            
            # Fondo semitransparente
            cv2.rectangle(image, (x-5, y-20), (x+text_size[0]+5, y+5), (0, 0, 0), -1)
            cv2.putText(image, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.gesture_color, 2)
        
        # Indicador ESC en la esquina inferior izquierda
        cv2.putText(image, "ESC: Salir", (10, image.shape[0] - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
  
    def run(self):
        """Ejecutar el bucle principal del control de volumen."""
        if not self.gesture_recognizer:
            return False
            
        if not self.start_camera():
            return False
        
        try:
            frame_timestamp = 0
            while True:
                # Verificar si se debe salir del script
                if self.should_exit:
                    break
                    
                image = self.process_frame()
                if image is None:
                    break
                
                # Convertir BGR a RGB para MediaPipe
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
                
                # Procesar el frame con el reconocedor de gestos
                if self.gesture_recognizer:
                    frame_timestamp += 33
                    self.gesture_recognizer.recognize_async(mp_image, frame_timestamp)
                
                # Dibujar landmarks
                self.draw_hand_landmarks(image)
                
                # Obtener gesto actual para mostrar
                current_gesture = None
                current_confidence = 0.0
                if self.current_result and self.current_result.gestures:
                    for hand_gesture in self.current_result.gestures:
                        if hand_gesture:
                            gesture = hand_gesture[0]
                            if gesture.category_name in self.gesture_actions:
                                current_gesture = gesture.category_name
                                current_confidence = gesture.score
                                break
                
                # Dibujar información mínima
                self.draw_minimal_info(image, current_gesture, current_confidence)
                
                # Mostrar la imagen
                cv2.imshow('Control de Volumen', image)
                
                # Verificar si se presionó ESC o se cerró la ventana
                key = cv2.waitKey(1) & 0xFF
                if key == 27 or cv2.getWindowProperty('Control de Volumen', cv2.WND_PROP_VISIBLE) < 1:
                    break
                    
        except KeyboardInterrupt:
            pass
        except Exception as e:
            pass
        finally:
            self.stop_camera()
            return True

def main():
    """Funcion principal limpia"""
    try:
        controller = VolumeControllerEnhanced()
        controller.run()
    except Exception as e:
        pass

if __name__ == "__main__":
    main() 