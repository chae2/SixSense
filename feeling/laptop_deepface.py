import requests
from deepface import DeepFace
import face_recognition
import cv2
import threading
import time
from flask import Flask, jsonify, request

# MJPEG 스트림 URL
stream_url = "http://192.168.1.7:8000/stream.mjpg"
cap = cv2.VideoCapture(stream_url)

# 표정 감지 값 저장
current_emotion = None
last_emotion_time = time.time()  # 마지막 표정 감지 시간 기록
emotion_detection_interval = 3  # 표정 분석 간격 (초)

# 표정 감지 및 업데이트 함수
def emotion_detection():
    global current_emotion, last_emotion_time
    while True:
        ret, frame = cap.read()
        if not ret:
            print("프레임 읽기 실패")
            break
        
        # 얼굴 인식
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # BGR -> RGB 변환
        face_locations = face_recognition.face_locations(rgb_frame)
        
        if len(face_locations) > 0:
            # 첫 번째 얼굴 위치를 가져오기 (여러 얼굴을 다룰 수 있음)
            face_location = face_locations[0]
            top, right, bottom, left = face_location
            
            # 얼굴 영역 표시
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            
            # 일정 간격마다 표정 분석을 수행
            if time.time() - last_emotion_time > emotion_detection_interval:
                try:
                    # DeepFace 분석 (얼굴 영역만 분석)
                    face_image = frame[top:bottom, left:right]
                    results = DeepFace.analyze(face_image, actions=['emotion'], enforce_detection=False)
                    
                    if results:
                        result = results[0]
                        dominant_emotion = result['dominant_emotion']
                        
                        # 표정이 변경될 때만 저장
                        if dominant_emotion != current_emotion:
                            current_emotion = dominant_emotion
                            print(f"Updated Emotion: {current_emotion}")
                        
                        # 결과 화면에 표시
                        cv2.putText(frame, f"Emotion: {current_emotion}", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                        # 마지막 표정 분석 시간 업데이트
                        last_emotion_time = time.time()

                except Exception as e:
                    print(f"DeepFace Error: {e}")
        
        # 화면에 표시하지 않음
        # cv2.imshow("Emotion Detection", frame)

        # 'q' 키를 눌러 종료
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break

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
