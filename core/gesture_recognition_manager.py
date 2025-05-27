import cv2
import mediapipe as mp
import time
import json
import os
import threading
import logging
from typing import Dict, List, Callable, Any, Optional, Tuple
from collections import defaultdict
from core.gesture_detector import GestureDetector
from config import settings

class GestureRecognitionManager(GestureDetector):
    """Controlador centralizado para el reconocimiento de gestos manuales.
    
    Esta clase implementa el patrón Singleton para proporcionar una instancia única
    que gestiona todo el reconocimiento de gestos para la aplicación. Centraliza la
    lógica de detección y permite que múltiples controladores se suscriban a gestos
    específicos sin duplicar código.
    
    Attributes:
        _instance (GestureRecognitionManager): Instancia única del gestor de reconocimiento.
        _lock (threading.Lock): Bloqueo para inicialización segura en entornos multihilo.
        _subscribers (Dict): Diccionario de suscriptores a gestos específicos.
        _gesture_configs (Dict): Configuraciones de gestos cargadas desde JSON.
        _current_gestures (Dict): Gestos actualmente detectados y su información.
        _camera_width (int): Ancho de resolución de la cámara.
        _camera_height (int): Alto de resolución de la cámara.
        _target_fps (int): FPS objetivo para el procesamiento.
        _running (bool): Indica si el procesamiento de gestos está activo.
        _processing_thread (threading.Thread): Hilo para procesamiento de gestos.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Implementa el patrón Singleton con inicialización segura en multihilo."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(GestureRecognitionManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        """Inicializa el gestor de reconocimiento de gestos si aún no está inicializado."""
        if self._initialized:
            return
            
        super().__init__()
        
        # Configuración de logging
        logging.basicConfig(filename=settings.GESTURE_LOG_PATH, 
                           level=logging.INFO,
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger('GestureRecognitionManager')
        
        # Configuración de cámara
        self._camera_width = settings.CAMERA_WIDTH
        self._camera_height = settings.CAMERA_HEIGHT
        self._target_fps = settings.CAMERA_FPS
        self._camera_id = settings.DEFAULT_CAMERA_ID
        
        # Estado del gestor
        self._running = False
        self._processing_thread = None
        
        # Gestión de gestos
        self._subscribers = defaultdict(list)
        self._gesture_configs = {}
        self._current_gestures = {}
        self._gesture_confidence = {}
        self._last_detected_gestures = {}
        
        # Pool de objetos para frames
        self._frame_pool = []
        self._max_pool_size = settings.GESTURE_POOL_SIZE
        
        # Cargar configuraciones
        self._load_gesture_configs()
        
        self._initialized = True
        self.logger.info("GestureRecognitionManager inicializado")
    
    def __del__(self):
        """Asegura la liberación de recursos al destruir la instancia."""
        self.dispose()
    
    def dispose(self):
        """Libera recursos y detiene el procesamiento.
        
        Implementa IDisposable para asegurar la liberación adecuada de recursos.
        """
        if self._running:
            self.stop_processing()
        
        if self.webcam and self.webcam.isOpened():
            self.stop_camera()
        
        self.logger.info("GestureRecognitionManager: recursos liberados")
    
    def _load_gesture_configs(self):
        """Carga las configuraciones de gestos desde el archivo JSON."""
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                 settings.GESTURE_CONFIG_PATH)
        
        # Configuración por defecto si no existe el archivo
        default_config = {
            "hand_gestures": [
                {
                    "id": "pinch",
                    "name": "Pinch Gesture",
                    "landmarks": [[4, 8]],  # Pulgar e índice
                    "threshold": 0.85,
                    "action": "pinch_action"
                },
                {
                    "id": "palm",
                    "name": "Open Palm",
                    "landmarks": [[0, 5, 9, 13, 17]],  # Base de la palma
                    "threshold": 0.80,
                    "action": "palm_action"
                },
                {
                    "id": "fist",
                    "name": "Closed Fist",
                    "landmarks": [[0, 9]],  # Base de la palma y base del dedo medio
                    "threshold": 0.90,
                    "action": "fist_action"
                },
                {
                    "id": "point",
                    "name": "Pointing Gesture",
                    "landmarks": [[8, 5]],  # Punta del índice y base del índice
                    "threshold": 0.85,
                    "action": "point_action"
                },
                {
                    "id": "victory",
                    "name": "Victory Sign",
                    "landmarks": [[8, 12]],  # Punta del índice y punta del medio
                    "threshold": 0.85,
                    "action": "victory_action"
                }
            ],
            "keyboard_gestures": {},
            "button_gestures": {},
            "app_gestures": {}
        }
        
        try:
            # Crear directorio de configuración si no existe
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    self._gesture_configs = json.load(f)
                self.logger.info(f"Configuraciones de gestos cargadas desde {config_path}")
            else:
                self._gesture_configs = default_config
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=4)
                self.logger.info(f"Configuración por defecto creada en {config_path}")
        except Exception as e:
            self.logger.error(f"Error al cargar configuraciones de gestos: {e}")
            self._gesture_configs = default_config
    
    def start_camera_with_settings(self, camera_id: int = 0, width: int = 640, height: int = 480):
        """Inicializa la cámara con resolución y FPS definidos.
        
        Args:
            camera_id: ID del dispositivo de cámara a utilizar.
            width: Ancho de resolución deseado.
            height: Alto de resolución deseado.
            
        Returns:
            bool: True si la cámara se inició correctamente, False en caso contrario.
        """
        self._camera_id = camera_id
        self._camera_width = width
        self._camera_height = height
        
        # Intentar iniciar la cámara con el ID proporcionado
        if not self.start_camera(camera_id):
            self.logger.warning(f"No se pudo iniciar la cámara con ID {camera_id}, intentando con cámara por defecto")
            # Fallback a la cámara por defecto
            if not self.start_camera(0):
                self.logger.error("No se pudo iniciar ninguna cámara")
                return False
        
        # Configurar resolución
        self.webcam.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        # Verificar si se aplicó la resolución correctamente
        actual_width = self.webcam.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = self.webcam.get(cv2.CAP_PROP_FRAME_HEIGHT)
        
        if actual_width != width or actual_height != height:
            self.logger.warning(f"Resolución solicitada ({width}x{height}) no soportada. "  
                               f"Usando ({actual_width}x{actual_height})")
        
        self.logger.info(f"Cámara iniciada con resolución {actual_width}x{actual_height}")
        return True
    
    def start_processing(self):
        """Inicia el procesamiento de gestos en un hilo separado.
        
        Returns:
            bool: True si se inició el procesamiento, False si ya estaba en ejecución.
        """
        if self._running:
            self.logger.warning("El procesamiento de gestos ya está en ejecución")
            return False
        
        if not self.webcam or not self.webcam.isOpened():
            self.logger.error("No se puede iniciar el procesamiento sin una cámara activa")
            return False
        
        self._running = True
        self._processing_thread = threading.Thread(target=self._process_frames)
        self._processing_thread.daemon = True
        self._processing_thread.start()
        
        self.logger.info("Procesamiento de gestos iniciado")
        return True
    
    def stop_processing(self):
        """Detiene el procesamiento de gestos.
        
        Returns:
            bool: True si se detuvo el procesamiento, False si no estaba en ejecución.
        """
        if not self._running:
            return False
        
        self._running = False
        if self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=1.0)
        
        self.logger.info("Procesamiento de gestos detenido")
        return True
    
    def _get_frame_from_pool(self):
        """Obtiene un frame del pool o crea uno nuevo si el pool está vacío.
        
        Returns:
            numpy.ndarray: Frame de imagen.
        """
        if self._frame_pool:
            return self._frame_pool.pop()
        return None
    
    def _return_frame_to_pool(self, frame):
        """Devuelve un frame al pool si hay espacio disponible.
        
        Args:
            frame: Frame de imagen a devolver al pool.
        """
        if len(self._frame_pool) < self._max_pool_size:
            self._frame_pool.append(frame)
    
    def _process_frames(self):
        """Procesa frames de la cámara para detectar gestos.
        
        Este método se ejecuta en un hilo separado para mantener el rendimiento.
        """
        frame_time = 1.0 / self._target_fps
        last_frame_time = time.time()
        
        while self._running:
            current_time = time.time()
            elapsed = current_time - last_frame_time
            
            # Controlar FPS
            if elapsed < frame_time:
                time.sleep(frame_time - elapsed)
                continue
            
            last_frame_time = current_time
            
            # Procesar frame
            image, results = self.process_frame()
            if image is None or results is None:
                continue
            
            # Detectar gestos en el frame actual
            detected_gestures = {}
            
            if results.multi_hand_landmarks:
                for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                    # Detectar gestos configurados
                    for gesture_config in self._gesture_configs.get("hand_gestures", []):
                        gesture_id = gesture_config["id"]
                        confidence = self._detect_gesture(hand_landmarks, gesture_config)
                        
                        if confidence >= gesture_config["threshold"]:
                            detected_gestures[gesture_id] = {
                                "id": gesture_id,
                                "name": gesture_config["name"],
                                "confidence": confidence,
                                "hand_index": hand_idx,
                                "landmarks": hand_landmarks,
                                "timestamp": current_time
                            }
                            
                            # Actualizar confianza del gesto
                            self._gesture_confidence[gesture_id] = confidence
            
            # Actualizar gestos actuales y notificar a los suscriptores
            with self._lock:
                # Identificar gestos que ya no están activos
                ended_gestures = set(self._current_gestures.keys()) - set(detected_gestures.keys())
                
                # Notificar gestos terminados
                for gesture_id in ended_gestures:
                    self._notify_gesture_ended(gesture_id)
                
                # Actualizar gestos actuales
                self._current_gestures = detected_gestures
                
                # Notificar gestos activos
                for gesture_id, gesture_data in detected_gestures.items():
                    if gesture_id not in self._last_detected_gestures:
                        # Nuevo gesto detectado
                        self._notify_gesture_detected(gesture_id, gesture_data)
                    else:
                        # Gesto continúa activo
                        self._notify_gesture_updated(gesture_id, gesture_data)
                
                # Actualizar registro de gestos detectados
                self._last_detected_gestures = detected_gestures.copy()
    
    def _detect_gesture(self, hand_landmarks, gesture_config):
        """Detecta un gesto específico basado en su configuración.
        
        Args:
            hand_landmarks: Landmarks de la mano detectada.
            gesture_config: Configuración del gesto a detectar.
            
        Returns:
            float: Nivel de confianza de la detección (0.0 a 1.0).
        """
        # Implementación básica - se puede mejorar con algoritmos más sofisticados
        confidence = 0.0
        landmark_sets = gesture_config.get("landmarks", [])
        
        if not landmark_sets:
            return 0.0
        
        # Calcular confianza basada en las posiciones relativas de los landmarks
        for landmark_set in landmark_sets:
            if len(landmark_set) < 2:
                continue
                
            # Calcular distancias entre landmarks
            distances = []
            for i in range(len(landmark_set) - 1):
                idx1 = landmark_set[i]
                idx2 = landmark_set[i + 1]
                
                p1 = (hand_landmarks.landmark[idx1].x, hand_landmarks.landmark[idx1].y)
                p2 = (hand_landmarks.landmark[idx2].x, hand_landmarks.landmark[idx2].y)
                
                distance = self.calculate_distance(p1, p2)
                distances.append(distance)
            
            # Normalizar distancias y calcular confianza
            if distances:
                # Algoritmo simplificado - se puede mejorar
                avg_distance = sum(distances) / len(distances)
                set_confidence = 1.0 - min(avg_distance * 10, 1.0)  # Normalizar a 0-1
                confidence = max(confidence, set_confidence)
        
        return confidence
    
    def _notify_gesture_detected(self, gesture_id, gesture_data):
        """Notifica a los suscriptores que se ha detectado un nuevo gesto.
        
        Args:
            gesture_id: ID del gesto detectado.
            gesture_data: Datos del gesto detectado.
        """
        if gesture_id in self._subscribers:
            for callback in self._subscribers[gesture_id]:
                try:
                    callback("detected", gesture_data)
                except Exception as e:
                    self.logger.error(f"Error en callback para gesto {gesture_id}: {e}")
    
    def _notify_gesture_updated(self, gesture_id, gesture_data):
        """Notifica a los suscriptores que un gesto activo se ha actualizado.
        
        Args:
            gesture_id: ID del gesto actualizado.
            gesture_data: Datos actualizados del gesto.
        """
        if gesture_id in self._subscribers:
            for callback in self._subscribers[gesture_id]:
                try:
                    callback("updated", gesture_data)
                except Exception as e:
                    self.logger.error(f"Error en callback para gesto {gesture_id}: {e}")
    
    def _notify_gesture_ended(self, gesture_id):
        """Notifica a los suscriptores que un gesto ha terminado.
        
        Args:
            gesture_id: ID del gesto terminado.
        """
        if gesture_id in self._subscribers:
            for callback in self._subscribers[gesture_id]:
                try:
                    callback("ended", {"id": gesture_id})
                except Exception as e:
                    self.logger.error(f"Error en callback para gesto {gesture_id}: {e}")
    
    # API Pública
    
    def get_current_gesture(self, gesture_id=None):
        """Obtiene información sobre el gesto activo.
        
        Args:
            gesture_id: ID específico del gesto a consultar. Si es None, devuelve todos los gestos activos.
            
        Returns:
            dict: Datos del gesto o gestos activos.
        """
        with self._lock:
            if gesture_id is None:
                return self._current_gestures.copy()
            return self._current_gestures.get(gesture_id)
    
    def subscribe_to_gesture(self, gesture_id, callback):
        """Suscribe una función de callback a un gesto específico.
        
        Args:
            gesture_id: ID del gesto al que suscribirse.
            callback: Función a llamar cuando se detecte el gesto.
            
        Returns:
            bool: True si la suscripción fue exitosa, False en caso contrario.
        """
        if not callable(callback):
            self.logger.error(f"El callback para {gesture_id} no es una función válida")
            return False
            
        with self._lock:
            self._subscribers[gesture_id].append(callback)
            self.logger.info(f"Nuevo suscriptor registrado para gesto {gesture_id}")
            return True
    
    def unsubscribe_from_gesture(self, gesture_id, callback=None):
        """Cancela la suscripción a un gesto específico.
        
        Args:
            gesture_id: ID del gesto del que desuscribirse.
            callback: Función específica a eliminar. Si es None, elimina todas las suscripciones.
            
        Returns:
            bool: True si la desuscripción fue exitosa, False en caso contrario.
        """
        with self._lock:
            if gesture_id not in self._subscribers:
                return False
                
            if callback is None:
                self._subscribers[gesture_id].clear()
                self.logger.info(f"Todas las suscripciones eliminadas para gesto {gesture_id}")
            else:
                try:
                    self._subscribers[gesture_id].remove(callback)
                    self.logger.info(f"Suscripción específica eliminada para gesto {gesture_id}")
                except ValueError:
                    self.logger.warning(f"Callback no encontrado para gesto {gesture_id}")
                    return False
            return True
    
    def update_gesture_config(self, gesture_id, parameters):
        """Actualiza la configuración de un gesto específico.
        
        Args:
            gesture_id: ID del gesto a actualizar.
            parameters: Diccionario con los parámetros a actualizar.
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario.
        """
        with self._lock:
            for i, gesture in enumerate(self._gesture_configs.get("hand_gestures", [])):
                if gesture.get("id") == gesture_id:
                    # Actualizar parámetros
                    for key, value in parameters.items():
                        if key in gesture:
                            self._gesture_configs["hand_gestures"][i][key] = value
                    
                    # Guardar configuración actualizada
                    try:
                        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                                settings.GESTURE_CONFIG_PATH)
                        with open(config_path, 'w') as f:
                            json.dump(self._gesture_configs, f, indent=4)
                        self.logger.info(f"Configuración actualizada para gesto {gesture_id}")
                        return True
                    except Exception as e:
                        self.logger.error(f"Error al guardar configuración: {e}")
                        return False
            
            self.logger.warning(f"Gesto {gesture_id} no encontrado para actualizar")
            return False
    
    def get_gesture_confidence(self, gesture_id=None):
        """Obtiene el nivel de confianza de un gesto específico.
        
        Args:
            gesture_id: ID del gesto a consultar. Si es None, devuelve todos los niveles de confianza.
            
        Returns:
            float o dict: Nivel de confianza del gesto o diccionario con todos los niveles.
        """
        with self._lock:
            if gesture_id is None:
                return self._gesture_confidence.copy()
            return self._gesture_confidence.get(gesture_id, 0.0)
    
    def get_camera_status(self):
        """Obtiene el estado actual de la cámara.
        
        Returns:
            dict: Estado de la cámara incluyendo resolución, FPS y estado de conexión.
        """
        status = {
            "connected": self.webcam is not None and self.webcam.isOpened(),
            "width": self._camera_width,
            "height": self._camera_height,
            "target_fps": self._target_fps,
            "camera_id": self._camera_id
        }
        
        if status["connected"]:
            status["actual_width"] = self.webcam.get(cv2.CAP_PROP_FRAME_WIDTH)
            status["actual_height"] = self.webcam.get(cv2.CAP_PROP_FRAME_HEIGHT)
            status["actual_fps"] = self.webcam.get(cv2.CAP_PROP_FPS)
        
        return status
    
    def get_available_gestures(self):
        """Obtiene la lista de gestos disponibles en la configuración.
        
        Returns:
            list: Lista de gestos disponibles con sus configuraciones.
        """
        return self._gesture_configs.get("gestures", [])
    
    def add_gesture_config(self, gesture_config):
        """Añade una nueva configuración de gesto.
        
        Args:
            gesture_config: Diccionario con la configuración del nuevo gesto.
            
        Returns:
            bool: True si se añadió correctamente, False en caso contrario.
        """
        required_fields = ["id", "name", "landmarks", "threshold", "action"]
        
        # Verificar campos requeridos
        for field in required_fields:
            if field not in gesture_config:
                self.logger.error(f"Campo requerido '{field}' no encontrado en la configuración del gesto")
                return False
        
        # Verificar que el ID no exista
        for gesture in self._gesture_configs.get("gestures", []):
            if gesture.get("id") == gesture_config["id"]:
                self.logger.error(f"Ya existe un gesto con ID '{gesture_config['id']}'")
                return False
        
        # Añadir nuevo gesto
        with self._lock:
            if "gestures" not in self._gesture_configs:
                self._gesture_configs["gestures"] = []
            
            self._gesture_configs["gestures"].append(gesture_config)
            
            # Guardar configuración actualizada
            try:
                config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                         "config", "GestureConfig.json")
                with open(config_path, 'w') as f:
                    json.dump(self._gesture_configs, f, indent=4)
                self.logger.info(f"Nuevo gesto '{gesture_config['id']}' añadido a la configuración")
                return True
            except Exception as e:
                self.logger.error(f"Error al guardar configuración: {e}")
                return False
    
    def remove_gesture_config(self, gesture_id):
        """Elimina una configuración de gesto.
        
        Args:
            gesture_id: ID del gesto a eliminar.
            
        Returns:
            bool: True si se eliminó correctamente, False en caso contrario.
        """
        with self._lock:
            for i, gesture in enumerate(self._gesture_configs.get("gestures", [])):
                if gesture.get("id") == gesture_id:
                    # Eliminar gesto
                    del self._gesture_configs["gestures"][i]
                    
                    # Guardar configuración actualizada
                    try:
                        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                                "config", "GestureConfig.json")
                        with open(config_path, 'w') as f:
                            json.dump(self._gesture_configs, f, indent=4)
                        self.logger.info(f"Gesto '{gesture_id}' eliminado de la configuración")
                        return True
                    except Exception as e:
                        self.logger.error(f"Error al guardar configuración: {e}")
                        return False
            
            self.logger.warning(f"Gesto '{gesture_id}' no encontrado para eliminar")
            return False