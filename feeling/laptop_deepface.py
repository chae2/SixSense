import requests
from deepface import DeepFace
import cv2
import threading
import time
from flask import Flask, jsonify, request

# rtsp 스트림 URL
stream_url = "rtsp://192.168.1.7:8554/unicast"
cap = cv2.VideoCapture(stream_url)

# 표정 감지 값 저장
current_emotion = 'neutral'

# 표정 감지 및 업데이트 함수 (블루투스 요청 시에만 실행됨)
def emotion_detection():
    ret, frame = cap.read()
    if not ret:
        print("프레임 읽기 실패")
        return None
    
    try:
        # DeepFace 분석 (얼굴 인식 및 감정 분석 포함)
        results = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        
        if results:
            result = results[0]
            dominant_emotion = result['dominant_emotion']
            confidence = result['emotion'][dominant_emotion]  # confidence 값 가져오기
                
            print(f"Detected Emotion: {dominant_emotion} with confidence {confidence}")
            return dominant_emotion

    except Exception as e:
        print(f"DeepFace Error: {e}")
        return None

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
        # 블루투스 요청이 들어오면 표정 인식을 한 번 수행
    detected_emotion = emotion_detection()
    print(detected_emotion)
    if detected_emotion:
        send_emotion_to_raspberrypi(detected_emotion)
        return jsonify({"emotion": detected_emotion}), 200
    else:
        return jsonify({"emotion": "No face detected"}), 404


# 스트리밍을 화면에 표시하는 함수
def display_stream():
    while True:
        ret, frame = cap.read()
        if not ret:
            print("스트리밍 오류 발생")
            break
        
        # 화면에 스트리밍 표시
        cv2.imshow("RTSP Stream", frame)
        
        # 'q' 키를 누르면 종료
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 스트리밍 종료 시 리소스 정리
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    # 스트리밍을 표시하는 스레드 실행
    #threading.Thread(target=display_stream, daemon=True).start()
    
    # Flask 서버 실행
    app.run(host='0.0.0.0', port=5000)
