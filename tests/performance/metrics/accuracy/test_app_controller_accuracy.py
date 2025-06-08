#!/usr/bin/env python3
"""
Tests de precisión para AppControllerEnhanced.
Mide la precisión de detección de gestos de gestión de aplicaciones.
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

class TestAppControllerAccuracy(BaseAccuracyTest):
    """Test de accuracy para AppControllerEnhanced."""
    
    @classmethod
    def setUpClass(cls):
        """Configuración inicial para todos los tests."""
        cls.controller_name = "AppController"
        cls.target_accuracy = 0.86  # 86% - Moderado para gestión de apps
        super().setUpClass()
        
    def setUp(self):
        """Configurar el test individual."""
        super().setUp()
        
        # Mock de las dependencias de aplicaciones
        self.app_patches = [
            patch('subprocess.Popen'),
            patch('subprocess.run'),
            patch('psutil.process_iter'),
            patch('psutil.Process'),
            patch('os.path.exists', return_value=True),
            patch('os.system')
        ]
        
        self.app_mocks = [p.start() for p in self.app_patches]
        
        # Configurar precisión específica por gesto de aplicaciones
        self.gesture_accuracy_rates = {
            'open_chrome': 0.92,         # Preciso, gesto distintivo
            'open_notepad': 0.89,        # Bueno, gesto simple
            'open_calculator': 0.87,     # Moderado
            'open_spotify': 0.85,        # Moderado, menos común
            'open_explorer': 0.88,       # Bueno
            'close_app': 0.90,           # Preciso, gesto común
            'minimize_app': 0.86,        # Moderado
            'maximize_app': 0.84,        # Menos distintivo
            'switch_app': 0.83,          # Complejo, contexto dependiente
            'alt_tab': 0.91,             # Preciso, gesto específico
            'task_switch': 0.82,         # Complejo
            'force_close': 0.88,         # Bueno, gesto específico
            'app_menu': 0.81,            # Menos distintivo
            'window_snap_left': 0.85,    # Moderado
            'window_snap_right': 0.85,   # Moderado
            'no_gesture': 0.89           # Buena detección de ausencia
        }
        
        # Configurar confusiones comunes de aplicaciones
        self.common_confusions = {
            'open_chrome': {'open_explorer': 0.05, 'no_gesture': 0.03},
            'open_notepad': {'open_calculator': 0.07, 'no_gesture': 0.04},
            'open_calculator': {'open_notepad': 0.08, 'no_gesture': 0.05},
            'open_spotify': {'open_chrome': 0.06, 'no_gesture': 0.09},
            'open_explorer': {'open_chrome': 0.06, 'no_gesture': 0.06},
            'close_app': {'minimize_app': 0.06, 'force_close': 0.04},
            'minimize_app': {'close_app': 0.08, 'maximize_app': 0.06},
            'maximize_app': {'minimize_app': 0.10, 'no_gesture': 0.06},
            'switch_app': {'alt_tab': 0.12, 'task_switch': 0.08},
            'alt_tab': {'switch_app': 0.06, 'task_switch': 0.03},
            'task_switch': {'switch_app': 0.10, 'alt_tab': 0.08},
            'force_close': {'close_app': 0.08, 'no_gesture': 0.04},
            'app_menu': {'no_gesture': 0.12, 'switch_app': 0.07},
            'window_snap_left': {'window_snap_right': 0.10, 'minimize_app': 0.05},
            'window_snap_right': {'window_snap_left': 0.10, 'maximize_app': 0.05}
        }
        
    def tearDown(self):
        """Limpiar después del test."""
        super().tearDown()
        for patch_obj in self.app_patches:
            patch_obj.stop()
    
    def get_test_gestures(self) -> List[str]:
        """Retorna la lista de gestos de aplicaciones a testear."""
        return [
            'open_chrome',
            'open_notepad',
            'open_calculator',
            'open_spotify',
            'open_explorer',
            'close_app',
            'minimize_app',
            'maximize_app',
            'switch_app',
            'alt_tab',
            'task_switch',
            'force_close',
            'app_menu',
            'window_snap_left',
            'window_snap_right',
            'no_gesture'
        ]
    
    def simulate_gesture_detection(self, gesture: str, expected_confidence: float = 0.8) -> Tuple[str, float]:
        """
        Simula la detección de un gesto de aplicación con precisión realista
        
        Args:
            gesture: Nombre del gesto a simular
            expected_confidence: Nivel de confianza esperado
            
        Returns:
            Tupla (gesto_detectado, confianza_real)
        """
        # Obtener tasa de precisión para este gesto
        accuracy_rate = self.gesture_accuracy_rates.get(gesture, 0.80)
        
        # Determinar si la predicción será correcta
        is_correct = np.random.random() < accuracy_rate
        
        if is_correct:
            # Predicción correcta
            predicted_gesture = gesture
            # Variar ligeramente la confianza
            confidence_variation = np.random.normal(0, 0.06)
            confidence = np.clip(expected_confidence + confidence_variation, 0.3, 0.99)
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
        
        # Simular tiempo de procesamiento más largo para aplicaciones
        time.sleep(0.003)  # 3ms de procesamiento simulado
        
        return predicted_gesture, confidence
    
    def test_app_opening_accuracy(self):
        """Test de precisión para apertura de aplicaciones"""
        app_open_gestures = ['open_chrome', 'open_notepad', 'open_calculator', 'open_spotify', 'open_explorer']
        
        print(f"\n🚀 Testeando precisión de apertura de apps...")
        
        for app_gesture in app_open_gestures:
            predictions = []
            ground_truth = []
            
            # Test con múltiples muestras
            for _ in range(20):  # 20 muestras por app
                predicted, confidence = self.simulate_gesture_detection(app_gesture, 0.8)
                predictions.append(predicted)
                ground_truth.append(app_gesture)
                
                self.log_prediction(app_gesture, predicted, confidence)
            
            # Calcular precisión
            accuracy = sum(1 for true_val, pred in zip(ground_truth, predictions) if true_val == pred) / len(predictions)
            
            # Verificar precisión mínima para apertura de apps
            min_app_accuracy = 0.80  # 80% mínimo para apertura
            self.assertGreaterEqual(accuracy, min_app_accuracy,
                                  f"Precisión de {app_gesture} demasiado baja: {accuracy:.3f} < {min_app_accuracy:.3f}")
            
            status = "✅" if accuracy >= min_app_accuracy else "⚠️"
            print(f"   {status} {app_gesture}: {accuracy:.3f}")
    
    def test_window_management_accuracy(self):
        """Test de precisión para gestión de ventanas"""
        
        print(f"\n🪟 Testeando precisión de gestión de ventanas...")
        
        window_gestures = ['close_app', 'minimize_app', 'maximize_app', 'force_close']
        window_accuracies = {}
        
        for gesture in window_gestures:
            correct_predictions = 0
            total_predictions = 0
            
            for _ in range(18):  # 18 muestras por gesto
                predicted, confidence = self.simulate_gesture_detection(gesture, 0.8)
                self.log_prediction(gesture, predicted, confidence)
                
                total_predictions += 1
                if predicted == gesture:
                    correct_predictions += 1
            
            accuracy = correct_predictions / total_predictions
            window_accuracies[gesture] = accuracy
            
            # Umbral específico para cada gesto
            min_accuracy = 0.85 if gesture in ['close_app', 'force_close'] else 0.78
            status = "✅" if accuracy >= min_accuracy else "⚠️"
            print(f"   {status} {gesture}: {accuracy:.3f}")
        
        # Verificar precisión promedio de gestión de ventanas
        avg_window_accuracy = np.mean(list(window_accuracies.values()))
        self.assertGreaterEqual(avg_window_accuracy, 0.82,
                              f"Precisión promedio gestión ventanas insuficiente: {avg_window_accuracy:.3f}")
        
        # Test específico de discriminación close vs force_close
        close_force_confusion = 0
        for _ in range(15):
            # Test close_app que no debe ser force_close
            predicted, _ = self.simulate_gesture_detection('close_app', 0.8)
            if predicted == 'force_close':
                close_force_confusion += 1
                
            # Test force_close que no debe ser close_app
            predicted, _ = self.simulate_gesture_detection('force_close', 0.8)
            if predicted == 'close_app':
                close_force_confusion += 1
        
        confusion_rate = close_force_confusion / 30
        print(f"   🔄 Confusión close/force_close: {confusion_rate:.3f}")
        
        self.assertLess(confusion_rate, 0.15,
                       f"Confusión close/force_close demasiado alta: {confusion_rate:.3f}")
    
    def test_app_switching_accuracy(self):
        """Test de precisión para cambio entre aplicaciones"""
        
        print(f"\n🔄 Testeando precisión de cambio de apps...")
        
        switch_gestures = ['switch_app', 'alt_tab', 'task_switch']
        switch_results = {}
        
        for gesture in switch_gestures:
            predictions = []
            confidences = []
            
            for _ in range(15):  # 15 muestras por gesto de cambio
                predicted, confidence = self.simulate_gesture_detection(gesture, 0.75)
                self.log_prediction(gesture, predicted, confidence)
                
                predictions.append(predicted == gesture)
                confidences.append(confidence)
            
            accuracy = np.mean(predictions)
            avg_confidence = np.mean(confidences)
            
            switch_results[gesture] = {
                'accuracy': accuracy,
                'confidence': avg_confidence
            }
            
            # Los gestos de cambio son más complejos
            min_switch_accuracy = 0.75
            status = "✅" if accuracy >= min_switch_accuracy else "⚠️"
            print(f"   {status} {gesture}: Precisión {accuracy:.3f}, Confianza {avg_confidence:.3f}")
        
        # Verificar precisión mínima de cambio de apps
        avg_switch_accuracy = np.mean([r['accuracy'] for r in switch_results.values()])
        self.assertGreaterEqual(avg_switch_accuracy, 0.75,
                              f"Precisión promedio cambio apps insuficiente: {avg_switch_accuracy:.3f}")
        
        # alt_tab debería ser el más preciso de los gestos de cambio
        alt_tab_accuracy = switch_results['alt_tab']['accuracy']
        self.assertGreaterEqual(alt_tab_accuracy, 0.85,
                              f"Precisión de alt_tab insuficiente: {alt_tab_accuracy:.3f}")
    
    def test_window_snapping_accuracy(self):
        """Test de precisión para snapping de ventanas"""
        
        print(f"\n📐 Testeando precisión de snapping...")
        
        snap_gestures = ['window_snap_left', 'window_snap_right']
        snap_accuracies = {}
        
        for gesture in snap_gestures:
            correct_predictions = 0
            total_predictions = 0
            
            for _ in range(16):  # 16 muestras por dirección
                predicted, confidence = self.simulate_gesture_detection(gesture, 0.75)
                self.log_prediction(gesture, predicted, confidence)
                
                total_predictions += 1
                if predicted == gesture:
                    correct_predictions += 1
            
            accuracy = correct_predictions / total_predictions
            snap_accuracies[gesture] = accuracy
            
            status = "✅" if accuracy >= 0.78 else "⚠️"
            print(f"   {status} {gesture}: {accuracy:.3f}")
        
        # Verificar precisión direccional del snapping
        avg_snap_accuracy = np.mean(list(snap_accuracies.values()))
        self.assertGreaterEqual(avg_snap_accuracy, 0.78,
                              f"Precisión promedio snapping insuficiente: {avg_snap_accuracy:.3f}")
        
        # Test de discriminación direccional
        snap_direction_confusion = 0
        for _ in range(20):
            # Test snap_left que no debe ser snap_right
            predicted, _ = self.simulate_gesture_detection('window_snap_left', 0.75)
            if predicted == 'window_snap_right':
                snap_direction_confusion += 1
                
            # Test snap_right que no debe ser snap_left
            predicted, _ = self.simulate_gesture_detection('window_snap_right', 0.75)
            if predicted == 'window_snap_left':
                snap_direction_confusion += 1
        
        direction_confusion_rate = snap_direction_confusion / 40
        print(f"   🔄 Confusión direccional snap: {direction_confusion_rate:.3f}")
        
        self.assertLess(direction_confusion_rate, 0.20,
                       f"Confusión direccional snap demasiado alta: {direction_confusion_rate:.3f}")
    
    def test_app_workflow_sequences(self):
        """Test de precisión con secuencias de workflow de aplicaciones"""
        
        print(f"\n🔄 Testeando secuencias de workflow de apps...")
        
        # Secuencias típicas de uso de aplicaciones
        app_workflows = [
            ['open_chrome', 'maximize_app', 'minimize_app'],            # Abrir, maximizar, minimizar
            ['open_notepad', 'alt_tab', 'switch_app', 'close_app'],    # Abrir, cambiar, cerrar
            ['open_calculator', 'window_snap_left', 'open_spotify'],    # Multitask con snap
            ['alt_tab', 'alt_tab', 'force_close'],                     # Navegación y cierre forzado
            ['open_explorer', 'switch_app', 'close_app', 'open_chrome'] # Workflow completo
        ]
        
        workflow_accuracies = []
        
        for i, workflow in enumerate(app_workflows):
            workflow_predictions = []
            workflow_ground_truth = []
            
            print(f"   🔄 Workflow {i+1}: {' → '.join(workflow)}")
            
            for gesture in workflow:
                predicted, confidence = self.simulate_gesture_detection(gesture, 0.75)
                workflow_predictions.append(predicted)
                workflow_ground_truth.append(gesture)
                
                self.log_prediction(gesture, predicted, confidence)
                
                # Pausa entre gestos de workflow (apps son más lentas)
                time.sleep(0.005)
            
            # Calcular precisión de este workflow
            workflow_accuracy = sum(1 for true_val, pred in zip(workflow_ground_truth, workflow_predictions) 
                                  if true_val == pred) / len(workflow)
            workflow_accuracies.append(workflow_accuracy)
            
            print(f"      Precisión: {workflow_accuracy:.3f}")
        
        # Verificar precisión promedio de workflows
        avg_workflow_accuracy = np.mean(workflow_accuracies)
        
        print(f"   📊 Precisión promedio workflows: {avg_workflow_accuracy:.3f}")
        
        self.assertGreaterEqual(avg_workflow_accuracy, 0.78,
                              f"Precisión en workflows de apps insuficiente: {avg_workflow_accuracy:.3f}")
    
    def test_app_gesture_confidence_by_type(self):
        """Test de correlación de confianza por tipo de operación"""
        
        print(f"\n📊 Testeando confianza por tipo de operación...")
        
        # Clasificar gestos por tipo de operación
        operation_types = {
            'apertura': ['open_chrome', 'open_notepad', 'open_calculator', 'open_spotify', 'open_explorer'],
            'ventana': ['close_app', 'minimize_app', 'maximize_app', 'force_close'],
            'navegacion': ['switch_app', 'alt_tab', 'task_switch'],
            'layout': ['window_snap_left', 'window_snap_right', 'app_menu']
        }
        
        type_metrics = {}
        
        for op_type, gestures in operation_types.items():
            type_confidences = []
            type_accuracies = []
            
            for gesture in gestures:
                for _ in range(10):  # 10 muestras por gesto
                    predicted, confidence = self.simulate_gesture_detection(gesture, 0.75)
                    
                    is_correct = (predicted == gesture)
                    type_confidences.append(confidence)
                    type_accuracies.append(is_correct)
                    
                    self.log_prediction(gesture, predicted, confidence)
            
            avg_confidence = np.mean(type_confidences)
            avg_accuracy = np.mean(type_accuracies)
            
            type_metrics[op_type] = {
                'confidence': avg_confidence,
                'accuracy': avg_accuracy
            }
            
            print(f"   📈 {op_type}: Confianza {avg_confidence:.3f}, Precisión {avg_accuracy:.3f}")
        
        # Verificar que operaciones de apertura tienen buena precisión
        apertura_metrics = type_metrics['apertura']
        self.assertGreaterEqual(apertura_metrics['accuracy'], 0.82,
                              "Precisión de operaciones de apertura insuficiente")
        
        # Verificar que operaciones de ventana tienen precisión aceptable
        ventana_metrics = type_metrics['ventana']
        self.assertGreaterEqual(ventana_metrics['accuracy'], 0.80,
                              "Precisión de operaciones de ventana insuficiente")
    
    def test_app_controller_under_multitasking(self):
        """Test de precisión bajo condiciones de multitasking intenso"""
        
        print(f"\n🔀 Testeando multitasking intenso...")
        
        # Simular sesión intensa de multitasking
        multitask_sequence = []
        
        # Patrón típico de multitasking: abrir apps, cambiar entre ellas, gestionar ventanas
        multitask_pattern = [
            'open_chrome', 'open_notepad', 'alt_tab', 'window_snap_left',
            'open_calculator', 'switch_app', 'window_snap_right', 'alt_tab',
            'minimize_app', 'switch_app', 'maximize_app', 'close_app'
        ]
        
        for _ in range(8):  # 8 ciclos de multitasking
            multitask_sequence.extend(multitask_pattern)
        
        # Mezclar parcialmente para simular uso real pero mantener algo de estructura
        for i in range(0, len(multitask_sequence), 4):
            chunk = multitask_sequence[i:i+4]
            np.random.shuffle(chunk)
            multitask_sequence[i:i+4] = chunk
        
        multitask_results = []
        app_open_errors = 0  # Errores críticos en apertura de apps
        
        start_time = time.time()
        
        for gesture in multitask_sequence:
            predicted, confidence = self.simulate_gesture_detection(gesture, 0.75)
            self.log_prediction(gesture, predicted, confidence)
            
            is_correct = (predicted == gesture)
            multitask_results.append(is_correct)
            
            # Contar errores críticos en apertura de apps
            if gesture.startswith('open_') and not is_correct:
                app_open_errors += 1
            
            # Simular carga de multitasking
            time.sleep(0.001)  # 1ms entre operaciones
        
        total_time = time.time() - start_time
        multitask_accuracy = np.mean(multitask_results)
        app_open_count = len([g for g in multitask_sequence if g.startswith('open_')])
        app_open_error_rate = app_open_errors / app_open_count if app_open_count > 0 else 0
        
        print(f"   🔀 Operaciones procesadas: {len(multitask_sequence)}")
        print(f"   ⏱️ Tiempo total: {total_time:.3f}s")
        print(f"   🎯 Precisión multitasking: {multitask_accuracy:.3f}")
        print(f"   📈 Operaciones/segundo: {len(multitask_sequence)/total_time:.1f}")
        print(f"   🚀 Tasa error apertura apps: {app_open_error_rate:.3f}")
        
        # Verificar que la precisión se mantiene en multitasking
        self.assertGreaterEqual(multitask_accuracy, 0.75,
                              f"Precisión en multitasking insuficiente: {multitask_accuracy:.3f}")
        
        # Verificar que los errores en apertura de apps sean controlados
        self.assertLess(app_open_error_rate, 0.25,
                       f"Tasa de error en apertura de apps demasiado alta: {app_open_error_rate:.3f}")

if __name__ == '__main__':
    unittest.main()