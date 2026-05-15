# DocMind AI â€” Complete Technical Deep Dive (Interview Prep)

> **Every claim in this document is backed by actual code I read. Nothing is guessed.**

---

## 1. PROJECT OVERVIEW â€” IN ONE PARAGRAPH

DocMind AI is a full-stack AI-powered research assistant that solves one core problem: "I have documents and questions â€” help me find answers and generate reports." A user signs up, uploads PDF documents (up to 5, max 10MB each), and the system extracts text page-by-page using `pdfplumber`, splits it into overlapping 1000-character chunks via LangChain's `RecursiveCharacterTextSplitter`, embeds those chunks using Google's `gemini-embedding-001` model, and stores the vectors in ChromaDB with per-user collection isolation. The user can then ask questions in a conversational chat interface (Mode 1), where the system performs cosine similarity search against their vectors, optionally falls back to Tavily web search if the similarity score drops below 0.65, feeds both contexts to Gemini 2.5 Flash, and returns an answer with citations, confidence scores, and source attribution. Alternatively, the user can submit a research topic (Mode 2), which triggers a LangGraph-based multi-step agent that decomposes the topic into sub-questions, researches each one, reflects on coverage gaps, loops back to fill them (up to 3 iterations), synthesizes everything into a narrative, and writes a downloadable 7-section DOCX report. The entire system is wrapped in JWT authentication with refresh token rotation, bcrypt password hashing, rate limiting, an admin kill-switch for AI services, and a RAGAS evaluation dashboard that measures faithfulness, answer relevancy, and context precision.

---

## 2. TECH STACK â€” WITH REASONS

### Backend Core

| Technology | What it does HERE | Why chosen | Where used |
|---|---|---|---|
| **FastAPI** | REST API framework, handles all HTTP endpoints, request validation via Pydantic models, background tasks for research jobs | Async support, automatic OpenAPI docs, native Pydantic integration for request/response validation | `backend/main.py`, all files in `backend/api/v1/routers/` |
| **Python 3.11+** | Runtime language | Type hints (`str \| None`), match-case, required by LangChain/LangGraph ecosystem | Entire backend |
| **Pydantic + pydantic-settings** | Request/response validation, environment config management | `BaseSettings` auto-loads `.env` files, field validators enforce password complexity rules | `backend/config.py`, `backend/api/v1/models/` |
| **PostgreSQL** | Primary relational database â€” stores users, documents metadata, chat sessions/messages, research jobs, eval results, app settings | ACID compliance, JSONB for flexible `sources`/`tools_used`/`progress` fields, UUID primary keys via `pgcrypto` | `backend/database/db_client.py` (DDL), all `backend/repositories/` |
| **psycopg2** | PostgreSQL driver with `ThreadedConnectionPool` (min=2, max=10 connections), `RealDictCursor` for dict-based row access | Direct SQL control vs ORM overhead, connection pooling for concurrent requests | `backend/database/db_client.py` |
| **ChromaDB** | Vector database for document embeddings, per-user collections with cosine distance space | Lightweight, works locally with `PersistentClient` and in production with `CloudClient`, simple Python API | `backend/rag/retriever.py`, `backend/rag/indexer.py` |
| **Google Gemini 2.5 Flash** | LLM for all AI tasks â€” Q&A synthesis, question generation, research planning/reflection/synthesis | Cost-effective, fast inference, accessed via `langchain-google-genai` wrapper | `backend/services/chat_service.py`, all `backend/agent/nodes/`, `backend/services/doc_service.py` |
| **Gemini Embedding 001** | Embedding model for vectorizing document chunks and queries | Same provider as LLM (single API key), high-quality embeddings | `backend/rag/indexer.py` (`models/gemini-embedding-001`) |
| **LangGraph** | State machine framework for the Deep Research agent â€” defines a graph of nodes with conditional edges | Enables the reflectâ†’gap-fill loop that a simple chain can't do; typed state passed between nodes | `backend/agent/graph.py` |
| **LangChain** | Text splitting (`RecursiveCharacterTextSplitter`), LLM wrappers (`ChatGoogleGenerativeAI`), embedding wrappers | Provides the chunking utilities and unified LLM interface that LangGraph nodes consume | `backend/rag/indexer.py`, all agent nodes |
| **Tavily** | Web search API â€” fallback when RAG cosine score < 0.65 or collection is empty | Purpose-built for AI search, returns structured results with titles/URLs/snippets | `backend/agent/tools.py` |
| **PyJWT** | JWT access token creation and verification (HS256) | Lightweight, no external auth service needed | `backend/auth/jwt_handler.py` |
| **bcrypt** | Password hashing with configurable work factor (default 12 rounds) | Industry-standard adaptive hashing, constant-time comparison prevents timing attacks | `backend/auth/password_handler.py` |
| **slowapi** | IP-based rate limiting â€” 30 req/min general, 10 req/min for AI endpoints | Prevents abuse of expensive LLM calls | `backend/middleware/rate_limiter.py`, applied in `chat.py` and `research.py` routers |
| **python-docx** | DOCX report generation with styled sections, color-coded confidence, references | Generates downloadable Word documents without external services | `backend/report/docx_writer.py` |
| **pdfplumber** | PDF text extraction, page-by-page | Better table/layout handling than PyPDF2, returns text per page with page numbers | `backend/rag/indexer.py` |
| **Resend / SMTP** | Password reset email delivery | Dual-provider support â€” Resend API for production, SMTP fallback, local logging for dev | `backend/mailer/email_sender.py` |
| **Supabase** | Production storage â€” Supabase PostgreSQL for DB, Supabase Storage for PDF files | Managed PostgreSQL with generous free tier, built-in file storage with signed URLs | `backend/storage/supabase_storage.py`, `backend/config.py` |

### Frontend

| Technology | What it does HERE | Where used |
|---|---|---|
| **React 19 + TypeScript** | SPA framework, all UI components | Entire `frontend/src/` |
| **Vite** | Dev server and bundler | `frontend/vite.config.ts` |
| **Tailwind CSS v4** | Utility-first styling | `frontend/src/index.css`, all `.tsx` files |
| **shadcn/ui** | Pre-built accessible UI components (Button, Card, Input, AlertDialog, ScrollArea, etc.) | `frontend/src/components/ui/` (13 components) |
| **Axios** | HTTP client with request/response interceptors for JWT auto-attach and 401 auto-refresh | `frontend/src/api/client.ts` |
| **React Router v7** | Client-side routing with protected routes | `frontend/src/App.tsx` |
| **React Hook Form + Zod** | Form state management + schema validation | `frontend/src/lib/validators/`, auth pages |
| **Sonner** | Toast notifications | Throughout all pages |
| **Lucide React** | Icon library | Throughout all components |

### Eval Dashboard

| Technology | What it does HERE | Where used |
|---|---|---|
| **Streamlit** | Interactive evaluation dashboard UI | `eval_dashboard/dashboard.py` |
| **RAGAS** | Computes Faithfulness, ResponseRelevancy, ContextUtilization metrics | `eval_dashboard/ragas_runner.py` |
| **Plotly** | Bar charts for historical eval scores | `eval_dashboard/dashboard.py` |
| **Pandas** | DataFrame manipulation for eval results | `eval_dashboard/dashboard.py` |

---

## 3. COMPLETE DATA FLOW â€” STEP BY STEP

### Flow A: Document Upload (Mode 1 prerequisite)

```
Step 1: User drags PDF onto UploadDropzone.tsx
  â†’ Client-side validation: PDF only, max 10MB
  â†’ FormData POST to /api/v1/documents/upload

Step 2: documents router (documents.py) â†’ doc_service.upload_document()
  â†’ MIME check (application/pdf only)
  â†’ Size check (MAX_PDF_SIZE_MB * 1024 * 1024)
  â†’ Count check: document_repository.count_by_user() vs MAX_DOCUMENTS_PER_USER (5)

Step 3: Storage layer (local_storage.py or supabase_storage.py based on ENVIRONMENT)
  â†’ Saves file with UUID prefix: "{uuid8}_{filename}"
  â†’ Returns storage_path: "{user_id}/{safe_name}"

Step 4: RAG Indexing Pipeline (indexer.py)
  â†’ pdfplumber extracts text per page â†’ [{ page: 1, text: "..." }, ...]
  â†’ RecursiveCharacterTextSplitter chunks at 1000 chars, 200 overlap
  â†’ GoogleGenerativeAIEmbeddings embeds all chunk texts in batch
  â†’ ChromaDB collection "user_{user_id}" gets vectors with metadata:
    { document_id, filename, page_number, chunk_index, user_id }

Step 5: PostgreSQL INSERT into documents table
  â†’ Stores: id, user_id, filename, storage_path, chunk_count, file_size_kb

Step 6: LLM generates 5 suggested questions from first 3 chunks
  â†’ Stored in suggested_questions table
  â†’ Returned to frontend alongside document metadata
```

### Flow B: Chat Q&A (Mode 1)

```
Step 1: User types question in ChatWindow.tsx
  â†’ Optimistic user message bubble appears immediately
  â†’ POST /api/v1/chat/{session_id}/messages { query: "..." }

Step 2: chat router (chat.py) â†’ chat_service.send_message()
  â†’ _check_ai_enabled() â€” reads app_settings table, 503 if disabled
  â†’ Validates ownership: session must belong to user
  â†’ Saves user message to chat_messages table

Step 3: Build conversation context
  â†’ chat_repository.get_recent_messages(session_id, CHAT_CONTEXT_WINDOW=10)
  â†’ Format: "USER: ...\nASSISTANT: ..." string

Step 4: RAG Search (agent/tools.py â†’ rag/retriever.py)
  â†’ Embed query via gemini-embedding-001
  â†’ ChromaDB collection.query(query_embeddings, n_results=RAG_TOP_K=5)
  â†’ Convert distances to cosine scores: score = 1 - distance
  â†’ Returns { chunks, top_score, collection_empty }

Step 5: Conditional Web Search
  â†’ should_use_web_search(): triggers if collection_empty OR top_score < 0.65
  â†’ Tavily search returns [{ url, title, snippet }]

Step 6: LLM Synthesis
  â†’ QA_SYSTEM_PROMPT + QA_USER_PROMPT with {document_context, web_context, conversation_history, query}
  â†’ Gemini 2.5 Flash generates answer

Step 7: Confidence Computation
  â†’ top_score >= 0.75 â†’ "high"
  â†’ top_score >= 0.65 â†’ "medium"  
  â†’ else â†’ "low"
  â†’ If web_search used and top_score == 0.0 â†’ forced "low"

Step 8: Save & Return
  â†’ Save assistant message with sources (JSONB), tools_used (JSONB), confidence
  â†’ Auto-title session to first 50 chars of query if title is "New Chat"
  â†’ Return MessageResponse to frontend

Step 9: Frontend renders MessageBubble.tsx
  â†’ Shows ConfidenceBar (5 dots, colored by level)
  â†’ Shows ToolBadge ("Documents", "Web")
  â†’ Shows CitationBlock (document sources with page numbers + cosine scores, web sources with links)
```

### Flow C: Deep Research (Mode 2)

```
Step 1: User enters topic in ResearchInput.tsx
  â†’ POST /api/v1/research { topic: "..." }
  â†’ Returns 202 Accepted with job_id

Step 2: BackgroundTasks.add_task(research_service.run_research_agent)
  â†’ Frontend starts polling GET /research/{job_id}/status every 3 seconds
  â†’ ProgressStepper.tsx shows typewriter "Thinking: ..." updates

Step 3: LangGraph State Machine (graph.py)
  Entry â†’ planner â†’ researcher â†’ reflector â†’ [gap_filler â†’ reflector]* â†’ synthesizer â†’ writer â†’ END

  PLANNER NODE:
  â†’ LLM decomposes topic into MAX_SUB_QUESTIONS (5) sub-questions
  â†’ Updates job status to "planning"

  RESEARCHER NODE:
  â†’ For each sub-question: RAG search + conditional web search
  â†’ Collects all cosine scores for later confidence computation
  â†’ Updates progress: "Researching '{question}' (2/5)..."

  REFLECTOR NODE:
  â†’ LLM reviews all findings against original topic
  â†’ Returns "NO_GAPS" or list of gaps
  â†’ Increments iteration_count

  CONDITIONAL EDGE (_should_fill_gaps):
  â†’ If gaps > 0 AND iteration_count < MAX_REFLECTION_ITERATIONS (3) â†’ gap_filler
  â†’ Else â†’ synthesizer

  GAP_FILLER NODE:
  â†’ For each gap: LLM generates targeted question â†’ RAG + web search
  â†’ Findings stored under "[Gap Fill] {question}" key

  SYNTHESIZER NODE:
  â†’ LLM combines all findings into executive summary + detailed narrative

  WRITER NODE:
  â†’ Computes confidence: avg(chunk_scores) - WEB_SEARCH_PENALTY (0.10 if web used)
  â†’ generate_report() creates 7-section DOCX via python-docx
  â†’ Saves to backend/reports/{user_id}/docmind_report_{job_id[:8]}.docx
  â†’ Updates job as "complete" with confidence score

Step 4: Frontend detects status="complete", shows ReportDownloadCard
  â†’ GET /research/{job_id}/download returns FileResponse (DOCX)
```
# DocMind AI â€” Deep Dive Part 2: Decisions, Concepts & Interview Prep

---

## 4. EVERY MAJOR DECISION â€” EXPLAINED AS A STORY

### Decision 1: "LangGraph instead of a simple LangChain chain for Deep Research"

**What:** The research agent uses `langgraph.graph.StateGraph` with 6 nodes and a conditional edge, rather than a linear `chain.invoke()`.

**Problem it solves:** Research needs a _loop_. After gathering findings, the reflector might discover gaps. Those gaps need to be researched, then reflected on again. A linear chain can't loop. LangGraph's conditional edges let the graph go `reflector â†’ gap_filler â†’ reflector` up to 3 times.

**What would break otherwise:** Without the reflect-loop, the agent would do one pass of research and miss coverage gaps. The report quality would be shallow. The conditional edge `_should_fill_gaps()` in `backend/agent/graph.py:31-38` checks `len(gaps) > 0 AND iteration < MAX_REFLECTION_ITERATIONS` to decide whether to loop or proceed to synthesis.

**Where:** `backend/agent/graph.py` â€” the entire graph definition. State is defined as `AgentState(TypedDict)` with fields like `reflection_gaps`, `iteration_count`, `chunk_scores`.

---

### Decision 2: "Raw SQL with psycopg2 instead of an ORM like SQLAlchemy"

**What:** Every database operation uses hand-written SQL with parameterized queries via psycopg2's `cursor.execute()`.

**Problem it solves:** Full control over queries, no ORM overhead, explicit connection pool management. The `ThreadedConnectionPool(minconn=2, maxconn=10)` is tuned for Supabase's free tier (15 connections max, leaving headroom for admin tools).

**What would break:** An ORM would add complexity for what is essentially CRUD + a few joins. The DDL in `db_client.py` creates all tables with proper indexes and constraints on first request (lazy initialization with double-checked locking to prevent TOCTOU race conditions â€” `_db_init_lock` at line 15).

**Where:** `backend/database/db_client.py` (pool + DDL), all files in `backend/repositories/`.

---

### Decision 3: "Refresh token rotation stored as SHA-256 hashes in PostgreSQL"

**What:** Refresh tokens are raw UUIDs sent as `httpOnly` cookies. The database stores only the SHA-256 hash of each token, never the raw value.

**Problem it solves:** If the database is compromised, attackers can't use the stolen hashes to forge refresh tokens. On each refresh, the old token is revoked and a new one is issued (rotation), limiting the window of a stolen token. On password reset, ALL refresh tokens for the user are revoked.

**Where:** `backend/repositories/token_repository.py:7-9` (`_hash_token` uses `hashlib.sha256`), `backend/services/auth_service.py:126-132` (rotation logic).

---

### Decision 4: "Per-user ChromaDB collections instead of a single shared collection"

**What:** Each user's documents are stored in a separate ChromaDB collection named `user_{user_id}` (with hyphens replaced by underscores).

**Problem it solves:** Complete data isolation between users. When user A searches, they only hit their own vectors. No need for metadata filtering on every query. Deletion of a user's data is a simple collection drop.

**What would break:** A shared collection would require adding `where={"user_id": user_id}` to every query, which is slower and error-prone. A bug in the filter could leak data between users.

**Where:** `backend/rag/retriever.py:7-9` (`get_collection_name`), used everywhere vectors are accessed.

---

### Decision 5: "Cosine similarity threshold (0.65) triggers web search fallback"

**What:** After RAG retrieves chunks, the top cosine score is checked. If it's below `WEB_SEARCH_FALLBACK_THRESHOLD` (0.65) or the collection is empty, Tavily web search runs automatically.

**Problem it solves:** If the user asks a question their documents don't cover, the system doesn't return garbage â€” it supplements with web results. The threshold is configurable via `.env`.

**Where:** `backend/rag/retriever.py:31-37` (`should_use_web_search`), called from both `chat_service.py:125` (Mode 1) and `researcher.py:58` (Mode 2).

---

### Decision 6: "Background tasks + polling instead of WebSockets for research"

**What:** Research jobs are launched via FastAPI's `BackgroundTasks`, and the frontend polls `GET /research/{job_id}/status` every 3 seconds.

**Problem it solves:** Simplicity. WebSockets would require a persistent connection, special deployment config (sticky sessions on Render), and more complex error handling. Polling is stateless, works behind any reverse proxy, and the 3-second interval is configurable via `VITE_RESEARCH_POLL_INTERVAL_MS`.

**Where:** `backend/api/v1/routers/research.py:28-33` (background task), `frontend/src/components/research/ResearchPage.tsx:14,47` (polling).

---

### Decision 7: "Dual-environment architecture â€” local vs. production"

**What:** A single `ENVIRONMENT` flag switches between: local PostgreSQL / Supabase, local filesystem / Supabase Storage, local ChromaDB / ChromaDB Cloud.

**Where:** `backend/config.py:103-104` (`is_production` property), `backend/services/doc_service.py:16-22` (storage module swap), `backend/rag/retriever.py:12-21` (ChromaDB client swap).

---

### Decision 8: "Admin kill-switch for AI services via app_settings table"

**What:** A database row `app_settings.ai_enabled = 'true'/'false'` can disable all AI endpoints (chat, research, suggested questions) without restarting the server.

**Problem it solves:** If the Gemini API is having issues or you're over quota, an admin can disable AI to prevent cascading errors. The toggle is protected by `ADMIN_PASSWORD` header.

**Where:** `backend/admin/controls.py`, `backend/services/chat_service.py:21-32` (`_check_ai_enabled`), `backend/api/v1/routers/admin.py`.

---

### Decision 9: "Lazy DDL initialization with double-checked locking"

**What:** Database tables are NOT created at application startup. Instead, the first request triggers `_ensure_db()` which runs all DDL inside a `threading.Lock`. A `_db_initialized` flag prevents re-running.

**Problem it solves:** Avoids a circular dependency (`get_db()` â†’ `_ensure_db()` â†’ `get_db()`) by using `_init_db_raw()` which grabs a connection directly from the pool. The double-checked lock prevents multiple threads from running DDL simultaneously on the first concurrent requests.

**Where:** `backend/database/db_client.py:50-70`.

---

### Decision 10: "Axios interceptor queue for concurrent 401 retry"

**What:** When a 401 occurs, the interceptor refreshes the token and retries. If multiple requests fail simultaneously, they're queued â€” only one refresh call is made, and all queued requests are replayed with the new token.

**Where:** `frontend/src/api/client.ts:36-101` â€” `isRefreshing` flag, `failedQueue` array, `processQueue()` function.

---

## 5. CONCEPTS YOU NEED TO UNDERSTAND

### RAG (Retrieval-Augmented Generation)

**What it is:** Instead of asking an LLM to answer from its training data alone, you first _retrieve_ relevant chunks from your own documents, then _augment_ the LLM's prompt with those chunks, so it _generates_ grounded answers.

**How it works in THIS codebase:** User uploads PDF â†’ pdfplumber extracts text â†’ RecursiveCharacterTextSplitter chunks it (1000 chars, 200 overlap) â†’ Gemini embeds each chunk â†’ stored in ChromaDB. At query time: embed the query â†’ cosine similarity search in ChromaDB â†’ top 5 chunks become `document_context` in the prompt â†’ Gemini generates answer grounded in those chunks.

**Files:** `backend/rag/indexer.py` (indexing pipeline), `backend/rag/retriever.py` (search), `backend/agent/tools.py` (rag_search wrapper), `backend/services/chat_service.py:99-118` (context building).

**Most likely interview question:** "How do you prevent hallucination in your system?"

**Ideal answer:** "Three ways. First, RAG grounds the LLM in actual document content â€” the prompt includes the retrieved chunks and instructs the model to cite sources. Second, the confidence score is based on the actual cosine similarity of the retrieved chunks â€” if the top score is below 0.65, we flag it as low confidence AND trigger web search for supplementary data. Third, the RAGAS evaluation framework measures faithfulness â€” whether the answer is actually supported by the retrieved context â€” and we track this over time."

---

### Vector Embeddings & Cosine Similarity

**What it is:** Text is converted into high-dimensional numeric vectors (embeddings) where semantically similar texts are close together. Cosine similarity measures the angle between two vectors â€” 1.0 means identical direction, 0.0 means orthogonal.

**How it works HERE:** `gemini-embedding-001` converts text to vectors. ChromaDB stores them with `hnsw:space = "cosine"`. At query time, ChromaDB returns `distances` (where distance = 1 - cosine_similarity), and the code converts: `cosine_score = max(0.0, 1.0 - dist)` in `retriever.py:69`.

**Most likely interview question:** "Why 1000-character chunks with 200 overlap?"

**Ideal answer:** "The chunk size is a trade-off. Too small and you lose context; too large and the embedding becomes diluted across multiple topics. 1000 characters is roughly a paragraph â€” enough for a coherent thought. The 200-character overlap ensures that if a concept spans two chunks, at least part of it appears in both, so neither chunk misses it completely. These values are configurable via `CHUNK_SIZE` and `CHUNK_OVERLAP` in the environment."

---

### JWT Authentication with Refresh Token Rotation

**What it is:** JWTs are short-lived tokens (15 min) containing user_id and email. Refresh tokens are long-lived (7 days), stored as httpOnly cookies, used to get new access tokens without re-login.

**How it works HERE:** Login â†’ create JWT access token (HS256, 15 min) + UUID refresh token â†’ hash refresh token with SHA-256 â†’ store hash in `refresh_tokens` table â†’ set raw token as httpOnly cookie. On 401 â†’ frontend interceptor calls `/auth/refresh` â†’ server validates cookie against hashed DB record â†’ revokes old token, creates new one (rotation) â†’ returns new access token.

**Files:** `backend/auth/jwt_handler.py`, `backend/services/auth_service.py:104-135`, `frontend/src/api/client.ts:50-101`.

**Most likely interview question:** "Why not just use a long-lived JWT?"

**Ideal answer:** "Long-lived JWTs can't be revoked â€” once issued, they're valid until expiry. By using short-lived access tokens (15 min) with server-side refresh tokens, we can: (1) revoke sessions instantly by marking the refresh token as revoked, (2) rotate tokens on each refresh to limit the window of a stolen token, (3) revoke ALL sessions on password reset by calling `revoke_all_user_tokens`. The refresh token is stored as SHA-256 hash so a database breach doesn't expose usable tokens."

---

### LangGraph Nodes & State Machine

**What it is:** LangGraph models AI workflows as directed graphs where nodes are functions that transform a shared state dict, and edges (including conditional ones) control flow.

**How it works HERE:** `AgentState` is a TypedDict with fields like `sub_questions`, `research_findings`, `reflection_gaps`, `iteration_count`, `chunk_scores`, `web_used`. Each node function receives the full state and returns an updated copy. The graph is: `planner â†’ researcher â†’ reflector â†’(conditional)â†’ gap_filler|synthesizer â†’ writer â†’ END`. The conditional edge checks if gaps exist and iteration count < 3.

**Files:** `backend/agent/graph.py` (graph definition), `backend/agent/nodes/` (6 node functions).

**Most likely interview question:** "Why not just call the LLM in a loop?"

**Ideal answer:** "LangGraph gives us several things a manual loop doesn't: (1) typed state management â€” every node declares what it reads and writes, (2) the conditional edge `_should_fill_gaps` is a first-class graph concept, not a buried if-statement, (3) the graph is compiled once at module level and reused across requests, (4) each node independently checks for job cancellation by querying the DB, enabling graceful mid-execution cancellation, (5) the graph structure is self-documenting â€” you can trace the flow by reading `graph.py` alone."

---

### RAGAS Evaluation

**What it is:** RAGAS (Retrieval Augmented Generation Assessment) is a framework that measures RAG quality using LLM-as-judge metrics: Faithfulness (is the answer supported by context?), Answer Relevancy (does it actually answer the question?), and Context Utilization (is the retrieved context relevant?).

**How it works HERE:** The Streamlit dashboard (`eval_dashboard/dashboard.py`) runs a "dual-pass" evaluation: Pass 1 sends questions with `rag_only=true` (no web search), Pass 2 sends with web search enabled. For each question, it creates a chat session, sends the message, extracts the answer and contexts from the response, then feeds them to RAGAS. Results are persisted to the `eval_results` table via the `/api/v1/eval/results` endpoint and displayed with Plotly charts. A pass threshold of 0.70 is used to color-code scores.

**Files:** `eval_dashboard/ragas_runner.py` (RAGAS scoring), `eval_dashboard/dashboard.py` (Streamlit UI), `backend/api/v1/routers/eval.py` (persistence API), `backend/repositories/eval_repository.py` (DB operations).

**Most likely interview question:** "How do you know your RAG system actually works?"

**Ideal answer:** "We built a RAGAS evaluation pipeline. An admin uploads test PDFs, enters or auto-generates test questions, and runs a dual-pass evaluation. The 'RAG-Only' pass tests pure document retrieval quality. The 'Full Pipeline' pass tests with web search fallback. For each question, we measure three metrics using RAGAS with Gemini as the judge LLM: faithfulness (is the answer grounded in the retrieved context?), answer relevancy (does it actually address the question?), and context utilization (did we retrieve the right chunks?). All scores above 0.70 pass. Historical results are tracked over time in PostgreSQL and visualized in Plotly charts, so we can catch regressions."

---

### Confidence Scoring

**What it is:** A tri-level confidence indicator (high/medium/low) derived from the actual cosine similarity of retrieved chunks.

**How it works HERE â€” Mode 1 (Chat):** `_compute_confidence()` in `chat_service.py:35-42` â€” if web search was used AND top_score is 0.0 â†’ "low". Else: score â‰¥ 0.75 â†’ "high", â‰¥ 0.65 â†’ "medium", else â†’ "low".

**How it works HERE â€” Mode 2 (Research):** `writer_node` in `writer.py:30-41` â€” averages ALL cosine scores from all sub-questions, subtracts `WEB_SEARCH_PENALTY` (0.10) if web search was used. Uses different thresholds: â‰¥ 0.70 â†’ "high", â‰¥ 0.45 â†’ "medium", else â†’ "low".

**Most likely interview question:** "Why are Mode 1 and Mode 2 confidence thresholds different?"

**Ideal answer:** "Mode 1 scores a single query against a specific document, so a 0.75 threshold for 'high' makes sense â€” the chunks should be highly relevant. Mode 2 averages scores across 5+ sub-questions, some of which might not exist in the user's documents at all. A 0.70 threshold for 'high' with a 0.10 web penalty accounts for the reality that broad research topics inevitably require some web supplementation. The research confidence is computed in `writer.py` and the chat confidence in `chat_service.py`."

---

### Rate Limiting

**What it is:** IP-based request throttling to prevent abuse.

**How it works HERE:** `slowapi` with two tiers: `STANDARD_LIMIT` (30/min) for general endpoints, `AI_LIMIT` (10/min) for expensive LLM-calling endpoints. The limiter is attached to specific routes via `@limiter.limit(AI_LIMIT)` decorator on the `send_message` and `start_research` endpoints.

**Files:** `backend/middleware/rate_limiter.py`, applied in `backend/api/v1/routers/chat.py:53` and `backend/api/v1/routers/research.py:20`.

---

### Connection Pooling

**What it is:** Reusing database connections instead of opening/closing one per request.

**How it works HERE:** `psycopg2.pool.ThreadedConnectionPool` with min=2 (always warm), max=10 (cap for Supabase free tier). The `get_db()` context manager gets a connection from the pool, yields it, commits on success, rollbacks on exception, and always returns it to the pool via `putconn()` â€” never closes it.

**Files:** `backend/database/db_client.py:18-97`.
# DocMind AI â€” Deep Dive Part 3: Interview Questions & Honest Summary

---

## 6. INTERVIEW QUESTIONS â€” PER MODULE

### Module: Authentication System

**If they ask you about this:**

**Q1: "Walk me through your authentication flow."**
> User registers with email/password/full_name â†’ password validated (8+ chars, uppercase, digit, special char via Pydantic field_validator in `auth_models.py`) â†’ bcrypt hash stored in `users` table â†’ login returns JWT access token (15 min, HS256) + sets httpOnly refresh token cookie (UUID, SHA-256 hashed in DB, 7 day expiry) â†’ on 401, Axios interceptor calls `/auth/refresh`, server validates hash, rotates token, returns new access token. Multiple concurrent 401s are queued â€” only one refresh call fires.

**Q2: "How do you prevent email enumeration on the forgot-password endpoint?"**
> The endpoint always returns `"If this email is registered, you will receive a reset link."` regardless of whether the email exists (`auth_service.py:151`). This prevents attackers from discovering valid emails.

**Q3: "What happens to sessions when a user resets their password?"**
> All refresh tokens for that user are revoked via `token_repository.revoke_all_user_tokens()` (`auth_service.py:184`). This invalidates all existing sessions across all devices. The reset token itself is marked as `used=TRUE`.

**Q4: "Why httpOnly cookies for refresh tokens instead of localStorage?"**
> httpOnly cookies are inaccessible to JavaScript, preventing XSS attacks from stealing the refresh token. We also set `secure=True` and `samesite=none` in production (`auth_service.py:20-29`), and `secure=False, samesite=lax` in local dev.

**Follow-up: "What about CSRF?"**
> The refresh endpoint reads the token from a cookie (not a header), which could be CSRF-vulnerable. However, the endpoint only returns a new access token â€” it doesn't perform any state-changing operations. The access token must be explicitly attached as a `Bearer` header, which CSRF can't do.

---

### Module: Document Management & RAG Pipeline

**If they ask you about this:**

**Q1: "What happens if a document upload fails midway â€” after the file is saved but before indexing completes?"**
> There's explicit rollback logic in `doc_service.py:105-123`. If any step after file save fails, the code catches the exception and: (1) deletes the file from storage via `storage.delete_file()`, (2) deletes any vectors from ChromaDB via `delete_document_vectors()`. Both cleanup steps are wrapped in their own try/except to ensure partial cleanup doesn't cause a secondary crash.

**Q2: "How do you handle document limits?"**
> Before upload, `document_repository.count_by_user()` checks the count against `MAX_DOCUMENTS_PER_USER` (default 5). If at limit, the response includes the list of existing documents so the user knows what to delete (`doc_service.py:46-57`). This uses HTTP 409 Conflict.

**Q3: "Why RecursiveCharacterTextSplitter specifically?"**
> It tries to split on natural boundaries (paragraphs â†’ sentences â†’ words) before falling back to character count. This produces more semantically coherent chunks than a naive character splitter. The 200-char overlap ensures ideas that span chunk boundaries aren't lost.

**Q4: "How are suggested questions generated?"**
> After indexing, the first 3 chunks are retrieved from ChromaDB, concatenated, and sent to Gemini with a prompt asking for exactly 5 questions. Results are cached in the `suggested_questions` table â€” subsequent requests return the cached version (`doc_service.py:177-234`).

**Q5: "What happens when you delete a document?"**
> Three-layer deletion in `doc_service.py:136-174`: (1) delete file from storage, (2) delete vectors from ChromaDB via `collection.delete(where={"document_id": doc_id})`, (3) delete DB record (CASCADE deletes `suggested_questions`). Each step has independent error handling â€” if one fails, the others still execute, and warnings are returned.

---

### Module: Chat Q&A (Mode 1)

**If they ask you about this:**

**Q1: "How does your system decide when to use web search?"**
> The function `should_use_web_search()` in `retriever.py:31-37` checks two conditions: (1) if the user's ChromaDB collection is empty (no documents uploaded), web search always triggers, or (2) if the top cosine similarity score from RAG is below `WEB_SEARCH_FALLBACK_THRESHOLD` (0.65). This threshold is configurable via environment variable.

**Q2: "How do you maintain conversation context?"**
> The last 10 messages (configurable via `CHAT_CONTEXT_WINDOW`) are fetched using a subquery that gets the most recent N messages ordered DESC, then re-orders them ASC (`chat_repository.py:120-133`). This context is formatted as `"USER: ...\nASSISTANT: ..."` and injected into the prompt template.

**Q3: "What does the confidence score actually mean?"**
> It's derived from the cosine similarity of the best-matching chunk. â‰¥0.75 means the document had a very relevant passage â€” "high". â‰¥0.65 means somewhat relevant â€” "medium". Below that, or if only web search was used â€” "low". This isn't a measure of answer correctness; it's a measure of how well the user's documents matched the query.

**Follow-up: "How would you make it more accurate?"**
> "I'd add answer-level validation â€” have a second LLM call assess whether the generated answer is actually supported by the retrieved context (similar to what RAGAS faithfulness does). Currently the confidence only reflects retrieval quality, not generation quality."

**Q4: "How does session auto-titling work?"**
> When the session title is still "New Chat" (the default), the first user query is truncated to 50 characters and set as the title via `chat_repository.update_session_title()` (`chat_service.py:170-172`).

---

### Module: Deep Research Agent (Mode 2)

**If they ask you about this:**

**Q1: "Walk me through the agent architecture."**
> It's a LangGraph `StateGraph` with 6 nodes compiled once at module load (`graph.py:69`). The flow is: Planner breaks the topic into 5 sub-questions â†’ Researcher runs RAG + conditional web search for each â†’ Reflector evaluates coverage gaps â†’ if gaps exist and we haven't iterated 3 times, Gap Filler researches the gaps and loops back to Reflector â†’ once satisfied, Synthesizer combines everything â†’ Writer computes confidence and generates a 7-section DOCX report.

**Q2: "How do you handle cancellation mid-research?"**
> Every node checks cancellation at entry by querying `research_repository.find_by_id(job_id)` and checking if `status == "cancelled"`. The Researcher node checks before each sub-question too (`researcher.py:27-29`). When cancelled, the node returns state unchanged, and the graph completes without further processing. The cancel API endpoint sets `status = 'cancelled'` in the DB.

**Q3: "What happens if the server restarts during a research job?"**
> On startup, `mark_stale_jobs_failed()` in `main.py:36-38` finds any jobs in active states (`queued`, `planning`, etc.) that haven't been updated in 20 minutes (`STALE_JOB_TIMEOUT_MINUTES`) and marks them as `failed` with the message "Job was interrupted by a server restart." Additionally, `cleanup_expired_jobs()` deletes jobs older than 7 days and cleans up their report files.

**Q4: "How is the confidence score different from Mode 1?"**
> Mode 2 averages ALL cosine scores across all sub-questions and gap-fill queries. It then subtracts a 0.10 penalty if web search was used anywhere (`writer.py:30-41`). The thresholds are also different: â‰¥0.70 for high (vs 0.75 in Mode 1) and â‰¥0.45 for medium (vs 0.65), reflecting that broad research topics naturally have more variable retrieval quality.

**Q5: "What does the DOCX report contain?"**
> Seven sections generated by `report/docx_writer.py`: (1) Title page with topic, date, color-coded confidence, (2) Executive Summary (first 3 paragraphs of synthesis), (3) Research Sub-Questions list, (4) Findings per sub-question with citations, (5) Coverage Gaps Analysis, (6) Full Synthesis narrative, (7) References extracted via regex from findings (both `[filename.pdf p.N]` document refs and `[Web: title](url)` web refs).

---

### Module: Admin & Evaluation

**If they ask you about this:**

**Q1: "How does the admin panel work without role-based access control?"**
> The admin endpoints are protected by a shared password sent via `X-Admin-Password` header, verified against `ADMIN_PASSWORD` in config (`eval.py:23-29`, `admin.py:16-21`). This is simple but effective for a single-admin system. The admin panel in the frontend (`AdminPage.tsx`) accepts the password and sends it with every admin API call.

**Q2: "How does the RAGAS evaluation actually run?"**
> The Streamlit dashboard: (1) auto-registers/logs in as `eval@docmind.ai` to get an API token, (2) uploads test PDFs via the normal document upload API, (3) for each test question, creates a chat session and sends the question (once with `rag_only=true`, once without), (4) extracts the answer and source contexts from the response, (5) feeds Q/A/contexts to RAGAS which uses Gemini as the judge LLM, (6) persists scores to the `eval_results` table via the admin eval API, (7) displays results and history with Plotly charts.

**Q3: "What's the difference between rag_only and full_pipeline eval modes?"**
> `rag_only` passes `?rag_only=true` query param to the chat endpoint, which skips the web search fallback â€” only document chunks are used. `full_pipeline` allows web search. Comparing the two shows how much the web fallback improves (or degrades) answer quality.

---

## 7. WHAT YOU ACTUALLY BUILT â€” HONEST SUMMARY

### What You Can Honestly Claim

âœ… **"I built a full-stack AI research assistant with two modes: conversational Q&A with RAG and autonomous deep research with report generation."** â€” This is the entire project.

âœ… **"I implemented a complete RAG pipeline from scratch â€” PDF extraction, chunking, embedding, vector storage, semantic retrieval, and LLM synthesis."** â€” `rag/indexer.py` and `rag/retriever.py` are custom code, not a pre-built LangChain RAG chain.

âœ… **"I designed a LangGraph-based multi-step research agent with a reflect-and-fill loop."** â€” The 6-node graph with conditional edges is your design (`agent/graph.py`).

âœ… **"I implemented JWT authentication with refresh token rotation, bcrypt hashing, and SHA-256 token storage."** â€” All hand-written in `auth/`, `services/auth_service.py`, `repositories/token_repository.py`.

âœ… **"I built confidence scoring derived from actual retrieval cosine similarity scores."** â€” Custom logic in `chat_service.py` and `writer.py`.

âœ… **"I built a RAGAS evaluation framework with dual-pass (RAG-only vs full pipeline) testing."** â€” `eval_dashboard/` is a complete Streamlit app.

âœ… **"I implemented an Axios interceptor that handles concurrent 401s with a queue pattern."** â€” `frontend/src/api/client.ts` has a non-trivial `failedQueue` + `processQueue` implementation.

âœ… **"I designed the database schema with lazy DDL initialization and double-checked locking."** â€” `db_client.py` with `_db_init_lock` and `_ensure_db()`.

âœ… **"I implemented stale job recovery and retention-based cleanup on server startup."** â€” `main.py:35-43`, `research_repository.py:106-151`.

âœ… **"I built environment-aware deployment â€” single codebase works locally and in production."** â€” Storage, ChromaDB, cookies, logging all switch based on `ENVIRONMENT`.

### What Is Surface Level or Borrowed (Know Your Boundaries)

âš ï¸ **shadcn/ui components** â€” The 13 files in `frontend/src/components/ui/` are generated by the shadcn CLI, not hand-written. You customized their usage but didn't write `button.tsx`, `card.tsx`, etc. from scratch.

âš ï¸ **LangChain wrappers** â€” You use `ChatGoogleGenerativeAI` and `GoogleGenerativeAIEmbeddings` as black boxes. You didn't implement the Gemini API integration â€” LangChain handles that.

âš ï¸ **RAGAS metrics** â€” You call `evaluate()` from the RAGAS library. You understand what the metrics mean and how to interpret them, but the actual Faithfulness/ResponseRelevancy/ContextUtilization computation is the library's.

âš ï¸ **No WebSocket/streaming** â€” Chat responses are synchronous HTTP. There's no token-by-token streaming. If asked "why not stream?", say "for an MVP, synchronous was simpler and the Gemini response times are fast enough. Streaming would be the next iteration."

âš ï¸ **No RBAC** â€” There's no role system. "Admin" is just a shared password. If asked, acknowledge this and say a production system would use a `role` column on the `users` table.

âš ï¸ **No automated tests** â€” There are no unit or integration tests in the codebase. The RAGAS dashboard is the closest thing to quality validation. If asked, acknowledge this as a gap.

âš ï¸ **Password validation duplication** â€” The same password regex validation exists in both `RegisterRequest` and `ResetPasswordRequest` in `auth_models.py`. This should be a shared validator.

âš ï¸ **The README phase checklist shows phases 2-7 as â¬œ** â€” but the code for all phases is implemented. The README wasn't updated.

### Key Metrics You Can Defend

| Metric | Value | Source |
|---|---|---|
| PDF size limit | 10 MB | `config.py:58` |
| Documents per user | 5 | `config.py:59` |
| Chunk size / overlap | 1000 / 200 chars | `config.py:63-64` |
| RAG top-k | 5 chunks | `config.py:65` |
| Web search threshold | 0.65 cosine | `config.py:66` |
| Access token TTL | 15 minutes | `config.py:23` |
| Refresh token TTL | 7 days | `config.py:24` |
| Max research iterations | 3 reflect loops | `config.py:85` |
| Sub-questions per topic | 5 | `config.py:84` |
| Rate limit (AI) | 10 req/min | `config.py:92` |
| DB pool | min=2, max=10 | `db_client.py:29-31` |
| Bcrypt work factor | 12 rounds | `config.py:26` |
| RAGAS pass threshold | 0.70 | `config.py:99` |
| Stale job timeout | 20 minutes | `config.py:88` |
| Job retention | 7 days | `config.py:87` |

---

*End of document. Every claim above is backed by code I read. If something wasn't in the code, I didn't claim it.*
