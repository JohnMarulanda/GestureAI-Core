#!/usr/bin/env python3
"""
Script de prueba para el Control de Atajos de Teclado por Gestos
Utiliza MediaPipe Gesture Recognizer para ejecutar atajos de teclado comunes.

Gestos soportados:
1. Victoria (Victory) → Copiar (Ctrl+C)
2. Palma abierta (Open_Palm) → Pegar (Ctrl+V)
3. Puño cerrado (Closed_Fist) → Escape (ESC)
4. Señalar arriba (Pointing_Up) → Actualizar (F5)
5. Pulgar arriba (Thumb_Up) → Deshacer (Ctrl+Z)
6. Pulgar abajo (Thumb_Down) → Rehacer (Ctrl+Y)
7. Te amo (ILoveYou) → Guardar (Ctrl+S)

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

from core.controllers.shortcuts_controller import ShortcutsController

class ShortcutsControllerTest:
    """Test wrapper for ShortcutsController with enhanced UI and statistics."""
    
    def __init__(self):
        """Initialize the test wrapper."""
        self.controller = ShortcutsController()
        
        # Action status
        self.action_message = ""
        self.action_message_time = 0
        self.action_message_duration = 2.5
        
        # Spanish translations for display
        self.gesture_names = {
            'Victory': 'Victoria (V)',
            'Open_Palm': 'Palma abierta',
            'Closed_Fist': 'Puño cerrado',
            'Pointing_Up': 'Señalando hacia arriba',
            'Thumb_Up': 'Pulgar hacia arriba',
            'Thumb_Down': 'Pulgar hacia abajo',
            'ILoveYou': 'Te amo (I Love You)'
        }
        
        # Action descriptions in Spanish
        self.action_descriptions = {
            'copy': 'Copiar (Ctrl+C)',
            'paste': 'Pegar (Ctrl+V)',
            'escape': 'Escape (ESC)',
            'refresh': 'Actualizar (F5)',
            'undo': 'Deshacer (Ctrl+Z)',
            'redo': 'Rehacer (Ctrl+Y)',
            'save': 'Guardar (Ctrl+S)'
        }
        
        # Shortcut action counters
        self.action_counts = {
            'copy': 0,
            'paste': 0,
            'escape': 0,
            'refresh': 0,
            'undo': 0,
            'redo': 0,
            'save': 0
        }
        
        # Override controller methods to add logging and statistics
        self._override_controller_methods()
        
        print("✅ Controlador de Atajos de Teclado inicializado")
        if self.controller.gesture_recognizer:
            print("✅ Gesture Recognizer para atajos inicializado")
        else:
            print(f"❌ Modelo no encontrado: {self.controller.model_path}")
    
    def _override_controller_methods(self):
        """Override controller methods to add logging and statistics."""
        # Store original method
        original_perform_shortcut_action = self.controller._perform_shortcut_action
        
        def enhanced_perform_shortcut_action(gesture_name, confidence):
            action = self.controller.gesture_actions[gesture_name]
            gesture_display = self.gesture_names[gesture_name]
            action_description = self.action_descriptions[action]
            keys = self.controller.shortcuts[action]
            
            # Update counter and display message
            self.action_counts[action] += 1
            shortcut_display = "+".join(keys).upper()
            self._set_action_message(f"⌨️ {shortcut_display}")
            print(f"⌨️ {gesture_display} (Confianza: {confidence:.2f}) - {action_description}")
            
            # Call original method
            original_perform_shortcut_action(gesture_name, confidence)
        
        # Replace method
        self.controller._perform_shortcut_action = enhanced_perform_shortcut_action
    
    def _set_action_message(self, message):
        """Set the action message to display on screen."""
        self.action_message = message
        self.action_message_time = time.time()
    
    def draw_shortcuts_info(self, image):
        """Draw shortcuts control information on the image."""
        try:
            height, width, _ = image.shape
            
            # Draw background rectangle for text
            cv2.rectangle(image, (10, 10), (width - 10, 320), (0, 0, 0), -1)
            cv2.rectangle(image, (10, 10), (width - 10, 320), (255, 255, 255), 2)
            
            # Draw title
            cv2.putText(image, "Atajos de Teclado por Gestos", 
                       (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Draw gesture instructions
            y_pos = 65
            instructions = [
                "✌️ Victoria (V): Copiar (Ctrl+C)",
                "✋ Palma abierta: Pegar (Ctrl+V)",
                "✊ Puño cerrado: Escape (ESC)",
                "☝️ Señalar arriba: Actualizar (F5)",
                "👍 Pulgar arriba: Deshacer (Ctrl+Z)",
                "👎 Pulgar abajo: Rehacer (Ctrl+Y)",
                "🤟 Te amo: Guardar (Ctrl+S)"
            ]
            
            for instruction in instructions:
                cv2.putText(image, instruction, (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                y_pos += 25
            
            # Draw current gesture
            if self.controller.last_gesture:
                gesture_display = self.gesture_names[self.controller.last_gesture]
                action = self.controller.gesture_actions[self.controller.last_gesture]
                action_desc = self.action_descriptions[action]
                cv2.putText(image, f"Gesto: {gesture_display} -> {action_desc}", 
                           (20, y_pos + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            
            # Draw delay status
            current_time = time.time()
            y_delay_pos = y_pos + 60
            
            # Action delay
            action_remaining = max(0, self.controller.action_delay - (current_time - self.controller.last_action_time))
            if action_remaining > 0:
                cv2.putText(image, f"Siguiente atajo en: {action_remaining:.1f}s", 
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
        """Display shortcuts statistics on the right side."""
        try:
            height, width, _ = image.shape
            
            # Draw background for statistics
            stats_x = width - 280
            cv2.rectangle(image, (stats_x, 10), (width - 10, 250), (0, 0, 0), -1)
            cv2.rectangle(image, (stats_x, 10), (width - 10, 250), (255, 255, 255), 2)
            
            # Draw statistics title
            cv2.putText(image, "Estadisticas", 
                       (stats_x + 10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            y_pos = 60
            for action, count in self.action_counts.items():
                action_name = self.action_descriptions[action].split(' (')[0]  # Remove shortcut part
                cv2.putText(image, f"{action_name}: {count}", 
                           (stats_x + 10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                y_pos += 22
            
            # Total actions
            total_actions = sum(self.action_counts.values())
            cv2.putText(image, f"Total: {total_actions}", 
                       (stats_x + 10, y_pos + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
            
        except Exception as e:
            print(f"⚠️ Error al dibujar estadísticas: {e}")
    
    def print_statistics(self):
        """Print shortcuts control statistics."""
        print("\n" + "="*50)
        print("📊 ESTADÍSTICAS DE ATAJOS DE TECLADO")
        print("="*50)
        
        total_actions = sum(self.action_counts.values())
        
        for action, count in self.action_counts.items():
            action_name = self.action_descriptions[action]
            percentage = (count / total_actions * 100) if total_actions > 0 else 0
            print(f"{action_name:<25} | {count:>3} veces ({percentage:>5.1f}%)")
        
        print("-"*50)
        print(f"{'Total de atajos':<25} | {total_actions:>3}")
        print("="*50 + "\n")
    
    def run(self):
        """Run the enhanced shortcuts control loop."""
        if not self.controller.gesture_recognizer:
            print("❌ Error: Gesture Recognizer no está inicializado")
            return
            
        if not self.controller.start_camera():
            print("❌ Error: No se pudo iniciar la cámara")
            return
        
        print("\n⌨️ Iniciando control de atajos de teclado por gestos...")
        print("Gestos disponibles:")
        print("  ✌️ Victoria (V) → Copiar (Ctrl+C)")
        print("  ✋ Palma abierta → Pegar (Ctrl+V)")
        print("  ✊ Puño cerrado → Escape (ESC)")
        print("  ☝️ Señalar arriba → Actualizar (F5)")
        print("  👍 Pulgar arriba → Deshacer (Ctrl+Z)")
        print("  👎 Pulgar abajo → Rehacer (Ctrl+Y)")
        print("  🤟 Te amo → Guardar (Ctrl+S)")
        print("\n⌨️ Ejecuta atajos de teclado con gestos naturales")
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
                
                # Draw shortcuts control information
                self.draw_shortcuts_info(image)
                
                # Draw statistics
                self.draw_statistics(image)
                
                # Draw hand landmarks
                self.controller.draw_hand_landmarks(image)
                
                # Display the image
                cv2.imshow('Atajos de Teclado por Gestos', image)
                
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
            print("👋 Control de atajos de teclado finalizado")

def main():
    """Función principal para ejecutar la prueba de control de atajos de teclado."""
    print("="*60)
    print("⌨️ PRUEBA DE ATAJOS DE TECLADO POR GESTOS")
    print("="*60)
    print("🎯 OBJETIVO:")
    print("   Probar la ejecución de atajos de teclado comunes usando")
    print("   7 gestos predefinidos para mayor productividad.")
    print()
    print("🖐️ GESTOS DE CONTROL:")
    print("   ✌️ Victoria (V)          → Copiar (Ctrl+C)")
    print("   ✋ Palma abierta         → Pegar (Ctrl+V)")
    print("   ✊ Puño cerrado          → Escape (ESC)")
    print("   ☝️ Señalar arriba        → Actualizar (F5)")
    print("   👍 Pulgar arriba         → Deshacer (Ctrl+Z)")
    print("   👎 Pulgar abajo          → Rehacer (Ctrl+Y)")
    print("   🤟 Te amo                → Guardar (Ctrl+S)")
    print()
    print("⌨️ FUNCIONES DE ATAJOS:")
    print("   - Copiar: Copia texto o elementos seleccionados")
    print("   - Pegar: Pega contenido del portapapeles")
    print("   - Escape: Cancela operación actual o cierra diálogos")
    print("   - Actualizar: Refresca página web o aplicación")
    print("   - Deshacer: Revierte la última acción realizada")
    print("   - Rehacer: Repite la última acción deshecha")
    print("   - Guardar: Guarda el documento o archivo actual")
    print()
    print("📊 CARACTERÍSTICAS:")
    print("   - Ejecución instantánea de atajos con alta precisión")
    print("   - Umbral de confianza: 70%")
    print("   - Delay entre atajos: 0.8 segundos")
    print("   - Soporte para 1 mano optimizado")
    print("   - Gestos universalmente reconocidos")
    print("   - Estadísticas de uso en tiempo real")
    print("   - Interfaz visual con información detallada")
    print("   - Landmarks de mano dibujados")
    print("   - Indicadores de tiempo de espera")
    print("   - Mensajes de confirmación visual")
    print("   - Threading para ejecución no bloqueante")
    print()
    print("🔧 CONFIGURACIÓN:")
    print("   - Gestos: Victory, Open_Palm, Closed_Fist, Pointing_Up, Thumb_Up, Thumb_Down, ILoveYou")
    print("   - Detección automática sin configuración manual")
    print("   - Delay específico para evitar ejecuciones múltiples")
    print("   - Integración completa con sistema operativo")
    print("   - Manejo robusto de errores")
    print("   - Atajos universales multiplataforma")
    print()
    print("⌨️  CONTROLES:")
    print("   ESC      : Salir del programa")
    print()
    print("🎯 ATAJOS DE TECLADO:")
    print("   📄 COPIAR (Ctrl+C): Copia texto o elementos seleccionados")
    print("   📋 PEGAR (Ctrl+V): Pega contenido del portapapeles")
    print("   ❌ ESCAPE (ESC): Cancela operación o cierra diálogos")
    print("   🔄 ACTUALIZAR (F5): Refresca página web o aplicación")
    print("   ↶ DESHACER (Ctrl+Z): Revierte la última acción")
    print("   ↷ REHACER (Ctrl+Y): Repite acción deshecha")
    print("   💾 GUARDAR (Ctrl+S): Guarda documento actual")
    print()
    print("🔍 REQUISITOS:")
    print("   - Cámara web funcional")
    print("   - Modelo gesture_recognizer.task en models/")
    print("   - pyautogui instalado para ejecución de atajos")
    print("   - Editor de texto o aplicación para probar atajos")
    print("   - Algunos archivos de texto para probar")
    print()
    print("💡 RECOMENDACIONES DE PRUEBA:")
    print("   1. Abre un editor de texto (Notepad, Word, VS Code)")
    print("   2. Escribe algo de texto para probar Copiar/Pegar")
    print("   3. Selecciona texto y usa Victoria (V) para copiar")
    print("   4. Cambia posición del cursor y usa Palma abierta para pegar")
    print("   5. Usa Pulgar arriba para deshacer cambios")
    print("   6. Usa Pulgar abajo para rehacer")
    print("   7. Usa Te amo para guardar documento")
    print("   8. Abre un navegador web y usa Señalar arriba para actualizar")
    print("   9. Usa Puño cerrado para cerrar diálogos")
    print()
    print("🎯 CASOS DE USO:")
    print("   - Edición de documentos sin teclado")
    print("   - Presentaciones interactivas")
    print("   - Control remoto de aplicaciones")
    print("   - Accesibilidad para usuarios con limitaciones")
    print("   - Flujos de trabajo eficientes")
    print("   - Automatización de tareas repetitivas")
    print("   - Control de aplicaciones a distancia")
    print()
    print("⚠️  ADVERTENCIAS:")
    print("   - Los atajos se ejecutarán en la aplicación activa")
    print("   - Asegúrate de tener contenido para copiar/pegar")
    print("   - Ctrl+S guardará en la aplicación actual")
    print("   - Delay de 0.8 segundos entre atajos")
    print("   - F5 actualizará la página/aplicación activa")
    print("   - ESC puede cerrar diálogos o cancelar operaciones")
    print("   - Prueba en aplicaciones seguras primero")
    print()
    print("🔧 ATAJOS IMPLEMENTADOS:")
    print("   - Ctrl+C: Atajo universal para copiar")
    print("   - Ctrl+V: Atajo universal para pegar")
    print("   - ESC: Tecla de escape universal")
    print("   - F5: Atajo universal para actualizar")
    print("   - Ctrl+Z: Atajo universal para deshacer")
    print("   - Ctrl+Y: Atajo universal para rehacer")
    print("   - Ctrl+S: Atajo universal para guardar")
    print()
    print("📱 APLICACIONES SUGERIDAS PARA PRUEBA:")
    print("   - Notepad/TextEdit: Para probar copiar/pegar/guardar")
    print("   - Navegador web: Para probar actualizar")
    print("   - Word/LibreOffice: Para probar edición avanzada")
    print("   - Visual Studio Code: Para programación")
    print("   - Paint/GIMP: Para edición de imágenes")
    print("   - Excel/Calc: Para hojas de cálculo")
    print()
    print("🎨 GESTIÓN DE GESTOS:")
    print("   - Victoria: Dedos índice y medio extendidos en V")
    print("   - Palma abierta: Todos los dedos extendidos")
    print("   - Puño cerrado: Todos los dedos cerrados")
    print("   - Señalar arriba: Solo dedo índice extendido hacia arriba")
    print("   - Pulgar arriba: Solo pulgar extendido hacia arriba")
    print("   - Pulgar abajo: Solo pulgar extendido hacia abajo")
    print("   - Te amo: Pulgar, índice y meñique extendidos")
    print()
    
    try:
        input("Presiona ENTER para comenzar la prueba...")
    except KeyboardInterrupt:
        print("\n❌ Operación cancelada por el usuario")
        return
    
    # Crear y ejecutar el controlador de prueba
    try:
        print("\n⌨️ Inicializando controlador de atajos de teclado...")
        test_controller = ShortcutsControllerTest()
        test_controller.run()
    except Exception as e:
        print(f"❌ Error al ejecutar el controlador: {e}")
        print("   Verifica que:")
        print("   1. La cámara esté disponible")
        print("   2. El modelo gesture_recognizer.task exista en models/")
        print("   3. Las dependencias estén instaladas correctamente:")
        print("      pip install mediapipe opencv-python pyautogui")
        print("   4. pyautogui esté configurado correctamente")
        print("   5. Tengas permisos para ejecutar atajos de teclado")
        print("   6. La aplicación de destino esté activa")
    
    print("\n👋 ¡Gracias por probar los atajos de teclado por gestos!")
    print("   Recuerda: Los gestos naturales hacen el trabajo más eficiente")

if __name__ == "__main__":
    main() 