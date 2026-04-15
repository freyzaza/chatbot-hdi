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


def ask(question, conversation_history=None):

    contexts = retrieve(question, vectordb, TOP_K)

    prompt = build_prompt(question, contexts, conversation_history)

    raw_answer = generate_answer(prompt)

    answer, products = parse_products_from_answer(raw_answer)

    return answer, contexts, products
