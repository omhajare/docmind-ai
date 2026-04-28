from agent.tools import rag_search, web_search
from rag.retriever import should_use_web_search
from repositories import research_repository
from utils.logger import logger


def researcher_node(state: dict) -> dict:
    """Research each sub-question using RAG and optional web search."""
    job_id = state["job_id"]
    user_id = state["user_id"]
    sub_questions = state.get("sub_questions", [])

    # Check cancellation
    job = research_repository.find_by_id(job_id)
    if job and job["status"] == "cancelled":
        return state

    research_repository.update_status(job_id, "researching")

    findings = state.get("research_findings", {})
    chunk_scores = state.get("chunk_scores", [])
    web_used = state.get("web_used", False)

    total = len(sub_questions)
    for i, question in enumerate(sub_questions):
        # Check cancellation at each sub-question
        job = research_repository.find_by_id(job_id)
        if job and job["status"] == "cancelled":
            return state

        # Update progress
        research_repository.update_progress(job_id, {
            "current_step": f"Researching sub-question {i + 1} of {total}",
            "steps_done": i,
            "total_steps": total,
            "current_node": "researching",
        })

        # RAG search
        rag_result = rag_search(user_id, question)
        chunks = rag_result["chunks"]
        top_score = rag_result["top_score"]
        collection_empty = rag_result["collection_empty"]

        # Collect scores
        for c in chunks:
            chunk_scores.append(c["cosine_score"])

        # Build finding text
        finding_parts = []
        if chunks:
            for c in chunks:
                meta = c.get("metadata", {})
                source = f"[{meta.get('filename', 'Doc')} p.{meta.get('page_number', '?')}]"
                finding_parts.append(f"{source}: {c['content'][:500]}")

        # Conditional web search
        if should_use_web_search(top_score, collection_empty):
            web_used = True
            web_results = web_search(question)
            for r in web_results:
                finding_parts.append(f"[Web: {r['title']}]({r['url']}): {r['snippet']}")

        findings[question] = "\n\n".join(finding_parts) if finding_parts else "No relevant information found."
        logger.info(f"Researched sub-question {i + 1}/{total}: score={top_score:.2f}")

    return {
        **state,
        "research_findings": findings,
        "chunk_scores": chunk_scores,
        "web_used": web_used,
    }
