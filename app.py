# # .\venv\Scripts\activate
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_session import Session
import os
import json
from dotenv import load_dotenv
from message_handler import handle_message
import pyttsx3
from message_handler import set_mute, get_mute
# from message_handler import engine

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Dummy user system
users = {
    'admin': 'admin123',
    'test': 'test123'
}

# Text-to-speech
# def speechtx(text):
#     global engine
#     try:
#         # engine = pyttsx3.init()
#         voice = engine.getProperty('voices')
#         engine.setProperty('voice', voice[1].id)
#         engine.setProperty('rate', 150)
#         engine.say(text)
#         engine.runAndWait()
#         # engine.stop()
#         engine = None
#     except RuntimeError as e:
#         print(f"Speech engine error: {e}")
def speechtx(text):
    from message_handler import get_mute
    if get_mute():
        print(" Mute is ON — skipping speech.")
        return

    try:
        local_engine = pyttsx3.init()  #  create engine fresh per call
        voice = local_engine.getProperty('voices')
        local_engine.setProperty('voice', voice[1].id)
        local_engine.setProperty('rate', 150)
        local_engine.say(text)
        local_engine.runAndWait()
        local_engine.stop()
        print(" Speech done.")
    except RuntimeError as e:
        print(" Speech engine error:", e)




# ---------------- Routes ----------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['user'] = username
            return redirect(url_for('home'))
        else:
            return "Invalid Credentials! Please try again."
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        new_username = request.form['username']
        new_password = request.form['password']
        if new_username in users:
            return "Username already exists. Please choose another."
        users[new_username] = new_password
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/')
def home():
    if 'user' in session:
        return render_template('index.html')
    else:
        return redirect(url_for('login'))

@app.route('/api/message', methods=['POST'])
def message():
    if 'user' not in session:
        return jsonify({'response': 'Unauthorized! Please login first.'}), 401
    user_message = request.json['message']
    response_message = handle_message(user_message, speechtx)
    return jsonify({'response': response_message})

#  Toggle Model API (for UI switch)
@app.route('/api/switch_model', methods=['POST'])
def switch_model():
    try:
        with open("settings.json", "r+") as f:
            settings = json.load(f)
            current = settings.get("use_huggingface", True)
            settings["use_huggingface"] = not current
            f.seek(0)
            json.dump(settings, f, indent=4)
            f.truncate()
        return jsonify({"use_huggingface": not current})
    except Exception as e:
        print("Failed to toggle model:", e)
        return jsonify({"error": "Toggle failed"}), 500
from message_handler import set_knowledge_mode

@app.route('/api/toggle_knowledge', methods=['POST'])
def toggle_knowledge():
    is_on = request.json.get('on', False)
    set_knowledge_mode(is_on)
    return jsonify({'knowledge_mode': is_on})
# @app.route('/api/stop_speech', methods=['POST'])
# def stop_speech():
#     from message_handler import engine
#     try:
#         if engine:
#             engine.stop()
#         return jsonify({"status": "stopped"})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

@app.route('/api/stop_speech', methods=['POST'])
def stop_speech():
    try:
        # No direct speech engine to stop — handled in speech queue now
        return jsonify({"status": "speech stop simulated"})
    except Exception as e:
        print("Failed to stop speech:", e)
        return jsonify({"error": str(e)}), 500



# ---------------- Run ----------------
if __name__ == '__main__':
    app.run(debug=True)
