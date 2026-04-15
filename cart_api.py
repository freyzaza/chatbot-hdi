"""
cart_api.py — REST API untuk keranjang belanja
Jalankan terpisah: python cart_api.py
Berjalan di http://localhost:5050

Cart disimpan persisten ke: carts/<username>.json
"""

import json
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

CARTS_DIR = "carts"
os.makedirs(CARTS_DIR, exist_ok=True)


# ── Helpers JSON ──────────────────────────────────────────────────────────────

def _cart_path(username: str) -> str:
    return os.path.join(CARTS_DIR, f"{username}.json")


def load_cart(username: str) -> list:
    path = _cart_path(username)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_cart(username: str, cart: list):
    with open(_cart_path(username), "w", encoding="utf-8") as f:
        json.dump(cart, f, indent=2, ensure_ascii=False)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})


@app.route("/cart/add", methods=["POST"])
def add_to_cart():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Request body kosong"}), 400

    username = data.get("session_id", "default")
    product_name = data.get("product_name")
    product_url = data.get("product_url")
    image_url = data.get("image_url", "")
    quantity = data.get("quantity", 1)

    if not product_name or not product_url:
        return jsonify({"success": False, "message": "product_name dan product_url wajib diisi"}), 400

    cart = load_cart(username)

    existing = next((item for item in cart if item["product_url"] == product_url), None)
    if existing:
        existing["quantity"] += quantity
        message = f"Jumlah '{product_name}' ditambah menjadi {existing['quantity']}"
    else:
        cart.append({
            "product_name": product_name,
            "product_url": product_url,
            "image_url": image_url,
            "quantity": quantity,
            "added_at": datetime.now().isoformat()
        })
        message = f"'{product_name}' berhasil ditambahkan ke keranjang"

    save_cart(username, cart)

    return jsonify({
        "success": True,
        "message": message,
        "cart_count": len(cart)
    })


@app.route("/cart/<username>", methods=["GET"])
def get_cart(username):
    cart = load_cart(username)
    return jsonify({
        "session_id": username,
        "items": cart,
        "total_items": len(cart)
    })


@app.route("/cart/<username>/remove", methods=["DELETE"])
def remove_from_cart(username):
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Request body kosong"}), 400

    product_url = data.get("product_url")
    cart = load_cart(username)
    new_cart = [item for item in cart if item["product_url"] != product_url]
    save_cart(username, new_cart)

    return jsonify({"success": True, "message": "Produk dihapus dari keranjang"})


@app.route("/cart/<username>/clear", methods=["DELETE"])
def clear_cart(username):
    save_cart(username, [])
    return jsonify({"success": True, "message": "Keranjang dikosongkan"})


if __name__ == "__main__":
    print("🛒 Cart API berjalan di http://localhost:5050")
    app.run(host="0.0.0.0", port=5050, debug=True)