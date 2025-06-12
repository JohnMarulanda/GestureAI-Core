#!/usr/bin/env python3
"""
Runner principal para tests de precisión (accuracy) de detección de gestos.
Ejecuta tests de accuracy para todos los controladores y genera reportes detallados.
"""

import sys
import os
import time
import unittest
import importlib
from datetime import datetime
from typing import Dict, List, Any
import json

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

# Importar tests de accuracy
from tests.performance.metrics.accuracy.test_mouse_controller_accuracy import TestMouseControllerAccuracy
from tests.performance.metrics.accuracy.test_volume_controller_accuracy import TestVolumeControllerAccuracy
from tests.performance.metrics.accuracy.test_navigation_controller_accuracy import TestNavigationControllerAccuracy
from tests.performance.metrics.accuracy.test_system_controller_accuracy import TestSystemControllerAccuracy
from tests.performance.metrics.accuracy.test_shortcuts_controller_accuracy import TestShortcutsControllerAccuracy
from tests.performance.metrics.accuracy.test_multimedia_controller_accuracy import TestMultimediaControllerAccuracy
from tests.performance.metrics.accuracy.test_app_controller_accuracy import TestAppControllerAccuracy

class AccuracyTestRunner:
    """Runner para tests de precisión de gestos"""
    
    def __init__(self):
        self.results = {}
        self.test_start_time = None
        self.test_end_time = None
        
        # Mapeo de tests disponibles
        self.available_tests = {
            'mouse': TestMouseControllerAccuracy,
            'volume': TestVolumeControllerAccuracy,
            'navigation': TestNavigationControllerAccuracy,
            'system': TestSystemControllerAccuracy,
            'shortcuts': TestShortcutsControllerAccuracy,
            'multimedia': TestMultimediaControllerAccuracy,
            'app': TestAppControllerAccuracy
        }
        
        # Objetivos de precisión por controlador
        self.accuracy_targets = {
            'mouse': 0.94,        # 94% - Muy alto para interacción crítica
            'volume': 0.92,       # 92% - Alto para controles de audio
            'navigation': 0.91,   # 91% - Alto para navegación frecuente
            'shortcuts': 0.93,    # 93% - Muy alto para atajos críticos
            'multimedia': 0.89,   # 89% - Bueno para controles multimedia
            'system': 0.88,       # 88% - Conservador para operaciones críticas
            'app': 0.86          # 86% - Moderado para gestión de apps
        }
    
    def run_controller_tests(self, controller_name: str) -> Dict[str, Any]:
        """
        Ejecuta tests de accuracy para un controlador específico
        
        Args:
            controller_name: Nombre del controlador a testear
            
        Returns:
            Dict con resultados del test
        """
        if controller_name not in self.available_tests:
            raise ValueError(f"Controlador {controller_name} no disponible")
        
        print(f"\n{'='*60}")
        print(f"🎯 TESTING ACCURACY: {controller_name.upper()} CONTROLLER")
        print(f"{'='*60}")
        
        test_class = self.available_tests[controller_name]
        target_accuracy = self.accuracy_targets[controller_name]
        
        # Crear suite de tests
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        
        # Capturar resultados
        stream = TestResultCapture()
        runner = unittest.TextTestRunner(stream=stream, verbosity=2)
        
        start_time = time.time()
        result = runner.run(suite)
        end_time = time.time()
        
        # Procesar resultados
        controller_results = {
            'controller': controller_name,
            'target_accuracy': target_accuracy,
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success_rate': (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun if result.testsRun > 0 else 0,
            'execution_time': end_time - start_time,
            'timestamp': datetime.now().isoformat(),
            'test_details': {
                'failures': [str(f[0]) + ": " + str(f[1]) for f in result.failures],
                'errors': [str(e[0]) + ": " + str(e[1]) for e in result.errors]
            }
        }
        
        # Determinar estado del test
        if controller_results['success_rate'] >= 0.95:
            status = "✅ EXCELENTE"
        elif controller_results['success_rate'] >= 0.85:
            status = "✅ BUENO"
        elif controller_results['success_rate'] >= 0.70:
            status = "⚠️ ACEPTABLE"
        else:
            status = "❌ NECESITA MEJORAS"
        
        controller_results['status'] = status
        
        # Mostrar resumen
        print(f"\n📊 RESUMEN {controller_name.upper()}:")
        print(f"   🎯 Objetivo de precisión: {target_accuracy:.1%}")
        print(f"   ✅ Tests ejecutados: {controller_results['tests_run']}")
        print(f"   📈 Tasa de éxito: {controller_results['success_rate']:.1%}")
        print(f"   ⏱️ Tiempo ejecución: {controller_results['execution_time']:.2f}s")
        print(f"   🏆 Estado: {status}")
        
        if controller_results['failures'] > 0:
            print(f"   ⚠️ Fallos: {controller_results['failures']}")
        
        if controller_results['errors'] > 0:
            print(f"   ❌ Errores: {controller_results['errors']}")
        
        return controller_results
    
    def run_all_tests(self, controllers: List[str] = None) -> Dict[str, Any]:
        """
        Ejecuta tests de accuracy para todos los controladores especificados
        
        Args:
            controllers: Lista de controladores a testear (None = todos)
            
        Returns:
            Dict con resultados completos
        """
        if controllers is None:
            controllers = list(self.available_tests.keys())
        
        print("\n🎯 INICIANDO SUITE COMPLETA DE TESTS DE PRECISIÓN")
        print("=" * 80)
        
        self.test_start_time = time.time()
        all_results = {}
        
        # Ejecutar tests por controlador
        for controller in controllers:
            try:
                controller_results = self.run_controller_tests(controller)
                all_results[controller] = controller_results
                
                # Pausa entre controladores
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error ejecutando tests para {controller}: {e}")
                all_results[controller] = {
                    'controller': controller,
                    'error': str(e),
                    'status': '❌ ERROR'
                }
        
        self.test_end_time = time.time()
        
        # Generar reporte final
        self.generate_final_report(all_results)
        
        return all_results
    
    def generate_final_report(self, results: Dict[str, Any]):
        """
        Genera reporte final de todos los tests de accuracy
        
        Args:
            results: Resultados de todos los controladores
        """
        total_time = self.test_end_time - self.test_start_time
        
        print(f"\n{'='*80}")
        print("📊 REPORTE FINAL DE PRECISIÓN DE GESTOS")
        print(f"{'='*80}")
        
        print(f"\n⏱️ Tiempo total de ejecución: {total_time:.2f}s")
        print(f"📅 Ejecutado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Estadísticas globales
        total_tests = sum(r.get('tests_run', 0) for r in results.values() if 'tests_run' in r)
        total_failures = sum(r.get('failures', 0) for r in results.values() if 'failures' in r)
        total_errors = sum(r.get('errors', 0) for r in results.values() if 'errors' in r)
        overall_success = (total_tests - total_failures - total_errors) / total_tests if total_tests > 0 else 0
        
        print(f"\n📈 ESTADÍSTICAS GLOBALES:")
        print(f"   🎯 Tests totales ejecutados: {total_tests}")
        print(f"   ✅ Tasa de éxito global: {overall_success:.1%}")
        print(f"   ⚠️ Fallos totales: {total_failures}")
        print(f"   ❌ Errores totales: {total_errors}")
        
        # Ranking de controladores por precisión
        print(f"\n🏆 RANKING DE PRECISIÓN POR CONTROLADOR:")
        
        valid_results = [(name, data) for name, data in results.items() if 'success_rate' in data]
        valid_results.sort(key=lambda x: x[1]['success_rate'], reverse=True)
        
        for i, (controller, data) in enumerate(valid_results, 1):
            target = self.accuracy_targets.get(controller, 0.85)
            actual = data['success_rate']
            target_met = "✅" if actual >= target * 0.90 else "⚠️"  # 90% del objetivo como umbral
            
            print(f"   {i}. {controller.upper():12} - {actual:.1%} (objetivo: {target:.1%}) {target_met}")
        
        # Controladores que necesitan atención
        needs_attention = [
            (name, data) for name, data in valid_results 
            if data['success_rate'] < self.accuracy_targets.get(name, 0.85) * 0.90
        ]
        
        if needs_attention:
            print(f"\n⚠️ CONTROLADORES QUE NECESITAN ATENCIÓN:")
            for controller, data in needs_attention:
                target = self.accuracy_targets.get(controller, 0.85)
                gap = target - data['success_rate']
                print(f"   • {controller.upper()}: {data['success_rate']:.1%} (brecha: -{gap:.1%})")
        
        # Recomendaciones
        print(f"\n💡 RECOMENDACIONES:")
        
        if overall_success >= 0.90:
            print("   ✅ Excelente precisión global. Sistema listo para producción.")
        elif overall_success >= 0.80:
            print("   ✅ Buena precisión global. Considerar mejoras menores.")
        elif overall_success >= 0.70:
            print("   ⚠️ Precisión aceptable. Revisar controladores con bajo rendimiento.")
        else:
            print("   ❌ Precisión insuficiente. Requiere mejoras significativas.")
        
        if total_failures > 0:
            print(f"   🔧 Revisar {total_failures} tests que fallaron")
        
        if total_errors > 0:
            print(f"   🐛 Corregir {total_errors} errores encontrados")
        
        # Generar archivo de resultados
        self.save_results_to_file(results)
        
        print(f"\n💾 Resultados guardados en: accuracy_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        print("=" * 80)
    
    def save_results_to_file(self, results: Dict[str, Any]):
        """
        Guarda los resultados en un archivo JSON
        
        Args:
            results: Resultados a guardar
        """
        try:
            # Preparar datos para JSON
            json_data = {
                'test_type': 'accuracy',
                'execution_date': datetime.now().isoformat(),
                'total_execution_time': self.test_end_time - self.test_start_time if self.test_start_time else 0,
                'controllers_tested': len(results),
                'accuracy_targets': self.accuracy_targets,
                'results': results
            }
            
            # Guardar archivo
            filename = f"accuracy_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(os.path.dirname(__file__), 'reports', filename)
            
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ Error guardando resultados: {e}")


class TestResultCapture:
    """Captura de resultados de tests para procesamiento"""
    
    def __init__(self):
        self.output = []
    
    def write(self, text):
        self.output.append(text)
        # También mostrar en consola
        print(text, end='')
    
    def flush(self):
        pass


def main():
    """Función principal"""
    runner = AccuracyTestRunner()
    
    # Argumentos de línea de comandos simples
    if len(sys.argv) > 1:
        # Controladores específicos
        controllers = sys.argv[1].split(',')
        print(f"🎯 Ejecutando tests de accuracy para: {', '.join(controllers)}")
        runner.run_all_tests(controllers)
    else:
        # Todos los controladores
        print("🎯 Ejecutando tests de accuracy para todos los controladores")
        runner.run_all_tests()


if __name__ == '__main__':
    main() 