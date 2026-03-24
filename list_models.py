import os
from google import genai
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("Available models:")
for model in client.models.list():
    print(f"- {model.name} (supported actions: {model.supported_generation_methods})")
