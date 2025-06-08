#!/usr/bin/env python3
"""
Analizador de Modelo Real para Matriz de Confusión
Usa los modelos reales de MediaPipe para análisis en tiempo real
"""

import sys
import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Any, Optional
import mediapipe as mp
import json
from datetime import datetime
import time
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

class RealModelAnalyzer:
    """Analizador que usa el modelo real de MediaPipe"""
    
    def __init__(self, model_path: str = None):
        """
        Inicializar el analizador con modelo real
        
        Args:
            model_path: Ruta al modelo de MediaPipe
        """
        self.model_path = model_path or self._get_default_model_path()
        
        # Configurar MediaPipe
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Inicializar reconocedor de gestos
        self.gesture_recognizer = None
        self.hands_detector = None
        self._initialize_models()
        
        # Mapeo de gestos del modelo MediaPipe
        self.mediapipe_gestures = [
            'Closed_Fist', 'Open_Palm', 'Pointing_Up', 'Thumb_Down', 
            'Thumb_Up', 'Victory', 'ILoveYou'
        ]
        
        # Mapeo a nombres internos
        self.gesture_mapping = {
            'Closed_Fist': 'fist',
            'Open_Palm': 'open_palm', 
            'Pointing_Up': 'point_up',
            'Thumb_Down': 'thumb_down',
            'Thumb_Up': 'thumb_up',
            'Victory': 'victory',
            'ILoveYou': 'love_you'
        }
        
        # Resultados de análisis
        self.real_predictions = []
        self.ground_truth_labels = []
        self.confidence_scores = []
        
    def _get_default_model_path(self) -> str:
        """Obtener ruta por defecto del modelo"""
        base_path = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_path, '../../../../models/gesture_recognizer.task')
        return os.path.abspath(model_path)
    
    def _initialize_models(self):
        """Inicializar modelos de MediaPipe"""
        try:
            # Verificar que el modelo existe
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Modelo no encontrado: {self.model_path}")
            
            # Inicializar reconocedor de gestos
            BaseOptions = mp.tasks.BaseOptions
            GestureRecognizer = mp.tasks.vision.GestureRecognizer
            GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
            VisionRunningMode = mp.tasks.vision.RunningMode
            
            gesture_options = GestureRecognizerOptions(
                base_options=BaseOptions(model_asset_path=self.model_path),
                running_mode=VisionRunningMode.IMAGE,
                num_hands=1,
                min_hand_detection_confidence=0.7,
                min_hand_presence_confidence=0.5,
                min_tracking_confidence=0.5
            )
            
            self.gesture_recognizer = GestureRecognizer.create_from_options(gesture_options)
            
            # Inicializar detector de manos
            self.hands_detector = self.mp_hands.Hands(
                static_image_mode=True,
                max_num_hands=1,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.5
            )
            
            print(f"✅ Modelos inicializados correctamente")
            print(f"📁 Modelo: {os.path.basename(self.model_path)}")
            
        except Exception as e:
            print(f"❌ Error inicializando modelos: {e}")
            self.gesture_recognizer = None
            self.hands_detector = None
    
    def generate_synthetic_hand_image(self, gesture_type: str, image_size: Tuple[int, int] = (640, 480)) -> np.ndarray:
        """
        Generar imagen sintética de mano para un gesto específico
        
        Args:
            gesture_type: Tipo de gesto a generar
            image_size: Tamaño de la imagen (width, height)
            
        Returns:
            Imagen sintética como array numpy
        """
        width, height = image_size
        
        # Crear imagen base
        image = np.ones((height, width, 3), dtype=np.uint8) * 240  # Fondo gris claro
        
        # Coordenadas base de la mano (centro de la imagen)
        center_x, center_y = width // 2, height // 2
        
        # Definir puntos clave para diferentes gestos
        gesture_landmarks = {
            'fist': {
                'description': 'Puño cerrado',
                'finger_positions': [0.2, 0.1, 0.1, 0.1, 0.1],  # Todos los dedos cerrados
                'hand_rotation': 0
            },
            'open_palm': {
                'description': 'Palma abierta',
                'finger_positions': [1.0, 1.0, 1.0, 1.0, 1.0],  # Todos los dedos extendidos
                'hand_rotation': 0
            },
            'point_up': {
                'description': 'Apuntar hacia arriba',
                'finger_positions': [0.2, 1.0, 0.1, 0.1, 0.1],  # Solo índice extendido
                'hand_rotation': 0
            },
            'thumb_up': {
                'description': 'Pulgar arriba',
                'finger_positions': [1.0, 0.1, 0.1, 0.1, 0.1],  # Solo pulgar extendido
                'hand_rotation': 15
            },
            'thumb_down': {
                'description': 'Pulgar abajo',
                'finger_positions': [1.0, 0.1, 0.1, 0.1, 0.1],  # Solo pulgar extendido
                'hand_rotation': 180
            },
            'victory': {
                'description': 'Señal de victoria',
                'finger_positions': [0.2, 1.0, 1.0, 0.1, 0.1],  # Índice y medio extendidos
                'hand_rotation': 0
            },
            'love_you': {
                'description': 'Te amo (ASL)',
                'finger_positions': [1.0, 1.0, 0.1, 0.1, 1.0],  # Pulgar, índice y meñique
                'hand_rotation': 0
            }
        }
        
        if gesture_type not in gesture_landmarks:
            gesture_type = 'open_palm'  # Fallback
        
        gesture_config = gesture_landmarks[gesture_type]
        
        # Dibujar mano simplificada
        self._draw_simplified_hand(image, center_x, center_y, gesture_config)
        
        # Añadir algo de ruido realista
        noise = np.random.normal(0, 10, image.shape).astype(np.uint8)
        image = cv2.add(image, noise)
        
        return image
    
    def _draw_simplified_hand(self, image: np.ndarray, center_x: int, center_y: int, gesture_config: Dict):
        """Dibujar una representación simplificada de la mano"""
        
        # Colores
        hand_color = (220, 180, 140)  # Color de piel
        joint_color = (180, 140, 100)  # Color de articulaciones
        
        # Dimensiones base
        palm_radius = 60
        finger_length = 80
        finger_width = 12
        
        # Dibujar palma
        cv2.circle(image, (center_x, center_y), palm_radius, hand_color, -1)
        cv2.circle(image, (center_x, center_y), palm_radius, joint_color, 3)
        
        # Posiciones de dedos (relativas al centro de la palma)
        finger_positions = [
            (-40, -30),   # Pulgar
            (-20, -60),   # Índice
            (0, -65),     # Medio
            (20, -60),    # Anular
            (35, -50)     # Meñique
        ]
        
        finger_extensions = gesture_config['finger_positions']
        
        # Dibujar dedos
        for i, ((dx, dy), extension) in enumerate(zip(finger_positions, finger_extensions)):
            start_x = center_x + dx
            start_y = center_y + dy
            
            # Calcular longitud del dedo basada en extensión
            actual_length = int(finger_length * extension)
            
            if actual_length > 10:  # Solo dibujar si está extendido
                # Dirección del dedo
                if i == 0:  # Pulgar - dirección especial
                    end_x = start_x - int(actual_length * 0.7)
                    end_y = start_y - int(actual_length * 0.7)
                else:  # Otros dedos - hacia arriba
                    end_x = start_x
                    end_y = start_y - actual_length
                
                # Dibujar dedo como línea gruesa
                cv2.line(image, (start_x, start_y), (end_x, end_y), hand_color, finger_width)
                cv2.line(image, (start_x, start_y), (end_x, end_y), joint_color, 2)
                
                # Punta del dedo
                cv2.circle(image, (end_x, end_y), finger_width//2, joint_color, -1)
        
        # Añadir articulaciones de la palma
        for dx, dy in [(-20, -10), (20, -10), (0, 20)]:
            cv2.circle(image, (center_x + dx, center_y + dy), 4, joint_color, -1)
    
    def analyze_real_gesture_recognition(self, num_samples_per_gesture: int = 50) -> Dict[str, Any]:
        """
        Analizar reconocimiento de gestos usando el modelo real
        
        Args:
            num_samples_per_gesture: Número de muestras por gesto
            
        Returns:
            Análisis completo de reconocimiento
        """
        print("\n🔍 ANÁLISIS CON MODELO REAL DE MEDIAPIPE")
        print("="*60)
        
        if self.gesture_recognizer is None:
            raise RuntimeError("Reconocedor de gestos no inicializado")
        
        self.real_predictions.clear()
        self.ground_truth_labels.clear()
        self.confidence_scores.clear()
        
        total_samples = 0
        correct_predictions = 0
        
        # Analizar cada tipo de gesto
        for gesture_name in self.gesture_mapping.keys():
            internal_name = self.gesture_mapping[gesture_name]
            
            print(f"\n📝 Analizando gesto: {gesture_name} ({internal_name})")
            print("─" * 40)
            
            gesture_correct = 0
            gesture_total = 0
            
            for sample_idx in range(num_samples_per_gesture):
                try:
                    # Generar imagen sintética
                    test_image = self.generate_synthetic_hand_image(internal_name)
                    
                    # Convertir a formato MediaPipe
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=test_image)
                    
                    # Realizar predicción
                    results = self.gesture_recognizer.recognize(mp_image)
                    
                    # Procesar resultados
                    predicted_gesture = "None"
                    confidence = 0.0
                    
                    if results.gestures and len(results.gestures) > 0:
                        top_gesture = results.gestures[0][0]
                        predicted_gesture = top_gesture.category_name
                        confidence = top_gesture.score
                    
                    # Mapear a nombre interno
                    predicted_internal = self.gesture_mapping.get(predicted_gesture, 'unknown')
                    
                    # Registrar resultados
                    self.ground_truth_labels.append(internal_name)
                    self.real_predictions.append(predicted_internal)
                    self.confidence_scores.append(confidence)
                    
                    # Contar precisión
                    is_correct = (predicted_internal == internal_name)
                    if is_correct:
                        gesture_correct += 1
                        correct_predictions += 1
                    
                    gesture_total += 1
                    total_samples += 1
                    
                    # Mostrar progreso cada 10 muestras
                    if (sample_idx + 1) % 10 == 0:
                        current_accuracy = gesture_correct / gesture_total
                        print(f"  Muestra {sample_idx + 1:2d}/{num_samples_per_gesture}: {current_accuracy:.1%} precisión")
                
                except Exception as e:
                    print(f"  ❌ Error en muestra {sample_idx + 1}: {e}")
                    continue
            
            # Resumen del gesto
            gesture_accuracy = gesture_correct / gesture_total if gesture_total > 0 else 0
            print(f"  ✅ {gesture_name}: {gesture_accuracy:.1%} precisión ({gesture_correct}/{gesture_total})")
        
        # Calcular métricas globales
        overall_accuracy = correct_predictions / total_samples if total_samples > 0 else 0
        
        print(f"\n📊 RESUMEN GENERAL:")
        print(f"🎯 Precisión general: {overall_accuracy:.1%}")
        print(f"📈 Muestras procesadas: {total_samples}")
        print(f"✅ Predicciones correctas: {correct_predictions}")
        
        # Generar análisis detallado
        analysis_results = self._generate_detailed_analysis()
        
        return analysis_results
    
    def _generate_detailed_analysis(self) -> Dict[str, Any]:
        """Generar análisis detallado de los resultados"""
        
        if not self.real_predictions or not self.ground_truth_labels:
            return {}
        
        from sklearn.metrics import confusion_matrix, classification_report, accuracy_score
        
        # Obtener etiquetas únicas
        unique_labels = sorted(list(set(self.ground_truth_labels + self.real_predictions)))
        
        # Calcular matriz de confusión
        cm = confusion_matrix(self.ground_truth_labels, self.real_predictions, labels=unique_labels)
        
        # Calcular métricas
        accuracy = accuracy_score(self.ground_truth_labels, self.real_predictions)
        class_report = classification_report(self.ground_truth_labels, self.real_predictions, 
                                           labels=unique_labels, output_dict=True, zero_division=0)
        
        # Análisis de confianza
        confidence_analysis = self._analyze_confidence_patterns()
        
        # Análisis de confusiones
        confusion_analysis = self._analyze_confusion_patterns(cm, unique_labels)
        
        return {
            'overall_accuracy': accuracy,
            'confusion_matrix': cm,
            'class_report': class_report,
            'unique_labels': unique_labels,
            'confidence_analysis': confidence_analysis,
            'confusion_analysis': confusion_analysis,
            'total_samples': len(self.ground_truth_labels),
            'timestamp': datetime.now().isoformat()
        }
    
    def _analyze_confidence_patterns(self) -> Dict[str, Any]:
        """Analizar patrones de confianza"""
        
        if not self.confidence_scores:
            return {}
        
        confidence_by_gesture = {}
        
        for gt_label, pred_label, conf in zip(self.ground_truth_labels, self.real_predictions, self.confidence_scores):
            if gt_label not in confidence_by_gesture:
                confidence_by_gesture[gt_label] = {
                    'correct_confidences': [],
                    'incorrect_confidences': []
                }
            
            if gt_label == pred_label:
                confidence_by_gesture[gt_label]['correct_confidences'].append(conf)
            else:
                confidence_by_gesture[gt_label]['incorrect_confidences'].append(conf)
        
        # Calcular estadísticas
        confidence_stats = {}
        for gesture, data in confidence_by_gesture.items():
            correct_confs = data['correct_confidences']
            incorrect_confs = data['incorrect_confidences']
            
            confidence_stats[gesture] = {
                'avg_correct_confidence': np.mean(correct_confs) if correct_confs else 0,
                'avg_incorrect_confidence': np.mean(incorrect_confs) if incorrect_confs else 0,
                'min_correct_confidence': min(correct_confs) if correct_confs else 0,
                'max_correct_confidence': max(correct_confs) if correct_confs else 0,
                'confidence_separation': np.mean(correct_confs) - np.mean(incorrect_confs) if correct_confs and incorrect_confs else 0
            }
        
        return {
            'overall_avg_confidence': np.mean(self.confidence_scores),
            'overall_std_confidence': np.std(self.confidence_scores),
            'confidence_by_gesture': confidence_stats
        }
    
    def _analyze_confusion_patterns(self, cm: np.ndarray, labels: List[str]) -> Dict[str, Any]:
        """Analizar patrones de confusión"""
        
        # Normalizar matriz de confusión
        cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        cm_normalized = np.nan_to_num(cm_normalized)
        
        # Encontrar pares más confundidos
        confusion_pairs = []
        for i in range(len(labels)):
            for j in range(len(labels)):
                if i != j and cm_normalized[i][j] > 0.1:  # > 10% confusión
                    confusion_pairs.append({
                        'true_gesture': labels[i],
                        'predicted_gesture': labels[j],
                        'confusion_rate': cm_normalized[i][j],
                        'count': cm[i][j]
                    })
        
        confusion_pairs.sort(key=lambda x: x['confusion_rate'], reverse=True)
        
        # Calcular precisión por gesto
        gesture_accuracies = []
        for i, label in enumerate(labels):
            if cm[i].sum() > 0:
                accuracy = cm[i][i] / cm[i].sum()
                gesture_accuracies.append({
                    'gesture': label,
                    'accuracy': accuracy,
                    'total_samples': cm[i].sum(),
                    'correct_predictions': cm[i][i]
                })
        
        gesture_accuracies.sort(key=lambda x: x['accuracy'], reverse=True)
        
        return {
            'most_confused_pairs': confusion_pairs[:5],
            'gesture_accuracies': gesture_accuracies,
            'best_recognized': gesture_accuracies[:3] if gesture_accuracies else [],
            'worst_recognized': gesture_accuracies[-3:] if gesture_accuracies else []
        }
    
    def visualize_real_model_results(self, analysis: Dict[str, Any], save_path: str = None) -> str:
        """
        Visualizar resultados del modelo real
        
        Args:
            analysis: Resultados del análisis
            save_path: Ruta para guardar visualizaciones
            
        Returns:
            Ruta del archivo guardado
        """
        if not analysis:
            raise ValueError("No hay análisis para visualizar")
        
        # Crear visualización con múltiples subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Análisis del Modelo Real de MediaPipe', fontsize=16, fontweight='bold')
        
        # 1. Matriz de confusión
        cm = analysis['confusion_matrix']
        labels = analysis['unique_labels']
        
        cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        cm_normalized = np.nan_to_num(cm_normalized)
        
        sns.heatmap(cm_normalized, annot=True, fmt='.2f', cmap='Blues',
                   xticklabels=labels, yticklabels=labels, ax=ax1)
        ax1.set_title('Matriz de Confusión (Normalizada)')
        ax1.set_xlabel('Predicción')
        ax1.set_ylabel('Real')
        
        # 2. Precisión por gesto
        gesture_accs = analysis['confusion_analysis']['gesture_accuracies']
        gestures = [g['gesture'] for g in gesture_accs]
        accuracies = [g['accuracy'] for g in gesture_accs]
        
        bars = ax2.bar(gestures, accuracies, color='skyblue', edgecolor='navy')
        ax2.set_title('Precisión por Gesto')
        ax2.set_ylabel('Precisión')
        ax2.set_xlabel('Gesto')
        ax2.tick_params(axis='x', rotation=45)
        ax2.set_ylim(0, 1)
        
        # Añadir valores en las barras
        for bar, acc in zip(bars, accuracies):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{acc:.1%}', ha='center', va='bottom')
        
        # 3. Análisis de confianza
        conf_analysis = analysis['confidence_analysis']
        if conf_analysis and 'confidence_by_gesture' in conf_analysis:
            conf_data = conf_analysis['confidence_by_gesture']
            gestures_conf = list(conf_data.keys())
            correct_confs = [conf_data[g]['avg_correct_confidence'] for g in gestures_conf]
            incorrect_confs = [conf_data[g]['avg_incorrect_confidence'] for g in gestures_conf]
            
            x_pos = np.arange(len(gestures_conf))
            width = 0.35
            
            ax3.bar(x_pos - width/2, correct_confs, width, label='Predicciones correctas', color='green', alpha=0.7)
            ax3.bar(x_pos + width/2, incorrect_confs, width, label='Predicciones incorrectas', color='red', alpha=0.7)
            
            ax3.set_title('Confianza Promedio por Gesto')
            ax3.set_ylabel('Confianza')
            ax3.set_xlabel('Gesto')
            ax3.set_xticks(x_pos)
            ax3.set_xticklabels(gestures_conf, rotation=45)
            ax3.legend()
            ax3.set_ylim(0, 1)
        
        # 4. Patrones de confusión más problemáticos
        confused_pairs = analysis['confusion_analysis']['most_confused_pairs']
        if confused_pairs:
            pair_labels = [f"{p['true_gesture']} →\n{p['predicted_gesture']}" for p in confused_pairs[:5]]
            confusion_rates = [p['confusion_rate'] for p in confused_pairs[:5]]
            
            bars = ax4.bar(range(len(pair_labels)), confusion_rates, color='orange', edgecolor='darkred')
            ax4.set_title('Principales Confusiones')
            ax4.set_ylabel('Tasa de Confusión')
            ax4.set_xlabel('Par de Gestos')
            ax4.set_xticks(range(len(pair_labels)))
            ax4.set_xticklabels(pair_labels, rotation=45, ha='right')
            
            # Añadir valores
            for bar, rate in zip(bars, confusion_rates):
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                        f'{rate:.1%}', ha='center', va='bottom')
        
        plt.tight_layout()
        
        # Guardar
        if save_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_dir = os.path.join(os.path.dirname(__file__), 'reports', 'visualizations')
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, f'real_model_analysis_{timestamp}.png')
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Visualización guardada: {save_path}")
        return save_path
    
    def generate_calibration_report(self, analysis: Dict[str, Any]) -> str:
        """
        Generar reporte de calibración del modelo real
        
        Args:
            analysis: Resultados del análisis
            
        Returns:
            Ruta del reporte generado
        """
        report = []
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        report.append("# REPORTE DE CALIBRACIÓN - MODELO REAL MEDIAPIPE")
        report.append(f"Generado: {timestamp}")
        report.append("=" * 70)
        
        # Información del modelo
        report.append(f"\n## 🔧 INFORMACIÓN DEL MODELO")
        report.append(f"Modelo utilizado: {os.path.basename(self.model_path)}")
        report.append(f"Muestras analizadas: {analysis['total_samples']}")
        report.append(f"Precisión general: {analysis['overall_accuracy']:.1%}")
        
        # Análisis por gesto
        report.append(f"\n## 📊 ANÁLISIS POR GESTO")
        gesture_accs = analysis['confusion_analysis']['gesture_accuracies']
        
        for gesture_data in gesture_accs:
            gesture = gesture_data['gesture']
            accuracy = gesture_data['accuracy']
            total = gesture_data['total_samples']
            correct = gesture_data['correct_predictions']
            
            status = "🟢" if accuracy >= 0.9 else "🟡" if accuracy >= 0.7 else "🔴"
            report.append(f"{status} {gesture}: {accuracy:.1%} ({correct}/{total})")
        
        # Análisis de confianza
        conf_analysis = analysis['confidence_analysis']
        report.append(f"\n## 🎯 ANÁLISIS DE CONFIANZA")
        report.append(f"Confianza promedio general: {conf_analysis['overall_avg_confidence']:.3f}")
        report.append(f"Desviación estándar: {conf_analysis['overall_std_confidence']:.3f}")
        
        if 'confidence_by_gesture' in conf_analysis:
            report.append(f"\nConfianza por gesto:")
            for gesture, conf_data in conf_analysis['confidence_by_gesture'].items():
                avg_correct = conf_data['avg_correct_confidence']
                avg_incorrect = conf_data['avg_incorrect_confidence']
                separation = conf_data['confidence_separation']
                
                report.append(f"  {gesture}:")
                report.append(f"    - Correctas: {avg_correct:.3f}")
                report.append(f"    - Incorrectas: {avg_incorrect:.3f}")
                report.append(f"    - Separación: {separation:.3f}")
        
        # Confusiones principales
        confused_pairs = analysis['confusion_analysis']['most_confused_pairs']
        if confused_pairs:
            report.append(f"\n## ⚠️ PRINCIPALES CONFUSIONES")
            for i, pair in enumerate(confused_pairs, 1):
                true_gesture = pair['true_gesture']
                pred_gesture = pair['predicted_gesture']
                rate = pair['confusion_rate']
                count = pair['count']
                
                report.append(f"{i}. {true_gesture} → {pred_gesture}: {rate:.1%} ({count} casos)")
        
        # Recomendaciones
        report.append(f"\n## 💡 RECOMENDACIONES DE CALIBRACIÓN")
        
        worst_gestures = analysis['confusion_analysis']['worst_recognized']
        if worst_gestures:
            worst_names = [g['gesture'] for g in worst_gestures if g['accuracy'] < 0.8]
            if worst_names:
                report.append(f"• Mejorar entrenamiento para: {', '.join(worst_names)}")
        
        if confused_pairs:
            main_confusion = confused_pairs[0]
            if main_confusion['confusion_rate'] > 0.2:
                report.append(f"• Revisar características distintivas entre "
                            f"{main_confusion['true_gesture']} y {main_confusion['predicted_gesture']}")
        
        low_conf_gestures = []
        for gesture, conf_data in conf_analysis.get('confidence_by_gesture', {}).items():
            if conf_data['avg_correct_confidence'] < 0.7:
                low_conf_gestures.append(gesture)
        
        if low_conf_gestures:
            report.append(f"• Ajustar umbrales de confianza para: {', '.join(low_conf_gestures)}")
        
        # Guardar reporte
        timestamp_file = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_dir = os.path.join(os.path.dirname(__file__), 'reports')
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, f'calibration_report_{timestamp_file}.txt')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        print(f"📝 Reporte de calibración guardado: {report_path}")
        return report_path


def main():
    """Función principal para ejecutar análisis del modelo real"""
    print("🧠 ANALIZADOR DE MODELO REAL - MEDIAPIPE")
    print("="*50)
    
    analyzer = RealModelAnalyzer()
    
    if analyzer.gesture_recognizer is None:
        print("❌ No se pudo inicializar el modelo. Verifica que el archivo .task esté disponible.")
        return
    
    try:
        # Ejecutar análisis
        print("\n🚀 Iniciando análisis con modelo real...")
        results = analyzer.analyze_real_gesture_recognition(num_samples_per_gesture=30)
        
        # Generar visualizaciones
        print("\n📊 Generando visualizaciones...")
        analyzer.visualize_real_model_results(results)
        
        # Generar reporte de calibración
        print("\n📝 Generando reporte de calibración...")
        analyzer.generate_calibration_report(results)
        
        print("\n✅ Análisis del modelo real completado!")
        
    except Exception as e:
        print(f"\n❌ Error durante el análisis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()