#!/usr/bin/env python3
"""
Clase base para tests de precisión de detección de gestos.
Proporciona funcionalidades comunes para medir accuracy, precision, recall, F1-score.
"""

import time
import logging
import unittest
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from collections import defaultdict, Counter
import json
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)

class AccuracyMetrics:
    """Clase para calcular métricas de precisión"""
    
    @staticmethod
    def calculate_confusion_matrix(y_true: List[str], y_pred: List[str], labels: List[str]) -> np.ndarray:
        """
        Calcula la matriz de confusión
        
        Args:
            y_true: Etiquetas verdaderas
            y_pred: Predicciones
            labels: Lista de etiquetas únicas
            
        Returns:
            Matriz de confusión
        """
        matrix = np.zeros((len(labels), len(labels)), dtype=int)
        label_to_idx = {label: idx for idx, label in enumerate(labels)}
        
        for true_label, pred_label in zip(y_true, y_pred):
            if true_label in label_to_idx and pred_label in label_to_idx:
                true_idx = label_to_idx[true_label]
                pred_idx = label_to_idx[pred_label]
                matrix[true_idx][pred_idx] += 1
        
        return matrix
    
    @staticmethod
    def calculate_precision_recall_f1(confusion_matrix: np.ndarray, labels: List[str]) -> Dict[str, Dict[str, float]]:
        """
        Calcula precision, recall y F1-score por clase
        
        Args:
            confusion_matrix: Matriz de confusión
            labels: Lista de etiquetas
            
        Returns:
            Dict con métricas por clase
        """
        metrics = {}
        
        for i, label in enumerate(labels):
            # True Positives, False Positives, False Negatives
            tp = confusion_matrix[i, i]
            fp = np.sum(confusion_matrix[:, i]) - tp
            fn = np.sum(confusion_matrix[i, :]) - tp
            
            # Calcular métricas
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            
            metrics[label] = {
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'true_positives': int(tp),
                'false_positives': int(fp),
                'false_negatives': int(fn),
                'support': int(tp + fn)
            }
        
        return metrics
    
    @staticmethod
    def calculate_overall_accuracy(y_true: List[str], y_pred: List[str]) -> float:
        """
        Calcula la precisión general
        
        Args:
            y_true: Etiquetas verdaderas
            y_pred: Predicciones
            
        Returns:
            Precisión general (0-1)
        """
        if len(y_true) != len(y_pred) or len(y_true) == 0:
            return 0.0
        
        correct = sum(1 for true_label, pred_label in zip(y_true, y_pred) if true_label == pred_label)
        return correct / len(y_true)
    
    @staticmethod
    def calculate_weighted_metrics(class_metrics: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """
        Calcula métricas promedio ponderadas por soporte
        
        Args:
            class_metrics: Métricas por clase
            
        Returns:
            Métricas promedio ponderadas
        """
        total_support = sum(metrics['support'] for metrics in class_metrics.values())
        
        if total_support == 0:
            return {'weighted_precision': 0.0, 'weighted_recall': 0.0, 'weighted_f1': 0.0}
        
        weighted_precision = sum(metrics['precision'] * metrics['support'] for metrics in class_metrics.values()) / total_support
        weighted_recall = sum(metrics['recall'] * metrics['support'] for metrics in class_metrics.values()) / total_support
        weighted_f1 = sum(metrics['f1_score'] * metrics['support'] for metrics in class_metrics.values()) / total_support
        
        return {
            'weighted_precision': weighted_precision,
            'weighted_recall': weighted_recall,
            'weighted_f1': weighted_f1
        }

class BaseAccuracyTest(unittest.TestCase, ABC):
    """Clase base abstracta para tests de precisión de controladores"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.timing_data = []
        self.accuracy_results = {}
        self.test_start_time = None
        
        # Configuración por defecto
        self.test_iterations = 100
        self.confidence_threshold = 0.7
        self.target_accuracy = 0.90  # 90% por defecto
        self.min_samples_per_gesture = 10
        
    @classmethod
    def setUpClass(cls):
        """Configuración inicial para todos los tests de la clase"""
        cls.controller_name = getattr(cls, 'controller_name', 'UnknownController')
        cls.target_accuracy = getattr(cls, 'target_accuracy', 0.90)
        print(f"\n🎯 Iniciando tests de precisión para {cls.controller_name}")
        print(f"   Objetivo de precisión: {cls.target_accuracy*100:.1f}%")
    
    def setUp(self):
        """Configurar el test individual"""
        self.test_start_time = time.time()
        self.accuracy_results = {
            'predictions': [],
            'ground_truth': [],
            'confidence_scores': [],
            'timing_data': [],
            'test_metadata': {
                'controller': self.controller_name,
                'timestamp': datetime.now().isoformat(),
                'test_method': self._testMethodName
            }
        }
    
    def tearDown(self):
        """Limpiar después del test"""
        test_duration = time.time() - self.test_start_time
        self.logger.info(f"Test {self._testMethodName} completado en {test_duration:.3f}s")
    
    @abstractmethod
    def get_test_gestures(self) -> List[str]:
        """
        Retorna la lista de gestos a testear para este controlador
        
        Returns:
            Lista de nombres de gestos
        """
        pass
    
    @abstractmethod
    def simulate_gesture_detection(self, gesture: str, confidence: float = 0.8) -> Tuple[str, float]:
        """
        Simula la detección de un gesto específico
        
        Args:
            gesture: Nombre del gesto a simular
            confidence: Nivel de confianza esperado
            
        Returns:
            Tupla (gesto_detectado, confianza_real)
        """
        pass
    
    def log_prediction(self, true_gesture: str, predicted_gesture: str, confidence: float, detection_time: float = 0.0):
        """
        Registra una predicción para análisis posterior
        
        Args:
            true_gesture: Gesto verdadero
            predicted_gesture: Gesto predicho
            confidence: Confianza de la predicción
            detection_time: Tiempo de detección en ms
        """
        self.accuracy_results['ground_truth'].append(true_gesture)
        self.accuracy_results['predictions'].append(predicted_gesture)
        self.accuracy_results['confidence_scores'].append(confidence)
        self.accuracy_results['timing_data'].append(detection_time)
    
    def calculate_accuracy_metrics(self) -> Dict[str, Any]:
        """
        Calcula métricas de precisión basadas en las predicciones registradas
        
        Returns:
            Dict con todas las métricas de precisión
        """
        if not self.accuracy_results['predictions']:
            return {'error': 'No hay predicciones registradas'}
        
        y_true = self.accuracy_results['ground_truth']
        y_pred = self.accuracy_results['predictions']
        confidence_scores = self.accuracy_results['confidence_scores']
        
        # Obtener etiquetas únicas
        unique_labels = sorted(list(set(y_true + y_pred)))
        
        # Calcular métricas
        overall_accuracy = AccuracyMetrics.calculate_overall_accuracy(y_true, y_pred)
        confusion_matrix = AccuracyMetrics.calculate_confusion_matrix(y_true, y_pred, unique_labels)
        class_metrics = AccuracyMetrics.calculate_precision_recall_f1(confusion_matrix, unique_labels)
        weighted_metrics = AccuracyMetrics.calculate_weighted_metrics(class_metrics)
        
        # Estadísticas de confianza
        confidence_stats = {
            'mean_confidence': np.mean(confidence_scores),
            'median_confidence': np.median(confidence_scores),
            'min_confidence': np.min(confidence_scores),
            'max_confidence': np.max(confidence_scores),
            'std_confidence': np.std(confidence_scores)
        }
        
        # Análisis de errores
        error_analysis = self._analyze_errors(y_true, y_pred, confidence_scores)
        
        return {
            'overall_accuracy': overall_accuracy,
            'confusion_matrix': confusion_matrix.tolist(),
            'class_metrics': class_metrics,
            'weighted_metrics': weighted_metrics,
            'confidence_stats': confidence_stats,
            'error_analysis': error_analysis,
            'labels': unique_labels,
            'total_samples': len(y_true),
            'target_achieved': overall_accuracy >= self.target_accuracy
        }
    
    def _analyze_errors(self, y_true: List[str], y_pred: List[str], confidence_scores: List[float]) -> Dict[str, Any]:
        """
        Analiza los errores de predicción
        
        Args:
            y_true: Etiquetas verdaderas
            y_pred: Predicciones
            confidence_scores: Scores de confianza
            
        Returns:
            Análisis de errores
        """
        errors = []
        high_confidence_errors = []
        low_confidence_correct = []
        
        for i, (true_label, pred_label, confidence) in enumerate(zip(y_true, y_pred, confidence_scores)):
            if true_label != pred_label:
                error_info = {
                    'index': i,
                    'true_gesture': true_label,
                    'predicted_gesture': pred_label,
                    'confidence': confidence
                }
                errors.append(error_info)
                
                if confidence > 0.8:  # Errores con alta confianza
                    high_confidence_errors.append(error_info)
            else:
                if confidence < 0.6:  # Predicciones correctas con baja confianza
                    low_confidence_correct.append({
                        'index': i,
                        'gesture': true_label,
                        'confidence': confidence
                    })
        
        # Análisis de confusiones más comunes
        confusion_pairs = Counter()
        for error in errors:
            pair = (error['true_gesture'], error['predicted_gesture'])
            confusion_pairs[pair] += 1
        
        return {
            'total_errors': len(errors),
            'error_rate': len(errors) / len(y_true),
            'high_confidence_errors': len(high_confidence_errors),
            'low_confidence_correct': len(low_confidence_correct),
            'most_confused_pairs': confusion_pairs.most_common(5),
            'error_details': errors[:10]  # Primeros 10 errores para debugging
        }
    
    def generate_test_sequences(self, gesture_counts: Dict[str, int]) -> List[Tuple[str, float]]:
        """
        Genera secuencias de test balanceadas
        
        Args:
            gesture_counts: Dict con cantidad de muestras por gesto
            
        Returns:
            Lista de tuplas (gesto, confianza_esperada)
        """
        sequences = []
        
        for gesture, count in gesture_counts.items():
            for i in range(count):
                # Variar confianza para crear datos más realistas
                base_confidence = 0.8
                confidence_variation = np.random.normal(0, 0.1)  # Variación normal
                confidence = np.clip(base_confidence + confidence_variation, 0.3, 0.99)
                
                sequences.append((gesture, confidence))
        
        # Mezclar secuencias para evitar patrones
        np.random.shuffle(sequences)
        return sequences
    
    def test_overall_accuracy(self):
        """Test de precisión general del controlador"""
        gestures = self.get_test_gestures()
        
        # Generar secuencias de test balanceadas
        gesture_counts = {gesture: self.min_samples_per_gesture for gesture in gestures}
        test_sequences = self.generate_test_sequences(gesture_counts)
        
        print(f"\n🎯 Testear precisión general con {len(test_sequences)} muestras...")
        
        for true_gesture, expected_confidence in test_sequences:
            start_time = time.time()
            predicted_gesture, actual_confidence = self.simulate_gesture_detection(true_gesture, expected_confidence)
            detection_time = (time.time() - start_time) * 1000  # ms
            
            self.log_prediction(true_gesture, predicted_gesture, actual_confidence, detection_time)
        
        # Calcular métricas
        metrics = self.calculate_accuracy_metrics()
        
        # Assertions
        self.assertGreaterEqual(metrics['overall_accuracy'], self.target_accuracy,
                              f"Precisión general {metrics['overall_accuracy']:.3f} por debajo del objetivo {self.target_accuracy:.3f}")
        
        self.assertLess(metrics['error_analysis']['error_rate'], 1 - self.target_accuracy,
                       f"Tasa de error demasiado alta: {metrics['error_analysis']['error_rate']:.3f}")
        
        print(f"✅ Precisión general: {metrics['overall_accuracy']:.3f} (objetivo: {self.target_accuracy:.3f})")
        print(f"📊 Precisión ponderada: {metrics['weighted_metrics']['weighted_precision']:.3f}")
        print(f"📈 Recall ponderado: {metrics['weighted_metrics']['weighted_recall']:.3f}")
        print(f"🎯 F1-score ponderado: {metrics['weighted_metrics']['weighted_f1']:.3f}")
        
        return metrics
    
    def test_individual_gesture_accuracy(self):
        """Test de precisión por gesto individual"""
        gestures = self.get_test_gestures()
        individual_results = {}
        
        print(f"\n🔍 Testeando precisión individual para {len(gestures)} gestos...")
        
        for gesture in gestures:
            # Test específico para este gesto
            gesture_predictions = []
            gesture_ground_truth = []
            
            for _ in range(self.min_samples_per_gesture):
                predicted_gesture, confidence = self.simulate_gesture_detection(gesture, 0.8)
                gesture_predictions.append(predicted_gesture)
                gesture_ground_truth.append(gesture)
            
            # Calcular precisión individual
            accuracy = AccuracyMetrics.calculate_overall_accuracy(gesture_ground_truth, gesture_predictions)
            individual_results[gesture] = {
                'accuracy': accuracy,
                'samples': len(gesture_predictions),
                'target_met': accuracy >= self.target_accuracy
            }
            
            # Log resultados
            status = "✅" if accuracy >= self.target_accuracy else "⚠️"
            print(f"   {status} {gesture}: {accuracy:.3f}")
        
        # Verificar que la mayoría cumple el objetivo
        passing_gestures = sum(1 for result in individual_results.values() if result['target_met'])
        passing_rate = passing_gestures / len(gestures)
        
        self.assertGreaterEqual(passing_rate, 0.8,
                              f"Solo {passing_rate:.1%} de gestos cumplen objetivo (mínimo 80%)")
        
        return individual_results
    
    def test_confidence_calibration(self):
        """Test de calibración de confianza"""
        gestures = self.get_test_gestures()
        calibration_data = []
        
        print(f"\n📊 Testeando calibración de confianza...")
        
        # Test con diferentes niveles de confianza
        confidence_levels = [0.3, 0.5, 0.7, 0.9]
        
        for confidence_target in confidence_levels:
            for gesture in gestures[:3]:  # Solo algunos gestos para eficiencia
                for _ in range(5):  # Pocas muestras por nivel
                    predicted_gesture, actual_confidence = self.simulate_gesture_detection(gesture, confidence_target)
                    
                    calibration_data.append({
                        'target_confidence': confidence_target,
                        'actual_confidence': actual_confidence,
                        'correct_prediction': gesture == predicted_gesture
                    })
        
        # Analizar calibración
        confidence_analysis = self._analyze_confidence_calibration(calibration_data)
        
        # Verificar que la confianza esté bien calibrada
        self.assertLess(abs(confidence_analysis['mean_calibration_error']), 0.2,
                       "Error de calibración de confianza demasiado alto")
        
        print(f"📈 Error medio de calibración: {confidence_analysis['mean_calibration_error']:.3f}")
        
        return confidence_analysis
    
    def _analyze_confidence_calibration(self, calibration_data: List[Dict]) -> Dict[str, float]:
        """
        Analiza la calibración de confianza
        
        Args:
            calibration_data: Datos de calibración
            
        Returns:
            Análisis de calibración
        """
        if not calibration_data:
            return {'mean_calibration_error': 1.0}
        
        # Agrupar por bins de confianza
        bins = np.linspace(0, 1, 11)  # 10 bins
        bin_accuracies = []
        bin_confidences = []
        
        for i in range(len(bins) - 1):
            bin_data = [d for d in calibration_data 
                       if bins[i] <= d['actual_confidence'] < bins[i+1]]
            
            if bin_data:
                bin_accuracy = np.mean([d['correct_prediction'] for d in bin_data])
                bin_confidence = np.mean([d['actual_confidence'] for d in bin_data])
                
                bin_accuracies.append(bin_accuracy)
                bin_confidences.append(bin_confidence)
        
        # Calcular error de calibración esperado (ECE)
        if bin_accuracies and bin_confidences:
            calibration_errors = [abs(acc - conf) for acc, conf in zip(bin_accuracies, bin_confidences)]
            mean_calibration_error = np.mean(calibration_errors)
        else:
            mean_calibration_error = 1.0
        
        return {
            'mean_calibration_error': mean_calibration_error,
            'bin_accuracies': bin_accuracies,
            'bin_confidences': bin_confidences
        }
    
    def run_accuracy_test_suite(self) -> Dict[str, Any]:
        """
        Ejecuta la suite completa de tests de precisión
        
        Returns:
            Resultados consolidados
        """
        print(f"\n🚀 Ejecutando suite de precisión para {self.controller_name}...")
        
        suite_results = {
            'controller': self.controller_name,
            'timestamp': datetime.now().isoformat(),
            'tests': {}
        }
        
        try:
            # Test 1: Precisión general
            suite_results['tests']['overall_accuracy'] = self.test_overall_accuracy()
            
            # Test 2: Precisión individual por gesto
            suite_results['tests']['individual_gestures'] = self.test_individual_gesture_accuracy()
            
            # Test 3: Calibración de confianza
            suite_results['tests']['confidence_calibration'] = self.test_confidence_calibration()
            
            # Resumen consolidado
            suite_results['summary'] = self._create_suite_summary(suite_results['tests'])
            
            print(f"✅ Suite de precisión completada para {self.controller_name}")
            
        except Exception as e:
            suite_results['error'] = str(e)
            print(f"❌ Error en suite de precisión: {e}")
        
        return suite_results
    
    def _create_suite_summary(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea resumen consolidado de la suite
        
        Args:
            test_results: Resultados de todos los tests
            
        Returns:
            Resumen consolidado
        """
        summary = {
            'overall_status': 'unknown',
            'target_accuracy_met': False,
            'key_metrics': {},
            'recommendations': []
        }
        
        # Extraer métricas clave
        if 'overall_accuracy' in test_results:
            overall_acc = test_results['overall_accuracy']['overall_accuracy']
            summary['key_metrics']['overall_accuracy'] = overall_acc
            summary['target_accuracy_met'] = overall_acc >= self.target_accuracy
            
            if overall_acc >= self.target_accuracy:
                summary['overall_status'] = 'excellent' if overall_acc >= 0.95 else 'good'
            else:
                summary['overall_status'] = 'needs_improvement'
        
        # Recomendaciones basadas en resultados
        if summary.get('target_accuracy_met', False):
            summary['recommendations'].append("✅ El controlador cumple los objetivos de precisión")
        else:
            summary['recommendations'].append("⚠️ Revisar algoritmos de detección de gestos")
            summary['recommendations'].append("🔧 Considerar ajustar umbrales de confianza")
        
        return summary

if __name__ == '__main__':
    # Esta clase es abstracta, no se puede ejecutar directamente
    print("BaseAccuracyTest es una clase abstracta. Use las implementaciones específicas.")