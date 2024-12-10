import requests
from deepface import DeepFace
import cv2
import threading
import time
from flask import Flask, jsonify, request

# MJPEG 스트림 URL
stream_url = "http://192.168.1.7:8000/stream.mjpg"
cap = cv2.VideoCapture(stream_url)

# 표정 감지 값 저장
current_emotion = None

# 표정 감지 및 업데이트 함수
def emotion_detection():
    global current_emotion
    while True:
        ret, frame = cap.read()
        if not ret:
            print("프레임 읽기 실패")
            break
        
        try:
            # DeepFace 분석
            results = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            
            # 첫 번째 얼굴에 대한 결과 추출
            if results:
                result = results[0]
                dominant_emotion = result['dominant_emotion']
                emotion_confidence = result['emotion'][dominant_emotion]  # Confidence 값
                
                # 표정이 변경될 때만 저장
                if dominant_emotion != current_emotion:
                    current_emotion = dominant_emotion
                    print(f"Updated Emotion: {current_emotion} (Confidence: {emotion_confidence:.2f}%)")

        except Exception as e:
            print(f"DeepFace Error: {e}")

        time.sleep(1)
        
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
    # 표정 감지 쓰레드 시작
    emotion_thread = threading.Thread(target=emotion_detection)
    emotion_thread.daemon = True
    emotion_thread.start()
    
    # Flask 서버 실행
    app.run(host='0.0.0.0', port=5000)