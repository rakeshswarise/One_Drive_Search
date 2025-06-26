📄 Project: OneDrive Semantic Document Search
🔍 Purpose:
This app allows users to ask questions about their .docx files stored in OneDrive, and it will:

Extract semantic keywords using Gemini AI.

Authenticate and access files from OneDrive using the Microsoft Graph API.

Read .docx file contents and search for keyword matches.

Use Gemini AI to generate context-aware answers from the document content.

📦 Dependencies
Make sure the following are installed (via pip install -r requirements.txt):

txt
Copy
Edit
streamlit
requests
msal
python-docx
google-generativeai
🔧 Configuration
Create a .env file for storing environment variables:

env
Copy
Edit
GEMINI_API_KEY=your_google_gemini_api_key
In your Python script:

python
Copy
Edit
CLIENT_ID = "your_azure_app_client_id"
TENANT_ID = "your_azure_tenant_id"
To get these:

Register an app on Azure Portal

Grant API permissions: Files.Read.All and User.Read

Enable "Device Code Flow" under Authentication

📂 File Structure
bash
Copy
Edit
SPO_search/
│
├── spo_search.py         # Main Streamlit app
├── ms_token.json         # Token cache for MSAL (auto-created)
├── requirements.txt
└── .env                  # API keys and secrets (not tracked by Git)
🧠 Core Components
1. Gemini Semantic Keyword Extraction
python
Copy
Edit
def semantic_keywords_gemini(query):
    ...
    response = model.generate_content(prompt)
    ...
Uses Gemini 1.5 Flash model to extract top 15 semantic keywords.

Converts the response string into a Python list using eval().

2. OneDrive Authentication
python
Copy
Edit
def onedrive_auth():
    ...
    flow = app.initiate_device_flow(...)
    ...
    result = app.acquire_token_by_device_flow(flow)
Uses MSAL device code flow to authenticate the user.

Token saved in ms_token.json.

3. Document Content Extraction
python
Copy
Edit
def read_docx_content(file_bytes):
    ...
    doc = Document("temp.docx")
Saves downloaded .docx from OneDrive temporarily.

Reads using python-docx.

4. Keyword Matching
python
Copy
Edit
def search_in_text(content, keywords):
    pattern = "|".join([re.escape(k) for k in keywords])
    return re.search(pattern, content, re.IGNORECASE)
Performs a case-insensitive regex search on the content.

5. Gemini-Powered Answer Generation
python
Copy
Edit
prompt = f"""
You are a document expert...
"""
answer = model.generate_content(prompt)
Analyzes document using Gemini to reason out answers based on the question and text, even with indirect meaning.

🖥️ Streamlit UI Flow
python
Copy
Edit
st.title("🔍 OneDrive Semantic Document Search")

query = st.text_input("💬 Ask your question")
Flow:
User enters a question.

Gemini extracts semantic keywords.

Authenticate with OneDrive.

Loop through .docx files in root folder:

If content matches keywords → show document

Ask Gemini to generate a meaning-based answer

Show final answer or a "Not found" message.

✅ Output Example
bash
Copy
Edit
💬 Ask your question: "What are the project timelines?"

📚 Semantic Keywords:
['project', 'timelines', 'schedule', 'deadline', 'milestones', ...]

📄 Found in: ProjectPlan.docx

✅ Gemini Answer:
"The document outlines a 3-phase schedule with a final delivery in Q4 2025."
🛡️ Security Tips
Do not upload .env or ms_token.json to GitHub.

Use .gitignore:

gitignore
Copy
Edit
.env
ms_token.json
🚀 Future Enhancements
✅ Support .pdf files (use PyMuPDF)

✅ Enable folder navigation

🧠 Add vector-based search with embeddings

📊 Show document ranking by relevance

🗂️ Cache keyword matches for faster re-use