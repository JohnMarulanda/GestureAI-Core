#!/usr/bin/env python3
"""
Runner específico para tests de tiempo de respuesta de todos los controladores.
Ejecuta tests de latencia, rendimiento y genera reportes detallados.
"""

import sys
import os
import time
import json
import argparse
from datetime import datetime
from typing import Dict, List, Any
import numpy as np

# Agregar paths para imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from tests.performance.metrics.response_time.test_mouse_controller_response_time import TestMouseControllerResponseTime
from tests.performance.metrics.response_time.test_volume_controller_response_time import TestVolumeControllerResponseTime
from tests.performance.metrics.response_time.test_navigation_controller_response_time import TestNavigationControllerResponseTime
from tests.performance.metrics.response_time.test_system_controller_response_time import TestSystemControllerResponseTime
from tests.performance.metrics.response_time.test_shortcuts_controller_response_time import TestShortcutsControllerResponseTime
from tests.performance.metrics.response_time.test_multimedia_controller_response_time import TestMultimediaControllerResponseTime
from tests.performance.metrics.response_time.test_app_controller_response_time import TestAppControllerResponseTime
from tests.performance.utils.metrics_utils import MetricsVisualizer, ReportGenerator
from tests.performance.config.test_config import get_controller_config, ControllerTestConfig

class ResponseTimeTestRunner:
    """Runner para ejecutar todos los tests de tiempo de respuesta"""
    
    def __init__(self):
        self.results = {}
        self.start_time = None
        self.end_time = None
        self.failed_tests = []
        
        # Mapa de tests disponibles
        self.available_tests = {
            'mouse_controller_enhanced': TestMouseControllerResponseTime,
            'volume_controller_enhanced': TestVolumeControllerResponseTime, 
            'navigation_controller_enhanced': TestNavigationControllerResponseTime,
            'system_controller_enhanced': TestSystemControllerResponseTime,
            'shortcuts_controller_enhanced': TestShortcutsControllerResponseTime,
            'multimedia_controller_enhanced': TestMultimediaControllerResponseTime,
            'app_controller_enhanced': TestAppControllerResponseTime
        }
        
    def run_single_controller_test(self, controller_name: str) -> Dict[str, Any]:
        """
        Ejecuta test de tiempo de respuesta para un controlador específico
        
        Args:
            controller_name: Nombre del controlador a testear
            
        Returns:
            Resultados del test
        """
        if controller_name not in self.available_tests:
            raise ValueError(f"Test no disponible para controlador: {controller_name}")
        
        print(f"🎮 Ejecutando test de tiempo de respuesta para {controller_name}...")
        
        test_class = self.available_tests[controller_name]
        test_instance = test_class()
        
        try:
            # Ejecutar test de rendimiento
            results = test_instance.run_performance_test()
            
            # Agregar metadata
            results['test_status'] = 'success'
            results['controller_config'] = get_controller_config(controller_name)
            
            print(f"✅ Test completado para {controller_name}")
            
            return results
            
        except Exception as e:
            error_result = {
                'controller': controller_name,
                'test_status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
            self.failed_tests.append(controller_name)
            print(f"❌ Test falló para {controller_name}: {e}")
            
            return error_result
    
    def run_all_controller_tests(self) -> Dict[str, Any]:
        """
        Ejecuta tests de tiempo de respuesta para todos los controladores disponibles
        
        Returns:
            Resultados consolidados de todos los tests
        """
        print("🚀 Iniciando tests de tiempo de respuesta para todos los controladores...")
        self.start_time = datetime.now()
        
        all_results = {
            'suite_type': 'response_time_full_suite',
            'start_time': self.start_time.isoformat(),
            'controllers': {}
        }
        
        # Ejecutar test para cada controlador
        for controller_name in self.available_tests.keys():
            controller_results = self.run_single_controller_test(controller_name)
            all_results['controllers'][controller_name] = controller_results
            
            # Pequeña pausa entre tests
            time.sleep(0.5)
        
        self.end_time = datetime.now()
        all_results['end_time'] = self.end_time.isoformat()
        all_results['duration'] = (self.end_time - self.start_time).total_seconds()
        
        # Generar estadísticas consolidadas
        all_results['summary'] = self.generate_consolidated_summary(all_results['controllers'])
        
        print(f"✅ Suite completa finalizada en {all_results['duration']:.2f} segundos")
        
        return all_results
    
    def generate_consolidated_summary(self, controller_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera resumen consolidado de todos los resultados
        
        Args:
            controller_results: Resultados de todos los controladores
            
        Returns:
            Resumen consolidado
        """
        summary = {
            'total_controllers': len(controller_results),
            'successful_tests': 0,
            'failed_tests': len(self.failed_tests),
            'failed_controllers': self.failed_tests,
            'performance_metrics': {},
            'overall_status': 'unknown'
        }
        
        # Recopilar métricas de rendimiento
        all_init_times = []
        all_e2e_times = []
        controller_performances = {}
        
        for controller_name, results in controller_results.items():
            if results.get('test_status') == 'success':
                summary['successful_tests'] += 1
                
                # Recopilar tiempos de inicialización
                if 'initialization_time' in results:
                    all_init_times.append(results['initialization_time'])
                
                # Recopilar tiempos end-to-end
                if 'end_to_end_latency' in results:
                    e2e_data = results['end_to_end_latency']
                    if isinstance(e2e_data, list):
                        for item in e2e_data:
                            if 'mean_latency' in item:
                                all_e2e_times.append(item['mean_latency'])
                    elif isinstance(e2e_data, dict) and 'mean' in e2e_data:
                        all_e2e_times.append(e2e_data['mean'])
                
                # Evaluación de rendimiento por controlador
                config = get_controller_config(controller_name)
                expected_time = config.get('expected_response_time', 0.1)
                
                if 'summary' in results and 'target_achieved' in results['summary']:
                    meets_target = results['summary']['target_achieved']
                else:
                    # Evaluar basado en tiempos end-to-end si están disponibles
                    meets_target = True
                    if all_e2e_times:
                        avg_e2e = np.mean(all_e2e_times)
                        meets_target = avg_e2e <= expected_time
                
                controller_performances[controller_name] = {
                    'meets_target': meets_target,
                    'expected_time': expected_time,
                    'status': 'pass' if meets_target else 'warning'
                }
        
        # Calcular métricas generales
        if all_init_times:
            summary['performance_metrics']['initialization'] = {
                'mean': np.mean(all_init_times),
                'median': np.median(all_init_times),
                'max': np.max(all_init_times),
                'min': np.min(all_init_times)
            }
        
        if all_e2e_times:
            summary['performance_metrics']['end_to_end'] = {
                'mean': np.mean(all_e2e_times),
                'median': np.median(all_e2e_times),
                'p95': np.percentile(all_e2e_times, 95),
                'max': np.max(all_e2e_times),
                'min': np.min(all_e2e_times)
            }
        
        # Determinar estado general
        success_rate = summary['successful_tests'] / summary['total_controllers']
        performance_rate = sum(1 for p in controller_performances.values() if p['meets_target']) / len(controller_performances) if controller_performances else 0
        
        if success_rate == 1.0 and performance_rate >= 0.8:
            summary['overall_status'] = 'excellent'
        elif success_rate >= 0.8 and performance_rate >= 0.6:
            summary['overall_status'] = 'good'
        elif success_rate >= 0.6:
            summary['overall_status'] = 'acceptable'
        else:
            summary['overall_status'] = 'needs_improvement'
        
        summary['controller_performances'] = controller_performances
        summary['success_rate'] = success_rate
        summary['performance_rate'] = performance_rate
        
        return summary
    
    def generate_detailed_report(self, results: Dict[str, Any], output_dir: str = "tests/performance/reports") -> str:
        """
        Genera reporte detallado de los resultados
        
        Args:
            results: Resultados de los tests
            output_dir: Directorio de salida
            
        Returns:
            Ruta del archivo de reporte
        """
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Reporte JSON principal
        report_path = os.path.join(output_dir, f"response_time_report_{timestamp}.json")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        # Generar reporte HTML si es posible
        try:
            html_report_path = self.generate_html_report(results, output_dir, timestamp)
            print(f"📄 Reporte HTML generado: {html_report_path}")
        except Exception as e:
            print(f"⚠️ No se pudo generar reporte HTML: {e}")
        
        # Generar gráficos si es posible
        try:
            self.generate_performance_charts(results, output_dir, timestamp)
            print(f"📊 Gráficos de rendimiento generados en: {output_dir}")
        except Exception as e:
            print(f"⚠️ No se pudieron generar gráficos: {e}")
        
        print(f"📋 Reporte principal guardado en: {report_path}")
        return report_path
    
    def generate_html_report(self, results: Dict[str, Any], output_dir: str, timestamp: str) -> str:
        """Genera reporte HTML básico"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Response Time Test Report - {timestamp}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f0f0f0; padding: 15px; border-radius: 5px; }}
        .controller {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; }}
        .success {{ border-left: 5px solid #4CAF50; }}
        .warning {{ border-left: 5px solid #FF9800; }}
        .error {{ border-left: 5px solid #F44336; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>Response Time Test Report</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Overall Status:</strong> {results.get('summary', {}).get('overall_status', 'unknown')}</p>
        <p><strong>Total Controllers:</strong> {results.get('summary', {}).get('total_controllers', 0)}</p>
        <p><strong>Successful Tests:</strong> {results.get('summary', {}).get('successful_tests', 0)}</p>
        <p><strong>Failed Tests:</strong> {results.get('summary', {}).get('failed_tests', 0)}</p>
        <p><strong>Duration:</strong> {results.get('duration', 0):.2f} seconds</p>
    </div>
    
    <h2>Controller Results</h2>
"""
        
        for controller_name, controller_results in results.get('controllers', {}).items():
            status_class = 'success' if controller_results.get('test_status') == 'success' else 'error'
            
            html_content += f"""
    <div class="controller {status_class}">
        <h3>{controller_name}</h3>
        <p><strong>Status:</strong> {controller_results.get('test_status', 'unknown')}</p>
"""
            
            if 'initialization_time' in controller_results:
                html_content += f"<p><strong>Initialization Time:</strong> {controller_results['initialization_time']*1000:.2f} ms</p>"
            
            if 'summary' in controller_results:
                summary = controller_results['summary']
                html_content += f"""
        <p><strong>Total Tests:</strong> {summary.get('total_tests', 0)}</p>
        <p><strong>Target Achieved:</strong> {summary.get('target_achieved', 'N/A')}</p>
"""
            
            html_content += "</div>"
        
        html_content += """
</body>
</html>
"""
        
        html_path = os.path.join(output_dir, f"response_time_report_{timestamp}.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_path
    
    def generate_performance_charts(self, results: Dict[str, Any], output_dir: str, timestamp: str):
        """Genera gráficos de rendimiento"""
        try:
            import matplotlib.pyplot as plt
            
            # Gráfico de tiempos de inicialización
            controllers = []
            init_times = []
            
            for controller_name, controller_results in results.get('controllers', {}).items():
                if 'initialization_time' in controller_results:
                    controllers.append(controller_name.replace('_enhanced', ''))
                    init_times.append(controller_results['initialization_time'] * 1000)  # Convertir a ms
            
            if controllers:
                plt.figure(figsize=(12, 6))
                bars = plt.bar(controllers, init_times, color=['#4CAF50' if t < 50 else '#FF9800' for t in init_times])
                plt.title('Initialization Times by Controller')
                plt.ylabel('Time (ms)')
                plt.xlabel('Controller')
                plt.xticks(rotation=45)
                
                # Añadir línea de threshold
                plt.axhline(y=50, color='red', linestyle='--', label='Target (50ms)')
                plt.legend()
                
                # Añadir valores en las barras
                for bar, time in zip(bars, init_times):
                    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                           f'{time:.1f}ms', ha='center', va='bottom')
                
                plt.tight_layout()
                plt.savefig(os.path.join(output_dir, f"initialization_times_{timestamp}.png"), dpi=300)
                plt.close()
            
        except ImportError:
            print("⚠️ matplotlib no disponible, saltando generación de gráficos")

def main():
    """Función principal del runner"""
    parser = argparse.ArgumentParser(description='Response Time Test Runner')
    
    parser.add_argument('--controller', type=str, 
                       choices=['mouse_controller_enhanced', 'volume_controller_enhanced', 
                               'navigation_controller_enhanced'],
                       help='Ejecutar test para controlador específico')
    
    parser.add_argument('--output-dir', type=str, default='tests/performance/reports',
                       help='Directorio de salida para reportes')
    
    parser.add_argument('--generate-charts', action='store_true',
                       help='Generar gráficos de rendimiento')
    
    args = parser.parse_args()
    
    # Crear directorio de salida
    os.makedirs(args.output_dir, exist_ok=True)
    
    runner = ResponseTimeTestRunner()
    
    print("⏱️ Response Time Test Runner - GestureAI-Core")
    print("=" * 50)
    
    try:
        if args.controller:
            # Ejecutar test para controlador específico
            print(f"🎯 Ejecutando test para: {args.controller}")
            results = {
                'suite_type': 'single_controller_response_time',
                'timestamp': datetime.now().isoformat(),
                'controllers': {
                    args.controller: runner.run_single_controller_test(args.controller)
                }
            }
            results['summary'] = runner.generate_consolidated_summary(results['controllers'])
        else:
            # Ejecutar suite completa
            print("🚀 Ejecutando suite completa de response time...")
            results = runner.run_all_controller_tests()
        
        # Generar reporte
        report_path = runner.generate_detailed_report(results, args.output_dir)
        
        # Mostrar resumen en consola
        print("\n📊 RESUMEN DE RESULTADOS:")
        print("-" * 30)
        summary = results.get('summary', {})
        print(f"Estado General: {summary.get('overall_status', 'unknown')}")
        print(f"Tests Exitosos: {summary.get('successful_tests', 0)}/{summary.get('total_controllers', 0)}")
        
        if summary.get('performance_metrics', {}).get('end_to_end'):
            e2e = summary['performance_metrics']['end_to_end']
            print(f"Latencia E2E Promedio: {e2e.get('mean', 0)*1000:.2f}ms")
            print(f"Latencia E2E P95: {e2e.get('p95', 0)*1000:.2f}ms")
        
        if summary.get('failed_controllers'):
            print(f"❌ Controladores fallidos: {', '.join(summary['failed_controllers'])}")
        
        print(f"\n📋 Reporte completo: {report_path}")
        
    except Exception as e:
        print(f"❌ Error durante la ejecución: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main()) 