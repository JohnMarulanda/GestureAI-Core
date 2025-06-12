"""
Test de tiempo de respuesta específico para VolumeControllerEnhanced.
Mide latencia de cambios de volumen, mute/unmute y operaciones de audio.
"""

import sys
import os
import time
import numpy as np
from unittest.mock import Mock, patch

# Agregar paths para imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from tests.performance.metrics.response_time.base_response_time_test import BaseResponseTimeTest

class MockVolumeControllerEnhanced:
    """Mock del VolumeControllerEnhanced para testing"""
    
    def __init__(self):
        """Inicializar mock controller"""
        self.current_volume = 50  # Volumen inicial 50%
        self.is_muted = False
        self.volume_step = 5
        self.max_volume = 100
        self.min_volume = 0
        
        # Simular tiempo de inicialización
        time.sleep(0.005)  # 5ms simulado
        
    def detect_gesture(self, fingers, landmarks):
        """Mock de detección de gesto de volumen"""
        finger_pattern = ''.join(map(str, fingers))
        
        gestures = {
            '10000': 'volume_up',     # Solo pulgar
            '01000': 'volume_down',   # Solo índice
            '11000': 'mute',          # Pulgar + índice
            '00000': 'unmute'         # Ningún dedo (mano cerrada)
        }
        
        # Simular tiempo de procesamiento de gesto
        time.sleep(0.001)  # 1ms simulado
        
        return gestures.get(finger_pattern, 'none')
    
    def increase_volume(self, amount=None):
        """Mock de aumento de volumen"""
        amount = amount or self.volume_step
        
        # Simular tiempo de operación del sistema
        time.sleep(0.003)  # 3ms simulado
        
        self.current_volume = min(self.max_volume, self.current_volume + amount)
        return self.current_volume
    
    def decrease_volume(self, amount=None):
        """Mock de disminución de volumen"""
        amount = amount or self.volume_step
        
        # Simular tiempo de operación del sistema
        time.sleep(0.003)  # 3ms simulado
        
        self.current_volume = max(self.min_volume, self.current_volume - amount)
        return self.current_volume
    
    def mute_toggle(self):
        """Mock de toggle mute"""
        # Simular tiempo de operación del sistema
        time.sleep(0.002)  # 2ms simulado
        
        self.is_muted = not self.is_muted
        return self.is_muted
    
    def set_volume(self, level):
        """Mock de establecer volumen específico"""
        # Simular tiempo de operación del sistema
        time.sleep(0.004)  # 4ms simulado
        
        self.current_volume = max(self.min_volume, min(self.max_volume, level))
        return self.current_volume
    
    def get_volume(self):
        """Mock de obtener volumen actual"""
        time.sleep(0.001)  # 1ms simulado
        return self.current_volume

class TestVolumeControllerResponseTime(BaseResponseTimeTest):
    """Test de tiempo de respuesta para VolumeControllerEnhanced"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(
            controller_class=MockVolumeControllerEnhanced,
            controller_name='volume_controller_enhanced'
        )
    
    def test_volume_change_response_time(self):
        """Test de tiempo de respuesta para cambios de volumen"""
        self.logger.info("Testing volume change response time")
        
        results = {'increase': [], 'decrease': []}
        
        # Test aumento de volumen
        for i in range(10):
            self.start_timer()
            if self.controller_instance:
                new_volume = self.controller_instance.increase_volume()
            response_time = self.stop_timer()
            
            results['increase'].append({
                'iteration': i + 1,
                'response_time': response_time,
                'new_volume': new_volume if self.controller_instance else 0,
                'success': response_time < 0.01  # 10ms threshold
            })
            
            self.log_metric(f"volume_increase_{i+1}", response_time * 1000, "ms")
        
        # Test disminución de volumen
        for i in range(10):
            self.start_timer()
            if self.controller_instance:
                new_volume = self.controller_instance.decrease_volume()
            response_time = self.stop_timer()
            
            results['decrease'].append({
                'iteration': i + 1,
                'response_time': response_time,
                'new_volume': new_volume if self.controller_instance else 0,
                'success': response_time < 0.01  # 10ms threshold
            })
            
            self.log_metric(f"volume_decrease_{i+1}", response_time * 1000, "ms")
        
        # Calcular estadísticas
        increase_times = [r['response_time'] for r in results['increase']]
        decrease_times = [r['response_time'] for r in results['decrease']]
        
        increase_mean = np.mean(increase_times)
        decrease_mean = np.mean(decrease_times)
        
        # Validaciones
        self.assertLess(increase_mean, 0.01, "Aumento de volumen promedio debe ser < 10ms")
        self.assertLess(decrease_mean, 0.01, "Disminución de volumen promedio debe ser < 10ms")
        
        success_rate_inc = sum(r['success'] for r in results['increase']) / len(results['increase']) * 100
        success_rate_dec = sum(r['success'] for r in results['decrease']) / len(results['decrease']) * 100
        
        self.assertGreater(success_rate_inc, 90, "Al menos 90% de aumentos debe cumplir threshold")
        self.assertGreater(success_rate_dec, 90, "Al menos 90% de disminuciones debe cumplir threshold")
        
        return results
    
    def test_mute_toggle_response_time(self):
        """Test de tiempo de respuesta para mute/unmute"""
        self.logger.info("Testing mute toggle response time")
        
        results = []
        
        # Test múltiples toggles de mute
        for i in range(10):
            self.start_timer()
            if self.controller_instance:
                mute_state = self.controller_instance.mute_toggle()
            response_time = self.stop_timer()
            
            results.append({
                'iteration': i + 1,
                'response_time': response_time,
                'mute_state': mute_state if self.controller_instance else False,
                'success': response_time < 0.005  # 5ms threshold para mute
            })
            
            self.log_metric(f"mute_toggle_{i+1}", response_time * 1000, "ms")
        
        # Validaciones
        times = [r['response_time'] for r in results]
        mean_time = np.mean(times)
        success_rate = sum(r['success'] for r in results) / len(results) * 100
        
        self.assertLess(mean_time, 0.005, "Mute toggle promedio debe ser < 5ms")
        self.assertGreater(success_rate, 95, "Al menos 95% debe cumplir threshold de 5ms")
        
        return results
    
    def test_gesture_detection_response_time(self):
        """Test de tiempo de respuesta para detección de gestos de volumen"""
        self.logger.info("Testing volume gesture detection response times")
        
        results = []
        
        # Test diferentes patrones de gestos de volumen
        gesture_patterns = [
            ([1, 0, 0, 0, 0], 'volume_up'),
            ([0, 1, 0, 0, 0], 'volume_down'),
            ([1, 1, 0, 0, 0], 'mute'),
            ([0, 0, 0, 0, 0], 'unmute')
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
                'success': mean_time < 0.003  # 3ms threshold
            })
            
            self.log_metric(f"gesture_detection_{expected_gesture}", mean_time * 1000, "ms")
        
        # Validar tiempos de detección
        for result in results:
            self.assertLess(result['mean_detection_time'], 0.003, 
                          f"Detección de {result['gesture']} debe ser < 3ms")
        
        return results
    
    def test_volume_precision_response_time(self):
        """Test de tiempo de respuesta para cambios precisos de volumen"""
        self.logger.info("Testing volume precision response time")
        
        results = []
        
        # Test establecer volúmenes específicos
        target_volumes = [0, 25, 50, 75, 100]
        
        for target in target_volumes:
            self.start_timer()
            if self.controller_instance:
                final_volume = self.controller_instance.set_volume(target)
            response_time = self.stop_timer()
            
            results.append({
                'target_volume': target,
                'final_volume': final_volume if self.controller_instance else 0,
                'response_time': response_time,
                'accuracy': final_volume == target if self.controller_instance else False,
                'success': response_time < 0.008  # 8ms threshold
            })
            
            self.log_metric(f"set_volume_{target}", response_time * 1000, "ms")
        
        # Validaciones
        times = [r['response_time'] for r in results]
        accuracy_rate = sum(r['accuracy'] for r in results) / len(results) * 100
        success_rate = sum(r['success'] for r in results) / len(results) * 100
        
        self.assertLess(np.mean(times), 0.008, "Cambio preciso promedio debe ser < 8ms")
        self.assertEqual(accuracy_rate, 100, "Todos los cambios deben ser precisos")
        self.assertGreater(success_rate, 90, "Al menos 90% debe cumplir threshold")
        
        return results
    
    def test_end_to_end_latency(self):
        """Test de latencia completa end-to-end para operaciones de volumen"""
        self.logger.info("Testing volume operations end-to-end latency")
        
        results = []
        
        # Secuencias completas de gesto -> acción
        test_sequences = [
            ('volume_up', 'increase_volume'),
            ('volume_down', 'decrease_volume'),
            ('mute', 'mute_toggle'),
            ('unmute', 'mute_toggle')
        ]
        
        for gesture, action in test_sequences:
            sequence_times = []
            
            for i in range(5):
                self.start_timer()
                
                # Simular secuencia completa
                # 1. Procesamiento de frame
                time.sleep(0.001)
                
                # 2. Detección de gesto
                fingers = [1, 0, 0, 0, 0] if gesture == 'volume_up' else [0, 1, 0, 0, 0]
                landmarks = self.create_synthetic_landmarks()
                
                if self.controller_instance:
                    detected_gesture = self.controller_instance.detect_gesture(fingers, landmarks)
                
                # 3. Ejecución de acción
                if self.controller_instance:
                    if action == 'increase_volume':
                        self.controller_instance.increase_volume()
                    elif action == 'decrease_volume':
                        self.controller_instance.decrease_volume()
                    elif action == 'mute_toggle':
                        self.controller_instance.mute_toggle()
                
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
        
        # Validar latencias (volume controller debe ser muy rápido)
        for result in results:
            self.assertLess(result['mean_latency'], 0.02, 
                          f"Latencia E2E de {result['sequence']} debe ser < 20ms")
            self.assertTrue(result['meets_target'], 
                          f"Debe cumplir target de {self.expected_response_time}s")
        
        return results
    
    def run_performance_test(self) -> dict:
        """Ejecutar todos los tests de rendimiento del volume controller"""
        
        # Inicializar controlador
        init_time = self.measure_initialization_time()
        
        # Ejecutar tests específicos
        volume_change_results = self.test_volume_change_response_time()
        mute_results = self.test_mute_toggle_response_time()
        gesture_results = self.test_gesture_detection_response_time()
        precision_results = self.test_volume_precision_response_time()
        e2e_results = self.test_end_to_end_latency()
        
        # Compilar resultados finales
        results = {
            'controller': self.controller_name,
            'initialization_time': init_time,
            'volume_changes': volume_change_results,
            'mute_operations': mute_results,
            'gesture_detection': gesture_results,
            'precision_operations': precision_results,
            'end_to_end_latency': e2e_results,
            'summary': {
                'total_tests': (len(volume_change_results['increase']) + 
                              len(volume_change_results['decrease']) +
                              len(mute_results) + len(gesture_results) + 
                              len(precision_results) + len(e2e_results)),
                'expected_response_time': self.expected_response_time,
                'meets_performance_target': init_time <= 0.01,  # 10ms para inicialización
                'target_achieved': all(r['meets_target'] for r in e2e_results)
            }
        }
        
        return results

if __name__ == "__main__":
    import unittest
    
    # Crear suite de tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVolumeControllerResponseTime)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite) 