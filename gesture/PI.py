import socket
import pyttsx3
from picamera2 import Picamera2
import cv2

# TTS
engine = pyttsx3.init()

# socket
LOCAL_HOST = '로컬_PC_IP'  # Local PC IP address
LOCAL_PORT = 65432

def send_video_to_local():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((LOCAL_HOST, LOCAL_PORT))
        with Picamera2() as camera:
            camera.configure(camera.create_video_configuration(main={"size": (640, 480)}))
            camera.start()
            try:
                while True:
                    frame = camera.capture_array()
                    _, buffer = cv2.imencode('.jpg', frame)
                    client_socket.sendall(buffer.tobytes())
            except KeyboardInterrupt:
                camera.stop()

def receive_gesture_from_local():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(('0.0.0.0', LOCAL_PORT + 1))
        server_socket.listen(1)
        print(f"TTS Server waiting on PORT {LOCAL_PORT + 1}...")
        conn, _ = server_socket.accept()
        with conn:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                gesture = data.decode('utf-8')
                print(f"Received Gesture: {gesture}")
                engine.say(gesture)
                engine.runAndWait()

if __name__ == "__main__":
    from threading import Thread

    video_thread = Thread(target=send_video_to_local)
    gesture_thread = Thread(target=receive_gesture_from_local)

    video_thread.start()
    gesture_thread.start()

    video_thread.join()
    gesture_thread.join()
