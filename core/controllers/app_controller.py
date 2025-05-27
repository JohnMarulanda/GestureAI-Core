import cv2
import time
import subprocess
import psutil
import os
import json
import threading
from core.gesture_recognition_manager import GestureRecognitionManager
from config import settings

class AppController:
    """Controlador para abrir y cerrar aplicaciones usando gestos.
    
    Este controlador utiliza el GestureRecognitionManager centralizado para el
    reconocimiento de gestos, eliminando la lógica duplicada de detección.
    """
    
    def __init__(self):
        """Inicializa el controlador de aplicaciones."""
        # Obtener la instancia única del gestor de reconocimiento
        self.gesture_manager = GestureRecognitionManager()
        
        # Variables de estado
        self.running = False
        self.display_thread = None
        self.lock = threading.Lock()
        
        # Estado de gestos
        self.active_gestures = {}
        self.gesture_messages = {}
        self.current_gesture = None
        self.gesture_start_time = 0
        self.gesture_duration = 0
        
        # Configuración
        self.required_duration = settings.APP_GESTURE_DURATION
        self.confirmation_required = settings.APP_CONFIRMATION_REQUIRED
        self.confirmation_multiplier = settings.APP_CONFIRMATION_MULTIPLIER
        self.message_duration = settings.SYSTEM_MESSAGE_DURATION
        
        # Cargar configuración
        self.config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                       settings.GESTURE_CONFIG_PATH)
        self.load_config()
        
        # Seguimiento de aplicaciones en ejecución
        self.running_apps = {}  # {app_name: process}
        
        print("Controlador de aplicaciones inicializado")
    
    def load_config(self):
        """Carga la configuración de gestos desde el archivo JSON"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.config = {
                    "gestures": config.get("app_gestures", {}),
                    "paths": config.get("app_paths", {})
                }
        except Exception as e:
            print(f"Error cargando configuración: {e}")
            self.config = {"gestures": {}, "paths": {}}
    
    def start(self):
        """Inicia el controlador y se suscribe a los gestos."""
        # Iniciar la cámara si no está iniciada
        camera_status = self.gesture_manager.get_camera_status()
        if not camera_status["connected"]:
            self.gesture_manager.start_camera_with_settings(
                camera_id=settings.DEFAULT_CAMERA_ID,
                width=settings.CAMERA_WIDTH,
                height=settings.CAMERA_HEIGHT
            )
        
        # Suscribirse a los gestos configurados
        for action in self.config["gestures"]:
            for app_name in self.config["gestures"][action]:
                gesture_id = f"{action}_{app_name}"
                self.gesture_manager.subscribe_to_gesture(gesture_id, self.handle_gesture)
        
        # Iniciar el procesamiento de gestos si no está en ejecución
        if not self.gesture_manager._running:
            self.gesture_manager.start_processing()
        
        # Iniciar el hilo de visualización
        self.running = True
        self.display_thread = threading.Thread(target=self.display_loop)
        self.display_thread.daemon = True
        self.display_thread.start()
        
        print("Controlador de aplicaciones iniciado")
        print("Presiona 'q' para salir, 'c' para alternar confirmación")
    
    def stop(self):
        """Detiene el controlador y cancela las suscripciones."""
        self.running = False
        
        if self.display_thread and self.display_thread.is_alive():
            self.display_thread.join(timeout=1.0)
        
        # Cancelar suscripciones
        for action in self.config["gestures"]:
            for app_name in self.config["gestures"][action]:
                gesture_id = f"{action}_{app_name}"
                self.gesture_manager.unsubscribe_from_gesture(gesture_id)
        
        print("Controlador de aplicaciones detenido")
    
    def handle_gesture(self, event_type, gesture_data):
        """Maneja los eventos de gestos recibidos del gestor.
        
        Args:
            event_type: Tipo de evento ('detected', 'updated', 'ended').
            gesture_data: Datos del gesto.
        """
        gesture_id = gesture_data.get("id")
        
        with self.lock:
            if event_type == "detected":
                # Nuevo gesto detectado
                self.active_gestures[gesture_id] = gesture_data
                action, app_name = gesture_id.split("_", 1)
                self.gesture_messages[gesture_id] = f"Detectando: {action} {app_name}"
                
                # Iniciar seguimiento de duración
                self.current_gesture = (action, app_name)
                self.gesture_start_time = time.time()
                self.gesture_duration = 0
                
            elif event_type == "updated":
                # Actualizar gesto y duración
                self.active_gestures[gesture_id] = gesture_data
                if self.current_gesture:
                    self.gesture_duration = time.time() - self.gesture_start_time
                    
                    # Verificar si se alcanzó la duración requerida
                    action, app_name = self.current_gesture
                    if self.gesture_duration >= self.required_duration:
                        if action == "open":
                            self.open_application(app_name)
                            self.current_gesture = None
                        elif action == "close":
                            if not self.confirmation_required or \
                               self.gesture_duration >= self.required_duration * self.confirmation_multiplier:
                                self.close_application(app_name)
                                self.current_gesture = None
                
            elif event_type == "ended":
                # Gesto terminado
                if gesture_id in self.active_gestures:
                    del self.active_gestures[gesture_id]
                    self.current_gesture = None
                    self.gesture_duration = 0
    
    def open_application(self, app_name):
        """Abre la aplicación especificada."""
        app_path = self.config["paths"].get(app_name)
        if not app_path:
            self.set_action_message(f"Error: Ruta no configurada para {app_name}")
            return False
        
        try:
            # Verificar si la aplicación ya está en ejecución
            if app_name in self.running_apps and self.running_apps[app_name].is_running():
                self.set_action_message(f"{app_name} ya está en ejecución")
                return True
            
            # Abrir la aplicación
            process = subprocess.Popen(app_path)
            self.running_apps[app_name] = psutil.Process(process.pid)
            self.set_action_message(f"Abierto: {app_name}")
            return True
        except Exception as e:
            self.set_action_message(f"Error abriendo {app_name}: {e}")
            return False
    
    def close_application(self, app_name):
        """Cierra la aplicación especificada."""
        # Si tenemos un proceso almacenado, intentar cerrarlo
        if app_name in self.running_apps:
            try:
                process = self.running_apps[app_name]
                if process.is_running():
                    process.terminate()
                    self.set_action_message(f"Cerrado: {app_name}")
                    del self.running_apps[app_name]
                    return True
                else:
                    del self.running_apps[app_name]
            except Exception as e:
                self.set_action_message(f"Error cerrando proceso de {app_name}: {e}")
        
        # Intentar encontrar el proceso por nombre
        try:
            found = False
            for proc in psutil.process_iter(['pid', 'name']):
                if app_name.lower() in proc.info['name'].lower():
                    proc.terminate()
                    found = True
            
            if found:
                self.set_action_message(f"Cerrado: {app_name}")
                return True
            else:
                self.set_action_message(f"{app_name} no está en ejecución")
                return False
        except Exception as e:
            self.set_action_message(f"Error cerrando {app_name}: {e}")
            return False
    
    def set_action_message(self, message):
        """Establece el mensaje de acción para mostrar en pantalla."""
        with self.lock:
            message_id = str(time.time())
            self.gesture_messages[message_id] = message
            # Programar la eliminación del mensaje
            threading.Timer(self.message_duration, 
                          lambda: self.remove_message(message_id)).start()
        print(message)
    
    def remove_message(self, message_id):
        """Elimina un mensaje después de su duración."""
        with self.lock:
            if message_id in self.gesture_messages:
                del self.gesture_messages[message_id]
    
    def display_loop(self):
        """Bucle principal para mostrar la interfaz de usuario."""
        while self.running:
            # Obtener el frame actual
            image, _ = self.gesture_manager.process_frame()
            if image is None:
                time.sleep(0.01)
                continue
            
            # Mostrar información de gestos activos
            self.display_active_gestures(image)
            
            # Mostrar mensajes
            self.display_messages(image)
            
            # Mostrar instrucciones
            self.display_instructions(image)
            
            # Mostrar barra de progreso si hay un gesto activo
            if self.current_gesture:
                self.display_gesture_progress(image)
            
            # Mostrar el frame
            cv2.imshow('Control de Aplicaciones con Gestos', image)
            
            # Manejar teclas
            key = cv2.waitKey(5) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                self.confirmation_required = not self.confirmation_required
                self.set_action_message(
                    f"Confirmación {'activada' if self.confirmation_required else 'desactivada'}")
        
        # Cerrar ventanas
        cv2.destroyAllWindows()
    
    def display_active_gestures(self, image):
        """Muestra información sobre los gestos activos."""
        with self.lock:
            y_pos = 30
            cv2.putText(image, "GESTOS ACTIVOS:", (10, y_pos), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            y_pos += 30
            for gesture_id, gesture_data in self.active_gestures.items():
                confidence = gesture_data.get("confidence", 0) * 100
                action, app_name = gesture_id.split("_", 1)
                text = f"{action.capitalize()} {app_name}: {confidence:.1f}%"
                cv2.putText(image, text, (10, y_pos), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                y_pos += 25
    
    def display_messages(self, image):
        """Muestra mensajes de eventos de gestos."""
        with self.lock:
            y_pos = image.shape[0] - 60
            for message in self.gesture_messages.values():
                cv2.putText(image, message, (10, y_pos), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                y_pos -= 30
    
    def display_instructions(self, image):
        """Muestra instrucciones de uso."""
        y_pos = 30
        x_pos = image.shape[1] - 300
        
        cv2.putText(image, "GESTOS DE CONTROL:", (x_pos, y_pos), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        y_pos += 30
        # Mostrar gestos de apertura
        cv2.putText(image, "ABRIR:", (x_pos, y_pos), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        y_pos += 25
        for app_name in self.config["gestures"].get("open", {}):
            cv2.putText(image, f"- {app_name}", (x_pos + 20, y_pos), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_pos += 20
        
        # Mostrar gestos de cierre
        y_pos += 10
        cv2.putText(image, "CERRAR:", (x_pos, y_pos), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        y_pos += 25
        for app_name in self.config["gestures"].get("close", {}):
            cv2.putText(image, f"- {app_name}", (x_pos + 20, y_pos), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_pos += 20
    
    def display_gesture_progress(self, image):
        """Muestra la barra de progreso para la duración del gesto."""
        if self.gesture_duration > 0:
            action, app_name = self.current_gesture
            required_time = self.required_duration
            if action == "close" and self.confirmation_required:
                required_time *= self.confirmation_multiplier
            
            progress = min(self.gesture_duration / required_time, 1.0)
            bar_width = int(image.shape[1] * 0.6)
            bar_height = 20
            bar_x = int((image.shape[1] - bar_width) / 2)
            bar_y = image.shape[0] - 100
            
            # Dibujar barra de fondo
            cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), 
                          (100, 100, 100), -1)
            
            # Dibujar barra de progreso
            progress_width = int(bar_width * progress)
            cv2.rectangle(image, (bar_x, bar_y), (bar_x + progress_width, bar_y + bar_height), 
                          (0, 255, 0), -1)
            
            # Dibujar texto
            text = f"Detectando: {action.capitalize()} {app_name} ({int(progress * 100)}%)"
            cv2.putText(image, text, (bar_x, bar_y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)