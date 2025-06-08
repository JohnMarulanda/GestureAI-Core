#!/usr/bin/env python3
"""
Runner rápido para tests de precisión (accuracy) de detección de gestos.
Ejecuta un subconjunto optimizado de tests para validación rápida.
"""

import sys
import os
import time
import unittest
from datetime import datetime
from typing import Dict, List, Any

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

class QuickAccuracyTestRunner:
    """Runner rápido para tests de precisión"""
    
    def __init__(self):
        # Tests priorizados por importancia y velocidad
        self.priority_controllers = [
            'mouse',        # Crítico para interacción
            'shortcuts',    # Crítico para productividad
            'volume',       # Usado frecuentemente
            'navigation',   # Usado frecuentemente
            'multimedia',   # Moderadamente usado
            'system',       # Crítico pero menos frecuente
            'app'          # Menos crítico
        ]
        
        # Mapeo de tests disponibles
        self.test_classes = {
            'mouse': TestMouseControllerAccuracy,
            'volume': TestVolumeControllerAccuracy,
            'navigation': TestNavigationControllerAccuracy,
            'system': TestSystemControllerAccuracy,
            'shortcuts': TestShortcutsControllerAccuracy,
            'multimedia': TestMultimediaControllerAccuracy,
            'app': TestAppControllerAccuracy
        }
        
        # Objetivos de precisión mínima para test rápido
        self.min_accuracy_thresholds = {
            'mouse': 0.90,        # 90% mínimo para mouse
            'shortcuts': 0.88,    # 88% mínimo para atajos
            'volume': 0.85,       # 85% mínimo para volumen
            'navigation': 0.83,   # 83% mínimo para navegación
            'multimedia': 0.80,   # 80% mínimo para multimedia
            'system': 0.75,       # 75% mínimo para sistema (más conservador)
            'app': 0.72           # 72% mínimo para apps
        }
        
        # Tests específicos a ejecutar por controlador (subset rápido)
        self.quick_test_methods = {
            'mouse': ['test_basic_mouse_controls_accuracy', 'test_click_precision_accuracy'],
            'shortcuts': ['test_essential_shortcuts_accuracy', 'test_copy_paste_cut_discrimination'],
            'volume': ['test_basic_volume_controls_accuracy', 'test_volume_direction_discrimination'],
            'navigation': ['test_basic_navigation_accuracy', 'test_back_forward_discrimination'],
            'multimedia': ['test_basic_playback_controls_accuracy', 'test_play_pause_stop_discrimination'],
            'system': ['test_critical_operations_accuracy', 'test_shutdown_restart_discrimination'],
            'app': ['test_app_opening_accuracy', 'test_window_management_accuracy']
        }
    
    def run_quick_test(self, controller: str) -> Dict[str, Any]:
        """
        Ejecuta test rápido para un controlador específico
        
        Args:
            controller: Nombre del controlador
            
        Returns:
            Dict con resultados del test rápido
        """
        if controller not in self.test_classes:
            raise ValueError(f"Controlador {controller} no disponible")
        
        print(f"\n⚡ QUICK TEST: {controller.upper()}")
        print(f"{'─' * 40}")
        
        test_class = self.test_classes[controller]
        test_methods = self.quick_test_methods.get(controller, [])
        min_threshold = self.min_accuracy_thresholds[controller]
        
        # Crear instancia de la clase de test
        test_instance = test_class()
        test_instance.setUp()
        
        results = {
            'controller': controller,
            'min_threshold': min_threshold,
            'tests_executed': [],
            'success_count': 0,
            'total_tests': len(test_methods),
            'execution_time': 0,
            'overall_status': 'PENDING'
        }
        
        start_time = time.time()
        
        try:
            # Ejecutar tests específicos
            for method_name in test_methods:
                if hasattr(test_instance, method_name):
                    print(f"   🔍 {method_name}...", end=' ')
                    
                    try:
                        method = getattr(test_instance, method_name)
                        method()
                        
                        results['tests_executed'].append({
                            'method': method_name,
                            'status': 'PASS',
                            'error': None
                        })
                        results['success_count'] += 1
                        print("✅")
                        
                    except Exception as e:
                        results['tests_executed'].append({
                            'method': method_name,
                            'status': 'FAIL',
                            'error': str(e)
                        })
                        print(f"❌ ({str(e)[:50]}...)")
                
                else:
                    print(f"   ⚠️ Método {method_name} no encontrado")
            
            # Limpiar
            test_instance.tearDown()
            
        except Exception as e:
            print(f"   ❌ Error en setup/teardown: {e}")
        
        end_time = time.time()
        results['execution_time'] = end_time - start_time
        
        # Calcular tasa de éxito
        success_rate = results['success_count'] / results['total_tests'] if results['total_tests'] > 0 else 0
        results['success_rate'] = success_rate
        
        # Determinar estado general
        if success_rate >= min_threshold:
            if success_rate >= 0.95:
                results['overall_status'] = '✅ EXCELENTE'
            elif success_rate >= 0.85:
                results['overall_status'] = '✅ BUENO'
            else:
                results['overall_status'] = '✅ ACEPTABLE'
        else:
            results['overall_status'] = '❌ INSUFICIENTE'
        
        # Mostrar resumen
        print(f"   📊 Éxito: {results['success_count']}/{results['total_tests']} ({success_rate:.1%})")
        print(f"   ⏱️ Tiempo: {results['execution_time']:.2f}s")
        print(f"   🎯 Estado: {results['overall_status']}")
        
        return results
    
    def run_all_quick_tests(self, max_controllers: int = None) -> Dict[str, Any]:
        """
        Ejecuta tests rápidos para múltiples controladores
        
        Args:
            max_controllers: Número máximo de controladores a testear
            
        Returns:
            Dict con resultados de todos los tests
        """
        print("\n⚡ QUICK ACCURACY TEST SUITE")
        print("=" * 50)
        print("🎯 Ejecutando subset optimizado de tests de precisión")
        
        start_time = time.time()
        all_results = {}
        
        # Determinar controladores a testear
        controllers_to_test = self.priority_controllers
        if max_controllers:
            controllers_to_test = controllers_to_test[:max_controllers]
        
        print(f"📋 Controladores a testear: {', '.join(controllers_to_test)}")
        
        # Ejecutar tests
        for i, controller in enumerate(controllers_to_test, 1):
            try:
                print(f"\n[{i}/{len(controllers_to_test)}] ", end='')
                result = self.run_quick_test(controller)
                all_results[controller] = result
                
            except Exception as e:
                print(f"❌ Error en {controller}: {e}")
                all_results[controller] = {
                    'controller': controller,
                    'error': str(e),
                    'overall_status': '❌ ERROR'
                }
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Generar reporte rápido
        self.generate_quick_report(all_results, total_time)
        
        return all_results
    
    def generate_quick_report(self, results: Dict[str, Any], total_time: float):
        """
        Genera reporte rápido de los tests
        
        Args:
            results: Resultados de los tests
            total_time: Tiempo total de ejecución
        """
        print(f"\n{'=' * 50}")
        print("📊 REPORTE RÁPIDO DE PRECISIÓN")
        print(f"{'=' * 50}")
        
        print(f"⏱️ Tiempo total: {total_time:.2f}s")
        print(f"📅 Ejecutado: {datetime.now().strftime('%H:%M:%S')}")
        
        # Estadísticas rápidas
        total_tests = sum(r.get('total_tests', 0) for r in results.values() if 'total_tests' in r)
        total_success = sum(r.get('success_count', 0) for r in results.values() if 'success_count' in r)
        overall_rate = total_success / total_tests if total_tests > 0 else 0
        
        print(f"\n📈 RESULTADOS GLOBALES:")
        print(f"   🎯 Tests ejecutados: {total_tests}")
        print(f"   ✅ Tasa de éxito: {overall_rate:.1%}")
        
        # Resultados por controlador
        print(f"\n🏆 RESULTADOS POR CONTROLADOR:")
        
        valid_results = [(name, data) for name, data in results.items() if 'success_rate' in data]
        
        for controller, data in valid_results:
            threshold = self.min_accuracy_thresholds.get(controller, 0.80)
            rate = data['success_rate']
            time_taken = data['execution_time']
            status = data['overall_status']
            
            threshold_met = "✅" if rate >= threshold else "❌"
            
            print(f"   • {controller.upper():12} {rate:6.1%} ({time_taken:4.1f}s) {threshold_met} {status}")
        
        # Alertas
        failed_controllers = [
            name for name, data in valid_results 
            if data['success_rate'] < self.min_accuracy_thresholds.get(name, 0.80)
        ]
        
        if failed_controllers:
            print(f"\n⚠️ REQUIEREN ATENCIÓN:")
            for controller in failed_controllers:
                data = results[controller]
                threshold = self.min_accuracy_thresholds[controller]
                gap = threshold - data['success_rate']
                print(f"   • {controller.upper()}: {data['success_rate']:.1%} (necesita +{gap:.1%})")
        
        # Estado general
        print(f"\n🎯 ESTADO GENERAL:")
        if overall_rate >= 0.90:
            print("   ✅ Sistema con excelente precisión")
        elif overall_rate >= 0.80:
            print("   ✅ Sistema con buena precisión")
        elif overall_rate >= 0.70:
            print("   ⚠️ Sistema con precisión aceptable")
        else:
            print("   ❌ Sistema requiere mejoras en precisión")
        
        print("=" * 50)
    
    def run_single_controller_deep_dive(self, controller: str):
        """
        Ejecuta test profundo para un controlador específico
        
        Args:
            controller: Controlador a testear en profundidad
        """
        if controller not in self.test_classes:
            print(f"❌ Controlador '{controller}' no disponible")
            return
        
        print(f"\n🔍 DEEP DIVE: {controller.upper()} CONTROLLER")
        print("=" * 60)
        
        test_class = self.test_classes[controller]
        
        # Ejecutar todos los tests del controlador
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        
        start_time = time.time()
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        end_time = time.time()
        
        # Mostrar resumen detallado
        print(f"\n📊 RESUMEN DETALLADO {controller.upper()}:")
        print(f"   ✅ Tests ejecutados: {result.testsRun}")
        print(f"   ❌ Fallos: {len(result.failures)}")
        print(f"   🐛 Errores: {len(result.errors)}")
        print(f"   ⏱️ Tiempo: {end_time - start_time:.2f}s")
        
        success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun
        print(f"   📈 Tasa de éxito: {success_rate:.1%}")


def main():
    """Función principal"""
    runner = QuickAccuracyTestRunner()
    
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        if arg == "all":
            # Todos los controladores
            runner.run_all_quick_tests()
        elif arg.startswith("top"):
            # Top N controladores
            try:
                n = int(arg[3:]) if len(arg) > 3 else 3
                runner.run_all_quick_tests(max_controllers=n)
            except ValueError:
                runner.run_all_quick_tests(max_controllers=3)
        elif arg in runner.test_classes:
            # Controlador específico (deep dive)
            runner.run_single_controller_deep_dive(arg)
        else:
            # Lista de controladores
            controllers = arg.split(',')
            for controller in controllers:
                if controller in runner.test_classes:
                    runner.run_quick_test(controller)
                else:
                    print(f"⚠️ Controlador '{controller}' no disponible")
    else:
        # Test rápido por defecto (top 3)
        print("🚀 Ejecutando quick test para controladores prioritarios")
        runner.run_all_quick_tests(max_controllers=3)


if __name__ == '__main__':
    main() 