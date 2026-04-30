import threading
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
from contextlib import contextmanager

from config import get_settings
from utils.logger import logger

settings = get_settings()

# ─── Pool & Init State ───────────────────────────────────────
connection_pool: pool.ThreadedConnectionPool | None = None
_db_initialized = False
_db_init_lock = threading.Lock()  # Prevents TOCTOU race on first request


def init_pool():
    """Initialize the global ThreadedConnectionPool.

    minconn=2  — keep 2 warm connections at all times.
    maxconn=10 — Supabase free tier allows ~15 direct connections;
                 10 leaves headroom for admin/pgAdmin sessions.
    """
    global connection_pool
    if connection_pool is not None:
        return  # Already initialised
    try:
        connection_pool = pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            dsn=settings.DATABASE_URL,
            cursor_factory=RealDictCursor,
        )
        logger.info("Database connection pool created (min=2, max=10).")
    except Exception as e:
        logger.error(f"Failed to create connection pool: {e}")
        raise


def close_pool():
    """Close all connections in the pool (called on server shutdown)."""
    global connection_pool
    if connection_pool is not None:
        connection_pool.closeall()
        connection_pool = None
        logger.info("Database connection pool closed.")


def _ensure_db():
    """Run DDL exactly once per application lifecycle.

    Uses a threading.Lock to prevent multiple concurrent first-requests
    from each running init_db() simultaneously (TOCTOU race condition).

    IMPORTANT: calls _init_db_raw() which acquires a connection directly
    from the pool — NOT via get_db() — to avoid circular recursion:
        get_db() → _ensure_db() → init_db() → get_db() → ∞
    """
    global _db_initialized
    if _db_initialized:
        return
    with _db_init_lock:
        # Double-checked locking: another thread may have initialised
        # between our first check and acquiring the lock.
        if not _db_initialized:
            logger.info("Performing lazy database initialization...")
            _init_db_raw()
            _db_initialized = True
            logger.info("Lazy database initialization complete.")


@contextmanager
def get_db():
    """Context manager that yields a pooled connection.

    • Raises RuntimeError if the pool was never started (init_pool not called).
    • Calls _ensure_db() to lazily run DDL on the very first request.
    • Returns the connection to the pool via putconn() in the finally block.
    """
    if connection_pool is None:
        raise RuntimeError(
            "Connection pool is not initialised. "
            "Ensure init_pool() is called during application startup."
        )

    conn = connection_pool.getconn()
    try:
        _ensure_db()
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        # Return to pool — never close it
        connection_pool.putconn(conn)


# ─── DDL ─────────────────────────────────────────────────────

def _init_db_raw():
    """Run the full DDL using a raw pool connection (NOT via get_db).

    This avoids the circular call chain:
        get_db() → _ensure_db() → _init_db_raw()  ✓  (no recursion)

    Called exclusively by _ensure_db().
    """
    if connection_pool is None:
        raise RuntimeError("Cannot run init_db: pool is not initialised.")

    conn = connection_pool.getconn()
    try:
        _run_ddl(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        connection_pool.putconn(conn)


def _run_ddl(conn):
    """Execute all CREATE TABLE / CREATE INDEX statements."""
    ddl = """
    -- Enable uuid generation
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";

    -- Users
    CREATE TABLE IF NOT EXISTS users (
        id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email         TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        full_name     TEXT NOT NULL,
        is_active     BOOLEAN NOT NULL DEFAULT TRUE,
        last_login    TIMESTAMPTZ,
        created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

    -- Refresh Tokens
    CREATE TABLE IF NOT EXISTS refresh_tokens (
        id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        token_hash  TEXT NOT NULL UNIQUE,
        expires_at  TIMESTAMPTZ NOT NULL,
        is_revoked  BOOLEAN NOT NULL DEFAULT FALSE,
        created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens (user_id);
    CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_hash ON refresh_tokens (token_hash);

    -- Password Reset Tokens
    CREATE TABLE IF NOT EXISTS password_reset_tokens (
        id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        token_hash  TEXT NOT NULL UNIQUE,
        expires_at  TIMESTAMPTZ NOT NULL,
        used        BOOLEAN NOT NULL DEFAULT FALSE,
        created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_prt_token_hash ON password_reset_tokens (token_hash);

    -- Documents
    CREATE TABLE IF NOT EXISTS documents (
        id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        filename      TEXT NOT NULL,
        storage_path  TEXT NOT NULL,
        chunk_count   INTEGER NOT NULL DEFAULT 0,
        file_size_kb  INTEGER,
        uploaded_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents (user_id);

    -- Suggested Questions
    CREATE TABLE IF NOT EXISTS suggested_questions (
        id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        document_id  UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
        user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        question     TEXT NOT NULL,
        created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_sq_document_id ON suggested_questions (document_id);

    -- Chat Sessions
    CREATE TABLE IF NOT EXISTS chat_sessions (
        id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        title       TEXT NOT NULL DEFAULT 'New Chat',
        created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions (user_id);

    -- Chat Messages
    CREATE TABLE IF NOT EXISTS chat_messages (
        id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        session_id   UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
        user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        role         TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
        content      TEXT NOT NULL,
        sources      JSONB,
        tools_used   JSONB,
        confidence   TEXT CHECK (confidence IN ('high', 'medium', 'low', NULL)),
        created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages (session_id);
    CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id ON chat_messages (user_id);

    -- Research Jobs
    CREATE TABLE IF NOT EXISTS research_jobs (
        id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        topic            TEXT NOT NULL,
        status           TEXT NOT NULL DEFAULT 'queued'
                         CHECK (status IN ('queued','planning','researching',
                                           'reflecting','synthesizing','writing',
                                           'complete','failed','cancelled')),
        progress         JSONB,
        report_path      TEXT,
        confidence       TEXT CHECK (confidence IN ('high', 'medium', 'low', NULL)),
        confidence_score FLOAT,
        error_message    TEXT,
        expires_at       TIMESTAMPTZ,
        created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_research_jobs_user_id ON research_jobs (user_id);
    CREATE INDEX IF NOT EXISTS idx_research_jobs_status ON research_jobs (status);
    CREATE INDEX IF NOT EXISTS idx_research_jobs_expires_at ON research_jobs (expires_at);

    -- App Settings
    CREATE TABLE IF NOT EXISTS app_settings (
        key    TEXT PRIMARY KEY,
        value  TEXT NOT NULL
    );
    INSERT INTO app_settings (key, value) VALUES ('ai_enabled', 'true')
    ON CONFLICT (key) DO NOTHING;

    -- Eval Results
    CREATE TABLE IF NOT EXISTS eval_results (
        id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        run_id            UUID NOT NULL,
        eval_mode         TEXT NOT NULL DEFAULT 'full_pipeline'
                          CHECK (eval_mode IN ('rag_only', 'full_pipeline')),
        question          TEXT NOT NULL,
        answer            TEXT,
        faithfulness      FLOAT,
        answer_relevancy  FLOAT,
        context_precision FLOAT,
        passed            BOOLEAN,
        evaluated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_eval_results_run_id ON eval_results (run_id);
    """

    with conn.cursor() as cur:
        cur.execute(ddl)

        # Migration: add eval_mode column if table existed before this update
        cur.execute("""
            DO $$
            BEGIN
                ALTER TABLE eval_results
                    ADD COLUMN eval_mode TEXT NOT NULL DEFAULT 'full_pipeline'
                    CHECK (eval_mode IN ('rag_only', 'full_pipeline'));
            EXCEPTION WHEN duplicate_column THEN
                NULL;
            END $$;
        """)

        # Create index after column is guaranteed to exist
        cur.execute("CREATE INDEX IF NOT EXISTS idx_eval_results_eval_mode ON eval_results (eval_mode);")
