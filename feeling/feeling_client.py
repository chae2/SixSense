import cv2
import base64
import socketio

# 웹소켓 클라이언트 설정
sio = socketio.Client()

# 서버에 연결
sio.connect("http://<서버_IP>:5000")

# 카메라 초기화
cap = cv2.VideoCapture(0)

# 프레임 캡처 후 웹소켓을 통해 서버로 전송
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

    # 서버로부터 감정 분석 결과 받기
    @sio.event
    def emotion_result(data):
        emotion = data['emotion']
        print(f"Emotion received: {emotion}")

    # 잠시 대기 (프레임 전송 간격)
    cv2.waitKey(1)

cap.release()
