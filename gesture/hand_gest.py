import socket
import cv2
import mediapipe as mp
import pyttsx3
import numpy as np

# Mediapipe 설정
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# 음성 엔진 설정
engine = pyttsx3.init()

# 제스처 맵핑
GESTURES = {
    "waving": "손을 흔들었습니다.",
    "thumbs_up": "엄지를 올렸습니다.",
    "thumbs_down": "엄지를 내렸습니다.",
    "pointing": "손가락을 휘저었습니다.",
    "ok_sign": "오케이 표시를 했습니다.",
    "number_sign": "숫자를 표시했습니다.",
    "v_sign": "V 사인을 했습니다.",
    "palm_up": "손바닥을 위로 올렸습니다.",
    "hands_clap": "손을 모았습니다.",
    "fist": "주먹을 쥐었습니다.",
    "fingers_fold": "손가락을 접었다 폈습니다.",
    "drawing_square": "네모를 그렸습니다.",
    "little_bit": "조금 사인을 했습니다.",
    "rock_paper_scissors": "가위바위보를 했습니다."
}

PI_HOST = 'PI_IP'
PI_PORT = 65432

def detect_gesture(hand_landmarks):
    # 손목과 손가락 마디 위치 가져오기
    landmarks = np.array([(lm.x, lm.y, lm.z) for lm in hand_landmarks.landmark])

    # 주요 마디 정의
    WRIST = landmarks[0]
    THUMB_TIP = landmarks[4]
    INDEX_TIP = landmarks[8]
    MIDDLE_TIP = landmarks[12]
    RING_TIP = landmarks[16]
    PINKY_TIP = landmarks[20]

    def is_thumb_up():
        return THUMB_TIP[1] < WRIST[1] and all(THUMB_TIP[1] < lm[1] for lm in landmarks[5:9])

    def is_thumb_down():
        return THUMB_TIP[1] > WRIST[1] and all(THUMB_TIP[1] > lm[1] for lm in landmarks[5:9])

    def is_waving():
        return abs(THUMB_TIP[0] - WRIST[0]) > 0.1 and all(THUMB_TIP[1] > lm[1] for lm in landmarks[1:5])

    def is_ok_sign():
        return np.linalg.norm(THUMB_TIP - INDEX_TIP) < 0.05

    def count_fingers():
        fingers_up = [
            np.linalg.norm(landmarks[i] - landmarks[i-2]) > 0.04
            for i in [8, 12, 16, 20]
        ]
        return fingers_up.count(True)

    def is_v_sign():
        return np.linalg.norm(INDEX_TIP - MIDDLE_TIP) > 0.1 and \
               np.linalg.norm(INDEX_TIP - WRIST) > 0.2 and \
               np.linalg.norm(MIDDLE_TIP - WRIST) > 0.2

    if is_thumb_up():
        return "thumbs_up"
    elif is_thumb_down():
        return "thumbs_down"
    elif is_waving():
        return "waving"
    elif is_ok_sign():
        return "ok_sign"
    elif is_v_sign():
        return "v_sign"
    else:
        fingers = count_fingers()
        if fingers == 0:
            return "fist"
        elif fingers == 2:
            return "v_sign"
        elif fingers == 1:
            return "pointing"
        elif fingers >= 3:
            return "number_sign"
        return "unknown"

def main(): ## local camera 사용함
    cap = cv2.VideoCapture(0)
    with mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    detected_gesture = detect_gesture(hand_landmarks)
                    if detected_gesture in GESTURES:
                        cv2.putText(frame, GESTURES[detected_gesture], (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        engine.say(GESTURES[detected_gesture])
                        engine.runAndWait()

            cv2.imshow('Hand Gesture Recognition', frame)
            if cv2.waitKey(5) & 0xFF == 27:
                break

    cap.release()
    cv2.destroyAllWindows()

def process_frame(frame_data):
    nparr = np.frombuffer(frame_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    with mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
        results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                detected_gesture = detect_gesture(hand_landmarks)
                if detected_gesture in GESTURES:
                    gesture_messsage = GESTURES[detected_gesture]
                    cv2.putText(frame, gesture_message, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    send_to_pi(gesture_messsage)
                    # engine.say(GESTURES[detected_gesture])
                    # engine.runAndWait()
                    # 파이로 보내는 로직 필요

def send_to_pi(message):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall(message.encode('utf-8'))
    except Exception as e:
        print(f"error occured during sending message: {e}")


def start_local_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 9999))
    server_socket.listen(1)
    print("Starting Server...")

    conn, addr = server_socket.accept()
    print(f"RaspberryPi Connected: {addr}")

    while True:
        data = conn.recv(4096)
        if not data:
            break
        
        result = process_frame(data)
        conn.sendall(result.encode())
    conn.close()
    server_socket.close()

if __name__ == "__main__":
    # main() # 로컬 실험
    process_frame() # 라즈베리 파이로 실험
