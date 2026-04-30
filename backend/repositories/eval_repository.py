"""CRUD operations for eval_results table."""

from database.db_client import get_db


def save_results(run_id: str, eval_mode: str, results: list[dict]) -> int:
    """Bulk insert eval results for a run. Returns count inserted."""
    with get_db() as conn:
        with conn.cursor() as cur:
            for r in results:
                passed = all(
                    r.get(m, 0) >= 0.70
                    for m in ("faithfulness", "answer_relevancy", "context_precision")
                )
                cur.execute(
                    """
                    INSERT INTO eval_results
                        (run_id, eval_mode, question, answer, faithfulness,
                         answer_relevancy, context_precision, passed)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        run_id,
                        eval_mode,
                        r.get("question", ""),
                        r.get("answer", ""),
                        r.get("faithfulness"),
                        r.get("answer_relevancy"),
                        r.get("context_precision"),
                        passed,
                    ),
                )
    return len(results)


def get_all_runs() -> list[dict]:
    """Get aggregated averages grouped by run_id, ordered by most recent first."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    run_id::TEXT as run_id,
                    eval_mode,
                    COUNT(*) as question_count,
                    ROUND(AVG(faithfulness)::NUMERIC, 4) as avg_faithfulness,
                    ROUND(AVG(answer_relevancy)::NUMERIC, 4) as avg_answer_relevancy,
                    ROUND(AVG(context_precision)::NUMERIC, 4) as avg_context_precision,
                    COUNT(*) FILTER (WHERE passed = TRUE) as passed_count,
                    MIN(evaluated_at) as evaluated_at
                FROM eval_results
                GROUP BY run_id, eval_mode
                ORDER BY MIN(evaluated_at) DESC
                """
            )
            rows = cur.fetchall()
            return [_serialize_run(row) for row in rows]


def get_results_by_run(run_id: str) -> list[dict]:
    """Get per-question detail for a specific run."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id::TEXT as id, run_id::TEXT as run_id, eval_mode,
                       question, answer, faithfulness, answer_relevancy,
                       context_precision, passed, evaluated_at
                FROM eval_results
                WHERE run_id = %s
                ORDER BY evaluated_at ASC
                """,
                (run_id,),
            )
            return [_serialize_result(row) for row in cur.fetchall()]


def delete_run(run_id: str) -> int:
    """Delete all results for a run. Returns count deleted."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM eval_results WHERE run_id = %s", (run_id,))
            return cur.rowcount


def _serialize_run(row: dict) -> dict:
    return {
        "run_id": str(row["run_id"]),
        "eval_mode": row["eval_mode"],
        "question_count": row["question_count"],
        "avg_faithfulness": float(row["avg_faithfulness"]) if row["avg_faithfulness"] else 0,
        "avg_answer_relevancy": float(row["avg_answer_relevancy"]) if row["avg_answer_relevancy"] else 0,
        "avg_context_precision": float(row["avg_context_precision"]) if row["avg_context_precision"] else 0,
        "passed_count": row["passed_count"],
        "evaluated_at": row["evaluated_at"].isoformat() if row.get("evaluated_at") else None,
    }


def _serialize_result(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "run_id": str(row["run_id"]),
        "eval_mode": row["eval_mode"],
        "question": row["question"],
        "answer": row.get("answer"),
        "faithfulness": float(row["faithfulness"]) if row["faithfulness"] is not None else None,
        "answer_relevancy": float(row["answer_relevancy"]) if row["answer_relevancy"] is not None else None,
        "context_precision": float(row["context_precision"]) if row["context_precision"] is not None else None,
        "passed": row["passed"],
        "evaluated_at": row["evaluated_at"].isoformat() if row.get("evaluated_at") else None,
    }
