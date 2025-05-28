#!/usr/bin/env python3
"""
Script de prueba para el Controlador de Mouse Mejorado
Autor: Asistente IA
Fecha: 2025

Este script demuestra el uso del controlador de mouse mejorado con gestos de mano.
"""

import sys
import os

# Agregar el directorio core al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

from core.controllers.mouse_controller import ImprovedMouseController

def main():
    """Función principal para probar el controlador de mouse mejorado."""
    
    print("🎯 CONTROLADOR DE MOUSE CON GESTOS MEJORADO")
    print("=" * 50)
    print()
    print("📋 GESTOS DISPONIBLES:")
    print("   👆 Dedo índice solo: Mover cursor")
    print("   ✌️  Índice + Medio: Doble click")
    print("   🤟 Índice + Medio + Anular: Click derecho")
    print("   👍 Solo pulgar: Arrastrar")
    print()
    print("💡 CONSEJOS:")
    print("   • USA SOLO TU MANO DERECHA")
    print("   • Mantén la mano dentro del área blanca")
    print("   • Los gestos requieren 0.5 segundos para activarse")
    print("   • Usa buena iluminación para mejor detección")
    print("   • Mantén la mano a distancia media de la cámara")
    print()
    print("⌨️  CONTROLES:")
    print("   • Presiona 'q' para salir")
    print("   • ESC también funciona para cerrar")
    print()
    
    try:
        # Crear y ejecutar el controlador
        controller = ImprovedMouseController()
        
        print("🚀 Iniciando controlador...")
        print("   Asegúrate de que tu cámara esté funcionando")
        print("   Coloca tu mano frente a la cámara para comenzar")
        print()
        
        # Ejecutar el controlador
        controller.run()
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupción por teclado detectada")
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("💡 Asegúrate de instalar todas las dependencias:")
        print("   pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        print("💡 Verifica que tu cámara esté disponible y funcionando")
    finally:
        print("\n👋 Programa finalizado")
        print("   ¡Gracias por usar el Controlador de Mouse con Gestos!")


if __name__ == "__main__":
    main() 