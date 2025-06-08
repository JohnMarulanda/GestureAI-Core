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
import cv2
import time
import mediapipe as mp

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.controllers.navigation_controller import NavigationController

class NavigationControllerTest:
    """Test wrapper for NavigationController with enhanced UI and statistics."""
    
    def __init__(self):
        """Initialize the test wrapper."""
        self.controller = NavigationController()
        
        # Action status
        self.action_message = ""
        self.action_message_time = 0
        self.action_message_duration = 2.0
        
        # Spanish translations for display
        self.gesture_names = {
            'Victory': 'Victoria (V)',
            'ILoveYou': 'Te amo (I Love You)',
            'Closed_Fist': 'Puño cerrado',
            'Pointing_Up': 'Señalando hacia arriba',
            'Thumb_Up': 'Pulgar hacia arriba'
        }
        
        # Action descriptions
        self.action_descriptions = {
            'win_tab_open': 'Abrir Win+Tab',
            'win_tab_navigate': 'Navegar Win+Tab',
            'minimize': 'Minimizar ventana',
            'maximize': 'Maximizar ventana',
            'close_window': 'Cerrar ventana',
            'switch_desktop': 'Cambiar escritorio'
        }
        
        # Navigation action counters
        self.action_counts = {
            'win_tab_open': 0,
            'win_tab_navigate': 0,
            'minimize': 0,
            'maximize': 0,
            'close_window': 0,
            'switch_desktop': 0
        }
        
        # Override controller methods to add logging and statistics
        self._override_controller_methods()
        
        print("✅ Controlador de Navegación inicializado")
        if self.controller.gesture_recognizer:
            print("✅ Gesture Recognizer para navegación inicializado")
        else:
            print(f"❌ Modelo no encontrado: {self.controller.model_path}")
    
    def _override_controller_methods(self):
        """Override controller methods to add logging and statistics."""
        # Store original method
        original_perform_navigation_action = self.controller._perform_navigation_action
        
        def enhanced_perform_navigation_action(gesture_name, confidence):
            # Handle special Victory + Thumb gesture
            if gesture_name == 'Victory_Thumb':
                # Victory + Thumb → Navigate Task View
                self.action_counts['win_tab_navigate'] += 1
                self._set_action_message("🔄 Navegar Win+Tab")
                print(f"🔄 Victoria + Pulgar (Confianza: {confidence:.2f}) - Navegar Win+Tab")
                # Call original method
                original_perform_navigation_action(gesture_name, confidence)
                return
            
            # Handle regular gestures
            action = self.controller.gesture_actions[gesture_name]
            gesture_display = self.gesture_names[gesture_name]
            action_description = self.action_descriptions[action]
            
            if action == 'win_tab_open':
                self.action_counts['win_tab_open'] += 1
                self._set_action_message("📋 Abrir Win+Tab")
                print(f"📋 {gesture_display} (Confianza: {confidence:.2f}) - {action_description}")
                
            elif action == 'minimize':
                self.action_counts['minimize'] += 1
                self._set_action_message("⬇️ Minimizar ventana")
                print(f"⬇️ {gesture_display} (Confianza: {confidence:.2f}) - {action_description}")
                
            elif action == 'maximize':
                self.action_counts['maximize'] += 1
                self._set_action_message("⬆️ Maximizar ventana")
                print(f"⬆️ {gesture_display} (Confianza: {confidence:.2f}) - {action_description}")
                
            elif action == 'close_window':
                self.action_counts['close_window'] += 1
                self._set_action_message("❌ Cerrar ventana")
                print(f"❌ {gesture_display} (Confianza: {confidence:.2f}) - {action_description}")
                
            elif action == 'switch_desktop':
                self.action_counts['switch_desktop'] += 1
                self._set_action_message("🖥️ Cambiar escritorio")
                print(f"🖥️ {gesture_display} (Confianza: {confidence:.2f}) - {action_description}")
            
            # Call original method
            original_perform_navigation_action(gesture_name, confidence)
        
        # Replace method
        self.controller._perform_navigation_action = enhanced_perform_navigation_action
    
    def _set_action_message(self, message):
        """Set the action message to display on screen."""
        self.action_message = message
        self.action_message_time = time.time()
    
    def draw_navigation_info(self, image):
        """Draw navigation control information on the image."""
        try:
            height, width, _ = image.shape
            
            # Draw background rectangle for text
            cv2.rectangle(image, (10, 10), (width - 10, 280), (0, 0, 0), -1)
            cv2.rectangle(image, (10, 10), (width - 10, 280), (255, 255, 255), 2)
            
            # Draw title
            cv2.putText(image, "Control de Navegacion por Gestos", 
                       (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Draw gesture instructions
            y_pos = 65
            instructions = [
                "✌️ Victoria (V): Abrir Win+Tab",
                "✌️👍 Victoria + Pulgar: Navegar Win+Tab",
                "🤟 Te amo: Minimizar ventana",
                "✊ Puño cerrado: Maximizar ventana",
                "☝️ Señalar arriba: Cerrar ventana",
                "👍 Pulgar arriba: Cambiar escritorio"
            ]
            
            for instruction in instructions:
                cv2.putText(image, instruction, (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                y_pos += 25
            
            # Draw current gesture
            if self.controller.last_gesture:
                if self.controller.last_gesture == 'Victory_Thumb':
                    gesture_display = "Victoria + Pulgar"
                    action_desc = "Navegar Win+Tab"
                else:
                    gesture_display = self.gesture_names.get(self.controller.last_gesture, self.controller.last_gesture)
                    action = self.controller.gesture_actions.get(self.controller.last_gesture, "Desconocida")
                    action_desc = self.action_descriptions.get(action, "Desconocida")
                cv2.putText(image, f"Gesto: {gesture_display} -> {action_desc}", 
                           (20, y_pos + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            
            # Draw delay status
            current_time = time.time()
            y_delay_pos = y_pos + 60
            
            # Action delay
            action_remaining = max(0, self.controller.action_delay - (current_time - self.controller.last_action_time))
            if action_remaining > 0:
                cv2.putText(image, f"Accion disponible en: {action_remaining:.1f}s", 
                           (20, y_delay_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 100, 100), 1)
                y_delay_pos += 20
            
            # Draw hands detected count
            hands_count = len(self.controller.current_result.hand_landmarks) if self.controller.current_result and self.controller.current_result.hand_landmarks else 0
            cv2.putText(image, f"Manos detectadas: {hands_count}", 
                       (20, y_delay_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Draw action message
            if self.action_message and time.time() - self.action_message_time < self.action_message_duration:
                cv2.putText(image, self.action_message, 
                           (20, y_delay_pos + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # Draw exit instruction
            cv2.putText(image, "Presiona ESC para salir", 
                       (20, y_delay_pos + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
                       
        except Exception as e:
            print(f"⚠️ Error al dibujar información: {e}")
    
    def draw_statistics(self, image):
        """Display navigation statistics on the right side."""
        try:
            height, width, _ = image.shape
            
            # Draw background for statistics
            stats_x = width - 280
            cv2.rectangle(image, (stats_x, 10), (width - 10, 200), (0, 0, 0), -1)
            cv2.rectangle(image, (stats_x, 10), (width - 10, 200), (255, 255, 255), 2)
            
            # Draw statistics title
            cv2.putText(image, "Estadisticas", 
                       (stats_x + 10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            y_pos = 60
            for action, count in self.action_counts.items():
                if action in self.action_descriptions:
                    action_name = self.action_descriptions[action]
                else:
                    action_name = action.replace('_', ' ').title()
                cv2.putText(image, f"{action_name}: {count}", 
                           (stats_x + 10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                y_pos += 20
            
            # Total actions
            total_actions = sum(self.action_counts.values())
            cv2.putText(image, f"Total: {total_actions}", 
                       (stats_x + 10, y_pos + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
            
        except Exception as e:
            print(f"⚠️ Error al dibujar estadísticas: {e}")
    
    def print_statistics(self):
        """Print navigation control statistics."""
        print("\n" + "="*50)
        print("📊 ESTADÍSTICAS DE CONTROL DE NAVEGACIÓN")
        print("="*50)
        
        total_actions = sum(self.action_counts.values())
        
        for action, count in self.action_counts.items():
            action_name = self.action_descriptions[action]
            percentage = (count / total_actions * 100) if total_actions > 0 else 0
            print(f"{action_name:<25} | {count:>3} veces ({percentage:>5.1f}%)")
        
        print("-"*50)
        print(f"{'Total de acciones':<25} | {total_actions:>3}")
        print("="*50 + "\n")
    
    def run(self):
        """Run the enhanced navigation control loop."""
        if not self.controller.gesture_recognizer:
            print("❌ Error: Gesture Recognizer no está inicializado")
            return
            
        if not self.controller.start_camera():
            print("❌ Error: No se pudo iniciar la cámara")
            return
        
        print("\n🧭 Iniciando control de navegación por gestos...")
        print("Gestos disponibles:")
        print("  ✌️ Victoria (V) → Abrir Win+Tab")
        print("  ✌️👍 Victoria + Pulgar → Navegar Win+Tab")
        print("  🤟 Te amo → Minimizar ventana")
        print("  ✊ Puño cerrado → Maximizar ventana")
        print("  ☝️ Señalar arriba → Cerrar ventana")
        print("  👍 Pulgar arriba → Cambiar escritorio")
        print("\n🎮 Controla tu navegación con gestos naturales")
        print("   Presiona ESC para salir\n")
        
        try:
            frame_timestamp = 0
            frame_count = 0
            
            while True:
                image = self.controller.process_frame()
                if image is None:
                    break
                
                frame_count += 1
                
                # Process every 2nd frame for better performance
                if frame_count % 2 == 0:
                    # Convert BGR to RGB for MediaPipe
                    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
                    
                    # Process the frame with gesture recognizer
                    if self.controller.gesture_recognizer:
                        frame_timestamp += 66
                        try:
                            self.controller.gesture_recognizer.recognize_async(mp_image, frame_timestamp)
                        except Exception as e:
                            print(f"⚠️ Error en reconocimiento: {e}")
                
                # Draw navigation control information
                self.draw_navigation_info(image)
                
                # Draw statistics
                self.draw_statistics(image)
                
                # Draw hand landmarks
                self.controller.draw_hand_landmarks(image)
                
                # Display the image
                cv2.imshow('Control de Navegacion por Gestos', image)
                
                # Exit on ESC key
                if cv2.waitKey(1) & 0xFF == 27:
                    break
                    
        except KeyboardInterrupt:
            print("\n⚠️ Interrupción por teclado detectada")
        except Exception as e:
            print(f"❌ Error durante la ejecución: {e}")
        finally:
            self.controller.stop_camera()
            self.print_statistics()
            print("👋 Control de navegación finalizado")

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
    
    # Crear y ejecutar el controlador de prueba
    try:
        print("\n🧭 Inicializando controlador de navegación...")
        test_controller = NavigationControllerTest()
        test_controller.run()
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