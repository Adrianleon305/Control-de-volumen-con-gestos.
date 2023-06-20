import cv2
import mediapipe as mp
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Inicializar la captura de video
cap = cv2.VideoCapture(0)

# Obtener el controlador de volumen
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volumen = cast(interface, POINTER(IAudioEndpointVolume))

# Configuraciones del volumen
volumen_maximo = 1.0  # Volumen máximo permitido
volumen_minimo = 0.0  # Volumen mínimo permitido
volumen_actual = volumen.GetMasterVolumeLevelScalar()

# Inicializar la detección de manos con menor precisión
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False,
                       max_num_hands=1,
                       min_detection_confidence=0.9,
                       min_tracking_confidence=0.9)

# Variables para almacenar la distancia máxima entre los puntos del dedo gordo (pulgar) e índice
max_distance = 0
frame_count = 0

while cap.isOpened():
    ret, frame = cap.read()

    if not ret:
        break

    frame_count += 1

    if frame_count % 5 == 0:
        # Convertir la imagen de BGR a RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detectar manos utilizando mediapipe
        results = hands.process(rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Calcular la distancia entre los puntos del dedo gordo (pulgar) e índice
                if len(hand_landmarks.landmark) >= 4:
                    thumb_tip = hand_landmarks.landmark[4]
                    index_tip = hand_landmarks.landmark[8]
                    distance = math.sqrt((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)
                    if distance > max_distance:
                        max_distance = distance
                else:
                    distance = 0

                # Normalizar la distancia en el rango [0, 1]
                normalized_distance = distance / max_distance

                # Si la distancia es menor a un umbral, se considera la mano cerrada
                umbral_cerrado = 0.1
                if normalized_distance < umbral_cerrado:
                    # Si la mano está cerrada, se baja el volumen si no está ya al mínimo
                    if volumen_actual != volumen_minimo:
                        volumen_actual = volumen_minimo
                        volumen.SetMasterVolumeLevelScalar(volumen_actual, None)
                else:
                    # Si la mano está abierta, se sube el volumen si no está ya al máximo
                    if volumen_actual != volumen_maximo:
                        volumen_actual = volumen_maximo
                        volumen.SetMasterVolumeLevelScalar(volumen_actual, None)

    # Salir del bucle si se presiona la tecla 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Liberar los recursos
cap.release()
cv2.destroyAllWindows()
