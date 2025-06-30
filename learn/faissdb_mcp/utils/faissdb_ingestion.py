import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import MarkdownHeaderTextSplitter

model = SentenceTransformer("all-MiniLM-L6-v2")
index_path = "faiss_index.index"
meta_path = "metadata.json"

def load_and_split_md(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        markdown_text = f.read()

    splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[("###", "subsection")])
    splits = splitter.split_text(markdown_text)

    docs = [doc.page_content for doc in splits]
    metas = [doc.metadata for doc in splits]

    return docs, metas

def build_faiss_index(docs):
    embeddings = model.encode(docs, show_progress_bar=True, normalize_embeddings=True)  # Normalize here

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  #  inner product (cosine if normalized)
    index.add(embeddings)
    faiss.write_index(index, index_path)
    return index, embeddings

if __name__ == "__main__":
    docs, metas = load_and_split_md("./NPP.md")  # Only one file
    build_faiss_index(docs)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metas, f, indent=2)
    print(f"Indexed {len(docs)} chunks into FAISS (cosine similarity).")
