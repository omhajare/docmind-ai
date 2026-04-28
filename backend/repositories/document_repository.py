from database.db_client import get_db


def create(user_id: str, filename: str, storage_path: str, chunk_count: int, file_size_kb: int) -> dict:
    """Insert a new document record."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO documents (user_id, filename, storage_path, chunk_count, file_size_kb)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, user_id, filename, storage_path, chunk_count, file_size_kb, uploaded_at
                """,
                (user_id, filename, storage_path, chunk_count, file_size_kb),
            )
            return dict(cur.fetchone())


def find_by_user(user_id: str) -> list[dict]:
    """Get all documents for a user, ordered by uploaded_at desc."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id, filename, storage_path, chunk_count, file_size_kb, uploaded_at
                FROM documents WHERE user_id = %s ORDER BY uploaded_at DESC
                """,
                (user_id,),
            )
            return [dict(row) for row in cur.fetchall()]


def find_by_id(document_id: str) -> dict | None:
    """Find a document by ID."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM documents WHERE id = %s", (document_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def count_by_user(user_id: str) -> int:
    """Count documents for a user."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM documents WHERE user_id = %s", (user_id,))
            return cur.fetchone()["cnt"]


def delete(document_id: str) -> None:
    """Delete a document record (cascades to suggested_questions)."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM documents WHERE id = %s", (document_id,))


# ─── Suggested Questions ─────────────────────────────────────

def get_suggested_questions(document_id: str) -> list[dict]:
    """Get cached suggested questions for a document."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, question, created_at FROM suggested_questions WHERE document_id = %s ORDER BY created_at",
                (document_id,),
            )
            return [dict(row) for row in cur.fetchall()]


def save_suggested_questions(document_id: str, user_id: str, questions: list[str]) -> list[dict]:
    """Store generated questions for a document."""
    results = []
    with get_db() as conn:
        with conn.cursor() as cur:
            for q in questions:
                cur.execute(
                    """
                    INSERT INTO suggested_questions (document_id, user_id, question)
                    VALUES (%s, %s, %s)
                    RETURNING id, question, created_at
                    """,
                    (document_id, user_id, q),
                )
                results.append(dict(cur.fetchone()))
    return results
