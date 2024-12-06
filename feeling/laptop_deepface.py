import requests
from deepface import DeepFace
import cv2
import json

# MJPEG 스트림 URL
stream_url = "http://192.168.1.7:8000/stream.mjpg"
cap = cv2.VideoCapture(stream_url)

previous_emotion = None  # 이전 감지된 표정

def send_emotion_to_server(emotion, confidence):
    url = "http://192.168.1.7:5000/update_emotion"  # Flask 서버 주소
    headers = {'Content-Type': 'application/json'}
    data = {
        'emotion': emotion,
        'confidence': confidence
    }
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        print(f"Emotion {emotion} sent to server.")
    else:
        print(f"Error sending emotion to server: {response.text}")

if not cap.isOpened():
    print("스트림을 열 수 없습니다.")
else:
    print("스트림 열림 성공")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("프레임 읽기 실패")
            break
        
        try:
            # DeepFace 분석
            results = DeepFace.analyze(frame, actions=['emotion'])
            
            # 첫 번째 얼굴에 대한 결과 추출
            if results:
                result = results[0]
                dominant_emotion = result['dominant_emotion']
                confidence = result['face_confidence']
                
                print(f"Dominant Emotion: {dominant_emotion}, Confidence: {confidence:.2f}")
                
                # 표정이 이전과 다를 때만 서버로 전송
                if dominant_emotion != previous_emotion:
                    send_emotion_to_server(dominant_emotion, confidence)
                    previous_emotion = dominant_emotion
                    
        except Exception as e:
            print(f"DeepFace Error: {e}")

        # OpenCV 창에 영상 출력
        cv2.imshow('Stream', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
