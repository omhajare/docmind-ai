# Database Optimization Implementation Plan

This plan outlines the exact changes required to implement **Connection Pooling** and **Lazy Database Initialization** in the DocMind AI backend. This will significantly reduce API latency and fix potential startup timeouts on deployment platforms like Render.

## Goal 1: Connection Pooling (Fixing Latency)
Currently, `psycopg2.connect()` is called on every query, adding 50-200ms of TCP/TLS handshake overhead per request.

**Strategy:** Use `psycopg2.pool.ThreadedConnectionPool` (FastAPI handles concurrent synchronous endpoints in separate threads, so `ThreadedConnectionPool` is safer than `SimpleConnectionPool`).

## Goal 2: Lazy Initialization (Fixing Startup Timeouts)
Currently, `init_db()` (which runs a massive DDL script to create 10+ tables) is called in the FastAPI `startup` event. This blocks the web server from binding to its port, often causing Render to kill the container for failing health checks.

**Strategy:** Defer `init_db()` until the very first time the application actually needs to read or write to the database.

---

## Required Changes

### 1. Update `backend/database/db_client.py`

**A. Import Pooling Module**
```python
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool  # <-- New import
from contextlib import contextmanager

from config import get_settings
from utils.logger import logger  # <-- Import logger for pool events
```

**B. Setup Global Pool and State Variables**
```python
settings = get_settings()

# Global variables
connection_pool = None
_db_initialized = False
```

**C. Create Pool Management Functions**
```python
def init_pool():
    """Initialize the global connection pool."""
    global connection_pool
    if connection_pool is None:
        try:
            # 1 to 20 connections is a good default for FastAPI
            connection_pool = pool.ThreadedConnectionPool(
                1, 20,
                dsn=settings.DATABASE_URL,
                cursor_factory=RealDictCursor
            )
            logger.info("Database connection pool created successfully.")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise

def close_pool():
    """Close all connections in the pool."""
    global connection_pool
    if connection_pool is not None:
        connection_pool.closeall()
        logger.info("Database connection pool closed.")
```

**D. Implement Lazy Initialization Wrapper**
```python
def ensure_db():
    """Run DDL scripts only once per application lifecycle."""
    global _db_initialized
    if not _db_initialized:
        logger.info("Performing lazy database initialization...")
        init_db()  # The existing DDL function
        _db_initialized = True
        logger.info("Lazy database initialization complete.")
```

**E. Rewrite `get_db()` Context Manager**
Replace the old `get_connection()` logic. Note how `yield conn` is wrapped to ensure lazy init, and `finally` uses `putconn()` instead of `close()`.

```python
@contextmanager
def get_db():
    """Context manager that yields a connection from the pool."""
    global connection_pool
    
    if connection_pool is None:
        # Fallback if someone calls get_db before init_pool
        init_pool()

    conn = connection_pool.getconn()
    try:
        # Ensure tables exist before yielding the connection
        ensure_db()
        
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        # Return connection to the pool instead of destroying it
        connection_pool.putconn(conn)
```

---

### 2. Update `backend/main.py`

**A. Import the new pool functions**
```diff
- from database.db_client import init_db
+ from database.db_client import init_pool, close_pool
```

**B. Modify the Startup Event**
Remove `init_db()` and replace it with `init_pool()`. This makes startup instant.

```python
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting DocMind AI v{settings.APP_VERSION} [{settings.ENVIRONMENT}]")
    
    # Initialize the pool, but DO NOT run init_db() here
    init_pool()

    # (Keep the existing stale job recovery logic...)
```

**C. Add a Shutdown Event**
Cleanly close the pool when the server stops.

```python
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down DocMind AI...")
    close_pool()
```

---

## Execution Order
1. Modify `backend/database/db_client.py` to add `psycopg2.pool` logic and `ensure_db()`.
2. Modify `backend/main.py` to remove `init_db` from startup and add `init_pool` / `close_pool` lifecycle events.
3. Test locally using `python -m uvicorn main:app --reload` to ensure the server boots instantly, and verify that the DB initializes cleanly upon the first API request.
