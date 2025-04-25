import tkinter as tk
from tkinter import ttk, PhotoImage
from tkinter.font import Font
import sys
import os
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

class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("GestureAI Control Panel")
        self.root.geometry("1000x700")  # Ventana más grande
        
        # Configurar estilo
        self.style = ttk.Style()
        self.style.configure("Controller.TButton", padding=10, font=('Helvetica', 10))
        self.style.configure("Title.TLabel", font=('Helvetica', 24, 'bold'), foreground='#2C3E50')
        self.style.configure("Description.TLabel", font=('Helvetica', 9), foreground='#34495E')
        
        # Configurar colores
        self.root.configure(bg='#ECF0F1')
        self.style.configure("TFrame", background='#ECF0F1')
        
        self.active_controller = None
        self.create_widgets()

    def create_widgets(self):
        # Frame principal con padding y color de fondo
        main_frame = ttk.Frame(self.root, padding="20", style="TFrame")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Título con mejor formato
        title_frame = ttk.Frame(main_frame, style="TFrame")
        title_frame.grid(row=0, column=0, columnspan=3, pady=20)
        
        title_label = ttk.Label(title_frame, 
                              text="GestureAI Control Panel",
                              style="Title.TLabel")
        title_label.pack()
        
        subtitle_label = ttk.Label(title_frame,
                                 text="Control por gestos intuitivo y eficiente",
                                 font=('Helvetica', 12),
                                 foreground='#7F8C8D')
        subtitle_label.pack(pady=5)
        
        # Crear botones para cada controlador con mejor diseño
        controllers = [
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
        
        # Crear grid de botones con mejor espaciado y diseño
        row = 1
        col = 0
        for name, controller, description in controllers:
            frame = ttk.Frame(main_frame, padding="10", style="TFrame")
            frame.grid(row=row, column=col, padx=10, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # Botón con mejor estilo
            btn = ttk.Button(frame, 
                           text=name,
                           style="Controller.TButton",
                           command=lambda c=controller: self.start_controller(c))
            btn.grid(row=0, column=0, pady=5, sticky=(tk.W, tk.E))
            
            # Descripción con mejor formato
            desc_label = ttk.Label(frame, 
                                 text=description,
                                 style="Description.TLabel",
                                 wraplength=250)
            desc_label.grid(row=1, column=0, pady=5)
            
            col += 1
            if col > 2:
                col = 0
                row += 1
        
        # Botón para cerrar con mejor diseño
        quit_frame = ttk.Frame(main_frame, style="TFrame")
        quit_frame.grid(row=row+1, column=0, columnspan=3, pady=30)
        
        quit_btn = ttk.Button(quit_frame,
                            text="Cerrar Aplicación",
                            style="Controller.TButton",
                            command=self.root.quit)
        quit_btn.pack()
    
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
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = MainWindow()
    app.run()