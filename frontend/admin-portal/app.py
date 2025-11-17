import os
import requests
import streamlit as st

API_BASE = os.environ.get("ADMIN_API_BASE", "http://localhost:8000/api/v1")
AUTH_HEADER = {}

st.set_page_config(page_title="Admin Portal", layout="wide")
st.title("🔐 Admin Portal – Financial Chatbot")

st.sidebar.header("Authentication")
token = st.sidebar.text_input("Bearer Token", type="password", help="Use /auth/login to get a token for an admin user")
if token:
    AUTH_HEADER = {"Authorization": f"Bearer {token}"}

tab_docs, tab_rag, tab_users, tab_tx, tab_bens = st.tabs(
    ["📄 Documents", "🧠 RAG", "👤 Users", "💳 Transactions", "👥 Beneficiaries"]
)

with tab_docs:
    st.subheader("Upload & Ingest Documents")
    dtype = st.selectbox("Document Type", ["sanctions_list", "compliance_rules", "terms_conditions", "other"])
    file = st.file_uploader("Upload file (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"])
    if st.button("Upload", disabled=not file):
        files = {"file": (file.name, file.read())}
        data = {"document_type": dtype}
        r = requests.post(f"{API_BASE}/documents/upload", files=files, data=data, headers=AUTH_HEADER)
        st.write(r.json())

    st.divider()
    if st.button("Refresh List"):
        pass
    r = requests.get(f"{API_BASE}/documents/list", headers=AUTH_HEADER)
    if r.ok:
        st.table(r.json())

    doc_id = st.text_input("Document ID to ingest")
    if st.button("Ingest to RAG", disabled=not doc_id):
        r = requests.post(f"{API_BASE}/documents/ingest/{doc_id}", headers=AUTH_HEADER)
        st.write(r.json())

with tab_rag:
    st.subheader("Vector DB / RAG")
    if st.button("Show RAG Stats"):
        r = requests.get(f"{API_BASE}/documents/rag/stats", headers=AUTH_HEADER)
        st.json(r.json())

    del_id = st.text_input("Delete vectors by source (document_id)")
    if st.button("Delete by Source", disabled=not del_id):
        r = requests.delete(f"{API_BASE}/documents/rag/delete-by-source/{del_id}", headers=AUTH_HEADER)
        st.json(r.json())

with tab_users:
    st.subheader("Users")
    r = requests.get(f"{API_BASE}/admin/users", headers=AUTH_HEADER)
    if r.ok:
        st.table(r.json())

    st.markdown("**Credit/Debit**")
    uid = st.text_input("User ID")
    op_type = st.selectbox("Operation", ["credit", "debit"])
    amt = st.number_input("Amount", min_value=0.0, step=10.0)
    if st.button("Submit Operation", disabled=not uid or amt <= 0):
        payload = {"user_id": uid, "amount": float(amt), "operation_type": op_type}
        r = requests.post(f"{API_BASE}/admin/users/credit-debit", json=payload, headers=AUTH_HEADER)
        st.json(r.json())

with tab_tx:
    st.subheader("Transactions")
    r = requests.get(f"{API_BASE}/admin/transactions", headers=AUTH_HEADER)
    if r.ok:
        st.table(r.json())

with tab_bens:
    st.subheader("Beneficiaries")
    r = requests.get(f"{API_BASE}/admin/beneficiaries", headers=AUTH_HEADER)
    if r.ok:
        st.table(r.json())