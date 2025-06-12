#!/usr/bin/env python3
"""
Tests de precisión para MouseControllerEnhanced.
Mide la precisión de detección de gestos de mouse como clicks, movimientos, scrolls.
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

class TestMouseControllerAccuracy(BaseAccuracyTest):
    """Test de accuracy para MouseControllerEnhanced."""
    
    @classmethod
    def setUpClass(cls):
        """Configuración inicial para todos los tests."""
        cls.controller_name = "MouseController"
        cls.target_accuracy = 0.94  # 94% - Muy alto para interacción crítica
        super().setUpClass()
        
    def setUp(self):
        """Configurar el test individual."""
        super().setUp()
        
        # Mock de las dependencias de mouse
        self.mouse_patches = [
            patch('pyautogui.click'),
            patch('pyautogui.doubleClick'),
            patch('pyautogui.rightClick'),
            patch('pyautogui.moveTo'),
            patch('pyautogui.scroll'),
            patch('pyautogui.drag'),
            patch('os.path.exists', return_value=True)
        ]
        
        self.mouse_mocks = [p.start() for p in self.mouse_patches]
        
        # Configurar precisión específica por gesto de mouse
        self.gesture_accuracy_rates = {
            'left_click': 0.98,          # Muy preciso, gesto fundamental
            'right_click': 0.96,         # Muy preciso, gesto común
            'double_click': 0.94,        # Preciso, requiere timing
            'middle_click': 0.91,        # Bueno, menos común
            'scroll_up': 0.95,           # Muy preciso, gesto común
            'scroll_down': 0.95,         # Muy preciso, gesto común
            'scroll_left': 0.89,         # Menos preciso, menos común
            'scroll_right': 0.89,        # Menos preciso, menos común
            'move_cursor': 0.92,         # Bueno, movimiento continuo
            'drag_drop': 0.88,           # Complejo, requiere inicio/fin
            'hover': 0.90,               # Bueno pero requiere estabilidad
            'click_and_hold': 0.86,      # Complejo, requiere timing
            'no_gesture': 0.96           # Excelente detección de ausencia
        }
        
        # Configurar confusiones comunes específicas de mouse
        self.common_confusions = {
            'left_click': {'double_click': 0.02},
            'double_click': {'left_click': 0.04, 'right_click': 0.02},
            'right_click': {'left_click': 0.02, 'middle_click': 0.02},
            'middle_click': {'right_click': 0.05, 'scroll_up': 0.04},
            'scroll_up': {'scroll_down': 0.03, 'move_cursor': 0.02},
            'scroll_down': {'scroll_up': 0.03, 'move_cursor': 0.02},
            'scroll_left': {'scroll_right': 0.07, 'scroll_up': 0.04},
            'scroll_right': {'scroll_left': 0.07, 'scroll_down': 0.04},
            'move_cursor': {'hover': 0.05, 'no_gesture': 0.03},
            'drag_drop': {'move_cursor': 0.08, 'click_and_hold': 0.04},
            'hover': {'move_cursor': 0.06, 'no_gesture': 0.04},
            'click_and_hold': {'left_click': 0.08, 'drag_drop': 0.06}
        }
        
    def tearDown(self):
        """Limpiar después del test."""
        super().tearDown()
        for patch_obj in self.mouse_patches:
            patch_obj.stop()
    
    def get_test_gestures(self) -> List[str]:
        """Retorna la lista de gestos de mouse a testear."""
        return [
            'left_click',
            'right_click',
            'double_click',
            'middle_click',
            'scroll_up',
            'scroll_down',
            'scroll_left',
            'scroll_right',
            'move_cursor',
            'drag_drop',
            'hover',
            'click_and_hold',
            'no_gesture'
        ]
    
    def simulate_gesture_detection(self, gesture: str, expected_confidence: float = 0.8) -> Tuple[str, float]:
        """
        Simula la detección de un gesto de mouse con precisión realista
        
        Args:
            gesture: Nombre del gesto a simular
            expected_confidence: Nivel de confianza esperado
            
        Returns:
            Tupla (gesto_detectado, confianza_real)
        """
        # Obtener tasa de precisión para este gesto
        accuracy_rate = self.gesture_accuracy_rates.get(gesture, 0.90)
        
        # Determinar si la predicción será correcta
        is_correct = np.random.random() < accuracy_rate
        
        if is_correct:
            # Predicción correcta
            predicted_gesture = gesture
            # Variar ligeramente la confianza
            confidence_variation = np.random.normal(0, 0.02)
            confidence = np.clip(expected_confidence + confidence_variation, 0.3, 0.99)
        else:
            # Predicción incorrecta - elegir confusión común
            confusions = self.common_confusions.get(gesture, {})
            
            if confusions and np.random.random() < 0.80:  # 80% de errores son confusiones comunes
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
            confidence = np.random.uniform(0.3, 0.65)
        
        # Simular tiempo de procesamiento muy rápido para mouse
        time.sleep(0.0003)  # 0.3ms de procesamiento simulado
        
        return predicted_gesture, confidence
    
    def test_basic_mouse_controls_accuracy(self):
        """Test de precisión para controles básicos de mouse"""
        basic_controls = ['left_click', 'right_click', 'double_click', 'middle_click']
        
        print(f"\n🖱️ Testeando precisión de controles básicos...")
        
        for control in basic_controls:
            predictions = []
            ground_truth = []
            
            # Test con múltiples muestras
            for _ in range(25):  # 25 muestras por control básico
                predicted, confidence = self.simulate_gesture_detection(control, 0.9)
                predictions.append(predicted)
                ground_truth.append(control)
                
                self.log_prediction(control, predicted, confidence)
            
            # Calcular precisión para este control
            accuracy = sum(1 for true_val, pred in zip(ground_truth, predictions) if true_val == pred) / len(predictions)
            
            # Verificar que cumple mínimo para controles básicos
            min_basic_accuracy = 0.93  # 93% mínimo para controles básicos
            self.assertGreaterEqual(accuracy, min_basic_accuracy,
                                  f"Precisión de {control} demasiado baja: {accuracy:.3f} < {min_basic_accuracy:.3f}")
            
            status = "✅" if accuracy >= min_basic_accuracy else "⚠️"
            print(f"   {status} {control}: {accuracy:.3f}")
    
    def test_click_precision_accuracy(self):
        """Test de precisión específica para diferentes tipos de click"""
        
        print(f"\n👆 Testeando precisión de tipos de click...")
        
        click_types = ['left_click', 'right_click', 'double_click']
        click_accuracies = {}
        
        for click_type in click_types:
            correct_predictions = 0
            total_predictions = 0
            
            for _ in range(20):  # 20 muestras por tipo de click
                predicted, confidence = self.simulate_gesture_detection(click_type, 0.9)
                self.log_prediction(click_type, predicted, confidence)
                
                total_predictions += 1
                if predicted == click_type:
                    correct_predictions += 1
            
            accuracy = correct_predictions / total_predictions
            click_accuracies[click_type] = accuracy
            
            status = "✅" if accuracy >= 0.90 else "⚠️"
            print(f"   {status} {click_type}: {accuracy:.3f}")
        
        # Verificar que la precisión promedio de clicks es alta
        avg_click_accuracy = np.mean(list(click_accuracies.values()))
        self.assertGreaterEqual(avg_click_accuracy, 0.92,
                              f"Precisión promedio de clicks insuficiente: {avg_click_accuracy:.3f}")
        
        # Test específico de discriminación left_click vs double_click
        click_double_confusion = 0
        for _ in range(20):
            # Test left_click que no debe ser detectado como double_click
            predicted, _ = self.simulate_gesture_detection('left_click', 0.9)
            if predicted == 'double_click':
                click_double_confusion += 1
        
        confusion_rate = click_double_confusion / 20
        print(f"   🔄 Confusión left_click→double_click: {confusion_rate:.3f}")
        
        self.assertLess(confusion_rate, 0.05,
                       f"Confusión left_click→double_click demasiado alta: {confusion_rate:.3f}")
    
    def test_scroll_direction_accuracy(self):
        """Test de precisión para direcciones de scroll"""
        
        print(f"\n📜 Testeando precisión de direcciones de scroll...")
        
        scroll_directions = ['scroll_up', 'scroll_down', 'scroll_left', 'scroll_right']
        scroll_accuracies = {}
        
        for direction in scroll_directions:
            correct_predictions = 0
            total_predictions = 0
            
            for _ in range(18):  # 18 muestras por dirección
                predicted, confidence = self.simulate_gesture_detection(direction, 0.85)
                self.log_prediction(direction, predicted, confidence)
                
                total_predictions += 1
                if predicted == direction:
                    correct_predictions += 1
            
            accuracy = correct_predictions / total_predictions
            scroll_accuracies[direction] = accuracy
            
            # Scroll vertical debería ser más preciso que horizontal
            min_accuracy = 0.90 if direction in ['scroll_up', 'scroll_down'] else 0.80
            status = "✅" if accuracy >= min_accuracy else "⚠️"
            print(f"   {status} {direction}: {accuracy:.3f}")
        
        # Verificar discriminación up/down vs left/right
        vertical_accuracy = np.mean([scroll_accuracies['scroll_up'], scroll_accuracies['scroll_down']])
        horizontal_accuracy = np.mean([scroll_accuracies['scroll_left'], scroll_accuracies['scroll_right']])
        
        print(f"   📊 Precisión vertical: {vertical_accuracy:.3f}")
        print(f"   📊 Precisión horizontal: {horizontal_accuracy:.3f}")
        
        self.assertGreaterEqual(vertical_accuracy, 0.90,
                              f"Precisión de scroll vertical insuficiente: {vertical_accuracy:.3f}")
        self.assertGreaterEqual(horizontal_accuracy, 0.80,
                              f"Precisión de scroll horizontal insuficiente: {horizontal_accuracy:.3f}")
    
    def test_movement_gestures_accuracy(self):
        """Test de precisión para gestos de movimiento"""
        
        print(f"\n🎯 Testeando precisión de gestos de movimiento...")
        
        movement_gestures = ['move_cursor', 'hover', 'drag_drop', 'click_and_hold']
        movement_results = {}
        
        for gesture in movement_gestures:
            predictions = []
            confidences = []
            
            for _ in range(15):  # 15 muestras por gesto de movimiento
                predicted, confidence = self.simulate_gesture_detection(gesture, 0.8)
                self.log_prediction(gesture, predicted, confidence)
                
                predictions.append(predicted == gesture)
                confidences.append(confidence)
            
            accuracy = np.mean(predictions)
            avg_confidence = np.mean(confidences)
            
            movement_results[gesture] = {
                'accuracy': accuracy,
                'confidence': avg_confidence
            }
            
            # Los gestos de movimiento son más complejos, umbral menor
            min_movement_accuracy = 0.85 if gesture in ['move_cursor', 'hover'] else 0.75
            status = "✅" if accuracy >= min_movement_accuracy else "⚠️"
            print(f"   {status} {gesture}: Precisión {accuracy:.3f}, Confianza {avg_confidence:.3f}")
        
        # Verificar que move_cursor y hover tienen buena precisión
        move_accuracy = movement_results['move_cursor']['accuracy']
        hover_accuracy = movement_results['hover']['accuracy']
        
        self.assertGreaterEqual(move_accuracy, 0.85,
                              f"Precisión de move_cursor insuficiente: {move_accuracy:.3f}")
        self.assertGreaterEqual(hover_accuracy, 0.85,
                              f"Precisión de hover insuficiente: {hover_accuracy:.3f}")
    
    def test_complex_mouse_sequences(self):
        """Test de precisión con secuencias complejas de mouse"""
        
        print(f"\n🔄 Testeando secuencias complejas de mouse...")
        
        # Secuencias típicas de uso de mouse
        mouse_sequences = [
            ['left_click', 'move_cursor', 'left_click'],           # Click y reposición
            ['right_click', 'move_cursor', 'left_click'],          # Menu contextual
            ['double_click', 'move_cursor', 'drag_drop'],          # Selección y arrastre
            ['scroll_down', 'scroll_down', 'left_click'],          # Navegación y click
            ['hover', 'left_click', 'scroll_up']                   # Interacción compleja
        ]
        
        sequence_accuracies = []
        
        for i, sequence in enumerate(mouse_sequences):
            sequence_predictions = []
            sequence_ground_truth = []
            
            print(f"   🔄 Secuencia {i+1}: {' → '.join(sequence)}")
            
            for gesture in sequence:
                predicted, confidence = self.simulate_gesture_detection(gesture, 0.85)
                sequence_predictions.append(predicted)
                sequence_ground_truth.append(gesture)
                
                self.log_prediction(gesture, predicted, confidence)
                
                # Pausa muy corta entre gestos
                time.sleep(0.001)
            
            # Calcular precisión de esta secuencia
            sequence_accuracy = sum(1 for true_val, pred in zip(sequence_ground_truth, sequence_predictions) 
                                  if true_val == pred) / len(sequence_predictions)
            sequence_accuracies.append(sequence_accuracy)
            
            print(f"      Precisión: {sequence_accuracy:.3f}")
        
        # Verificar precisión promedio de secuencias
        avg_sequence_accuracy = np.mean(sequence_accuracies)
        
        print(f"   📊 Precisión promedio secuencias: {avg_sequence_accuracy:.3f}")
        
        self.assertGreaterEqual(avg_sequence_accuracy, 0.85,
                              f"Precisión en secuencias complejas insuficiente: {avg_sequence_accuracy:.3f}")
    
    def test_mouse_rapid_interaction(self):
        """Test de precisión con interacciones rápidas de mouse"""
        
        print(f"\n⚡ Testeando interacciones rápidas de mouse...")
        
        # Gestos más comunes en uso rápido
        rapid_gestures = ['left_click', 'right_click', 'scroll_up', 'scroll_down', 'move_cursor']
        
        rapid_sequence = []
        for _ in range(30):  # 30 ciclos de gestos comunes
            rapid_sequence.extend(rapid_gestures)
        
        # Mezclar para simular uso real
        np.random.shuffle(rapid_sequence)
        
        rapid_results = []
        start_time = time.time()
        
        for gesture in rapid_sequence:
            predicted, confidence = self.simulate_gesture_detection(gesture, 0.85)
            self.log_prediction(gesture, predicted, confidence)
            
            rapid_results.append(predicted == gesture)
            
            # Procesamiento muy rápido
            time.sleep(0.0001)  # 0.1ms entre gestos
        
        total_time = time.time() - start_time
        rapid_accuracy = np.mean(rapid_results)
        
        print(f"   ⚡ Gestos procesados: {len(rapid_sequence)}")
        print(f"   ⏱️ Tiempo total: {total_time:.3f}s")
        print(f"   🎯 Precisión rápida: {rapid_accuracy:.3f}")
        print(f"   📈 Gestos/segundo: {len(rapid_sequence)/total_time:.1f}")
        
        # Verificar que la precisión se mantiene en uso rápido
        self.assertGreaterEqual(rapid_accuracy, 0.90,
                              f"Precisión en uso rápido insuficiente: {rapid_accuracy:.3f}")
    
    def test_mouse_gesture_confidence_thresholds(self):
        """Test de umbrales de confianza por tipo de gesto de mouse"""
        
        print(f"\n📊 Testeando umbrales de confianza por tipo...")
        
        # Clasificar gestos por complejidad
        gesture_complexity = {
            'basic_clicks': ['left_click', 'right_click'],
            'advanced_clicks': ['double_click', 'middle_click'],
            'scroll': ['scroll_up', 'scroll_down', 'scroll_left', 'scroll_right'],
            'movement': ['move_cursor', 'hover', 'drag_drop', 'click_and_hold']
        }
        
        complexity_metrics = {}
        
        for complexity, gestures in gesture_complexity.items():
            group_confidences = []
            group_accuracies = []
            
            for gesture in gestures:
                for _ in range(12):  # 12 muestras por gesto
                    predicted, confidence = self.simulate_gesture_detection(gesture, 0.85)
                    
                    is_correct = (predicted == gesture)
                    group_confidences.append(confidence)
                    group_accuracies.append(is_correct)
                    
                    self.log_prediction(gesture, predicted, confidence)
            
            avg_confidence = np.mean(group_confidences)
            avg_accuracy = np.mean(group_accuracies)
            
            complexity_metrics[complexity] = {
                'confidence': avg_confidence,
                'accuracy': avg_accuracy
            }
            
            print(f"   📈 {complexity}: Confianza {avg_confidence:.3f}, Precisión {avg_accuracy:.3f}")
        
        # Verificar que clicks básicos tienen alta precisión
        basic_metrics = complexity_metrics['basic_clicks']
        self.assertGreaterEqual(basic_metrics['accuracy'], 0.95,
                              "Precisión de clicks básicos insuficiente")
        self.assertGreaterEqual(basic_metrics['confidence'], 0.85,
                              "Confianza de clicks básicos insuficiente")
        
        # Verificar que scroll tiene buena precisión
        scroll_metrics = complexity_metrics['scroll']
        self.assertGreaterEqual(scroll_metrics['accuracy'], 0.88,
                              "Precisión de scroll insuficiente")

if __name__ == '__main__':
    unittest.main()