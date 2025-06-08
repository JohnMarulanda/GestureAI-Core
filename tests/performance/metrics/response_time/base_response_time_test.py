"""
Clase base para tests de tiempo de respuesta de controladores.
Mide latencia end-to-end y rendimiento por operación.
"""

import time
import threading
import numpy as np
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import cv2
import sys
import os

# Agregar path para imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from tests.performance.base_performance_test import BasePerformanceTest
from tests.performance.config.test_config import get_controller_config
from tests.performance.utils.metrics_utils import MetricsCalculator, MetricsVisualizer

class BaseResponseTimeTest(BasePerformanceTest):
    """
    Clase base para tests de tiempo de respuesta de controladores.
    
    Mide:
    - Tiempo de inicialización del controlador
    - Tiempo de procesamiento de frame
    - Tiempo de detección de gesto
    - Tiempo de ejecución de acción
    - Latencia end-to-end
    """
    
    def __init__(self, controller_class, controller_name: str):
        super().__init__()
        self.controller_class = controller_class
        self.controller_name = controller_name
        self.controller_instance = None
        
        # Configuración específica del controlador
        self.config = get_controller_config(controller_name)
        self.expected_response_time = self.config.get('expected_response_time', 0.1)
        
        # Métricas de tiempo
        self.initialization_time = 0
        self.frame_processing_times = []
        self.gesture_detection_times = []
        self.action_execution_times = []
        self.end_to_end_times = []
        
        # Estado del test
        self.test_frame = None
        self.gesture_detected = False
        self.action_completed = False
        
    def setUp(self):
        """Configuración inicial específica para tests de tiempo de respuesta"""
        super().setUp()
        
        # Crear frame de test sintético
        self.test_frame = self.create_synthetic_test_frame()
        
        # Inicializar métricas específicas
        self.initialization_time = 0
        self.frame_processing_times = []
        self.gesture_detection_times = []
        self.action_execution_times = []
        self.end_to_end_times = []
        
    def create_synthetic_test_frame(self) -> np.ndarray:
        """
        Crea un frame sintético para testing sin depender de cámara real
        
        Returns:
            Frame de test con mano simulada
        """
        # Crear frame base de 480x360 (tamaño típico del sistema)
        frame = np.zeros((360, 480, 3), dtype=np.uint8)
        
        # Simular fondo realista con ruido
        noise = np.random.randint(0, 50, frame.shape, dtype=np.uint8)
        frame = cv2.add(frame, noise)
        
        # Simular región de mano (color piel aproximado)
        skin_color = (150, 120, 100)  # BGR
        cv2.rectangle(frame, (200, 150), (350, 280), skin_color, -1)
        
        # Añadir algunos puntos de referencia para simular landmarks
        landmark_points = [
            (225, 175), (240, 180), (255, 185), (270, 190),  # Dedos
            (210, 200), (220, 210), (230, 220), (240, 230),  # Palma
            (280, 170), (290, 175), (300, 180), (310, 185),  # Otros dedos
            (320, 200), (330, 210), (340, 220), (345, 230),
            (200, 240), (210, 250), (220, 260), (230, 270), (240, 275)
        ]
        
        for point in landmark_points:
            cv2.circle(frame, point, 2, (0, 255, 0), -1)
        
        return frame
    
    def measure_initialization_time(self) -> float:
        """
        Mide el tiempo de inicialización del controlador
        
        Returns:
            Tiempo de inicialización en segundos
        """
        self.start_timer()
        
        try:
            self.controller_instance = self.controller_class()
            initialization_time = self.stop_timer()
            self.initialization_time = initialization_time
            
            self.log_metric("initialization_time", initialization_time, "s")
            return initialization_time
            
        except Exception as e:
            self.logger.error(f"Error en inicialización: {e}")
            return float('inf')
    
    def measure_frame_processing_time(self, frame: np.ndarray) -> float:
        """
        Mide el tiempo de procesamiento de un frame
        
        Args:
            frame: Frame a procesar
            
        Returns:
            Tiempo de procesamiento en segundos
        """
        if not self.controller_instance:
            return float('inf')
        
        self.start_timer()
        
        try:
            # Simular procesamiento de frame según el tipo de controlador
            if hasattr(self.controller_instance, 'hand_landmarker'):
                # Para controladores con MediaPipe
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                
                # Procesar frame con timestamp
                timestamp_ms = int(time.time() * 1000)
                self.controller_instance.hand_landmarker.detect_async(mp_image, timestamp_ms)
                
            processing_time = self.stop_timer()
            self.frame_processing_times.append(processing_time)
            
            return processing_time
            
        except Exception as e:
            self.logger.error(f"Error en procesamiento de frame: {e}")
            return float('inf')
    
    def measure_gesture_detection_time(self, gesture_input: str = "test_gesture") -> float:
        """
        Mide el tiempo de detección de gesto
        
        Args:
            gesture_input: Tipo de gesto a detectar
            
        Returns:
            Tiempo de detección en segundos
        """
        if not self.controller_instance:
            return float('inf')
        
        self.start_timer()
        
        try:
            # Simular detección de gesto específico según controlador
            if hasattr(self.controller_instance, 'detect_gesture'):
                # Simular fingers y landmarks para el test
                test_fingers = [1, 1, 0, 0, 0]  # Gesto de cursor típico
                test_landmarks = self.create_synthetic_landmarks()
                
                gesture = self.controller_instance.detect_gesture(test_fingers, test_landmarks)
                self.gesture_detected = gesture != 'none'
                
            elif hasattr(self.controller_instance, 'recognize_gesture'):
                # Para otros tipos de controladores
                gesture = self.controller_instance.recognize_gesture(gesture_input)
                self.gesture_detected = gesture is not None
                
            detection_time = self.stop_timer()
            self.gesture_detection_times.append(detection_time)
            
            return detection_time
            
        except Exception as e:
            self.logger.error(f"Error en detección de gesto: {e}")
            return float('inf')
    
    def measure_action_execution_time(self, action: str = "test_action") -> float:
        """
        Mide el tiempo de ejecución de una acción
        
        Args:
            action: Acción a ejecutar
            
        Returns:
            Tiempo de ejecución en segundos
        """
        if not self.controller_instance:
            return float('inf')
        
        self.start_timer()
        
        try:
            # Ejecutar acción específica según el controlador
            if self.controller_name == 'mouse_controller_enhanced':
                if action == "move_cursor":
                    landmarks = self.create_synthetic_landmarks()
                    self.controller_instance.move_cursor(landmarks)
                elif action == "left_click":
                    self.controller_instance.handle_left_click()
                elif action == "right_click":
                    self.controller_instance.handle_right_click()
                    
            elif self.controller_name == 'volume_controller_enhanced':
                if action == "volume_up":
                    if hasattr(self.controller_instance, 'increase_volume'):
                        self.controller_instance.increase_volume()
                elif action == "volume_down":
                    if hasattr(self.controller_instance, 'decrease_volume'):
                        self.controller_instance.decrease_volume()
                        
            # Para otros controladores, simular ejecución
            else:
                time.sleep(0.001)  # Simular tiempo mínimo de ejecución
            
            execution_time = self.stop_timer()
            self.action_execution_times.append(execution_time)
            self.action_completed = True
            
            return execution_time
            
        except Exception as e:
            self.logger.error(f"Error en ejecución de acción: {e}")
            return float('inf')
    
    def measure_end_to_end_latency(self, frame: np.ndarray, gesture: str, action: str) -> float:
        """
        Mide la latencia completa desde frame hasta acción ejecutada
        
        Args:
            frame: Frame de entrada
            gesture: Gesto a detectar
            action: Acción a ejecutar
            
        Returns:
            Latencia total en segundos
        """
        self.start_timer()
        
        try:
            # Secuencia completa: procesamiento -> detección -> ejecución
            self.measure_frame_processing_time(frame)
            self.measure_gesture_detection_time(gesture)
            self.measure_action_execution_time(action)
            
            total_latency = self.stop_timer()
            self.end_to_end_times.append(total_latency)
            
            return total_latency
            
        except Exception as e:
            self.logger.error(f"Error en latencia end-to-end: {e}")
            return float('inf')
    
    def create_synthetic_landmarks(self) -> List[Any]:
        """
        Crea landmarks sintéticos para testing
        
        Returns:
            Lista de landmarks simulados
        """
        # Simular 21 landmarks de MediaPipe para mano
        landmarks = []
        
        # Coordenadas base para una mano en posición estándar
        base_points = [
            (0.5, 0.7), (0.52, 0.65), (0.54, 0.6), (0.56, 0.55), (0.58, 0.5),  # Pulgar
            (0.45, 0.6), (0.43, 0.5), (0.41, 0.4), (0.39, 0.3),                # Índice
            (0.48, 0.6), (0.46, 0.45), (0.44, 0.35), (0.42, 0.25),             # Medio
            (0.51, 0.6), (0.49, 0.48), (0.47, 0.38), (0.45, 0.28),             # Anular
            (0.54, 0.62), (0.52, 0.52), (0.5, 0.42), (0.48, 0.32),             # Meñique
        ]
        
        # Crear objetos landmark simulados
        class MockLandmark:
            def __init__(self, x, y, z=0):
                self.x = x
                self.y = y
                self.z = z
        
        landmarks = [MockLandmark(x, y) for x, y in base_points]
        
        return landmarks
    
    def run_performance_test(self) -> Dict[str, Any]:
        """
        Ejecuta el test de rendimiento específico de tiempo de respuesta
        
        Returns:
            Diccionario con resultados del test
        """
        results = {
            'test_type': 'response_time',
            'controller': self.controller_name,
            'timestamp': datetime.now().isoformat(),
            'success': False
        }
        
        try:
            # 1. Medir inicialización
            init_time = self.measure_initialization_time()
            
            # 2. Medir procesamiento de frames (múltiples iteraciones)
            frame_times = []
            for i in range(10):
                frame_time = self.measure_frame_processing_time(self.test_frame)
                if frame_time != float('inf'):
                    frame_times.append(frame_time)
            
            # 3. Medir detección de gestos
            gesture_times = []
            test_gestures = self.config.get('test_gestures', ['test_gesture'])
            for gesture in test_gestures[:5]:  # Limitar a 5 gestos
                detection_time = self.measure_gesture_detection_time(gesture)
                if detection_time != float('inf'):
                    gesture_times.append(detection_time)
            
            # 4. Medir ejecución de acciones
            action_times = []
            critical_functions = self.config.get('critical_functions', ['test_action'])
            for action in critical_functions[:3]:  # Limitar a 3 acciones
                execution_time = self.measure_action_execution_time(action)
                if execution_time != float('inf'):
                    action_times.append(execution_time)
            
            # 5. Medir latencia end-to-end
            e2e_times = []
            for i in range(5):
                e2e_time = self.measure_end_to_end_latency(
                    self.test_frame, 
                    test_gestures[0] if test_gestures else 'test',
                    critical_functions[0] if critical_functions else 'test'
                )
                if e2e_time != float('inf'):
                    e2e_times.append(e2e_time)
            
            # Calcular estadísticas
            results.update({
                'initialization_time': init_time,
                'frame_processing': {
                    'times': frame_times,
                    'mean': np.mean(frame_times) if frame_times else 0,
                    'std': np.std(frame_times) if frame_times else 0,
                    'min': np.min(frame_times) if frame_times else 0,
                    'max': np.max(frame_times) if frame_times else 0
                },
                'gesture_detection': {
                    'times': gesture_times,
                    'mean': np.mean(gesture_times) if gesture_times else 0,
                    'std': np.std(gesture_times) if gesture_times else 0
                },
                'action_execution': {
                    'times': action_times,
                    'mean': np.mean(action_times) if action_times else 0,
                    'std': np.std(action_times) if action_times else 0
                },
                'end_to_end_latency': {
                    'times': e2e_times,
                    'mean': np.mean(e2e_times) if e2e_times else 0,
                    'std': np.std(e2e_times) if e2e_times else 0,
                    'percentile_95': np.percentile(e2e_times, 95) if e2e_times else 0
                },
                'meets_expectations': {
                    'expected_time': self.expected_response_time,
                    'actual_mean': np.mean(e2e_times) if e2e_times else float('inf'),
                    'passes': np.mean(e2e_times) <= self.expected_response_time if e2e_times else False
                },
                'success': True
            })
            
            # Log resultados principales
            if e2e_times:
                self.log_metric("mean_e2e_latency", np.mean(e2e_times) * 1000, "ms")
                self.log_metric("p95_e2e_latency", np.percentile(e2e_times, 95) * 1000, "ms")
            
        except Exception as e:
            self.logger.error(f"Error en test de rendimiento: {e}")
            results['error'] = str(e)
        
        finally:
            # Cleanup
            if self.controller_instance:
                try:
                    if hasattr(self.controller_instance, 'stop_camera'):
                        self.controller_instance.stop_camera()
                except:
                    pass
        
        return results 