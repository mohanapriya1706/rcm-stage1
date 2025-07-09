import os, faiss, json, logging
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from fastmcp import FastMCP, Context
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from mcp.server.sse import SseServerTransport

# ------------------ Setup Logging ------------------
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ------------------ Env + Constants ------------------
load_dotenv('./gemini.env', override=True)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise EnvironmentError("Missing GEMINI_API_KEY in environment.")

FAISS_INDEX_PATH = "./faiss.index"
DOCS_JSON_PATH = "./semantic_chunks.json"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 5

# ------------------ App State ------------------
class RAGContext:
    def __init__(self):
        self.index = None
        self.documents = None
        self.embedder = None
        self.gemini_model = None

    async def setup(self):
        logger.debug("Setting up RAG context...")
        try:
            self.index = faiss.read_index(FAISS_INDEX_PATH)
            logger.debug(f"Loaded FAISS index from {FAISS_INDEX_PATH}")

            with open(DOCS_JSON_PATH, 'r') as f:
                chunk_dicts = json.load(f)
            self.documents = [d["chunk"] for d in chunk_dicts]
            logger.debug(f"Loaded {len(self.documents)} document chunks")

            self.embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
            logger.debug(f"Initialized SentenceTransformer with model '{EMBEDDING_MODEL_NAME}'")

            genai.configure(api_key=GEMINI_API_KEY)
            self.gemini_model = genai.GenerativeModel("gemini-1.5-flash")
            logger.debug("Initialized Gemini model")

        except Exception as e:
            logger.exception(f"Failed to initialize RAG context: {e}")
            raise

    async def cleanup(self):
        logger.debug("Cleaning up RAG context...")
        self.index = None
        self.documents = None
        self.embedder = None
        self.gemini_model = None

# ------------------ Lifespan Context Manager ------------------
@asynccontextmanager
async def app_lifespan(server: FastMCP):
    rag = RAGContext()
    await rag.setup()
    try:
        yield rag
    finally:
        await rag.cleanup()

# ------------------ Initialize FastMCP ------------------
mcp = FastMCP("RAGServer", lifespan=app_lifespan)

# ------------------ RAG Tool ------------------
@mcp.tool()
async def rag_query(ctx: Context, user_query: str) -> str:
    rag_context: RAGContext = ctx.app_data

    if not all([rag_context.index, rag_context.documents, rag_context.embedder, rag_context.gemini_model]):
        logger.error("RAG system not fully initialized.")
        return "RAG system not initialized. Please check server logs."

    logger.info(f"[RAG Tool] Received query: '{user_query}'")

    try:
        # --- Embed and Search ---
        query_embedding = rag_context.embedder.encode([user_query], normalize_embeddings=True)
        D, I = rag_context.index.search(query_embedding, TOP_K)
        matched_docs = [rag_context.documents[i] for i in I[0] if i != -1]
        logger.debug(f"[RAG Tool] Retrieved {len(matched_docs)} documents for query.")

        context = "\n\n".join(matched_docs) if matched_docs else ""
        if not matched_docs:
            logger.warning("[RAG Tool] No relevant documents found. Proceeding without context.")

        prompt = f"""You are a helpful assistant. Use the following context to answer the the question. If the context does not contain enough information, state that clearly and then try to answer based on your general knowledge.

Context:
{context}

Question: {user_query}
Answer:"""

        response = await rag_context.gemini_model.generate_content_async(prompt)
        logger.info("[RAG Tool] Gemini response generated successfully.")
        return response.text.strip()

    except Exception as e:
        logger.exception(f"[RAG Tool] Error during processing: {e}")
        return f"An error occurred while processing the query: {e}"

# ------------------ Start MCP Server ------------------
if __name__ == "__main__":
    logger.info("Starting FastMCP RAG Server...")
    try:
        mcp.run(
            transport="sse",  
            host="127.0.0.1",
            port=4200,
            path="/rag_query",
            log_level="debug",
        )
    except Exception as e:
        logger.exception(f"FastMCP server failed to start: {e}")
