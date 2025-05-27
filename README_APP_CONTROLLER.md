# Controlador de Aplicaciones con Gestos de Mano

Este controlador permite abrir y cerrar aplicaciones de Windows usando gestos de mano detectados por la cámara.

## 🚀 Características

- **Control por gestos**: Abre y cierra aplicaciones usando gestos específicos de los dedos
- **Detección en tiempo real**: Procesamiento de video en tiempo real con MediaPipe
- **Interfaz visual**: Muestra el estado de los dedos y gestos detectados
- **Configuración flexible**: Gestos y aplicaciones configurables desde archivo JSON
- **Gestión de procesos**: Seguimiento inteligente de aplicaciones abiertas

## 📋 Requisitos

### Dependencias Python
```bash
pip install opencv-python mediapipe psutil numpy
```

### Aplicaciones configuradas por defecto
- **App1**: Google Chrome (`chrome.exe`)
- **App2**: Bloc de notas (`notepad.exe`) 
- **App3**: Calculadora (`calc.exe`)

## 🎮 Gestos Configurados

### Para Abrir Aplicaciones
| Aplicación | Gesto | Descripción |
|------------|-------|-------------|
| App1 (Chrome) | `[0,1,1,0,0]` | Índice y medio extendidos |
| App2 (Notepad) | `[1,1,0,0,0]` | Pulgar e índice extendidos |
| App3 (Calc) | `[1,1,1,0,0]` | Pulgar, índice y medio extendidos |

### Para Cerrar Aplicaciones
| Aplicación | Gesto | Descripción |
|------------|-------|-------------|
| App1 (Chrome) | `[0,0,0,0,0]` | Puño cerrado |
| App2 (Notepad) | `[0,0,0,0,1]` | Solo meñique extendido |
| App3 (Calc) | `[1,0,0,0,1]` | Pulgar y meñique extendidos |

### Controles Especiales
| Acción | Gesto | Descripción |
|--------|-------|-------------|
| Salir del controlador | `[1,0,0,1,0]` | Pulgar y anular extendidos |
| Salir de la aplicación | `[0,1,1,1,0]` | Índice, medio y anular extendidos |

## 🖐️ Cómo hacer los gestos

Los gestos se representan como `[Pulgar, Índice, Medio, Anular, Meñique]` donde:
- **1** = dedo extendido
- **0** = dedo cerrado/doblado

### Ejemplos:
- `[0,1,1,0,0]` = Solo índice y medio extendidos (✌️)
- `[1,1,1,1,1]` = Todos los dedos extendidos (🖐️)
- `[0,0,0,0,0]` = Puño cerrado (✊)

## 🚀 Uso

### Opción 1: Ejecutar directamente
```bash
cd GestureAI-Core
python core/controllers/app_controller.py
```

### Opción 2: Usar el script de prueba
```bash
cd GestureAI-Core
python test_app_controller.py
```

## 📖 Instrucciones de uso

1. **Inicia el programa** usando una de las opciones anteriores
2. **Posiciona tu mano** frente a la cámara, asegurándote de que esté bien iluminada
3. **Haz los gestos** configurados para controlar las aplicaciones
4. **Observa la pantalla** para ver:
   - El estado actual de tus dedos
   - Los gestos disponibles
   - Mensajes de confirmación cuando se ejecutan acciones
5. **Presiona 'q'** en la ventana de video para salir

## ⚙️ Configuración

### Modificar gestos y aplicaciones

Edita el archivo `config/GestureConfig.json`:

```json
{
    "app_gestures": {
        "open": {
            "MiApp": [1,0,1,0,1]
        },
        "close": {
            "MiApp": [0,1,0,1,0]
        }
    },
    "app_paths": {
        "MiApp": "C:\\Ruta\\A\\MiAplicacion.exe"
    }
}
```

### Agregar nuevas aplicaciones

1. Agrega la ruta en `app_paths`
2. Define gestos de apertura en `app_gestures.open`
3. Define gestos de cierre en `app_gestures.close`
4. Reinicia el controlador

## 🔧 Solución de problemas

### La cámara no funciona
- Verifica que la cámara esté conectada y funcionando
- Cierra otras aplicaciones que puedan estar usando la cámara
- Cambia el ID de cámara en `config/settings.py`

### Los gestos no se detectan
- Asegúrate de que tu mano esté bien iluminada
- Mantén la mano estable y visible
- Verifica que los dedos estén claramente extendidos o cerrados
- Ajusta la distancia de la cámara

### Las aplicaciones no se abren
- Verifica que las rutas en `app_paths` sean correctas
- Asegúrate de que las aplicaciones estén instaladas
- Ejecuta el programa como administrador si es necesario

### Error al cerrar aplicaciones
- Algunas aplicaciones pueden requerir permisos especiales
- Verifica que el proceso esté realmente en ejecución
- Usa el Administrador de tareas como respaldo

## 📁 Estructura de archivos

```
GestureAI-Core/
├── config/
│   ├── GestureConfig.json      # Configuración de gestos
│   └── settings.py             # Configuración general
├── core/
│   ├── controllers/
│   │   └── app_controller.py   # Controlador principal
│   ├── gesture_detector.py     # Detector base
│   └── gesture_recognition_manager.py  # Gestor centralizado
├── test_app_controller.py      # Script de prueba
└── README_APP_CONTROLLER.md    # Este archivo
```

## 🎯 Consejos para mejores resultados

1. **Iluminación**: Usa una buena iluminación frontal
2. **Fondo**: Un fondo contrastante ayuda a la detección
3. **Distancia**: Mantén tu mano a 30-60 cm de la cámara
4. **Estabilidad**: Mantén los gestos estables por 1-2 segundos
5. **Claridad**: Haz gestos claros y definidos

## 🆘 Soporte

Si encuentras problemas:

1. Revisa los logs en `logs/gesture_recognition.log`
2. Verifica que todas las dependencias estén instaladas
3. Asegúrate de que las rutas de aplicaciones sean correctas
4. Consulta la consola para mensajes de error detallados

---

¡Disfruta controlando tus aplicaciones con gestos de mano! 🖐️✨ 