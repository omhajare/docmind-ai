from langchain_google_genai import ChatGoogleGenerativeAI

from config import get_settings
from agent.prompts import GAP_FILLER_PROMPT
from agent.tools import rag_search, web_search
from rag.retriever import should_use_web_search
from repositories import research_repository
from utils.logger import logger

settings = get_settings()


def gap_filler_node(state: dict) -> dict:
    """Fill identified gaps with additional research."""
    job_id = state["job_id"]
    user_id = state["user_id"]

    job = research_repository.find_by_id(job_id)
    if job and job["status"] == "cancelled":
        return state

    gaps = state.get("reflection_gaps", [])
    findings = state.get("research_findings", {})
    chunk_scores = state.get("chunk_scores", [])
    web_used = state.get("web_used", False)

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=settings.GEMINI_API_KEY)

    for gap in gaps:
        prompt = GAP_FILLER_PROMPT.format(topic=state["topic"], gap=gap)
        response = llm.invoke(prompt)
        question = response.content.strip()

        # Research the gap question
        rag_result = rag_search(user_id, question)
        chunks = rag_result["chunks"]
        top_score = rag_result["top_score"]

        for c in chunks:
            chunk_scores.append(c["cosine_score"])

        finding_parts = []
        if chunks:
            for c in chunks:
                meta = c.get("metadata", {})
                source = f"[{meta.get('filename', 'Doc')} p.{meta.get('page_number', '?')}]"
                finding_parts.append(f"{source}: {c['content'][:500]}")

        if should_use_web_search(top_score, rag_result["collection_empty"]):
            web_used = True
            web_results = web_search(question)
            for r in web_results:
                finding_parts.append(f"[Web: {r['title']}]({r['url']}): {r['snippet']}")

        findings[f"[Gap Fill] {question}"] = "\n\n".join(finding_parts) if finding_parts else "No additional info found."

    logger.info(f"Gap filler addressed {len(gaps)} gaps")
    return {
        **state,
        "research_findings": findings,
        "chunk_scores": chunk_scores,
        "web_used": web_used,
    }
