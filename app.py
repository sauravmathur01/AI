from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_session import Session
import os, json
import pyttsx3
from dotenv import load_dotenv
from message_handler import handle_message, set_mute, get_mute, set_knowledge_mode

# Load env vars
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "123abc")
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Dummy user data
users = {'admin': 'admin123', 'test': 'test123'}

# TTS

def speak(text):
    if get_mute(): return
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[1].id)
        engine.setProperty('rate', 150)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print("TTS Error:", e)

# Auth routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form['username'], request.form['password']
        if users.get(u) == p:
            session['user'] = u
            return redirect(url_for('home'))
        return "Invalid credentials"
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        u, p = request.form['username'], request.form['password']
        if u in users:
            return "Username already exists"
        users[u] = p
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# Main routes
@app.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/api/message', methods=['POST'])
def message():
    if 'user' not in session:
        return jsonify({'response': 'Unauthorized'}), 401
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing data'}), 400
    user_msg = data.get('message', '')
    bot_reply = handle_message(user_msg, speak)
    return jsonify({'response': bot_reply})

@app.route('/api/switch_model', methods=['POST'])
def switch_model():
    try:
        with open("settings.json", "r+") as f:
            settings = json.load(f)
            settings["use_huggingface"] = not settings.get("use_huggingface", True)
            f.seek(0)
            json.dump(settings, f, indent=4)
            f.truncate()
        return jsonify({"use_huggingface": settings["use_huggingface"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/toggle_knowledge', methods=['POST'])
def toggle_knowledge():
    data = request.get_json()
    mode = data.get('on', False)
    set_knowledge_mode(mode)
    return jsonify({'knowledge_mode': mode})

@app.route('/api/toggle_mute', methods=['POST'])
def toggle_mute():
    data = request.get_json()
    mute_on = data.get('on', False)
    set_mute(mute_on)
    return jsonify({'mute': mute_on})

@app.route('/api/get_mute', methods=['GET'])
def get_mute_state():
    return jsonify({'muted': get_mute()})

@app.route('/api/stop_speech', methods=['POST'])
def stop_speech():
    return jsonify({"status": "TTS stopped"})

if __name__ == '__main__':
    app.run(debug=True)
