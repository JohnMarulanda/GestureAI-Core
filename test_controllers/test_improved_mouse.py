#!/usr/bin/env python3
"""
Script de prueba para el Controlador de Mouse Mejorado
Utiliza MediaPipe para control de mouse con gestos de mano derecha.

Gestos soportados:
1. Dedo índice solo → Mover cursor
2. Índice + Medio → Doble click
3. Índice + Medio + Anular → Click derecho
4. Solo pulgar → Arrastrar

Controles:
- q: Salir del programa
"""

import sys
import os
import cv2
import time
import numpy as np

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.controllers.mouse_controller import ImprovedMouseController

class ImprovedMouseControllerTest:
    """Test wrapper for ImprovedMouseController with enhanced UI and statistics."""
    
    def __init__(self):
        """Initialize the test wrapper."""
        self.controller = ImprovedMouseController()
        
        # Gesture mapping for display
        self.gesture_names = {
            'cursor': 'Mover cursor (Índice)',
            'double_click': 'Doble click (Índice + Medio)',
            'right_click': 'Click derecho (3 dedos)',
            'drag': 'Arrastrar (Pulgar)',
            'none': 'Ninguno'
        }
        
        # Action counters
        self.action_counts = {
            'cursor_moves': 0,
            'double_clicks': 0,
            'right_clicks': 0,
            'drag_actions': 0
        }
        
        # Override controller methods to add logging and statistics
        self._override_controller_methods()
        
        print("✅ Controlador de Mouse Mejorado inicializado (Mano Derecha)")
        print("📋 Gestos disponibles:")
        print("   👆 Dedo índice: Mover cursor")
        print("   ✌️ Índice + Medio: Doble click")
        print("   🤟 Índice + Medio + Anular: Click derecho")
        print("   👍 Pulgar arriba: Arrastrar")
        print("   Presiona 'q' para salir")
    
    def _override_controller_methods(self):
        """Override controller methods to add logging and statistics."""
        # Store original methods
        original_move_cursor = self.controller.move_cursor
        original_handle_double_click = self.controller.handle_double_click
        original_handle_right_click = self.controller.handle_right_click
        original_handle_drag = self.controller.handle_drag
        
        def enhanced_move_cursor(landmarks):
            self.action_counts['cursor_moves'] += 1
            return original_move_cursor(landmarks)
        
        def enhanced_handle_double_click():
            result = original_handle_double_click()
            if result:
                self.action_counts['double_clicks'] += 1
                print(f"🖱️ Doble click ejecutado (Total: {self.action_counts['double_clicks']})")
            return result
        
        def enhanced_handle_right_click():
            result = original_handle_right_click()
            if result:
                self.action_counts['right_clicks'] += 1
                print(f"🖱️ Click derecho ejecutado (Total: {self.action_counts['right_clicks']})")
            return result
        
        def enhanced_handle_drag(active):
            if active and not self.controller.drag_active:
                self.action_counts['drag_actions'] += 1
                print(f"🖱️ Arrastre iniciado (Total: {self.action_counts['drag_actions']})")
            elif not active and self.controller.drag_active:
                print("🖱️ Arrastre finalizado")
            return original_handle_drag(active)
        
        # Replace methods
        self.controller.move_cursor = enhanced_move_cursor
        self.controller.handle_double_click = enhanced_handle_double_click
        self.controller.handle_right_click = enhanced_handle_right_click
        self.controller.handle_drag = enhanced_handle_drag
    
    def draw_ui(self, img, gesture, hand_type="", landmarks=None):
        """Dibujar interfaz de usuario."""
        h, w, _ = img.shape
        
        # Área de control del cursor
        cv2.rectangle(img, (self.controller.frameR, self.controller.frameR), 
                     (w - self.controller.frameR, h - self.controller.frameR), (255, 255, 255), 2)
        
        # Información del gesto actual y tipo de mano
        hand_status = "✅" if hand_type == "Derecha" else "❌" if hand_type == "Izquierda" else ""
        cv2.putText(img, f'Mano: {hand_type} {hand_status}', (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        gesture_display = self.gesture_names.get(gesture, gesture)
        cv2.putText(img, f'Gesto: {gesture_display}', (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # FPS
        cTime = time.time()
        fps = 1 / (cTime - self.controller.pTime + 0.001)
        self.controller.pTime = cTime
        cv2.putText(img, f'FPS: {int(fps)}', (w - 120, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        
        # Instrucciones
        instructions = [
            "👆 Indice: Cursor",
            "✌️ Indice+Medio: Doble click",
            "🤟 3 dedos: Click derecho",
            "👍 Pulgar: Arrastrar"
        ]
        
        for i, instruction in enumerate(instructions):
            cv2.putText(img, instruction, (10, h - 150 + i * 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    
    def draw_gesture_indicators(self, img, gesture, x=None, y=None):
        """Draw visual indicators for gestures."""
        if x is None or y is None:
            return
            
        if gesture == 'cursor':
            cv2.circle(img, (x, y), 8, (0, 255, 0), -1)
        elif gesture == 'double_click':
            cv2.circle(img, (x, y), 15, (0, 255, 0), -1)
            cv2.putText(img, "DOBLE CLICK", (x - 50, y - 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        elif gesture == 'right_click':
            cv2.circle(img, (x, y), 15, (0, 0, 255), -1)
            cv2.putText(img, "CLICK DERECHO", (x - 60, y - 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        elif gesture == 'drag':
            cv2.circle(img, (x, y), 12, (255, 0, 255), -1)
            cv2.putText(img, "ARRASTRANDO", (x - 50, y - 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
    
    def draw_statistics(self, img):
        """Display mouse control statistics."""
        try:
            height, width, _ = img.shape
            
            # Draw background for statistics
            stats_x = width - 250
            cv2.rectangle(img, (stats_x, 100), (width - 10, 220), (0, 0, 0), -1)
            cv2.rectangle(img, (stats_x, 100), (width - 10, 220), (255, 255, 255), 2)
            
            # Draw statistics title
            cv2.putText(img, "Estadisticas", 
                       (stats_x + 10, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            y_pos = 150
            stats_items = [
                ("Movimientos", self.action_counts['cursor_moves']),
                ("Doble clicks", self.action_counts['double_clicks']),
                ("Clicks derechos", self.action_counts['right_clicks']),
                ("Arrastres", self.action_counts['drag_actions'])
            ]
            
            for name, count in stats_items:
                cv2.putText(img, f"{name}: {count}", 
                           (stats_x + 10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                y_pos += 15
            
            # Total actions
            total_actions = sum([self.action_counts['double_clicks'], 
                               self.action_counts['right_clicks'], 
                               self.action_counts['drag_actions']])
            cv2.putText(img, f"Total acciones: {total_actions}", 
                       (stats_x + 10, y_pos + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
            
        except Exception as e:
            print(f"⚠️ Error al dibujar estadísticas: {e}")
    
    def print_statistics(self):
        """Print mouse control statistics."""
        print("\n" + "="*50)
        print("📊 ESTADÍSTICAS DE CONTROL DE MOUSE")
        print("="*50)
        
        print(f"{'Movimientos de cursor':<25} | {self.action_counts['cursor_moves']:>6}")
        print(f"{'Doble clicks':<25} | {self.action_counts['double_clicks']:>6}")
        print(f"{'Clicks derechos':<25} | {self.action_counts['right_clicks']:>6}")
        print(f"{'Acciones de arrastre':<25} | {self.action_counts['drag_actions']:>6}")
        
        total_actions = sum([self.action_counts['double_clicks'], 
                           self.action_counts['right_clicks'], 
                           self.action_counts['drag_actions']])
        print("-"*50)
        print(f"{'Total de acciones':<25} | {total_actions:>6}")
        print("="*50 + "\n")
    
    def run(self):
        """Run the enhanced mouse control loop."""
        if not self.controller.start_camera():
            print("❌ No se pudo iniciar la cámara")
            return
        
        print("🚀 Iniciando controlador de mouse con gestos...")
        print("   Muestra tu MANO DERECHA frente a la cámara")
        
        try:
            while True:
                success, img = self.controller.cap.read()
                if not success:
                    continue
                
                # Voltear imagen para efecto espejo
                img = cv2.flip(img, 1)
                h, w, _ = img.shape
                
                # Procesar con MediaPipe
                rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                results = self.controller.hands.process(rgb_img)
                
                gesture = 'none'
                hand_type = "Ninguna"
                cursor_x, cursor_y = None, None
                
                if results.multi_hand_landmarks:
                    for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                        # Verificar si es mano derecha
                        if self.controller.is_right_hand(hand_landmarks, results):
                            hand_type = "Derecha"
                            
                            # Dibujar landmarks
                            self.controller.draw_hand_landmarks(img, hand_landmarks, True)
                            
                            # Detectar posición de dedos
                            fingers = self.controller.get_finger_positions(hand_landmarks.landmark)
                            gesture = self.controller.detect_gesture(fingers, hand_landmarks.landmark)
                            
                            # Ejecutar acciones basadas en el gesto
                            if gesture == 'cursor':
                                cursor_x, cursor_y = self.controller.move_cursor(hand_landmarks.landmark)
                            
                            elif gesture == 'double_click':
                                cursor_x, cursor_y = self.controller.move_cursor(hand_landmarks.landmark)
                                self.controller.handle_double_click()
                            
                            elif gesture == 'right_click':
                                cursor_x, cursor_y = self.controller.move_cursor(hand_landmarks.landmark)
                                self.controller.handle_right_click()
                            
                            elif gesture == 'drag':
                                cursor_x, cursor_y = self.controller.move_cursor(hand_landmarks.landmark)
                                self.controller.handle_drag(True)
                            
                            # Si no hay gesto de arrastrar activo, detener arrastre
                            if gesture != 'drag':
                                self.controller.handle_drag(False)
                        else:
                            hand_type = "Izquierda"
                            # Dibujar landmarks en rojo para mano izquierda
                            self.controller.draw_hand_landmarks(img, hand_landmarks, False)
                
                # Actualizar cooldowns
                if self.controller.click_cooldown > 0:
                    self.controller.click_cooldown -= 1
                
                # Dibujar UI
                self.draw_ui(img, gesture, hand_type)
                
                # Dibujar indicadores de gestos
                self.draw_gesture_indicators(img, gesture, cursor_x, cursor_y)
                
                # Dibujar estadísticas
                self.draw_statistics(img)
                
                # Mostrar imagen
                cv2.imshow('Control de Mouse con Gestos - Mano Derecha', img)
                
                # Salir con 'q'
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        except KeyboardInterrupt:
            print("\n⚠️ Interrupción detectada")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            self.controller.stop_camera()
            self.print_statistics()
            print("👋 Controlador finalizado")

def main():
    """Función principal para probar el controlador de mouse mejorado."""
    
    print("🎯 CONTROLADOR DE MOUSE CON GESTOS MEJORADO")
    print("=" * 60)
    print()
    print("🎯 OBJETIVO:")
    print("   Controlar el mouse de tu computadora usando gestos")
    print("   de mano derecha con alta precisión y suavidad.")
    print()
    print("📋 GESTOS DISPONIBLES:")
    print("   👆 Dedo índice solo: Mover cursor")
    print("   ✌️  Índice + Medio: Doble click")
    print("   🤟 Índice + Medio + Anular: Click derecho")
    print("   👍 Solo pulgar: Arrastrar")
    print()
    print("🖐️ DETECCIÓN DE MANOS:")
    print("   ✅ Mano derecha: Funcional (landmarks verdes)")
    print("   ❌ Mano izquierda: Solo visual (landmarks rojos)")
    print("   - Solo la mano derecha controla el mouse")
    print("   - Detección automática del tipo de mano")
    print()
    print("📊 CARACTERÍSTICAS:")
    print("   - Suavizado de movimiento (factor 7)")
    print("   - Área de control delimitada (marco blanco)")
    print("   - Cooldown para evitar clicks múltiples")
    print("   - Confirmación de gestos (0.5 segundos)")
    print("   - Estadísticas en tiempo real")
    print("   - FPS counter para rendimiento")
    print("   - Indicadores visuales de acciones")
    print()
    print("🔧 CONFIGURACIÓN TÉCNICA:")
    print("   - Resolución cámara: 640x480")
    print("   - FPS objetivo: 30")
    print("   - Umbral detección: 70%")
    print("   - Modelo MediaPipe: Complejidad 1")
    print("   - Máximo 1 mano detectada")
    print("   - Cooldown doble click: 20 frames")
    print("   - Cooldown click derecho: 15 frames")
    print()
    print("💡 CONSEJOS:")
    print("   • USA SOLO TU MANO DERECHA")
    print("   • Mantén la mano dentro del área blanca")
    print("   • Los gestos requieren 0.5 segundos para activarse")
    print("   • Usa buena iluminación para mejor detección")
    print("   • Mantén la mano a distancia media de la cámara")
    print("   • Evita movimientos bruscos para mejor suavidad")
    print()
    print("⌨️  CONTROLES:")
    print("   • Presiona 'q' para salir")
    print("   • ESC también funciona para cerrar")
    print()
    print("🎯 CASOS DE USO:")
    print("   - Presentaciones sin tocar el mouse")
    print("   - Control remoto de la computadora")
    print("   - Accesibilidad para usuarios con limitaciones")
    print("   - Demostraciones interactivas")
    print("   - Gaming y entretenimiento")
    print()
    print("🔍 REQUISITOS:")
    print("   - Cámara web funcional")
    print("   - Buena iluminación")
    print("   - Dependencias instaladas:")
    print("     pip install mediapipe opencv-python pyautogui autopy pynput")
    print()
    
    try:
        input("Presiona ENTER para comenzar la prueba...")
    except KeyboardInterrupt:
        print("\n❌ Operación cancelada por el usuario")
        return
    
    # Crear y ejecutar el controlador de prueba
    try:
        print("\n🚀 Inicializando controlador de mouse...")
        print("   Asegúrate de que tu cámara esté funcionando")
        print("   Coloca tu mano derecha frente a la cámara para comenzar")
        print()
        
        test_controller = ImprovedMouseControllerTest()
        test_controller.run()
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupción por teclado detectada")
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("💡 Asegúrate de instalar todas las dependencias:")
        print("   pip install mediapipe opencv-python pyautogui autopy pynput numpy")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        print("💡 Verifica que tu cámara esté disponible y funcionando")
    finally:
        print("\n👋 Programa finalizado")
        print("   ¡Gracias por usar el Controlador de Mouse con Gestos!")

if __name__ == "__main__":
    main() 