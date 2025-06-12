"""
Configuración para tests de rendimiento del sistema GestureAI-Core.
Define parámetros, umbrales y configuraciones por defecto.
"""

from dataclasses import dataclass
from typing import Dict, List, Any
import os

@dataclass
class PerformanceThresholds:
    """Umbrales de rendimiento aceptables"""
    
    # Tiempo de respuesta (en segundos)
    max_response_time: float = 0.1  # 100ms
    avg_response_time: float = 0.05  # 50ms
    
    # Precisión (en porcentaje)
    min_accuracy: float = 90.0
    target_accuracy: float = 95.0
    
    # Tasa de error (en porcentaje)
    max_error_rate: float = 5.0
    target_error_rate: float = 2.0
    
    # Memoria y CPU
    max_memory_usage_mb: float = 512.0
    max_cpu_usage_percent: float = 80.0

@dataclass
class TestConfiguration:
    """Configuración general de tests"""
    
    # Iteraciones por defecto
    default_iterations: int = 100
    stress_test_iterations: int = 1000
    quick_test_iterations: int = 10
    
    # Timeouts
    test_timeout_seconds: int = 300  # 5 minutos
    single_iteration_timeout: int = 10  # 10 segundos
    
    # Directorios
    base_test_dir: str = "tests/performance"
    reports_dir: str = "tests/performance/reports"
    fixtures_dir: str = "tests/performance/fixtures"
    
    # Logging
    log_level: str = "INFO"
    log_to_file: bool = True
    
    # Visualización
    generate_plots: bool = True
    save_detailed_results: bool = True

class GestureTestData:
    """Datos de test para diferentes tipos de gestos"""
    
    # Gestos básicos para testing
    BASIC_GESTURES = [
        "open_hand",
        "closed_fist", 
        "pointing",
        "thumbs_up",
        "peace_sign"
    ]
    
    # Gestos de mouse
    MOUSE_GESTURES = [
        "click_left",
        "click_right", 
        "scroll_up",
        "scroll_down",
        "drag"
    ]
    
    # Gestos de navegación
    NAVIGATION_GESTURES = [
        "swipe_left",
        "swipe_right",
        "swipe_up", 
        "swipe_down",
        "zoom_in",
        "zoom_out"
    ]
    
    # Gestos de volumen
    VOLUME_GESTURES = [
        "volume_up",
        "volume_down",
        "mute",
        "unmute"
    ]
    
    # Gestos del sistema
    SYSTEM_GESTURES = [
        "minimize_all",
        "switch_app",
        "close_app",
        "screenshot"
    ]

class ControllerTestConfig:
    """Configuración específica para tests de controladores"""
    
    CONTROLLERS = {
        'mouse_controller_enhanced': {
            'test_gestures': GestureTestData.MOUSE_GESTURES,
            'expected_response_time': 0.03,  # 30ms
            'min_accuracy': 95.0,
            'critical_functions': ['move_mouse', 'click', 'scroll']
        },
        
        'navigation_controller_enhanced': {
            'test_gestures': GestureTestData.NAVIGATION_GESTURES,
            'expected_response_time': 0.05,  # 50ms
            'min_accuracy': 90.0,
            'critical_functions': ['navigate', 'zoom', 'swipe']
        },
        
        'volume_controller_enhanced': {
            'test_gestures': GestureTestData.VOLUME_GESTURES,
            'expected_response_time': 0.02,  # 20ms
            'min_accuracy': 98.0,
            'critical_functions': ['change_volume', 'mute_toggle']
        },
        
        'system_controller_enhanced': {
            'test_gestures': GestureTestData.SYSTEM_GESTURES,
            'expected_response_time': 0.1,  # 100ms
            'min_accuracy': 85.0,
            'critical_functions': ['execute_command', 'system_action']
        },
        
        'app_controller_enhanced': {
            'test_gestures': ['open_app', 'close_app', 'switch_app'],
            'expected_response_time': 0.2,  # 200ms (más lento por IO)
            'min_accuracy': 90.0,
            'critical_functions': ['launch_app', 'close_app', 'switch_context']
        },
        
        'shortcuts_controller_enhanced': {
            'test_gestures': ['ctrl_c', 'ctrl_v', 'alt_tab', 'win_key'],
            'expected_response_time': 0.03,  # 30ms
            'min_accuracy': 95.0,
            'critical_functions': ['execute_shortcut', 'key_combination']
        },
        
        'multimedia_controller_enhanced': {
            'test_gestures': ['play_pause', 'next_track', 'prev_track', 'stop'],
            'expected_response_time': 0.05,  # 50ms
            'min_accuracy': 92.0,
            'critical_functions': ['media_control', 'playback_control']
        },
        
        'brightness_controller_enhanced': {
            'test_gestures': ['brightness_up', 'brightness_down'],
            'expected_response_time': 0.04,  # 40ms
            'min_accuracy': 95.0,
            'critical_functions': ['adjust_brightness', 'get_brightness']
        },
        
        'canned_gestures_controller_enhanced': {
            'test_gestures': ['preset_1', 'preset_2', 'preset_3'],
            'expected_response_time': 0.02,  # 20ms
            'min_accuracy': 98.0,
            'critical_functions': ['execute_canned', 'load_preset']
        }
    }

class ModelTestConfig:
    """Configuración para tests de modelos"""
    
    MODELS = {
        'hand_landmarker.task': {
            'input_size': (224, 224),
            'expected_landmarks': 21,
            'confidence_threshold': 0.5,
            'max_inference_time': 0.05,  # 50ms
            'test_images_count': 100
        },
        
        'gesture_recognizer.task': {
            'input_size': (224, 224),
            'num_classes': len(GestureTestData.BASIC_GESTURES),
            'confidence_threshold': 0.7,
            'max_inference_time': 0.03,  # 30ms
            'test_sequences_count': 50
        }
    }

def get_test_config() -> TestConfiguration:
    """Retorna la configuración de test por defecto"""
    return TestConfiguration()

def get_performance_thresholds() -> PerformanceThresholds:
    """Retorna los umbrales de rendimiento por defecto"""
    return PerformanceThresholds()

def get_controller_config(controller_name: str) -> Dict[str, Any]:
    """
    Obtiene la configuración específica para un controlador
    
    Args:
        controller_name: Nombre del controlador
        
    Returns:
        Diccionario con la configuración del controlador
    """
    return ControllerTestConfig.CONTROLLERS.get(controller_name, {})

def get_model_config(model_name: str) -> Dict[str, Any]:
    """
    Obtiene la configuración específica para un modelo
    
    Args:
        model_name: Nombre del modelo
        
    Returns:
        Diccionario con la configuración del modelo
    """
    return ModelTestConfig.MODELS.get(model_name, {})

def create_test_directories():
    """Crea los directorios necesarios para los tests"""
    config = get_test_config()
    
    directories = [
        config.base_test_dir,
        config.reports_dir,
        config.fixtures_dir,
        f"{config.base_test_dir}/metrics/accuracy",
        f"{config.base_test_dir}/metrics/response_time",
        f"{config.base_test_dir}/metrics/error_analysis",
        f"{config.base_test_dir}/metrics/confusion_matrix",
        f"{config.base_test_dir}/metrics/false_predictions"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# Configuración de logging específica para tests
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        },
        'simple': {
            'format': '%(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'simple',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': 'tests/performance/reports/test_performance.log',
            'mode': 'a'
        }
    },
    'loggers': {
        'PerformanceTest': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': False
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    }
} 