# import socket
import cv2
import mediapipe as mp
import numpy as np
import requests

# Mediapipe 설정
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# MJPEG 스트림 url
stream_url = "http://192.168.1.7:8000/stream.mjpg"
cap = cv2.VideoCapture(stream_url)

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

PI_HOST = '192.168.1.7' #'172.20.10.4'
PI_PORT = 8000 #65432

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

def process_frame(frame):
    with mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
        results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                return detect_gesture(hand_landmarks)
    return None

def send_gesture_to_pi(gesture_message):
    url = "http://192.168.1.7:5000/detect_gesture"
    headers = {'Content-Type': 'application/json'}
    data={
        'gesture': gesture_message
    }
    response = requests.post(url, headers=headers, json=data)

    if response.status_code==200:
        print(f"Gesture {gesture_message} sent to pi server.")
    else:
        print(f"Error sending gesture to pi server: {response}")
    # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
    #     client_socket.connect((PI_HOST, PI_PORT + 1))
    #     client_socket.sendall(gesture_message.encode('utf-8'))

if not cap.isOpened():
    print("Cannot open stream.")
else:
    print("Success in opening stream")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Frame reading failed")
            break

        try:
            # Mediapipe로 행동 알아차리기
            detected_gesture = process_frame(frame)
            if detected_gesture and detected_gesture in GESTURES:
                print(f"Current Gesture: {GESTURES[detected_gesture]}")
                send_gesture_to_pi(GESTURES[detected_gesture])
        except Exception as e:
            print(f"Mediapipe Error: {e}")
        
        # OpenCV 창에 영상 출력
        cv2.imshow('Stream', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()

# def receive_video_from_pi():
#     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
#         server_socket.bind((PI_HOST, PI_PORT))
#         server_socket.listen(1)
#         print(f"Video Server waiting on PORT {PI_PORT}...")
#         conn, _ = server_socket.accept()
#         with conn:
#             buffer = b""
#             while True:
#                 data = conn.recv(4096)
#                 if not data:
#                     break
#                 buffer += data
#                 # JPEG 프레임이 끝날 때마다 처리
#                 if b'\xff\xd9' in buffer:
#                     frame_data, buffer = buffer.split(b'\xff\xd9')[:2]
#                     frame_data += b'\xff\xd9'
#                     nparr = np.frombuffer(frame_data, np.uint8)
#                     frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
#                     detected_gesture = process_frame(frame)
#                     if detected_gesture and detected_gesture in GESTURES:
#                         send_gesture_to_pi(GESTURES[detected_gesture])
#                     cv2.imshow("Received Video", frame)
#                     if cv2.waitKey(1) & 0xFF == ord('q'):
#                         break
#             cv2.destroyAllWindows()



# if __name__ == "__main__":
#     receive_video_from_pi()
