import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import MarkdownHeaderTextSplitter

# Load SentenceTransformer model
model = SentenceTransformer("all-MiniLM-L6-v2")

# File paths
index_path = "faiss.index"
meta_path = "./semantic_chunks.json"
input_md_path = "./NPP.md"

def load_and_split_md(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        markdown_text = f.read()

    # Split using markdown headers
    splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[("###", "subsection")])
    splits = splitter.split_text(markdown_text)

    # Extract both content and metadata
    docs = [doc.page_content.strip() for doc in splits]
    metas = [{"chunk": doc.page_content.strip()} for doc in splits]  # Changed here

    return docs, metas

def build_faiss_index(docs):
    embeddings = model.encode(docs, show_progress_bar=True, normalize_embeddings=True)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # Cosine similarity due to normalization
    index.add(embeddings)

    faiss.write_index(index, index_path)
    return index, embeddings

if __name__ == "__main__":
    docs, metas = load_and_split_md(input_md_path)
    build_faiss_index(docs)

    # Save the metadata with structure: [{ "chunk": "..." }]
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metas, f, indent=2)

    print(f" Indexed {len(docs)} chunks into FAISS (cosine similarity).")
