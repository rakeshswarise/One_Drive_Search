import os
import io
import re
import requests
import streamlit as st
from msal import PublicClientApplication, SerializableTokenCache
from docx import Document
import google.generativeai as genai

# === CONFIG ===
CLIENT_ID = ""
TENANT_ID = ""
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["Files.Read.All", "User.Read"]
TOKEN_PATH = "ms_token.json"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# === Gemini Setup ===
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# === Functions ===

def semantic_keywords_gemini(query):
    prompt = f"""
You are an NLP assistant.
Extract the top 15 relevant semantic keywords from the question below.
Query: "{query}"
Respond as a Python list.
"""
    try:
        response = model.generate_content(prompt)
        match = re.findall(r'\[.*?\]', response.text)
        if match:
            return eval(match[0])
    except Exception as e:
        st.error(f"Gemini error: {e}")
    return []

def read_docx_content(file_bytes):
    try:
        with open("temp.docx", "wb") as f:
            f.write(file_bytes)
        doc = Document("temp.docx")
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        os.remove("temp.docx")
        return text
    except Exception as e:
        return f"Error reading DOCX: {e}"

def search_in_text(content, keywords):
    pattern = "|".join([re.escape(k) for k in keywords])
    return re.search(pattern, content, re.IGNORECASE)

def onedrive_auth():
    cache = SerializableTokenCache()
    if os.path.exists(TOKEN_PATH):
        cache.deserialize(open(TOKEN_PATH, "r").read())

    app = PublicClientApplication(CLIENT_ID, authority=AUTHORITY, token_cache=cache)

    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            return result["access_token"]

    flow = app.initiate_device_flow(scopes=SCOPES)
    st.info(f"🔑 Go to: {flow['verification_uri']}")
    st.info(f"📋 Enter code: `{flow['user_code']}` to authenticate your OneDrive")

    result = app.acquire_token_by_device_flow(flow)
    if "access_token" in result:
        with open(TOKEN_PATH, "w") as f:
            f.write(cache.serialize())
        return result["access_token"]

    st.error("❌ Authentication failed.")
    return None

# === Streamlit UI ===

st.set_page_config(page_title="🔍 OneDrive Semantic Search", layout="centered")
st.title("🔍 OneDrive Semantic Document Search")
st.caption("Ask a question about your OneDrive `.docx` files")

query = st.text_input("💬 Ask your question")

if query:
    with st.spinner("Extracting semantic keywords using Gemini..."):
        keywords = semantic_keywords_gemini(query)

    if not keywords:
        st.error("❌ Could not extract keywords.")
    else:
        st.write("📚 Semantic Keywords:")
        st.code(keywords, language="python")

        access_token = onedrive_auth()
        if access_token:
            headers = {"Authorization": f"Bearer {access_token}"}
            url = "https://graph.microsoft.com/v1.0/me/drive/root/children"
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                files = response.json().get("value", [])
                found_any = False

                for item in files:
                    name = item["name"]
                    file_id = item["id"]

                    if name.endswith(".docx"):
                        content_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}/content"
                        file_bytes = requests.get(content_url, headers=headers).content
                        text = read_docx_content(file_bytes)

                        if search_in_text(text, keywords):
                            found_any = True
                            st.markdown(f"---\n📄 **{name}**")
                            st.text_area("📄 Document Content", text, height=200)

                            prompt = f"""
You are a document expert. Read the following document and answer the user's question.
Use your reasoning and inference to understand synonyms and implied meanings.

Question: {query}   
Document:
\"\"\"{text}\"\"\"

Instructions:
- Try to answer based on meaning, not just exact words.
- If the answer is clearly implied or indirectly present, respond with your best interpretation.
- If no relation at all, reply: "Not found in this document."
"""

                            try:
                                answer = model.generate_content(prompt)
                                st.success("✅ Gemini Answer:")
                                st.markdown(answer.text)
                            except Exception as e:
                                st.error(f"Gemini error: {e}")

                if not found_any:
                    st.warning("❌ No matching OneDrive `.docx` file found.")
            else:
                st.error(f"❌ Failed to list OneDrive files: {response.status_code}")
