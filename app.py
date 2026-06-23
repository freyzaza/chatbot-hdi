import streamlit as st
import requests
from datetime import datetime
from rag_pipeline import build_knowledge_base, ask
from auth import login, register
from session_manager import (
    get_all_sessions, create_session, load_session,
    save_session, delete_session,
    generate_title_from_message, update_session_title
)

CART_API_URL = "http://localhost:5050"

st.set_page_config(page_title="Chatbot RAG", layout="wide")

#CSS
st.markdown("""
<style>
.product-card img {
    width: 100%;
    height: 200px;
    object-fit: contain;
    background: #f8f8f8;
    display: block;
    padding: 8px;
    border-radius: 10px 10px 0 0;
}
.products-label {
    font-size: 13px;
    font-weight: 700;
    color: #888;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 4px;
    margin-top: 12px;
}
.btn-detail {
    display: block;
    width: 100%;
    background: transparent;
    color: #ff4b4b !important;
    border: 1.5px solid #ff4b4b;
    border-radius: 7px;
    padding: 6px 0;
    font-size: 11px;
    font-weight: 600;
    text-align: center;
    text-decoration: none !important;
    margin-bottom: 6px;
    transition: background 0.2s;
}
.btn-detail:hover { background: #fff0f0; }
.session-item {
    padding: 8px 10px;
    border-radius: 8px;
    margin-bottom: 4px;
    cursor: pointer;
    font-size: 13px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    border: 1px solid transparent;
    transition: background 0.15s;
}
.session-item:hover { background: #f0f0f0; }
.session-item.active {
    background: #fff0f0;
    border-color: #ffcccc;
    font-weight: 600;
    color: #e03333;
}
.login-box {
    max-width: 380px;
    margin: 60px auto;
    padding: 36px 32px;
    background: #fff;
    border-radius: 16px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.10);
}
</style>
""", unsafe_allow_html=True)


#Init knowledge base
if "kb_initialized" not in st.session_state:
    with st.spinner("Building knowledge base..."):
        build_knowledge_base()
    st.session_state.kb_initialized = True


#Helper: baca cart langsung dari file JSON
def fetch_cart(username: str) -> list:
    import json, os
    path = os.path.join("carts", f"{username}.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


#Helper: add to cart + langsung update state
def add_to_cart_api(product, username):
    try:
        resp = requests.post(
            f"{CART_API_URL}/cart/add",
            json={
                "session_id": username,
                "product_name": product.get("name", ""),
                "product_url": product.get("product_url", ""),
                "image_url": product.get("image_url", ""),
                "quantity": 1
            },
            timeout=3
        )
        data = resp.json()
        if data.get("success"):
            # Langsung refresh cart state setelah add berhasil
            st.session_state.cart_items = fetch_cart(username)
        return data.get("success", False), data.get("message", "")
    except requests.exceptions.ConnectionError:
        return False, "❌ Cart API tidak berjalan. Jalankan: python cart_api.py"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"


#Render kartu produk
def render_product_cards(products, username, msg_index):
    if not products:
        return
    st.markdown('<div class="products-label">🛍️ Produk yang direkomendasikan</div>', unsafe_allow_html=True)

    COLS_PER_ROW = 4
    for row_start in range(0, len(products), COLS_PER_ROW):
        row_products = products[row_start : row_start + COLS_PER_ROW]
        cols = st.columns(len(row_products))
        for i, product in enumerate(row_products):
            with cols[i]:
                name = product.get("name", "Produk")
                image_url = product.get("image_url", "")
                product_url = product.get("product_url", "#")

                if image_url:
                    st.markdown(
                        f'<img src="{image_url}" style="width:100%;height:200px;object-fit:contain;'
                        f'background:#f8f8f8;padding:8px;border-radius:10px 10px 0 0;" />',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        '<div style="width:100%;height:200px;background:#f0f0f0;border-radius:10px 10px 0 0;'
                        'display:flex;align-items:center;justify-content:center;font-size:32px;">📦</div>',
                        unsafe_allow_html=True
                    )

                st.markdown(
                    f'<p style="font-size:13px;font-weight:600;margin:8px 0 6px 0;line-height:1.4;">{name}</p>',
                    unsafe_allow_html=True
                )
                st.markdown(
                    f'<a href="{product_url}" target="_blank" class="btn-detail">🔍 Lihat Detail</a>',
                    unsafe_allow_html=True
                )
                btn_key = f"cart_{msg_index}_{row_start + i}_{username}"
                if st.button("🛒 Tambah ke Keranjang", key=btn_key, use_container_width=True):
                    success, message = add_to_cart_api(product, username)
                    if success:
                        st.rerun()
                    else:
                        st.error(message)

# HALAMAN LOGIN / REGISTER
def show_login_page():
    st.markdown("<h2 style='text-align:center;margin-top:40px;'>💬 Chatbot RAG</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#888;margin-bottom:32px;'>Silakan login untuk melanjutkan</p>", unsafe_allow_html=True)

    col_l, col_mid, col_r = st.columns([1, 1.2, 1])
    with col_mid:
        tab_login, tab_register = st.tabs(["🔑 Login", "📝 Register"])

        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            username = st.text_input("Username", key="login_user", placeholder="Masukkan username")
            password = st.text_input("Password", type="password", key="login_pass", placeholder="Masukkan password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Login", use_container_width=True, type="primary"):
                if not username or not password:
                    st.error("Username dan password wajib diisi.")
                else:
                    success, msg = login(username, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.active_session_id = None
                        st.session_state.messages = []
                        st.session_state.cart_items = fetch_cart(username)
                        st.session_state.language = "id"  # default bahasa Indonesia
                        st.rerun()
                    else:
                        st.error(msg)

        with tab_register:
            st.markdown("<br>", unsafe_allow_html=True)
            reg_user = st.text_input("Username", key="reg_user", placeholder="Buat username baru")
            reg_pass = st.text_input("Password", type="password", key="reg_pass", placeholder="Buat password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Daftar", use_container_width=True, type="primary"):
                success, msg = register(reg_user, reg_pass)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)


# HALAMAN CHAT UTAMA
def show_chat_page():
    username = st.session_state.username

    # Selalu sync cart dari file sebelum render apapun
    st.session_state.cart_items = fetch_cart(username)

    # Pastikan language selalu ada di session state
    if "language" not in st.session_state:
        st.session_state.language = "id"

    #Sidebar
    with st.sidebar:
        st.markdown(f"👤 **{username}**")
        if st.button("Logout", use_container_width=True):
            for key in ["logged_in", "username", "active_session_id", "messages", "cart_items", "language"]:
                st.session_state.pop(key, None)
            st.rerun()

        st.markdown("---")

        # Pilihan Bahasa
        st.markdown("**🌐 Bahasa / Language**")
        language_options = {"🇮🇩 Bahasa Indonesia": "id", "🇬🇧 English": "en"}
        selected_label = st.selectbox(
            label="Pilih bahasa",
            options=list(language_options.keys()),
            index=0 if st.session_state.language == "id" else 1,
            label_visibility="collapsed"
        )
        st.session_state.language = language_options[selected_label]

        st.markdown("---")

        if st.button("✏️  New Chat", use_container_width=True, type="primary"):
            new_id = create_session(username)
            st.session_state.active_session_id = new_id
            st.session_state.messages = []
            st.rerun()

        st.markdown("---")
        st.markdown("**Riwayat Chat**")

        sessions = get_all_sessions(username)
        active_id = st.session_state.get("active_session_id")

        if not sessions:
            st.caption("Belum ada chat. Mulai chat baru!")
        else:
            for s in sessions:
                sid = s["session_id"]
                title = s["title"]
                is_active = sid == active_id

                col_title, col_del = st.columns([5, 1])
                with col_title:
                    label = f"**{title}**" if is_active else title
                    if st.button(label, key=f"sess_{sid}", use_container_width=True):
                        st.session_state.active_session_id = sid
                        data = load_session(username, sid)
                        st.session_state.messages = data.get("messages", [])
                        st.rerun()
                with col_del:
                    if st.button("🗑", key=f"del_{sid}", help="Hapus chat ini"):
                        delete_session(username, sid)
                        if active_id == sid:
                            st.session_state.active_session_id = None
                            st.session_state.messages = []
                        st.rerun()

        #Keranjang real-time
        st.markdown("---")
        cart_items = st.session_state.get("cart_items", [])
        total_qty = sum(item.get("quantity", 0) for item in cart_items)
        cart_label = f"**🛒 Keranjang** ({total_qty} item)" if total_qty > 0 else "**🛒 Keranjang**"
        st.markdown(cart_label)

        if not cart_items:
            st.caption("Keranjang kosong")
        else:
            for item in cart_items:
                col_name, col_qty = st.columns([4, 1])
                with col_name:
                    st.markdown(
                        f'<p style="font-size:12px;margin:2px 0;">{item["product_name"]}</p>',
                        unsafe_allow_html=True
                    )
                with col_qty:
                    st.markdown(
                        f'<p style="font-size:12px;margin:2px 0;text-align:right;">x{item["quantity"]}</p>',
                        unsafe_allow_html=True
                    )

    #Area Chat Utama
    active_id = st.session_state.get("active_session_id")

    if not active_id:
        if st.session_state.language == "en":
            greeting_title = f"Hello, {username}! 👋"
            greeting_sub = "Start a new chat or select a chat history from the sidebar."
        else:
            greeting_title = f"Halo, {username}! 👋"
            greeting_sub = "Mulai chat baru atau pilih riwayat chat di sidebar."

        st.markdown(
            f"<div style='text-align:center;margin-top:120px;'>"
            f"<h2>{greeting_title}</h2>"
            f"<p style='color:#888;font-size:16px;'>{greeting_sub}</p>"
            f"</div>",
            unsafe_allow_html=True
        )
        return

    if "messages" not in st.session_state:
        data = load_session(username, active_id)
        st.session_state.messages = data.get("messages", [])

    st.title("💬 Chatbot RAG")
    st.markdown("---")

    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "timestamp" in message:
                st.caption(f"⏰ {message['timestamp']}")
            if message["role"] == "assistant":
                if message.get("contexts"):
                    with st.expander("📚 Context yang digunakan"):
                        for c in message["contexts"]:
                            st.write("-", c)
                if message.get("products"):
                    render_product_cards(message["products"], username, f"{active_id}_{idx}")

    # Placeholder chat input sesuai bahasa
    chat_placeholder = "Ask something..." if st.session_state.language == "en" else "Tanyakan sesuatu..."
    prompt = st.chat_input(chat_placeholder)

    if prompt:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        user_msg = {"role": "user", "content": prompt, "timestamp": now}
        st.session_state.messages.append(user_msg)

        with st.chat_message("user"):
            st.write(prompt)

        is_first_message = len(st.session_state.messages) == 1
        if is_first_message:
            title = generate_title_from_message(prompt)
            update_session_title(username, active_id, title)

        spinner_text = "Searching for answer..." if st.session_state.language == "en" else "Sedang mencari jawaban..."
        with st.spinner(spinner_text):
            recent_history = st.session_state.messages[-10:]
            answer, contexts, products = ask(prompt, recent_history, language=st.session_state.language)

        assistant_msg = {
            "role": "assistant",
            "content": answer,
            "contexts": contexts,
            "products": products,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.session_state.messages.append(assistant_msg)

        title = generate_title_from_message(prompt) if is_first_message else None
        save_session(username, active_id, st.session_state.messages, title)

        with st.chat_message("assistant"):
            st.write(answer)
            with st.expander("📚 Context yang digunakan"):
                for c in contexts:
                    st.write("-", c)
            render_product_cards(products, username, f"{active_id}_{len(st.session_state.messages)-1}")

        st.rerun()


# ROUTING UTAMA
if not st.session_state.get("logged_in"):
    show_login_page()
else:
    show_chat_page()
