
# CHAPTER 7: FULL STACK CONCEPTS — EXPLAINED FROM ZERO

## CONCEPT: REST APIs and HTTP Methods

**THE SIMPLE VERSION:**
A restaurant menu. GET = "show me the menu." POST = "I'd like to order this." PATCH = "change my order." DELETE = "cancel my order." The waiter (API) takes your request to the kitchen (backend) and brings back a response.

**HOW IT LIVES IN THIS CODE:**
- `GET /api/v1/chat/sessions` — list all sessions (reading data)
- `POST /api/v1/chat/sessions` — create a new session (creating data)
- `PATCH /api/v1/chat/sessions/{id}` — rename a session (partial update)
- `DELETE /api/v1/chat/sessions/{id}` — delete a session (removing data)
- `POST /api/v1/research` returns `202 Accepted` (not 200) because the work happens asynchronously — the response means "I accepted your request and will work on it," not "here's your result."

**INTERVIEW Q:** "Why 202 instead of 200 for research?"
**Answer:** "200 means the request is complete. 202 means the request was accepted for processing, but the processing isn't done. The client should poll for the result. This accurately represents that research takes minutes, not milliseconds."

## CONCEPT: JWT Authentication

**THE SIMPLE VERSION:**
A movie ticket with your name, seat number, and expiry time printed on it. Anyone can read the ticket (JWTs are base64-encoded, not encrypted), but only the theater can ISSUE a valid one because they have the secret stamp (JWT_SECRET_KEY). If someone modifies the ticket, the stamp won't match and it's rejected.

**HOW IT LIVES IN THIS CODE:**
`jwt_handler.py` creates tokens with `jwt.encode({user_id, email, iat, exp}, SECRET, HS256)`. `dependencies.py` verifies them: `jwt.decode(token, SECRET, [HS256])`. The token lives in the `Authorization: Bearer <token>` header, set by the Axios request interceptor in `client.ts:27-33`.

**WHY NOT ENCRYPTED?** JWTs are signed, not encrypted. The signature proves authenticity (the server issued it) and integrity (nobody tampered with it). Encryption would hide the payload, but the payload contains only `user_id` and `email` — not sensitive enough to encrypt.

## CONCEPT: CORS (Cross-Origin Resource Sharing)

**THE SIMPLE VERSION:**
A bank that only accepts phone calls from numbers it recognizes. If a stranger calls, the bank hangs up. CORS tells the browser: "Only accept responses from these specific origins (domains)."

**HOW IT LIVES IN THIS CODE:**
`main.py:62-71` configures `CORSMiddleware` with `allow_origins=settings.cors_origin_list`. Locally this is `["http://localhost:5173"]` (the Vite dev server). In production it would be `["https://your-app.vercel.app"]`. Without CORS, the browser would block ALL API calls from the frontend because it runs on a different port.

## CONCEPT: PostgreSQL Schema Design

**HOW IT LIVES IN THIS CODE:**
10 tables with UUID primary keys (via `pgcrypto`'s `gen_random_uuid()`):
- `users` — identity with bcrypt hash, last_login tracking
- `refresh_tokens` — SHA-256 hashed tokens with `is_revoked` flag
- `password_reset_tokens` — with `used` flag and expiry
- `documents` — metadata with FK to users
- `suggested_questions` — FK to documents, CASCADE delete
- `chat_sessions` — FK to users, with auto-updated timestamps
- `chat_messages` — FK to sessions with JSONB for `sources` and `tools_used`
- `research_jobs` — status enum, JSONB progress, expiry
- `app_settings` — key-value store for admin toggles
- `eval_results` — RAGAS scores with `passed` boolean

**INTERVIEW Q:** "Why UUIDs instead of auto-incrementing integers?"
**Answer:** "UUIDs prevent enumeration attacks (an attacker can't guess the next ID by incrementing), work across distributed systems without coordination, and are safe to expose in URLs. The trade-off is slightly larger storage and slower index lookups, but for this scale it's negligible."

## CONCEPT: React Component Architecture

**HOW IT LIVES IN THIS CODE:**
Components follow a clear hierarchy:
- **Pages** (`DashboardPage`, `ResearchPage`, `AdminPage`) — compose multiple components, manage page-level state
- **Feature Components** (`ChatWindow`, `SessionSidebar`, `DocumentPanel`) — own their domain logic
- **UI Primitives** (`Button`, `Card`, `Input`) — shadcn/ui generated, purely presentational

State management uses React's built-in hooks (useState, useEffect, useCallback) — no Redux, no Zustand, no React Query. Global state is only `AuthContext` (access token + user). All other state is local to components.

**CRITIQUE:** The project does NOT use React Query (TanStack Query). Every API call manually manages loading/error states with `useState`. React Query would provide automatic caching, background refetching, optimistic updates, and retry logic out of the box. This is the single biggest improvement opportunity on the frontend.

## CONCEPT: Environment-Aware Configuration

**HOW IT LIVES IN THIS CODE:**
A single `ENVIRONMENT` variable switches behavior in 4 places:
1. `db_client.py` — `DATABASE_URL` points to local PostgreSQL or Supabase
2. `doc_service.py:16-22` — imports `local_storage` or `supabase_storage`
3. `rag/retriever.py:12-21` — creates `PersistentClient` or `CloudClient`
4. `auth_service.py:18-39` — cookies set with `secure=False/True`, `samesite=lax/none`

This means the exact same code runs locally and in production. No conditional branches scattered throughout — the switch happens at the import/initialization level.

---

# CHAPTER 8: WHAT YOU CAN HONESTLY CLAIM YOU BUILT

## LIST A — THINGS YOU DEEPLY OWN

1. **Complete RAG pipeline from scratch** — "I built PDF extraction with pdfplumber, recursive text chunking with configurable overlap, Gemini embedding, ChromaDB storage with per-user collection isolation, and cosine-similarity retrieval with a configurable threshold that triggers web search fallback."

2. **LangGraph research agent with reflect-loop** — "I designed a 6-node state machine where a reflector evaluates coverage gaps and conditionally loops back through a gap-filler up to 3 times before synthesis."

3. **JWT auth with refresh token rotation** — "I implemented short-lived access tokens, SHA-256-hashed refresh tokens stored in PostgreSQL, rotation on every refresh, and revocation of all tokens on password reset."

4. **Axios 401 interceptor with request queuing** — "I built an interceptor that queues concurrent failed requests, fires a single refresh call, and replays all queued requests with the new token."

5. **Confidence scoring from retrieval metrics** — "Confidence is computed from actual cosine similarity scores, not arbitrary labels. Different thresholds for chat (single-query) vs research (multi-query average with web penalty)."

6. **Dual-pass RAGAS evaluation** — "I built a Streamlit dashboard that tests the pipeline twice — once with web search disabled, once enabled — to isolate RAG quality from web-search quality."

7. **Database connection pooling with lazy DDL** — "I implemented ThreadedConnectionPool with double-checked locking for lazy schema initialization, solving Render's health-check timeout."

8. **7-section DOCX report generator** — "I used python-docx to generate structured reports with styled title pages, color-coded confidence badges, extracted references, and proper formatting."

9. **Environment-aware dual-deployment** — "A single codebase works locally and in production by switching storage, database, ChromaDB, and cookie configuration via one environment variable."

10. **Admin AI kill-switch** — "A database-driven toggle that disables all LLM calls globally, returning 503 errors, controllable via a password-protected admin endpoint."

## LIST B — THINGS THAT ARE SURFACE LEVEL

1. **shadcn/ui components** — The 13 files in `components/ui/` are CLI-generated. Study: How shadcn/ui works internally, how to customize theme tokens, how to create your own shadcn-style component.

2. **LangChain wrappers** — `ChatGoogleGenerativeAI` and `GoogleGenerativeAIEmbeddings` are black boxes. Study: The Gemini API directly, how LangChain wraps it, what parameters are available (temperature, top_k, max_tokens).

3. **RAGAS internals** — You call `evaluate()` but don't implement the metrics. Study: How faithfulness scoring works internally (statement extraction → entailment checking), how answer relevancy uses reverse-question generation.

4. **Tailwind CSS** — Used via utility classes but no custom Tailwind plugins or theme extensions. Study: How `@apply` works, custom plugins, responsive design patterns.

5. **No automated tests** — This is a significant gap. Study: pytest for backend, Vitest + React Testing Library for frontend, how to mock database connections and external APIs.

6. **No streaming responses** — Chat is synchronous. Study: Server-Sent Events (SSE) with FastAPI's `StreamingResponse`, how to stream LLM tokens to the frontend.

---

# CHAPTER 9: THE INTERVIEW SIMULATION

**Q1: "Explain this project in 2 minutes."**
TESTING: Can you communicate clearly under pressure?
ANSWER: "DocMind AI is a full-stack research assistant with two modes. Mode 1: upload PDFs, ask questions, get RAG-powered answers with citations and confidence scores. If documents don't cover the query, it falls back to web search via Tavily. Mode 2: submit a research topic, and a LangGraph agent decomposes it into sub-questions, researches each one, reflects on coverage gaps, fills them iteratively, and generates a downloadable DOCX report. The backend is FastAPI with PostgreSQL and ChromaDB, the frontend is React with TypeScript, and we have a RAGAS evaluation dashboard that measures pipeline quality."
FOLLOW-UP: "What is your most technically interesting feature?"
ANSWER: "The reflect-loop in the research agent. After gathering findings, a reflector node evaluates whether the research is comprehensive. If it finds gaps, a gap-filler node researches them and the reflector checks again — up to 3 iterations. This produces significantly better research coverage than a single-pass approach."

**Q2: "How does RAG work in your system?"**
TESTING: Do you understand your core AI pipeline?
ANSWER: "PDFs are extracted with pdfplumber, chunked into 1000-character overlapping segments, embedded with Gemini's embedding model, and stored in per-user ChromaDB collections. At query time, the query is embedded, ChromaDB finds the 5 nearest chunks by cosine similarity, and those chunks are injected into the LLM prompt alongside conversation history. The LLM generates an answer grounded in those chunks."
FOLLOW-UP: "Why 1000 characters?"
ANSWER: "Trade-off between context and precision. Too small and chunks lack context. Too large and the embedding represents too many topics, reducing retrieval accuracy. 1000 characters is roughly a paragraph — enough for a coherent thought."

**Q3: "How do you handle authentication?"**
TESTING: Security understanding.
ANSWER: "Short-lived JWT access tokens (15 min, HS256) for API authentication, long-lived refresh tokens (7 days) stored as SHA-256 hashes in PostgreSQL and delivered as httpOnly cookies. On every refresh, the old token is revoked and a new one issued — token rotation. On password reset, all refresh tokens for the user are revoked."
FOLLOW-UP: "Why hash refresh tokens?"
ANSWER: "If the database is breached, attackers get hashes, not usable tokens. They cannot reverse SHA-256 to get the raw token needed to call the refresh endpoint."

**Q4: "What happens if the Gemini API goes down?"**
TESTING: Error handling and resilience.
ANSWER: "The admin kill-switch. An admin can toggle the `ai_enabled` flag in the app_settings table via a password-protected endpoint. When disabled, all AI endpoints (chat, research, suggested questions) return 503 Service Unavailable. Additionally, every LLM call is wrapped in try/except — failures are logged and returned as user-friendly error messages, not 500 crashes."

**Q5: "How do you know your RAG quality is good?"**
TESTING: Quality assurance mindset.
ANSWER: "We built a RAGAS evaluation dashboard. It runs dual-pass tests — RAG-only (web search disabled) and full pipeline — measuring faithfulness, answer relevancy, and context utilization using Gemini as an LLM judge. Scores above 0.70 pass. Historical results are tracked in PostgreSQL and visualized in Plotly charts to detect regressions."

**Q6: "Why LangGraph instead of a simple chain?"**
TESTING: Architecture decision-making.
ANSWER: "The research agent needs a conditional loop — the reflector might find coverage gaps that need additional research. A LangChain chain is linear. LangGraph's conditional edges let me route from reflector to gap-filler and back to reflector, up to 3 iterations."

**Q7: "How do you prevent SQL injection?"**
TESTING: Security fundamentals.
ANSWER: "Every SQL query uses psycopg2 parameterized queries with %s placeholders. User input never touches the SQL string directly. For example: `cur.execute('SELECT * FROM users WHERE email = %s', (email,))`. The driver handles escaping."

**Q8: "Walk me through what happens when a chat message is sent."**
TESTING: End-to-end understanding.
ANSWER: "User types in ChatWindow.tsx, optimistic UI adds the message immediately, POST to /chat/{session_id}/messages. Backend: check AI enabled, verify session ownership, save user message, load last 10 messages for context, embed query, search ChromaDB for top 5 chunks, check if top cosine score < 0.65 (trigger web search if so), inject document + web context into prompt, call Gemini, compute confidence from cosine score, save assistant message with sources/tools/confidence as JSONB, auto-title session if first message, return response. Frontend renders MessageBubble with ConfidenceBar, ToolBadge, and CitationBlock."

**Q9: "What would you change if starting over?"**
TESTING: Self-awareness and growth.
ANSWER: "Three things. First, use React Query instead of manual useState for API calls — it provides caching, background refetching, and retry logic for free. Second, add streaming responses via Server-Sent Events so users see tokens appear in real-time instead of waiting for the full response. Third, use Alembic for database migrations instead of DDL in code."

**Q10: "How do you handle concurrent users?"**
TESTING: Scalability understanding.
ANSWER: "ThreadedConnectionPool with max=10 connections handles concurrent database access. Per-user ChromaDB collections ensure search isolation. Rate limiting via slowapi prevents any single IP from overwhelming the server. FastAPI runs sync endpoints in a thread pool. The main bottleneck is LLM API calls — these are sequential per user but concurrent across users."

**Q11: "What is the most complex bug you fixed?"**
TESTING: Debugging experience.
ANSWER: "Circular recursion in database initialization. `get_db()` called `_ensure_db()` which called `init_db()` which called `get_db()` — infinite loop. Fixed by creating `_init_db_raw()` that grabs a connection directly from the pool, bypassing `get_db()` entirely. Documented in `docs/db_optimization_plan.md`."

**Q12: "How do you handle file uploads securely?"**
TESTING: Security in practice.
ANSWER: "Four validations: MIME type must be application/pdf, file size must be under 10MB, user must not exceed 5 documents. Files are saved with a UUID prefix to prevent filename collisions and directory traversal. If indexing fails after file save, there is explicit rollback that deletes the file from storage and vectors from ChromaDB."

**Q13: "Explain your confidence scoring."**
TESTING: Feature depth.
ANSWER: "Confidence is derived from cosine similarity of retrieved chunks, not from the LLM's self-assessment. In chat mode: top_score >= 0.75 is high, >= 0.65 is medium, below is low. If web search was used and no document matches (score 0.0), it is forced to low. In research mode: average of all chunk scores across sub-questions minus a 0.10 penalty if web search was used anywhere."

**Q14: "Why PostgreSQL instead of MongoDB?"**
TESTING: Database choice reasoning.
ANSWER: "The data is relational — sessions have messages, users have documents, documents have suggested questions. Foreign keys enforce referential integrity. JSONB columns (sources, progress) provide document-store flexibility where needed. MongoDB would lose the referential integrity guarantees."

**Q15: "How does the frontend handle token refresh?"**
TESTING: Frontend complexity.
ANSWER: "An Axios response interceptor catches 401s. It checks if a refresh is already in progress — if so, it queues the failed request. If not, it calls /auth/refresh, gets a new access token, replays the original request, and processes the queue so all concurrent failures are retried with the new token. This prevents cascading refresh calls."

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
ANSWER: "The database connection pool. Max 10 connections with Supabase's 15 limit. I would need to switch to connection pooling via PgBouncer or Supabase's built-in pooler. Second, ChromaDB — 10,000 per-user collections would strain the vector database. I would evaluate switching to a shared collection with metadata filtering, or a managed service like Pinecone. Third, the Gemini API rate limits — I would need to implement request queuing with exponential backoff."
