from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import numpy as np
from deepface import DeepFace
import base64
import cv2

app = Flask(__name__)
socketio = SocketIO(app)

# 이전 감정을 저장하기 위한 변수
previous_emotion = None

# 클라이언트로부터 이미지를 받는 웹소켓 핸들러
@socketio.on('upload_image')
def handle_image(data):
    global previous_emotion

    # Base64로 전송된 이미지 데이터
    img_data = base64.b64decode(data['image'])
    
    # 이미지 데이터를 numpy 배열로 변환
    np_arr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    
    # 감정 분석
    try:
        analysis = DeepFace.analyze(img, actions=['emotion'], enforce_detection=False)
        emotion = analysis[0]['dominant_emotion']
        print(f"Detected emotion: {emotion}")
    except Exception as e:
        print(f"Error analyzing image: {e}")
        emotion = "unknown"

    # 감정이 변경되었을 경우에만 전송
    if emotion != previous_emotion:
        previous_emotion = emotion  # 이전 감정을 업데이트
        print(f"Emotion changed to: {emotion}. Sending to Raspberry Pi...")
        emit('emotion_result', {'emotion': emotion})
    else:
        print(f"Emotion ({emotion}) is unchanged. Not sending.")

# 기본 라우트
@app.route('/')
def index():
    return "Emotion Detection Server is running"

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
