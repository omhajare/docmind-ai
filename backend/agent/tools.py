"""RAG search and web search tools for the Q&A agent."""

from tavily import TavilyClient

from config import get_settings
from rag.indexer import get_embedding
from rag.retriever import search as rag_search_fn, should_use_web_search, get_collection_name, get_chroma_client
from utils.logger import logger

settings = get_settings()


def rag_search(user_id: str, query: str) -> dict:
    """Search the user's documents via ChromaDB.
    Returns { chunks: [...], top_score: float, collection_empty: bool }
    """
    try:
        query_embedding = get_embedding(query)
        result = rag_search_fn(user_id, query, query_embedding)
        return result
    except Exception as e:
        logger.error(f"RAG search failed: {e}")
        return {"chunks": [], "top_score": 0.0, "collection_empty": True}


def web_search(query: str, max_results: int = 5) -> list[dict]:
    """Search the web via Tavily API.
    Returns [{ url, title, snippet }]
    """
    if not settings.TAVILY_API_KEY:
        logger.warning("TAVILY_API_KEY not set, skipping web search")
        return []

    try:
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        response = client.search(query=query, max_results=max_results)
        results = []
        for r in response.get("results", []):
            results.append({
                "url": r.get("url", ""),
                "title": r.get("title", ""),
                "snippet": r.get("content", "")[:300],
            })
        return results
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return []
