"""
Test de tiempo de respuesta específico para NavigationControllerEnhanced.
Mide latencia de navegación, swipes, zoom y operaciones de scrolling.
"""

import sys
import os
import time
import numpy as np
from unittest.mock import Mock, patch

# Agregar paths para imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from tests.performance.metrics.response_time.base_response_time_test import BaseResponseTimeTest

class MockNavigationControllerEnhanced:
    """Mock del NavigationControllerEnhanced para testing"""
    
    def __init__(self):
        """Inicializar mock controller"""
        self.current_page = 0
        self.zoom_level = 100  # Porcentaje
        self.scroll_position = 0
        self.gesture_threshold = 0.8
        
        # Simular tiempo de inicialización
        time.sleep(0.008)  # 8ms simulado
        
    def detect_gesture(self, fingers, landmarks):
        """Mock de detección de gestos de navegación"""
        finger_pattern = ''.join(map(str, fingers))
        
        # Analizar también la dirección del movimiento basado en landmarks
        if len(landmarks) >= 8:
            index_tip = landmarks[8]
            # Simular detección direccional
            
        gestures = {
            '01100': 'swipe_left',    # Índice + medio
            '00110': 'swipe_right',   # Medio + anular  
            '01000': 'swipe_up',      # Solo índice hacia arriba
            '00100': 'swipe_down',    # Solo medio hacia abajo
            '11000': 'zoom_in',       # Pulgar + índice (pellizcar)
            '10100': 'zoom_out',      # Pulgar + medio (separar)
            '01110': 'scroll'         # Tres dedos para scroll
        }
        
        # Simular tiempo de procesamiento
        time.sleep(0.003)  # 3ms simulado
        
        return gestures.get(finger_pattern, 'none')
    
    def swipe_left(self, distance=100):
        """Mock de swipe hacia la izquierda"""
        # Simular tiempo de operación de navegación
        time.sleep(0.008)  # 8ms simulado
        
        self.current_page = max(0, self.current_page - 1)
        return self.current_page
    
    def swipe_right(self, distance=100):
        """Mock de swipe hacia la derecha"""
        # Simular tiempo de operación de navegación
        time.sleep(0.008)  # 8ms simulado
        
        self.current_page += 1
        return self.current_page
    
    def swipe_up(self, distance=100):
        """Mock de swipe hacia arriba"""
        # Simular tiempo de scroll
        time.sleep(0.006)  # 6ms simulado
        
        self.scroll_position += distance
        return self.scroll_position
    
    def swipe_down(self, distance=100):
        """Mock de swipe hacia abajo"""
        # Simular tiempo de scroll
        time.sleep(0.006)  # 6ms simulado
        
        self.scroll_position = max(0, self.scroll_position - distance)
        return self.scroll_position
    
    def zoom_in(self, factor=1.2):
        """Mock de zoom in"""
        # Simular tiempo de operación de zoom
        time.sleep(0.010)  # 10ms simulado
        
        self.zoom_level = min(500, self.zoom_level * factor)
        return self.zoom_level
    
    def zoom_out(self, factor=0.8):
        """Mock de zoom out"""
        # Simular tiempo de operación de zoom
        time.sleep(0.010)  # 10ms simulado
        
        self.zoom_level = max(25, self.zoom_level * factor)
        return self.zoom_level
    
    def navigate_back(self):
        """Mock de navegación hacia atrás"""
        time.sleep(0.015)  # 15ms simulado (más lento por IO)
        return True
    
    def navigate_forward(self):
        """Mock de navegación hacia adelante"""
        time.sleep(0.015)  # 15ms simulado
        return True

class TestNavigationControllerResponseTime(BaseResponseTimeTest):
    """Test de tiempo de respuesta para NavigationControllerEnhanced"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(
            controller_class=MockNavigationControllerEnhanced,
            controller_name='navigation_controller_enhanced'
        )
    
    def test_swipe_response_time(self):
        """Test de tiempo de respuesta para operaciones de swipe"""
        self.logger.info("Testing swipe operations response time")
        
        results = {
            'swipe_left': [],
            'swipe_right': [], 
            'swipe_up': [],
            'swipe_down': []
        }
        
        # Test swipe left
        for i in range(8):
            self.start_timer()
            if self.controller_instance:
                page = self.controller_instance.swipe_left()
            response_time = self.stop_timer()
            
            results['swipe_left'].append({
                'iteration': i + 1,
                'response_time': response_time,
                'result_page': page if self.controller_instance else 0,
                'success': response_time < 0.02  # 20ms threshold
            })
            
            self.log_metric(f"swipe_left_{i+1}", response_time * 1000, "ms")
        
        # Test swipe right
        for i in range(8):
            self.start_timer()
            if self.controller_instance:
                page = self.controller_instance.swipe_right()
            response_time = self.stop_timer()
            
            results['swipe_right'].append({
                'iteration': i + 1,
                'response_time': response_time,
                'result_page': page if self.controller_instance else 0,
                'success': response_time < 0.02  # 20ms threshold
            })
            
            self.log_metric(f"swipe_right_{i+1}", response_time * 1000, "ms")
        
        # Test swipe up/down (scrolling)
        for i in range(5):
            self.start_timer()
            if self.controller_instance:
                pos = self.controller_instance.swipe_up()
            response_time = self.stop_timer()
            
            results['swipe_up'].append({
                'iteration': i + 1,
                'response_time': response_time,
                'scroll_position': pos if self.controller_instance else 0,
                'success': response_time < 0.015  # 15ms threshold
            })
            
            self.log_metric(f"swipe_up_{i+1}", response_time * 1000, "ms")
        
        for i in range(5):
            self.start_timer()
            if self.controller_instance:
                pos = self.controller_instance.swipe_down()
            response_time = self.stop_timer()
            
            results['swipe_down'].append({
                'iteration': i + 1,
                'response_time': response_time,
                'scroll_position': pos if self.controller_instance else 0,
                'success': response_time < 0.015  # 15ms threshold
            })
            
            self.log_metric(f"swipe_down_{i+1}", response_time * 1000, "ms")
        
        # Validaciones
        for direction in results:
            times = [r['response_time'] for r in results[direction]]
            mean_time = np.mean(times)
            success_rate = sum(r['success'] for r in results[direction]) / len(results[direction]) * 100
            
            threshold = 0.02 if 'left' in direction or 'right' in direction else 0.015
            self.assertLess(mean_time, threshold, 
                          f"Tiempo promedio de {direction} debe ser < {threshold*1000}ms")
            self.assertGreater(success_rate, 85, 
                             f"Al menos 85% de {direction} debe cumplir threshold")
        
        return results
    
    def test_zoom_response_time(self):
        """Test de tiempo de respuesta para operaciones de zoom"""
        self.logger.info("Testing zoom operations response time")
        
        results = {'zoom_in': [], 'zoom_out': []}
        
        # Test zoom in
        for i in range(10):
            self.start_timer()
            if self.controller_instance:
                zoom_level = self.controller_instance.zoom_in()
            response_time = self.stop_timer()
            
            results['zoom_in'].append({
                'iteration': i + 1,
                'response_time': response_time,
                'zoom_level': zoom_level if self.controller_instance else 100,
                'success': response_time < 0.025  # 25ms threshold
            })
            
            self.log_metric(f"zoom_in_{i+1}", response_time * 1000, "ms")
        
        # Test zoom out
        for i in range(10):
            self.start_timer()
            if self.controller_instance:
                zoom_level = self.controller_instance.zoom_out()
            response_time = self.stop_timer()
            
            results['zoom_out'].append({
                'iteration': i + 1,
                'response_time': response_time,
                'zoom_level': zoom_level if self.controller_instance else 100,
                'success': response_time < 0.025  # 25ms threshold
            })
            
            self.log_metric(f"zoom_out_{i+1}", response_time * 1000, "ms")
        
        # Validaciones
        zoom_in_times = [r['response_time'] for r in results['zoom_in']]
        zoom_out_times = [r['response_time'] for r in results['zoom_out']]
        
        self.assertLess(np.mean(zoom_in_times), 0.025, "Zoom in promedio debe ser < 25ms")
        self.assertLess(np.mean(zoom_out_times), 0.025, "Zoom out promedio debe ser < 25ms")
        
        success_rate_in = sum(r['success'] for r in results['zoom_in']) / len(results['zoom_in']) * 100
        success_rate_out = sum(r['success'] for r in results['zoom_out']) / len(results['zoom_out']) * 100
        
        self.assertGreater(success_rate_in, 80, "Al menos 80% de zoom in debe cumplir threshold")
        self.assertGreater(success_rate_out, 80, "Al menos 80% de zoom out debe cumplir threshold")
        
        return results
    
    def test_gesture_detection_response_time(self):
        """Test de tiempo de respuesta para detección de gestos de navegación"""
        self.logger.info("Testing navigation gesture detection response times")
        
        results = []
        
        # Test diferentes patrones de gestos de navegación
        gesture_patterns = [
            ([0, 1, 1, 0, 0], 'swipe_left'),
            ([0, 0, 1, 1, 0], 'swipe_right'),
            ([0, 1, 0, 0, 0], 'swipe_up'),
            ([0, 0, 1, 0, 0], 'swipe_down'),
            ([1, 1, 0, 0, 0], 'zoom_in'),
            ([1, 0, 1, 0, 0], 'zoom_out'),
            ([0, 1, 1, 1, 0], 'scroll')
        ]
        
        for fingers, expected_gesture in gesture_patterns:
            detection_times = []
            
            for i in range(8):
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
                'success': mean_time < 0.008  # 8ms threshold
            })
            
            self.log_metric(f"gesture_detection_{expected_gesture}", mean_time * 1000, "ms")
        
        # Validar tiempos de detección
        for result in results:
            self.assertLess(result['mean_detection_time'], 0.008, 
                          f"Detección de {result['gesture']} debe ser < 8ms")
        
        return results
    
    def test_navigation_latency(self):
        """Test de latencia para operaciones de navegación"""
        self.logger.info("Testing navigation operations latency")
        
        results = []
        
        # Test operaciones de navegación (más lentas por IO)
        navigation_ops = ['navigate_back', 'navigate_forward']
        
        for op in navigation_ops:
            op_times = []
            
            for i in range(5):
                self.start_timer()
                if self.controller_instance and hasattr(self.controller_instance, op):
                    success = getattr(self.controller_instance, op)()
                response_time = self.stop_timer()
                
                op_times.append(response_time)
            
            mean_time = np.mean(op_times)
            results.append({
                'operation': op,
                'mean_time': mean_time,
                'times': op_times,
                'success': mean_time < 0.05  # 50ms threshold para navegación
            })
            
            self.log_metric(f"navigation_{op}", mean_time * 1000, "ms")
        
        # Validar latencias de navegación
        for result in results:
            self.assertLess(result['mean_time'], 0.05, 
                          f"Navegación {result['operation']} debe ser < 50ms")
        
        return results
    
    def test_end_to_end_latency(self):
        """Test de latencia completa end-to-end para operaciones de navegación"""
        self.logger.info("Testing navigation end-to-end latency")
        
        results = []
        
        # Secuencias completas de gesto -> acción
        test_sequences = [
            ('swipe_left', 'swipe_left'),
            ('swipe_right', 'swipe_right'),
            ('swipe_up', 'swipe_up'),
            ('zoom_in', 'zoom_in'),
            ('zoom_out', 'zoom_out')
        ]
        
        for gesture, action in test_sequences:
            sequence_times = []
            
            for i in range(5):
                self.start_timer()
                
                # Simular secuencia completa
                # 1. Procesamiento de frame
                time.sleep(0.002)
                
                # 2. Detección de gesto
                if gesture == 'swipe_left':
                    fingers = [0, 1, 1, 0, 0]
                elif gesture == 'swipe_right':
                    fingers = [0, 0, 1, 1, 0]
                elif gesture == 'swipe_up':
                    fingers = [0, 1, 0, 0, 0]
                elif gesture == 'zoom_in':
                    fingers = [1, 1, 0, 0, 0]
                else:  # zoom_out
                    fingers = [1, 0, 1, 0, 0]
                
                landmarks = self.create_synthetic_landmarks()
                
                if self.controller_instance:
                    detected_gesture = self.controller_instance.detect_gesture(fingers, landmarks)
                
                # 3. Ejecución de acción
                if self.controller_instance:
                    if action == 'swipe_left':
                        self.controller_instance.swipe_left()
                    elif action == 'swipe_right':
                        self.controller_instance.swipe_right()
                    elif action == 'swipe_up':
                        self.controller_instance.swipe_up()
                    elif action == 'zoom_in':
                        self.controller_instance.zoom_in()
                    elif action == 'zoom_out':
                        self.controller_instance.zoom_out()
                
                total_time = self.stop_timer()
                sequence_times.append(total_time)
            
            mean_latency = np.mean(sequence_times)
            p95_latency = np.percentile(sequence_times, 95)
            
            results.append({
                'sequence': f"{gesture} -> {action}",
                'mean_latency': mean_latency,
                'p95_latency': p95_latency,
                'times': sequence_times,
                'meets_target': mean_latency <= self.expected_response_time
            })
            
            self.log_metric(f"e2e_{gesture}", mean_latency * 1000, "ms")
            self.log_metric(f"e2e_p95_{gesture}", p95_latency * 1000, "ms")
        
        # Validar latencias
        for result in results:
            self.assertLess(result['mean_latency'], 0.05, 
                          f"Latencia E2E de {result['sequence']} debe ser < 50ms")
            self.assertTrue(result['meets_target'], 
                          f"Debe cumplir target de {self.expected_response_time}s")
        
        return results
    
    def run_performance_test(self) -> dict:
        """Ejecutar todos los tests de rendimiento del navigation controller"""
        
        # Inicializar controlador
        init_time = self.measure_initialization_time()
        
        # Ejecutar tests específicos
        swipe_results = self.test_swipe_response_time()
        zoom_results = self.test_zoom_response_time()
        gesture_results = self.test_gesture_detection_response_time()
        navigation_results = self.test_navigation_latency()
        e2e_results = self.test_end_to_end_latency()
        
        # Compilar resultados finales
        results = {
            'controller': self.controller_name,
            'initialization_time': init_time,
            'swipe_operations': swipe_results,
            'zoom_operations': zoom_results,
            'gesture_detection': gesture_results,
            'navigation_operations': navigation_results,
            'end_to_end_latency': e2e_results,
            'summary': {
                'total_tests': (sum(len(swipe_results[k]) for k in swipe_results) +
                              len(zoom_results['zoom_in']) + len(zoom_results['zoom_out']) +
                              len(gesture_results) + len(navigation_results) + len(e2e_results)),
                'expected_response_time': self.expected_response_time,
                'meets_performance_target': init_time <= 0.02,  # 20ms para inicialización
                'target_achieved': all(r['meets_target'] for r in e2e_results)
            }
        }
        
        return results

if __name__ == "__main__":
    import unittest
    
    # Crear suite de tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestNavigationControllerResponseTime)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite) 