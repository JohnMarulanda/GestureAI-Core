import cv2
import numpy as np
import time
import os
from core.gesture_detector import GestureDetector

class PaintController(GestureDetector):
    """Controller for virtual painting using hand gestures."""
    
    def __init__(self):
        """Initialize the virtual paint controller."""
        super().__init__()
        
        # Configuraciones y constantes iniciales
        self.ml = 150  # Margen izquierdo para la zona de herramientas
        self.max_x, self.max_y = 250 + self.ml, 50  # Dimensiones máximas de la zona de herramientas
        self.curr_tool = "select tool"  # Herramienta actual seleccionada
        self.time_init = True  # Bandera para inicializar tiempo
        self.rad = 40  # Radio para selección de herramienta
        self.var_inits = False  # Bandera para inicializar variables de dibujo
        self.thick = 4  # Grosor de las líneas de dibujo
        self.prevx, self.prevy = 0, 0  # Coordenadas previas para dibujar
        self.xii, self.yii = 0, 0  # Coordenadas iniciales para formas
        
        # Cargar imagen de herramientas
        tools_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                 "core", "ui", "images", "tools.png")
        self.tools = cv2.imread(tools_path)
        if self.tools is None:
            print(f"Warning: Could not load tools image from {tools_path}")
            # Create a placeholder image
            self.tools = np.ones((50, 250, 3), dtype=np.uint8) * 255
            # Add text for each tool
            cv2.putText(self.tools, "Line", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
            cv2.putText(self.tools, "Rect", (60, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
            cv2.putText(self.tools, "Draw", (110, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
            cv2.putText(self.tools, "Circle", (160, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
            cv2.putText(self.tools, "Erase", (210, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        self.tools = self.tools.astype('uint8')
        
        # Crear máscara en blanco para dibujar
        self.mask = np.ones((480, 640)) * 255
        self.mask = self.mask.astype('uint8')
        
        print("Virtual Paint Controller initialized")
        print("Press 'ESC' to quit")
    
    def get_tool(self, x):
        """Determinar la herramienta seleccionada según la posición x"""
        if x < 50 + self.ml:
            return "line"
        elif x < 100 + self.ml:
            return "rectangle"
        elif x < 150 + self.ml:
            return "draw"
        elif x < 200 + self.ml:
            return "circle"
        else:
            return "erase"
    
    def index_raised(self, yi, y9):
        """Detectar si el dedo índice está levantado"""
        if (y9 - yi) > 40:
            return True
        return False
    
    def display_instructions(self, frame):
        """Display the list of available gestures and their functions"""
        instructions = [
            "VIRTUAL PAINT GESTURES:",
            "Move index finger to toolbar and hold to select tool",
            "Raise middle finger to draw/preview",
            "Lower middle finger to confirm drawing"
        ]
        
        y_pos = 70
        for instruction in instructions:
            cv2.putText(frame, instruction, (10, y_pos), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_pos += 25
    
    def run(self):
        """Main loop to capture video and process hand gestures for painting."""
        if not self.start_camera():
            print("Failed to open webcam")
            return
        
        try:
            while True:
                # Get the frame
                success, frame = self.cap.read()
                if not success:
                    print("Failed to capture image from camera.")
                    break
                
                # Flip the frame horizontally for a more intuitive mirror view
                frame = cv2.flip(frame, 1)
                
                # Convert the BGR image to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Process the frame with MediaPipe
                results = self.hands.process(rgb_frame)
                
                # Display instructions
                self.display_instructions(frame)
                
                # If hands are detected
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        # Draw hand landmarks
                        self.drawing_utils.draw_landmarks(
                            frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                        
                        # Obtener coordenadas de la punta del dedo índice
                        x, y = int(hand_landmarks.landmark[8].x * 640), int(hand_landmarks.landmark[8].y * 480)
                        
                        # Si el dedo está en la zona de herramientas
                        if x < self.max_x and y < self.max_y and x > self.ml:
                            if self.time_init:
                                # Iniciar conteo de tiempo para selección de herramienta
                                ctime = time.time()
                                self.time_init = False
                            ptime = time.time()
                            
                            # Dibujar círculo de selección
                            cv2.circle(frame, (x, y), self.rad, (0, 255, 255), 2)
                            self.rad -= 1
                            
                            # Si se mantiene presionado más de 0.8 segundos
                            if (ptime - ctime) > 0.8:
                                # Seleccionar herramienta
                                self.curr_tool = self.get_tool(x)
                                print("your current tool set to : ", self.curr_tool)
                                self.time_init = True
                                self.rad = 40
                        
                        else:
                            self.time_init = True
                            self.rad = 40
                        
                        # Lógica para cada herramienta
                        if self.curr_tool == "draw":
                            # Obtener coordenadas de otro punto de la mano
                            xi, yi = int(hand_landmarks.landmark[12].x * 640), int(hand_landmarks.landmark[12].y * 480)
                            y9 = int(hand_landmarks.landmark[9].y * 480)
                            
                            # Si el dedo índice está levantado, dibujar línea
                            if self.index_raised(yi, y9):
                                cv2.line(self.mask, (self.prevx, self.prevy), (x, y), 0, self.thick)
                                self.prevx, self.prevy = x, y
                            
                            else:
                                self.prevx = x
                                self.prevy = y
                        
                        elif self.curr_tool == "line":
                            # Similar a "draw" pero dibuja línea en el frame
                            xi, yi = int(hand_landmarks.landmark[12].x * 640), int(hand_landmarks.landmark[12].y * 480)
                            y9 = int(hand_landmarks.landmark[9].y * 480)
                            
                            if self.index_raised(yi, y9):
                                if not (self.var_inits):
                                    self.xii, self.yii = x, y
                                    self.var_inits = True
                                
                                cv2.line(frame, (self.xii, self.yii), (x, y), (50, 152, 255), self.thick)
                            
                            else:
                                if self.var_inits:
                                    cv2.line(self.mask, (self.xii, self.yii), (x, y), 0, self.thick)
                                    self.var_inits = False
                        
                        elif self.curr_tool == "rectangle":
                            # Dibujar rectángulo con coordenadas inicial y final
                            xi, yi = int(hand_landmarks.landmark[12].x * 640), int(hand_landmarks.landmark[12].y * 480)
                            y9 = int(hand_landmarks.landmark[9].y * 480)
                            
                            if self.index_raised(yi, y9):
                                if not (self.var_inits):
                                    self.xii, self.yii = x, y
                                    self.var_inits = True
                                
                                cv2.rectangle(frame, (self.xii, self.yii), (x, y), (0, 255, 255), self.thick)
                            
                            else:
                                if self.var_inits:
                                    cv2.rectangle(self.mask, (self.xii, self.yii), (x, y), 0, self.thick)
                                    self.var_inits = False
                        
                        elif self.curr_tool == "circle":
                            # Dibujar círculo usando distancia entre puntos
                            xi, yi = int(hand_landmarks.landmark[12].x * 640), int(hand_landmarks.landmark[12].y * 480)
                            y9 = int(hand_landmarks.landmark[9].y * 480)
                            
                            if self.index_raised(yi, y9):
                                if not (self.var_inits):
                                    self.xii, self.yii = x, y
                                    self.var_inits = True
                                
                                radius = int(((self.xii - x) ** 2 + (self.yii - y) ** 2) ** 0.5)
                                cv2.circle(frame, (self.xii, self.yii), radius, (255, 255, 0), self.thick)
                            
                            else:
                                if self.var_inits:
                                    radius = int(((self.xii - x) ** 2 + (self.yii - y) ** 2) ** 0.5)
                                    cv2.circle(self.mask, (self.xii, self.yii), radius, 0, self.thick)
                                    self.var_inits = False
                        
                        elif self.curr_tool == "erase":
                            # Herramienta de borrado
                            xi, yi = int(hand_landmarks.landmark[12].x * 640), int(hand_landmarks.landmark[12].y * 480)
                            y9 = int(hand_landmarks.landmark[9].y * 480)
                            
                            if self.index_raised(yi, y9):
                                # Dibujar círculo negro para borrar
                                cv2.circle(frame, (x, y), 30, (0, 0, 0), -1)
                                cv2.circle(self.mask, (x, y), 30, 255, -1)
                
                # Aplicar máscara al frame
                op = cv2.bitwise_and(frame, frame, mask=self.mask)
                frame[:, :, 1] = op[:, :, 1]
                frame[:, :, 2] = op[:, :, 2]
                
                # Superponer imagen de herramientas
                frame[:self.max_y, self.ml:self.max_x] = cv2.addWeighted(
                    self.tools, 0.7, frame[:self.max_y, self.ml:self.max_x], 0.3, 0)
                
                # Mostrar herramienta actual
                cv2.putText(frame, self.curr_tool, (270 + self.ml, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                # Display the frame
                cv2.imshow('Virtual Paint with Hand Gestures', frame)
                
                # Exit on 'ESC' key press
                if cv2.waitKey(5) & 0xFF == 27:
                    break
        
        finally:
            self.stop_camera()