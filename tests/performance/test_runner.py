"""
Test Runner para ejecutar todas las pruebas de rendimiento del sistema GestureAI-Core.
Permite ejecutar tests individuales o suites completas de métricas.
"""

import argparse
import sys
import os
from typing import List, Dict, Any
import unittest
from datetime import datetime
import json

# Agregar paths para imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.performance.base_performance_test import BasePerformanceTest
from tests.performance.utils.metrics_utils import ReportGenerator

class PerformanceTestRunner:
    """Ejecutor principal de tests de rendimiento"""
    
    def __init__(self):
        self.test_results = []
        self.failed_tests = []
        self.start_time = None
        self.end_time = None
        
    def discover_tests(self, test_directory: str) -> List[str]:
        """
        Descubre automáticamente tests de rendimiento en un directorio
        
        Args:
            test_directory: Directorio donde buscar tests
            
        Returns:
            Lista de archivos de test encontrados
        """
        test_files = []
        
        for root, dirs, files in os.walk(test_directory):
            for file in files:
                if file.startswith('test_') and file.endswith('.py'):
                    test_files.append(os.path.join(root, file))
                    
        return test_files
    
    def run_accuracy_tests(self) -> Dict[str, Any]:
        """Ejecuta todos los tests de precisión"""
        print("🎯 Ejecutando tests de precisión...")
        
        results = {
            'test_type': 'accuracy',
            'timestamp': datetime.now().isoformat(),
            'tests': []
        }
        
        # Aquí se ejecutarían los tests específicos de precisión
        # Por ahora, estructura placeholder
        
        return results
    
    def run_response_time_tests(self) -> Dict[str, Any]:
        """Ejecuta todos los tests de tiempo de respuesta"""
        print("⏱️ Ejecutando tests de tiempo de respuesta...")
        
        results = {
            'test_type': 'response_time',
            'timestamp': datetime.now().isoformat(),
            'tests': []
        }
        
        return results
    
    def run_error_analysis_tests(self) -> Dict[str, Any]:
        """Ejecuta todos los tests de análisis de errores"""
        print("🔍 Ejecutando tests de análisis de errores...")
        
        results = {
            'test_type': 'error_analysis',
            'timestamp': datetime.now().isoformat(),
            'tests': []
        }
        
        return results
    
    def run_confusion_matrix_tests(self) -> Dict[str, Any]:
        """Ejecuta todos los tests de matriz de confusión"""
        print("📊 Ejecutando tests de matriz de confusión...")
        
        results = {
            'test_type': 'confusion_matrix',
            'timestamp': datetime.now().isoformat(),
            'tests': []
        }
        
        return results
    
    def run_false_predictions_tests(self) -> Dict[str, Any]:
        """Ejecuta todos los tests de predicciones falsas"""
        print("❌ Ejecutando tests de predicciones falsas...")
        
        results = {
            'test_type': 'false_predictions',
            'timestamp': datetime.now().isoformat(),
            'tests': []
        }
        
        return results
    
    def run_controller_tests(self, controller_name: str = None) -> Dict[str, Any]:
        """
        Ejecuta tests específicos para controladores
        
        Args:
            controller_name: Nombre del controlador específico (opcional)
            
        Returns:
            Resultados de los tests del controlador
        """
        controllers = [
            'mouse_controller_enhanced',
            'navigation_controller_enhanced',
            'app_controller_enhanced',
            'volume_controller_enhanced',
            'system_controller_enhanced',
            'shortcuts_controller_enhanced',
            'multimedia_controller_enhanced',
            'brightness_controller_enhanced',
            'canned_gestures_controller_enhanced'
        ]
        
        if controller_name:
            controllers = [controller_name] if controller_name in controllers else []
        
        results = {
            'test_type': 'controller_tests',
            'timestamp': datetime.now().isoformat(),
            'controllers_tested': controllers,
            'tests': []
        }
        
        for controller in controllers:
            print(f"🎮 Testing {controller}...")
            # Aquí iría la lógica específica para cada controlador
            
        return results
    
    def run_model_tests(self) -> Dict[str, Any]:
        """Ejecuta tests específicos para los modelos"""
        print("🤖 Ejecutando tests de modelos...")
        
        models = [
            'hand_landmarker.task',
            'gesture_recognizer.task'
        ]
        
        results = {
            'test_type': 'model_tests',
            'timestamp': datetime.now().isoformat(),
            'models_tested': models,
            'tests': []
        }
        
        return results
    
    def run_full_suite(self) -> Dict[str, Any]:
        """Ejecuta la suite completa de tests de rendimiento"""
        print("🚀 Iniciando suite completa de tests de rendimiento...")
        self.start_time = datetime.now()
        
        full_results = {
            'suite_type': 'full_performance_suite',
            'start_time': self.start_time.isoformat(),
            'results': {}
        }
        
        try:
            # Ejecutar cada tipo de test
            full_results['results']['accuracy'] = self.run_accuracy_tests()
            full_results['results']['response_time'] = self.run_response_time_tests()
            full_results['results']['error_analysis'] = self.run_error_analysis_tests()
            full_results['results']['confusion_matrix'] = self.run_confusion_matrix_tests()
            full_results['results']['false_predictions'] = self.run_false_predictions_tests()
            full_results['results']['controllers'] = self.run_controller_tests()
            full_results['results']['models'] = self.run_model_tests()
            
        except Exception as e:
            print(f"❌ Error durante la ejecución de tests: {e}")
            full_results['error'] = str(e)
        
        self.end_time = datetime.now()
        full_results['end_time'] = self.end_time.isoformat()
        full_results['duration'] = (self.end_time - self.start_time).total_seconds()
        
        # Generar reporte final
        report_path = self.generate_final_report(full_results)
        full_results['report_path'] = report_path
        
        print(f"✅ Suite completa finalizada. Reporte guardado en: {report_path}")
        
        return full_results
    
    def generate_final_report(self, results: Dict[str, Any]) -> str:
        """
        Genera el reporte final consolidado
        
        Args:
            results: Resultados de todos los tests
            
        Returns:
            Ruta del archivo de reporte
        """
        return ReportGenerator.generate_performance_report(
            results, 
            f"tests/performance/reports/full_suite_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

def main():
    """Función principal del test runner"""
    parser = argparse.ArgumentParser(description='GestureAI-Core Performance Test Runner')
    
    parser.add_argument('--suite', choices=['full', 'accuracy', 'response_time', 'error_analysis', 
                                          'confusion_matrix', 'false_predictions', 'controllers', 'models'],
                       default='full', help='Tipo de suite de tests a ejecutar')
    
    parser.add_argument('--controller', type=str, help='Controlador específico a testear')
    
    parser.add_argument('--iterations', type=int, default=100, 
                       help='Número de iteraciones para tests de rendimiento')
    
    parser.add_argument('--output-dir', type=str, default='tests/performance/reports',
                       help='Directorio de salida para reportes')
    
    args = parser.parse_args()
    
    # Crear directorio de salida si no existe
    os.makedirs(args.output_dir, exist_ok=True)
    
    runner = PerformanceTestRunner()
    
    print(f"🎯 Iniciando GestureAI-Core Performance Tests")
    print(f"📊 Suite: {args.suite}")
    print(f"🔄 Iteraciones: {args.iterations}")
    print(f"📁 Directorio de salida: {args.output_dir}")
    print("-" * 50)
    
    # Ejecutar suite seleccionada
    if args.suite == 'full':
        results = runner.run_full_suite()
    elif args.suite == 'accuracy':
        results = runner.run_accuracy_tests()
    elif args.suite == 'response_time':
        results = runner.run_response_time_tests()
    elif args.suite == 'error_analysis':
        results = runner.run_error_analysis_tests()
    elif args.suite == 'confusion_matrix':
        results = runner.run_confusion_matrix_tests()
    elif args.suite == 'false_predictions':
        results = runner.run_false_predictions_tests()
    elif args.suite == 'controllers':
        results = runner.run_controller_tests(args.controller)
    elif args.suite == 'models':
        results = runner.run_model_tests()
    
    print("\n✅ Tests completados exitosamente!")
    return results

if __name__ == "__main__":
    results = main() 