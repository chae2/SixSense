import cv2
import socket

def send_video_to_local():
    cap = cv2.VideoCapture(0) # pi cam
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('LOCAL_IP', 9999))
    
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            _,buffer = cv2.imencode('.jpg', frame)
            client_socket.sendall(buffer.tobytes())
    
    finally:
        cap.release()
        client_socket.close()

if __name__=="__main__":
    send_video_to_local()