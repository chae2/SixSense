from flask import Flask, request, jsonify
import pyttsx3

app = Flask(__name__)
engine = pyttsx3.init()
voices = engine.getProperty('voices')

for voice in voices:
    if 'Korean' in voice.name or '한국어' in voice.name:
        engine.setProperty('voice', voice.id)
        break

emotion_data = None
gesture_data = None

@app.route('/detect_gesture', methods=['POST'])
def update_gesture():
    global gesture_data
    data = request.json  # JSON 데이터 받기
    gesture = data.get('gesture')

    # 제스처 데이터가 들어왔을 때, 우선적으로 표정 데이터가 있으면 표정을 먼저 출력하고
    # 그 후 제스처를 음성으로 출력
    if emotion_data:
        engine.say(f"The detected emotion is {emotion_data}")  # 표정 출력
        engine.runAndWait()
    if gesture_data:
        engine.say(f"The detected gesture is {gesture_data}")  # 제스처 출력
        engine.runAndWait()
    
    return jsonify({"status": "success", "message": "Gesture Detected."})

# 표정 업데이트 엔드포인트
@app.route('/update_emotion', methods=['POST'])
def update_emotion():
    global emotion_data
    data = request.get_json()

    # 표정 정보 받기
    emotion_data = data.get('emotion', 'Unknown')

    if emotion_data:
        print(f"Received emotion: {emotion_data}")
        
        # 표정에 대한 음성출력 먼저
        engine.say(f"The detected emotion is {emotion_data}")
        engine.runAndWait()
        
        # 응답을 보내기 전에 음성 출력 완료
        return jsonify({"status": "success", "emotion": emotion_data}), 200
    else:
        return jsonify({"status": "failure", "message": "No emotion data received."}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # 5000 포트로 서버 실행
