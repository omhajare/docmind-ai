from langchain_google_genai import ChatGoogleGenerativeAI

from config import get_settings
from agent.prompts import SYNTHESIZER_PROMPT
from repositories import research_repository
from utils.logger import logger

settings = get_settings()


def synthesizer_node(state: dict) -> dict:
    """Synthesize all findings into a coherent narrative."""
    job_id = state["job_id"]

    job = research_repository.find_by_id(job_id)
    if job and job["status"] == "cancelled":
        return state

    research_repository.update_status(job_id, "synthesizing")

    findings_text = "\n\n---\n\n".join(
        f"**{q}**\n{f}" for q, f in state.get("research_findings", {}).items()
    )

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=settings.GEMINI_API_KEY)
    prompt = SYNTHESIZER_PROMPT.format(topic=state["topic"], findings=findings_text)
    response = llm.invoke(prompt)

    logger.info(f"Synthesizer completed for job {job_id}")
    return {**state, "final_synthesis": response.content}
