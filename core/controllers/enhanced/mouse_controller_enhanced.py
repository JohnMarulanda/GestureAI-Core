import cv2
import numpy as np
import time
import math
import pyautogui
import autopy
import os
import sys
from pynput.mouse import Button, Controller
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class MouseControllerEnhanced:
    """Controlador mejorado para operaciones de mouse usando gestos de mano derecha."""
    
    def __init__(self, model_path=None):
        """Inicializar el controlador de mouse mejorado."""
        # Buscar el modelo en varias ubicaciones
        if model_path is None:
            # Función auxiliar para obtener el directorio base
            def get_base_path():
                if getattr(sys, 'frozen', False):
                    return sys._MEIPASS
                else:
                    return os.path.dirname(os.path.abspath(__file__))
            
            base_path = get_base_path()
            
            possible_paths = [
                os.path.join(base_path, 'models', 'hand_landmarker.task'),
                os.path.join(base_path, 'hand_landmarker.task'),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'models', 'hand_landmarker.task'),
                os.path.join(os.path.dirname(sys.executable), 'models', 'hand_landmarker.task'),
                os.path.join(os.getcwd(), 'models', 'hand_landmarker.task'),
                'models/hand_landmarker.task',
                'hand_landmarker.task'
            ]
            
            model_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    model_path = path
                    break
            
            if model_path is None:
                print("Error: No se encontró el modelo hand_landmarker.task")
                sys.exit(1)
        
        self.model_path = model_path
        self.hand_landmarker = None
        self.current_result = None
        
        try:
            # Inicializar MediaPipe Tasks HandLandmarker
            base_options = python.BaseOptions(model_asset_path=self.model_path)
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.LIVE_STREAM,
                result_callback=self._hand_result_callback,
                num_hands=1,
                min_hand_detection_confidence=0.7,
                min_hand_presence_confidence=0.7,
                min_tracking_confidence=0.7
            )
            self.hand_landmarker = vision.HandLandmarker.create_from_options(options)
        except Exception as e:
            print(f"Error: No se pudo inicializar MediaPipe HandLandmarker")
            raise
        
        # Configuración de cámara
        self.cap = None
        self.wCam, self.hCam = 480, 360
        
        # Configuración de control
        self.frameR = 5
        self.smoothening = 7
        self.plocX, self.plocY = 0, 0
        self.clocX, self.clocY = 0, 0
        
        # Configuración de gestos
        self.gesture_threshold = 0.8
        self.click_cooldown = 0
        self.drag_active = False
        self.last_gesture = None
        self.gesture_start_time = 0
        self.gesture_hold_time = 0.5
        
        try:
            # Obtener dimensiones de pantalla
            self.screen_width, self.screen_height = pyautogui.size()
            
            # Deshabilitar failsafe de pyautogui
            pyautogui.FAILSAFE = False
            
            # Inicializar controlador de mouse
            self.mouse = Controller()
        except Exception as e:
            print("Error: No se pudo inicializar el controlador del mouse")
            raise
        
        # Colores para visualización
        self.landmark_color = (0, 255, 0)  # Verde
        self.connection_color = (255, 0, 0)  # Azul
        self.gesture_color = (0, 255, 255)  # Amarillo
        self.text_color = (86, 185, 157)  # Azul verdoso
        
        # Mapeo de gestos para mostrar
        self.gesture_display_names = {
            'cursor': 'Mover cursor',
            'left_click': 'Doble clic',
            'right_click': 'Clic derecho',
            'drag': 'Arrastrar'
        }
    
    def _hand_result_callback(self, result: vision.HandLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
        """Callback function to handle hand landmark detection results."""
        self.current_result = result
    
    def start_camera(self, camera_id=0):
        """Iniciar la captura de la cámara."""
        try:
            self.cap = cv2.VideoCapture(camera_id)
            if not self.cap.isOpened():
                return False
            
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.wCam)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.hCam)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Probar captura
            success, frame = self.cap.read()
            if not success:
                return False
                
            return True
        except Exception:
            return False
    
    def stop_camera(self):
        """Detener la cámara y limpiar recursos."""
        try:
            if self.cap:
                self.cap.release()
            cv2.destroyAllWindows()
            if self.hand_landmarker:
                self.hand_landmarker.close()
        except Exception:
            pass
    
    def is_right_hand(self):
        """Determinar si la mano detectada es la mano derecha."""
        if (self.current_result and 
            self.current_result.handedness):
            for handedness in self.current_result.handedness:
                if handedness:
                    if handedness[0].category_name == 'Right':
                        return True
        return False
    
    def get_finger_positions(self, landmarks):
        """Obtener posiciones de los dedos basado en landmarks de MediaPipe para mano derecha."""
        if len(landmarks) < 21:
            return [0, 0, 0, 0, 0]
        
        fingers = []
        
        # Pulgar (para mano derecha: si x del tip < x del pip, está levantado)
        if landmarks[4].x < landmarks[3].x:  # Pulgar derecho levantado
            fingers.append(1)
        else:
            fingers.append(0)

        # Otros dedos (comparar y: si tip está arriba del pip, está levantado)
        finger_tips = [8, 12, 16, 20]  # Índice, medio, anular, meñique
        finger_pips = [6, 10, 14, 18]  # Articulaciones medias
        
        for tip, pip in zip(finger_tips, finger_pips):
            if landmarks[tip].y < landmarks[pip].y:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers
    
    def detect_gesture(self, fingers, landmarks):
        """Detectar el gesto basado en la posición de los dedos."""
        # Convertir a string para comparación fácil
        finger_pattern = ''.join(map(str, fingers))
        
        gestures = {
            '11000': 'cursor',      # Pulgar + índice (mover mouse)
            '11100': 'left_click',  # Pulgar + índice + medio (doble click)
            '11110': 'right_click', # Pulgar + índice + medio + anular (click derecho)
            '01111': 'drag'         # 4 dedos sin pulgar (arrastrar)
        }
        
        detected_gesture = gestures.get(finger_pattern, 'none')
        
        # Confirmar gesto con tiempo de espera
        current_time = time.time()
        if detected_gesture != self.last_gesture:
            self.last_gesture = detected_gesture
            self.gesture_start_time = current_time
            return 'none'  # No confirmar hasta que pase el tiempo
        
        if current_time - self.gesture_start_time > self.gesture_hold_time:
            return detected_gesture
        
        return 'none'
    
    def get_landmark_coords(self, landmarks, index):
        """Obtener coordenadas de un landmark específico."""
        if index < len(landmarks):
            return int(landmarks[index].x * self.wCam), int(landmarks[index].y * self.hCam)
        return 0, 0
    
    def move_cursor(self, landmarks):
        """Mover el cursor basado en la posición del dedo índice."""
        x1, y1 = self.get_landmark_coords(landmarks, 8)  # Punta del índice
        
        # Convertir coordenadas a posición de pantalla
        x = np.interp(x1, [self.frameR, self.wCam - self.frameR], [0, self.screen_width])
        y = np.interp(y1, [self.frameR, self.hCam - self.frameR], [0, self.screen_height])
        
        # Suavizar movimiento
        self.clocX = self.plocX + (x - self.plocX) / self.smoothening
        self.clocY = self.plocY + (y - self.plocY) / self.smoothening
        
        # Mover mouse - usar pyautogui como principal ya que es más confiable en ejecutables
        try:
            # Asegurar que las coordenadas estén dentro de los límites
            final_x = max(0, min(self.screen_width - 1, self.clocX))
            final_y = max(0, min(self.screen_height - 1, self.clocY))
            
            # Usar pyautogui como método principal
            pyautogui.moveTo(final_x, final_y)
            
        except Exception:
            try:
                # Fallback a autopy si pyautogui falla
                autopy.mouse.move(final_x, final_y)
            except:
                pass
        
        self.plocX, self.plocY = self.clocX, self.clocY
        return x1, y1
    
    def handle_left_click(self):
        """Manejar doble click izquierdo."""
        if self.click_cooldown == 0:
            pyautogui.doubleClick()
            self.click_cooldown = 20
            return True
        return False
    
    def handle_right_click(self):
        """Manejar click derecho."""
        if self.click_cooldown == 0:
            self.mouse.click(Button.right)
            self.click_cooldown = 15
            return True
        return False
    
    def handle_drag(self, active):
        """Manejar arrastrar."""
        if active and not self.drag_active:
            self.mouse.press(Button.left)
            self.drag_active = True
        elif not active and self.drag_active:
            self.mouse.release(Button.left)
            self.drag_active = False
    
    def draw_hand_landmarks(self, img, hand_landmarks, is_right_hand=True):
        """Dibujar landmarks de la mano con estilo mejorado."""
        try:
            if is_right_hand:
                # Convertir landmarks normalizados a coordenadas de píxeles
                hand_landmarks_pixel = []
                for landmark in hand_landmarks:
                    x = int(landmark.x * img.shape[1])
                    y = int(landmark.y * img.shape[0])
                    hand_landmarks_pixel.append((x, y))
                
                # Dibujar landmarks individuales con mejor estilo
                for i, point in enumerate(hand_landmarks_pixel):
                    if i == 0:  # Muñeca más grande
                        cv2.circle(img, point, 8, self.landmark_color, -1)
                        cv2.circle(img, point, 10, (255, 255, 255), 2)
                    else:
                        cv2.circle(img, point, 4, self.landmark_color, -1)
                        cv2.circle(img, point, 6, (255, 255, 255), 1)
                
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
                        cv2.line(img, 
                                hand_landmarks_pixel[connection[0]], 
                                hand_landmarks_pixel[connection[1]], 
                                self.connection_color, 3)
            else:
                # Dibujar landmarks en rojo para mano izquierda
                hand_landmarks_pixel = []
                for landmark in hand_landmarks:
                    x = int(landmark.x * img.shape[1])
                    y = int(landmark.y * img.shape[0])
                    hand_landmarks_pixel.append((x, y))
                
                for point in hand_landmarks_pixel:
                    cv2.circle(img, point, 4, (0, 0, 255), -1)
        except Exception:
            pass
    
    def draw_minimal_info(self, image, gesture=None, cursor_pos=None):
        """Dibujar información mínima en la esquina."""
        # Dibujar instrucciones de gestos
        instructions = [
            "Gestos disponibles:",
            "Indice: Mover cursor",
            "Indice + medio: Doble clic izquierdo",
            "Indice + medio + anular: Clic derecho",
            "Palma: Arrastrar"
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

        # Mostrar el gesto actual en la esquina superior derecha
        if gesture and gesture != 'none':
            display_name = self.gesture_display_names.get(gesture, gesture)
            text = f"ACTIVO: {display_name}"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
            x = image.shape[1] - text_size[0] - 10
            y = 30
            
            # Fondo de color para mejor visibilidad
            color = (0, 255, 0) if gesture == 'cursor' else (0, 165, 255)  # Verde para cursor, naranja para clicks
            cv2.rectangle(image, (x-10, y-25), (x+text_size[0]+10, y+10), color, -1)
            cv2.putText(image, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        
        # Mostrar posición del cursor si está disponible
        if cursor_pos:
            cursor_text = f"Cursor: ({int(cursor_pos[0])}, {int(cursor_pos[1])})"
            cv2.putText(image, cursor_text, (10, image.shape[0] - 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # Indicador ESC en la esquina inferior izquierda
        cv2.putText(image, "ESC: Salir", (10, image.shape[0] - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def run(self):
        """Ejecutar el bucle principal del controlador."""
        if not self.hand_landmarker:
            print("Error: HandLandmarker no inicializado")
            return False
        
        if not self.start_camera():
            print("Error: No se pudo inicializar la cámara")
            return False
        
        try:
            frame_count = 0
            frame_timestamp = 0
            while True:
                success, img = self.cap.read()
                if not success:
                    continue
                
                frame_count += 1
                frame_timestamp += 33
                
                # Voltear imagen para efecto espejo
                img = cv2.flip(img, 1)
                
                # Convertir BGR a RGB para MediaPipe
                rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_img)
                
                # Procesar con HandLandmarker
                if self.hand_landmarker:
                    self.hand_landmarker.detect_async(mp_image, frame_timestamp)
                
                gesture = 'none'
                hand_type = "Ninguna"
                cursor_pos = None
                
                if self.current_result and self.current_result.hand_landmarks:
                    for idx, hand_landmarks in enumerate(self.current_result.hand_landmarks):
                        # Verificar si es mano derecha
                        if self.is_right_hand():
                            hand_type = "Derecha"
                            
                            # Dibujar landmarks
                            self.draw_hand_landmarks(img, hand_landmarks, True)
                            
                            # Detectar posición de dedos
                            fingers = self.get_finger_positions(hand_landmarks)
                            gesture = self.detect_gesture(fingers, hand_landmarks)
                            
                            # Ejecutar acciones basadas en el gesto
                            if gesture == 'cursor':
                                x, y = self.move_cursor(hand_landmarks)
                                cursor_pos = (self.clocX, self.clocY)
                                # Dibujar círculo en la posición del dedo índice
                                finger_x, finger_y = self.get_landmark_coords(hand_landmarks, 8)
                                cv2.circle(img, (finger_x, finger_y), 15, (0, 255, 0), 3)
                                cv2.circle(img, (finger_x, finger_y), 5, (0, 255, 0), -1)
                            
                            elif gesture == 'left_click':
                                x, y = self.move_cursor(hand_landmarks)
                                cursor_pos = (self.clocX, self.clocY)
                                self.handle_left_click()
                                # Dibujar círculo azul para click izquierdo
                                finger_x, finger_y = self.get_landmark_coords(hand_landmarks, 8)
                                cv2.circle(img, (finger_x, finger_y), 20, (255, 0, 0), 4)
                                cv2.circle(img, (finger_x, finger_y), 8, (255, 0, 0), -1)
                            
                            elif gesture == 'right_click':
                                x, y = self.move_cursor(hand_landmarks)
                                cursor_pos = (self.clocX, self.clocY)
                                self.handle_right_click()
                                # Dibujar círculo rojo para click derecho
                                finger_x, finger_y = self.get_landmark_coords(hand_landmarks, 8)
                                cv2.circle(img, (finger_x, finger_y), 20, (0, 0, 255), 4)
                                cv2.circle(img, (finger_x, finger_y), 8, (0, 0, 255), -1)
                            
                            elif gesture == 'drag':
                                x, y = self.move_cursor(hand_landmarks)
                                cursor_pos = (self.clocX, self.clocY)
                                self.handle_drag(True)
                                # Dibujar círculo amarillo para arrastrar
                                finger_x, finger_y = self.get_landmark_coords(hand_landmarks, 8)
                                cv2.circle(img, (finger_x, finger_y), 25, (0, 255, 255), 4)
                                cv2.circle(img, (finger_x, finger_y), 10, (0, 255, 255), -1)
                            
                            # Si no hay gesto de arrastrar activo, detener arrastre
                            if gesture != 'drag':
                                self.handle_drag(False)
                        else:
                            hand_type = "Izquierda"
                            # Dibujar landmarks en rojo para mano izquierda
                            self.draw_hand_landmarks(img, hand_landmarks, False)
                
                # Actualizar cooldowns
                if self.click_cooldown > 0:
                    self.click_cooldown -= 1
                
                # Dibujar área de control
                cv2.rectangle(img, (self.frameR, self.frameR), 
                             (self.wCam - self.frameR, self.hCam - self.frameR), 
                             (255, 0, 255), 2)
                cv2.putText(img, "AREA DE CONTROL", (self.frameR + 5, self.frameR - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
                
                # Dibujar información mínima
                self.draw_minimal_info(img, gesture, cursor_pos)
                
                # Mostrar imagen
                cv2.imshow('Control del Mouse', img)
                
                # Verificar si se presionó ESC o se cerró la ventana
                key = cv2.waitKey(1) & 0xFF
                if key == 27 or cv2.getWindowProperty('Control del Mouse', cv2.WND_PROP_VISIBLE) < 1:
                    break
                    
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"Error: {str(e)}")
        finally:
            self.stop_camera()
            return True

def main():
    """Función principal."""
    try:
        controller = MouseControllerEnhanced()
        controller.run()
    except Exception as e:
        print(f"Error crítico: {str(e)}")

if __name__ == "__main__":
    main() 