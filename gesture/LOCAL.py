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

PI_HOST = '192.168.1.7' #'172.20.10.4'
PI_PORT = 8000 #65432

# Mediapipe 설정
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_holistic = mp.solutions.holistic

# 표정 및 제스처 관련 전역 변수
previous_gesture = None
previous_pose = None
previous_nose_y = None

# Gesture, Pose, and Emotion Constants
GESTURES = {
    "waving": "currently waving.",
    "thumbs_up": "thumbs up.",
    "thumbs_down": "thumbs down.",
    "pointing": "finger pointing.",
    "ok_sign": "made an OK sign.",
    "v_sign": "made a V sign.",
    "fist": "made a fist.",
    "nodding": "nodding in consent.",
    "shaking_head": "shaking head.",
    "raising_hand": "rasing hand."
}
nodding_thsd = 14
shaking_thsd = 20

previous_wrist = np.array([0, 0, 0])
previous_palm = np.array([0, 0, 0])

# 제스처 감지 함수
def detect_gesture(hand_landmarks, image_height, image_width):
    global previous_palm, previous_wrist
    def to_pixel(landmark):
        return np.array([landmark.x * image_width, landmark.y * image_height, landmark.z])

    landmarks = np.array([to_pixel(lm) for lm in hand_landmarks.landmark])
    WRIST, THUMB_TIP, INDEX_DIP, INDEX_TIP, MIDDLE_TIP = landmarks[0], landmarks[4], landmarks[7], landmarks[8], landmarks[12]
    finger_mcp = [to_pixel(hand_landmarks.landmark[lm]) for lm in [
        mp_hands.HandLandmark.THUMB_CMC,
        mp_hands.HandLandmark.INDEX_FINGER_MCP,
        mp_hands.HandLandmark.MIDDLE_FINGER_MCP,
        mp_hands.HandLandmark.RING_FINGER_MCP,
        mp_hands.HandLandmark.PINKY_MCP
    ]]
    
    finger_tips = [to_pixel(hand_landmarks.landmark[lm]) for lm in [
        mp_hands.HandLandmark.THUMB_TIP,
        mp_hands.HandLandmark.INDEX_FINGER_TIP,
        mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
        mp_hands.HandLandmark.RING_FINGER_TIP,
        mp_hands.HandLandmark.PINKY_TIP
    ]]
    mid_point = np.mean([WRIST]+finger_mcp, axis=0)


    def is_thumb_up():
        return THUMB_TIP[1] < WRIST[1] and all(THUMB_TIP[1] < lm[1] for lm in landmarks[5:9])
    def is_thumb_down():
        return THUMB_TIP[1] > WRIST[1] and all(THUMB_TIP[1] > lm[1] for lm in landmarks[5:9])

    def is_v_sign():
        index_middle_dist = np.linalg.norm(INDEX_TIP-MIDDLE_TIP)
        fingers_extended = all(finger_tips[i][1]<finger_mcp[i][1] for i in range(1,3)) # 검지, 중지
        other_fingers_down = all(finger_tips[i][1] > finger_mcp[i][1] for i in range(3,5)) #약지, 새끼
        return index_middle_dist > 40 and fingers_extended and other_fingers_down
    def is_ok_sign():
        thumb_index_dist = np.linalg.norm(THUMB_TIP - INDEX_TIP)
        other_fingers_up = all(finger_tips[i][1] < finger_mcp[i][1] for i in range(2,5)) # 중지, 약지, 새끼
        return thumb_index_dist < 20 and other_fingers_up

    def is_waving():
        global previous_wrist, previous_palm
        wrist_position = to_pixel(hand_landmarks.landmark[mp_hands.HandLandmark.WRIST])
        palm_position = (wrist_position + np.mean([to_pixel(hand_landmarks.landmark[lm]) for lm in [mp_hands.HandLandmark.INDEX_FINGER_TIP, mp_hands.HandLandmark.MIDDLE_FINGER_TIP]], axis=0))

        # wrist와 palm의 이전 위치와 현재 위치를 비교
        wrist_distance = np.linalg.norm(wrist_position - previous_wrist)
        palm_distance = np.linalg.norm(palm_position - previous_palm)
        all_up = all(finger_tips[i][1] < finger_mcp[i][1] for i in range(1,5))

        previous_wrist = wrist_position
        previous_palm = palm_position

        # 일정한 거리가 이동한 경우 waving으로 감지
        return wrist_distance > 50 and palm_distance > 50 and all_up
    
    def make_fist():
        return all(np.linalg.norm(tip-mid_point)<40 for tip in finger_tips)

    def pointing():
        other_fingers_down = all(finger_tips[i][1] > finger_mcp[i][1] for i in range(2,5))
        return INDEX_TIP[2] < INDEX_DIP[2] and other_fingers_down

    if is_thumb_up():
        return "thumbs_up"
    elif is_thumb_down():
        return "thumbs_down"
    elif is_v_sign():
        return "v_sign"
    elif is_waving():
        return "waving"
    elif make_fist():
        return "fist"
    elif pointing():
        return "pointing"
    elif is_ok_sign():
        return "ok_sign"
    return None


# 자세 감지 함수
def detect_pose(landmarks, image_height, image_width):
    global previous_nose_y

    def to_pixel(landmark):
        return np.array([landmark.x * image_width, landmark.y * image_height])

    nose = to_pixel(landmarks[mp_holistic.PoseLandmark.NOSE.value])
    left_shoulder = to_pixel(landmarks[mp_holistic.PoseLandmark.LEFT_SHOULDER.value])
    right_shoulder = to_pixel(landmarks[mp_holistic.PoseLandmark.RIGHT_SHOULDER.value])
    left_wrist = to_pixel(landmarks[mp_holistic.PoseLandmark.LEFT_WRIST.value])
    right_wrist = to_pixel(landmarks[mp_holistic.PoseLandmark.RIGHT_WRIST.value])
    shoulder_width = np.linalg.norm(left_shoulder - right_shoulder)

    if previous_nose_y is not None:
        vertical_movement = abs(nose[1] - previous_nose_y)
        if vertical_movement > nodding_thsd:
            previous_nose_y = nose[1]
            return "nodding"
    else:
        previous_nose_y = nose[1]
    
    ## Shaking head
    if abs(nose[0]-(left_shoulder[0]+right_shoulder[0])/2) > shaking_thsd:
        return "shaking_head"

    if left_wrist[1] < left_shoulder[1] or right_wrist[1] <right_shoulder[1]:
        return "raising_hand"

def process_frame(frame):
    global previous_gesture, previous_pose

    with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic, \
         mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:

            image_height, image_width, _ = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            flag = 0

            # Hand Gesture Detection
            hand_results = hands.process(rgb_frame)
            if hand_results.multi_hand_landmarks:
                for hand_landmarks in hand_results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    gesture = detect_gesture(hand_landmarks, image_height, image_width)
                    if gesture and gesture != previous_gesture:
                        # print(f"Hand detected: {GESTURES[gesture]}")
                        previous_gesture = gesture
                        send_gesture_to_pi(GESTURES[gesture])
                        flag = 1
                    else:
                        gesture = None
            
            # Pose Detection
            results = holistic.process(rgb_frame)
            if results.pose_landmarks:
                pose = detect_pose(results.pose_landmarks.landmark, image_height, image_width)
                if pose and pose != previous_pose and flag!=1:
                    # print(f"Pose detected: {GESTURES[pose]}")
                    send_gesture_to_pi(GESTURES[pose])
                    previous_pose = pose
                else:
                    pose = None

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
            process_frame(frame)

        except Exception as e:
            print(f"Mediapipe Error: {e}")
        
        # OpenCV 창에 영상 출력
        cv2.imshow('Stream', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
