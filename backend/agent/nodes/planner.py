from langchain_google_genai import ChatGoogleGenerativeAI

from config import get_settings
from agent.prompts import PLANNER_PROMPT
from repositories import research_repository
from utils.logger import logger

settings = get_settings()


def planner_node(state: dict) -> dict:
    """Decompose research topic into sub-questions."""
    job_id = state["job_id"]
    topic = state["topic"]

    # Check cancellation
    job = research_repository.find_by_id(job_id)
    if job and job["status"] == "cancelled":
        return state

    research_repository.update_status(job_id, "planning")
    research_repository.update_progress(job_id, {
        "current_step": f"Thinking: How should I break down '{topic}' into focused sub-questions?",
        "current_node": "planning"
    })

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=settings.GEMINI_API_KEY)
    prompt = PLANNER_PROMPT.format(topic=topic, max_questions=settings.MAX_SUB_QUESTIONS)
    response = llm.invoke(prompt)

    questions = [q.strip() for q in response.content.strip().split("\n") if q.strip()]
    questions = questions[:settings.MAX_SUB_QUESTIONS]

    logger.info(f"Planner generated {len(questions)} sub-questions for job {job_id}")
    research_repository.update_progress(job_id, {
        "current_step": f"Thinking: I've divided the topic into {len(questions)} key areas to investigate.",
        "current_node": "planning"
    })
    return {**state, "sub_questions": questions}
