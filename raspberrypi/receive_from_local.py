import socket
import pyttsx3

def receive_from_local():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('LOCAL_IP', 9999))
    engine = pyttsx3.init()

    try:
        while True:
            result = client_socket.recv(1024).decode
            if result:
                print(f"result: {result}")
                engine.say(result)
                engine.runAndWait()
            else:
                break
    finally:
        client_socket.close()

if __name__=="__main__":
    receive_from_local()