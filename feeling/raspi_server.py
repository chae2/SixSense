from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/update_emotion', methods=['POST'])
def update_emotion():
    data = request.json  # JSON 데이터 받기
    emotion = data.get('emotion')
    confidence = data.get('confidence')

    # 받은 표정 데이터 출력
    print(f"Emotion: {emotion}, Confidence: {confidence}")
    
    return jsonify({"status": "success", "message": "Emotion updated"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # 5000 포트로 서버 실행
