- 전체 동작 구조
  ![image](https://github.com/user-attachments/assets/cb003038-15c2-4fd7-a4af-22ec1f485ee1)

- 개발 목표 및 구현
  시각장애인이 상대의 비언어적인 행동을 소리와 촉각으로 인지할 수 있도록 돕는 커뮤니케이션 도구를 생각해보았습니다!
  - 표정: Deepface를 활용해 7가지 표정을 인식, D1 R2&mini 보드와 서보모터를 활용한 **피드백 보드**로 표시
    - 예시: 표정이 'happy'로 인식된 경우 100, 첫번째 서보모터가 작동하는 방식
  - 제스처: Mediapipe를 활용해 7가지 손 제스처와 3가지 전신 제스처를 인식하여 음성 tts로 전달
- 파일 구조
  - [feeling]
    - laptop_deepface_arduino.py
      - face_recognition을 통해 영상 프레임 속 사람의 얼굴만을 크롭함.
      - Deepface를 활용하여 크롭된 얼굴을 7가지 표정 중 80% 이상의 정확성을 가진 
      - feedback_board.ino에서 생성한 http 서버로 서보모터 값들을 보내 피드백 보드를 작동시키는 역할.
      - 로컬에서 동작.
    - (optional) BT-server.py
      - 피드백 보드를 작동하지 못할 경우, laptop_deepface.py와 BT-server.py를 사용하면, 블루투스를 통해 사용자가 값을 전송할 때마다 음성으로 값이 전달됨.
      - 라즈베리파이에서 동작.
  - [gesture]
    - LOCAL.py
      - 라즈베리파이에서 받은 스트리밍 영상값을 처리함.
      - Mediapipe를 활용하여 10가지 제스처를 인식함.
      - 로컬에서 동작.
    - STREAM.py
      - 로컬에서 받은 값을 플라스크를 통해 라즈베리파이에서 받아 이를 음성 tts로 나타냄.
      - 라즈베리파이에서 동작.
  - [feedback_board]
    - feedback_board.ino: D1 R2&mini 보드에서 작동하여 피드백보드에 사용되는 서보모터를 제어합니다.
    - 로컬에서 동작.
  - streaming.py
    - 라즈베리파이 파이카메라로부터 영상을 받아 스트리밍함.
    - 라즈베리파이에서 동작.

- 작동 매뉴얼
  - 준비물
    - 라즈베리파이4
    - 파이카메라2
    - 스피커(usb와 jack으로 연결)
    - D1 R2&mini 보드
    - D1에 연결된 서보모터 3개 (피드백 보드의 역할 수행)
  - 준비
    1. 라즈베리파이와 로컬 컴퓨터를 네트워크 커넥터로 연결(vnc 뷰어를 이용하면 스트리밍 영상을 실시간으로 볼 수 있음).
    2. 라즈베리파이는 전원을 끈 상태로 파이카메라와 스피커를 연결.
    3. 로컬 컴퓨터와 D1 보드를 usb 커넥터로 연결.
    4. 라즈베리파이와 로컬 컴퓨터가 동일한 네트워크에 접속하도록 설정.
       D1 보드를 같은 wifi로 동작시키기 위해 2.4Ghz의 wifi를 사용하는 것을 권장.
  - 라즈베리파이에서 streaming.py, STREAM.py를 실행.
  - 로컬 컴퓨터에서 laptop_deepface_arduino.py, LOCAL.py, feedback_board.ino를 실행.
  - 파이카메라에 얼굴을 대고 손짓을 하거나 표정을 지으면 음성과 피드백 보드로 출력됨.
