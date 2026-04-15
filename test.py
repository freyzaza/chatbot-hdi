from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize the client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Generate content
response = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents="Halo, ini test"
)

print(response.text)