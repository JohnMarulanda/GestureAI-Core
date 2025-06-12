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
import cv2
import time
import mediapipe as mp

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.controllers.system_controller import SystemController

class SystemControllerTest:
    """Test wrapper for SystemController with enhanced UI and statistics."""
    
    def __init__(self):
        """Initialize the test wrapper."""
        self.controller = SystemController()
        
        # Action status
        self.action_message = ""
        self.action_message_time = 0
        self.action_message_duration = 3.0
        
        # Spanish translations for display
        self.gesture_names = {
            'Victory': 'Bloquear (Victoria)',
            'Closed_Fist': 'Apagar (Puño)',
            'Open_Palm': 'Suspender (Palma)',
            'Pointing_Up': 'Reiniciar (Señalar)'
        }
        
        # Action descriptions
        self.action_descriptions = {
            'lock': 'Bloquear pantalla',
            'shutdown': 'Apagar sistema',
            'sleep': 'Suspender sistema',
            'restart': 'Reiniciar sistema'
        }
        
        # System action counters
        self.action_counts = {
            'lock': 0,
            'shutdown': 0,
            'sleep': 0,
            'restart': 0
        }
        
        # Override controller methods to add logging and statistics
        self._override_controller_methods()
        
        print("✅ Controlador de Sistema inicializado")
        if self.controller.gesture_recognizer:
            print("✅ Gesture Recognizer para control de sistema inicializado")
            print(f"📊 Umbrales configurados:")
            for gesture, threshold in self.controller.gesture_thresholds.items():
                action = self.controller.gesture_actions[gesture]
                print(f"   {gesture}: {threshold*100:.0f}% → {self.action_descriptions[action]}")
        else:
            print(f"❌ Modelo no encontrado: {self.controller.model_path}")
    
    def _override_controller_methods(self):
        """Override controller methods to add logging and statistics."""
        # Store original methods
        original_start_confirmation = self.controller._start_confirmation
        original_cancel_confirmation = self.controller._cancel_confirmation
        original_perform_system_action = self.controller._perform_system_action
        original_lock_computer = self.controller._lock_computer
        original_shutdown_computer = self.controller._shutdown_computer
        original_sleep_computer = self.controller._sleep_computer
        original_restart_computer = self.controller._restart_computer
        
        def enhanced_start_confirmation(gesture_name, confidence):
            original_start_confirmation(gesture_name, confidence)
            action_name = self.action_descriptions[self.controller.confirmation_action]
            gesture_display = self.gesture_names[gesture_name]
            print(f"⚠️ CONFIRMACIÓN: {action_name}")
            print(f"   Mantén el gesto {gesture_display} para confirmar")
            print(f"   Confianza: {confidence:.2f}")
        
        def enhanced_cancel_confirmation():
            if self.controller.confirmation_active:
                print("❌ Confirmación cancelada")
            original_cancel_confirmation()
        
        def enhanced_perform_system_action(gesture_name, confidence):
            action = self.controller.gesture_actions[gesture_name]
            gesture_display = self.gesture_names[gesture_name]
            action_name = self.action_descriptions[action]
            
            print(f"🔧 Ejecutando: {action_name}")
            print(f"   Gesto: {gesture_display} (Confianza: {confidence:.2f})")
            
            self.action_message = f"Ejecutando: {action_name}"
            self.action_message_time = time.time()
            
            # Update statistics
            self.action_counts[action] += 1
            
            original_perform_system_action(gesture_name, confidence)
        
        def enhanced_lock_computer():
            print("🔒 Bloqueando pantalla...")
            original_lock_computer()
            print("✅ Pantalla bloqueada")
        
        def enhanced_shutdown_computer():
            print("⚡ Apagando sistema en 5 segundos...")
            original_shutdown_computer()
            print("✅ Comando de apagado enviado")
        
        def enhanced_sleep_computer():
            print("😴 Suspendiendo sistema...")
            original_sleep_computer()
            print("✅ Sistema suspendido")
        
        def enhanced_restart_computer():
            print("🔄 Reiniciando sistema...")
            original_restart_computer()
            print("✅ Comando de reinicio enviado")
        
        # Replace methods
        self.controller._start_confirmation = enhanced_start_confirmation
        self.controller._cancel_confirmation = enhanced_cancel_confirmation
        self.controller._perform_system_action = enhanced_perform_system_action
        self.controller._lock_computer = enhanced_lock_computer
        self.controller._shutdown_computer = enhanced_shutdown_computer
        self.controller._sleep_computer = enhanced_sleep_computer
        self.controller._restart_computer = enhanced_restart_computer
    
    def draw_system_info(self, image):
        """Draw system control information on the image."""
        try:
            height, width, _ = image.shape
            
            # Draw background rectangle for text
            cv2.rectangle(image, (10, 10), (width - 10, 280), (0, 0, 0), -1)
            cv2.rectangle(image, (10, 10), (width - 10, 280), (255, 255, 255), 2)
            
            # Draw title
            cv2.putText(image, "Control de Sistema por Gestos", 
                       (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Draw gesture instructions
            y_pos = 65
            instructions = [
                "✌️ Victoria: Bloquear pantalla (3s)",
                "✊ Puño: Apagar sistema (3s)",
                "🖐️ Palma: Suspender sistema (3s)",
                "👆 Señalar: Reiniciar sistema (3s)"
            ]
            
            for instruction in instructions:
                cv2.putText(image, instruction, (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                y_pos += 25
            
            # Draw current gesture and hold progress
            if self.controller.last_gesture and self.controller.last_gesture in self.controller.gesture_hold_time:
                current_time = time.time()
                hold_duration = current_time - self.controller.gesture_hold_time[self.controller.last_gesture]
                progress = min(hold_duration / self.controller.required_hold_duration, 1.0)
                
                gesture_display = self.gesture_names.get(self.controller.last_gesture, self.controller.last_gesture)
                cv2.putText(image, f"Detectando: {gesture_display}", 
                           (20, y_pos + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
                
                # Draw progress bar
                bar_width = 200
                bar_height = 15
                bar_x = 20
                bar_y = y_pos + 35
                
                # Bar outline
                cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (255, 255, 255), 1)
                
                # Bar fill
                filled_width = int(bar_width * progress)
                bar_color = (0, 255, 0) if progress < 1.0 else (0, 255, 255)
                cv2.rectangle(image, (bar_x, bar_y), (bar_x + filled_width, bar_y + bar_height), bar_color, -1)
                
                # Progress text
                cv2.putText(image, f"Progreso: {int(progress * 100)}%", 
                           (bar_x, bar_y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            
            # Draw hands detected count
            hands_count = len(self.controller.current_result.hand_landmarks) if self.controller.current_result and self.controller.current_result.hand_landmarks else 0
            cv2.putText(image, f"Manos detectadas: {hands_count}", 
                       (20, y_pos + 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Draw action message
            if self.action_message and time.time() - self.action_message_time < self.action_message_duration:
                cv2.putText(image, self.action_message, 
                           (20, y_pos + 95), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
            
            # Draw exit instruction
            cv2.putText(image, "Presiona ESC para salir", 
                       (20, y_pos + 120), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
                       
        except Exception as e:
            print(f"⚠️ Error al dibujar información: {e}")
    
    def draw_confirmation_dialog(self, image):
        """Draw confirmation dialog for system actions."""
        try:
            if self.controller.confirmation_active:
                height, width, _ = image.shape
                
                # Create semi-transparent overlay
                overlay = image.copy()
                cv2.rectangle(overlay, (50, 50), (width - 50, height - 50), (0, 0, 0), -1)
                alpha = 0.8
                cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0, image)
                
                # Draw confirmation border
                cv2.rectangle(image, (50, 50), (width - 50, height - 50), (0, 0, 255), 3)
                
                # Display confirmation message
                action_name = self.action_descriptions[self.controller.confirmation_action]
                gesture_display = self.gesture_names[self.controller.confirmation_gesture]
                
                cv2.putText(image, f"CONFIRMAR: {action_name.upper()}", 
                           (100, height // 2 - 80), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
                
                cv2.putText(image, f"Mantén el gesto {gesture_display}", 
                           (100, height // 2 - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                cv2.putText(image, "por 1 segundo para confirmar", 
                           (100, height // 2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                cv2.putText(image, "Cualquier otro gesto cancela", 
                           (100, height // 2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            
                # Display countdown
                elapsed = time.time() - self.controller.countdown_start_time
                remaining = max(0, self.controller.countdown_duration - elapsed)
                
                if remaining <= 0:
                    self.controller._cancel_confirmation()
                else:
                    cv2.putText(image, f"Auto-cancelar en: {int(remaining)}s", 
                               (100, height // 2 + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    
        except Exception as e:
            print(f"⚠️ Error al dibujar confirmación: {e}")
    
    def print_statistics(self):
        """Print system control statistics."""
        print("\n" + "="*50)
        print("📊 ESTADÍSTICAS DE CONTROL DE SISTEMA")
        print("="*50)
        total_actions = sum(self.action_counts.values())
        
        print(f"{'Bloqueos':<20} | {self.action_counts['lock']:>3} veces")
        print(f"{'Apagados':<20} | {self.action_counts['shutdown']:>3} veces")
        print(f"{'Suspensiones':<20} | {self.action_counts['sleep']:>3} veces")
        print(f"{'Reinicios':<20} | {self.action_counts['restart']:>3} veces")
        
        print("-"*50)
        print(f"{'Total de acciones':<20} | {total_actions:>3}")
        print("="*50 + "\n")
    
    def run(self):
        """Run the enhanced system control loop."""
        if not self.controller.gesture_recognizer:
            print("❌ Error: Gesture Recognizer no está inicializado")
            return
            
        if not self.controller.start_camera():
            print("❌ Error: No se pudo iniciar la cámara")
            return
        
        print("\n🔧 Iniciando control de sistema por gestos...")
        print("⚠️ ADVERTENCIA: Este programa puede ejecutar acciones del sistema")
        print("Gestos disponibles:")
        print("  ✌️ Victoria → Bloquear pantalla")
        print("  ✊ Puño cerrado → Apagar sistema")
        print("  🖐️ Palma abierta → Suspender sistema")
        print("  👆 Señalar arriba → Reiniciar sistema")
        print("\n🔒 Mantén cada gesto por 3 segundos para activar")
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
                
                # Draw system control information
                self.draw_system_info(image)
                
                # Draw confirmation dialog if active
                self.draw_confirmation_dialog(image)
                
                # Draw hand landmarks
                self.controller.draw_hand_landmarks(image)
                
                # Display the image
                cv2.imshow('Control de Sistema por Gestos', image)
                
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
            print("👋 Control de sistema finalizado")

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
    
    # Crear y ejecutar el controlador de prueba
    try:
        print("\n🔧 Inicializando controlador de sistema...")
        test_controller = SystemControllerTest()
        test_controller.run()
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