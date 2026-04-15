"""
auth.py — Manajemen user (login, register, simpan ke users.json)
"""

import json
import os

USERS_FILE = "users.json"


def load_users() -> dict:
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_users(users: dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def register(username: str, password: str) -> tuple[bool, str]:
    """
    Daftarkan user baru.
    Return (success, message)
    """
    username = username.strip()
    if not username or not password:
        return False, "Username dan password tidak boleh kosong."

    users = load_users()
    if username in users:
        return False, "Username sudah digunakan."

    users[username] = {"password": password}
    save_users(users)
    return True, "Registrasi berhasil! Silakan login."


def login(username: str, password: str) -> tuple[bool, str]:
    """
    Verifikasi login.
    Return (success, message)
    """
    username = username.strip()
    users = load_users()

    if username not in users:
        return False, "Username tidak ditemukan."
    if users[username]["password"] != password:
        return False, "Password salah."

    return True, "Login berhasil!"
