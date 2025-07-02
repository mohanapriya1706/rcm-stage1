import os
import faiss
import json
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from dotenv import load_dotenv

# --- Load Environment Variables ---
load_dotenv('gemini.env', override=True)

# --- Configuration ---
GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GEMINI_API_KEY:
    raise EnvironmentError(" GOOGLE_API_KEY not found in environment.")

FAISS_INDEX_PATH = "./faiss.index"
DOCS_JSON_PATH = "./semantic_chunks.json"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 5

# --- Load FAISS Index and Document Chunks ---
print(" Loading FAISS index and document chunks...")
index = faiss.read_index(FAISS_INDEX_PATH)

with open(DOCS_JSON_PATH, "r", encoding="utf-8") as f:
    chunk_dicts = json.load(f)  # List of { "chunk": "..." }

# Extract just the text chunks
documents = [chunk["chunk"] for chunk in chunk_dicts]

# --- Load Embedding Model ---
print(" Loading embedding model...")
embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)

# --- Get User Query ---
query = input(" Enter your question: ")

# --- Embed Query and Normalize for Cosine Similarity ---
print(" Embedding and searching...")
query_embedding = embedder.encode([query], normalize_embeddings=True)

# --- Perform FAISS Search ---
D, I = index.search(query_embedding, TOP_K)
matched_docs = [documents[i] for i in I[0]]

# --- Build Prompt for Gemini ---
context = "\n\n".join(matched_docs)
prompt = f"""You are a helpful assistant. Use the following context to answer the question.

Context:
{context}

Question: {query}
Answer:"""

# --- Query Gemini ---
print(" Querying Gemini...")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")
response = model.generate_content(prompt)

# --- Display Result ---
print("\n--- Gemini Answer ---")
print(response.text.strip())

