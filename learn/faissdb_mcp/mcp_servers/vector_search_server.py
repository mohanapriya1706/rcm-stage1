from fastmcp import FastMCP
import faiss
import json
import numpy as np
from sentence_transformers import SentenceTransformer

index = faiss.read_index("faiss_index.index")
with open("metadata.json", "r", encoding="utf-8") as f:
    metadata = json.load(f)

model = SentenceTransformer("all-MiniLM-L6-v2")
mcp = FastMCP("FAISS-MCP")

@mcp.tool()
def query(text: str, top_k: int = 5) -> list:
    embedding = model.encode([text])
    D, I = index.search(np.array(embedding).astype("float32"), top_k)
    results = []
    for idx, score in zip(I[0], D[0]):
        result = metadata[idx].copy()
        result["score"] = float(score)
        results.append(result)
    return results

if __name__ == "__main__":
    mcp.run(transport="sse", host="127.0.0.1", port=5050) # loopback
