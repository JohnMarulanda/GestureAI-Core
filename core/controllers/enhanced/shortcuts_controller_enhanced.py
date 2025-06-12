import cv2
import pyautogui
import time
import threading
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import os
import sys

class ShortcutsControllerEnhanced:
    """Controlador mejorado para ejecutar atajos de teclado usando gestos predefinidos de MediaPipe."""
    
    def __init__(self, model_path=None):
        """Inicializar el controlador de atajos con reconocimiento de gestos."""
        # Buscar el modelo en varias ubicaciones como en los otros controladores
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
        
        # Temporizacion de gestos y retrasos
        self.last_action_time = 0
        self.action_delay = 0.8
        
        # Estado actual del gesto
        self.last_gesture = None
        self.current_result = None
        self.confidence_threshold = 0.70
        
        # Variables para el gesto de cerrar script (Pointing_Up)
        self.close_gesture_start_time = None
        self.close_gesture_duration = 3.0  # 3 segundos para cerrar script
        self.is_showing_close_progress = False
        self.should_exit = False
        
        # Mapeo de gestos para atajos de teclado usando gestos predefinidos
        # Cambiar Pointing_Up a otro gesto ya que Pointing_Up se usa para cerrar
        self.gesture_actions = {
            'Victory': 'copiar',
            'Open_Palm': 'pegar',
            'Closed_Fist': 'escape',
            'Thumb_Up': 'deshacer',
            'Thumb_Down': 'rehacer',
            'ILoveYou': 'guardar'
        }
        
        # Mapeo de nombres de gestos para mostrar
        self.gesture_display_names = {
            'Victory': 'Copiar',
            'Open_Palm': 'Pegar', 
            'Closed_Fist': 'Escape',
            'Thumb_Up': 'Deshacer',
            'Thumb_Down': 'Rehacer',
            'ILoveYou': 'Guardar'
        }
        
        # Mapeo de atajos de teclado
        self.shortcuts = {
            'copiar': ['ctrl', 'c'],
            'pegar': ['ctrl', 'v'],
            'escape': ['esc'],
            'deshacer': ['ctrl', 'z'],
            'rehacer': ['ctrl', 'y'],
            'guardar': ['ctrl', 's']
        }
        
        # Seguridad de hilos
        self.shortcut_lock = threading.Lock()
        
        # Configuracion de ventana
        self.window_width = 480
        self.window_height = 360
        
        # Colores para landmarks mejorados (consistente con otros controladores)
        self.landmark_color = (0, 255, 0)  # Verde
        self.connection_color = (255, 0, 0)  # Azul
        self.gesture_color = (0, 255, 255)  # Amarillo
        
        # Deshabilitar failsafe de pyautogui
        pyautogui.FAILSAFE = False
        
        self._initialize_recognizer()
    
    def _initialize_recognizer(self):
        """Inicializar el MediaPipe Gesture Recognizer."""
        try:
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
        """Funcion de callback para manejar resultados del reconocimiento de gestos."""
        try:
            self.current_result = result
            
            if result.gestures and result.hand_landmarks:
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
                        
                        # Manejar gestos de atajos de teclado
                        elif (gesture_name in self.gesture_actions and 
                              confidence >= self.confidence_threshold):
                            
                            # Reset del gesto de cerrar si se detecta otro gesto
                            self.close_gesture_start_time = None
                            self.is_showing_close_progress = False
                            
                            self.last_gesture = gesture_name
                            
                            # Verificar si ha pasado suficiente tiempo desde la ultima accion
                            current_time = time.time()
                            if current_time - self.last_action_time > self.action_delay:
                                threading.Thread(
                                    target=self._perform_shortcut_action,
                                    args=(gesture_name, confidence),
                                    daemon=True
                                ).start()
                                self.last_action_time = current_time
                        else:
                            # Reset del gesto de cerrar si no se detecta gesto valido
                            self.close_gesture_start_time = None
                            self.is_showing_close_progress = False
            else:
                # Reset del gesto de cerrar si no hay gestos
                self.close_gesture_start_time = None
                self.is_showing_close_progress = False
                
        except Exception as e:
            pass
    
    def _perform_shortcut_action(self, gesture_name, confidence):
        """Ejecutar la accion de atajo de teclado basada en el gesto detectado."""
        with self.shortcut_lock:
            try:
                action = self.gesture_actions[gesture_name]
                keys = self.shortcuts[action]
                
                # Ejecutar el atajo de teclado
                pyautogui.hotkey(*keys)
                    
            except Exception as e:
                pass
    
    def start_camera(self, camera_id=0):
        """Iniciar la captura de la camara."""
        try:
            self.webcam = cv2.VideoCapture(camera_id)
            if not self.webcam.isOpened():
                return False
            
            # Configurar propiedades de la camara (resolucion consistente)
            self.webcam.set(cv2.CAP_PROP_FRAME_WIDTH, self.window_width)
            self.webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, self.window_height)
            self.webcam.set(cv2.CAP_PROP_FPS, 30)
            self.webcam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            return True
        except Exception as e:
            return False
    
    def stop_camera(self):
        """Detener la camara y limpiar recursos."""
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
        """Dibujar landmarks de la mano con estilo mejorado (consistente con otros controladores)."""
        try:
            if self.current_result and self.current_result.hand_landmarks:
                for hand_landmarks in self.current_result.hand_landmarks:
                    # Convertir landmarks normalizados a coordenadas de pixeles
                    hand_landmarks_pixel = []
                    for landmark in hand_landmarks:
                        x = int(landmark.x * image.shape[1])
                        y = int(landmark.y * image.shape[0])
                        hand_landmarks_pixel.append((x, y))
                    
                    # Dibujar landmarks individuales con mejor estilo
                    for i, point in enumerate(hand_landmarks_pixel):
                        if i == 0:  # Muneca mas grande
                            cv2.circle(image, point, 8, self.landmark_color, -1)
                            cv2.circle(image, point, 10, (255, 255, 255), 2)
                        else:
                            cv2.circle(image, point, 4, self.landmark_color, -1)
                            cv2.circle(image, point, 6, (255, 255, 255), 1)
                    
                    # Conexiones mejoradas
                    connections = [
                        # Pulgar
                        (0, 1), (1, 2), (2, 3), (3, 4),
                        # Indice
                        (0, 5), (5, 6), (6, 7), (7, 8),
                        # Medio
                        (0, 9), (9, 10), (10, 11), (11, 12),
                        # Anular
                        (0, 13), (13, 14), (14, 15), (15, 16),
                        # Menique
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
        except Exception as e:
            pass
    
    def draw_minimal_info(self, image, gesture_name=None, confidence=0.0):
        """Dibujar informacion minima en la imagen."""
        # Dibujar instrucciones de gestos
        instructions = [
            "Gestos disponibles:",
            "Victoria: Copiar",
            "Mano abierta: Pegar",
            "Puno: Escape",
            "Pulgar arriba: Deshacer",
            "Pulgar abajo: Rehacer",
            "Te amo: Guardar",
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

        # Solo mostrar el gesto actual en la esquina superior derecha (para gestos normales)
        if (gesture_name and confidence >= self.confidence_threshold and 
            gesture_name != 'Pointing_Up' and not self.is_showing_close_progress):
            display_name = self.gesture_display_names.get(gesture_name, gesture_name)
            text = f"{display_name}"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            x = image.shape[1] - text_size[0] - 10
            y = 25
            
            # Fondo semitransparente
            cv2.rectangle(image, (x-5, y-20), (x+text_size[0]+5, y+5), (0, 0, 0), -1)
            cv2.putText(image, text, (x, y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.gesture_color, 2)
        
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
            while True:
                # Verificar si se debe salir del script
                if self.should_exit:
                    break
                    
                image = self.process_frame()
                if image is None:
                    continue
                
                # Procesar con MediaPipe
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
                
                # Procesar el frame con el reconocedor de gestos
                if self.gesture_recognizer:
                    frame_timestamp += 33
                    try:
                        self.gesture_recognizer.recognize_async(mp_image, frame_timestamp)
                    except Exception as e:
                        pass
                
                # Dibujar landmarks de la mano
                self.draw_hand_landmarks(image)
                
                # Obtener gesto actual para mostrar
                current_gesture = None
                current_confidence = 0.0
                if self.current_result and self.current_result.gestures:
                    for hand_gesture in self.current_result.gestures:
                        if hand_gesture:
                            gesture = hand_gesture[0]
                            # Para gestos normales de atajos
                            if gesture.category_name in self.gesture_actions:
                                current_gesture = gesture.category_name
                                current_confidence = gesture.score
                                break
                            # Para el gesto especial de cerrar (Pointing_Up)
                            elif gesture.category_name == 'Pointing_Up' and gesture.score >= self.confidence_threshold:
                                current_gesture = gesture.category_name
                                current_confidence = gesture.score
                                break
                
                # Dibujar informacion minima
                self.draw_minimal_info(image, current_gesture, current_confidence)
                
                # Mostrar imagen
                cv2.imshow('Control de Atajos', image)
                
                # Salir con ESC o al cerrar la ventana
                key = cv2.waitKey(1) & 0xFF
                if key == 27 or cv2.getWindowProperty('Control de Atajos', cv2.WND_PROP_VISIBLE) < 1:
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
        controller = ShortcutsControllerEnhanced()
        controller.run()
    except Exception as e:
        pass

if __name__ == "__main__":
    main() 