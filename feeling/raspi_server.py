from flask import Flask, request, jsonify
import RPi.GPIO as GPIO
app = Flask(__name__)

# GPIO 핀 설정
GPIO.setmode(GPIO.BCM)  # BCM 모드 사용
emotion_pins = {
    "angry": 17,       # Angry -> GPIO 17
    "disgust": 18,     # Disgust -> GPIO 18
    "fear": 27,        # Fear -> GPIO 27
    "happy": 22,       # Happy -> GPIO 22
    "sad": 23,         # Sad -> GPIO 23
    "surprise": 24,    # Surprise -> GPIO 24
    "neutral": 25      # Neutral -> GPIO 25
}

# GPIO 핀 초기화
for pin in emotion_pins.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)  # 모든 핀 LOW로 초기화

@app.route('/update_emotion', methods=['POST'])
def update_emotion():
    data = request.json  # JSON 데이터 받기
    emotion = data.get('emotion')
    confidence = data.get('confidence')

     # 모든 핀 LOW로 초기화
    for pin in emotion_pins.values():
        GPIO.output(pin, GPIO.LOW)

    # 받은 감정에 따라 해당 핀 HIGH 설정
    if emotion in emotion_pins:
        GPIO.output(emotion_pins[emotion], GPIO.HIGH)
        print(f"GPIO {emotion_pins[emotion]} set to HIGH for emotion: {emotion}")
    else:
        print(f"Unknown emotion: {emotion}")

    return jsonify({"status": "success", "message": f"Emotion '{emotion}' updated"})


if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)  # Flask 서버 실행
    except KeyboardInterrupt:
        print("Server stopped.")
    finally:
        GPIO.cleanup()  # GPIO 핀 정리
