import cv2
import numpy as np
import time
import math
import pyautogui
import autopy
from pynput.mouse import Button, Controller
# Importaciones de control de volumen removidas (no necesarias)
import mediapipe as mp

# Initialize mouse controller
mouse = Controller()

# Get screen dimensions
screen_width, screen_height = pyautogui.size()

# Disable pyautogui failsafe
pyautogui.FAILSAFE = False

class ImprovedMouseController:
    """Controlador mejorado para operaciones de mouse usando gestos de mano derecha."""
    
    def __init__(self):
        """Inicializar el controlador de mouse mejorado."""
        
        # MediaPipe setup - configurado para detectar solo mano derecha
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,  # Solo una mano para mejor rendimiento
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
            model_complexity=1
        )
        self.drawing_utils = mp.solutions.drawing_utils
        self.drawing_styles = mp.solutions.drawing_styles
        
        # Camera setup
        self.cap = None
        self.wCam, self.hCam = 640, 480
        
        # Configuración simplificada sin control de volumen
        
        # Control settings
        self.frameR = 100  # Frame Reduction para área de control
        self.smoothening = 7  # Suavizado del movimiento del mouse
        self.plocX, self.plocY = 0, 0  # Posición anterior
        self.clocX, self.clocY = 0, 0  # Posición actual
        
        # Gesture detection settings
        self.gesture_threshold = 0.8  # Umbral de confianza para gestos
        self.click_cooldown = 0
        self.drag_active = False
        self.last_gesture = None
        self.gesture_start_time = 0
        self.gesture_hold_time = 0.5  # Tiempo para confirmar gesto
        
        # FPS tracking
        self.pTime = 0
        
        print("✅ Controlador de Mouse Mejorado inicializado (Mano Derecha)")
        print("📋 Gestos disponibles:")
        print("   👆 Dedo índice: Mover cursor")
        print("   ✌️ Índice + Medio: Doble click")
        print("   🤟 Índice + Medio + Anular: Click derecho")
        print("   👍 Pulgar arriba: Arrastrar")
        print("   Presiona 'q' para salir")
    
    def start_camera(self, camera_id=0):
        """Iniciar la captura de la cámara."""
        try:
            self.cap = cv2.VideoCapture(camera_id)
            if not self.cap.isOpened():
                return False
            
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.wCam)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.hCam)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            return True
        except Exception as e:
            print(f"❌ Error al iniciar cámara: {e}")
            return False
    
    def stop_camera(self):
        """Detener la cámara y limpiar recursos."""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        if self.hands:
            self.hands.close()
    
    def is_right_hand(self, hand_landmarks, results):
        """Determinar si la mano detectada es la mano derecha."""
        if results.multi_handedness:
            for hand_handedness in results.multi_handedness:
                # MediaPipe devuelve 'Right' para mano derecha en imagen espejo
                if hand_handedness.classification[0].label == 'Right':
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
            '01000': 'cursor',      # Solo índice
            '01100': 'double_click', # Índice + medio (doble click)
            '01110': 'right_click', # Índice + medio + anular
            '10000': 'drag'         # Solo pulgar
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
        x = np.interp(x1, [self.frameR, self.wCam - self.frameR], [0, screen_width])
        y = np.interp(y1, [self.frameR, self.hCam - self.frameR], [0, screen_height])
        
        # Suavizar movimiento
        self.clocX = self.plocX + (x - self.plocX) / self.smoothening
        self.clocY = self.plocY + (y - self.plocY) / self.smoothening
        
        # Mover mouse
        try:
            # Asegurar que las coordenadas estén dentro de los límites
            final_x = max(0, min(screen_width - 1, self.clocX))
            final_y = max(0, min(screen_height - 1, self.clocY))
            autopy.mouse.move(final_x, final_y)
        except:
            # Fallback a pyautogui
            pyautogui.moveTo(max(0, min(screen_width - 1, self.clocX)), 
                           max(0, min(screen_height - 1, self.clocY)))
        
        self.plocX, self.plocY = self.clocX, self.clocY
        return x1, y1
    
    def handle_double_click(self):
        """Manejar doble click."""
        if self.click_cooldown == 0:
            # Usar pyautogui para doble click más confiable
            pyautogui.doubleClick()
            self.click_cooldown = 20  # Cooldown más largo para doble click
            return True
        return False
    
    def handle_right_click(self):
        """Manejar click derecho."""
        if self.click_cooldown == 0:
            mouse.click(Button.right)
            self.click_cooldown = 15
            return True
        return False
    
    def handle_drag(self, active):
        """Manejar arrastrar."""
        if active and not self.drag_active:
            mouse.press(Button.left)
            self.drag_active = True
        elif not active and self.drag_active:
            mouse.release(Button.left)
            self.drag_active = False
    

    

    
    def draw_ui(self, img, gesture, hand_type="", landmarks=None):
        """Dibujar interfaz de usuario."""
        h, w, _ = img.shape
        
        # Área de control del cursor
        cv2.rectangle(img, (self.frameR, self.frameR), 
                     (w - self.frameR, h - self.frameR), (255, 255, 255), 2)
        
        # Información del gesto actual y tipo de mano
        cv2.putText(img, f'Mano: {hand_type}', (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        cv2.putText(img, f'Gesto: {gesture}', (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # FPS
        cTime = time.time()
        fps = 1 / (cTime - self.pTime + 0.001)
        self.pTime = cTime
        cv2.putText(img, f'FPS: {int(fps)}', (w - 120, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        
        # Instrucciones
        instructions = [
            "👆 Indice: Cursor",
            "✌️ Indice+Medio: Doble click",
            "🤟 3 dedos: Click derecho",
            "👍 Pulgar: Arrastrar"
        ]
        
        for i, instruction in enumerate(instructions):
            cv2.putText(img, instruction, (10, h - 150 + i * 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    
    def run(self):
        """Bucle principal del controlador."""
        if not self.start_camera():
            print("❌ No se pudo iniciar la cámara")
            return
        
        print("🚀 Iniciando controlador de mouse con gestos...")
        print("   Muestra tu MANO DERECHA frente a la cámara")
        
        try:
            while True:
                success, img = self.cap.read()
                if not success:
                    continue
                
                # Voltear imagen para efecto espejo
                img = cv2.flip(img, 1)
                h, w, _ = img.shape
                
                # Procesar con MediaPipe
                rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                results = self.hands.process(rgb_img)
                
                gesture = 'none'
                hand_type = "Ninguna"
                
                if results.multi_hand_landmarks:
                    for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                        # Verificar si es mano derecha
                        if self.is_right_hand(hand_landmarks, results):
                            hand_type = "Derecha ✅"
                            
                            # Dibujar landmarks
                            self.drawing_utils.draw_landmarks(
                                img, hand_landmarks, self.mp_hands.HAND_CONNECTIONS,
                                self.drawing_styles.get_default_hand_landmarks_style(),
                                self.drawing_styles.get_default_hand_connections_style()
                            )
                            
                            # Detectar posición de dedos
                            fingers = self.get_finger_positions(hand_landmarks.landmark)
                            gesture = self.detect_gesture(fingers, hand_landmarks.landmark)
                            
                            # Ejecutar acciones basadas en el gesto
                            if gesture == 'cursor':
                                x, y = self.move_cursor(hand_landmarks.landmark)
                                cv2.circle(img, (x, y), 8, (0, 255, 0), -1)
                            
                            elif gesture == 'double_click':
                                x, y = self.move_cursor(hand_landmarks.landmark)
                                if self.handle_double_click():
                                    cv2.circle(img, (x, y), 15, (0, 255, 0), -1)
                                    # Mostrar indicador de doble click
                                    cv2.putText(img, "DOBLE CLICK", (x - 50, y - 30), 
                                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                            
                            elif gesture == 'right_click':
                                x, y = self.move_cursor(hand_landmarks.landmark)
                                if self.handle_right_click():
                                    cv2.circle(img, (x, y), 15, (0, 0, 255), -1)
                            
                            elif gesture == 'drag':
                                x, y = self.move_cursor(hand_landmarks.landmark)
                                self.handle_drag(True)
                                cv2.circle(img, (x, y), 12, (255, 0, 255), -1)
                            

                            

                            
                            # Si no hay gesto de arrastrar activo, detener arrastre
                            if gesture != 'drag':
                                self.handle_drag(False)
                        else:
                            hand_type = "Izquierda ❌"
                            # Dibujar landmarks en rojo para mano izquierda
                            self.drawing_utils.draw_landmarks(
                                img, hand_landmarks, self.mp_hands.HAND_CONNECTIONS,
                                landmark_drawing_spec=mp.solutions.drawing_utils.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2),
                                connection_drawing_spec=mp.solutions.drawing_utils.DrawingSpec(color=(0, 0, 255), thickness=2)
                            )
                
                # Actualizar cooldowns
                if self.click_cooldown > 0:
                    self.click_cooldown -= 1
                
                # Dibujar UI
                self.draw_ui(img, gesture, hand_type)
                
                # Mostrar imagen
                cv2.imshow('Control de Mouse con Gestos - Mano Derecha', img)
                
                # Salir con 'q'
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        except KeyboardInterrupt:
            print("\n⚠️ Interrupción detectada")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            self.stop_camera()
            print("👋 Controlador finalizado")


def main():
    """Función principal."""
    controller = ImprovedMouseController()
    controller.run()


if __name__ == "__main__":
    main()