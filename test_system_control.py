#!/usr/bin/env python3
"""
Script de prueba para el Control de Sistema por Gestos
Utiliza MediaPipe Gesture Recognizer para controlar funciones del sistema.

Gestos soportados:
1. Victoria (Victory) → Bloquear pantalla
2. Puño cerrado (Closed_Fist) → Apagar sistema
3. Palma abierta (Open_Palm) → Suspender sistema
4. Señalar arriba (Pointing_Up) → Reiniciar sistema

Controles:
- ESC: Salir del programa
"""

import sys
import os

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.controllers.system_controller import SystemController

def main():
    """Función principal para ejecutar la prueba de control de sistema."""
    print("="*60)
    print("🔧 PRUEBA DE CONTROL DE SISTEMA POR GESTOS")
    print("="*60)
    print("⚠️ ADVERTENCIA CRÍTICA: Este programa puede ejecutar")
    print("   acciones del sistema que afectarán tu computadora.")
    print()
    print("🎯 OBJETIVO:")
    print("   Probar el control de sistema usando 4 gestos específicos")
    print("   con confirmación de seguridad obligatoria.")
    print()
    print("🖐️ GESTOS DE CONTROL:")
    print("   ✌️ Victoria (V)     → Bloquear pantalla")
    print("   ✊ Puño cerrado     → Apagar sistema")
    print("   🖐️ Palma abierta    → Suspender sistema")
    print("   👆 Señalar arriba   → Reiniciar sistema")
    print()
    print("🔒 SISTEMA DE SEGURIDAD:")
    print("   - Mantén el gesto por 3 segundos para activar")
    print("   - Confirmación visual obligatoria")
    print("   - Mantén el mismo gesto 1 segundo más para confirmar")
    print("   - Auto-cancelación en 5 segundos")
    print("   - Cualquier otro gesto cancela la acción")
    print()
    print("📊 CARACTERÍSTICAS:")
    print("   - Control en tiempo real con alta precisión")
    print("   - Umbrales de confianza optimizados por gesto:")
    print("     • Victoria: 80% (bloquear)")
    print("     • Puño: 85% (apagar - máxima seguridad)")
    print("     • Palma: 60% (suspender - mejorada detección)")
    print("     • Señalar: 75% (reiniciar)")
    print("   - Estadísticas de acciones ejecutadas")
    print("   - Interfaz visual con progreso y confirmación")
    print("   - Soporte para 1 mano optimizado")
    print("   - Landmarks de mano dibujados")
    print()
    print("🔧 CONFIGURACIÓN:")
    print("   - Umbrales específicos por gesto")
    print("   - Tiempo de activación: 3 segundos")
    print("   - Tiempo de confirmación: 1 segundo")
    print("   - Auto-cancelación: 5 segundos")
    print("   - Detección optimizada para Open_Palm")
    print()
    print("⌨️  CONTROLES:")
    print("   ESC      : Salir del programa")
    print()
    print("⚠️  ACCIONES REALES DEL SISTEMA:")
    print("   🔒 BLOQUEAR: Bloqueará tu pantalla inmediatamente")
    print("   ⚡ APAGAR: Apagará tu computadora en 5 segundos")
    print("   😴 SUSPENDER: Pondrá tu sistema en modo suspensión")
    print("   🔄 REINICIAR: Reiniciará tu computadora inmediatamente")
    print()
    print("🔍 REQUISITOS:")
    print("   - Cámara web funcional")
    print("   - Modelo gesture_recognizer.task en models/")
    print("   - Permisos de administrador (para algunas acciones)")
    print("   - Sistema Windows compatible")
    print()
    print("💡 RECOMENDACIONES:")
    print("   - Guarda tu trabajo antes de comenzar")
    print("   - Cierra aplicaciones importantes")
    print("   - Ten cuidado con los gestos de apagado")
    print("   - Usa en un entorno controlado")
    print()
    
    # Confirmación del usuario con advertencia extra
    print("🚨 CONFIRMACIÓN REQUERIDA:")
    print("   Este programa ejecutará acciones REALES del sistema.")
    print("   ¿Estás seguro de que quieres continuar?")
    print()
    
    try:
        response = input("Escribe 'SI ACEPTO' para continuar o presiona ENTER para cancelar: ")
        if response.strip().upper() != "SI ACEPTO":
            print("\n❌ Operación cancelada por el usuario")
            print("   Es recomendable probar primero con otros controladores")
            return
    except KeyboardInterrupt:
        print("\n❌ Operación cancelada por el usuario")
        return
    
    print("\n⚠️ ÚLTIMA ADVERTENCIA:")
    print("   Las acciones del sistema se ejecutarán REALMENTE.")
    print("   Asegúrate de haber guardado tu trabajo.")
    print()
    
    try:
        input("Presiona ENTER para continuar o Ctrl+C para cancelar...")
    except KeyboardInterrupt:
        print("\n❌ Operación cancelada por el usuario")
        return
    
    # Crear y ejecutar el controlador
    try:
        print("\n🔧 Inicializando controlador de sistema...")
        controller = SystemController()
        controller.run()
    except Exception as e:
        print(f"❌ Error al ejecutar el controlador: {e}")
        print("   Verifica que:")
        print("   1. La cámara esté disponible")
        print("   2. El modelo gesture_recognizer.task exista en models/")
        print("   3. Las dependencias estén instaladas correctamente")
        print("   4. Tengas permisos de administrador si es necesario")
        print("   5. Tu sistema sea compatible con las funciones")
    
    print("\n👋 ¡Gracias por probar el control de sistema por gestos!")
    print("   Recuerda: Siempre ten cuidado con las acciones del sistema")

if __name__ == "__main__":
    main() 