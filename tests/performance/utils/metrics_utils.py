"""
Utilidades para el cálculo y visualización de métricas de rendimiento.
Incluye funciones para matriz de confusión, ROC, precisión, recall, etc.
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Tuple, Any, Optional
from sklearn.metrics import confusion_matrix, classification_report, roc_curve, auc
import pandas as pd
from datetime import datetime
import json

class MetricsCalculator:
    """Clase para calcular métricas avanzadas de rendimiento"""
    
    @staticmethod
    def calculate_confusion_matrix(y_true: List[Any], y_pred: List[Any], 
                                 labels: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Calcula la matriz de confusión y métricas relacionadas
        
        Args:
            y_true: Valores reales
            y_pred: Predicciones
            labels: Etiquetas de las clases (opcional)
            
        Returns:
            Dict con matriz de confusión y métricas
        """
        cm = confusion_matrix(y_true, y_pred, labels=labels)
        
        # Calcular métricas por clase
        tn, fp, fn, tp = cm.ravel() if cm.shape == (2, 2) else (0, 0, 0, 0)
        
        metrics = {
            'confusion_matrix': cm.tolist(),
            'true_positives': int(tp) if cm.shape == (2, 2) else cm.diagonal().tolist(),
            'false_positives': int(fp) if cm.shape == (2, 2) else (cm.sum(axis=0) - cm.diagonal()).tolist(),
            'false_negatives': int(fn) if cm.shape == (2, 2) else (cm.sum(axis=1) - cm.diagonal()).tolist(),
            'true_negatives': int(tn) if cm.shape == (2, 2) else None,
            'labels': labels if labels else list(range(len(cm)))
        }
        
        return metrics
    
    @staticmethod
    def calculate_precision_recall_f1(y_true: List[Any], y_pred: List[Any], 
                                    labels: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Calcula precisión, recall y F1-score
        
        Args:
            y_true: Valores reales
            y_pred: Predicciones 
            labels: Etiquetas de las clases (opcional)
            
        Returns:
            Dict con métricas de precisión, recall y F1
        """
        cm = confusion_matrix(y_true, y_pred, labels=labels)
        
        # Para matriz binaria
        if cm.shape == (2, 2):
            tn, fp, fn, tp = cm.ravel()
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            return {
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'specificity': tn / (tn + fp) if (tn + fp) > 0 else 0
            }
        
        # Para matriz multiclase
        else:
            precisions = []
            recalls = []
            f1s = []
            
            for i in range(len(cm)):
                tp = cm[i, i]
                fp = cm[:, i].sum() - tp
                fn = cm[i, :].sum() - tp
                
                precision = tp / (tp + fp) if (tp + fp) > 0 else 0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0
                f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
                
                precisions.append(precision)
                recalls.append(recall)
                f1s.append(f1)
            
            return {
                'precision_per_class': precisions,
                'recall_per_class': recalls,
                'f1_score_per_class': f1s,
                'macro_precision': np.mean(precisions),
                'macro_recall': np.mean(recalls),
                'macro_f1': np.mean(f1s)
            }
    
    @staticmethod
    def calculate_false_positive_negative_rates(y_true: List[Any], y_pred: List[Any]) -> Dict[str, float]:
        """
        Calcula tasas de falsos positivos y falsos negativos
        
        Args:
            y_true: Valores reales
            y_pred: Predicciones
            
        Returns:
            Dict con tasas de FP y FN
        """
        cm = confusion_matrix(y_true, y_pred)
        
        if cm.shape == (2, 2):
            tn, fp, fn, tp = cm.ravel()
            
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0  # False Positive Rate
            fnr = fn / (fn + tp) if (fn + tp) > 0 else 0  # False Negative Rate
            
            return {
                'false_positive_rate': fpr,
                'false_negative_rate': fnr,
                'false_positives': int(fp),
                'false_negatives': int(fn),
                'true_positives': int(tp),
                'true_negatives': int(tn)
            }
        
        # Para multiclase, calcular promedio
        total_fp = 0
        total_fn = 0
        total_samples = len(y_true)
        
        for i in range(len(cm)):
            fp = cm[:, i].sum() - cm[i, i]
            fn = cm[i, :].sum() - cm[i, i]
            total_fp += fp
            total_fn += fn
        
        return {
            'average_false_positive_rate': total_fp / total_samples,
            'average_false_negative_rate': total_fn / total_samples,
            'total_false_positives': int(total_fp),
            'total_false_negatives': int(total_fn)
        }

class MetricsVisualizer:
    """Clase para crear visualizaciones de métricas"""
    
    @staticmethod
    def plot_confusion_matrix(cm: np.ndarray, labels: List[str], 
                            title: str = "Matriz de Confusión", 
                            save_path: Optional[str] = None) -> str:
        """
        Crea visualización de matriz de confusión
        
        Args:
            cm: Matriz de confusión
            labels: Etiquetas de las clases
            title: Título del gráfico
            save_path: Ruta para guardar (opcional)
            
        Returns:
            Ruta del archivo guardado
        """
        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=labels, yticklabels=labels)
        plt.title(title)
        plt.xlabel('Predicción')
        plt.ylabel('Valor Real')
        
        if save_path is None:
            save_path = f"tests/performance/reports/confusion_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return save_path
    
    @staticmethod
    def plot_metrics_over_time(metrics_history: List[Dict[str, Any]], 
                             metric_names: List[str],
                             title: str = "Métricas a lo Largo del Tiempo",
                             save_path: Optional[str] = None) -> str:
        """
        Crea gráfico de métricas a lo largo del tiempo
        
        Args:
            metrics_history: Lista de diccionarios con métricas históricas
            metric_names: Nombres de las métricas a graficar
            title: Título del gráfico
            save_path: Ruta para guardar (opcional)
            
        Returns:
            Ruta del archivo guardado
        """
        plt.figure(figsize=(12, 8))
        
        for metric in metric_names:
            values = [m.get(metric, 0) for m in metrics_history]
            timestamps = [m.get('timestamp', i) for i, m in enumerate(metrics_history)]
            plt.plot(timestamps, values, label=metric, marker='o')
        
        plt.title(title)
        plt.xlabel('Tiempo')
        plt.ylabel('Valor')
        plt.legend()
        plt.xticks(rotation=45)
        
        if save_path is None:
            save_path = f"tests/performance/reports/metrics_timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return save_path
    
    @staticmethod
    def plot_response_time_distribution(response_times: List[float],
                                      title: str = "Distribución de Tiempos de Respuesta",
                                      save_path: Optional[str] = None) -> str:
        """
        Crea histograma de distribución de tiempos de respuesta
        
        Args:
            response_times: Lista de tiempos de respuesta
            title: Título del gráfico
            save_path: Ruta para guardar (opcional)
            
        Returns:
            Ruta del archivo guardado
        """
        plt.figure(figsize=(10, 6))
        
        # Convertir a milisegundos
        response_times_ms = [t * 1000 for t in response_times]
        
        plt.hist(response_times_ms, bins=30, alpha=0.7, edgecolor='black')
        plt.axvline(np.mean(response_times_ms), color='red', linestyle='--', 
                   label=f'Media: {np.mean(response_times_ms):.2f} ms')
        plt.axvline(np.median(response_times_ms), color='green', linestyle='--',
                   label=f'Mediana: {np.median(response_times_ms):.2f} ms')
        
        plt.title(title)
        plt.xlabel('Tiempo de Respuesta (ms)')
        plt.ylabel('Frecuencia')
        plt.legend()
        
        if save_path is None:
            save_path = f"tests/performance/reports/response_time_dist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return save_path

class ReportGenerator:
    """Generador de reportes de métricas"""
    
    @staticmethod
    def generate_performance_report(metrics_data: Dict[str, Any], 
                                  save_path: Optional[str] = None) -> str:
        """
        Genera reporte completo de rendimiento en formato JSON
        
        Args:
            metrics_data: Datos de métricas
            save_path: Ruta para guardar (opcional)
            
        Returns:
            Ruta del archivo de reporte generado
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': metrics_data.get('total_tests', 0),
                'success_rate': metrics_data.get('success_rate', 0),
                'average_response_time': metrics_data.get('avg_response_time', 0),
                'error_rate': metrics_data.get('error_rate', 0)
            },
            'detailed_metrics': metrics_data,
            'recommendations': ReportGenerator._generate_recommendations(metrics_data)
        }
        
        if save_path is None:
            save_path = f"tests/performance/reports/performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return save_path
    
    @staticmethod
    def _generate_recommendations(metrics_data: Dict[str, Any]) -> List[str]:
        """
        Genera recomendaciones basadas en las métricas
        
        Args:
            metrics_data: Datos de métricas
            
        Returns:
            Lista de recomendaciones
        """
        recommendations = []
        
        # Recomendaciones basadas en tiempo de respuesta
        avg_response_time = metrics_data.get('avg_response_time', 0)
        if avg_response_time > 0.1:  # 100ms
            recommendations.append("El tiempo de respuesta promedio es alto (>100ms). Considere optimizar el código.")
        
        # Recomendaciones basadas en tasa de error
        error_rate = metrics_data.get('error_rate', 0)
        if error_rate > 5:  # 5%
            recommendations.append("La tasa de error es alta (>5%). Revisar manejo de errores y validaciones.")
        
        # Recomendaciones basadas en precisión
        accuracy = metrics_data.get('accuracy', 100)
        if accuracy < 90:
            recommendations.append("La precisión es baja (<90%). Considere mejorar el modelo o ajustar umbrales.")
        
        if not recommendations:
            recommendations.append("Todas las métricas están dentro de rangos aceptables.")
        
        return recommendations 