#!/usr/bin/env python3
"""
Script de prueba para verificar la detección de mano derecha
"""

import cv2
import mediapipe as mp
import time

def test_hand_detection():
    """Probar la detección de manos para verificar la clasificación."""
    
    # MediaPipe setup
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,  # Detectar ambas manos para comparar
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    )
    drawing_utils = mp.solutions.drawing_utils
    
    # Camera setup
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    print("🔍 PRUEBA DE DETECCIÓN DE MANOS")
    print("=" * 40)
    print("Muestra ambas manos frente a la cámara")
    print("Presiona 'q' para salir")
    print()
    
    try:
        while True:
            success, img = cap.read()
            if not success:
                continue
            
            # Voltear imagen para efecto espejo
            img = cv2.flip(img, 1)
            h, w, _ = img.shape
            
            # Procesar con MediaPipe
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_img)
            
            # Información de detección
            hand_info = []
            
            if results.multi_hand_landmarks and results.multi_handedness:
                for idx, (hand_landmarks, handedness) in enumerate(zip(results.multi_hand_landmarks, results.multi_handedness)):
                    # Obtener clasificación
                    label = handedness.classification[0].label
                    score = handedness.classification[0].score
                    
                    # Determinar color según la mano
                    if label == 'Right':
                        color = (0, 255, 0)  # Verde para mano derecha
                        hand_type = "DERECHA ✅"
                    else:
                        color = (0, 0, 255)  # Rojo para mano izquierda
                        hand_type = "IZQUIERDA ❌"
                    
                    # Dibujar landmarks
                    drawing_utils.draw_landmarks(
                        img, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                        landmark_drawing_spec=mp.solutions.drawing_utils.DrawingSpec(color=color, thickness=2, circle_radius=2),
                        connection_drawing_spec=mp.solutions.drawing_utils.DrawingSpec(color=color, thickness=2)
                    )
                    
                    # Obtener posición del centro de la mano
                    cx = int(hand_landmarks.landmark[9].x * w)
                    cy = int(hand_landmarks.landmark[9].y * h)
                    
                    # Mostrar información
                    cv2.putText(img, f'{hand_type}', (cx - 50, cy - 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                    cv2.putText(img, f'Conf: {score:.2f}', (cx - 50, cy), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                    
                    hand_info.append(f"{hand_type} (Conf: {score:.2f})")
            
            # Mostrar información general
            cv2.putText(img, "PRUEBA DE DETECCION DE MANOS", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            if hand_info:
                for i, info in enumerate(hand_info):
                    cv2.putText(img, info, (10, 70 + i * 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            else:
                cv2.putText(img, "No se detectan manos", (10, 70), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Instrucciones
            instructions = [
                "Verde = Mano Derecha (Funciona)",
                "Rojo = Mano Izquierda (No funciona)",
                "Presiona 'q' para salir"
            ]
            
            for i, instruction in enumerate(instructions):
                cv2.putText(img, instruction, (10, h - 80 + i * 25), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Mostrar imagen
            cv2.imshow('Prueba de Detección de Manos', img)
            
            # Salir con 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    except KeyboardInterrupt:
        print("\n⚠️ Interrupción detectada")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        hands.close()
        print("👋 Prueba finalizada")


if __name__ == "__main__":
    test_hand_detection() 