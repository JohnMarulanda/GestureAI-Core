"""
Clase base para todas las pruebas de rendimiento.
Proporciona métodos comunes y estructura estándar para los tests.
"""

import time
import logging
import json
import numpy as np
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import unittest

@dataclass
class PerformanceMetrics:
    """Estructura para almacenar métricas de rendimiento"""
    test_name: str
    timestamp: datetime
    accuracy: Optional[float] = None
    response_time: Optional[float] = None
    error_rate: Optional[float] = None
    throughput: Optional[float] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    
class BasePerformanceTest(unittest.TestCase, ABC):
    """
    Clase base para todas las pruebas de rendimiento del sistema GestureAI-Core.
    
    Proporciona:
    - Medición de tiempo estándar
    - Recopilación de métricas
    - Generación de reportes
    - Logging estructurado
    """
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.start_time = None
        self.end_time = None
        self.metrics = PerformanceMetrics(
            test_name=self._testMethodName,
            timestamp=datetime.now()
        )
        self.results = []
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(f"PerformanceTest.{self.__class__.__name__}")
        
    def tearDown(self):
        """Limpieza y guardado de métricas después de cada test"""
        self.save_metrics()
        
    def start_timer(self) -> None:
        """Inicia el cronómetro para medir tiempo de respuesta"""
        self.start_time = time.perf_counter()
        
    def stop_timer(self) -> float:
        """
        Detiene el cronómetro y retorna el tiempo transcurrido
        
        Returns:
            float: Tiempo transcurrido en segundos
        """
        if self.start_time is None:
            raise ValueError("Timer not started. Call start_timer() first.")
            
        self.end_time = time.perf_counter()
        elapsed_time = self.end_time - self.start_time
        self.metrics.response_time = elapsed_time
        return elapsed_time
        
    def calculate_accuracy(self, predictions: List[Any], ground_truth: List[Any]) -> float:
        """
        Calcula la precisión comparando predicciones con valores reales
        
        Args:
            predictions: Lista de predicciones
            ground_truth: Lista de valores reales
            
        Returns:
            float: Precisión como porcentaje (0-100)
        """
        if len(predictions) != len(ground_truth):
            raise ValueError("Predictions and ground truth must have same length")
            
        if len(predictions) == 0:
            return 0.0
            
        correct = sum(1 for p, gt in zip(predictions, ground_truth) if p == gt)
        accuracy = (correct / len(predictions)) * 100
        self.metrics.accuracy = accuracy
        return accuracy
        
    def calculate_error_rate(self, total_attempts: int, errors: int) -> float:
        """
        Calcula la tasa de error
        
        Args:
            total_attempts: Número total de intentos
            errors: Número de errores
            
        Returns:
            float: Tasa de error como porcentaje (0-100)
        """
        if total_attempts == 0:
            return 0.0
            
        error_rate = (errors / total_attempts) * 100
        self.metrics.error_rate = error_rate
        return error_rate
        
    def log_metric(self, metric_name: str, value: Any, unit: str = "") -> None:
        """
        Registra una métrica en el log
        
        Args:
            metric_name: Nombre de la métrica
            value: Valor de la métrica
            unit: Unidad de medida (opcional)
        """
        unit_str = f" {unit}" if unit else ""
        self.logger.info(f"{metric_name}: {value}{unit_str}")
        
    def add_result(self, result: Dict[str, Any]) -> None:
        """
        Añade un resultado a la lista de resultados del test
        
        Args:
            result: Diccionario con los datos del resultado
        """
        result['timestamp'] = datetime.now().isoformat()
        self.results.append(result)
        
    def save_metrics(self) -> None:
        """Guarda las métricas en archivo JSON"""
        try:
            metrics_dict = {
                'test_name': self.metrics.test_name,
                'timestamp': self.metrics.timestamp.isoformat(),
                'accuracy': self.metrics.accuracy,
                'response_time': self.metrics.response_time,
                'error_rate': self.metrics.error_rate,
                'throughput': self.metrics.throughput,
                'memory_usage': self.metrics.memory_usage,
                'cpu_usage': self.metrics.cpu_usage,
                'results': self.results
            }
            
            filename = f"tests/performance/reports/{self.metrics.test_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(filename, 'w') as f:
                json.dump(metrics_dict, f, indent=2)
                
            self.logger.info(f"Metrics saved to {filename}")
            
        except Exception as e:
            self.logger.error(f"Failed to save metrics: {e}")
            
    @abstractmethod
    def run_performance_test(self) -> Dict[str, Any]:
        """
        Método abstracto que debe implementar cada test de rendimiento específico
        
        Returns:
            Dict[str, Any]: Diccionario con los resultados del test
        """
        pass
        
    def run_multiple_iterations(self, iterations: int = 100) -> List[Dict[str, Any]]:
        """
        Ejecuta el test múltiples veces para obtener estadísticas
        
        Args:
            iterations: Número de iteraciones a ejecutar
            
        Returns:
            List[Dict[str, Any]]: Lista con resultados de todas las iteraciones
        """
        results = []
        
        self.logger.info(f"Starting {iterations} iterations of {self.metrics.test_name}")
        
        for i in range(iterations):
            try:
                result = self.run_performance_test()
                result['iteration'] = i + 1
                results.append(result)
                
                if (i + 1) % 10 == 0:
                    self.logger.info(f"Completed {i + 1}/{iterations} iterations")
                    
            except Exception as e:
                self.logger.error(f"Error in iteration {i + 1}: {e}")
                results.append({
                    'iteration': i + 1,
                    'error': str(e),
                    'success': False
                })
                
        self.analyze_iteration_results(results)
        return results
        
    def analyze_iteration_results(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Analiza los resultados de múltiples iteraciones
        
        Args:
            results: Lista de resultados de iteraciones
            
        Returns:
            Dict[str, float]: Estadísticas de los resultados
        """
        successful_results = [r for r in results if r.get('success', True)]
        
        if not successful_results:
            self.logger.warning("No successful results to analyze")
            return {}
            
        # Extraer tiempos de respuesta
        response_times = [r.get('response_time', 0) for r in successful_results if 'response_time' in r]
        
        if response_times:
            stats = {
                'mean_response_time': np.mean(response_times),
                'median_response_time': np.median(response_times),
                'std_response_time': np.std(response_times),
                'min_response_time': np.min(response_times),
                'max_response_time': np.max(response_times),
                'success_rate': len(successful_results) / len(results) * 100
            }
            
            # Log estadísticas
            for metric, value in stats.items():
                unit = "ms" if "time" in metric else "%" if "rate" in metric else ""
                if "time" in metric:
                    value = value * 1000  # Convertir a milisegundos
                self.log_metric(metric, round(value, 2), unit)
                
            return stats
            
        return {'success_rate': len(successful_results) / len(results) * 100} 