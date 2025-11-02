from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

r = client.chat.completions.create(
    model="llama-3.1-8b-instant",   # ← updated model ID
    messages=[{"role": "user", "content": "Say OK"}],
    max_tokens=5,
)
print(r.choices[0].message.content)
