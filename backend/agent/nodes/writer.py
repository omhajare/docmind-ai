from pathlib import Path

from config import get_settings
from report.docx_writer import generate_report
from repositories import research_repository
from utils.logger import logger

settings = get_settings()

# Reports dir at backend/reports/
REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "reports"


def writer_node(state: dict) -> dict:
    """Generate DOCX report and complete the job."""
    job_id = state["job_id"]
    user_id = state["user_id"]

    job = research_repository.find_by_id(job_id)
    if job and job["status"] == "cancelled":
        return state

    research_repository.update_status(job_id, "writing")

    # Compute confidence
    chunk_scores = state.get("chunk_scores", [])
    web_used = state.get("web_used", False)
    base_score = sum(chunk_scores) / len(chunk_scores) if chunk_scores else 0.0
    penalty = settings.WEB_SEARCH_PENALTY if web_used else 0.0
    final_score = max(0.0, base_score - penalty)

    if final_score >= settings.RESEARCH_CONFIDENCE_HIGH:
        confidence = "high"
    elif final_score >= settings.RESEARCH_CONFIDENCE_MEDIUM:
        confidence = "medium"
    else:
        confidence = "low"

    # Generate DOCX
    report_filename = f"docmind_report_{job_id[:8]}.docx"
    user_dir = REPORTS_DIR / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    report_path_abs = user_dir / report_filename

    generate_report(
        filepath=str(report_path_abs),
        topic=state["topic"],
        sub_questions=state.get("sub_questions", []),
        research_findings=state.get("research_findings", {}),
        reflection_gaps=state.get("reflection_gaps", []),
        final_synthesis=state.get("final_synthesis", ""),
        confidence=confidence,
        confidence_score=round(final_score, 4),
        web_used=web_used,
    )

    storage_path = f"{user_id}/{report_filename}"

    # Update job as complete
    research_repository.complete_job(job_id, storage_path, confidence, round(final_score, 4))

    logger.info(f"Writer completed: {report_filename} confidence={confidence} ({final_score:.2f})")
    return {**state, "report_path": storage_path}
