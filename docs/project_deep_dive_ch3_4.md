
# CHAPTER 3: THE ARCHITECTURE — THE BLUEPRINT

## 3a. THE LAYERS

**Layer 1: User Interface (Frontend)**
Files: Everything under `frontend/src/`. React components in `components/`, API wrappers in `api/`, auth state in `auth/AuthContext.tsx`, validation in `lib/validators/`.
Responsibility: Renders the UI, handles user input, manages client-side auth state, communicates with backend via Axios.
If deleted: Users have no way to interact with the system. The backend API still works (you could use curl), but there is no application.

**Layer 2: API/Router Layer**
Files: `backend/api/v1/routers/` (7 router files) + `backend/api/v1/models/` (5 Pydantic model files).
Responsibility: Defines HTTP endpoints, validates request/response shapes, enforces authentication via `Depends(get_current_user)`, delegates to services.
If deleted: No HTTP interface. Services exist but nothing calls them.

**Layer 3: Service Layer (Business Logic)**
Files: `backend/services/auth_service.py`, `doc_service.py`, `chat_service.py`, `research_service.py`.
Responsibility: Orchestrates operations — calls repositories, invokes AI tools, handles error logic, computes confidence scores.
If deleted: Routers would need to contain all business logic directly. Tight coupling, zero reuse.

**Layer 4: AI Operations**
Files: `backend/rag/` (indexer + retriever), `backend/agent/` (graph + nodes + tools + prompts), `backend/report/docx_writer.py`.
Responsibility: PDF extraction, text chunking, embedding, vector search, LLM synthesis, LangGraph agent orchestration, DOCX generation.
If deleted: The entire AI capability vanishes. The app becomes a file storage system with chat that returns nothing useful.

**Layer 5: Data Access (Repository Pattern)**
Files: `backend/repositories/` (6 repository files).
Responsibility: Raw SQL queries encapsulated in functions. Each repository handles one domain entity. Never imported directly by routers — only by services.
If deleted: Services would need inline SQL. Database operations would be scattered across the codebase.

**Layer 6: Data Storage**
Files: `backend/database/db_client.py` (PostgreSQL pool + DDL), `backend/storage/` (local + Supabase file storage).
Responsibility: Connection pooling, schema creation, file persistence.
If deleted: No data survives between server restarts. Everything is in-memory only.

**Layer 7: Authentication & Security**
Files: `backend/auth/` (jwt_handler, password_handler, dependencies), `backend/middleware/rate_limiter.py`, `backend/admin/controls.py`.
Responsibility: Password hashing, JWT creation/verification, request authentication, rate limiting, AI kill-switch.
If deleted: Anyone can access any endpoint. No identity, no protection.

## 3b. THE MONOREPO STRUCTURE

`README.md` — Project documentation. Setup instructions. Phase checklist (outdated — shows only Phase 1 complete but all are built).

`.env.example` — 118-line environment template with inline comments. This is NOT the actual `.env` (which is gitignored). It documents every configurable value in the system. Delete it and new developers have no idea what environment variables exist.

`.gitignore` — Excludes `.env`, `__pycache__/`, `node_modules/`, `uploads/`, `reports/`, `.chroma/`. Critical because committing `.env` exposes API keys. Committing `uploads/` would put user PDFs in version control.

`backend/` — The entire Python/FastAPI backend. Lives at root level because it is a peer to `frontend/`, not nested inside it. This is a monorepo pattern — one repo, multiple deployable units.

`frontend/` — The entire React/Vite frontend. Deployed separately (to Vercel) from the backend (to Render).

`eval_dashboard/` — Streamlit evaluation tool. Separate from both backend and frontend because it runs as its own process and has its own `requirements.txt`. It communicates with the backend via HTTP, not imports.

`docs/` — Two internal documents: `db_optimization_plan.md` (explains the connection pooling rewrite) and `technical_breakdown.txt` (a full technical summary of all features). These are developer documentation, not user-facing.

`DocMind_AI_SRS_v1.md` and `v2.md` — Software Requirements Specification documents (124KB and 122KB). Formal requirements documents. At root level because they describe the entire project, not a specific module.

## 3c. TECHNOLOGY CHOICES

**FastAPI** vs Flask vs Django:
FastAPI was chosen because it provides automatic request validation via Pydantic models (every request body is type-checked before your code runs), built-in OpenAPI documentation, native async support, and `Depends()` for dependency injection (used for `get_current_user`). Flask would require manual validation. Django would bring an ORM the project explicitly avoided.
**Verdict:** Right choice. The Pydantic integration alone saves hundreds of lines of validation code.

**psycopg2 (raw SQL)** vs SQLAlchemy vs Prisma:
The project uses hand-written SQL with parameterized queries. This gives full control over query optimization and avoids ORM overhead. The `ThreadedConnectionPool` is tuned for Supabase's 15-connection limit.
**Critique:** For a project this size, SQLAlchemy with its ORM would have been fine and would prevent SQL injection bugs more systematically. The raw SQL approach works but requires discipline — every query must use `%s` parameterized queries (which this code does correctly).

**ChromaDB** vs Pinecone vs Weaviate vs pgvector:
ChromaDB was chosen because it works locally with zero setup (`PersistentClient`) and can switch to cloud (`CloudClient`) by changing environment variables. Pinecone requires a cloud account even for development. pgvector would keep everything in PostgreSQL but has worse search performance at scale.
**Verdict:** Right choice for a project that needs local-first development with production cloud deployment.

**LangGraph** vs AutoGen vs CrewAI vs raw Python loops:
LangGraph was chosen because the Deep Research agent needs a conditional loop (reflect → gap-fill → reflect again). A simple LangChain chain cannot loop. AutoGen is designed for multi-agent conversations, not document-grounded research. CrewAI adds unnecessary abstraction.
**Verdict:** Perfect fit. The reflect-loop is the killer feature that justifies the dependency.

**Gemini 2.5 Flash** vs GPT-4 vs Claude vs open-source:
Gemini was chosen because it offers a generous free tier for development, fast inference, and the `langchain-google-genai` wrapper provides both chat and embedding models from a single API key.
**Verdict:** Practical choice for a student project. The code is provider-agnostic enough (via LangChain wrappers) that swapping to GPT-4 would only require changing model names.

**Tailwind CSS** vs vanilla CSS vs Material UI:
Tailwind provides utility classes that keep styling co-located with components. Combined with shadcn/ui (which generates accessible, customizable components), it eliminates the need for a heavy component library.
**Verdict:** Modern standard. Right choice.

---

# CHAPTER 4: BUILDING IT FROM SCRATCH

## PHASE 1: Project Skeleton & Configuration

**WHAT WAS DONE:**
Three files formed the foundation: `backend/config.py`, `backend/database/db_client.py`, and `backend/main.py`.

`config.py` was written first. It defines a `Settings` class using `pydantic-settings` that reads 50+ environment variables with defaults:
```python
class Settings(BaseSettings):
    ENVIRONMENT: str = "local"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/docmind"
    GEMINI_API_KEY: str = ""
    # ... 50+ more fields
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
```
The `@lru_cache()` decorator on `get_settings()` ensures this class is instantiated exactly once and reused everywhere.

**CONCEPT: Environment Variables**
*Real-world analogy:* You own a coffee shop chain. Each location needs a slightly different recipe — more sugar downtown, less milk uptown. You don't rewrite the recipe book for each location. You tape a note to the fridge: "SUGAR_AMOUNT=2tsp". Environment variables are those sticky notes. They let the same code behave differently depending on where it runs.
*In this codebase:* The `.env` file contains secrets (API keys, database passwords) and configuration (chunk sizes, rate limits). `config.py` reads them all into a typed Python object so the rest of the code never touches `os.getenv` directly.
*Interview Q:* "Why not hardcode configuration values?"
*Answer:* "Hardcoded values mean I need different code for local vs production. With env vars, the same Docker image (or code) works everywhere — I just change the env file. Also, secrets like API keys must never appear in source code because they'd be exposed in version control."

**MISTAKE:** The `Settings` class has `model_config = SettingsConfigDict(env_file=".env")` which looks for `.env` relative to the working directory. If you run the server from a different directory, it won't find the file. A more robust approach would use `Path(__file__).parent / ".env"` for an absolute path.

## PHASE 2: Database Schema & Connection Pooling

**WHAT WAS DONE:**
`db_client.py` contains both the connection pool logic and all DDL (Data Definition Language — the SQL that creates tables).

The pool is created on server startup in `main.py`:
```python
async def lifespan(app):
    init_pool()              # Creates ThreadedConnectionPool
    mark_stale_jobs_failed() # Cleanup stuck research jobs
    cleanup_expired_jobs()   # Delete old reports
    yield
    close_pool()             # Returns all connections
```

Tables are created lazily — not at startup, but on the first database request. This is because the DDL contains 10+ CREATE TABLE statements, and running them at startup would delay the health check response on Render (causing container restarts).

**CONCEPT: Connection Pooling**
*Real-world analogy:* Imagine a hotel with 10 phone lines. When a guest needs to call, they pick up a line, use it, and hang up. If all 10 are busy, they wait. Without pooling, the hotel would install a new phone line for every call and rip it out when done — expensive and slow.
*In this codebase:* `ThreadedConnectionPool(minconn=2, maxconn=10)` keeps 2 connections always open and can scale to 10. `get_db()` borrows a connection, uses it inside a `with` block, and returns it via `putconn()`. It never closes connections.
*Interview Q:* "Why ThreadedConnectionPool and not SimpleConnectionPool?"
*Answer:* "FastAPI runs synchronous endpoints in a thread pool. Multiple threads handle requests concurrently. SimpleConnectionPool is not thread-safe — two threads could grab the same connection. ThreadedConnectionPool uses internal locks to prevent this."

**CONCEPT: Lazy Initialization with Double-Checked Locking**
*Real-world analogy:* A restaurant only turns on the kitchen lights when the first customer arrives. But if two customers arrive simultaneously, you don't want both of them trying to flip the switch. One person locks the door, checks if the lights are on, flips them if not, then unlocks.
*In this codebase:* `_ensure_db()` checks `_db_initialized`. If False, it acquires `_db_init_lock`, checks again (double-check), runs DDL, then sets the flag. This prevents two concurrent first-requests from both running CREATE TABLE.

**MISTAKE:** The DDL is embedded as raw SQL strings inside `db_client.py`. A production project would use a migration tool like Alembic to version-control schema changes. Adding a column later requires manually writing `ALTER TABLE` inside the DDL function (which was actually done — see the `eval_mode` migration block).

## PHASE 3: Authentication System

**WHAT WAS DONE:**
Four files implement auth: `auth/jwt_handler.py` (create/verify JWTs), `auth/password_handler.py` (bcrypt hash/verify), `auth/dependencies.py` (FastAPI `get_current_user` dependency), and `services/auth_service.py` (orchestration).

The login flow:
1. User sends `{email, password}` to `POST /api/v1/auth/login`
2. `auth_service.login()` finds user by email, verifies bcrypt hash
3. Creates JWT access token (15 min): `jwt.encode({user_id, email, iat, exp}, SECRET, HS256)`
4. Creates UUID refresh token, SHA-256 hashes it, stores hash in DB
5. Sets raw refresh token as httpOnly cookie
6. Returns `{access_token, user}` in response body

**CONCEPT: JWT (JSON Web Token)**
*Real-world analogy:* A concert wristband. When you enter, security checks your ticket (login). They give you a wristband stamped with your name and a timestamp. For the next 3 hours, you can walk in and out by showing the wristband — no one re-checks your ticket. But after 3 hours, the wristband expires.
*In this codebase:* The JWT contains `user_id`, `email`, `iat` (issued at), and `exp` (expires in 15 minutes). Every protected endpoint calls `get_current_user()` which decodes the JWT and extracts the user identity without hitting the database.
*Interview Q:* "Why 15 minutes for access tokens?"
*Answer:* "Short-lived tokens limit the damage if one is stolen. 15 minutes means even if someone intercepts the token, it's useless after a quarter hour. We use refresh tokens (7 days, stored as hashed values in the DB) to get new access tokens without re-login."

**CONCEPT: Refresh Token Rotation**
*Real-world analogy:* Each time you use your parking garage key card, the old one is deactivated and you get a new one. If someone copied your old card, it won't work.
*In this codebase:* `auth_service.refresh_tokens()` at line 126-132: revokes the old token, creates a new one, stores its hash, sets a new cookie. If an attacker steals and uses your refresh token, the legitimate user's next refresh attempt fails (because the token was already rotated), alerting them to a compromise.

## PHASE 4: RAG Pipeline & Document Management

**WHAT WAS DONE:**
`rag/indexer.py` handles PDF ingestion. `rag/retriever.py` handles search. `services/doc_service.py` orchestrates the upload flow.

The indexing pipeline in `indexer.py`:
```python
def index_document(user_id, document_id, file_path, filename):
    pages = extract_text(file_path)         # pdfplumber page-by-page
    chunks = chunk_pages(pages)              # RecursiveCharacterTextSplitter
    embeddings = embed_chunks(chunks)        # gemini-embedding-001
    store_in_chroma(user_id, document_id, chunks, embeddings)
```

**CONCEPT: RAG (Retrieval-Augmented Generation)**
*Real-world analogy:* Imagine asking a librarian a question. Instead of answering from memory (which might be wrong), they first go to the shelves, pull out relevant books, read the relevant pages, and THEN answer you — citing which book and page they found it on. RAG is that librarian.
*In this codebase:* "Retrieval" = search ChromaDB for chunks matching the query. "Augmented" = inject those chunks into the LLM prompt. "Generation" = the LLM writes the answer using those chunks as evidence. The key files are `rag/retriever.py` (retrieval) and `chat_service.py` (augmentation + generation).

**CONCEPT: Text Chunking**
*Real-world analogy:* You cannot photocopy an entire book and hand it to someone asking a question. You find the relevant paragraph and photocopy just that. Chunking is cutting the book into paragraph-sized pieces ahead of time so you can find the right one fast.
*In this codebase:* `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)` cuts text into 1000-character pieces. The 200-character overlap ensures concepts that span two chunks appear in both. The splitter tries to break on paragraph boundaries first, then sentences, then words.
*Interview Q:* "Why 1000 characters and not 500 or 2000?"
*Answer:* "Too small (500) loses context — a chunk might contain half a sentence. Too large (2000) dilutes the embedding — the vector represents too many topics at once, reducing retrieval precision. 1000 is roughly one paragraph. The overlap of 200 ensures edge concepts are not lost."

## PHASE 5: LangGraph Deep Research Agent

**WHAT WAS DONE:**
`agent/graph.py` defines a 6-node state machine:

```python
graph.add_node("planner", planner_node)
graph.add_node("researcher", researcher_node)
graph.add_node("reflector", reflector_node)
graph.add_node("gap_filler", gap_filler_node)
graph.add_node("synthesizer", synthesizer_node)
graph.add_node("writer", writer_node)

graph.add_edge(START, "planner")
graph.add_edge("planner", "researcher")
graph.add_edge("researcher", "reflector")
graph.add_conditional_edges("reflector", _should_fill_gaps, {...})
graph.add_edge("gap_filler", "reflector")
graph.add_edge("synthesizer", "writer")
graph.add_edge("writer", END)
```

The conditional edge `_should_fill_gaps` checks: are there gaps AND have we iterated fewer than 3 times? If yes, go to gap_filler (which loops back to reflector). If no, go to synthesizer.

**CONCEPT: State Machine / Agentic Workflow**
*Real-world analogy:* A car wash. Your car enters, goes through soap, rinse, wax, dry — each station does one job and passes the car to the next. But imagine one station is a quality inspector. If the car is still dirty, it sends it BACK to the soap station. That loop is what makes this a state machine, not a simple pipeline.
*In this codebase:* `AgentState` is the "car" — a TypedDict carrying `topic`, `sub_questions`, `research_findings`, `reflection_gaps`, `iteration_count`, etc. Each node reads from state, does work, and returns updated state. The reflector is the quality inspector — if it finds gaps, the car goes back for more washing.

**MISTAKE:** The researcher node processes sub-questions sequentially, not in parallel. Each sub-question involves an LLM call + potentially a web search. For 5 sub-questions, this means 5x sequential latency. Using `asyncio.gather()` or threading could cut research time dramatically.

## PHASE 6: Frontend Architecture

**WHAT WAS DONE:**
React 19 + Vite + TypeScript + Tailwind v4 + shadcn/ui. The app structure:

- `App.tsx` defines routes with React Router v7
- `auth/AuthContext.tsx` provides global auth state
- `api/client.ts` is the Axios instance with interceptors
- `api/*.api.ts` files wrap each backend domain
- `components/` organized by feature (auth, chat, documents, research, admin, landing)
- `lib/validators/` has Zod schemas mirroring backend Pydantic validators

The Axios interceptor in `client.ts` is the most sophisticated frontend code. When a 401 occurs:
1. Check if we're already refreshing. If yes, push this request onto `failedQueue`.
2. If not, set `isRefreshing = true`, call `/auth/refresh`.
3. On success, replay the original request with the new token.
4. Process the queue — all other failed requests get the new token too.
5. On failure, call `onAuthFailure()` which triggers `logout()`.

This prevents a cascade where 5 simultaneous 401s trigger 5 refresh calls.

**CONCEPT: Protected Routes**
*Real-world analogy:* A bouncer at a VIP section. If you have a wristband (access token), you walk in. If not, you are redirected to the entrance (login page). If you are still being checked (loading), you wait.
*In this codebase:* `ProtectedRoute.tsx` checks `accessToken` from `useAuth()`. If loading, shows skeleton. If no token, redirects to `/login`. If token exists, renders children.
