print("✅ message_handler.py loaded from:", __file__)

import datetime
import json
import os
import queue
import random
import threading
import time
import webbrowser
import requests
import wikipedia
import pyttsx3
import pyjokes
from dotenv import load_dotenv
from transformers import pipeline, Conversation

# === Load environment variables ===
load_dotenv()
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# === Global Settings File ===
SETTINGS_FILE = "settings.json"

def load_settings():
    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"mute": False, "use_huggingface": True, "is_muted": False}

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

# === Global state ===
settings = load_settings()
memory = {}
speech_queue = queue.Queue()

# === Async TTS ===
def speak_async(text):
    if get_mute():
        print("🔇 Mute is ON, skipping speech")
        return
    speech_queue.put(text)

def speech_worker():
    engine = pyttsx3.init()
    voice = engine.getProperty('voices')
    engine.setProperty('voice', voice[1].id)
    engine.setProperty('rate', 150)
    while True:
        text = speech_queue.get()
        if text is None:
            break
        try:
            engine.say(text)
            engine.runAndWait()
            print("🔊 Spoke:", text)
        except Exception as e:
            print("❌ Speech engine error in thread:", e)
        speech_queue.task_done()

threading.Thread(target=speech_worker, daemon=True).start()

# === Mute & Knowledge Mode ===
def set_mute(on: bool):
    settings["is_muted"] = on
    save_settings(settings)

def get_mute():
    return settings.get("is_muted", False)

def set_knowledge_mode(on: bool):
    settings["use_huggingface"] = not on
    save_settings(settings)

def get_knowledge_mode():
    return not settings.get("use_huggingface", True)

# === NLP Helpers ===
def extract_after_keyword(text, keyword):
    import re
    match = re.search(f"{keyword}\\s*(.*)", text, re.IGNORECASE)
    return match.group(1).strip().replace(".", "") if match else None

# === Wikipedia ===
def get_wikipedia_answer(query):
    try:
        summary = wikipedia.summary(query, sentences=2)
        page = wikipedia.page(query)
        summary += f"\n\n[LINK]{page.url}"
        return summary
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Your question is ambiguous. Try something more specific like: {e.options[0]}"
    except wikipedia.exceptions.PageError:
        return "I couldn't find any relevant information on that. Please be more specific."

# === Hugging Face API ===
def get_huggingface_response(user_prompt):
    API_URL = "https://api-inference.huggingface.co/models/facebook/blenderbot-1B-distill"
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": user_prompt,
        "parameters": {
            "max_new_tokens": 100,
            "temperature": 0.7,
            "top_p": 0.9
        }
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=6)
        response.raise_for_status()
        result = response.json()
        if isinstance(result, dict) and 'generated_text' in result:
            return result['generated_text'].strip()
        if isinstance(result, list) and 'generated_text' in result[0]:
            return result[0]['generated_text'].strip()
    except Exception as e:
        print("⚠️ Hugging Face API failed:", e)
        # fallback to local model
        try:
            chatbot = pipeline("conversational", model="microsoft/DialoGPT-medium")
            convo = Conversation(user_prompt)
            chatbot([convo])
            return convo.generated_responses[-1]
        except Exception as fallback_error:
            print("❌ Local model fallback failed:", fallback_error)
            return "I'm having trouble understanding right now. Please try again later."

# === Combined Response ===
def handle_message(user_message, speak_fn):
    user_prompt = user_message.lower().strip()

    if "my name is" in user_prompt:
        name = extract_after_keyword(user_prompt, "my name is")
        if name:
            memory['name'] = name
            msg = f"Nice to meet you, {name}!"
            speak_async(msg)
            return msg

    if "i am feeling" in user_prompt:
        mood = extract_after_keyword(user_prompt, "feeling")
        if mood:
            memory['mood'] = mood
            msg = f"I'm sorry you're feeling {mood}. I'm always here if you want to talk!"
            speak_async(msg)
            return msg

    if "what's my name" in user_prompt:
        msg = memory.get('name', "I don't know your name yet. Tell me by saying 'My name is ...'")
        speak_async(msg)
        return f"Your name is {msg}" if 'name' in memory else msg

    if "how am i feeling" in user_prompt:
        msg = memory.get('mood', "You haven't told me how you're feeling yet.")
        speak_async(msg)
        return msg

    if "joke" in user_prompt:
        msg = pyjokes.get_joke(language="en", category="neutral")
        speak_async(msg)
        return msg

    if "time" in user_prompt:
        msg = f"The current time is {datetime.datetime.now().strftime('%H:%M %p')}"
        speak_async(msg)
        return msg

    if "youtube" in user_prompt:
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube."

    if "google" in user_prompt:
        webbrowser.open("https://www.google.com")
        return "Opening Google."

    if "play song" in user_prompt:
        webbrowser.open("https://www.youtube.com/watch?v=8LZgzAZ2lpQ")
        return "Playing your song."

    if "bye" in user_prompt:
        msg = "Thank you for using my AI Assistant. Goodbye!"
        speak_async(msg)
        return msg

    # Wikipedia fallback
    if get_knowledge_mode():
        result = get_wikipedia_answer(user_prompt)
        if "[LINK]" in result:
            url = result.split("[LINK]")[-1].strip()
            msg = result.split("[LINK]")[0].strip() + " Click link to read more."
            speak_async(msg)
            return result.replace(f"[LINK]{url}", f"<a href='{url}' target='_blank'>Read more</a>")
        speak_async(result)
        return result

    # Hugging Face mode
    result = get_huggingface_response(user_prompt)
    speak_async(result)
    return result
