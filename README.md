# GestureAI-Core

## 🎯 Descripción
GestureAI-Core es un sistema backend robusto diseñado para el reconocimiento de gestos en tiempo real, permitiendo el control del sistema operativo a través de gestos de mano. Utiliza tecnologías de vanguardia como MediaPipe, Python y FastAPI para proporcionar una experiencia fluida y precisa.

## ✨ Características Principales

- **Control de Ratón Avanzado**: Navegación fluida del cursor, clicks y arrastrado mediante gestos de mano derecha
- **Gestión de Aplicaciones**: Apertura y cierre de aplicaciones específicas mediante gestos personalizados
- **Control Multimedia**: Reproducción, pausa, volumen y navegación de contenido multimedia
- **Navegación del Sistema**: Navegación web, cambio entre ventanas y manejo del escritorio
- **Atajos del Sistema**: Ejecución de shortcuts comunes del sistema operativo
- **Control de Configuración**: Ajuste de brillo, volumen del sistema y configuraciones básicas

## 🚀 Rendimiento

- **Tiempo de Respuesta**: < 45ms para gestos básicos
- **Precisión**: 87-92% en condiciones normales de iluminación
- **Uso de CPU**: 12-18%
- **Uso de Memoria**: 245-280MB
- **FPS**: 28-30 frames por segundo

## 🛠️ Tecnologías Utilizadas

### Core Framework
- MediaPipe >= 0.10.0
- OpenCV >= 4.8.0
- NumPy >= 1.21.0
- Python 3.8+

### API y Comunicación
- FastAPI >= 0.103.0
- uvicorn == 0.34.2
- python-dotenv >= 1.0.0

### Control del Sistema
- PyAutoGUI >= 0.9.54
- pynput >= 1.7.6
- autopy >= 4.0.0
- keyboard >= 0.13.5
- psutil >= 5.9.0

## 📦 Estructura del Sistema

El sistema está dividido en 9 controladores especializados:

1. **MouseController**: Control preciso del cursor (21KB)
2. **AppController**: Gestión de aplicaciones (23KB)
3. **NavigationController**: Navegación del sistema (18KB)
4. **VolumeController**: Control de audio (17KB)
5. **SystemController**: Funciones del sistema (24KB)
6. **ShortcutsController**: Atajos del sistema (18KB)
7. **MultimediaController**: Control multimedia (24KB)
8. **BrightnessController**: Control de brillo (17KB)
9. **CannedGesturesController**: Gestos predefinidos (12KB)

## 🤚 Gestos Implementados

```python
# Gestos para control de mouse (mano derecha)
GESTOS_MOUSE = {
    '11000': 'cursor',      # Pulgar + índice (mover cursor)
    '11100': 'left_click',  # Pulgar + índice + medio (click izquierdo)
    '11110': 'right_click', # Pulgar + índice + medio + anular (click derecho)
    '01111': 'drag'         # 4 dedos sin pulgar (arrastrar)
}

# Gestos para aplicaciones
GESTOS_APLICACIONES = {
    'Closed_Fist': 'Chrome',
    'Thumb_Up': 'Notepad',
    'Victory': 'Calculator',
    'ILoveYou': 'Spotify'
}
```

## 🔧 Instalación y Uso

1. Clona el repositorio
2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Ejecuta el controlador deseado:
```bash
python -m core.controllers.enhanced.mouse_controller_enhanced
```

## 🎮 Ejecutables Disponibles

El sistema se distribuye como ejecutables independientes (~171MB cada uno):

- GestOS Mouse.exe - Control del ratón
- GestOS App.exe - Gestión de aplicaciones
- GestOS Navegacion.exe - Navegación web/sistema
- GestOS Sistema.exe - Funciones del sistema
- GestOS Volumen.exe - Control de audio
- GestOS Multimedia.exe - Control multimedia
- GestOS Atajos.exe - Atajos del sistema
- GestOS Brillo.exe - Control de brillo
- GestOS Canned.exe - Gestos predefinidos

## 🔍 Testing y Métricas

El sistema incluye un framework completo de testing ubicado en `/tests/performance/`:

- Tests de precisión de gestos
- Tests de latencia
- Análisis de errores
- Matrices de confusión
- Tests de falsos positivos

## 🤝 Contribución

Las pull requests son bienvenidas. Para cambios mayores, por favor abre un issue primero para discutir qué te gustaría cambiar.

## 📝 Licencia

[MIT](https://choosealicense.com/licenses/mit/)
