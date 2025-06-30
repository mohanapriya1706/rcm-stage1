import faiss
import json
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

# --- Configuration ---
FAISS_INDEX_PATH = "./faiss_index.index"           # Path to your FAISS index
DOCS_JSON_PATH = "./metadata.json"                 # Your original text chunks (JSON list)
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"          # Same embedding model used during indexing
GEMINI_API_KEY = "apikey"             
TOP_K = 5                                           # Number of top documents to retrieve

# --- Load FAISS index and documents ---
print("Loading FAISS index and documents...")
index = faiss.read_index(FAISS_INDEX_PATH)

with open(DOCS_JSON_PATH, "r", encoding="utf-8") as f:
    documents = json.load(f)  # List of text chunks

# --- Load embedding model ---
print("Loading embedding model...")
embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)

# --- User query ---
query = input("Enter your question: ")

# --- Embed query ---
print("Embedding query...")
query_embedding = embedder.encode([query])

# --- Search FAISS index ---
print(f"Searching top {TOP_K} relevant chunks...")
D, I = index.search(query_embedding, TOP_K)
matched_docs = [documents[i] for i in I[0]]

# --- Build prompt for Gemini ---
context = "\n\n".join(matched_docs)
prompt = f"""Answer the question based on the context below.

Context:
{context}

Question: {query}
Answer:"""

# --- Set up Gemini ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-pro")

# --- Send prompt to Gemini ---
print("Querying Gemini...")
response = model.generate_content(prompt)

# --- Output result ---
print("\n--- Answer ---")
print(response.text)
