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
        print("Gestos disponibles:")
        self.print_available_gestures()
        print("Presiona 'q' para salir")
    
    def load_config(self):
        """Carga la configuración de gestos desde el archivo JSON"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.config = {
                    "gestures": config.get("app_gestures", {}),
                    "paths": config.get("app_paths", {}),
                    "button_gestures": config.get("button_gestures", {})
                }
            print("Configuración cargada exitosamente")
        except Exception as e:
            print(f"Error cargando configuración: {e}")
            self.config = {"gestures": {}, "paths": {}, "button_gestures": {}}
    
    def print_available_gestures(self):
        """Imprime los gestos disponibles para abrir y cerrar aplicaciones"""
        print("- Gestos para ABRIR aplicaciones:")
        for app_name, gesture in self.config["gestures"].get("open", {}).items():
            gesture_str = "".join(map(str, gesture))
            app_path = self.config["paths"].get(app_name, "No configurado")
            print(f"  • {app_name}: [{gesture_str}] -> {app_path}")
        
        print("- Gestos para CERRAR aplicaciones:")
        for app_name, gesture in self.config["gestures"].get("close", {}).items():
            gesture_str = "".join(map(str, gesture))
            print(f"  • {app_name}: [{gesture_str}]")
    
    def start(self):
        """Inicia el controlador y se suscribe a los gestos."""
        # Iniciar la cámara si no está iniciada
        camera_status = self.gesture_manager.get_camera_status()
        if not camera_status["connected"]:
            success = self.gesture_manager.start_camera_with_settings(
                camera_id=settings.DEFAULT_CAMERA_ID,
                width=settings.CAMERA_WIDTH,
                height=settings.CAMERA_HEIGHT
            )
            if not success:
                print("Error: No se pudo iniciar la cámara")
                return False
        
        # Suscribirse a todos los gestos de mano disponibles
        # En lugar de crear gestos específicos, usamos los gestos base
        available_gestures = ["pinch", "palm", "fist", "point", "victory", "thumbs_up", 
                             "swipe_left", "swipe_right", "grab", "release"]
        
        for gesture_id in available_gestures:
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
        return True
    
    def stop(self):
        """Detiene el controlador y cancela las suscripciones."""
        self.running = False
        
        if self.display_thread and self.display_thread.is_alive():
            self.display_thread.join(timeout=1.0)
        
        # Cancelar suscripciones
        available_gestures = ["pinch", "palm", "fist", "point", "victory", "thumbs_up", 
                             "swipe_left", "swipe_right", "grab", "release"]
        
        for gesture_id in available_gestures:
            self.gesture_manager.unsubscribe_from_gesture(gesture_id)
        
        print("Controlador de aplicaciones detenido")
    
    def handle_gesture(self, event_type, gesture_data):
        """Maneja los eventos de gestos recibidos del gestor.
        
        Args:
            event_type: Tipo de evento ('detected', 'updated', 'ended').
            gesture_data: Datos del gesto.
        """
        gesture_id = gesture_data.get("id")
        landmarks = gesture_data.get("landmarks")
        
        with self.lock:
            if event_type == "detected" or event_type == "updated":
                # Procesar el gesto si tenemos landmarks
                if landmarks:
                    # Detectar estados de los dedos
                    finger_states = self.detect_finger_states(landmarks)
                    if finger_states:
                        # Verificar gestos de apertura
                        for app_name, gesture_pattern in self.config["gestures"].get("open", {}).items():
                            if finger_states == gesture_pattern:
                                self.set_action_message(f"Detectado gesto para abrir {app_name}")
                                self.open_application(app_name)
                                return
                        
                        # Verificar gestos de cierre
                        for app_name, gesture_pattern in self.config["gestures"].get("close", {}).items():
                            if finger_states == gesture_pattern:
                                self.set_action_message(f"Detectado gesto para cerrar {app_name}")
                                self.close_application(app_name)
                                return
                        
                        # Verificar gestos de botones especiales
                        finger_state_str = "".join(map(str, finger_states))
                        for button_name, button_pattern in self.config["button_gestures"].items():
                            button_pattern_str = "".join(map(str, button_pattern))
                            if finger_state_str == button_pattern_str:
                                if button_name == "quit_controller":
                                    self.set_action_message("Cerrando controlador...")
                                    threading.Timer(1.0, self.stop).start()
                                elif button_name == "quit_app":
                                    self.set_action_message("Cerrando aplicación...")
                                    threading.Timer(1.0, lambda: os._exit(0)).start()
                                return
            
            elif event_type == "ended":
                # Limpiar el gesto terminado
                if gesture_id in self.active_gestures:
                    del self.active_gestures[gesture_id]
    
    def detect_finger_states(self, hand_landmarks):
        """
        Detecta el estado de los dedos (extendido o no) y devuelve una lista de 0s y 1s.
        
        Args:
            hand_landmarks: Los landmarks de la mano detectada.
            
        Returns:
            list: Lista de 5 valores (0 o 1) representando el estado de cada dedo.
        """
        if not hand_landmarks:
            return None
            
        finger_states = []
        
        # Pulgar: comparar con la articulación anterior
        if hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x:
            finger_states.append(1)  # Extendido
        else:
            finger_states.append(0)  # No extendido
        
        # Para los otros dedos, comparar con la articulación anterior
        for tip_id in [8, 12, 16, 20]:  # índice, medio, anular, meñique
            pip_id = tip_id - 2  # Articulación PIP (anterior a la punta)
            if hand_landmarks.landmark[tip_id].y < hand_landmarks.landmark[pip_id].y:
                finger_states.append(1)  # Extendido
            else:
                finger_states.append(0)  # No extendido
        
        return finger_states
    
    def open_application(self, app_name):
        """Abre la aplicación especificada."""
        app_path = self.config["paths"].get(app_name)
        if not app_path:
            self.set_action_message(f"Error: Ruta no configurada para {app_name}")
            return False
        
        try:
            # Verificar si la aplicación ya está en ejecución
            if app_name in self.running_apps:
                try:
                    process = self.running_apps[app_name]
                    if process.is_running():
                        self.set_action_message(f"{app_name} ya está en ejecución")
                        return True
                except:
                    # Si hay error al verificar el proceso, lo eliminamos del diccionario
                    del self.running_apps[app_name]
            
            # Intentar abrir la aplicación
            try:
                # Usar os.startfile para Windows que es más confiable
                os.startfile(app_path)
                self.set_action_message(f"✓ Abierto: {app_name}")
                
                # Intentar rastrear el proceso (opcional)
                time.sleep(1)  # Dar tiempo para que se inicie
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if app_path.lower().split("\\")[-1].replace(".exe", "") in proc.info['name'].lower():
                            self.running_apps[app_name] = proc
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                return True
                
            except Exception as subprocess_error:
                # Si falla os.startfile, intentar con subprocess
                try:
                    process = subprocess.Popen([app_path])
                    self.running_apps[app_name] = psutil.Process(process.pid)
                    self.set_action_message(f"✓ Abierto: {app_name}")
                    return True
                except Exception as final_error:
                    self.set_action_message(f"Error abriendo {app_name}: {str(final_error)}")
                    return False
                
        except Exception as e:
            self.set_action_message(f"Error abriendo {app_name}: {str(e)}")
            return False
    
    def close_application(self, app_name):
        """Cierra la aplicación especificada."""
        app_path = self.config["paths"].get(app_name, "")
        if not app_path:
            self.set_action_message(f"Error: Ruta no configurada para {app_name}")
            return False
            
        try:
            # Obtener el nombre del ejecutable
            app_exe = os.path.basename(app_path).lower()
            
            # Primero intentar cerrar por el proceso guardado
            if app_name in self.running_apps:
                try:
                    process = self.running_apps[app_name]
                    if process.is_running():
                        process.terminate()
                        self.set_action_message(f"✓ Cerrado: {app_name}")
                        del self.running_apps[app_name]
                        return True
                except:
                    del self.running_apps[app_name]
            
            # Si no se encontró en running_apps, buscar por nombre de ejecutable
            found = False
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if app_exe in proc.info['name'].lower():
                        proc.terminate()
                        found = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if found:
                self.set_action_message(f"✓ Cerrado: {app_name}")
                return True
            else:
                self.set_action_message(f"{app_name} no está en ejecución")
                return False
                
        except Exception as e:
            self.set_action_message(f"Error cerrando {app_name}: {str(e)}")
            return False
    
    def display_landmarks(self, frame):
        """
        Muestra los landmarks de la mano y el estado de los dedos.
        
        Args:
            frame: Frame donde mostrar los landmarks.
        """
        _, results = self.gesture_manager.process_frame()
        
        if results and results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Dibujar las conexiones entre landmarks
                self.gesture_manager.drawing_utils.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.gesture_manager.mp_hands.HAND_CONNECTIONS)
                
                # Detectar y mostrar estados de los dedos
                finger_states = self.detect_finger_states(hand_landmarks)
                if finger_states:
                    finger_state_str = "".join([str(s) for s in finger_states])
                    cv2.putText(frame, f"Estados dedos: {finger_state_str}", 
                                (10, frame.shape[0] - 120), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    
                    # Mostrar estado individual de cada dedo
                    finger_names = ["Pulgar", "Índice", "Medio", "Anular", "Meñique"]
                    y_pos = frame.shape[0] - 90
                    for i, (name, state) in enumerate(zip(finger_names, finger_states)):
                        color = (0, 255, 0) if state == 1 else (0, 0, 255)
                        status = "↑" if state == 1 else "↓"
                        cv2.putText(frame, f"{name}: {status}", 
                                    (10 + (i * 100), y_pos), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
                
                # Dibujar los puntos de los landmarks importantes
                important_landmarks = [4, 8, 12, 16, 20]  # Puntas de los dedos
                for i in important_landmarks:
                    landmark = hand_landmarks.landmark[i]
                    x = int(landmark.x * frame.shape[1])
                    y = int(landmark.y * frame.shape[0])
                    
                    # Dibujar círculo para cada landmark importante
                    cv2.circle(frame, (x, y), 8, (255, 0, 0), -1)
                    cv2.putText(frame, str(i), (x + 10, y), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
    
    def display_app_info(self, frame):
        """
        Muestra información sobre las aplicaciones y sus gestos.
        
        Args:
            frame: Frame donde mostrar la información.
        """
        y_pos = 30
        cv2.putText(frame, "CONTROL DE APLICACIONES", (10, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Mostrar gestos para abrir
        y_pos += 35
        cv2.putText(frame, "Gestos para ABRIR:", (10, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        y_pos += 25
        for app_name, gesture in self.config["gestures"].get("open", {}).items():
            gesture_str = "".join(map(str, gesture))
            cv2.putText(frame, f"{app_name}: [{gesture_str}]", (20, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            y_pos += 20
        
        # Mostrar gestos para cerrar
        y_pos += 10
        cv2.putText(frame, "Gestos para CERRAR:", (10, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        y_pos += 25
        for app_name, gesture in self.config["gestures"].get("close", {}).items():
            gesture_str = "".join(map(str, gesture))
            cv2.putText(frame, f"{app_name}: [{gesture_str}]", (20, y_pos),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            y_pos += 20
        
        # Mostrar controles especiales
        y_pos += 10
        cv2.putText(frame, "Controles especiales:", (10, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        y_pos += 25
        
        special_controls = [
            ("Salir controlador", self.config["button_gestures"].get("quit_controller", [])),
            ("Salir aplicacion", self.config["button_gestures"].get("quit_app", []))
        ]
        
        for control_name, gesture in special_controls:
            if gesture:
                gesture_str = "".join(map(str, gesture))
                cv2.putText(frame, f"{control_name}: [{gesture_str}]", (20, y_pos),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
                y_pos += 20
    
    def set_action_message(self, message):
        """Establece el mensaje de acción para mostrar en pantalla."""
        with self.lock:
            message_id = str(time.time())
            self.gesture_messages[message_id] = message
            # Programar la eliminación del mensaje
            threading.Timer(self.message_duration, 
                          lambda: self.remove_message(message_id)).start()
        print(f"[APP] {message}")
    
    def remove_message(self, message_id):
        """Elimina un mensaje después de su duración."""
        with self.lock:
            if message_id in self.gesture_messages:
                del self.gesture_messages[message_id]
    
    def display_messages(self, frame):
        """Muestra mensajes de eventos de gestos."""
        with self.lock:
            y_pos = frame.shape[0] - 180
            for message in list(self.gesture_messages.values())[-3:]:  # Mostrar solo los últimos 3 mensajes
                cv2.putText(frame, message, (10, y_pos), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                y_pos -= 25
    
    def display_loop(self):
        """Bucle principal para mostrar la interfaz de usuario."""
        while self.running:
            # Obtener el frame actual
            image, _ = self.gesture_manager.process_frame()
            if image is None:
                time.sleep(0.01)
                continue
            
            # Mostrar elementos de UI
            self.display_app_info(image)
            self.display_landmarks(image)
            self.display_messages(image)
            
            # Mostrar el frame
            cv2.imshow('Control de Aplicaciones con Gestos', image)
            
            # Salir con 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.running = False
                break
        
        cv2.destroyAllWindows()

def main():
    """Función principal para ejecutar el controlador."""
    controller = AppController()
    try:
        success = controller.start()
        if success:
            print("\n=== CONTROL DE APLICACIONES INICIADO ===")
            print("- Usa los gestos configurados para abrir/cerrar aplicaciones")
            print("- Presiona 'q' en la ventana de video para salir")
            print("- Los estados de dedos se muestran como: [Pulgar, Índice, Medio, Anular, Meñique]")
            print("- 1 = dedo extendido, 0 = dedo cerrado")
            print("="*50)
            
            # Mantener el programa en ejecución
            while controller.running:
                time.sleep(0.1)
        else:
            print("Error: No se pudo iniciar el controlador")
    except KeyboardInterrupt:
        print("\nPrograma interrumpido por el usuario")
    finally:
        controller.stop()

if __name__ == "__main__":
    main()