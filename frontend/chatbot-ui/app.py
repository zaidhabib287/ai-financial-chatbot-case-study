import requests
import streamlit as st

API_URL = "http://localhost:8000/api/v1/chatbot/chat"

st.set_page_config(page_title="AI Financial Assistant", page_icon="💬")
st.title("💬 AI Financial Assistant")

st.markdown(
    "1. Login via API to get a JWT token.\n"
    "2. Paste the token below.\n"
    "3. Start chatting."
)

# Token input
token = st.text_input("JWT access token", type="password")

if "session" not in st.session_state:
    st.session_state["session"] = []

user_input = st.chat_input("Type your message here…")

if user_input:
    st.session_state.session.append({"role": "user", "content": user_input})

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.post(
            API_URL,
            json={"content": user_input},
            headers=headers,
            timeout=60,
        )
        if response.ok:
            data = response.json()
            bot_reply = data.get("reply", "(no reply field in response)")
        else:
            bot_reply = f"Error {response.status_code}: {response.text}"
    except Exception as exc:
        bot_reply = f"Request failed: {exc}"

    st.session_state.session.append({"role": "assistant", "content": bot_reply})

# Render chat history
for msg in st.session_state.session:
    st.chat_message(msg["role"]).write(msg["content"])
