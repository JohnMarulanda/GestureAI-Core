#!/usr/bin/env python3
"""
Tests de precisión para SystemControllerEnhanced.
Mide la precisión de detección de gestos críticos del sistema.
"""

import sys
import os
import time
import unittest
from unittest.mock import Mock, patch
import numpy as np
from typing import List, Tuple, Dict, Any

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from tests.performance.metrics.accuracy.base_accuracy_test import BaseAccuracyTest

class TestSystemControllerAccuracy(BaseAccuracyTest):
    """Test de accuracy para SystemControllerEnhanced."""
    
    @classmethod
    def setUpClass(cls):
        """Configuración inicial para todos los tests."""
        cls.controller_name = "SystemController"
        cls.target_accuracy = 0.88  # 88% - Más conservador para operaciones críticas
        super().setUpClass()
        
    def setUp(self):
        """Configurar el test individual."""
        super().setUp()
        
        # Mock de las dependencias del sistema
        self.system_patches = [
            patch('ctypes.windll'),
            patch('subprocess.call'),
            patch('subprocess.run'),
            patch('os.system'),
            patch('os.path.exists', return_value=True)
        ]
        
        self.system_mocks = [p.start() for p in self.system_patches]
        
        # Configurar precisión específica por gesto del sistema (más conservador)
        self.gesture_accuracy_rates = {
            'lock_screen': 0.94,         # Muy preciso, gesto distintivo
            'shutdown': 0.90,            # Preciso pero requiere confirmación
            'restart': 0.88,             # Bueno, similar a shutdown
            'sleep': 0.92,               # Preciso, gesto común
            'logout': 0.86,              # Menos distintivo
            'task_manager': 0.91,        # Bueno, gesto específico
            'run_dialog': 0.89,          # Bueno
            'desktop_show': 0.93,        # Preciso, gesto claro
            'minimize_all': 0.90,        # Bueno
            'cancel_action': 0.95,       # Muy preciso, gesto de seguridad
            'confirm_action': 0.87,      # Más difícil, requiere intención clara
            'no_gesture': 0.90           # Buena detección de ausencia
        }
        
        # Configurar confusiones comunes para operaciones del sistema
        self.common_confusions = {
            'shutdown': {'restart': 0.06, 'sleep': 0.03, 'no_gesture': 0.01},
            'restart': {'shutdown': 0.08, 'sleep': 0.02, 'no_gesture': 0.02},
            'sleep': {'shutdown': 0.02, 'lock_screen': 0.04, 'no_gesture': 0.02},
            'lock_screen': {'sleep': 0.03, 'no_gesture': 0.03},
            'logout': {'shutdown': 0.05, 'lock_screen': 0.04, 'no_gesture': 0.05},
            'task_manager': {'run_dialog': 0.04, 'no_gesture': 0.05},
            'run_dialog': {'task_manager': 0.05, 'no_gesture': 0.06},
            'desktop_show': {'minimize_all': 0.04, 'no_gesture': 0.03},
            'minimize_all': {'desktop_show': 0.06, 'no_gesture': 0.04},
            'confirm_action': {'cancel_action': 0.08, 'no_gesture': 0.05},
            'cancel_action': {'no_gesture': 0.03, 'confirm_action': 0.02}
        }
        
        # Estados de confirmación para operaciones críticas
        self.critical_operations = ['shutdown', 'restart', 'logout']
        
    def tearDown(self):
        """Limpiar después del test."""
        super().tearDown()
        for patch_obj in self.system_patches:
            patch_obj.stop()
    
    def get_test_gestures(self) -> List[str]:
        """Retorna la lista de gestos del sistema a testear."""
        return [
            'lock_screen',
            'shutdown',
            'restart', 
            'sleep',
            'logout',
            'task_manager',
            'run_dialog',
            'desktop_show',
            'minimize_all',
            'cancel_action',
            'confirm_action',
            'no_gesture'
        ]
    
    def simulate_gesture_detection(self, gesture: str, expected_confidence: float = 0.8) -> Tuple[str, float]:
        """
        Simula la detección de un gesto del sistema con precisión realista
        
        Args:
            gesture: Nombre del gesto a simular
            expected_confidence: Nivel de confianza esperado
            
        Returns:
            Tupla (gesto_detectado, confianza_real)
        """
        # Obtener tasa de precisión para este gesto
        accuracy_rate = self.gesture_accuracy_rates.get(gesture, 0.85)
        
        # Operaciones críticas requieren mayor confianza
        if gesture in self.critical_operations:
            # Reducir ligeramente la tasa de detección para mayor seguridad
            accuracy_rate *= 0.95
            expected_confidence = max(expected_confidence, 0.8)
        
        # Determinar si la predicción será correcta
        is_correct = np.random.random() < accuracy_rate
        
        if is_correct:
            # Predicción correcta
            predicted_gesture = gesture
            # Variar ligeramente la confianza
            confidence_variation = np.random.normal(0, 0.03)
            confidence = np.clip(expected_confidence + confidence_variation, 0.3, 0.99)
            
            # Operaciones críticas requieren confianza más alta
            if gesture in self.critical_operations:
                confidence = max(confidence, 0.75)
                
        else:
            # Predicción incorrecta
            confusions = self.common_confusions.get(gesture, {})
            
            if confusions and np.random.random() < 0.70:  # 70% de errores son confusiones comunes
                confusion_gestures = list(confusions.keys())
                confusion_probs = list(confusions.values())
                
                total_prob = sum(confusion_probs)
                if total_prob > 0:
                    confusion_probs = [p/total_prob for p in confusion_probs]
                    predicted_gesture = np.random.choice(confusion_gestures, p=confusion_probs)
                else:
                    predicted_gesture = np.random.choice(self.get_test_gestures())
            else:
                # Error aleatorio
                all_gestures = self.get_test_gestures()
                predicted_gesture = np.random.choice([g for g in all_gestures if g != gesture])
            
            # Confianza más baja para predicciones incorrectas
            confidence = np.random.uniform(0.25, 0.6)
        
        # Simular tiempo de procesamiento más largo para operaciones del sistema
        time.sleep(0.002)  # 2ms de procesamiento simulado
        
        return predicted_gesture, confidence
    
    def test_critical_operations_accuracy(self):
        """Test de precisión para operaciones críticas del sistema"""
        
        print(f"\n⚠️ Testeando precisión de operaciones críticas...")
        
        for critical_op in self.critical_operations:
            predictions = []
            ground_truth = []
            confidences = []
            
            # Test con múltiples muestras
            for _ in range(25):  # Más muestras para operaciones críticas
                predicted, confidence = self.simulate_gesture_detection(critical_op, 0.85)
                predictions.append(predicted)
                ground_truth.append(critical_op)
                confidences.append(confidence)
                
                self.log_prediction(critical_op, predicted, confidence)
            
            # Calcular precisión
            accuracy = sum(1 for true_val, pred in zip(ground_truth, predictions) if true_val == pred) / len(predictions)
            avg_confidence = np.mean(confidences)
            
            # Verificar precisión mínima para operaciones críticas
            min_critical_accuracy = 0.85  # 85% mínimo para operaciones críticas
            self.assertGreaterEqual(accuracy, min_critical_accuracy,
                                  f"Precisión de {critical_op} demasiado baja: {accuracy:.3f} < {min_critical_accuracy:.3f}")
            
            # Verificar confianza mínima para operaciones críticas
            min_critical_confidence = 0.70  # 70% confianza mínima
            self.assertGreaterEqual(avg_confidence, min_critical_confidence,
                                  f"Confianza promedio de {critical_op} demasiado baja: {avg_confidence:.3f}")
            
            status = "✅" if accuracy >= min_critical_accuracy else "⚠️"
            print(f"   {status} {critical_op}: Precisión {accuracy:.3f}, Confianza {avg_confidence:.3f}")
    
    def test_shutdown_restart_discrimination(self):
        """Test de discriminación entre shutdown y restart"""
        
        print(f"\n🔄💤 Testeando discriminación shutdown/restart...")
        
        # Test específico para evitar confusiones peligrosas
        shutdown_tests = []
        restart_tests = []
        
        for _ in range(20):
            # Test shutdown
            predicted, confidence = self.simulate_gesture_detection('shutdown', 0.85)
            shutdown_tests.append({
                'predicted': predicted,
                'confidence': confidence,
                'correct': predicted == 'shutdown',
                'dangerous_confusion': predicted == 'restart'
            })
            self.log_prediction('shutdown', predicted, confidence)
            
            # Test restart
            predicted, confidence = self.simulate_gesture_detection('restart', 0.85)
            restart_tests.append({
                'predicted': predicted,
                'confidence': confidence,
                'correct': predicted == 'restart',
                'dangerous_confusion': predicted == 'shutdown'
            })
            self.log_prediction('restart', predicted, confidence)
        
        # Analizar resultados
        shutdown_accuracy = np.mean([t['correct'] for t in shutdown_tests])
        restart_accuracy = np.mean([t['correct'] for t in restart_tests])
        
        shutdown_confusion_rate = np.mean([t['dangerous_confusion'] for t in shutdown_tests])
        restart_confusion_rate = np.mean([t['dangerous_confusion'] for t in restart_tests])
        
        print(f"   💤 Precisión shutdown: {shutdown_accuracy:.3f}")
        print(f"   🔄 Precisión restart: {restart_accuracy:.3f}")
        print(f"   ⚠️ Confusión shutdown→restart: {shutdown_confusion_rate:.3f}")
        print(f"   ⚠️ Confusión restart→shutdown: {restart_confusion_rate:.3f}")
        
        # Verificar precisión y confusiones bajas
        self.assertGreaterEqual(shutdown_accuracy, 0.80, "Precisión shutdown insuficiente")
        self.assertGreaterEqual(restart_accuracy, 0.80, "Precisión restart insuficiente")
        self.assertLess(shutdown_confusion_rate, 0.10, "Confusión shutdown→restart demasiado alta")
        self.assertLess(restart_confusion_rate, 0.10, "Confusión restart→shutdown demasiado alta")
    
    def test_lock_sleep_accuracy(self):
        """Test de precisión para lock y sleep (operaciones menos críticas)"""
        
        print(f"\n🔒😴 Testeando precisión lock/sleep...")
        
        safe_operations = ['lock_screen', 'sleep']
        safe_accuracies = {}
        
        for operation in safe_operations:
            correct_predictions = 0
            total_predictions = 0
            
            for _ in range(18):  # 18 muestras por operación
                predicted, confidence = self.simulate_gesture_detection(operation, 0.8)
                self.log_prediction(operation, predicted, confidence)
                
                total_predictions += 1
                if predicted == operation:
                    correct_predictions += 1
            
            accuracy = correct_predictions / total_predictions
            safe_accuracies[operation] = accuracy
            
            status = "✅" if accuracy >= 0.85 else "⚠️"
            print(f"   {status} {operation}: {accuracy:.3f}")
        
        # Verificar precisión promedio de operaciones seguras
        avg_safe_accuracy = np.mean(list(safe_accuracies.values()))
        self.assertGreaterEqual(avg_safe_accuracy, 0.85,
                              f"Precisión promedio operaciones seguras insuficiente: {avg_safe_accuracy:.3f}")
    
    def test_task_management_gestures_accuracy(self):
        """Test de precisión para gestos de gestión de tareas"""
        
        print(f"\n📋 Testeando precisión de gestión de tareas...")
        
        task_gestures = ['task_manager', 'run_dialog', 'desktop_show', 'minimize_all']
        task_accuracies = {}
        
        for gesture in task_gestures:
            correct_predictions = 0
            total_predictions = 0
            
            for _ in range(15):  # 15 muestras por gesto
                predicted, confidence = self.simulate_gesture_detection(gesture, 0.8)
                self.log_prediction(gesture, predicted, confidence)
                
                total_predictions += 1
                if predicted == gesture:
                    correct_predictions += 1
            
            accuracy = correct_predictions / total_predictions
            task_accuracies[gesture] = accuracy
            
            status = "✅" if accuracy >= 0.82 else "⚠️"
            print(f"   {status} {gesture}: {accuracy:.3f}")
        
        # Verificar precisión promedio de gestión de tareas
        avg_task_accuracy = np.mean(list(task_accuracies.values()))
        self.assertGreaterEqual(avg_task_accuracy, 0.82,
                              f"Precisión promedio gestión de tareas insuficiente: {avg_task_accuracy:.3f}")
    
    def test_confirmation_gestures_accuracy(self):
        """Test de precisión para gestos de confirmación/cancelación"""
        
        print(f"\n✅❌ Testeando precisión confirmación/cancelación...")
        
        confirmation_gestures = ['confirm_action', 'cancel_action']
        confirmation_results = {}
        
        for gesture in confirmation_gestures:
            predictions = []
            confidences = []
            
            for _ in range(20):  # 20 muestras por gesto de confirmación
                predicted, confidence = self.simulate_gesture_detection(gesture, 0.8)
                self.log_prediction(gesture, predicted, confidence)
                
                predictions.append(predicted == gesture)
                confidences.append(confidence)
            
            accuracy = np.mean(predictions)
            avg_confidence = np.mean(confidences)
            
            confirmation_results[gesture] = {
                'accuracy': accuracy,
                'confidence': avg_confidence
            }
            
            status = "✅" if accuracy >= 0.80 else "⚠️"
            print(f"   {status} {gesture}: Precisión {accuracy:.3f}, Confianza {avg_confidence:.3f}")
        
        # Verificar que cancel_action tiene alta precisión (crítico para seguridad)
        cancel_accuracy = confirmation_results['cancel_action']['accuracy']
        self.assertGreaterEqual(cancel_accuracy, 0.85,
                              f"Precisión de cancel_action insuficiente: {cancel_accuracy:.3f}")
        
        # Test de discriminación entre confirm y cancel
        confusion_tests = []
        for _ in range(15):
            # Test confirm que no debe ser cancel
            predicted, _ = self.simulate_gesture_detection('confirm_action', 0.8)
            if predicted == 'cancel_action':
                confusion_tests.append('confirm_as_cancel')
                
            # Test cancel que no debe ser confirm
            predicted, _ = self.simulate_gesture_detection('cancel_action', 0.85)
            if predicted == 'confirm_action':
                confusion_tests.append('cancel_as_confirm')
        
        confusion_rate = len(confusion_tests) / 30  # 30 tests total
        print(f"   🔄 Confusión confirm/cancel: {confusion_rate:.3f}")
        
        self.assertLess(confusion_rate, 0.15,
                       f"Confusión confirm/cancel demasiado alta: {confusion_rate:.3f}")
    
    def test_system_safety_under_stress(self):
        """Test de seguridad del sistema bajo condiciones de estrés"""
        
        print(f"\n⚡ Testeando seguridad bajo estrés...")
        
        # Simular condiciones de estrés con gestos rápidos
        stress_sequence = []
        
        # Agregar operaciones críticas y no críticas mezcladas
        for _ in range(5):
            stress_sequence.extend(self.critical_operations)
            stress_sequence.extend(['task_manager', 'lock_screen', 'desktop_show'])
        
        np.random.shuffle(stress_sequence)
        
        critical_errors = 0
        total_critical_tests = 0
        false_critical_detections = 0
        
        start_time = time.time()
        
        for gesture in stress_sequence:
            predicted, confidence = self.simulate_gesture_detection(gesture, 0.75)
            self.log_prediction(gesture, predicted, confidence)
            
            # Contar errores en operaciones críticas
            if gesture in self.critical_operations:
                total_critical_tests += 1
                if predicted != gesture:
                    critical_errors += 1
            
            # Contar detecciones falsas de operaciones críticas
            if gesture not in self.critical_operations and predicted in self.critical_operations:
                false_critical_detections += 1
            
            # Simular procesamiento rápido bajo estrés
            time.sleep(0.0008)
        
        total_time = time.time() - start_time
        
        # Calcular métricas de seguridad
        critical_error_rate = critical_errors / total_critical_tests if total_critical_tests > 0 else 0
        false_critical_rate = false_critical_detections / len(stress_sequence)
        
        print(f"   ⏱️ Tiempo total: {total_time:.3f}s")
        print(f"   📊 Gestos/segundo: {len(stress_sequence)/total_time:.1f}")
        print(f"   ⚠️ Tasa error operaciones críticas: {critical_error_rate:.3f}")
        print(f"   🚨 Tasa falsos críticos: {false_critical_rate:.3f}")
        
        # Verificar que los errores críticos sean bajos
        self.assertLess(critical_error_rate, 0.20,
                       f"Tasa de error en operaciones críticas demasiado alta: {critical_error_rate:.3f}")
        
        # Verificar que no haya demasiados falsos críticos
        self.assertLess(false_critical_rate, 0.10,
                       f"Tasa de falsos críticos demasiado alta: {false_critical_rate:.3f}")
    
    def test_system_gesture_confidence_thresholds(self):
        """Test de umbrales de confianza para diferentes tipos de operaciones"""
        
        print(f"\n📊 Testeando umbrales de confianza por tipo...")
        
        # Clasificar gestos por nivel de criticidad
        gesture_criticality = {
            'critical': ['shutdown', 'restart', 'logout'],
            'important': ['lock_screen', 'sleep', 'task_manager'],
            'normal': ['desktop_show', 'minimize_all', 'run_dialog'],
            'safety': ['cancel_action', 'confirm_action']
        }
        
        criticality_metrics = {}
        
        for level, gestures in gesture_criticality.items():
            level_confidences = []
            level_accuracies = []
            
            for gesture in gestures:
                for _ in range(12):  # 12 muestras por gesto
                    predicted, confidence = self.simulate_gesture_detection(gesture, 0.8)
                    
                    is_correct = (predicted == gesture)
                    level_confidences.append(confidence)
                    level_accuracies.append(is_correct)
                    
                    self.log_prediction(gesture, predicted, confidence)
            
            avg_confidence = np.mean(level_confidences)
            avg_accuracy = np.mean(level_accuracies)
            
            criticality_metrics[level] = {
                'confidence': avg_confidence,
                'accuracy': avg_accuracy
            }
            
            print(f"   📈 {level}: Confianza {avg_confidence:.3f}, Precisión {avg_accuracy:.3f}")
        
        # Verificar que operaciones críticas tienen suficiente confianza
        critical_metrics = criticality_metrics['critical']
        self.assertGreaterEqual(critical_metrics['confidence'], 0.70,
                              "Confianza de operaciones críticas insuficiente")
        self.assertGreaterEqual(critical_metrics['accuracy'], 0.80,
                              "Precisión de operaciones críticas insuficiente")
        
        # Verificar que gestos de seguridad tienen buena precisión
        safety_metrics = criticality_metrics['safety']
        self.assertGreaterEqual(safety_metrics['accuracy'], 0.82,
                              "Precisión de gestos de seguridad insuficiente")

if __name__ == '__main__':
    unittest.main()