import streamlit as st
import requests

API_URL = "http://localhost:8000/api/v1/chatbot/chat"
st.title("💬 AI Financial Assistant")

if "session" not in st.session_state:
    st.session_state["session"] = []

user_input = st.chat_input("Type your message here…")
if user_input:
    st.session_state.session.append({"role": "user", "content": user_input})
    response = requests.post(API_URL, json={"content": user_input})
    if response.ok:
        bot_reply = response.json()["response"]
        st.session_state.session.append({"role": "bot", "content": bot_reply})

for msg in st.session_state.session:
    st.chat_message(msg["role"]).write(msg["content"])
