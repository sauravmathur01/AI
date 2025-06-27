import pyttsx3
import datetime

# Initialize Text-to-Speech engine

engine = pyttsx3.init()

# Get a list of available voices

voices = engine.getProperty('voices')

# Select the voice

engine.setProperty('voice', voices[1].id)

# Adjust the speed of speech

engine.setProperty('rate', 150)

def speak(audio):

    # Speak the given audio 
    
    engine.say(audio)
    
    # Run the speech conversion
    
    engine.runAndWait()

def greetMe():
    
    # Get the current hour
    
    current_time = datetime.datetime.now().hour
    
    # Greet the user based on the current time
    
    if 0 <= current_time < 12:
        
        speak("Good morning!")
        
    elif 12 <= current_time < 18:
        
        speak("Good afternoon!")
        
    else:
        
        speak("Good evening!")

        speak("Please tell me, how can I help you?")

