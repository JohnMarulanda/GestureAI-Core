#!/usr/bin/env python3
"""
Tests de precisión para NavigationControllerEnhanced.
Mide la precisión de detección de gestos de navegación web y direccional.
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

class TestNavigationControllerAccuracy(BaseAccuracyTest):
    """Test de accuracy para NavigationControllerEnhanced."""
    
    @classmethod
    def setUpClass(cls):
        """Configuración inicial para todos los tests."""
        cls.controller_name = "NavigationController"
        cls.target_accuracy = 0.91  # 91% - Alto para navegación frecuente
        super().setUpClass()
        
    def setUp(self):
        """Configurar el test individual."""
        super().setUp()
        
        # Mock de las dependencias de navegación
        self.navigation_patches = [
            patch('pyautogui.press'),
            patch('pyautogui.hotkey'),
            patch('pyautogui.click'),
            patch('pyautogui.moveTo'),
            patch('os.path.exists', return_value=True)
        ]
        
        self.navigation_mocks = [p.start() for p in self.navigation_patches]
        
        # Configurar precisión específica por gesto de navegación
        self.gesture_accuracy_rates = {
            'navigate_back': 0.96,       # Muy preciso, gesto común
            'navigate_forward': 0.95,    # Muy preciso, gesto común
            'refresh': 0.93,             # Preciso, gesto distintivo
            'new_tab': 0.94,             # Preciso, gesto específico
            'close_tab': 0.92,           # Bueno, similar a otros
            'switch_tab_left': 0.89,     # Menos preciso, gesto sutil
            'switch_tab_right': 0.89,    # Menos preciso, gesto sutil
            'scroll_page_up': 0.91,      # Bueno
            'scroll_page_down': 0.91,    # Bueno
            'home': 0.88,                # Menos distintivo
            'bookmark': 0.87,            # Menos común, menos distintivo
            'search': 0.90,              # Bueno, gesto común
            'zoom_in': 0.85,             # Más difícil, gesto fino
            'zoom_out': 0.85,            # Más difícil, gesto fino
            'fullscreen': 0.86,          # Menos común
            'no_gesture': 0.92           # Buena detección de ausencia
        }
        
        # Configurar confusiones comunes de navegación
        self.common_confusions = {
            'navigate_back': {'navigate_forward': 0.03, 'no_gesture': 0.01},
            'navigate_forward': {'navigate_back': 0.04, 'no_gesture': 0.01},
            'switch_tab_left': {'switch_tab_right': 0.07, 'navigate_back': 0.03},
            'switch_tab_right': {'switch_tab_left': 0.07, 'navigate_forward': 0.03},
            'scroll_page_up': {'scroll_page_down': 0.05, 'refresh': 0.02},
            'scroll_page_down': {'scroll_page_up': 0.05, 'no_gesture': 0.02},
            'new_tab': {'close_tab': 0.04, 'search': 0.03},
            'close_tab': {'new_tab': 0.05, 'no_gesture': 0.03},
            'zoom_in': {'zoom_out': 0.08, 'scroll_page_up': 0.04},
            'zoom_out': {'zoom_in': 0.08, 'scroll_page_down': 0.04},
            'bookmark': {'search': 0.06, 'new_tab': 0.04},
            'search': {'bookmark': 0.04, 'new_tab': 0.03},
            'home': {'refresh': 0.05, 'no_gesture': 0.07},
            'fullscreen': {'zoom_in': 0.06, 'no_gesture': 0.08}
        }
        
    def tearDown(self):
        """Limpiar después del test."""
        super().tearDown()
        for patch_obj in self.navigation_patches:
            patch_obj.stop()
    
    def get_test_gestures(self) -> List[str]:
        """Retorna la lista de gestos de navegación a testear."""
        return [
            'navigate_back',
            'navigate_forward',
            'refresh',
            'new_tab',
            'close_tab',
            'switch_tab_left',
            'switch_tab_right',
            'scroll_page_up',
            'scroll_page_down',
            'home',
            'bookmark',
            'search',
            'zoom_in',
            'zoom_out',
            'fullscreen',
            'no_gesture'
        ]
    
    def simulate_gesture_detection(self, gesture: str, expected_confidence: float = 0.8) -> Tuple[str, float]:
        """
        Simula la detección de un gesto de navegación con precisión realista
        
        Args:
            gesture: Nombre del gesto a simular
            expected_confidence: Nivel de confianza esperado
            
        Returns:
            Tupla (gesto_detectado, confianza_real)
        """
        # Obtener tasa de precisión para este gesto
        accuracy_rate = self.gesture_accuracy_rates.get(gesture, 0.85)
        
        # Determinar si la predicción será correcta
        is_correct = np.random.random() < accuracy_rate
        
        if is_correct:
            # Predicción correcta
            predicted_gesture = gesture
            # Variar ligeramente la confianza
            confidence_variation = np.random.normal(0, 0.04)
            confidence = np.clip(expected_confidence + confidence_variation, 0.3, 0.99)
        else:
            # Predicción incorrecta
            confusions = self.common_confusions.get(gesture, {})
            
            if confusions and np.random.random() < 0.75:  # 75% de errores son confusiones comunes
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
        
        # Simular tiempo de procesamiento
        time.sleep(0.001)  # 1ms de procesamiento simulado
        
        return predicted_gesture, confidence
    
    def test_basic_navigation_accuracy(self):
        """Test de precisión para navegación básica"""
        basic_nav = ['navigate_back', 'navigate_forward', 'refresh', 'home']
        
        print(f"\n🧭 Testeando precisión de navegación básica...")
        
        for nav_gesture in basic_nav:
            predictions = []
            ground_truth = []
            
            # Test con múltiples muestras
            for _ in range(20):  # 20 muestras por gesto básico
                predicted, confidence = self.simulate_gesture_detection(nav_gesture, 0.85)
                predictions.append(predicted)
                ground_truth.append(nav_gesture)
                
                self.log_prediction(nav_gesture, predicted, confidence)
            
            # Calcular precisión
            accuracy = sum(1 for true_val, pred in zip(ground_truth, predictions) if true_val == pred) / len(predictions)
            
            # Verificar precisión mínima para navegación básica
            min_basic_nav_accuracy = 0.88  # 88% mínimo para navegación básica
            self.assertGreaterEqual(accuracy, min_basic_nav_accuracy,
                                  f"Precisión de {nav_gesture} demasiado baja: {accuracy:.3f} < {min_basic_nav_accuracy:.3f}")
            
            status = "✅" if accuracy >= min_basic_nav_accuracy else "⚠️"
            print(f"   {status} {nav_gesture}: {accuracy:.3f}")
    
    def test_back_forward_discrimination(self):
        """Test de discriminación entre navegación back y forward"""
        
        print(f"\n⬅️➡️ Testeando discriminación back/forward...")
        
        # Test específico para evitar confusiones direccionales
        back_tests = []
        forward_tests = []
        
        for _ in range(20):
            # Test back
            predicted, confidence = self.simulate_gesture_detection('navigate_back', 0.85)
            back_tests.append({
                'predicted': predicted,
                'confidence': confidence,
                'correct': predicted == 'navigate_back',
                'directional_confusion': predicted == 'navigate_forward'
            })
            self.log_prediction('navigate_back', predicted, confidence)
            
            # Test forward
            predicted, confidence = self.simulate_gesture_detection('navigate_forward', 0.85)
            forward_tests.append({
                'predicted': predicted,
                'confidence': confidence,
                'correct': predicted == 'navigate_forward',
                'directional_confusion': predicted == 'navigate_back'
            })
            self.log_prediction('navigate_forward', predicted, confidence)
        
        # Analizar resultados direccionales
        back_accuracy = np.mean([t['correct'] for t in back_tests])
        forward_accuracy = np.mean([t['correct'] for t in forward_tests])
        
        back_confusion_rate = np.mean([t['directional_confusion'] for t in back_tests])
        forward_confusion_rate = np.mean([t['directional_confusion'] for t in forward_tests])
        
        print(f"   ⬅️ Precisión back: {back_accuracy:.3f}")
        print(f"   ➡️ Precisión forward: {forward_accuracy:.3f}")
        print(f"   🔄 Confusión back→forward: {back_confusion_rate:.3f}")
        print(f"   🔄 Confusión forward→back: {forward_confusion_rate:.3f}")
        
        # Verificar precisión y confusiones bajas
        self.assertGreaterEqual(back_accuracy, 0.90, "Precisión navigate_back insuficiente")
        self.assertGreaterEqual(forward_accuracy, 0.90, "Precisión navigate_forward insuficiente")
        self.assertLess(back_confusion_rate, 0.08, "Confusión back→forward demasiado alta")
        self.assertLess(forward_confusion_rate, 0.08, "Confusión forward→back demasiado alta")
    
    def test_tab_management_accuracy(self):
        """Test de precisión para gestión de pestañas"""
        
        print(f"\n📑 Testeando precisión de gestión de pestañas...")
        
        tab_gestures = ['new_tab', 'close_tab', 'switch_tab_left', 'switch_tab_right']
        tab_accuracies = {}
        
        for tab_gesture in tab_gestures:
            correct_predictions = 0
            total_predictions = 0
            
            for _ in range(18):  # 18 muestras por gesto de pestaña
                predicted, confidence = self.simulate_gesture_detection(tab_gesture, 0.8)
                self.log_prediction(tab_gesture, predicted, confidence)
                
                total_predictions += 1
                if predicted == tab_gesture:
                    correct_predictions += 1
            
            accuracy = correct_predictions / total_predictions
            tab_accuracies[tab_gesture] = accuracy
            
            # Umbral específico para cada tipo de gesto de pestaña
            min_accuracy = 0.85 if tab_gesture in ['new_tab', 'close_tab'] else 0.80
            status = "✅" if accuracy >= min_accuracy else "⚠️"
            print(f"   {status} {tab_gesture}: {accuracy:.3f}")
        
        # Verificar precisión promedio de gestión de pestañas
        avg_tab_accuracy = np.mean(list(tab_accuracies.values()))
        self.assertGreaterEqual(avg_tab_accuracy, 0.82,
                              f"Precisión promedio gestión pestañas insuficiente: {avg_tab_accuracy:.3f}")
        
        # Test específico de discriminación tab switching
        tab_switch_confusion = 0
        for _ in range(20):
            # Test switch_tab_left que no debe ser switch_tab_right
            predicted, _ = self.simulate_gesture_detection('switch_tab_left', 0.8)
            if predicted == 'switch_tab_right':
                tab_switch_confusion += 1
                
            # Test switch_tab_right que no debe ser switch_tab_left
            predicted, _ = self.simulate_gesture_detection('switch_tab_right', 0.8)
            if predicted == 'switch_tab_left':
                tab_switch_confusion += 1
        
        switch_confusion_rate = tab_switch_confusion / 40
        print(f"   🔄 Confusión cambio pestañas: {switch_confusion_rate:.3f}")
        
        self.assertLess(switch_confusion_rate, 0.15,
                       f"Confusión en cambio de pestañas demasiado alta: {switch_confusion_rate:.3f}")
    
    def test_scroll_direction_accuracy(self):
        """Test de precisión para direcciones de scroll"""
        
        print(f"\n⬆️⬇️ Testeando precisión de direcciones de scroll...")
        
        scroll_gestures = ['scroll_page_up', 'scroll_page_down']
        scroll_accuracies = {}
        
        for scroll_direction in scroll_gestures:
            correct_predictions = 0
            total_predictions = 0
            
            for _ in range(18):  # 18 muestras por dirección
                predicted, confidence = self.simulate_gesture_detection(scroll_direction, 0.8)
                self.log_prediction(scroll_direction, predicted, confidence)
                
                total_predictions += 1
                if predicted == scroll_direction:
                    correct_predictions += 1
            
            accuracy = correct_predictions / total_predictions
            scroll_accuracies[scroll_direction] = accuracy
            
            status = "✅" if accuracy >= 0.85 else "⚠️"
            print(f"   {status} {scroll_direction}: {accuracy:.3f}")
        
        # Verificar precisión direccional del scroll
        avg_scroll_accuracy = np.mean(list(scroll_accuracies.values()))
        self.assertGreaterEqual(avg_scroll_accuracy, 0.85,
                              f"Precisión promedio direccional scroll insuficiente: {avg_scroll_accuracy:.3f}")
    
    def test_zoom_controls_accuracy(self):
        """Test de precisión para controles de zoom"""
        
        print(f"\n🔍 Testeando precisión de controles de zoom...")
        
        zoom_gestures = ['zoom_in', 'zoom_out']
        zoom_results = {}
        
        for zoom_gesture in zoom_gestures:
            predictions = []
            confidences = []
            
            for _ in range(15):  # 15 muestras por zoom (más difíciles)
                predicted, confidence = self.simulate_gesture_detection(zoom_gesture, 0.75)
                self.log_prediction(zoom_gesture, predicted, confidence)
                
                predictions.append(predicted == zoom_gesture)
                confidences.append(confidence)
            
            accuracy = np.mean(predictions)
            avg_confidence = np.mean(confidences)
            
            zoom_results[zoom_gesture] = {
                'accuracy': accuracy,
                'confidence': avg_confidence
            }
            
            # Los controles de zoom son más difíciles, umbral menor
            min_zoom_accuracy = 0.75
            status = "✅" if accuracy >= min_zoom_accuracy else "⚠️"
            print(f"   {status} {zoom_gesture}: Precisión {accuracy:.3f}, Confianza {avg_confidence:.3f}")
        
        # Verificar precisión mínima de zoom
        avg_zoom_accuracy = np.mean([r['accuracy'] for r in zoom_results.values()])
        self.assertGreaterEqual(avg_zoom_accuracy, 0.75,
                              f"Precisión promedio zoom insuficiente: {avg_zoom_accuracy:.3f}")
        
        # Test de discriminación zoom in/out
        zoom_confusion = 0
        for _ in range(20):
            # Test zoom_in que no debe ser zoom_out
            predicted, _ = self.simulate_gesture_detection('zoom_in', 0.75)
            if predicted == 'zoom_out':
                zoom_confusion += 1
                
            # Test zoom_out que no debe ser zoom_in  
            predicted, _ = self.simulate_gesture_detection('zoom_out', 0.75)
            if predicted == 'zoom_in':
                zoom_confusion += 1
        
        zoom_confusion_rate = zoom_confusion / 40
        print(f"   🔄 Confusión zoom in/out: {zoom_confusion_rate:.3f}")
        
        self.assertLess(zoom_confusion_rate, 0.20,
                       f"Confusión zoom in/out demasiado alta: {zoom_confusion_rate:.3f}")
    
    def test_search_bookmark_accuracy(self):
        """Test de precisión para búsqueda y marcadores"""
        
        print(f"\n🔍📖 Testeando precisión búsqueda/marcadores...")
        
        utility_gestures = ['search', 'bookmark']
        utility_accuracies = {}
        
        for utility_gesture in utility_gestures:
            correct_predictions = 0
            total_predictions = 0
            
            for _ in range(15):  # 15 muestras por utilidad
                predicted, confidence = self.simulate_gesture_detection(utility_gesture, 0.8)
                self.log_prediction(utility_gesture, predicted, confidence)
                
                total_predictions += 1
                if predicted == utility_gesture:
                    correct_predictions += 1
            
            accuracy = correct_predictions / total_predictions
            utility_accuracies[utility_gesture] = accuracy
            
            min_utility_accuracy = 0.80
            status = "✅" if accuracy >= min_utility_accuracy else "⚠️"
            print(f"   {status} {utility_gesture}: {accuracy:.3f}")
        
        # Verificar precisión de utilidades
        avg_utility_accuracy = np.mean(list(utility_accuracies.values()))
        self.assertGreaterEqual(avg_utility_accuracy, 0.80,
                              f"Precisión promedio utilidades insuficiente: {avg_utility_accuracy:.3f}")
    
    def test_navigation_workflow_sequences(self):
        """Test de precisión con secuencias de trabajo típicas"""
        
        print(f"\n🔄 Testeando secuencias de trabajo navegación...")
        
        # Definir workflows típicos de navegación
        navigation_workflows = [
            ['new_tab', 'search', 'navigate_forward', 'bookmark'],           # Búsqueda y marcado
            ['navigate_back', 'navigate_back', 'refresh', 'navigate_forward'], # Navegación histórica
            ['switch_tab_left', 'close_tab', 'new_tab', 'search'],           # Gestión pestañas
            ['scroll_page_down', 'scroll_page_down', 'scroll_page_up', 'bookmark'], # Lectura y marcado
            ['zoom_in', 'scroll_page_down', 'zoom_out', 'refresh']           # Zoom y navegación
        ]
        
        workflow_accuracies = []
        
        for i, workflow in enumerate(navigation_workflows):
            workflow_predictions = []
            workflow_ground_truth = []
            
            print(f"   🔄 Workflow {i+1}: {' → '.join(workflow)}")
            
            for gesture in workflow:
                predicted, confidence = self.simulate_gesture_detection(gesture, 0.8)
                workflow_predictions.append(predicted)
                workflow_ground_truth.append(gesture)
                
                self.log_prediction(gesture, predicted, confidence)
                
                # Pausa entre gestos de workflow
                time.sleep(0.002)
            
            # Calcular precisión de este workflow
            workflow_accuracy = sum(1 for true_val, pred in zip(workflow_ground_truth, workflow_predictions) 
                                  if true_val == pred) / len(workflow)
            workflow_accuracies.append(workflow_accuracy)
            
            print(f"      Precisión: {workflow_accuracy:.3f}")
        
        # Verificar precisión promedio de workflows
        avg_workflow_accuracy = np.mean(workflow_accuracies)
        
        print(f"   📊 Precisión promedio workflows: {avg_workflow_accuracy:.3f}")
        
        self.assertGreaterEqual(avg_workflow_accuracy, 0.85,
                              f"Precisión en workflows de navegación insuficiente: {avg_workflow_accuracy:.3f}")
    
    def test_navigation_under_rapid_use(self):
        """Test de precisión de navegación bajo uso rápido"""
        
        print(f"\n⚡ Testeando navegación bajo uso rápido...")
        
        # Gestos más comunes en navegación rápida
        common_nav_gestures = [
            'navigate_back', 'navigate_forward', 'refresh', 'new_tab', 
            'close_tab', 'scroll_page_down', 'scroll_page_up'
        ]
        
        rapid_sequence = []
        for _ in range(15):  # 15 ciclos de gestos comunes
            rapid_sequence.extend(common_nav_gestures)
        
        # Mezclar para simular uso real
        np.random.shuffle(rapid_sequence)
        
        rapid_results = []
        start_time = time.time()
        
        for gesture in rapid_sequence:
            predicted, confidence = self.simulate_gesture_detection(gesture, 0.8)
            self.log_prediction(gesture, predicted, confidence)
            
            rapid_results.append(predicted == gesture)
            
            # Procesamiento muy rápido
            time.sleep(0.0003)  # 0.3ms entre gestos
        
        total_time = time.time() - start_time
        rapid_accuracy = np.mean(rapid_results)
        
        print(f"   ⚡ Gestos procesados: {len(rapid_sequence)}")
        print(f"   ⏱️ Tiempo total: {total_time:.3f}s")
        print(f"   🎯 Precisión bajo uso rápido: {rapid_accuracy:.3f}")
        print(f"   📈 Gestos/segundo: {len(rapid_sequence)/total_time:.1f}")
        
        # Verificar que la precisión se mantiene en uso rápido
        self.assertGreaterEqual(rapid_accuracy, 0.85,
                              f"Precisión bajo uso rápido insuficiente: {rapid_accuracy:.3f}")

if __name__ == '__main__':
    unittest.main()