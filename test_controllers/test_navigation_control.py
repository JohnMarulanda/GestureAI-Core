#!/usr/bin/env python3
"""
Script de prueba para el Control de Navegación por Gestos
Utiliza MediaPipe Gesture Recognizer para controlar la navegación de ventanas.

Gestos soportados:
1. Victoria (Victory) → Abrir Win+Tab
2. Victoria + Pulgar → Flecha Derecha
3. Te amo (ILoveYou) → Minimizar ventana
4. Puño cerrado (Closed_Fist) → Maximizar ventana
5. Señalar arriba (Pointing_Up) → Cerrar ventana
6. Pulgar arriba (Thumb_Up) → Cambiar escritorio

Controles:
- ESC: Salir del programa
"""

import sys
import os

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.controllers.navigation_controller import NavigationController

def main():
    """Función principal para ejecutar la prueba de control de navegación."""
    print("="*60)
    print("🧭 PRUEBA DE CONTROL DE NAVEGACIÓN POR GESTOS")
    print("="*60)
    print("🎯 OBJETIVO:")
    print("   Probar el control de navegación de ventanas usando")
    print("   5 gestos predefinidos para operaciones comunes.")
    print()
    print("🖐️ GESTOS DE CONTROL:")
    print("   ✌️ Victoria (V)          → Abrir Win+Tab")
    print("   ✌️👍 Victoria + Pulgar    → Flecha Derecha")
    print("   🤟 Te amo                → Minimizar ventana")
    print("   ✊ Puño cerrado          → Maximizar ventana")
    print("   ☝️ Señalar arriba        → Cerrar ventana")
    print("   👍 Pulgar arriba         → Cambiar escritorio")
    print()
    print("🎮 FUNCIONES DE NAVEGACIÓN:")
    print("   - Abrir Win+Tab: Mostrar vista de tareas (Task View)")
    print("   - Flecha Derecha: Navegar hacia la derecha en cualquier contexto")
    print("   - Minimizar: Reducir ventana actual a la barra de tareas")
    print("   - Maximizar: Expandir ventana actual a pantalla completa")
    print("   - Cerrar: Cerrar la ventana o aplicación actual")
    print("   - Cambiar escritorio: Navegar entre escritorios virtuales")
    print()
    print("📊 CARACTERÍSTICAS:")
    print("   - Control en tiempo real con alta precisión")
    print("   - Umbral de confianza: 75%")
    print("   - Delay entre acciones: 1.0 segundos")
    print("   - Soporte para 1 mano optimizado")
    print("   - Gestos naturales e intuitivos")
    print("   - Estadísticas de uso en tiempo real")
    print("   - Interfaz visual con información detallada")
    print("   - Landmarks de mano dibujados")
    print("   - Indicadores de tiempo de espera")
    print("   - Mensajes de confirmación de acciones")
    print()
    print("🔧 CONFIGURACIÓN:")
    print("   - Gestos: Victory, Victory+Thumb, ILoveYou, Closed_Fist, Pointing_Up, Thumb_Up")
    print("   - Detección personalizada para Victoria + Pulgar")
    print("   - Delay específico para evitar acciones múltiples")
    print("   - Threading para acciones no bloqueantes")
    print("   - Manejo robusto de errores")
    print("   - Integración completa con Windows")
    print()
    print("⌨️  CONTROLES:")
    print("   ESC      : Salir del programa")
    print()
    print("🪟 ACCIONES DE NAVEGACIÓN:")
    print("   📋 ABRIR WIN+TAB: Abre Task View (vista de tareas)")
    print("   ➡️ FLECHA DERECHA: Presiona flecha derecha para navegar")
    print("   ⬇️ MINIMIZAR: Usa Win+Flecha Abajo para minimizar")
    print("   ⬆️ MAXIMIZAR: Usa Win+Flecha Arriba para maximizar")
    print("   ❌ CERRAR: Usa Alt+F4 para cerrar ventana actual")
    print("   🖥️ CAMBIAR ESCRITORIO: Usa Ctrl+Win+Derecha para cambiar")
    print()
    print("🔍 REQUISITOS:")
    print("   - Cámara web funcional")
    print("   - Modelo gesture_recognizer.task en models/")
    print("   - pyautogui instalado para control de ventanas")
    print("   - Windows 10/11 para funciones completas")
    print("   - Escritorios virtuales configurados (opcional)")
    print()
    print("💡 RECOMENDACIONES:")
    print("   - Ten algunas ventanas abiertas para probar")
    print("   - Configura escritorios virtuales para probar cambio")
    print("   - Mantén buena iluminación para detección")
    print("   - Usa gestos claros y definidos")
    print("   - Victoria simple: solo índice y medio extendidos")
    print("   - Victoria + Pulgar: índice, medio Y pulgar extendidos")
    print("   - El gesto 'Te amo' es meñique + índice + pulgar extendidos")
    print("   - Prueba cada gesto individualmente primero")
    print()
    print("🎯 CASOS DE USO:")
    print("   - Abrir Task View con Victoria simple")
    print("   - Navegar con Victoria + Pulgar (solo flecha derecha)")
    print("   - Control de ventanas sin tocar teclado")
    print("   - Presentaciones y demostraciones")
    print("   - Accesibilidad para usuarios con limitaciones")
    print("   - Flujos de trabajo eficientes")
    print("   - Control remoto de presentaciones")
    print()
    print("⚠️  ADVERTENCIAS:")
    print("   - Las acciones se ejecutarán en ventanas reales")
    print("   - Guarda tu trabajo antes de probar cerrar ventanas")
    print("   - Delay de 1 segundo entre acciones")
    print("   - Algunas funciones requieren Windows 10/11")
    print("   - Los escritorios virtuales deben estar configurados")
    print("   - Alt+F4 cerrará la aplicación actual")
    print()
    print("🔧 FUNCIONES DE WINDOWS:")
    print("   - Win+Tab: Abre Task View (vista de tareas)")
    print("   - Win+↑: Maximiza la ventana actual")
    print("   - Win+↓: Minimiza la ventana actual")
    print("   - Alt+F4: Cierra la aplicación actual")
    print("   - Ctrl+Win+→: Cambia al siguiente escritorio virtual")
    print()
    
    try:
        input("Presiona ENTER para comenzar la prueba...")
    except KeyboardInterrupt:
        print("\n❌ Operación cancelada por el usuario")
        return
    
    # Crear y ejecutar el controlador
    try:
        print("\n🧭 Inicializando controlador de navegación...")
        controller = NavigationController()
        controller.run()
    except Exception as e:
        print(f"❌ Error al ejecutar el controlador: {e}")
        print("   Verifica que:")
        print("   1. La cámara esté disponible")
        print("   2. El modelo gesture_recognizer.task exista en models/")
        print("   3. Las dependencias estén instaladas correctamente:")
        print("      pip install mediapipe opencv-python pyautogui")
        print("   4. Estés usando Windows 10/11 para funciones completas")
        print("   5. Tengas permisos para controlar ventanas")
        print("   6. pyautogui esté configurado correctamente")
    
    print("\n👋 ¡Gracias por probar el control de navegación por gestos!")
    print("   Recuerda: Los gestos naturales hacen la navegación más fluida")

if __name__ == "__main__":
    main() 