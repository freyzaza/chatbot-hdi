from google import genai
from config import EMBEDDING_MODEL, GOOGLE_API_KEY

# Inisialisasi dengan versi v1beta
client = genai.Client(
    api_key=GOOGLE_API_KEY
)

def get_embedding(text):
    if not text:
        return []

    # Coba gunakan nama model tanpa prefix 'models/' jika masih error
    response = client.models.embed_content(
    model=EMBEDDING_MODEL,
    contents=text
)

    return response.embeddings[0].values