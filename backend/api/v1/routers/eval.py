"""Eval API endpoints — protected by admin password header."""

from fastapi import APIRouter, Header, HTTPException, status

from config import get_settings
from api.v1.models.eval_models import (
    CleanupResponse,
    EvalResultDetail,
    EvalRunSummary,
    MessageResponse,
    SaveEvalResultsRequest,
    SaveEvalResultsResponse,
)
from repositories import eval_repository
from repositories import user_repository
from database.db_client import get_db
from utils.logger import logger

settings = get_settings()
router = APIRouter(prefix="/eval", tags=["Evaluation"])


def _verify_admin(password: str | None) -> None:
    """Verify admin password from header."""
    if password != settings.ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin password",
        )


@router.post("/results", response_model=SaveEvalResultsResponse, status_code=status.HTTP_201_CREATED)
async def save_results(
    body: SaveEvalResultsRequest,
    x_admin_password: str = Header(None),
):
    """Bulk save evaluation results from a RAGAS run."""
    _verify_admin(x_admin_password)

    if body.eval_mode not in ("rag_only", "full_pipeline"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="eval_mode must be 'rag_only' or 'full_pipeline'",
        )

    results_dicts = [r.model_dump() for r in body.results]
    count = eval_repository.save_results(body.run_id, body.eval_mode, results_dicts)
    logger.info(f"Saved {count} eval results for run {body.run_id[:8]} ({body.eval_mode})")
    return {"run_id": body.run_id, "eval_mode": body.eval_mode, "count": count}


@router.get("/runs", response_model=list[EvalRunSummary])
async def list_runs(x_admin_password: str = Header(None)):
    """List all eval runs with aggregated averages."""
    _verify_admin(x_admin_password)
    return eval_repository.get_all_runs()


@router.get("/runs/{run_id}", response_model=list[EvalResultDetail])
async def get_run_details(run_id: str, x_admin_password: str = Header(None)):
    """Get per-question detail for a specific eval run."""
    _verify_admin(x_admin_password)
    results = eval_repository.get_results_by_run(run_id)
    if not results:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return results


@router.delete("/runs/{run_id}", response_model=MessageResponse)
async def delete_run(run_id: str, x_admin_password: str = Header(None)):
    """Delete all results for a specific eval run."""
    _verify_admin(x_admin_password)
    count = eval_repository.delete_run(run_id)
    if count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    logger.info(f"Deleted eval run {run_id[:8]} ({count} results)")
    return {"message": f"Deleted {count} results"}


@router.delete("/sessions/cleanup", response_model=CleanupResponse)
async def cleanup_eval_sessions(x_admin_password: str = Header(None)):
    """Delete all chat sessions belonging to the eval bot user."""
    _verify_admin(x_admin_password)

    eval_user = user_repository.find_by_email("eval@docmind.ai")
    if not eval_user:
        return {"message": "Eval bot user not found — nothing to clean up", "sessions_deleted": 0}

    user_id = str(eval_user["id"])
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM chat_sessions WHERE user_id = %s", (user_id,))
            count = cur.rowcount

    logger.info(f"Cleaned up {count} eval bot chat sessions")
    return {"message": f"Deleted {count} eval sessions", "sessions_deleted": count}
