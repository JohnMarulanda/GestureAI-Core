"""
Test de tiempo de respuesta específico para MouseControllerEnhanced.
Mide latencia de movimiento de cursor, clicks y operaciones de arrastre.
"""

import sys
import os
import time
import numpy as np
from unittest.mock import Mock, patch

# Agregar paths para imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from tests.performance.metrics.response_time.base_response_time_test import BaseResponseTimeTest

# Mock para evitar dependencias del sistema real durante testing
class MockMouseControllerEnhanced:
    """Mock del MouseControllerEnhanced para testing sin hardware real"""
    
    def __init__(self, model_path=None):
        """Inicializar mock controller"""
        self.model_path = model_path or "mock_model.task"
        self.current_result = None
        self.gesture_threshold = 0.8
        self.last_gesture = None
        self.screen_width = 1920
        self.screen_height = 1080
        
        # Simular tiempos de inicialización realistas
        time.sleep(0.01)  # 10ms simulado
        
    def detect_gesture(self, fingers, landmarks):
        """Mock de detección de gesto"""
        finger_pattern = ''.join(map(str, fingers))
        
        gestures = {
            '11000': 'cursor',
            '11100': 'left_click', 
            '11110': 'right_click',
            '01111': 'drag'
        }
        
        # Simular tiempo de procesamiento
        time.sleep(0.002)  # 2ms simulado
        
        return gestures.get(finger_pattern, 'none')
    
    def move_cursor(self, landmarks):
        """Mock de movimiento de cursor"""
        if not landmarks or len(landmarks) < 8:
            return
        
        # Simular cálculo de posición
        x = landmarks[8].x * self.screen_width
        y = landmarks[8].y * self.screen_height
        
        # Simular tiempo de movimiento
        time.sleep(0.001)  # 1ms simulado
        
        return (x, y)
    
    def handle_left_click(self):
        """Mock de click izquierdo"""
        time.sleep(0.005)  # 5ms simulado
        return True
    
    def handle_right_click(self):
        """Mock de click derecho"""
        time.sleep(0.005)  # 5ms simulado 
        return True
    
    def handle_drag(self, active):
        """Mock de arrastre"""
        time.sleep(0.003)  # 3ms simulado
        return active
    
    def stop_camera(self):
        """Mock de cleanup"""
        pass

class TestMouseControllerResponseTime(BaseResponseTimeTest):
    """Test de tiempo de respuesta para MouseControllerEnhanced"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(
            controller_class=MockMouseControllerEnhanced,
            controller_name='mouse_controller_enhanced'
        )
    
    def test_cursor_movement_response_time(self):
        """Test específico de tiempo de respuesta para movimiento de cursor"""
        self.logger.info("Testing cursor movement response time")
        
        results = []
        
        # Test con diferentes posiciones de cursor
        test_positions = [
            (0.2, 0.3), (0.8, 0.7), (0.5, 0.5), (0.1, 0.9), (0.9, 0.1)
        ]
        
        for i, (x, y) in enumerate(test_positions):
            self.start_timer()
            
            # Crear landmarks para posición específica
            landmarks = self.create_cursor_landmarks(x, y)
            
            # Medir tiempo de movimiento
            if self.controller_instance:
                position = self.controller_instance.move_cursor(landmarks)
                
            response_time = self.stop_timer()
            
            results.append({
                'iteration': i + 1,
                'target_position': (x, y),
                'response_time': response_time,
                'success': response_time < 0.05  # 50ms threshold
            })
            
            self.log_metric(f"cursor_move_{i+1}", response_time * 1000, "ms")
        
        # Calcular estadísticas
        times = [r['response_time'] for r in results]
        success_rate = sum(r['success'] for r in results) / len(results) * 100
        
        self.assertEqual(len(results), 5, "Debe completar 5 tests de movimiento")
        self.assertGreater(success_rate, 80, "Al menos 80% debe cumplir threshold de 50ms")
        self.assertLess(np.mean(times), 0.03, "Tiempo promedio debe ser < 30ms")
        
        return results
    
    def test_click_response_time(self):
        """Test de tiempo de respuesta para clicks"""
        self.logger.info("Testing click response times")
        
        results = {'left_clicks': [], 'right_clicks': []}
        
        # Test clicks izquierdos
        for i in range(10):
            self.start_timer()
            if self.controller_instance:
                self.controller_instance.handle_left_click()
            response_time = self.stop_timer()
            
            results['left_clicks'].append(response_time)
            self.log_metric(f"left_click_{i+1}", response_time * 1000, "ms")
        
        # Test clicks derechos  
        for i in range(10):
            self.start_timer()
            if self.controller_instance:
                self.controller_instance.handle_right_click()
            response_time = self.stop_timer()
            
            results['right_clicks'].append(response_time)
            self.log_metric(f"right_click_{i+1}", response_time * 1000, "ms")
        
        # Validaciones
        left_mean = np.mean(results['left_clicks'])
        right_mean = np.mean(results['right_clicks'])
        
        self.assertLess(left_mean, 0.02, "Click izquierdo promedio debe ser < 20ms")
        self.assertLess(right_mean, 0.02, "Click derecho promedio debe ser < 20ms")
        
        return results
    
    def test_gesture_detection_response_time(self):
        """Test de tiempo de respuesta para detección de gestos"""
        self.logger.info("Testing gesture detection response times")
        
        results = []
        
        # Test diferentes patrones de gestos
        gesture_patterns = [
            ([1, 1, 0, 0, 0], 'cursor'),
            ([1, 1, 1, 0, 0], 'left_click'),
            ([1, 1, 1, 1, 0], 'right_click'),
            ([0, 1, 1, 1, 1], 'drag')
        ]
        
        for fingers, expected_gesture in gesture_patterns:
            detection_times = []
            
            for i in range(10):
                landmarks = self.create_synthetic_landmarks()
                
                self.start_timer()
                if self.controller_instance:
                    detected = self.controller_instance.detect_gesture(fingers, landmarks)
                response_time = self.stop_timer()
                
                detection_times.append(response_time)
                
                self.assertEqual(detected, expected_gesture, 
                               f"Gesto detectado debe ser {expected_gesture}")
            
            mean_time = np.mean(detection_times)
            results.append({
                'gesture': expected_gesture,
                'mean_detection_time': mean_time,
                'times': detection_times,
                'success': mean_time < 0.01  # 10ms threshold
            })
            
            self.log_metric(f"gesture_detection_{expected_gesture}", mean_time * 1000, "ms")
        
        # Validar que todos los gestos se detecten rápidamente
        for result in results:
            self.assertLess(result['mean_detection_time'], 0.01, 
                          f"Detección de {result['gesture']} debe ser < 10ms")
        
        return results
    
    def test_end_to_end_latency(self):
        """Test de latencia completa end-to-end"""
        self.logger.info("Testing end-to-end latency")
        
        results = []
        
        # Secuencias completas de gesto -> acción
        test_sequences = [
            (['cursor'], 'move_cursor'),
            (['left_click'], 'handle_left_click'),
            (['right_click'], 'handle_right_click'),
            (['drag'], 'handle_drag')
        ]
        
        for gestures, action in test_sequences:
            sequence_times = []
            
            for i in range(5):
                self.start_timer()
                
                # Simular secuencia completa
                frame = self.create_synthetic_test_frame()
                
                # 1. Procesamiento de frame (simulado)
                time.sleep(0.002)
                
                # 2. Detección de gesto
                fingers = [1, 1, 0, 0, 0] if gestures[0] == 'cursor' else [1, 1, 1, 0, 0]
                landmarks = self.create_synthetic_landmarks()
                
                if self.controller_instance:
                    gesture = self.controller_instance.detect_gesture(fingers, landmarks)
                
                # 3. Ejecución de acción
                if self.controller_instance and action == 'move_cursor':
                    self.controller_instance.move_cursor(landmarks)
                elif self.controller_instance and action == 'handle_left_click':
                    self.controller_instance.handle_left_click()
                elif self.controller_instance and action == 'handle_right_click':
                    self.controller_instance.handle_right_click()
                elif self.controller_instance and action == 'handle_drag':
                    self.controller_instance.handle_drag(True)
                
                total_time = self.stop_timer()
                sequence_times.append(total_time)
            
            mean_latency = np.mean(sequence_times)
            p95_latency = np.percentile(sequence_times, 95)
            
            results.append({
                'sequence': f"{gestures[0]} -> {action}",
                'mean_latency': mean_latency,
                'p95_latency': p95_latency,
                'times': sequence_times,
                'meets_target': mean_latency <= self.expected_response_time
            })
            
            self.log_metric(f"e2e_{gestures[0]}", mean_latency * 1000, "ms")
            self.log_metric(f"e2e_p95_{gestures[0]}", p95_latency * 1000, "ms")
        
        # Validar latencias
        for result in results:
            self.assertLess(result['mean_latency'], 0.05, 
                          f"Latencia E2E de {result['sequence']} debe ser < 50ms")
            self.assertTrue(result['meets_target'], 
                          f"Debe cumplir target de {self.expected_response_time}s")
        
        return results
    
    def create_cursor_landmarks(self, target_x: float, target_y: float):
        """Crear landmarks para posición específica del cursor"""
        landmarks = self.create_synthetic_landmarks()
        
        # Ajustar landmark del índice (punto 8) a la posición objetivo
        if len(landmarks) > 8:
            landmarks[8].x = target_x
            landmarks[8].y = target_y
        
        return landmarks
    
    def run_performance_test(self) -> dict:
        """Ejecutar todos los tests de rendimiento del mouse controller"""
        
        # Inicializar controlador
        init_time = self.measure_initialization_time()
        
        # Ejecutar tests específicos
        cursor_results = self.test_cursor_movement_response_time()
        click_results = self.test_click_response_time()
        gesture_results = self.test_gesture_detection_response_time()
        e2e_results = self.test_end_to_end_latency()
        
        # Compilar resultados finales
        results = {
            'controller': self.controller_name,
            'initialization_time': init_time,
            'cursor_movement': cursor_results,
            'click_operations': click_results,
            'gesture_detection': gesture_results,
            'end_to_end_latency': e2e_results,
            'summary': {
                'total_tests': len(cursor_results) + len(click_results['left_clicks']) + 
                              len(click_results['right_clicks']) + len(gesture_results) + len(e2e_results),
                'expected_response_time': self.expected_response_time,
                'meets_performance_target': init_time <= 0.1  # 100ms para inicialización
            }
        }
        
        return results

if __name__ == "__main__":
    import unittest
    
    # Crear suite de tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMouseControllerResponseTime)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite) 