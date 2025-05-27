# GestureRecognitionManager

## Descripción General

El `GestureRecognitionManager` es un controlador centralizado para el reconocimiento de gestos manuales en la aplicación GestureAI-Core. Implementa el patrón Singleton para proporcionar una instancia única que gestiona todo el reconocimiento de gestos, permitiendo que múltiples controladores se suscriban a gestos específicos sin duplicar código.

## Características Principales

- **Patrón Singleton**: Garantiza una única instancia en toda la aplicación
- **Thread-safe**: Implementación segura para entornos multihilo
- **Gestión de Cámara**: Inicialización con resolución configurable y selección automática
- **Procesamiento de Gestos**: Detección de múltiples gestos simultáneamente
- **Configuración desde JSON**: Gestos definidos en `GestureConfig.json`
- **Sistema de Suscripción**: Los controladores pueden suscribirse a gestos específicos
- **Optimización de Rendimiento**: Pool de objetos para frames y control de FPS

## Requisitos de Rendimiento

- **Latencia**: < 50ms
- **Uso de memoria**: < 200MB
- **Uso de CPU**: < 30%
- **FPS**: 30 FPS o superior

## Diagrama de Arquitectura

```
+-------------------+      +------------------------+
| Controladores     |      | GestureRecognitionManager |
| (App, System,     +----->+ (Singleton)           |
|  Mouse, etc.)     |      |                        |
+-------------------+      +------------+-----------+
                                        |
                                        v
                            +-----------------------+
                            | GestureDetector       |
                            | (MediaPipe)           |
                            +-----------------------+
```

## Uso Básico

### Obtener la Instancia

```python
from core.gesture_recognition_manager import GestureRecognitionManager
from config import settings

# Obtener la instancia única
gesture_manager = GestureRecognitionManager()
```

### Iniciar la Cámara y el Procesamiento

```python
# Iniciar la cámara con configuración desde settings.py
gesture_manager.start_camera_with_settings(
    camera_id=settings.DEFAULT_CAMERA_ID,
    width=settings.CAMERA_WIDTH,
    height=settings.CAMERA_HEIGHT
)

# Iniciar el procesamiento de gestos en un hilo separado
gesture_manager.start_processing()
```

### Suscribirse a Gestos

```python
def handle_gesture(event_type, gesture_data):
    """Callback para manejar eventos de gestos."""
    if event_type == "detected":
        print(f"Gesto detectado: {gesture_data['name']}")
    elif event_type == "updated":
        print(f"Gesto actualizado: {gesture_data['name']}")
    elif event_type == "ended":
        print(f"Gesto terminado: {gesture_data['id']}")

# Suscribirse a un gesto específico
gesture_manager.subscribe_to_gesture("pinch", handle_gesture)
```

### Consultar Gestos Activos

```python
# Obtener todos los gestos activos
active_gestures = gesture_manager.get_current_gesture()

# Obtener un gesto específico
pinch_gesture = gesture_manager.get_current_gesture("pinch")

# Obtener nivel de confianza
confidence = gesture_manager.get_gesture_confidence("pinch")
```

### Liberar Recursos

```python
# Detener el procesamiento
gesture_manager.stop_processing()

# Liberar recursos
gesture_manager.dispose()
```

## Configuración de Gestos

Los gestos se configuran en el archivo `config/GestureConfig.json` con el siguiente formato:

```json
{
    "hand_gestures": [
        {
            "id": "pinch",
            "name": "Pinch Gesture",
            "landmarks": [[4, 8]],
            "threshold": 0.85,
            "action": "pinch_action"
        }
    ],
    "keyboard_gestures": {
        "copy": {
            "shortcut": ["ctrl", "c"],
            "gesture": [0, 1, 1, 0, 0]
        }
    },
    "button_gestures": {
        "button1": [0, 1, 0, 0, 0]
    },
    "app_gestures": {
        "open": {
            "Chrome": [0, 1, 1, 0, 0]
        }
    }
}
```

Donde:
- **id**: Identificador único del gesto
- **name**: Nombre descriptivo
- **landmarks**: Puntos de referencia en la mano para detectar el gesto
- **threshold**: Umbral de confianza (0.0 a 1.0)
- **action**: Comando o acción asociada

La configuración del GestureRecognitionManager se centraliza en `config/settings.py`, que incluye parámetros como resolución de cámara, FPS objetivo, y rutas a archivos de configuración.

## API Pública

### Gestión de Cámara

- `start_camera_with_settings(camera_id=0, width=640, height=480)`: Inicializa la cámara con resolución específica
- `get_camera_status()`: Obtiene el estado actual de la cámara

### Procesamiento de Gestos

- `start_processing()`: Inicia el procesamiento de gestos en un hilo separado
- `stop_processing()`: Detiene el procesamiento de gestos

### Interfaz de Gestos

- `get_current_gesture(gesture_id=None)`: Obtiene información sobre gestos activos
- `subscribe_to_gesture(gesture_id, callback)`: Suscribe una función a un gesto específico
- `unsubscribe_from_gesture(gesture_id, callback=None)`: Cancela la suscripción a un gesto
- `get_gesture_confidence(gesture_id=None)`: Obtiene el nivel de confianza de un gesto

### Configuración

- `update_gesture_config(gesture_id, parameters)`: Actualiza la configuración de un gesto
- `get_available_gestures()`: Obtiene la lista de gestos disponibles
- `add_gesture_config(gesture_config)`: Añade una nueva configuración de gesto
- `remove_gesture_config(gesture_id)`: Elimina una configuración de gesto

### Gestión de Recursos

- `dispose()`: Libera todos los recursos utilizados

## Integración con Controladores Existentes

Para integrar el `GestureRecognitionManager` con controladores existentes:

1. Obtener la instancia única del gestor
2. Suscribirse a los gestos necesarios
3. Implementar callbacks para manejar los eventos de gestos
4. Eliminar la lógica de detección duplicada en los controladores

Ejemplo de migración:

```python
# Antes
class MyController(GestureDetector):
    def __init__(self):
        super().__init__()
        # Inicialización específica del controlador
    
    def detect_gesture(self, hand_landmarks):
        # Lógica de detección específica
        pass

# Después
class MyController:
    def __init__(self):
        self.gesture_manager = GestureRecognitionManager()
        self.gesture_manager.subscribe_to_gesture("gesture_id", self.handle_gesture)
    
    def handle_gesture(self, event_type, gesture_data):
        # Manejar eventos de gestos
        pass
```

## Buenas Prácticas

1. **Suscripciones Específicas**: Suscribirse solo a los gestos necesarios para cada controlador
2. **Manejo de Eventos**: Implementar callbacks eficientes que no bloqueen el hilo principal
3. **Liberación de Recursos**: Llamar a `dispose()` cuando ya no se necesite el gestor
4. **Configuración de Gestos**: Utilizar umbrales apropiados para cada gesto
5. **Manejo de Excepciones**: Capturar excepciones en los callbacks para evitar interrupciones

## Solución de Problemas

- **Latencia Alta**: Reducir la resolución de la cámara o el FPS objetivo
- **Detección Incorrecta**: Ajustar los umbrales de confianza en la configuración
- **Uso Excesivo de CPU**: Verificar que no haya múltiples instancias procesando frames
- **Errores de Cámara**: Comprobar el estado con `get_camera_status()`

## Limitaciones Conocidas

- La detección de gestos depende de la calidad de la cámara y la iluminación
- El procesamiento en tiempo real puede verse afectado en hardware de baja potencia
- Algunos gestos complejos pueden requerir configuraciones personalizadas