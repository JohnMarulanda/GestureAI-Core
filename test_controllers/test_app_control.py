#!/usr/bin/env python3
"""
Script de prueba para el Control de Aplicaciones por Gestos
Utiliza MediaPipe Gesture Recognizer para abrir y cerrar aplicaciones.

Gestos soportados:
1. Puño cerrado (Closed_Fist) → Chrome (abrir/cerrar)
2. Dedo índice arriba (Pointing_Up) → Notepad (abrir/cerrar)
3. Victoria (Victory) → Calculator (abrir/cerrar)
4. Te amo (ILoveYou) → Spotify (abrir/cerrar)

Controles:
- ESC: Salir del programa
"""

import sys
import os
import cv2
import time

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.controllers.app_controller import AppController

class AppControllerTest:
    """Test wrapper for AppController with enhanced UI and statistics."""
    
    def __init__(self):
        """Initialize the test wrapper."""
        self.controller = AppController()
        
        # Spanish translations for display
        self.gesture_names = {
            'Closed_Fist': 'Puño cerrado',
            'Pointing_Up': 'Dedo índice arriba',
            'Victory': 'Victoria (V)',
            'ILoveYou': 'Te amo (I Love You)'
        }
        
        # Application action counters
        self.action_counts = {
            'Chrome': {'opened': 0, 'closed': 0},
            'Notepad': {'opened': 0, 'closed': 0},
            'Calculator': {'opened': 0, 'closed': 0},
            'Spotify': {'opened': 0, 'closed': 0}
        }
        
        # Action status for display
        self.action_message = ""
        self.action_message_time = 0
        self.action_message_duration = 3.0
        
        # Override controller methods to add logging and statistics
        self._override_controller_methods()
        
        if self.controller.gesture_recognizer:
            print("✅ Controlador de Aplicaciones inicializado")
        else:
            print(f"❌ Modelo no encontrado: {self.controller.model_path}")
    
    def _override_controller_methods(self):
        """Override controller methods to add logging and statistics."""
        # Store original methods
        original_open = self.controller._open_application
        original_close = self.controller._close_application
        original_callback = self.controller._gesture_result_callback
        
        def enhanced_open_application(app_name, gesture_name, confidence):
            result = original_open(app_name, gesture_name, confidence)
            if result:
                # Update counters
                self.action_counts[app_name]['opened'] += 1
                
                gesture_display = self.gesture_names[gesture_name]
                self._set_action_message(f"✅ Abriendo {app_name}")
                print(f"🚀 {gesture_display} (Confianza: {confidence:.2f}) - Abriendo {app_name}")
            else:
                if not self.controller._is_app_running(app_name):
                    self._set_action_message(f"❌ Error abriendo {app_name}")
                    print(f"❌ Error abriendo {app_name}")
                else:
                    self._set_action_message(f"ℹ️ {app_name} ya está ejecutándose")
            return result
        
        def enhanced_close_application(app_name, gesture_name, confidence):
            result = original_close(app_name, gesture_name, confidence)
            if result:
                # Update counters
                self.action_counts[app_name]['closed'] += 1
                
                gesture_display = self.gesture_names[gesture_name]
                self._set_action_message(f"🔴 Cerrando {app_name}")
                print(f"🔴 {gesture_display} (Confianza: {confidence:.2f}) - Cerrando {app_name}")
            else:
                self._set_action_message(f"ℹ️ {app_name} no está ejecutándose")
            return result
        
        def enhanced_gesture_result_callback(result, output_image, timestamp_ms):
            # Call original callback first
            original_callback(result, output_image, timestamp_ms)
            
            # Add enhanced error handling
            try:
                if result.gestures:
                    for hand_gesture in result.gestures:
                        if hand_gesture:
                            gesture = hand_gesture[0]
                            gesture_name = gesture.category_name
                            confidence = gesture.score
                            
                            # Log gesture detection for debugging
                            if (gesture_name in self.controller.gesture_apps and 
                                confidence >= self.controller.confidence_threshold):
                                current_time = time.time()
                                if current_time - self.controller.last_action_time > self.controller.action_delay:
                                    app_name = self.controller.gesture_apps[gesture_name]
                                    is_running = self.controller._is_app_running(app_name)
                                    action = "cerrar" if is_running else "abrir"
                                    print(f"🎯 Gesto válido detectado: {gesture_name} -> {action} {app_name}")
            except Exception as e:
                print(f"⚠️ Error en callback de gestos: {e}")
        
        # Replace methods
        self.controller._open_application = enhanced_open_application
        self.controller._close_application = enhanced_close_application
        self.controller._gesture_result_callback = enhanced_gesture_result_callback
    
    def _set_action_message(self, message):
        """Set the action message to display on screen."""
        self.action_message = message
        self.action_message_time = time.time()
    
    def draw_app_info(self, image):
        """Draw application control information on the image."""
        try:
            height, width, _ = image.shape
            
            # Draw background rectangle for text
            cv2.rectangle(image, (10, 10), (width - 10, 280), (0, 0, 0), -1)
            cv2.rectangle(image, (10, 10), (width - 10, 280), (255, 255, 255), 2)
            
            # Draw title
            cv2.putText(image, "Control de Aplicaciones por Gestos", 
                       (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Draw gesture instructions
            y_pos = 65
            instructions = [
                "✊ Puño cerrado: Chrome (abrir/cerrar)",
                "☝️ Dedo índice arriba: Notepad (abrir/cerrar)",
                "✌️ Victoria (V): Calculator (abrir/cerrar)",
                "🤟 Te amo: Spotify (abrir/cerrar)"
            ]
            
            for instruction in instructions:
                cv2.putText(image, instruction, (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                y_pos += 25
            
            # Draw current gesture
            if self.controller.last_gesture:
                gesture_display = self.gesture_names.get(self.controller.last_gesture, self.controller.last_gesture)
                app_name = self.controller.gesture_apps.get(self.controller.last_gesture, "Desconocida")
                cv2.putText(image, f"Gesto: {gesture_display} -> {app_name}", 
                           (20, y_pos + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            
            # Draw delay status
            current_time = time.time()
            y_delay_pos = y_pos + 50
            
            # General action delay
            action_remaining = max(0, self.controller.action_delay - (current_time - self.controller.last_action_time))
            if action_remaining > 0:
                cv2.putText(image, f"Accion disponible en: {action_remaining:.1f}s", 
                           (20, y_delay_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 100, 100), 1)
                y_delay_pos += 20
            
            # Close delays for each app
            for app_name in self.controller.gesture_apps.values():
                if app_name in self.controller.last_close_time:
                    close_remaining = max(0, self.controller.close_delay - (current_time - self.controller.last_close_time[app_name]))
                    if close_remaining > 0:
                        cv2.putText(image, f"Cerrar {app_name} en: {close_remaining:.1f}s", 
                                   (20, y_delay_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 100, 100), 1)
                        y_delay_pos += 20
                
                # Show open delay (prevents immediate closing after opening)
                if app_name in self.controller.last_open_time:
                    open_remaining = max(0, self.controller.open_delay - (current_time - self.controller.last_open_time[app_name]))
                    if open_remaining > 0:
                        cv2.putText(image, f"Protección {app_name}: {open_remaining:.1f}s", 
                                   (20, y_delay_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 255, 100), 1)
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
    
    def draw_app_status(self, image):
        """Display application status on the right side."""
        try:
            height, width, _ = image.shape
            
            # Draw background for status
            status_x = width - 250
            cv2.rectangle(image, (status_x, 10), (width - 10, 200), (0, 0, 0), -1)
            cv2.rectangle(image, (status_x, 10), (width - 10, 200), (255, 255, 255), 2)
            
            # Draw status title
            cv2.putText(image, "Estado de Apps", 
                       (status_x + 10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            y_pos = 60
            for app_name in self.controller.gesture_apps.values():
                is_running = self.controller._is_app_running(app_name)
                status_text = "ACTIVA" if is_running else "CERRADA"
                status_color = (0, 255, 0) if is_running else (0, 0, 255)
                
                cv2.putText(image, f"{app_name}: {status_text}", 
                           (status_x + 10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, status_color, 1)
                y_pos += 25
            
        except Exception as e:
            print(f"⚠️ Error al dibujar estado de apps: {e}")
    
    def print_statistics(self):
        """Print application control statistics."""
        print("\n" + "="*50)
        print("📊 ESTADÍSTICAS DE CONTROL DE APLICACIONES")
        print("="*50)
        
        total_opened = sum(app['opened'] for app in self.action_counts.values())
        total_closed = sum(app['closed'] for app in self.action_counts.values())
        
        for app_name, counts in self.action_counts.items():
            print(f"{app_name:<12} | Abierta: {counts['opened']:>2} | Cerrada: {counts['closed']:>2}")
        
        print("-"*50)
        print(f"{'Total abierto':<12} | {total_opened:>2}")
        print(f"{'Total cerrado':<12} | {total_closed:>2}")
        print(f"{'Apps rastreadas':<12} | {len(self.controller.running_apps):>2}")
        print("="*50 + "\n")
    
    def run(self):
        """Run the enhanced application control loop."""
        if not self.controller.gesture_recognizer:
            print("❌ Error: Gesture Recognizer no está inicializado")
            return
            
        if not self.controller.start_camera():
            print("❌ Error: No se pudo iniciar la cámara")
            return
        
        print("\n🚀 Iniciando control de aplicaciones por gestos...")
        print("Gestos disponibles:")
        print("  ✊ Puño cerrado → Chrome (abrir/cerrar)")
        print("  ☝️ Dedo índice arriba → Notepad (abrir/cerrar)")
        print("  ✌️ Victoria (V) → Calculator (abrir/cerrar)")
        print("  🤟 Te amo → Spotify (abrir/cerrar)")
        print("\n🎮 Controla tus aplicaciones con gestos naturales")
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
                        frame_timestamp += 66  # Approximately 15 FPS for gesture processing
                        try:
                            self.controller.gesture_recognizer.recognize_async(mp_image, frame_timestamp)
                        except Exception as e:
                            print(f"⚠️ Error en reconocimiento: {e}")
                
                # Draw application control information
                self.draw_app_info(image)
                
                # Draw application status
                self.draw_app_status(image)
                
                # Draw hand landmarks
                self.controller.draw_hand_landmarks(image)
                
                # Display the image
                cv2.imshow('Control de Aplicaciones por Gestos', image)
                
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
            print("👋 Control de aplicaciones finalizado")

def main():
    """Función principal para ejecutar la prueba de control de aplicaciones."""
    print("="*60)
    print("🚀 PRUEBA DE CONTROL DE APLICACIONES POR GESTOS")
    print("="*60)
    print("🎯 OBJETIVO:")
    print("   Probar el control automático de aplicaciones usando")
    print("   4 gestos predefinidos con detección inteligente.")
    print()
    print("🖐️ GESTOS DE CONTROL:")
    print("   ✊ Puño cerrado       → Chrome (abrir/cerrar)")
    print("   ☝️ Dedo índice arriba → Notepad (abrir/cerrar)")
    print("   ✌️ Victoria (V)       → Calculator (abrir/cerrar)")
    print("   🤟 Te amo             → Spotify (abrir/cerrar)")
    print()
    print("🎮 FUNCIONAMIENTO INTELIGENTE:")
    print("   - Mismo gesto para abrir y cerrar cada aplicación")
    print("   - Detección automática del estado de la aplicación")
    print("   - Si la app está cerrada → la abre")
    print("   - Si la app está abierta → la cierra")
    print("   - Delays de seguridad para evitar cierres accidentales")
    print("   - Rastreo de procesos en tiempo real")
    print()
    print("📊 CARACTERÍSTICAS:")
    print("   - Control en tiempo real con alta precisión")
    print("   - Umbral de confianza: 75%")
    print("   - Delay general: 2.0 segundos")
    print("   - Delay cerrar: 5.0 segundos (seguridad)")
    print("   - Delay protección: 3.0 segundos (después de abrir)")
    print("   - Soporte para 1 mano optimizado")
    print("   - Detección automática de rutas de aplicaciones")
    print("   - Estadísticas de acciones ejecutadas")
    print("   - Interfaz visual con estado de aplicaciones")
    print("   - Landmarks de mano dibujados")
    print("   - Indicadores de tiempo de espera")
    print("   - Protección contra cierres accidentales")
    print()
    print("🔧 CONFIGURACIÓN:")
    print("   - Gestos: Closed_Fist, Pointing_Up, Victory, ILoveYou")
    print("   - Delays específicos por tipo de acción")
    print("   - Threading para acciones no bloqueantes")
    print("   - Manejo robusto de errores")
    print("   - Búsqueda automática de rutas de aplicaciones")
    print("   - Sistema de protección multicapa")
    print()
    print("⌨️  CONTROLES:")
    print("   ESC      : Salir del programa")
    print()
    print("🚀 APLICACIONES CONTROLADAS:")
    print("   🌐 CHROME: Navegador web principal")
    print("   📝 NOTEPAD: Editor de texto básico")
    print("   🧮 CALCULATOR: Calculadora del sistema")
    print("   🎵 SPOTIFY: Reproductor de música")
    print()
    print("🔍 REQUISITOS:")
    print("   - Cámara web funcional")
    print("   - Modelo gesture_recognizer.task en models/")
    print("   - psutil instalado para manejo de procesos")
    print("   - Aplicaciones instaladas en el sistema")
    print("   - Permisos para abrir/cerrar aplicaciones")
    print()
    print("💡 RECOMENDACIONES:")
    print("   - Cierra aplicaciones importantes antes de probar")
    print("   - Mantén buena iluminación para detección")
    print("   - Usa gestos claros y definidos")
    print("   - 'Dedo índice arriba' es más confiable que palma abierta")
    print("   - El gesto 'Te amo' es meñique + índice + pulgar extendidos")
    print("   - Espera los delays de seguridad para cerrar aplicaciones")
    print("   - Las apps recién abiertas tienen protección de 3 segundos")
    print()
    print("🎯 CASOS DE USO:")
    print("   - Apertura rápida de aplicaciones frecuentes")
    print("   - Control sin tocar teclado o mouse")
    print("   - Demostraciones y presentaciones")
    print("   - Accesibilidad para usuarios con limitaciones")
    print("   - Automatización de flujos de trabajo")
    print()
    print("⚠️  ADVERTENCIAS:")
    print("   - Las aplicaciones se cerrarán realmente")
    print("   - Guarda tu trabajo antes de probar")
    print("   - Delay de 5 segundos para cerrar por seguridad")
    print("   - Protección de 3 segundos después de abrir")
    print("   - Chrome puede tener múltiples procesos")
    print("   - Spotify puede requerir instalación específica")
    print("   - Los delays son más largos para mayor seguridad")
    print()
    
    try:
        input("Presiona ENTER para comenzar la prueba...")
    except KeyboardInterrupt:
        print("\n❌ Operación cancelada por el usuario")
        return
    
    # Crear y ejecutar el controlador
    try:
        print("\n🚀 Inicializando controlador de aplicaciones...")
        test_controller = AppControllerTest()
        test_controller.run()
    except Exception as e:
        print(f"❌ Error al ejecutar el controlador: {e}")
        print("   Verifica que:")
        print("   1. La cámara esté disponible")
        print("   2. El modelo gesture_recognizer.task exista en models/")
        print("   3. Las dependencias estén instaladas correctamente:")
        print("      pip install mediapipe opencv-python psutil")
        print("   4. Las aplicaciones estén instaladas:")
        print("      - Chrome: Navegador web")
        print("      - Notepad: Incluido en Windows")
        print("      - Calculator: Incluido en Windows")
        print("      - Spotify: Descargable desde spotify.com")
        print("   5. Tengas permisos para ejecutar aplicaciones")
    
    print("\n👋 ¡Gracias por probar el control de aplicaciones por gestos!")
    print("   Recuerda: Los gestos naturales hacen la experiencia más fluida")

if __name__ == "__main__":
    main() 