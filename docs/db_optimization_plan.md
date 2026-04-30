# Database Optimization Implementation Plan (v2 — Corrected)

This document describes the **implemented** changes to fix high API latency on the
Render + Supabase deployment stack.

---

## Root Causes of Latency

| Problem | Impact |
|---|---|
| `psycopg2.connect()` called on every request | +50–200 ms TCP/TLS handshake per request |
| `init_db()` (10+ DDL statements) blocked startup event | Render health check timeout → container restart |

---

## Goal 1 — Connection Pooling (`ThreadedConnectionPool`)

FastAPI runs synchronous endpoints in a thread pool. `ThreadedConnectionPool` is
thread-safe, while `SimpleConnectionPool` is not.

**Pool sizing:** Supabase free tier allows ~15 direct connections. The pool uses
`minconn=2, maxconn=10` to leave headroom for admin/pgAdmin sessions.

---

## Goal 2 — Lazy DDL Initialization

`init_db()` is deferred until the very first real API request. Startup now only
creates the connection pool (fast), so the server binds to its port immediately
and passes Render's health check.

---

## Goal 3 — Thread-Safety (`threading.Lock`)

Without a lock, two concurrent first-requests can both observe `_db_initialized = False`
and both run the DDL. A **double-checked lock** (`_db_init_lock`) prevents this.

---

## Bugs Fixed Over the Original Plan

### Bug 1 — Circular Recursion (Critical)

The original plan placed `ensure_db()` inside `get_db()`, but `init_db()` also
called `get_db()` to run DDL:

```
get_db() → ensure_db() → init_db() → get_db() → ensure_db() → ∞
```

**Fix:** Renamed to `_init_db_raw()` / `_run_ddl()`. The DDL path acquires a
raw connection directly from the pool — never through `get_db()`.

```
get_db() → _ensure_db() → _init_db_raw() ✓  (no recursion)
```

### Bug 2 — Supabase Connection Limit

Original plan: `maxconn=20` → exceeds Supabase free tier limit (~15).  
**Fix:** `minconn=2, maxconn=10`.

### Bug 3 — TOCTOU Race on `_db_initialized`

Original plan: no lock → two threads could both call DDL simultaneously.  
**Fix:** `threading.Lock` with double-checked locking pattern.

### Bug 4 — Deprecated `@app.on_event`

Original plan used `@app.on_event("startup/shutdown")` (deprecated since FastAPI 0.93).  
**Fix:** Modern `asynccontextmanager` lifespan passed to `FastAPI(lifespan=...)`.

### Bug 5 — Silent Pool Fallback in `get_db()`

Original plan: `if pool is None: init_pool()` silently hides mis-initialization.  
**Fix:** Raises `RuntimeError` with a clear message if the pool is not ready.

---

## Files Changed

### `backend/database/db_client.py`

| Added | Removed |
|---|---|
| `import threading`, `from psycopg2 import pool` | `get_connection()` |
| `connection_pool`, `_db_initialized`, `_db_init_lock` | Direct `psycopg2.connect()` calls |
| `init_pool()`, `close_pool()` | `init_db()` (public) |
| `_ensure_db()` with double-checked lock | `get_db()` closing connection |
| `_init_db_raw()`, `_run_ddl(conn)` | |
| `get_db()` using `putconn()` | |

### `backend/main.py`

| Added | Removed |
|---|---|
| `from contextlib import asynccontextmanager` | `from database.db_client import init_db` |
| `from database.db_client import init_pool, close_pool` | `@app.on_event("startup")` |
| `async def lifespan(app)` with `yield` | `@app.on_event("shutdown")` (never existed) |
| `FastAPI(lifespan=lifespan)` | `init_db()` call in startup |
| `init_pool()` in startup, `close_pool()` in shutdown | |

---

## Execution Order (Completed)

1. ✅ Rewrote `backend/database/db_client.py`
2. ✅ Rewrote `backend/main.py` startup/shutdown lifecycle

## Testing Checklist

- [ ] Server boots instantly (`Application startup complete` within ~1 s)
- [ ] First API request triggers lazy DDL (`Lazy database initialization complete` in logs)
- [ ] Subsequent requests do NOT re-run DDL
- [ ] Pool log line visible: `Database connection pool created (min=2, max=10)`
- [ ] Shutdown log: `Database connection pool closed`
- [ ] No `PoolError: connection pool exhausted` under load
