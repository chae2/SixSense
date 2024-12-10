import requests
from deepface import DeepFace
import cv2
import threading
import time
from flask import Flask, jsonify, request
from queue import Queue
import face_recognition

# MJPEG 스트림 URL
stream_url = "http://192.168.1.7:8000/stream.mjpg"
cap = cv2.VideoCapture(stream_url)

# 표정 감지 값 저장
current_emotion = None

# 이미지 캡처를 위한 큐
image_queue = Queue()

# 표정 감지 함수
def emotion_detection():
    global current_emotion
    while True:
        if not image_queue.empty():
            frame = image_queue.get()
            try:
                # 얼굴 인식 (face_recognition 사용)
                rgb_frame = frame[:, :, ::-1]  # OpenCV는 BGR, face_recognition은 RGB 사용
                face_locations = face_recognition.face_locations(rgb_frame)

                if face_locations:
                    # 첫 번째 얼굴을 선택하여 표정 분석
                    top, right, bottom, left = face_locations[0]
                    face_image = frame[top:bottom, left:right]

                    # DeepFace 분석
                    results = DeepFace.analyze(face_image, actions=['emotion'], enforce_detection=False)

                    if results:
                        result = results[0]
                        dominant_emotion = result['dominant_emotion']
                        emotion_confidence = result['emotion'][dominant_emotion]  # Confidence 값
                        
                        # Confidence가 70 이상일 때만 current_emotion 업데이트
                        if emotion_confidence >= 80:
                            # 표정이 변경될 때만 저장
                            if dominant_emotion != current_emotion:
                                current_emotion = dominant_emotion
                                print(f"Updated Emotion: {current_emotion} (Confidence: {emotion_confidence:.2f}%)")
            except Exception as e:
                print(f"DeepFace Error: {e}")
        time.sleep(0.1)  # 짧은 대기 시간을 두어 너무 빠르게 반복하지 않도록

# 이미지 캡처 함수
def capture_images():
    while True:
        ret, frame = cap.read()
        if not ret:
            print("프레임 읽기 실패")
            break

        # 이미지 큐에 추가
        if image_queue.qsize() < 10:  # 큐에 너무 많은 프레임이 쌓이지 않도록 제한
            image_queue.put(frame)

# Flask 서버 코드
app = Flask(__name__)

# 라즈베리파이로 표정 값 전송 함수
def send_emotion_to_raspberrypi(emotion):
    try:
        # 라즈베리파이 Flask 서버로 표정 값 전송
        url = "http://192.168.1.7:5000/update_emotion"  # 라즈베리파이 Flask 서버 주소
        headers = {'Content-Type': 'application/json'}
        data = {'emotion': emotion}
        
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print(f"Emotion {emotion} sent to Raspberry Pi Flask server.")
        else:
            print(f"Failed to send emotion. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending emotion to Raspberry Pi: {e}")

# Bluetooth 서버에서 표정 값을 요청하면 해당 값을 라즈베리파이로 반환하는 Flask 엔드포인트
@app.route('/get_current_emotion', methods=['GET'])
def emotion():
    global current_emotion
    
    if current_emotion:
        # 요청이 들어오면 감정을 라즈베리파이로 전송
        send_emotion_to_raspberrypi(current_emotion)
        return jsonify({"emotion": current_emotion}), 200
    else:
        return jsonify({"emotion": "No emotion detected"}), 404


if __name__ == '__main__':
    # 이미지 캡처 쓰레드 시작
    capture_thread = threading.Thread(target=capture_images)
    capture_thread.daemon = True
    capture_thread.start()

    # 표정 감지 쓰레드 시작
    emotion_thread = threading.Thread(target=emotion_detection)
    emotion_thread.daemon = True
    emotion_thread.start()
    
    # Flask 서버 실행
    app.run(host='0.0.0.0', port=5000)
