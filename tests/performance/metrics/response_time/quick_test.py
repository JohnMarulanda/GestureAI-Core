#!/usr/bin/env python3
"""
Script de ejecución rápida para tests de tiempo de respuesta.
Ejecuta tests básicos sin generar reportes completos.
"""

import sys
import os
import time
from datetime import datetime

# Agregar paths para imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from tests.performance.metrics.response_time.run_response_time_tests import ResponseTimeTestRunner

def quick_response_time_test():
    """Ejecuta tests rápidos de tiempo de respuesta"""
    
    print("⚡ Quick Response Time Test - GestureAI-Core")
    print("=" * 45)
    
    runner = ResponseTimeTestRunner()
    
    # Lista de controladores a testear (orden por importancia)
    priority_controllers = [
        'mouse_controller_enhanced',      # Más crítico
        'volume_controller_enhanced',     # Rápido de testear  
        'navigation_controller_enhanced', # Medio
        'shortcuts_controller_enhanced',  # Rápido
        'multimedia_controller_enhanced', # Medio
        'system_controller_enhanced',     # Más lento
        'app_controller_enhanced'         # El más lento
    ]
    
    results = {}
    start_time = datetime.now()
    
    for controller in priority_controllers:
        print(f"\n🎮 Testing {controller}...")
        
        try:
            # Ejecutar test con timeout implícito
            controller_start = time.time()
            result = runner.run_single_controller_test(controller)
            test_duration = time.time() - controller_start
            
            # Extraer métricas clave
            if result.get('test_status') == 'success':
                init_time = result.get('initialization_time', 0) * 1000  # ms
                
                # Buscar tiempo E2E promedio
                e2e_time = 0
                if 'end_to_end_latency' in result:
                    e2e_data = result['end_to_end_latency']
                    if isinstance(e2e_data, list) and e2e_data:
                        e2e_time = e2e_data[0].get('mean_latency', 0) * 1000
                    elif isinstance(e2e_data, dict):
                        e2e_time = e2e_data.get('mean', 0) * 1000
                
                # Estado basado en configuración
                config = result.get('controller_config', {})
                expected_time = config.get('expected_response_time', 0.1) * 1000  # ms
                
                status = "✅ PASS" if e2e_time <= expected_time else "⚠️ SLOW"
                
                print(f"   Inicialización: {init_time:.1f}ms")
                print(f"   E2E Promedio: {e2e_time:.1f}ms (límite: {expected_time:.1f}ms)")
                print(f"   Estado: {status}")
                print(f"   Duración del test: {test_duration:.2f}s")
                
                results[controller] = {
                    'status': 'success',
                    'init_time_ms': init_time,
                    'e2e_time_ms': e2e_time,
                    'expected_ms': expected_time,
                    'passes': e2e_time <= expected_time,
                    'test_duration': test_duration
                }
                
            else:
                print(f"   ❌ FAILED: {result.get('error', 'Unknown error')}")
                results[controller] = {
                    'status': 'failed',
                    'error': result.get('error', 'Unknown error'),
                    'test_duration': test_duration
                }
                
        except Exception as e:
            print(f"   💥 ERROR: {e}")
            results[controller] = {
                'status': 'error',
                'error': str(e),
                'test_duration': 0
            }
    
    # Resumen final
    total_time = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "=" * 45)
    print("📊 RESUMEN RÁPIDO")
    print("=" * 45)
    
    passed = 0
    failed = 0
    total_controllers = len(results)
    
    for controller, result in results.items():
        controller_short = controller.replace('_controller_enhanced', '')
        
        if result['status'] == 'success':
            if result['passes']:
                print(f"✅ {controller_short:15} - {result['e2e_time_ms']:5.1f}ms (PASS)")
                passed += 1
            else:
                print(f"⚠️ {controller_short:15} - {result['e2e_time_ms']:5.1f}ms (SLOW)")
        else:
            print(f"❌ {controller_short:15} - FAILED")
            failed += 1
    
    print("-" * 45)
    print(f"Resultado: {passed}/{total_controllers} controladores dentro del objetivo")
    print(f"Tiempo total: {total_time:.2f}s")
    
    # Recomendaciones rápidas
    print("\n💡 RECOMENDACIONES:")
    
    if passed == total_controllers:
        print("🎉 ¡Excelente! Todos los controladores cumplen los objetivos de rendimiento.")
    elif passed >= total_controllers * 0.8:
        print("👍 Buen rendimiento general. Revisar controladores lentos.")
        for controller, result in results.items():
            if result['status'] == 'success' and not result['passes']:
                print(f"   - Optimizar {controller.replace('_controller_enhanced', '')}")
    else:
        print("⚠️ Varios controladores necesitan optimización.")
        print("   - Revisar algoritmos de detección de gestos")
        print("   - Verificar configuración de hardware")
        print("   - Considerar optimizaciones de código")
    
    # Guardar resultados básicos
    try:
        import json
        output_dir = "tests/performance/reports"
        os.makedirs(output_dir, exist_ok=True)
        
        quick_report = {
            'timestamp': start_time.isoformat(),
            'test_type': 'quick_response_time',
            'duration': total_time,
            'results': results,
            'summary': {
                'total_controllers': total_controllers,
                'passed': passed,
                'failed': failed,
                'success_rate': passed / total_controllers
            }
        }
        
        report_file = os.path.join(output_dir, f"quick_response_test_{start_time.strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_file, 'w') as f:
            json.dump(quick_report, f, indent=2)
        
        print(f"\n📄 Reporte guardado: {report_file}")
        
    except Exception as e:
        print(f"⚠️ No se pudo guardar reporte: {e}")
    
    return passed == total_controllers

if __name__ == "__main__":
    success = quick_response_time_test()
    sys.exit(0 if success else 1) 