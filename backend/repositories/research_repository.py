import json
from datetime import datetime, timedelta, timezone

from database.db_client import get_db
from config import get_settings

settings = get_settings()


def create_job(user_id: str, topic: str) -> dict:
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.RESEARCH_JOB_RETENTION_DAYS)
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO research_jobs (user_id, topic, status, expires_at)
                VALUES (%s, %s, 'queued', %s)
                RETURNING id, user_id, topic, status, progress, confidence, confidence_score,
                          report_path, error_message, created_at, updated_at
                """,
                (user_id, topic, expires_at),
            )
            return dict(cur.fetchone())


def find_by_id(job_id: str) -> dict | None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM research_jobs WHERE id = %s", (job_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def find_active_by_user(user_id: str) -> dict | None:
    active_states = ('queued', 'planning', 'researching', 'reflecting', 'synthesizing', 'writing')
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM research_jobs WHERE user_id = %s AND status = ANY(%s) LIMIT 1",
                (user_id, list(active_states)),
            )
            row = cur.fetchone()
            return dict(row) if row else None


def find_history_by_user(user_id: str, limit: int | None = None) -> list[dict]:
    limit = limit or settings.RESEARCH_JOB_HISTORY_LIMIT
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id, topic, status, confidence, confidence_score,
                       report_path, error_message, created_at, updated_at
                FROM research_jobs WHERE user_id = %s
                ORDER BY created_at DESC LIMIT %s
                """,
                (user_id, limit),
            )
            return [dict(row) for row in cur.fetchall()]


def update_status(job_id: str, status: str, error_message: str | None = None) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE research_jobs SET status = %s, error_message = %s, updated_at = NOW()
                WHERE id = %s
                """,
                (status, error_message, job_id),
            )


def update_progress(job_id: str, progress: dict) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE research_jobs SET progress = %s, updated_at = NOW() WHERE id = %s",
                (json.dumps(progress), job_id),
            )


def complete_job(job_id: str, report_path: str, confidence: str, confidence_score: float) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE research_jobs
                SET status = 'complete', report_path = %s, confidence = %s,
                    confidence_score = %s, updated_at = NOW()
                WHERE id = %s
                """,
                (report_path, confidence, confidence_score, job_id),
            )


def cancel_job(job_id: str) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE research_jobs SET status = 'cancelled', updated_at = NOW() WHERE id = %s",
                (job_id,),
            )


def mark_stale_jobs_failed() -> int:
    """Mark stuck jobs as failed. Returns count of affected jobs."""
    threshold = datetime.now(timezone.utc) - timedelta(minutes=settings.STALE_JOB_TIMEOUT_MINUTES)
    active_states = ('queued', 'planning', 'researching', 'reflecting', 'synthesizing', 'writing')
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE research_jobs SET status = 'failed',
                    error_message = 'Job was interrupted by a server restart.',
                    updated_at = NOW()
                WHERE status = ANY(%s) AND updated_at < %s
                RETURNING id
                """,
                (list(active_states), threshold),
            )
            return cur.rowcount


def cleanup_expired_jobs() -> int:
    """Delete expired jobs and return count."""
    with get_db() as conn:
        with conn.cursor() as cur:
            # Get report paths before deleting
            cur.execute(
                "SELECT report_path FROM research_jobs WHERE expires_at < NOW() AND report_path IS NOT NULL"
            )
            paths = [row["report_path"] for row in cur.fetchall()]

            cur.execute("DELETE FROM research_jobs WHERE expires_at < NOW()")
            count = cur.rowcount

    # Clean up files
    if paths:
        _cleanup_report_files(paths)

    return count


def _cleanup_report_files(paths: list[str]) -> None:
    from pathlib import Path
    reports_dir = Path(__file__).resolve().parent.parent / "reports"
    for p in paths:
        fp = reports_dir / p if not p.startswith("/") else Path(p)
        if fp.exists():
            fp.unlink()
