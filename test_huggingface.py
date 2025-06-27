import requests
import os
from dotenv import load_dotenv

# Load your .env file
load_dotenv()

huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY")

headers = {
    "Authorization": f"Bearer {huggingface_api_key}",
    "Content-Type": "application/json"
}

payload = {
    "inputs": "Hello! Can you introduce yourself?"
}

response = requests.post("https://api-inference.huggingface.co/models/distilgpt2", headers=headers, json=payload)

# First print the raw response
print(f"Status Code: {response.status_code}")
print(f"Raw Text: {response.text}")

# Only try to parse JSON if server responded correctly
if response.status_code == 200:
    print(response.json())
else:
    print("Failed to get valid JSON response.")
