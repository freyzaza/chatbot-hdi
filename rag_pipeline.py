import re
import json
from loader import load_documents, chunk_text
from embedder import get_embedding
from vectordb import VectorDB
from retriever import retrieve
from prompt import build_prompt
from llm import generate_answer
from config import TOP_K, CHUNK_SIZE

# init DB sekali saja
vectordb = VectorDB()

def build_knowledge_base():
    if vectordb.load():
        print("Menggunakan vectordb yang sudah ada")
        return
    
    print("Membangun vectordb baru...")
    docs = load_documents()

    for doc in docs:
        if len(doc) <= CHUNK_SIZE:
            chunks = [doc]
        else:
            chunks = chunk_text(doc)

        for chunk in chunks:
            emb = get_embedding(chunk)
            vectordb.add(chunk, emb)
    
    vectordb.save()


def is_valid_url(url):
    """Cek apakah URL valid (tidak kosong, tidak placeholder, diawali http)"""
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    if url in ("", "url_gambar_produk", "url_halaman_produk", "#", "null", "None"):
        return False
    if not url.startswith("http://") and not url.startswith("https://"):
        return False
    return True


def sanitize_input(text: str) -> str:
    """
    Sanitasi input user untuk memitigasi prompt injection.
    Menghapus / menetralisir pola umum yang digunakan untuk injection.
    """
    if not text or not isinstance(text, str):
        return ""

    # Batasi panjang input agar tidak overflow context
    MAX_INPUT_LENGTH = 1000
    text = text[:MAX_INPUT_LENGTH]

    # Pola-pola prompt injection umum yang perlu dideteksi
    INJECTION_PATTERNS = [
        # Instruksi untuk abaikan prompt sebelumnya
        r"ignore\s+(all\s+)?(previous|prior|above|earlier)\s+instructions?",
        r"disregard\s+(all\s+)?(previous|prior|above|earlier)\s+instructions?",
        r"forget\s+(all\s+)?(previous|prior|above|earlier)\s+instructions?",
        r"abaikan\s+(semua\s+)?(instruksi|perintah)\s+(sebelumnya|di atas)",
        # Override role
        r"you\s+are\s+now\s+",
        r"kamu\s+(sekarang\s+)?(adalah|berperan\s+sebagai)",
        r"act\s+as\s+",
        r"pretend\s+(you\s+are|to\s+be)\s+",
        r"roleplay\s+as\s+",
        r"berpura-pura\s+(menjadi|sebagai)",
        # Inject sistem
        r"<system>",
        r"\[system\]",
        r"system\s*:",
        r"new\s+instructions?\s*:",
        r"instruksi\s+baru\s*:",
        # Jailbreak klasik
        r"do\s+anything\s+now",
        r"jailbreak",
        r"bypass\s+(your\s+)?(restrictions?|guidelines?|rules?|filter)",
        # Injeksi via delimiter
        r"%%PRODUCTS%%",
        r"%%END_PRODUCTS%%",
        r"</?(system_instructions|product_context|user_question)>",
    ]

    injection_found = False
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            injection_found = True
            break

    if injection_found:
        # Kembalikan placeholder yang aman — prompt tetap diproses
        # tapi LLM akan mendeteksinya via instruksi di prompt
        return f"[POTENTIALLY UNSAFE INPUT DETECTED] {text}"

    return text


def sanitize_history(history: list) -> list:
    """Sanitasi semua pesan dalam conversation history."""
    if not history:
        return []
    sanitized = []
    for msg in history:
        if isinstance(msg, dict):
            sanitized.append({
                "role": msg.get("role", "user"),
                "content": sanitize_input(str(msg.get("content", "")))
            })
    return sanitized


def parse_products_from_answer(raw_answer):
    """
    Pisahkan teks jawaban biasa dari blok JSON produk.
    Hanya produk dengan image_url DAN product_url valid yang diloloskan.
    Mengembalikan (clean_answer, list_of_products)
    """
    products = []
    clean_answer = raw_answer

    pattern = r'%%PRODUCTS%%(.*?)%%END_PRODUCTS%%'
    match = re.search(pattern, raw_answer, re.DOTALL)

    if match:
        json_str = match.group(1).strip()
        try:
            raw_products = json.loads(json_str)
            # Filter: hanya produk yang punya kedua URL valid
            products = [
                p for p in raw_products
                if is_valid_url(p.get("product_url")) and is_valid_url(p.get("image_url"))
            ]
        except json.JSONDecodeError:
            products = []
        # Hapus blok produk dari teks jawaban
        clean_answer = re.sub(pattern, '', raw_answer, flags=re.DOTALL).strip()

    return clean_answer, products


def ask(question, conversation_history=None, language="id"):
    # --- Sanitasi input sebelum masuk ke pipeline ---
    clean_question = sanitize_input(question)
    clean_history = sanitize_history(conversation_history)

    contexts = retrieve(clean_question, vectordb, TOP_K)

    prompt = build_prompt(clean_question, contexts, clean_history, language=language)

    raw_answer = generate_answer(prompt)

    answer, products = parse_products_from_answer(raw_answer)

    return answer, contexts, products
