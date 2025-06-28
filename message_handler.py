print("✅ message_handler.py loaded from:", __file__)

import datetime
import json
import pyjokes
import webbrowser
import random
import os
import requests
import time
import wikipedia
import pyttsx3
import json
import threading
import pyttsx3
from dotenv import load_dotenv
from transformers import pipeline, Conversation
import wikipedia

# === Load environment variables ===
load_dotenv()
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# === Load default settings ===
SETTINGS_FILE = "settings.json"

def load_settings():
    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"mute": False, "use_huggingface": True}

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

# === Global settings state ===
settings = load_settings()

# === Helper: Async Text-to-Speech ===
def speak_async(text):
    if get_mute():
        print("🔇 Mute is ON, skipping speech")
        return

    def tts_worker():
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            engine.setProperty('voice', engine.getProperty('voices')[1].id)
            engine.say(text)
            engine.runAndWait()
        except RuntimeError as e:
            print("❌ TTS Error:", e)

    threading.Thread(target=tts_worker).start()

# === Mute and Knowledge Mode Handlers ===
def get_mute():
    return settings.get("mute", False)

def set_mute(value: bool):
    settings["mute"] = value
    save_settings(settings)

def set_knowledge_mode(value: bool):
    settings["use_huggingface"] = value
    save_settings(settings)

# === Custom NLP Logic ===
def extract_after_keyword(text, keyword):
    import re
    match = re.search(f"{keyword}\\s*(.*)", text, re.IGNORECASE)
    return match.group(1).strip().replace(".", "") if match else None

# === Response Dispatcher ===
def handle_message(user_message: str, speak_fn=None) -> str:
    user_prompt = user_message.lower().strip()

    # Basic Responses
    if "hello" in user_prompt:
        return speak_and_return("Hello! How can I help you today?", speak_fn)

    if "your name" in user_prompt:
        return speak_and_return("I'm ZAX, your AI assistant!", speak_fn)

    if "good morning" in user_prompt:
        return speak_and_return("Good morning! Have a great day!", speak_fn)

    if "good night" in user_prompt:
        return speak_and_return("Good night. Sweet dreams!", speak_fn)

    # Name & Mood Extraction
    if "my name is" in user_prompt:
        name = extract_after_keyword(user_message, "my name is")
        if name:
            return speak_and_return(f"Nice to meet you, {name}!", speak_fn)

    if "feeling" in user_prompt:
        mood = extract_after_keyword(user_message, "feeling")
        if mood:
            return speak_and_return(f"I'm here for you. You said you're feeling {mood}.", speak_fn)

    # Wikipedia Mode
    if settings.get("use_huggingface") is False:
        return get_wikipedia_summary(user_prompt, speak_fn)

    # HuggingFace Conversational Model
    return get_huggingface_response(user_prompt, speak_fn)

# === HuggingFace Chatbot ===
def get_huggingface_response(prompt, speak_fn=None):
    try:
        chatbot = pipeline("conversational", model="microsoft/DialoGPT-medium")
        conversation = Conversation(prompt)
        response = chatbot(conversation)
        reply = str(response.generated_responses[-1])
        if speak_fn:
            speak_fn(reply)
        return reply
    except Exception as e:
        print("⚠️ HF model failed, switching to Wikipedia fallback:", e)
        return get_wikipedia_summary(prompt, speak_fn)

# === Wikipedia Fallback ===
def get_wikipedia_summary(query, speak_fn=None):
    try:
        summary = wikipedia.summary(query, sentences=2)
        if speak_fn:
            speak_fn(summary)
        return summary
    except Exception as e:
        print("⚠️ Wikipedia error:", e)
        fallback = "Sorry, I couldn't find anything relevant right now."
        if speak_fn:
            speak_fn(fallback)
        return fallback

# === Combined Speak + Return Shortcut ===
def speak_and_return(msg: str, speak_fn=None) -> str:
    if speak_fn:
        speak_fn(msg)
    return msg

import queue
import threading
from dotenv import load_dotenv
from transformers import pipeline, Conversation

# ---------------- Global State ----------------
is_muted = False
knowledge_mode = False
memory = {}  # For name/mood memory

# ---------------- Mute Settings ----------------
def set_mute(on: bool):
    try:
        if not os.path.exists("settings.json"):
            with open("settings.json", "w") as f:
                json.dump({"is_muted": False}, f)
        with open("settings.json", "r+") as f:
            settings = json.load(f)
            settings["is_muted"] = on
            f.seek(0)
            json.dump(settings, f, indent=4)
            f.truncate()
    except Exception as e:
        print("Failed to save mute:", e)

def get_mute():
    try:
        with open("settings.json", "r") as f:
            settings = json.load(f)
            return settings.get("is_muted", False)
    except:
        return False

def set_knowledge_mode(on):
    global knowledge_mode
    knowledge_mode = on

# ---------------- Load API Keys ----------------
load_dotenv()
huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY")
local_chatbot = pipeline("conversational", model="microsoft/DialoGPT-medium")

# ---------------- Speech Queue System ----------------
speech_queue = queue.Queue()

def speech_worker():
    engine = pyttsx3.init()
    voice = engine.getProperty('voices')
    engine.setProperty('voice', voice[1].id)
    engine.setProperty('rate', 150)
    while True:
        text = speech_queue.get()
        if text is None:
            break
        if not get_mute():
            try:
                engine.say(text)
                engine.runAndWait()
                print("🔊 Spoke:", text)
            except Exception as e:
                print("❌ Speech engine error in thread:", e)
        speech_queue.task_done()

speech_thread = threading.Thread(target=speech_worker, daemon=True)
speech_thread.start()

# ---------------- Response Helpers ----------------
def speak_async(text):
    speech_queue.put(text)

def get_huggingface_response(user_prompt):
    API_URL = "https://api-inference.huggingface.co/models/facebook/blenderbot-1B-distill"
    print("📡 Using URL:", API_URL)
    headers = {
        "Authorization": f"Bearer {huggingface_api_key}",
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
    retries = 2
    for attempt in range(retries):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=6)
            response.raise_for_status()
            result = response.json()
            if isinstance(result, list) and 'generated_text' in result[0]:
                print("🔵 Using Hugging Face API")
                return result[0]['generated_text'].strip()
        except Exception as e:
            print(f"⚠️ Hugging Face error: {e}")
            if attempt < retries - 1:
                time.sleep(1)
    print("🟡 Falling back to local DialoGPT...")
    try:
        convo = Conversation(user_prompt)
        result = local_chatbot(convo)
        return str(result.generated_responses[-1])
    except Exception as fallback_error:
        print("❌ Local model failed:", fallback_error)
        return "I'm having trouble understanding right now. Please try again later."

def get_wikipedia_answer(query):
    try:
        summary = wikipedia.summary(query, sentences=2)
        page = wikipedia.page(query)
        if any(phrase in summary.lower() for phrase in ['this is a list', 'refer to', 'may refer to']):
            summary += "\n\n(For full details, see the article below.)"
        # summary += f"\n\n<a href='{page.url}' target='_blank'>{page.url}</a>"
        # summary += f"\n\nRead more: <a href='{page.url}' target='_blank'>{page.url}</a>"
        summary += f"\n\n[LINK]{page.url}"
        return summary



        return summary
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Your question is ambiguous. Try something more specific like: {e.options[0]}"
    except wikipedia.exceptions.PageError:
        return "I couldn't find any relevant information on that please be precise."

# ---------------- Main Message Handler ----------------
def handle_message(user_message, speechtx):
    global memory
    response_message = ""

    if "my name is" in user_message.lower():
        name = user_message.split("is")[-1].strip().replace(".", "")
        memory['name'] = name
        response_message = f"Nice to meet you, {name}!"

    elif "i am feeling" in user_message.lower():
        mood = user_message.split("feeling")[-1].strip().replace(".", "")
        memory['mood'] = mood
        response_message = f"I'm sorry you're feeling {mood}. I'm always here if you want to talk!"

    elif "what's my name" in user_message.lower() or "what is my name" in user_message.lower():
        response_message = f"Your name is {memory['name']}!" if 'name' in memory else "I don't know your name yet. Tell me by saying 'My name is...'."

    elif "how am i feeling" in user_message.lower():
        response_message = f"You told me you're feeling {memory['mood']}." if 'mood' in memory else "You haven't told me how you're feeling yet."

    elif "your name" in user_message:
        response_message = "My name is Zax, what can I help you with?"

    elif "who are you" in user_message:
        response_message = "I'm an AI assistant, and I don't have personal experiences or feelings."

    elif "hey" in user_message.lower() or "hello" in user_message.lower():
        response_message = random.choice(["Hey there!", "Hello!", "Hi! How can I assist?", "Greetings!", "Yo! How's it going?"])

    elif "who is Bihari" in user_message:
        response_message = "Sourabh is Bihari."

    elif "who created you" in user_message:
        response_message = "I was created by a team of programmers and researchers."

    elif "old are you" in user_message:
        response_message = "I'm a simple AI assistant; I don't have an age."

    elif "how are you" in user_message:
        response_message = "I'm doing well, thank you for asking. What can I help you with?"

    elif "joke" in user_message:
        response_message = pyjokes.get_joke(language="en", category="neutral")
        speak_async(response_message)
        return response_message

    elif "time" in user_message:
        response_message = f"The current time is {datetime.datetime.now().strftime('%H:%M:%p')}"
        speak_async(response_message)
        return response_message

    elif "teammates" in user_message:
        response_message = "Our team members are Sourabhh, Sanskriti, Shubhiii, Ratnesh, Shivani, and of course me, Zax."
        speak_async(response_message)
        return response_message

    elif "morning" in user_message:
        response_message = "Good morning! Have a great day!"
        speak_async(response_message)
        return response_message

    elif "evening" in user_message:
        response_message = "Good evening! Hope you had a great day!"
        speak_async(response_message)
        return response_message

    elif "night" in user_message:
        response_message = "Good night! Sweet dreams!"
        speak_async(response_message)
        return response_message

    elif "introduce" in user_message or "introduced yourself" in user_message:
        response_message = "I'm Zax, your AI assistant. I'm here to make your life easier."
        speak_async(response_message)
        return response_message

    elif "afternoon" in user_message:
        response_message = "Good afternoon! Hope your day is going great!"
        speak_async(response_message)
        return response_message

    elif "youtube" in user_message.lower():
        response_message = "Opening YouTube."
        webbrowser.open("https://www.youtube.com")

    elif "google" in user_message.lower():
        response_message = "Opening Google."
        webbrowser.open("https://www.google.com")

    elif 'play song' in user_message:
        response_message = "Playing your song."
        webbrowser.open("https://www.youtube.com/watch?v=8LZgzAZ2lpQ")

    elif "turn off" in user_message:
        response_message = "Microphone turned off."

    elif "bye" in user_message:
        response_message = "Thank you for using my AI Assistant. Goodbye!"

    else:
        response_message = get_wikipedia_answer(user_message) if knowledge_mode else get_huggingface_response(user_message)

    # 🎯 If it's a Wikipedia response, speak only the summary but show clickable link in chat
    if knowledge_mode and "[LINK]" in response_message:
        # Speak only the summary + "Read more"
        spoken_part = response_message.split("[LINK]")[0].strip() + " Click link to read more."
        speak_async(spoken_part)

        # Show clickable anchor in chat
        url = response_message.split("[LINK]")[-1].strip()
        response_message = response_message.replace(f"[LINK]{url}", f"<a href='{url}' target='_blank'>Read more</a>")
    else:
        speak_async(response_message)

    return response_message
