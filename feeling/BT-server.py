# Bluetooth 서버 코드 (라즈베리파이)
from bluetooth import *
import requests

# Bluetooth 연결
server_socket = BluetoothSocket(RFCOMM)
port = 1
server_socket.bind(("", port))
server_socket.listen(3)
print("Bluetooth server is running...")

client_socket, address = server_socket.accept()
print("Accepted connection from ", address)

client_socket.send("Bluetooth connected!")

while True:
    data = client_socket.recv(1024)
    print("Received:", data)

    if data:  # 값이 들어오면
        # 노트북 서버에 요청 (Flask 서버로 요청)
        response = requests.get('http://172.20.10.5:5000/get_current_emotion')  # 표정 감지 요청
        emotion_data = response.json()  # 표정 감지 결과 받기

        # 표정 감지 결과를 Bluetooth로 전송
        client_socket.send(str(emotion_data))

    if data == "q":  # 종료 조건
        break

client_socket.close()
server_socket.close()
