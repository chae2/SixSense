#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ESP8266_ISR_Servo.h> // ESP8266 전용 ISR Servo 라이브러리

// Wi-Fi 설정
const char* ssid = "il's back spine";       // Wi-Fi SSID
const char* password = "mci1309!"; // Wi-Fi 비밀번호

// HTTP 서버 초기화
ESP8266WebServer server(80);

// 서보 핀 설정
int servo1Pin = D5; // 서보 1 신호 핀
int servo2Pin = D6; // 서보 2 신호 핀
int servo3Pin = D7; // 서보 3 신호 핀

// 서보 핸들러
int servo1Index = -1;
int servo2Index = -1;
int servo3Index = -1;

int servoList[3] = {0}; // 서보 1, 2, 3에 대한 리스트
char servoIndexList[3] = {};

void handleRoot() {
  server.send(200, "text/plain", "Welcome to the Servo Control Server!");
}

void controlServo() {
  // url = /servo?s1=1&s2=0&s3=0
  if (server.hasArg("s1") && server.hasArg("s2") && server.hasArg("s3")){
    servoList[0] = server.arg("s1").toInt();
    servoList[1] = server.arg("s2").toInt();
    servoList[2] = server.arg("s3").toInt();

    servoIndexList[0] = servo1Index;
    servoIndexList[1] = servo2Index;
    servoIndexList[2] = servo3Index;
    
    // 유효한 값 확인 (0 또는 1만 허용)
    for (int i = 0; i < 3; i++) {
      if (servoList[i] < 0 || servoList[i] > 1) {
        server.send(400, "text/plain", "Servo value must be 0 or 1.");
        return;
      }
    }

    for (int i=0; i<3; i++){
      int servoIndex = servoIndexList[i];
      if (i==2){
        switch(servoList[i]){
          case 0:
            ISR_Servo.setPosition(servoIndex, 90);
            break;
          case 1:
            ISR_Servo.setPosition(servoIndex, 180);
            break;
        }
      } else{
        switch(servoList[i]){
          case 0:
            ISR_Servo.setPosition(servoIndex, 180);
            break;
          case 1:
            ISR_Servo.setPosition(servoIndex, 90);
            break;
        }
      
      }
    }
    server.send(200, "text/plain", "Servo positions updated.");
  } else {
    server.send(400, "text/plain", "Invalid parameters. Use /servo?s1=<num>&s2=<num>&s3=<num>");
  }
}

void setup() {
  // 시리얼 통신 초기화
  Serial.begin(115200);
  Serial.println();

  // Wi-Fi 연결 시도
  Serial.print("Connecting to Wi-Fi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }

  // 연결 성공 메시지 및 IP 출력
  Serial.println();
  Serial.println("Wi-Fi Connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  // HTTP 서버 설정
  server.on("/", handleRoot); // 기본 페이지
  server.on("/servo", controlServo); // 서보 제어 경로
  server.begin();
  Serial.println("HTTP server started");

  // 서보 핸들러 생성
  servo1Index = ISR_Servo.setupServo(servo1Pin, 0);
  servo2Index = ISR_Servo.setupServo(servo2Pin, 90);
  servo3Index = ISR_Servo.setupServo(servo3Pin, 180);

  if (servo1Index == -1 || servo2Index == -1 || servo3Index == -1) {
    Serial.println("Servo setup failed! Check pins or servo library limits.");
    while (true);
  }
  delay(1000);
  ISR_Servo.setPosition(servo1Index, 180);
  ISR_Servo.setPosition(servo2Index, 180);
  ISR_Servo.setPosition(servo3Index, 90);

  delay(1000); // 초기화 대기
}

void loop() {
  server.handleClient(); // HTTP 요청 처리
}
