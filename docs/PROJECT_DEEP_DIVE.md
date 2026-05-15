# PROJECT DEEP DIVE â€” DocMind AI

> Written after reading every single file in this repository. Every claim is backed by actual code. Nothing is guessed.

---

# CHAPTER 1: WHY THIS PROJECT EXISTS

Imagine you are a university researcher. You have 15 PDF papers on your desk about transformer architectures. You need to write a literature review. So you open each paper, skim it, highlight sentences, tab between them, copy quotes into a Google Doc, and try to stitch together a coherent narrative. It takes you three days. Half the time you are not even thinking â€” you are just searching, scrolling, finding which paper said what.

Now imagine someone hands you a tool. You drop all 15 PDFs into it. You type: "What are the key differences between attention mechanisms discussed across these papers?" And in under ten seconds, the tool reads every paper, finds the relevant paragraphs, cites exactly which paper and which page each fact came from, tells you how confident it is in the answer, and if your papers don't cover something, it goes and searches the internet for you automatically.

That is Mode 1 of DocMind AI.

But you also need to write that literature review. So you type a research topic: "Compare and contrast self-attention, cross-attention, and multi-head attention in modern transformer architectures." And instead of a chat response, the tool goes away quietly and decomposes your topic into sub-questions, researches each one across your documents and the web, checks whether it missed anything, goes back to fill gaps, synthesizes everything into a narrative, and hands you a downloadable Word document with an executive summary, findings, gap analysis, and references. All formatted. All cited.

That is Mode 2 of DocMind AI.

Before this tool existed, the gap was simple: Large Language Models like ChatGPT could answer questions, but they hallucinated â€” they made things up because they had no access to YOUR specific documents. And even if you pasted text into the chat window, it could not search across multiple documents, track which source said what, or tell you how much it was guessing. DocMind AI exists to close that gap. It grounds AI responses in YOUR data, tells you when it is uncertain, and automates the research process that used to take days.

---

# CHAPTER 2: THE PLANNING PHASE

## What Was Built First and Why

The README has a Development Phases table showing Phase 1 (Foundation) as complete and Phases 2-7 as unchecked. But ALL phases are fully implemented in code â€” the README was never updated. The ordering tells us the build sequence:

**Phase 1 (Foundation) first** because nothing works without `config.py`, `db_client.py`, and `main.py`. You cannot authenticate users before you have a database. You cannot store documents before you have a storage layer.

**Phase 2 (Auth) before Phase 3 (Documents)** because every document upload needs a user. The `documents` table has a `user_id` foreign key to `users`. You literally cannot insert a document record without a user existing first.

**Phase 3 (RAG) before Phase 4 (Chat)** because chat responses depend on retrieving chunks from ChromaDB. If you build chat first, there is nothing to retrieve.

**Phase 5 (Research) after Phase 4 (Chat)** because the research agent reuses the same `rag_search` and `web_search` tools from `agent/tools.py`.

**Phase 6 (Eval) last** because evaluation requires a working chat endpoint to test against.

## The Core Feature Everything Depends On

The **RAG pipeline** (`rag/indexer.py` + `rag/retriever.py`). Remove this, and:
- Chat returns empty responses (no document context)
- Research agent has nothing to search
- Suggested questions cannot be generated
- RAGAS evaluation has nothing to evaluate

## What Was Intentionally Left Out

- **No WebSocket/streaming** â€” chat is synchronous HTTP
- **No RBAC** â€” no `role` column on users. Admin is a shared password
- **No unit tests** â€” zero test files. RAGAS is the only quality validation
- **No Docker** â€” no Dockerfile or docker-compose
- **No file formats beyond PDF** â€” only `application/pdf` accepted
- **No real-time collaboration** â€” single-user sessions

## The System Architecture Diagram

```
USER'S BROWSER
  Landing Page | Auth Pages | Dashboard (Chat+Docs) | Research Page
                        |
                Axios API Client (client.ts)
                JWT auto-attach + 401 retry queue
                        |
                    HTTP (REST)
                        |
               FASTAPI BACKEND (main.py)
  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
  â”‚ MIDDLEWARE: CORS + Rate Limiter + Security Hdrs  â”‚
  â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
  â”‚ ROUTERS: auth | documents | chat | research     â”‚
  â”‚          admin | eval | health                   â”‚
  â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
  â”‚ SERVICES: auth_service | doc_service             â”‚
  â”‚           chat_service | research_service        â”‚
  â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
  â”‚ AI LAYER:  rag/indexer + rag/retriever           â”‚
  â”‚            agent/graph + agent/nodes (LangGraph) â”‚
  â”‚            agent/tools + agent/prompts            â”‚
  â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
  â”‚ REPOSITORIES: user | token | document | chat     â”‚
  â”‚               research | eval                    â”‚
  â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜
           â”‚          â”‚          â”‚          â”‚
      PostgreSQL  ChromaDB  Gemini API  Tavily API
      (psycopg2)  (vectors)  (LLM+Embed) (Web Search)

SEPARATE PROCESS:
  Streamlit Eval Dashboard --> Backend API as eval@docmind.ai
  ragas_runner.py --> RAGAS lib --> Gemini (LLM-as-Judge)
```

# CHAPTER 3: THE ARCHITECTURE â€” THE BLUEPRINT

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
Responsibility: Orchestrates operations â€” calls repositories, invokes AI tools, handles error logic, computes confidence scores.
If deleted: Routers would need to contain all business logic directly. Tight coupling, zero reuse.

**Layer 4: AI Operations**
Files: `backend/rag/` (indexer + retriever), `backend/agent/` (graph + nodes + tools + prompts), `backend/report/docx_writer.py`.
Responsibility: PDF extraction, text chunking, embedding, vector search, LLM synthesis, LangGraph agent orchestration, DOCX generation.
If deleted: The entire AI capability vanishes. The app becomes a file storage system with chat that returns nothing useful.

**Layer 5: Data Access (Repository Pattern)**
Files: `backend/repositories/` (6 repository files).
Responsibility: Raw SQL queries encapsulated in functions. Each repository handles one domain entity. Never imported directly by routers â€” only by services.
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

`README.md` â€” Project documentation. Setup instructions. Phase checklist (outdated â€” shows only Phase 1 complete but all are built).

`.env.example` â€” 118-line environment template with inline comments. This is NOT the actual `.env` (which is gitignored). It documents every configurable value in the system. Delete it and new developers have no idea what environment variables exist.

`.gitignore` â€” Excludes `.env`, `__pycache__/`, `node_modules/`, `uploads/`, `reports/`, `.chroma/`. Critical because committing `.env` exposes API keys. Committing `uploads/` would put user PDFs in version control.

`backend/` â€” The entire Python/FastAPI backend. Lives at root level because it is a peer to `frontend/`, not nested inside it. This is a monorepo pattern â€” one repo, multiple deployable units.

`frontend/` â€” The entire React/Vite frontend. Deployed separately (to Vercel) from the backend (to Render).

`eval_dashboard/` â€” Streamlit evaluation tool. Separate from both backend and frontend because it runs as its own process and has its own `requirements.txt`. It communicates with the backend via HTTP, not imports.

`docs/` â€” Two internal documents: `db_optimization_plan.md` (explains the connection pooling rewrite) and `technical_breakdown.txt` (a full technical summary of all features). These are developer documentation, not user-facing.

`DocMind_AI_SRS_v1.md` and `v2.md` â€” Software Requirements Specification documents (124KB and 122KB). Formal requirements documents. At root level because they describe the entire project, not a specific module.

## 3c. TECHNOLOGY CHOICES

**FastAPI** vs Flask vs Django:
FastAPI was chosen because it provides automatic request validation via Pydantic models (every request body is type-checked before your code runs), built-in OpenAPI documentation, native async support, and `Depends()` for dependency injection (used for `get_current_user`). Flask would require manual validation. Django would bring an ORM the project explicitly avoided.
**Verdict:** Right choice. The Pydantic integration alone saves hundreds of lines of validation code.

**psycopg2 (raw SQL)** vs SQLAlchemy vs Prisma:
The project uses hand-written SQL with parameterized queries. This gives full control over query optimization and avoids ORM overhead. The `ThreadedConnectionPool` is tuned for Supabase's 15-connection limit.
**Critique:** For a project this size, SQLAlchemy with its ORM would have been fine and would prevent SQL injection bugs more systematically. The raw SQL approach works but requires discipline â€” every query must use `%s` parameterized queries (which this code does correctly).

**ChromaDB** vs Pinecone vs Weaviate vs pgvector:
ChromaDB was chosen because it works locally with zero setup (`PersistentClient`) and can switch to cloud (`CloudClient`) by changing environment variables. Pinecone requires a cloud account even for development. pgvector would keep everything in PostgreSQL but has worse search performance at scale.
**Verdict:** Right choice for a project that needs local-first development with production cloud deployment.

**LangGraph** vs AutoGen vs CrewAI vs raw Python loops:
LangGraph was chosen because the Deep Research agent needs a conditional loop (reflect â†’ gap-fill â†’ reflect again). A simple LangChain chain cannot loop. AutoGen is designed for multi-agent conversations, not document-grounded research. CrewAI adds unnecessary abstraction.
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
*Real-world analogy:* You own a coffee shop chain. Each location needs a slightly different recipe â€” more sugar downtown, less milk uptown. You don't rewrite the recipe book for each location. You tape a note to the fridge: "SUGAR_AMOUNT=2tsp". Environment variables are those sticky notes. They let the same code behave differently depending on where it runs.
*In this codebase:* The `.env` file contains secrets (API keys, database passwords) and configuration (chunk sizes, rate limits). `config.py` reads them all into a typed Python object so the rest of the code never touches `os.getenv` directly.
*Interview Q:* "Why not hardcode configuration values?"
*Answer:* "Hardcoded values mean I need different code for local vs production. With env vars, the same Docker image (or code) works everywhere â€” I just change the env file. Also, secrets like API keys must never appear in source code because they'd be exposed in version control."

**MISTAKE:** The `Settings` class has `model_config = SettingsConfigDict(env_file=".env")` which looks for `.env` relative to the working directory. If you run the server from a different directory, it won't find the file. A more robust approach would use `Path(__file__).parent / ".env"` for an absolute path.

## PHASE 2: Database Schema & Connection Pooling

**WHAT WAS DONE:**
`db_client.py` contains both the connection pool logic and all DDL (Data Definition Language â€” the SQL that creates tables).

The pool is created on server startup in `main.py`:
```python
async def lifespan(app):
    init_pool()              # Creates ThreadedConnectionPool
    mark_stale_jobs_failed() # Cleanup stuck research jobs
    cleanup_expired_jobs()   # Delete old reports
    yield
    close_pool()             # Returns all connections
```

Tables are created lazily â€” not at startup, but on the first database request. This is because the DDL contains 10+ CREATE TABLE statements, and running them at startup would delay the health check response on Render (causing container restarts).

**CONCEPT: Connection Pooling**
*Real-world analogy:* Imagine a hotel with 10 phone lines. When a guest needs to call, they pick up a line, use it, and hang up. If all 10 are busy, they wait. Without pooling, the hotel would install a new phone line for every call and rip it out when done â€” expensive and slow.
*In this codebase:* `ThreadedConnectionPool(minconn=2, maxconn=10)` keeps 2 connections always open and can scale to 10. `get_db()` borrows a connection, uses it inside a `with` block, and returns it via `putconn()`. It never closes connections.
*Interview Q:* "Why ThreadedConnectionPool and not SimpleConnectionPool?"
*Answer:* "FastAPI runs synchronous endpoints in a thread pool. Multiple threads handle requests concurrently. SimpleConnectionPool is not thread-safe â€” two threads could grab the same connection. ThreadedConnectionPool uses internal locks to prevent this."

**CONCEPT: Lazy Initialization with Double-Checked Locking**
*Real-world analogy:* A restaurant only turns on the kitchen lights when the first customer arrives. But if two customers arrive simultaneously, you don't want both of them trying to flip the switch. One person locks the door, checks if the lights are on, flips them if not, then unlocks.
*In this codebase:* `_ensure_db()` checks `_db_initialized`. If False, it acquires `_db_init_lock`, checks again (double-check), runs DDL, then sets the flag. This prevents two concurrent first-requests from both running CREATE TABLE.

**MISTAKE:** The DDL is embedded as raw SQL strings inside `db_client.py`. A production project would use a migration tool like Alembic to version-control schema changes. Adding a column later requires manually writing `ALTER TABLE` inside the DDL function (which was actually done â€” see the `eval_mode` migration block).

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
*Real-world analogy:* A concert wristband. When you enter, security checks your ticket (login). They give you a wristband stamped with your name and a timestamp. For the next 3 hours, you can walk in and out by showing the wristband â€” no one re-checks your ticket. But after 3 hours, the wristband expires.
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
*Real-world analogy:* Imagine asking a librarian a question. Instead of answering from memory (which might be wrong), they first go to the shelves, pull out relevant books, read the relevant pages, and THEN answer you â€” citing which book and page they found it on. RAG is that librarian.
*In this codebase:* "Retrieval" = search ChromaDB for chunks matching the query. "Augmented" = inject those chunks into the LLM prompt. "Generation" = the LLM writes the answer using those chunks as evidence. The key files are `rag/retriever.py` (retrieval) and `chat_service.py` (augmentation + generation).

**CONCEPT: Text Chunking**
*Real-world analogy:* You cannot photocopy an entire book and hand it to someone asking a question. You find the relevant paragraph and photocopy just that. Chunking is cutting the book into paragraph-sized pieces ahead of time so you can find the right one fast.
*In this codebase:* `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)` cuts text into 1000-character pieces. The 200-character overlap ensures concepts that span two chunks appear in both. The splitter tries to break on paragraph boundaries first, then sentences, then words.
*Interview Q:* "Why 1000 characters and not 500 or 2000?"
*Answer:* "Too small (500) loses context â€” a chunk might contain half a sentence. Too large (2000) dilutes the embedding â€” the vector represents too many topics at once, reducing retrieval precision. 1000 is roughly one paragraph. The overlap of 200 ensures edge concepts are not lost."

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
*Real-world analogy:* A car wash. Your car enters, goes through soap, rinse, wax, dry â€” each station does one job and passes the car to the next. But imagine one station is a quality inspector. If the car is still dirty, it sends it BACK to the soap station. That loop is what makes this a state machine, not a simple pipeline.
*In this codebase:* `AgentState` is the "car" â€” a TypedDict carrying `topic`, `sub_questions`, `research_findings`, `reflection_gaps`, `iteration_count`, etc. Each node reads from state, does work, and returns updated state. The reflector is the quality inspector â€” if it finds gaps, the car goes back for more washing.

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
4. Process the queue â€” all other failed requests get the new token too.
5. On failure, call `onAuthFailure()` which triggers `logout()`.

This prevents a cascade where 5 simultaneous 401s trigger 5 refresh calls.

**CONCEPT: Protected Routes**
*Real-world analogy:* A bouncer at a VIP section. If you have a wristband (access token), you walk in. If not, you are redirected to the entrance (login page). If you are still being checked (loading), you wait.
*In this codebase:* `ProtectedRoute.tsx` checks `accessToken` from `useAuth()`. If loading, shows skeleton. If no token, redirects to `/login`. If token exists, renders children.

# CHAPTER 5: THE COMPLETE DATA FLOW â€” A REQUEST'S JOURNEY

I am tracing the most complex action: a user submitting a Deep Research topic, through every layer, to downloading the DOCX report.

**Step 1: User types a topic in ResearchInput.tsx and clicks Submit**
- Zod validates topic length (1-300 chars) via `researchSchema`
- `researchApi.start(topic)` sends `POST /api/v1/research` with body `{ topic: "..." }`
- Data shape at this point: `{ topic: string }`

**Step 2: Request hits the research router (`research.py:19-34`)**
- `@limiter.limit(AI_LIMIT)` checks: has this IP made 10+ AI requests this minute? If yes, 429.
- `Depends(get_current_user)` extracts and verifies JWT from Authorization header.
- `research_service.start_job(user_id, topic)` is called.
- `background_tasks.add_task(research_service.run_research_agent, job_id, topic, user_id)` schedules the agent.
- Returns `202 Accepted` with `{ job_id, status: "queued" }`.

What could go wrong: Rate limit exceeded (429), expired JWT (401), or an active job already exists for this user (409 â€” `find_active_by_user()` prevents concurrent jobs).

**Step 3: Frontend starts polling (`ResearchPage.tsx:47`)**
- `setInterval(() => pollStatus(jobId), 3000)` â€” every 3 seconds
- `GET /api/v1/research/{job_id}/status` returns current job state
- `ProgressStepper.tsx` renders the current node with a spinning indicator and typewriter text

**Step 4: Background â€” Planner Node (`nodes/planner.py`)**
- Checks cancellation: `if job["status"] == "cancelled": return state`
- Updates DB status to "planning"
- Sends `PLANNER_PROMPT` with the topic to Gemini 2.5 Flash
- LLM returns 5 sub-questions (one per line)
- Updates state: `sub_questions = ["How does...", "What are...", ...]`
- Updates progress in DB: `{ current_step: "Breaking down topic...", steps_done: 1, total_steps: 6 }`

**Step 5: Background â€” Researcher Node (`nodes/researcher.py`)**
- For each of the 5 sub-questions (sequentially):
  - Calls `rag_search(user_id, question)` â€” embeds query, searches ChromaDB
  - Gets back `{ chunks, top_score, collection_empty }`
  - If `should_use_web_search(top_score, collection_empty)` â€” i.e., score < 0.65 or empty â€” calls `web_search(question)`
  - Formats document chunks as `"[filename.pdf p.N] chunk_text..."` and web results as `"[Web: title](url) snippet"`
  - Sends to Gemini with a research prompt, gets synthesized findings
  - Stores findings in `state["research_findings"][question] = "..."`
  - Collects `top_score` into `state["chunk_scores"]`
- Updates progress: `{ current_step: "Researching 'What are...' (3/5)", steps_done: 2 }`

**Step 6: Background â€” Reflector Node (`nodes/reflector.py`)**
- Sends ALL findings + original topic to Gemini with `REFLECTOR_PROMPT`
- Gemini responds with either "NO_GAPS" or a list of gaps
- If gaps: `state["reflection_gaps"] = ["Missing coverage of...", ...]`
- Increments `state["iteration_count"]`

**Step 7: Background â€” Conditional Edge (`graph.py:31-38`)**
```python
def _should_fill_gaps(state: AgentState) -> str:
    gaps = state.get("reflection_gaps", [])
    iteration = state.get("iteration_count", 0)
    max_iter = settings.MAX_REFLECTION_ITERATIONS  # 3
    if gaps and iteration < max_iter:
        return "gap_filler"
    return "synthesizer"
```
If there ARE gaps AND we have NOT looped 3 times â†’ go to gap_filler â†’ loops back to reflector.
If no gaps OR exhausted iterations â†’ go to synthesizer.

**Step 8: Background â€” Gap Filler Node (if triggered)**
- For each gap: generates a targeted question via `GAP_FILLER_PROMPT`
- Runs `rag_search` + `web_search` for that question
- Stores findings under `"[Gap Fill] {question}"` key
- Returns to reflector (which may find more gaps or say NO_GAPS)

**Step 9: Background â€” Synthesizer Node (`nodes/synthesizer.py`)**
- Concatenates ALL findings (including gap-fill findings)
- Sends to Gemini with `SYNTHESIZER_PROMPT`
- Gets a multi-paragraph narrative with executive summary
- Stores in `state["final_synthesis"]`

**Step 10: Background â€” Writer Node (`nodes/writer.py`)**
- Computes confidence score:
  ```python
  avg_score = sum(chunk_scores) / len(chunk_scores) if chunk_scores else 0.0
  if web_used:
      avg_score -= settings.WEB_SEARCH_PENALTY  # 0.10
  # >= 0.70 = "high", >= 0.45 = "medium", else "low"
  ```
- Creates report directory: `backend/reports/{user_id}/`
- Calls `docx_writer.generate_report()` which creates a 7-section Word document:
  1. Title page with colored confidence badge
  2. Executive Summary (first 3 paragraphs)
  3. Research Sub-Questions list
  4. Findings per sub-question
  5. Coverage Gaps Analysis
  6. Full Synthesis
  7. References (extracted via regex from findings)
- Updates job in DB: `status="complete"`, `report_path`, `confidence`, `confidence_score`

**Step 11: Frontend detects completion**
- Next poll returns `status: "complete"` with `report_path` and confidence data
- `ProgressStepper` shows all steps with green checkmarks
- `ReportDownloadCard` appears with a download button

**Step 12: User clicks Download**
- `researchApi.download(jobId)` sends `GET /api/v1/research/{job_id}/download`
- Backend validates ownership, returns `FileResponse` with DOCX media type
- Frontend creates a blob URL and triggers browser download: `docmind_report_{job_id[:8]}.docx`

---

# CHAPTER 6: THE AI STACK â€” EXPLAINED FROM ZERO

## CONCEPT: Embeddings

**THE SIMPLE VERSION:**
Imagine every sentence is a point in a city. Similar sentences live in the same neighborhood. "The cat sat on the mat" lives near "A kitten was resting on a rug" â€” same neighborhood. But "Stock prices rose 5%" lives across town. An embedding is the GPS coordinate of a sentence.

**THE TECHNICAL VERSION:**
An embedding model converts text into a high-dimensional numeric vector (e.g., 768 numbers). Semantically similar texts produce vectors that point in similar directions. This enables mathematical comparison of meaning.

**HOW IT LIVES IN THIS CODE:**
`rag/indexer.py` uses `GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")` to embed chunks during indexing. `agent/tools.py` calls `get_embedding(query)` to embed user queries at search time. ChromaDB stores and indexes these vectors for fast nearest-neighbor search.

**INTERVIEW QUESTIONS:**
1. "What embedding model do you use and why?" â€” "Gemini embedding-001 because it comes from the same provider as our LLM, requiring only one API key. The embeddings are high-quality and the model is optimized for retrieval tasks."
2. "What dimensionality are your embeddings?" â€” "768 dimensions, determined by the Gemini embedding model. We don't control this."
3. "Could you use a different embedding model?" â€” "Yes, but we would need to re-embed all existing documents. Embeddings from different models are not compatible â€” you cannot search Model A's vectors with a Model B query embedding."

## CONCEPT: Vector Database (ChromaDB)

**THE SIMPLE VERSION:**
Imagine a library where books are not organized by genre or author, but by meaning. Books about "cooking Italian food" are physically next to books about "making pasta from scratch." A vector database is that library â€” it stores embeddings and lets you find the nearest neighbors to any query.

**THE TECHNICAL VERSION:**
ChromaDB stores vectors with associated metadata and documents. It uses HNSW (Hierarchical Navigable Small World) indexing for approximate nearest-neighbor search with cosine distance.

**HOW IT LIVES IN THIS CODE:**
`rag/retriever.py` creates per-user collections: `collection_name = f"user_{user_id}"` with `hnsw:space = "cosine"`. Search returns distances, which are converted to similarity scores: `score = max(0.0, 1.0 - distance)`. The project uses `PersistentClient` locally (data saved to `backend/.chroma/`) and `CloudClient` in production.

**INTERVIEW QUESTIONS:**
1. "Why per-user collections instead of one shared collection?" â€” "Data isolation. User A's search never touches User B's vectors. No metadata filtering needed, simpler deletion (drop the collection), and no risk of data leakage."
2. "What is HNSW?" â€” "Hierarchical Navigable Small World â€” a graph-based index that trades perfect recall for speed. It finds approximate nearest neighbors in O(log n) instead of O(n) brute force."

## CONCEPT: LangGraph Agentic Workflow

**THE SIMPLE VERSION:**
Think of it like a flowchart in a doctor's office. Step 1: take vitals. Step 2: see nurse. Step 3: see doctor. Step 4: doctor checks results â€” if something is wrong, go back to Step 2 for more tests. If everything is fine, go to Step 5: prescribe. That "go back" decision is a conditional edge. LangGraph builds these flowcharts for AI.

**THE TECHNICAL VERSION:**
LangGraph is a framework for building stateful, multi-step AI applications as directed graphs. Nodes are functions that transform a shared state dict. Edges define the flow, including conditional edges that route based on state values.

**HOW IT LIVES IN THIS CODE:**
`agent/graph.py` defines a `StateGraph(AgentState)` with 6 nodes. The `AgentState` TypedDict carries: `topic`, `sub_questions`, `research_findings`, `reflection_gaps`, `iteration_count`, `chunk_scores`, `web_used`, `final_synthesis`. The graph is compiled once at module load (`research_graph = graph.compile()`) and reused for every request.

**INTERVIEW QUESTIONS:**
1. "Why not just use a for loop?" â€” "A loop cannot express conditional branching cleanly. LangGraph's conditional edges make the reflectâ†’gap-fill loop a first-class construct, not a nested if-statement buried in a function."
2. "How do you handle cancellation?" â€” "Every node checks `research_repository.find_by_id(job_id)` at entry. If status is 'cancelled', the node returns state unchanged and the graph completes without further processing."
3. "What prevents infinite loops?" â€” "The conditional edge `_should_fill_gaps` checks `iteration_count < MAX_REFLECTION_ITERATIONS (3)`. Even if the reflector always finds gaps, we cap at 3 iterations."

## CONCEPT: Prompt Engineering

**THE SIMPLE VERSION:**
When you ask someone a question, HOW you ask matters. "Tell me about dogs" gets a different answer than "As a veterinarian, explain the top 3 health concerns for golden retrievers over age 8, citing medical studies." Prompt engineering is crafting that question precisely.

**HOW IT LIVES IN THIS CODE:**
`agent/prompts.py` contains 6 named prompt constants. Every prompt uses XML-style tags (`<document_context>`, `<research_topic>`) to structure the input. The `QA_SYSTEM_PROMPT` has 7 explicit rules including "prioritize document context" and "cite filename and page number." The `REFLECTOR_PROMPT` has a specific sentinel response: "If no gaps exist, respond with exactly: NO_GAPS" â€” this makes parsing deterministic.

**CRITIQUE:** The prompts are good but could be better. They don't use few-shot examples (showing the LLM example input/output pairs), which would improve consistency. The reflector's "NO_GAPS" sentinel is brittle â€” if the LLM says "No gaps found" instead, the code would treat it as a gap description.

## CONCEPT: RAGAS Evaluation

**THE SIMPLE VERSION:**
Imagine grading a student's exam, but instead of a human teacher, you hire another AI to grade it. RAGAS is that AI grader. It checks three things: Did the student use their notes correctly? (faithfulness) Did they actually answer the question? (relevancy) Did they read the right pages? (context utilization)

**HOW IT LIVES IN THIS CODE:**
`eval_dashboard/ragas_runner.py` creates `SingleTurnSample` objects with `user_input`, `response`, and `retrieved_contexts`. RAGAS evaluates them using Gemini as the judge LLM. The dashboard runs a "dual-pass" test: Pass 1 with `rag_only=true` (pure RAG), Pass 2 with web search enabled. This isolates whether good answers come from documents or web fallback.

**INTERVIEW QUESTIONS:**
1. "How do you know your RAG system works?" â€” "We built a RAGAS evaluation pipeline that measures faithfulness, answer relevancy, and context utilization. We run dual-pass tests to isolate RAG quality from web-search quality."
2. "What is faithfulness?" â€” "Whether every factual claim in the generated answer can be traced back to the retrieved context. A faithfulness of 0.85 means 85% of claims are grounded."
3. "Why dual-pass?" â€” "A high score on full-pipeline might mask poor RAG quality if the web search is compensating. RAG-only mode shows the true retrieval quality."

# CHAPTER 7: FULL STACK CONCEPTS â€” EXPLAINED FROM ZERO

## CONCEPT: REST APIs and HTTP Methods

**THE SIMPLE VERSION:**
A restaurant menu. GET = "show me the menu." POST = "I'd like to order this." PATCH = "change my order." DELETE = "cancel my order." The waiter (API) takes your request to the kitchen (backend) and brings back a response.

**HOW IT LIVES IN THIS CODE:**
- `GET /api/v1/chat/sessions` â€” list all sessions (reading data)
- `POST /api/v1/chat/sessions` â€” create a new session (creating data)
- `PATCH /api/v1/chat/sessions/{id}` â€” rename a session (partial update)
- `DELETE /api/v1/chat/sessions/{id}` â€” delete a session (removing data)
- `POST /api/v1/research` returns `202 Accepted` (not 200) because the work happens asynchronously â€” the response means "I accepted your request and will work on it," not "here's your result."

**INTERVIEW Q:** "Why 202 instead of 200 for research?"
**Answer:** "200 means the request is complete. 202 means the request was accepted for processing, but the processing isn't done. The client should poll for the result. This accurately represents that research takes minutes, not milliseconds."

## CONCEPT: JWT Authentication

**THE SIMPLE VERSION:**
A movie ticket with your name, seat number, and expiry time printed on it. Anyone can read the ticket (JWTs are base64-encoded, not encrypted), but only the theater can ISSUE a valid one because they have the secret stamp (JWT_SECRET_KEY). If someone modifies the ticket, the stamp won't match and it's rejected.

**HOW IT LIVES IN THIS CODE:**
`jwt_handler.py` creates tokens with `jwt.encode({user_id, email, iat, exp}, SECRET, HS256)`. `dependencies.py` verifies them: `jwt.decode(token, SECRET, [HS256])`. The token lives in the `Authorization: Bearer <token>` header, set by the Axios request interceptor in `client.ts:27-33`.

**WHY NOT ENCRYPTED?** JWTs are signed, not encrypted. The signature proves authenticity (the server issued it) and integrity (nobody tampered with it). Encryption would hide the payload, but the payload contains only `user_id` and `email` â€” not sensitive enough to encrypt.

## CONCEPT: CORS (Cross-Origin Resource Sharing)

**THE SIMPLE VERSION:**
A bank that only accepts phone calls from numbers it recognizes. If a stranger calls, the bank hangs up. CORS tells the browser: "Only accept responses from these specific origins (domains)."

**HOW IT LIVES IN THIS CODE:**
`main.py:62-71` configures `CORSMiddleware` with `allow_origins=settings.cors_origin_list`. Locally this is `["http://localhost:5173"]` (the Vite dev server). In production it would be `["https://your-app.vercel.app"]`. Without CORS, the browser would block ALL API calls from the frontend because it runs on a different port.

## CONCEPT: PostgreSQL Schema Design

**HOW IT LIVES IN THIS CODE:**
10 tables with UUID primary keys (via `pgcrypto`'s `gen_random_uuid()`):
- `users` â€” identity with bcrypt hash, last_login tracking
- `refresh_tokens` â€” SHA-256 hashed tokens with `is_revoked` flag
- `password_reset_tokens` â€” with `used` flag and expiry
- `documents` â€” metadata with FK to users
- `suggested_questions` â€” FK to documents, CASCADE delete
- `chat_sessions` â€” FK to users, with auto-updated timestamps
- `chat_messages` â€” FK to sessions with JSONB for `sources` and `tools_used`
- `research_jobs` â€” status enum, JSONB progress, expiry
- `app_settings` â€” key-value store for admin toggles
- `eval_results` â€” RAGAS scores with `passed` boolean

**INTERVIEW Q:** "Why UUIDs instead of auto-incrementing integers?"
**Answer:** "UUIDs prevent enumeration attacks (an attacker can't guess the next ID by incrementing), work across distributed systems without coordination, and are safe to expose in URLs. The trade-off is slightly larger storage and slower index lookups, but for this scale it's negligible."

## CONCEPT: React Component Architecture

**HOW IT LIVES IN THIS CODE:**
Components follow a clear hierarchy:
- **Pages** (`DashboardPage`, `ResearchPage`, `AdminPage`) â€” compose multiple components, manage page-level state
- **Feature Components** (`ChatWindow`, `SessionSidebar`, `DocumentPanel`) â€” own their domain logic
- **UI Primitives** (`Button`, `Card`, `Input`) â€” shadcn/ui generated, purely presentational

State management uses React's built-in hooks (useState, useEffect, useCallback) â€” no Redux, no Zustand, no React Query. Global state is only `AuthContext` (access token + user). All other state is local to components.

**CRITIQUE:** The project does NOT use React Query (TanStack Query). Every API call manually manages loading/error states with `useState`. React Query would provide automatic caching, background refetching, optimistic updates, and retry logic out of the box. This is the single biggest improvement opportunity on the frontend.

## CONCEPT: Environment-Aware Configuration

**HOW IT LIVES IN THIS CODE:**
A single `ENVIRONMENT` variable switches behavior in 4 places:
1. `db_client.py` â€” `DATABASE_URL` points to local PostgreSQL or Supabase
2. `doc_service.py:16-22` â€” imports `local_storage` or `supabase_storage`
3. `rag/retriever.py:12-21` â€” creates `PersistentClient` or `CloudClient`
4. `auth_service.py:18-39` â€” cookies set with `secure=False/True`, `samesite=lax/none`

This means the exact same code runs locally and in production. No conditional branches scattered throughout â€” the switch happens at the import/initialization level.

---

# CHAPTER 8: WHAT YOU CAN HONESTLY CLAIM YOU BUILT

## LIST A â€” THINGS YOU DEEPLY OWN

1. **Complete RAG pipeline from scratch** â€” "I built PDF extraction with pdfplumber, recursive text chunking with configurable overlap, Gemini embedding, ChromaDB storage with per-user collection isolation, and cosine-similarity retrieval with a configurable threshold that triggers web search fallback."

2. **LangGraph research agent with reflect-loop** â€” "I designed a 6-node state machine where a reflector evaluates coverage gaps and conditionally loops back through a gap-filler up to 3 times before synthesis."

3. **JWT auth with refresh token rotation** â€” "I implemented short-lived access tokens, SHA-256-hashed refresh tokens stored in PostgreSQL, rotation on every refresh, and revocation of all tokens on password reset."

4. **Axios 401 interceptor with request queuing** â€” "I built an interceptor that queues concurrent failed requests, fires a single refresh call, and replays all queued requests with the new token."

5. **Confidence scoring from retrieval metrics** â€” "Confidence is computed from actual cosine similarity scores, not arbitrary labels. Different thresholds for chat (single-query) vs research (multi-query average with web penalty)."

6. **Dual-pass RAGAS evaluation** â€” "I built a Streamlit dashboard that tests the pipeline twice â€” once with web search disabled, once enabled â€” to isolate RAG quality from web-search quality."

7. **Database connection pooling with lazy DDL** â€” "I implemented ThreadedConnectionPool with double-checked locking for lazy schema initialization, solving Render's health-check timeout."

8. **7-section DOCX report generator** â€” "I used python-docx to generate structured reports with styled title pages, color-coded confidence badges, extracted references, and proper formatting."

9. **Environment-aware dual-deployment** â€” "A single codebase works locally and in production by switching storage, database, ChromaDB, and cookie configuration via one environment variable."

10. **Admin AI kill-switch** â€” "A database-driven toggle that disables all LLM calls globally, returning 503 errors, controllable via a password-protected admin endpoint."

## LIST B â€” THINGS THAT ARE SURFACE LEVEL

1. **shadcn/ui components** â€” The 13 files in `components/ui/` are CLI-generated. Study: How shadcn/ui works internally, how to customize theme tokens, how to create your own shadcn-style component.

2. **LangChain wrappers** â€” `ChatGoogleGenerativeAI` and `GoogleGenerativeAIEmbeddings` are black boxes. Study: The Gemini API directly, how LangChain wraps it, what parameters are available (temperature, top_k, max_tokens).

3. **RAGAS internals** â€” You call `evaluate()` but don't implement the metrics. Study: How faithfulness scoring works internally (statement extraction â†’ entailment checking), how answer relevancy uses reverse-question generation.

4. **Tailwind CSS** â€” Used via utility classes but no custom Tailwind plugins or theme extensions. Study: How `@apply` works, custom plugins, responsive design patterns.

5. **No automated tests** â€” This is a significant gap. Study: pytest for backend, Vitest + React Testing Library for frontend, how to mock database connections and external APIs.

6. **No streaming responses** â€” Chat is synchronous. Study: Server-Sent Events (SSE) with FastAPI's `StreamingResponse`, how to stream LLM tokens to the frontend.

---

# CHAPTER 9: THE INTERVIEW SIMULATION

**Q1: "Explain this project in 2 minutes."**
TESTING: Can you communicate clearly under pressure?
ANSWER: "DocMind AI is a full-stack research assistant with two modes. Mode 1: upload PDFs, ask questions, get RAG-powered answers with citations and confidence scores. If documents don't cover the query, it falls back to web search via Tavily. Mode 2: submit a research topic, and a LangGraph agent decomposes it into sub-questions, researches each one, reflects on coverage gaps, fills them iteratively, and generates a downloadable DOCX report. The backend is FastAPI with PostgreSQL and ChromaDB, the frontend is React with TypeScript, and we have a RAGAS evaluation dashboard that measures pipeline quality."
FOLLOW-UP: "What is your most technically interesting feature?"
ANSWER: "The reflect-loop in the research agent. After gathering findings, a reflector node evaluates whether the research is comprehensive. If it finds gaps, a gap-filler node researches them and the reflector checks again â€” up to 3 iterations. This produces significantly better research coverage than a single-pass approach."

**Q2: "How does RAG work in your system?"**
TESTING: Do you understand your core AI pipeline?
ANSWER: "PDFs are extracted with pdfplumber, chunked into 1000-character overlapping segments, embedded with Gemini's embedding model, and stored in per-user ChromaDB collections. At query time, the query is embedded, ChromaDB finds the 5 nearest chunks by cosine similarity, and those chunks are injected into the LLM prompt alongside conversation history. The LLM generates an answer grounded in those chunks."
FOLLOW-UP: "Why 1000 characters?"
ANSWER: "Trade-off between context and precision. Too small and chunks lack context. Too large and the embedding represents too many topics, reducing retrieval accuracy. 1000 characters is roughly a paragraph â€” enough for a coherent thought."

**Q3: "How do you handle authentication?"**
TESTING: Security understanding.
ANSWER: "Short-lived JWT access tokens (15 min, HS256) for API authentication, long-lived refresh tokens (7 days) stored as SHA-256 hashes in PostgreSQL and delivered as httpOnly cookies. On every refresh, the old token is revoked and a new one issued â€” token rotation. On password reset, all refresh tokens for the user are revoked."
FOLLOW-UP: "Why hash refresh tokens?"
ANSWER: "If the database is breached, attackers get hashes, not usable tokens. They cannot reverse SHA-256 to get the raw token needed to call the refresh endpoint."

**Q4: "What happens if the Gemini API goes down?"**
TESTING: Error handling and resilience.
ANSWER: "The admin kill-switch. An admin can toggle the `ai_enabled` flag in the app_settings table via a password-protected endpoint. When disabled, all AI endpoints (chat, research, suggested questions) return 503 Service Unavailable. Additionally, every LLM call is wrapped in try/except â€” failures are logged and returned as user-friendly error messages, not 500 crashes."

**Q5: "How do you know your RAG quality is good?"**
TESTING: Quality assurance mindset.
ANSWER: "We built a RAGAS evaluation dashboard. It runs dual-pass tests â€” RAG-only (web search disabled) and full pipeline â€” measuring faithfulness, answer relevancy, and context utilization using Gemini as an LLM judge. Scores above 0.70 pass. Historical results are tracked in PostgreSQL and visualized in Plotly charts to detect regressions."

**Q6: "Why LangGraph instead of a simple chain?"**
TESTING: Architecture decision-making.
ANSWER: "The research agent needs a conditional loop â€” the reflector might find coverage gaps that need additional research. A LangChain chain is linear. LangGraph's conditional edges let me route from reflector to gap-filler and back to reflector, up to 3 iterations."

**Q7: "How do you prevent SQL injection?"**
TESTING: Security fundamentals.
ANSWER: "Every SQL query uses psycopg2 parameterized queries with %s placeholders. User input never touches the SQL string directly. For example: `cur.execute('SELECT * FROM users WHERE email = %s', (email,))`. The driver handles escaping."

**Q8: "Walk me through what happens when a chat message is sent."**
TESTING: End-to-end understanding.
ANSWER: "User types in ChatWindow.tsx, optimistic UI adds the message immediately, POST to /chat/{session_id}/messages. Backend: check AI enabled, verify session ownership, save user message, load last 10 messages for context, embed query, search ChromaDB for top 5 chunks, check if top cosine score < 0.65 (trigger web search if so), inject document + web context into prompt, call Gemini, compute confidence from cosine score, save assistant message with sources/tools/confidence as JSONB, auto-title session if first message, return response. Frontend renders MessageBubble with ConfidenceBar, ToolBadge, and CitationBlock."

**Q9: "What would you change if starting over?"**
TESTING: Self-awareness and growth.
ANSWER: "Three things. First, use React Query instead of manual useState for API calls â€” it provides caching, background refetching, and retry logic for free. Second, add streaming responses via Server-Sent Events so users see tokens appear in real-time instead of waiting for the full response. Third, use Alembic for database migrations instead of DDL in code."

**Q10: "How do you handle concurrent users?"**
TESTING: Scalability understanding.
ANSWER: "ThreadedConnectionPool with max=10 connections handles concurrent database access. Per-user ChromaDB collections ensure search isolation. Rate limiting via slowapi prevents any single IP from overwhelming the server. FastAPI runs sync endpoints in a thread pool. The main bottleneck is LLM API calls â€” these are sequential per user but concurrent across users."

**Q11: "What is the most complex bug you fixed?"**
TESTING: Debugging experience.
ANSWER: "Circular recursion in database initialization. `get_db()` called `_ensure_db()` which called `init_db()` which called `get_db()` â€” infinite loop. Fixed by creating `_init_db_raw()` that grabs a connection directly from the pool, bypassing `get_db()` entirely. Documented in `docs/db_optimization_plan.md`."

**Q12: "How do you handle file uploads securely?"**
TESTING: Security in practice.
ANSWER: "Four validations: MIME type must be application/pdf, file size must be under 10MB, user must not exceed 5 documents. Files are saved with a UUID prefix to prevent filename collisions and directory traversal. If indexing fails after file save, there is explicit rollback that deletes the file from storage and vectors from ChromaDB."

**Q13: "Explain your confidence scoring."**
TESTING: Feature depth.
ANSWER: "Confidence is derived from cosine similarity of retrieved chunks, not from the LLM's self-assessment. In chat mode: top_score >= 0.75 is high, >= 0.65 is medium, below is low. If web search was used and no document matches (score 0.0), it is forced to low. In research mode: average of all chunk scores across sub-questions minus a 0.10 penalty if web search was used anywhere."

**Q14: "Why PostgreSQL instead of MongoDB?"**
TESTING: Database choice reasoning.
ANSWER: "The data is relational â€” sessions have messages, users have documents, documents have suggested questions. Foreign keys enforce referential integrity. JSONB columns (sources, progress) provide document-store flexibility where needed. MongoDB would lose the referential integrity guarantees."

**Q15: "How does the frontend handle token refresh?"**
TESTING: Frontend complexity.
ANSWER: "An Axios response interceptor catches 401s. It checks if a refresh is already in progress â€” if so, it queues the failed request. If not, it calls /auth/refresh, gets a new access token, replays the original request, and processes the queue so all concurrent failures are retried with the new token. This prevents cascading refresh calls."

**Q16: "What rate limiting strategy do you use?"**
TESTING: API protection.
ANSWER: "IP-based rate limiting via slowapi. Two tiers: 30 requests/minute for general endpoints, 10 requests/minute for AI endpoints (chat messages and research submissions). AI endpoints are more expensive because they invoke LLM calls that cost money and time."

**Q17: "How do you handle stale research jobs?"**
TESTING: Resilience.
ANSWER: "On server startup, `mark_stale_jobs_failed()` finds any jobs in active states that have not been updated in 20 minutes and marks them as failed with the message 'Job was interrupted by a server restart.' Also, `cleanup_expired_jobs()` deletes jobs older than 7 days and removes their DOCX report files from disk."

**Q18: "What is your deployment architecture?"**
TESTING: DevOps awareness.
ANSWER: "Frontend on Vercel (static site hosting), backend on Render (Python web service), database on Supabase PostgreSQL, vectors on ChromaDB Cloud, eval dashboard on Render (Streamlit). UptimeRobot pings the health endpoint every 5 minutes to prevent Render's free-tier container from sleeping."

**Q19: "What is missing from this project?"**
TESTING: Honesty and self-assessment.
ANSWER: "Automated tests (zero test files), response streaming (synchronous HTTP only), role-based access control (admin is just a shared password), and database migrations (DDL is embedded in code). Also, the research agent processes sub-questions sequentially when they could be parallelized."

**Q20: "If this application had 10,000 users, what breaks first?"**
TESTING: Scale thinking.
ANSWER: "The database connection pool. Max 10 connections with Supabase's 15 limit. I would need to switch to connection pooling via PgBouncer or Supabase's built-in pooler. Second, ChromaDB â€” 10,000 per-user collections would strain the vector database. I would evaluate switching to a shared collection with metadata filtering, or a managed service like Pinecone. Third, the Gemini API rate limits â€” I would need to implement request queuing with exponential backoff."
