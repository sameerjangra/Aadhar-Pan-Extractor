import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ.get("GROQ_API_KEY")
)

try:
    print("Listing available Groq models:")
    models = client.models.list()
    for model in models.data:
        print(f"- {model.id}")
except Exception as e:
    print(f"Error listing models: {e}")
  