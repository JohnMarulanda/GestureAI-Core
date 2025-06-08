#!/usr/bin/env python3
"""
Script de prueba para el Control Multimedia por Gestos
Utiliza MediaPipe Gesture Recognizer para controlar funciones multimedia.

Gestos soportados:
1. Pulgar arriba (Thumb_Up) → Adelantar/Siguiente
2. Pulgar abajo (Thumb_Down) → Retroceder/Anterior
3. Puño cerrado (Closed_Fist) → Silenciar/Activar audio
4. Te amo (ILoveYou) → Pausar/Reproducir

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

from core.controllers.multimedia_controller import MultimediaController

class MultimediaControllerTest:
    """Test wrapper for MultimediaController with enhanced UI and statistics."""
    
    def __init__(self):
        """Initialize the test wrapper."""
        self.controller = MultimediaController()
        
        # Action status
        self.action_message = ""
        self.action_message_time = 0
        self.action_message_duration = 2.0
        
        # Spanish translations for display
        self.gesture_names = {
            'Thumb_Up': 'Adelantar (Pulgar arriba)',
            'Thumb_Down': 'Retroceder (Pulgar abajo)',
            'Closed_Fist': 'Silenciar (Puño)',
            'ILoveYou': 'Pausar/Reproducir (Te amo)'
        }
        
        # Action descriptions
        self.action_descriptions = {
            'forward': 'Adelantar/Siguiente',
            'backward': 'Retroceder/Anterior',
            'mute': 'Silenciar/Activar',
            'play_pause': 'Pausar/Reproducir'
        }
        
        # Multimedia action counters
        self.action_counts = {
            'forward': 0,
            'backward': 0,
            'mute': 0,
            'play_pause': 0
        }
        
        # Override controller methods to add logging and statistics
        self._override_controller_methods()
        
        print("✅ Controlador Multimedia inicializado")
        if self.controller.gesture_recognizer:
            print("✅ Gesture Recognizer para control multimedia inicializado")
        else:
            print(f"❌ Modelo no encontrado: {self.controller.model_path}")
        
        if self.controller.volume_available:
            print("✅ Control de volumen inicializado")
        else:
            print("⚠️ Control de volumen no disponible")
    
    def _override_controller_methods(self):
        """Override controller methods to add logging and statistics."""
        # Store original method
        original_perform_multimedia_action = self.controller._perform_multimedia_action
        
        def enhanced_perform_multimedia_action(gesture_name, confidence):
            action = self.controller.gesture_actions[gesture_name]
            gesture_display = self.gesture_names[gesture_name]
            
            if action == 'forward':
                self.action_counts['forward'] += 1
                self._set_action_message("⏭️ Adelantar/Siguiente")
                print(f"⏭️ {gesture_display} (Confianza: {confidence:.2f}) - Adelantar")
                
            elif action == 'backward':
                self.action_counts['backward'] += 1
                self._set_action_message("⏮️ Retroceder/Anterior")
                print(f"⏮️ {gesture_display} (Confianza: {confidence:.2f}) - Retroceder")
                
            elif action == 'mute':
                if self.controller.volume_available:
                    is_muted = self.controller.volume.GetMute()
                    mute_status = "Silenciado" if not is_muted else "Audio activado"
                    self.action_counts['mute'] += 1
                    self._set_action_message(f"🔇 {mute_status}")
                    print(f"🔇 {gesture_display} (Confianza: {confidence:.2f}) - {mute_status}")
                else:
                    print("⚠️ Control de volumen no disponible")
                    
            elif action == 'play_pause':
                self.action_counts['play_pause'] += 1
                self._set_action_message("⏯️ Pausar/Reproducir")
                print(f"⏯️ {gesture_display} (Confianza: {confidence:.2f}) - Pausar/Reproducir")
            
            # Call original method
            original_perform_multimedia_action(gesture_name, confidence)
        
        # Replace method
        self.controller._perform_multimedia_action = enhanced_perform_multimedia_action
    
    def _set_action_message(self, message):
        """Set the action message to display on screen."""
        self.action_message = message
        self.action_message_time = time.time()
    
    def draw_multimedia_info(self, image):
        """Draw multimedia control information on the image."""
        try:
            height, width, _ = image.shape
            
            # Draw background rectangle for text
            cv2.rectangle(image, (10, 10), (width - 10, 240), (0, 0, 0), -1)
            cv2.rectangle(image, (10, 10), (width - 10, 240), (255, 255, 255), 2)
            
            # Draw title
            cv2.putText(image, "Control Multimedia por Gestos", 
                       (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Draw gesture instructions
            y_pos = 65
            instructions = [
                "👍 Pulgar arriba: Adelantar/Siguiente",
                "👎 Pulgar abajo: Retroceder/Anterior",
                "✊ Puño: Silenciar/Activar audio",
                "🤟 Te amo: Pausar/Reproducir"
            ]
            
            for instruction in instructions:
                cv2.putText(image, instruction, (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                y_pos += 25
            
            # Draw current gesture
            if self.controller.last_gesture:
                gesture_display = self.gesture_names.get(self.controller.last_gesture, self.controller.last_gesture)
                cv2.putText(image, f"Gesto: {gesture_display}", 
                           (20, y_pos + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            
            # Draw delay status for mute and play/pause
            current_time = time.time()
            y_delay_pos = y_pos + 50
            
            # Mute delay status
            mute_remaining = max(0, self.controller.mute_delay - (current_time - self.controller.last_mute_time))
            if mute_remaining > 0:
                cv2.putText(image, f"Silenciar disponible en: {mute_remaining:.1f}s", 
                           (20, y_delay_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 100, 100), 1)
                y_delay_pos += 20
            
            # Play/pause delay status
            play_pause_remaining = max(0, self.controller.play_pause_delay - (current_time - self.controller.last_play_pause_time))
            if play_pause_remaining > 0:
                cv2.putText(image, f"Pausar disponible en: {play_pause_remaining:.1f}s", 
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
    
    def draw_volume_bar(self, image):
        """Display a volume level bar."""
        try:
            if not self.controller.volume_available:
                return
                
            current_volume = self.controller.volume.GetMasterVolumeLevelScalar()
            volume_percent = int(current_volume * 100)
            is_muted = self.controller.volume.GetMute()
            
            bar_width = 200
            bar_height = 20
            bar_x = image.shape[1] - bar_width - 20
            bar_y = 50
            
            # Draw background bar
            cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), 
                          (100, 100, 100), -1)
            
            # Draw filled volume bar (red if muted, green if not)
            filled_width = int(bar_width * current_volume)
            bar_color = (0, 0, 255) if is_muted else (0, 255, 0)
            cv2.rectangle(image, (bar_x, bar_y), (bar_x + filled_width, bar_y + bar_height), 
                          bar_color, -1)
            
            # Draw volume percentage text
            mute_text = " (MUTE)" if is_muted else ""
            cv2.putText(image, f"Volumen: {volume_percent}%{mute_text}", (bar_x, bar_y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        except Exception as e:
            print(f"⚠️ Error al dibujar barra de volumen: {e}")
    
    def draw_statistics(self, image):
        """Display multimedia statistics on the right side."""
        try:
            height, width, _ = image.shape
            
            # Draw background for statistics
            stats_x = width - 280
            cv2.rectangle(image, (stats_x, 100), (width - 10, 250), (0, 0, 0), -1)
            cv2.rectangle(image, (stats_x, 100), (width - 10, 250), (255, 255, 255), 2)
            
            # Draw statistics title
            cv2.putText(image, "Estadisticas", 
                       (stats_x + 10, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            y_pos = 150
            for action, count in self.action_counts.items():
                action_name = self.action_descriptions[action]
                cv2.putText(image, f"{action_name}: {count}", 
                           (stats_x + 10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                y_pos += 20
            
            # Total actions
            total_actions = sum(self.action_counts.values())
            cv2.putText(image, f"Total: {total_actions}", 
                       (stats_x + 10, y_pos + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
            
            # Audio status
            audio_status = "SÍ" if self.controller.volume_available else "NO"
            cv2.putText(image, f"Audio: {audio_status}", 
                       (stats_x + 10, y_pos + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            
        except Exception as e:
            print(f"⚠️ Error al dibujar estadísticas: {e}")
    
    def print_statistics(self):
        """Print multimedia control statistics."""
        print("\n" + "="*50)
        print("📊 ESTADÍSTICAS DE CONTROL MULTIMEDIA")
        print("="*50)
        total_actions = sum(self.action_counts.values())
        
        for action, count in self.action_counts.items():
            action_name = self.action_descriptions[action]
            percentage = (count / total_actions * 100) if total_actions > 0 else 0
            print(f"{action_name:<20} | {count:>3} veces ({percentage:>5.1f}%)")
        
        print("-"*50)
        print(f"{'Total de acciones':<20} | {total_actions:>3}")
        print(f"{'Audio disponible':<20} | {'SÍ' if self.controller.volume_available else 'NO':>3}")
        print("="*50 + "\n")
    
    def run(self):
        """Run the enhanced multimedia control loop."""
        if not self.controller.gesture_recognizer:
            print("❌ Error: Gesture Recognizer no está inicializado")
            return
            
        if not self.controller.start_camera():
            print("❌ Error: No se pudo iniciar la cámara")
            return
        
        print("\n🎵 Iniciando control multimedia por gestos...")
        print("Gestos disponibles:")
        print("  👍 Pulgar arriba → Adelantar/Siguiente")
        print("  👎 Pulgar abajo → Retroceder/Anterior")
        print("  ✊ Puño → Silenciar/Activar audio")
        print("  🤟 Te amo → Pausar/Reproducir")
        print("\n🎮 Controla tu multimedia con gestos naturales")
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
                
                # Draw multimedia control information
                self.draw_multimedia_info(image)
                
                # Draw volume bar
                self.draw_volume_bar(image)
                
                # Draw statistics
                self.draw_statistics(image)
                
                # Draw hand landmarks
                self.controller.draw_hand_landmarks(image)
                
                # Display the image
                cv2.imshow('Control Multimedia por Gestos', image)
                
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
            print("👋 Control multimedia finalizado")

def main():
    """Función principal para ejecutar la prueba de control multimedia."""
    print("="*60)
    print("🎵 PRUEBA DE CONTROL MULTIMEDIA POR GESTOS")
    print("="*60)
    print("🎯 OBJETIVO:")
    print("   Probar el control multimedia usando 4 gestos específicos")
    print("   con delays inteligentes para evitar activaciones múltiples.")
    print()
    print("🖐️ GESTOS DE CONTROL:")
    print("   👍 Pulgar arriba    → Adelantar/Siguiente pista")
    print("   👎 Pulgar abajo     → Retroceder/Anterior pista")
    print("   ✊ Puño             → Silenciar/Activar audio")
    print("   🤟 Te amo           → Pausar/Reproducir")
    print()
    print("🎮 GESTOS CON DELAYS INTELIGENTES:")
    print("   - Navegación rápida (0.4s): Adelantar/Retroceder")
    print("   - Controles lentos (1.5s): Silenciar/Pausar")
    print("   - Evita activaciones accidentales")
    print("   - Indicador visual de tiempo restante")
    print()
    print("📊 CARACTERÍSTICAS:")
    print("   - Control en tiempo real con alta precisión")
    print("   - Umbral de confianza: 70%")
    print("   - Delay navegación: 0.4 segundos")
    print("   - Delay silenciar/pausar: 1.5 segundos")
    print("   - Soporte para 1 mano optimizado")
    print("   - Control de volumen integrado con pycaw")
    print("   - Estadísticas de acciones ejecutadas")
    print("   - Interfaz visual con progreso y estado")
    print("   - Landmarks de mano dibujados")
    print("   - Barra de volumen con estado de silencio")
    print()
    print("🔧 CONFIGURACIÓN:")
    print("   - Gestos: Thumb_Up, Thumb_Down, Closed_Fist, ILoveYou")
    print("   - Delays específicos por tipo de acción")
    print("   - Threading para acciones no bloqueantes")
    print("   - Manejo robusto de errores")
    print("   - Indicadores visuales de disponibilidad")
    print()
    print("⌨️  CONTROLES:")
    print("   ESC      : Salir del programa")
    print()
    print("🎵 ACCIONES MULTIMEDIA:")
    print("   ⏭️ ADELANTAR: Envía tecla 'flecha derecha'")
    print("   ⏮️ RETROCEDER: Envía tecla 'flecha izquierda'")
    print("   🔇 SILENCIAR: Toggle del estado de mute del sistema")
    print("   ⏯️ PAUSAR: Envía tecla 'espacio' para play/pause")
    print()
    print("🔍 REQUISITOS:")
    print("   - Cámara web funcional")
    print("   - Modelo gesture_recognizer.task en models/")
    print("   - pycaw instalado para control de volumen")
    print("   - pyautogui para envío de teclas")
    print("   - Aplicación multimedia activa (reproductor, YouTube, etc.)")
    print()
    print("💡 RECOMENDACIONES:")
    print("   - Abre tu reproductor multimedia favorito")
    print("   - Reproduce algún contenido para probar")
    print("   - Mantén buena iluminación para detección")
    print("   - Usa gestos claros y definidos")
    print("   - El gesto 'Te amo' es meñique + índice + pulgar extendidos")
    print()
    print("🎯 CASOS DE USO:")
    print("   - Control de YouTube sin tocar el teclado")
    print("   - Navegación en Spotify o reproductores")
    print("   - Control de presentaciones multimedia")
    print("   - Accesibilidad para usuarios con limitaciones")
    print()
    
    try:
        input("Presiona ENTER para comenzar la prueba...")
    except KeyboardInterrupt:
        print("\n❌ Operación cancelada por el usuario")
        return
    
    # Crear y ejecutar el controlador de prueba
    try:
        print("\n🎵 Inicializando controlador multimedia...")
        test_controller = MultimediaControllerTest()
        test_controller.run()
    except Exception as e:
        print(f"❌ Error al ejecutar el controlador: {e}")
        print("   Verifica que:")
        print("   1. La cámara esté disponible")
        print("   2. El modelo gesture_recognizer.task exista en models/")
        print("   3. Las dependencias estén instaladas correctamente:")
        print("      pip install mediapipe opencv-python pyautogui pycaw comtypes")
        print("   4. Tu sistema tenga audio configurado")
        print("   5. Tengas una aplicación multimedia abierta")
    
    print("\n👋 ¡Gracias por probar el control multimedia por gestos!")
    print("   Recuerda: Los gestos naturales hacen la experiencia más fluida")

if __name__ == "__main__":
    main() 