from flask import Flask, render_template, request, jsonify
import speech_recognition as sr

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('mic.html')


@app.route('/recognize', methods=["POST"])
def recognize():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("開始說話...")
        audio_data = r.listen(source)  # 使用 listen 自動處理錄音時長

    try:
        text = r.recognize_google(audio_data, language='zh-tw')
        return jsonify({'success': True, 'text': text})
    except sr.UnknownValueError:
        return jsonify({
            'success': False,
            'error': "Google Speech Recognition 未能識別出任何語音"
        })
    except sr.RequestError as e:
        return jsonify({
            'success': False,
            'error': f"無法從 Google Speech Recognition 服務請求結果; {e}"
        })


if __name__ == '__main__':
    app.run(debug=True)
