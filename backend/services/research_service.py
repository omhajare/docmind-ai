from fastapi import HTTPException, status

from config import get_settings
from repositories import research_repository
from utils.logger import logger

settings = get_settings()


def _check_ai_enabled():
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


def start_job(user_id: str, topic: str) -> dict:
    """Create a research job and schedule the background agent."""
    _check_ai_enabled()

    topic = topic.strip()
    if not topic:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Topic cannot be empty")
    if len(topic) > settings.MAX_RESEARCH_TOPIC_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Topic exceeds maximum length of {settings.MAX_RESEARCH_TOPIC_LENGTH} characters",
        )

    # Check for active jobs
    active = research_repository.find_active_by_user(user_id)
    if active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A research job is already in progress. Please wait for it to complete or cancel it.",
        )

    job = research_repository.create_job(user_id, topic)
    logger.info(f"Research job created: {job['id']} for user {user_id}")
    return {"job_id": str(job["id"]), "status": "queued"}


def run_research_agent(job_id: str, topic: str, user_id: str) -> None:
    """Execute the LangGraph research agent. Called as a BackgroundTask."""
    try:
        from agent.graph import research_graph
        initial_state = {
            "user_id": user_id,
            "job_id": job_id,
            "topic": topic,
            "sub_questions": [],
            "research_findings": {},
            "reflection_gaps": [],
            "iteration_count": 0,
            "chunk_scores": [],
            "web_used": False,
            "final_synthesis": "",
            "report_path": "",
        }
        research_graph.invoke(initial_state)
        logger.info(f"Research job completed: {job_id}")
    except Exception as e:
        logger.error(f"Research job failed: {job_id} — {e}")
        research_repository.update_status(job_id, "failed", error_message=str(e))


def get_job_status(user_id: str, job_id: str) -> dict:
    job = research_repository.find_by_id(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if str(job["user_id"]) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return _serialize_job(job)


def get_history(user_id: str) -> list[dict]:
    jobs = research_repository.find_history_by_user(user_id)
    return [_serialize_job(j) for j in jobs]


def cancel_job(user_id: str, job_id: str) -> dict:
    job = research_repository.find_by_id(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if str(job["user_id"]) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    active_states = ("queued", "planning", "researching", "reflecting", "synthesizing", "writing")
    if job["status"] in active_states:
        research_repository.cancel_job(job_id)
        logger.info(f"Research job cancelled: {job_id}")

    return {"message": "Job cancelled"}


def get_report_path(user_id: str, job_id: str) -> str:
    """Validate and return the absolute file path for download."""
    job = research_repository.find_by_id(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if str(job["user_id"]) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if job["status"] != "complete":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Report not ready yet")
    if not job["report_path"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report file not found")

    from pathlib import Path
    reports_dir = Path(__file__).resolve().parent.parent / "reports"
    file_path = reports_dir / job["report_path"]
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report file not found on disk")

    return str(file_path)


def _serialize_job(job: dict) -> dict:
    import json
    progress = job.get("progress")
    if isinstance(progress, str):
        progress = json.loads(progress)

    return {
        "job_id": str(job["id"]),
        "topic": job["topic"],
        "status": job["status"],
        "progress": progress,
        "confidence": job.get("confidence"),
        "confidence_score": job.get("confidence_score"),
        "report_path": job.get("report_path"),
        "error_message": job.get("error_message"),
        "created_at": job["created_at"].isoformat() if job.get("created_at") else None,
        "updated_at": job["updated_at"].isoformat() if job.get("updated_at") else None,
    }
