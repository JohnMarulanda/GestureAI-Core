import tkinter as tk
from tkinter import ttk, PhotoImage
from tkinter.font import Font
import sys
import os
import json
import cv2
import time
from core.gesture_detector import GestureDetector
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

class MainWindow(GestureDetector):
    def __init__(self):
        super().__init__()
        
        # Gesture tracking variables
        self.current_gesture = None
        self.gesture_start_time = 0
        self.gesture_duration = 0
        self.required_duration = 2.0  # Seconds to hold gesture before action
        
        # Load gesture mappings
        self.config_file = os.path.join(os.path.dirname(__file__), "config", "gesture_mappings.json")
        self.load_gesture_config()
        self.root = tk.Tk()
        self.root.title("GestureAI Control Panel")
        
        # Obtener ancho de pantalla
        screen_width = self.root.winfo_screenwidth()
        
        # Definir dimensiones fijas
        window_width = 160
        window_height = 650
        x_position = screen_width - window_width  # Alineado al lado derecho
        y_position = 0  # Desde arriba

        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        
        # Configurar estilo
        self.style = ttk.Style()
        self.style.configure("Controller.TButton", padding=5, font=('Helvetica', 11, 'bold'), background='#3498DB', foreground='#4F8BB3')
        self.style.map('Controller.TButton',
                      background=[('active', '#2980B9')],
                      foreground=[('active', '#4F8BB3')])
        
        # Configurar colores
        self.root.configure(bg='#ECF0F1')
        self.style.configure("TFrame", background='#ECF0F1')
        
        # Lista de todos los controladores
        self.all_controllers = [
            ("Control de Volumen", VolumeController, "Controla el volumen del sistema con gestos"),
            ("Control de Brillo", BrightnessController, "Ajusta el brillo de la pantalla"),
            ("Control de Aplicaciones", AppController, "Abre y cierra aplicaciones con gestos"),
            ("Atajos de Teclado", ShortcutsController, "Ejecuta atajos de teclado"),
            ("Teclado Virtual", KeyboardController, "Teclado virtual controlado por gestos"),
            ("Navegación", NavigationController, "Navega por el sistema"),
            ("Control del Sistema", SystemController, "Controla funciones del sistema"),
            ("Control Multimedia", MultimediaController, "Controla la reproducción multimedia"),
            ("Control de Zoom", ZoomController, "Controla el zoom de imágenes"),
            ("Modo Pintura", PaintController, "Dibuja con gestos"),
            ("Control del Mouse", MouseController, "Controla el cursor con gestos")
        ]
        
        self.current_group = 0
        self.active_controller = None
        self.create_widgets()

    def create_widgets(self):
        # Frame principal con padding y color de fondo
        main_frame = ttk.Frame(self.root, padding="5", style="TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título con mejor formato
        # title_frame = ttk.Frame(main_frame, style="TFrame")
        # title_frame.pack(pady=20)
        
        # title_label = ttk.Label(title_frame, 
        #                       text="GestureAI Control Panel",
        #                       style="Title.TLabel")
        # title_label.pack()
        
        # subtitle_label = ttk.Label(title_frame,
        #                          text="Control por gestos intuitivo y eficiente",
        #                          font=('Helvetica', 12),
        #                          foreground='#7F8C8D')
        # subtitle_label.pack(pady=5)
        
        # Frame para los botones de control
        self.buttons_frame = ttk.Frame(main_frame, style="TFrame")
        self.buttons_frame.pack(fill=tk.X, pady=(10, 5), side=tk.TOP)
        
        # Mostrar los primeros 5 controladores y el botón 'Otros'
        self.update_controller_buttons()
        
        # Botón para cerrar con mejor diseño
        quit_frame = ttk.Frame(main_frame, style="TFrame")
        quit_frame.pack(side=tk.TOP, pady=(5, 10))
        
        quit_btn = ttk.Button(quit_frame,
                            text="Cerrar Aplicación",
                            style="Controller.TButton",
                            command=self.root.quit)
        quit_btn.pack()

    def update_controller_buttons(self):
        # Limpiar botones existentes
        for widget in self.buttons_frame.winfo_children():
            widget.destroy()
        
        # Calcular el índice inicial para el grupo actual
        start_idx = self.current_group * 5
        
        # Calcular el alto disponible para los botones
        available_height = 600  # Altura total menos márgenes
        button_height = available_height // 6  # 5 botones de control + 1 botón 'Otros'
        
        # Mostrar 5 controladores del grupo actual
        for i in range(5):
            idx = (start_idx + i) % len(self.all_controllers)
            name, controller, _ = self.all_controllers[idx]
            
            # Botón con mejor estilo y tamaño proporcional
            btn = ttk.Button(self.buttons_frame, 
                           text=name,
                           style="Controller.TButton",
                           command=lambda c=controller: self.start_controller(c))
            btn.pack(fill=tk.X, pady=2, ipady=button_height//4)
        
        # Botón 'Otros' para cambiar al siguiente grupo
        others_btn = ttk.Button(self.buttons_frame,
                               text="Otros Controles",
                               style="Controller.TButton",
                               command=self.next_controller_group)
        others_btn.pack(fill=tk.X, pady=2, ipady=button_height//4)

    def next_controller_group(self):
        # Cambiar al siguiente grupo de controladores
        total_groups = (len(self.all_controllers) + 4) // 5  # Redondear hacia arriba
        self.current_group = (self.current_group + 1) % total_groups
        self.update_controller_buttons()
    
    def start_controller(self, controller_class):
        # Detener el controlador actual si existe
        if self.active_controller:
            self.active_controller.stop_camera()
        
        # Crear y ejecutar el nuevo controlador
        try:
            self.active_controller = controller_class()
            self.active_controller.run()
        except Exception as e:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Error", f"Error al iniciar el controlador: {str(e)}")
    
    def load_gesture_config(self):
        """Load gesture mappings from config file"""
        try:
            with open(self.config_file, 'r') as f:
                self.gesture_config = json.load(f)
        except Exception as e:
            print(f"Error loading gesture config: {e}")
            self.gesture_config = {"button_gestures": {}}
    
    def detect_gesture(self, hand_landmarks):
        """Detect finger positions and return as a list of 0s and 1s"""
        fingertips = [4, 8, 12, 16, 20]  # Thumb, index, middle, ring, pinky
        finger_states = []
        
        for tip_id in fingertips:
            if tip_id == 4:
                if hand_landmarks.landmark[tip_id].x < hand_landmarks.landmark[tip_id - 2].x:
                    finger_states.append(1)
                else:
                    finger_states.append(0)
            else:
                if hand_landmarks.landmark[tip_id].y < hand_landmarks.landmark[tip_id - 2].y:
                    finger_states.append(1)
                else:
                    finger_states.append(0)
        
        return finger_states
    
    def identify_button(self, finger_states):
        """Identify which button to activate based on the detected gesture"""
        for button_name, gesture in self.gesture_config["button_gestures"].items():
            if finger_states == gesture:
                button_index = int(button_name.replace("button", "")) - 1
                return button_index
        return None
    
    def process_gestures(self):
        """Process gestures and activate corresponding buttons"""
        image, results = self.process_frame()
        if image is None:
            return False
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                finger_states = self.detect_gesture(hand_landmarks)
                
                # Verificar gestos de cierre
                if finger_states == self.gesture_config["button_gestures"]["quit_app"]:
                    return False
                elif finger_states == self.gesture_config["button_gestures"]["quit_controller"]:
                    if self.active_controller:
                        self.active_controller.stop_camera()
                        self.active_controller = None
                        return True
                
                button_index = self.identify_button(finger_states)
                
                if button_index is not None:
                    current_time = time.time()
                    if button_index == self.current_gesture:
                        self.gesture_duration = current_time - self.gesture_start_time
                        if self.gesture_duration >= self.required_duration:
                            # Calculate the actual button index based on current group
                            actual_index = button_index + (self.current_group * 5)
                            if actual_index < len(self.all_controllers):
                                if button_index == 5:  # Botón "Otros"
                                    self.next_controller_group()
                                else:
                                    name, controller, _ = self.all_controllers[actual_index]
                                    self.start_controller(controller)
                            self.current_gesture = None
                            self.gesture_duration = 0
                    else:
                        self.current_gesture = button_index
                        self.gesture_start_time = current_time
                        self.gesture_duration = 0
                else:
                    self.current_gesture = None
                    self.gesture_duration = 0
        else:
            self.current_gesture = None
            self.gesture_duration = 0
        
        cv2.imshow('Gesture Control', image)
        return True
    
    def run(self):
        """Main loop for the application"""
        if not self.start_camera():
            print("Failed to open webcam")
            return
        
        try:
            while True:
                self.root.update()
                
                if not self.process_gestures():
                    break
                
                if cv2.waitKey(5) & 0xFF == ord('z'):
                    break
        
        finally:
            self.stop_camera()
            cv2.destroyAllWindows()
            self.root.quit()

if __name__ == "__main__":
    app = MainWindow()
    app.run()