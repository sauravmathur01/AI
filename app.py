from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_session import Session
import os, json
import pyttsx3
from dotenv import load_dotenv

from message_handler import handle_message, set_mute, get_mute, set_knowledge_mode

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "123abc")
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Just testing users for login (not from DB)
users = {'admin': 'admin123', 'test': 'test123'}

# TTS stuff
def speak(text):
    if get_mute(): return
    try:
        e = pyttsx3.init()
        v = e.getProperty('voices')
        e.setProperty('voice', v[1].id)  # female voice
        e.setProperty('rate', 150)
        e.say(text)
        e.runAndWait()
        e.stop()
    except: pass  # ignore TTS errors for now

# -------------- Auth --------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        if users.get(u) == p:
            session['user'] = u
            return redirect(url_for('home'))
        return "Wrong login"
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        if u in users:
            return "Taken"
        users[u] = p
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# -------------- Main Routes --------------

@app.route('/')
def home():
    return render_template('index.html') if 'user' in session else redirect(url_for('login'))

@app.route('/api/message', methods=['POST'])
def message():
    if 'user' not in session: return jsonify({'response': 'Login required'}), 401
    data = request.get_json()
    if not data: return jsonify({'error': 'No data'}), 400
    msg = data.get('message', '')
    reply = handle_message(msg, speak)
    return jsonify({'response': reply})

@app.route('/api/switch_model', methods=['POST'])
def switch_model():
    try:
        f = open("settings.json", "r+")
        s = json.load(f)
        s["use_huggingface"] = not s.get("use_huggingface", True)
        f.seek(0)
        json.dump(s, f, indent=4)
        f.truncate()
        f.close()
        return jsonify({"use_huggingface": s["use_huggingface"]})
    except:
        return jsonify({"error": "fail"}), 500

@app.route('/api/toggle_knowledge', methods=['POST'])
def toggle_knowledge():
    data = request.get_json()
    set_knowledge_mode(data.get('on', False))
    return jsonify({'knowledge_mode': data.get('on', False)})

@app.route('/api/toggle_mute', methods=['POST'])
def toggle_mute():
    data = request.get_json()
    set_mute(data.get('on', False))
    return jsonify({'mute': data.get('on', False)})

@app.route('/api/stop_speech', methods=['POST'])
def stop_speech():
    return jsonify({"status": "tts stop (mock)"})

# -------------- Run --------------
if __name__ == '__main__':
    app.run(debug=True)
