from flask import Flask, request, jsonify
import pyttsx3

app = Flask(__name__)
engine = pyttsx3.init()
voices = engine.getProperty('voices')

for voice in voices:
    if 'Korean' in voice.name or '한국어' in voice.name:
        engine.setProperty('voice', voice.id)
        break

@app.route('/detect_gesture', methods=['POST'])
def update_emotion():
    data = request.json  # JSON 데이터 받기
    gesture = data.get('gesture')

    # 받은 표정 데이터 출력
    print(f"Gesture: {gesture}")
    # 음성출력
    engine.say(gesture)
    engine.runAndWait()
    
    return jsonify({"status": "success", "message": "Gesture Detected."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # 5000 포트로 서버 실행
