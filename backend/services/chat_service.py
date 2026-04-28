from fastapi import HTTPException, status
from langchain_google_genai import ChatGoogleGenerativeAI

from config import get_settings
from repositories import chat_repository
from agent.tools import rag_search, web_search
from agent.prompts import QA_SYSTEM_PROMPT, QA_USER_PROMPT
from rag.retriever import should_use_web_search
from utils.logger import logger

settings = get_settings()


def _get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=settings.GEMINI_API_KEY,
    )


def _check_ai_enabled():
    """Check if AI service is enabled."""
    from database.db_client import get_db
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT value FROM app_settings WHERE key = 'ai_enabled'")
            row = cur.fetchone()
            if row and row["value"] == "false":
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="AI service is temporarily unavailable.",
                )


def _compute_confidence(top_score: float, used_web: bool) -> str:
    if used_web and top_score == 0.0:
        return "low"
    if top_score >= settings.CONFIDENCE_HIGH_THRESHOLD:
        return "high"
    if top_score >= settings.CONFIDENCE_MEDIUM_THRESHOLD:
        return "medium"
    return "low"


# ─── Session Management ─────────────────────────────────────

def create_session(user_id: str, title: str | None = None) -> dict:
    count = chat_repository.count_sessions_by_user(user_id)
    if count >= settings.MAX_SESSIONS_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Session limit reached ({settings.MAX_SESSIONS_PER_USER}). Delete older sessions.",
        )
    session = chat_repository.create_session(user_id, title or "New Chat")
    return _serialize_session(session)


def list_sessions(user_id: str) -> list[dict]:
    sessions = chat_repository.find_sessions_by_user(user_id)
    return [_serialize_session(s) for s in sessions]


def rename_session(user_id: str, session_id: str, title: str) -> dict:
    session = _get_owned_session(user_id, session_id)
    updated = chat_repository.update_session_title(session_id, title.strip())
    return _serialize_session(updated)


def delete_session(user_id: str, session_id: str) -> dict:
    _get_owned_session(user_id, session_id)
    chat_repository.delete_session(session_id)
    return {"message": "Session deleted"}


# ─── Messages ───────────────────────────────────────────────

def send_message(user_id: str, session_id: str, query: str) -> dict:
    _check_ai_enabled()
    session = _get_owned_session(user_id, session_id)

    query = query.strip()
    if not query:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query cannot be empty")
    if len(query) > settings.MAX_CHAT_QUERY_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Query exceeds maximum length of {settings.MAX_CHAT_QUERY_LENGTH} characters",
        )

    # 1. Save user message
    chat_repository.save_message(session_id, user_id, "user", query)

    # 2. Get conversation context
    recent = chat_repository.get_recent_messages(session_id, settings.CHAT_CONTEXT_WINDOW)
    conversation_history = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in recent
    )

    # 3. RAG search
    rag_result = rag_search(user_id, query)
    chunks = rag_result["chunks"]
    top_score = rag_result["top_score"]
    collection_empty = rag_result["collection_empty"]

    # Build document context
    document_sources = []
    doc_context_parts = []
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        doc_context_parts.append(chunk["content"])
        document_sources.append({
            "filename": meta.get("filename", "Unknown"),
            "page_number": meta.get("page_number"),
            "chunk_preview": chunk["content"][:150],
            "cosine_score": chunk["cosine_score"],
        })

    document_context = "\n\n".join(doc_context_parts) if doc_context_parts else "No document context available."

    # 4. Conditional web search
    tools_used = ["rag_search"]
    web_sources = []
    web_context = "No web search performed."

    if should_use_web_search(top_score, collection_empty):
        tools_used.append("web_search")
        web_results = web_search(query)
        web_sources = web_results
        if web_results:
            web_context = "\n\n".join(
                f"[{r['title']}]({r['url']}): {r['snippet']}" for r in web_results
            )

    # 5. LLM synthesis
    try:
        llm = _get_llm()
        prompt = QA_USER_PROMPT.format(
            document_context=document_context,
            web_context=web_context,
            conversation_history=conversation_history,
            query=query,
        )
        response = llm.invoke([
            {"role": "system", "content": QA_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ])
        answer = response.content
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        answer = "I'm sorry, I encountered an error generating a response. Please try again."

    # 6. Compute confidence
    used_web = "web_search" in tools_used
    confidence = _compute_confidence(top_score, used_web)

    # 7. Build sources object
    sources = {
        "document_sources": document_sources,
        "web_sources": web_sources,
    }

    # 8. Save assistant message
    assistant_msg = chat_repository.save_message(
        session_id, user_id, "assistant", answer,
        sources=sources, tools_used=tools_used, confidence=confidence,
    )

    # 9. Update session timestamp + auto-title
    chat_repository.update_session_timestamp(session_id)
    if session["title"] == "New Chat":
        title = query[:settings.SESSION_TITLE_MAX_LENGTH]
        chat_repository.update_session_title(session_id, title)

    logger.info(f"Q&A: session={session_id} tools={tools_used} confidence={confidence} score={top_score:.2f}")
    return _serialize_message(assistant_msg)


def get_messages(user_id: str, session_id: str, limit: int = 10, offset: int = 0) -> list[dict]:
    _get_owned_session(user_id, session_id)
    limit = min(limit, 50)
    messages = chat_repository.get_messages(session_id, limit, offset)
    return [_serialize_message(m) for m in messages]


def delete_message(user_id: str, message_id: str) -> dict:
    msg = chat_repository.find_message_by_id(message_id)
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    if str(msg["user_id"]) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    chat_repository.delete_message(message_id)
    return {"message": "Message deleted"}


# ─── Helpers ─────────────────────────────────────────────────

def _get_owned_session(user_id: str, session_id: str) -> dict:
    session = chat_repository.find_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if str(session["user_id"]) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return session


def _serialize_session(s: dict) -> dict:
    return {
        "id": str(s["id"]),
        "title": s["title"],
        "created_at": s["created_at"].isoformat() if s.get("created_at") else None,
        "updated_at": s["updated_at"].isoformat() if s.get("updated_at") else None,
    }


def _serialize_message(m: dict) -> dict:
    import json
    sources = m.get("sources")
    if isinstance(sources, str):
        sources = json.loads(sources)
    tools_used = m.get("tools_used")
    if isinstance(tools_used, str):
        tools_used = json.loads(tools_used)

    return {
        "id": str(m["id"]),
        "session_id": str(m.get("session_id", "")),
        "role": m["role"],
        "content": m["content"],
        "sources": sources,
        "tools_used": tools_used,
        "confidence": m.get("confidence"),
        "created_at": m["created_at"].isoformat() if m.get("created_at") else None,
    }
