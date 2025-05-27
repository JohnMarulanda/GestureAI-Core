import tkinter as tk
from tkinter import ttk, messagebox
import os
from core.gesture_recognition_manager import GestureRecognitionManager
from core.controllers.volume_controller import VolumeController
from core.controllers.brightness_controller import BrightnessController
from core.controllers.app_controller import AppController
from core.controllers.shortcuts_controller import ShortcutsController
from core.controllers.navigation_controller import NavigationController
from core.controllers.system_controller import SystemController
from core.controllers.multimedia_controller import MultimediaController
from core.controllers.mouse_controller import MouseController
from config import settings

class MainWindow:
    def __init__(self):
        # Inicializar el gestor de reconocimiento de gestos
        self.gesture_manager = GestureRecognitionManager()
        
        # Configurar la ventana principal
        self.root = tk.Tk()
        self.root.title("GestureAI Control Panel")
        
        # Obtener dimensiones de pantalla
        screen_width = self.root.winfo_screenwidth()
        
        # Definir dimensiones fijas
        window_width = 160
        window_height = 650
        x_position = screen_width - window_width
        y_position = 0

        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        
        # Configurar estilo
        self.style = ttk.Style()
        self.style.configure("Controller.TButton", 
                          padding=5, 
                          font=('Helvetica', 11, 'bold'),
                          background='#3498DB',
                          foreground='#4F8BB3')
        
        self.style.map('Controller.TButton',
                      background=[('active', '#2980B9')],
                      foreground=[('active', '#4F8BB3')])
        
        # Configurar colores
        self.root.configure(bg='#ECF0F1')
        self.style.configure("TFrame", background='#ECF0F1')
        
        # Lista de controladores disponibles
        self.all_controllers = [
            ("Control de Volumen", VolumeController, "Controla el volumen del sistema con gestos"),
            ("Control de Brillo", BrightnessController, "Ajusta el brillo de la pantalla"),
            ("Control de Aplicaciones", AppController, "Abre y cierra aplicaciones con gestos"),
            ("Atajos de Teclado", ShortcutsController, "Ejecuta atajos de teclado"),
            ("Navegación", NavigationController, "Navega por el sistema"),
            ("Control del Sistema", SystemController, "Controla funciones del sistema"),
            ("Control Multimedia", MultimediaController, "Controla la reproducción multimedia"),
            ("Control del Mouse", MouseController, "Controla el cursor con gestos")
        ]
        
        self.current_group = 0
        self.active_controller = None
        self.create_widgets()
    
    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="5", style="TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame para los botones
        self.buttons_frame = ttk.Frame(main_frame, style="TFrame")
        self.buttons_frame.pack(fill=tk.X, pady=(10, 5), side=tk.TOP)
        
        # Actualizar botones
        self.update_controller_buttons()
        
        # Botón para cerrar
        quit_frame = ttk.Frame(main_frame, style="TFrame")
        quit_frame.pack(side=tk.TOP, pady=(5, 10))
        
        quit_btn = ttk.Button(quit_frame,
                            text="Cerrar Aplicación",
                            style="Controller.TButton",
                            command=self.quit_application)
        quit_btn.pack()
    
    def update_controller_buttons(self):
        # Limpiar botones existentes
        for widget in self.buttons_frame.winfo_children():
            widget.destroy()
        
        # Calcular índices
        start_idx = self.current_group * 5
        available_height = 600
        button_height = available_height // 6
        
        # Mostrar controladores del grupo actual
        for i in range(5):
            idx = (start_idx + i) % len(self.all_controllers)
            name, controller, tooltip = self.all_controllers[idx]
            
            btn = ttk.Button(self.buttons_frame,
                           text=name,
                           style="Controller.TButton",
                           command=lambda c=controller: self.start_controller(c))
            btn.pack(fill=tk.X, pady=2, ipady=button_height//4)
            
            # Crear tooltip
            self.create_tooltip(btn, tooltip)
        
        # Botón para cambiar grupo
        others_btn = ttk.Button(self.buttons_frame,
                               text="Otros Controles",
                               style="Controller.TButton",
                               command=self.next_controller_group)
        others_btn.pack(fill=tk.X, pady=2, ipady=button_height//4)
    
    def create_tooltip(self, widget, text):
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = ttk.Label(tooltip, text=text, justify=tk.LEFT,
                              background="#ffffe0", relief=tk.SOLID, borderwidth=1)
            label.pack()
            
            def hide_tooltip():
                tooltip.destroy()
            
            widget.tooltip = tooltip
            widget.bind('<Leave>', lambda e: hide_tooltip())
            
        widget.bind('<Enter>', show_tooltip)
    
    def next_controller_group(self):
        total_groups = (len(self.all_controllers) + 4) // 5
        self.current_group = (self.current_group + 1) % total_groups
        self.update_controller_buttons()
    
    def start_controller(self, controller_class):
        try:
            # Detener controlador actual si existe
            if self.active_controller:
                self.active_controller.stop()
                self.active_controller = None
            
            # Crear y ejecutar nuevo controlador
            self.active_controller = controller_class()
            self.active_controller.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al iniciar el controlador: {str(e)}")
    
    def quit_application(self):
        # Detener controlador activo
        if self.active_controller:
            self.active_controller.stop()
        
        # Detener el gestor de reconocimiento
        self.gesture_manager.dispose()
        
        # Cerrar la aplicación
        self.root.quit()
    
    def run(self):
        try:
            # Iniciar el gestor de reconocimiento
            self.gesture_manager.start_camera_with_settings(
                camera_id=settings.DEFAULT_CAMERA_ID,
                width=settings.CAMERA_WIDTH,
                height=settings.CAMERA_HEIGHT
            )
            
            # Iniciar el bucle principal
            self.root.mainloop()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al iniciar la aplicación: {str(e)}")
        finally:
            self.quit_application()

if __name__ == "__main__":
    app = MainWindow()
    app.run()