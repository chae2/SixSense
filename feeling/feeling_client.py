import cv2
import base64
import socketio
import RPi.GPIO as GPIO
import time

# GPIO 설정
GPIO.setmode(GPIO.BCM)  # BCM 핀 번호 사용
GPIO.setwarnings(False)

# 감정별 GPIO 핀 매핑
emotion_to_pin = {
    'angry': 17,     # GPIO 17번 핀
    'disgust': 27,   # GPIO 27번 핀
    'fear': 22,      # GPIO 22번 핀
    'happy': 23,     # GPIO 23번 핀
    'neutral': 24,   # GPIO 24번 핀
    'sad': 25,       # GPIO 25번 핀
    'surprise': 5    # GPIO 5번 핀
}

# 모든 핀을 출력 모드로 설정하고 초기 상태를 LOW로 설정
for pin in emotion_to_pin.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

# 웹소켓 클라이언트 설정
sio = socketio.Client()

# 서버에 연결
sio.connect("http://<서버_IP>:5000")

# 감정 결과 처리 함수
@sio.event
def emotion_result(data):
    emotion = data['emotion']
    print(f"Emotion received: {emotion}")

    # 모든 핀을 LOW로 초기화
    for pin in emotion_to_pin.values():
        GPIO.output(pin, GPIO.LOW)

    # 감정에 해당하는 핀을 HIGH로 설정
    if emotion in emotion_to_pin:
        pin = emotion_to_pin[emotion]
        GPIO.output(pin, GPIO.HIGH)
        print(f"GPIO {pin} HIGH")
        time.sleep(1)  # 1초 동안 전류를 흘림
        GPIO.output(pin, GPIO.LOW)  # 다시 LOW로 설정
    else:
        print("알 수 없는 감정: ", emotion)

# 카메라 초기화
cap = cv2.VideoCapture(0)

# 프레임 캡처 후 웹소켓을 통해 서버로 전송
try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("카메라에서 프레임을 읽을 수 없습니다.")
            break

        # 이미지를 JPEG로 인코딩
        _, img_encoded = cv2.imencode('.jpg', frame)
        img_bytes = img_encoded.tobytes()

        # 이미지를 Base64로 인코딩하여 전송
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')

        # 서버로 이미지 전송
        sio.emit('upload_image', {'image': img_base64})

        # 잠시 대기 (프레임 전송 간격)
        cv2.waitKey(1)

except KeyboardInterrupt:
    print("프로그램 종료")

finally:
    cap.release()
    GPIO.cleanup()  # GPIO 상태 초기화
