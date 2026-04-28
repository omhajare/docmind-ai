import chromadb
from config import get_settings

settings = get_settings()


def get_collection_name(user_id: str) -> str:
    """ChromaDB collection name for a user. Hyphens replaced with underscores."""
    return f"user_{user_id.replace('-', '_')}"


def get_chroma_client() -> chromadb.ClientAPI:
    """Return the appropriate ChromaDB client based on environment."""
    if settings.is_production and settings.CHROMA_HOST:
        return chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            headers={"Authorization": f"Bearer {settings.CHROMA_API_KEY}"},
        )
    # Local: persistent storage in .chroma/ directory
    return chromadb.PersistentClient(path=str(_local_chroma_path()))


def _local_chroma_path():
    from pathlib import Path
    p = Path(__file__).resolve().parent.parent / ".chroma"
    p.mkdir(exist_ok=True)
    return p


def should_use_web_search(top_score: float, collection_empty: bool) -> bool:
    """Determine if web search should be triggered.
    Shared by Mode 1 Q&A agent and Mode 2 Researcher Node.
    """
    if collection_empty:
        return True
    return top_score < settings.WEB_SEARCH_FALLBACK_THRESHOLD


def search(user_id: str, query_text: str, query_embedding: list[float], top_k: int | None = None) -> dict:
    """Semantic search in a user's ChromaDB collection.
    Returns { chunks: [...], top_score: float, collection_empty: bool }
    """
    top_k = top_k or settings.RAG_TOP_K
    collection_name = get_collection_name(user_id)
    client = get_chroma_client()

    try:
        collection = client.get_collection(name=collection_name)
    except Exception:
        return {"chunks": [], "top_score": 0.0, "collection_empty": True}

    if collection.count() == 0:
        return {"chunks": [], "top_score": 0.0, "collection_empty": True}

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    distances = results.get("distances", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
        # With cosine space: distance = 1 - cosine_similarity
        cosine_score = max(0.0, 1.0 - dist)
        chunks.append({
            "content": doc,
            "metadata": meta,
            "cosine_score": round(cosine_score, 4),
        })

    top_score = chunks[0]["cosine_score"] if chunks else 0.0
    return {"chunks": chunks, "top_score": top_score, "collection_empty": False}


def delete_document_vectors(user_id: str, document_id: str) -> None:
    """Delete all vectors for a specific document from a user's collection."""
    collection_name = get_collection_name(user_id)
    client = get_chroma_client()

    try:
        collection = client.get_collection(name=collection_name)
        collection.delete(where={"document_id": document_id})
    except Exception:
        raise
