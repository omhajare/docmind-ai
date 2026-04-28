import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

from config import get_settings

settings = get_settings()


def get_connection():
    """Create a new database connection."""
    return psycopg2.connect(settings.DATABASE_URL, cursor_factory=RealDictCursor)


@contextmanager
def get_db():
    """Context manager that yields a connection and handles commit/rollback."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create all tables if they do not exist."""
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

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)
