from langchain_google_genai import ChatGoogleGenerativeAI

from config import get_settings
from agent.prompts import REFLECTOR_PROMPT
from repositories import research_repository
from utils.logger import logger

settings = get_settings()


def reflector_node(state: dict) -> dict:
    """Evaluate research coverage and identify gaps."""
    job_id = state["job_id"]

    job = research_repository.find_by_id(job_id)
    if job and job["status"] == "cancelled":
        return state

    research_repository.update_status(job_id, "reflecting")

    findings_text = "\n\n---\n\n".join(
        f"**{q}**\n{f}" for q, f in state.get("research_findings", {}).items()
    )

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=settings.GEMINI_API_KEY)
    prompt = REFLECTOR_PROMPT.format(topic=state["topic"], findings=findings_text)
    response = llm.invoke(prompt)

    content = response.content.strip()
    iteration_count = state.get("iteration_count", 0) + 1

    if "NO_GAPS" in content:
        gaps = []
    else:
        gaps = [g.strip() for g in content.split("\n") if g.strip()]

    logger.info(f"Reflector found {len(gaps)} gaps (iteration {iteration_count})")
    return {
        **state,
        "reflection_gaps": gaps,
        "iteration_count": iteration_count,
    }
