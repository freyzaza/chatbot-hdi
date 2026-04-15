"""
session_manager.py — Kelola multi-session chat per user
Struktur file: chats/<username>/<session_id>.json
"""

import json
import os
import uuid
from datetime import datetime

CHATS_DIR = "chats"


def _user_dir(username: str) -> str:
    path = os.path.join(CHATS_DIR, username)
    os.makedirs(path, exist_ok=True)
    return path


def _session_path(username: str, session_id: str) -> str:
    return os.path.join(_user_dir(username), f"{session_id}.json")


# ── Session List ──────────────────────────────────────────────────────────────

def get_all_sessions(username: str) -> list[dict]:
    """
    Ambil semua session milik user, diurutkan dari terbaru.
    Return list of: { session_id, title, created_at, updated_at }
    """
    user_dir = _user_dir(username)
    sessions = []

    for fname in os.listdir(user_dir):
        if not fname.endswith(".json"):
            continue
        session_id = fname[:-5]
        try:
            with open(os.path.join(user_dir, fname), "r", encoding="utf-8") as f:
                data = json.load(f)
            sessions.append({
                "session_id": session_id,
                "title": data.get("title", "Chat baru"),
                "created_at": data.get("created_at", ""),
                "updated_at": data.get("updated_at", ""),
            })
        except Exception:
            continue

    # Urutkan dari yang paling baru diupdate
    sessions.sort(key=lambda x: x["updated_at"], reverse=True)
    return sessions


# ── CRUD Session ──────────────────────────────────────────────────────────────

def create_session(username: str) -> str:
    """Buat session baru, return session_id"""
    session_id = str(uuid.uuid4())[:8]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {
        "session_id": session_id,
        "title": "Chat baru",
        "created_at": now,
        "updated_at": now,
        "messages": []
    }
    with open(_session_path(username, session_id), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return session_id


def load_session(username: str, session_id: str) -> dict:
    """Load session, return dict dengan keys: title, messages, dll"""
    path = _session_path(username, session_id)
    if not os.path.exists(path):
        return {"title": "Chat baru", "messages": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"title": "Chat baru", "messages": []}


def save_session(username: str, session_id: str, messages: list, title: str = None):
    """Simpan messages ke session. Title di-update jika diberikan."""
    path = _session_path(username, session_id)

    # Load existing data dulu untuk jaga-jaga field lain
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    else:
        data = {
            "session_id": session_id,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    data["messages"] = messages
    data["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if title:
        data["title"] = title

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def delete_session(username: str, session_id: str) -> bool:
    """Hapus session, return True jika berhasil"""
    path = _session_path(username, session_id)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def update_session_title(username: str, session_id: str, title: str):
    """Update judul session saja"""
    path = _session_path(username, session_id)
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["title"] = title[:60]  # Batasi panjang judul
        data["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def generate_title_from_message(first_message: str) -> str:
    """Buat judul singkat dari pesan pertama user (maks 50 karakter)"""
    title = first_message.strip()
    if len(title) > 50:
        title = title[:47] + "..."
    return title
