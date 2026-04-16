import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

LLM_MODEL = "gemini-2.5-flash-lite"  
EMBEDDING_MODEL = "gemini-embedding-2-preview"

TOP_K = 15
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 50