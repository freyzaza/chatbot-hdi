from google import genai
from config import GOOGLE_API_KEY, LLM_MODEL

# 1. Inisialisasi client
client = genai.Client(api_key=GOOGLE_API_KEY)

# 2. Simpan konfigurasi dalam dict agar bisa digunakan berulang (opsional tapi rapi)
CONFIG = {
    "temperature": 0.3,
    "max_output_tokens": 2048,
}

def generate_answer(prompt):
    # Panggil generate_content melalui client.models
    response = client.models.generate_content(
        model=LLM_MODEL,
        contents=prompt,
        config=CONFIG # Masukkan konfigurasi di sini
    )

    try:
        return response.text
    except Exception:
        # Fallback jika .text gagal (biasanya karena safety filters)
        return response.candidates[0].content.parts[0].text
