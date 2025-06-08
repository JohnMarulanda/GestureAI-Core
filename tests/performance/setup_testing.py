"""
Script de configuración para el entorno de testing de performance.
Instala dependencias y configura directorios necesarios.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def create_directory_structure():
    """Crea la estructura de directorios para testing"""
    
    base_dir = Path("tests/performance")
    
    directories = [
        base_dir / "metrics" / "accuracy",
        base_dir / "metrics" / "response_time", 
        base_dir / "metrics" / "error_analysis",
        base_dir / "metrics" / "confusion_matrix",
        base_dir / "metrics" / "false_predictions",
        base_dir / "reports",
        base_dir / "fixtures",
        base_dir / "utils",
        base_dir / "config",
        base_dir / "data" / "test_images",
        base_dir / "data" / "test_videos",
        base_dir / "data" / "benchmarks"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✅ Creado directorio: {directory}")
    
    # Crear archivos __init__.py necesarios
    init_files = [
        base_dir / "__init__.py",
        base_dir / "metrics" / "__init__.py",
        base_dir / "utils" / "__init__.py",
        base_dir / "config" / "__init__.py"
    ]
    
    for init_file in init_files:
        if not init_file.exists():
            init_file.write_text('"""Performance testing module"""')
            print(f"✅ Creado archivo: {init_file}")

def install_dependencies():
    """Instala las dependencias específicas para testing"""
    
    requirements_file = "tests/performance/requirements_testing.txt"
    
    if not os.path.exists(requirements_file):
        print(f"❌ No se encontró el archivo {requirements_file}")
        return False
    
    try:
        print("📦 Instalando dependencias de testing...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", requirements_file
        ])
        print("✅ Dependencias instaladas correctamente")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        return False

def create_sample_fixtures():
    """Crea fixtures de ejemplo para testing"""
    
    fixtures_dir = Path("tests/performance/fixtures")
    
    # Crear archivo de configuración de ejemplo
    sample_config = fixtures_dir / "sample_test_config.json"
    if not sample_config.exists():
        config_content = '''{
    "test_configuration": {
        "iterations": 100,
        "timeout": 300,
        "precision_threshold": 0.9
    },
    "gestures": {
        "basic": ["open_hand", "closed_fist", "pointing"],
        "mouse": ["click_left", "click_right", "scroll_up"],
        "navigation": ["swipe_left", "swipe_right", "zoom_in"]
    },
    "expected_metrics": {
        "max_response_time": 0.1,
        "min_accuracy": 90.0,
        "max_error_rate": 5.0
    }
}'''
        sample_config.write_text(config_content)
        print(f"✅ Creado fixture: {sample_config}")
    
    # Crear datos de test de ejemplo
    sample_data = fixtures_dir / "sample_test_data.py"
    if not sample_data.exists():
        data_content = '''"""
Datos de ejemplo para testing de performance
"""

SAMPLE_GESTURE_SEQUENCES = [
    {
        "gesture": "open_hand",
        "expected_confidence": 0.95,
        "expected_landmarks": 21,
        "test_duration": 2.0
    },
    {
        "gesture": "closed_fist", 
        "expected_confidence": 0.90,
        "expected_landmarks": 21,
        "test_duration": 1.5
    },
    {
        "gesture": "pointing",
        "expected_confidence": 0.85,
        "expected_landmarks": 21,
        "test_duration": 1.8
    }
]

PERFORMANCE_BENCHMARKS = {
    "mouse_controller": {
        "target_response_time": 0.03,
        "target_accuracy": 95.0
    },
    "navigation_controller": {
        "target_response_time": 0.05,
        "target_accuracy": 90.0
    },
    "volume_controller": {
        "target_response_time": 0.02,
        "target_accuracy": 98.0
    }
}
'''
        sample_data.write_text(data_content)
        print(f"✅ Creado fixture: {sample_data}")

def create_run_scripts():
    """Crea scripts de ejecución rápida"""
    
    scripts_dir = Path("tests/performance")
    
    # Script para test rápido
    quick_test_script = scripts_dir / "run_quick_tests.py"
    if not quick_test_script.exists():
        script_content = '''#!/usr/bin/env python3
"""Script para ejecutar tests rápidos de performance"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.performance.test_runner import PerformanceTestRunner

def main():
    runner = PerformanceTestRunner()
    
    print("🚀 Ejecutando tests rápidos de performance...")
    
    # Test rápido con menos iteraciones
    results = runner.run_full_suite()
    
    print("✅ Tests rápidos completados")
    print(f"📊 Reporte guardado en: {results.get('report_path', 'N/A')}")

if __name__ == "__main__":
    main()
'''
        quick_test_script.write_text(script_content)
        print(f"✅ Creado script: {quick_test_script}")
    
    # Script para test completo
    full_test_script = scripts_dir / "run_full_tests.py"
    if not full_test_script.exists():
        script_content = '''#!/usr/bin/env python3
"""Script para ejecutar la suite completa de tests de performance"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.performance.test_runner import PerformanceTestRunner

def main():
    runner = PerformanceTestRunner()
    
    print("🎯 Ejecutando suite completa de performance...")
    
    results = runner.run_full_suite()
    
    print("✅ Suite completa finalizada")
    print(f"📊 Reporte guardado en: {results.get('report_path', 'N/A')}")
    
    # Mostrar resumen
    if 'results' in results:
        print("\\n📈 Resumen de resultados:")
        for test_type, data in results['results'].items():
            print(f"  - {test_type}: ✅ Completado")

if __name__ == "__main__":
    main()
'''
        full_test_script.write_text(script_content)
        print(f"✅ Creado script: {full_test_script}")

def verify_installation():
    """Verifica que la instalación sea correcta"""
    
    print("🔍 Verificando instalación...")
    
    # Verificar directorios
    required_dirs = [
        "tests/performance/metrics",
        "tests/performance/reports",
        "tests/performance/fixtures",
        "tests/performance/utils"
    ]
    
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✅ Directorio encontrado: {directory}")
        else:
            print(f"❌ Directorio faltante: {directory}")
            return False
    
    # Verificar archivos clave
    required_files = [
        "tests/performance/base_performance_test.py",
        "tests/performance/test_runner.py",
        "tests/performance/utils/metrics_utils.py",
        "tests/performance/config/test_config.py"
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ Archivo encontrado: {file_path}")
        else:
            print(f"❌ Archivo faltante: {file_path}")
            return False
    
    print("✅ Verificación completada exitosamente")
    return True

def main():
    """Función principal de configuración"""
    
    print("🚀 Configurando entorno de testing de performance para GestureAI-Core")
    print("=" * 60)
    
    # Paso 1: Crear estructura de directorios
    print("\\n📁 Paso 1: Creando estructura de directorios...")
    create_directory_structure()
    
    # Paso 2: Instalar dependencias
    print("\\n📦 Paso 2: Instalando dependencias...")
    if not install_dependencies():
        print("❌ Error en la instalación de dependencias")
        return False
    
    # Paso 3: Crear fixtures de ejemplo
    print("\\n🔧 Paso 3: Creando fixtures de ejemplo...")
    create_sample_fixtures()
    
    # Paso 4: Crear scripts de ejecución
    print("\\n📝 Paso 4: Creando scripts de ejecución...")
    create_run_scripts()
    
    # Paso 5: Verificar instalación
    print("\\n🔍 Paso 5: Verificando instalación...")
    if not verify_installation():
        print("❌ Error en la verificación")
        return False
    
    print("\\n✅ Configuración completada exitosamente!")
    print("\\n🎯 Siguiente pasos:")
    print("  1. Ejecutar tests rápidos: python tests/performance/run_quick_tests.py")
    print("  2. Ejecutar suite completa: python tests/performance/run_full_tests.py") 
    print("  3. Ejecutar test específico: python tests/performance/test_runner.py --suite accuracy")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)