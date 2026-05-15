# Software Requirements Specification (SRS)
## DocMind AI — AI Research & Synthesis Agent
### Version 1.1 | IEEE 830 Compliant | Post-Review Patch Applied

---

**Document Control**

| Field              | Detail                                      |
|--------------------|---------------------------------------------|
| Document Title     | Software Requirements Specification — DocMind AI |
| Version            | 1.1 — Post-Review Patch                    |
| Status             | Baseline — Implementation Ready             |
| Author             | Project Team — DocMind AI                  |
| Date               | 2025                                        |
| Classification     | Internal / Academic                         |

**Change Log**

| Version | Changes Applied |
|---------|-----------------|
| 1.0     | Initial baseline SRS |
| 1.1     | **C1** FR-AUTH-012 / SEC-005: `SameSite=Strict` → `SameSite=None; Secure` (production) / `SameSite=Lax` (local). **C2** Dev embedding model changed from HuggingFace to Gemini Embeddings in both environments. **C3** Explicit route registration order added to Section 6.2.2. **C4** NFR-REL-006 added: Uvicorn `--proxy-headers` required for real-IP rate limiting behind Render. **M1** Mode 1 Q&A agent architecture fully defined in FR-CHAT-009. **M2** `EVAL_BACKEND_URL` added to env vars; `eval_dashboard/.env` added to folder structure. **M3** `progress` JSONB column added to `research_jobs` schema; FR-RES-008/011 updated. **M4** FR-RES-029 added: stale job detection on startup; `STALE_JOB_TIMEOUT_MINUTES` added to env. **M5** FR-ADMIN-007 fixed: cross-service Streamlit trigger removed. **M6** Documents table note added: `uploaded_at` is immutable upload date, not "last modified". **M7** Web search decision logic defined with `WEB_SEARCH_FALLBACK_THRESHOLD`; shared utility function specified. **N1** `RESEARCH_POLL_INTERVAL_MS` moved to frontend env section as `REACT_APP_RESEARCH_POLL_INTERVAL_MS`. **N2** UptimeRobot interval corrected: 14 min → 5 min. **N3** ChromaDB UUID hyphen replacement made unconditional. **N4** Retention cleanup moved from `/health` endpoint to startup event. **N5** `MAX_SESSIONS_PER_USER` added to FR-CHAT-002 and env vars. **N6** HTTP 207 replaced with HTTP 200 + `warnings` array in FR-DOC-022. |

---

## Table of Contents

1. Introduction
2. Overall Description
3. System Features
4. External Interface Requirements
5. Non-Functional Requirements
6. System Architecture
7. Data Design
8. API Design
9. Configuration & Environment
10. Security Requirements
11. Constraints
12. Assumptions & Dependencies
13. Appendix A — `.env.example`
14. Appendix B — Folder Structure
15. Appendix C — Glossary

---

---

# 1. Introduction

## 1.1 Purpose

This Software Requirements Specification (SRS) document defines the complete functional and non-functional requirements for **DocMind AI**, a full-stack AI Agentic Web Application. It is intended to serve as the authoritative reference document for all development, testing, and deployment activities. The document is structured in accordance with IEEE Standard 830-1998 and has been adapted to reflect a zero-cost, student-implementable architecture.

This SRS is the primary source of truth at the time of implementation. Any deviation from this document must be recorded as a change request with justification.

## 1.2 Scope

**DocMind AI** is a web-based intelligent research assistant that enables authenticated users to:

1. Upload research documents (PDFs) and ask questions about their content using a Retrieval-Augmented Generation (RAG) pipeline — referred to as **Mode 1: Conversational Q&A**.
2. Submit a research topic and receive an autonomously generated, cited, downloadable research report produced by a multi-step AI agent — referred to as **Mode 2: Deep Research**.

The system is designed for researchers, students, and knowledge workers who need to extract, synthesize, and verify information across private document collections and the live web, without relying on generic, ungrounded language model responses.

The scope of this v1 document covers:

- Custom JWT-based authentication with access/refresh token architecture
- Document upload, storage, indexing, search, and deletion
- Multi-session conversational Q&A with citations, confidence scores, and chat management
- Asynchronous deep research with a multi-node LangGraph state machine
- An admin panel for AI service control
- A publicly accessible RAGAS evaluation dashboard
- Full deployment on zero-cost platforms (Vercel, Render, Supabase, ChromaDB Cloud)

**Out of Scope for v1 (Future Enhancements):**

- Multi-provider LLM support (OpenAI, Groq, etc.)
- User-supplied API keys
- Team/collaborative workspaces
- Real-time WebSocket streaming of agent responses
- CDN integration for global static asset delivery
- Advanced caching layers (Redis)
- Multi-tenancy at the database level beyond user_id scoping

## 1.3 Definitions, Acronyms, and Abbreviations

| Term               | Definition                                                                 |
|--------------------|----------------------------------------------------------------------------|
| SRS                | Software Requirements Specification                                        |
| JWT                | JSON Web Token — a compact, URL-safe token format for representing claims  |
| Access Token       | Short-lived JWT used to authenticate individual API requests (15 minutes)  |
| Refresh Token      | Long-lived opaque token used to obtain new access tokens (7 days)         |
| RAG                | Retrieval-Augmented Generation — technique combining vector search with LLM |
| LLM                | Large Language Model (Gemini 2.5 Flash in this system)                    |
| LangGraph          | A graph-based agent orchestration framework built on top of LangChain      |
| ChromaDB           | Open-source vector database used for semantic document chunk storage       |
| RAGAS              | RAG Assessment framework — measures faithfulness, relevancy, precision     |
| Cosine Similarity  | Mathematical measure of vector similarity used for chunk retrieval scoring |
| DOCX               | Microsoft Word document format, used for generated research reports        |
| Supabase           | Open-source Firebase alternative providing PostgreSQL, Storage, and more   |
| Render             | Free-tier cloud platform for hosting Python/FastAPI backends               |
| Vercel             | Free-tier platform for hosting React frontends                             |
| UptimeRobot        | Free external ping service to prevent Render free-tier cold starts         |
| Tavily             | Web search API with a free tier, used for live internet retrieval          |
| CORS               | Cross-Origin Resource Sharing — HTTP header mechanism for browser security |
| ORM                | Object Relational Mapper — maps database tables to Python objects          |
| N+1 Problem        | Performance anti-pattern involving excessive individual database queries    |
| httpOnly Cookie    | Browser cookie inaccessible to JavaScript, used to store refresh tokens   |
| bcrypt             | Password hashing algorithm with configurable work factor                  |
| Planner Node       | LangGraph node responsible for decomposing a research topic into sub-questions |
| Researcher Node    | LangGraph node that executes RAG and web search per sub-question          |
| Reflector Node     | LangGraph node that evaluates research coverage and identifies gaps       |
| Gap Filler Node    | LangGraph node that fills identified coverage gaps                        |
| Synthesizer Node   | LangGraph node that consolidates all findings into a coherent narrative   |
| Writer Node        | LangGraph node that generates the formatted DOCX report                   |
| slowapi            | Python rate-limiting library compatible with FastAPI                      |
| python-docx        | Python library for generating Microsoft Word documents                    |

## 1.4 Document Conventions

- Requirements are stated using the keyword **"shall"** for mandatory requirements and **"should"** for recommended/preferred behavior.
- Configuration values that must not be hardcoded are marked with `[ENV: VARIABLE_NAME]` indicating the `.env` key that governs that value.
- Requirements marked **[FUTURE SCOPE]** are architectural placeholders that are not implemented in v1 but should not be architecturally blocked.
- Requirements marked **[COST GUARD]** indicate a deliberate cost-saving design decision.

## 1.5 Overview

The remainder of this document is organized as follows:

- **Section 2** describes the overall product context and user characteristics.
- **Section 3** specifies all functional requirements, organized by feature area.
- **Section 4** describes all external interface requirements.
- **Section 5** specifies non-functional requirements including performance, security, and reliability.
- **Section 6** defines the system architecture, including layered design and deployment topology.
- **Section 7** defines the database schema and data flow.
- **Section 8** specifies the complete RESTful API design.
- **Section 9** documents all environment configuration requirements.
- **Section 10** consolidates all security requirements.
- **Sections 11–12** document constraints and assumptions.
- **Appendices A–C** provide the `.env.example`, folder structure, and glossary.

---

---

# 2. Overall Description

## 2.1 Product Perspective

DocMind AI is an independently developed, standalone web application. It does not replace or extend any existing product. It is designed as a portfolio-grade, production-deployed demonstration of full-stack AI engineering competencies including RAG pipelines, agentic workflows, asynchronous task orchestration, and evaluation dashboards.

The system integrates with the following external services, all of which provide free tiers sufficient for v1:

- **Supabase** — PostgreSQL database and file storage
- **ChromaDB Cloud** — Vector database for semantic chunk storage
- **Google Gemini API (AI Studio)** — LLM and embedding model
- **Tavily API** — Web search
- **Vercel** — Frontend hosting
- **Render** — Backend hosting
- **UptimeRobot** — Keep-alive pinging
- **GitHub** — Source control and CI/CD trigger

## 2.2 Product Functions

At a high level, DocMind AI shall provide the following capabilities:

1. **User Authentication** — Custom JWT-based registration, login, logout, and token refresh.
2. **Password Management** — Secure password reset via email-based token flow.
3. **Document Management** — Upload, list, search, and delete PDF documents, with automatic chunking and vector indexing.
4. **Suggested Questions** — Auto-generate document-specific questions after each upload.
5. **Conversational Q&A (Mode 1)** — Multi-session chat with RAG and web search, citations, and confidence indicators.
6. **Deep Research (Mode 2)** — Asynchronous multi-node agent research pipeline with live progress polling and DOCX report download.
7. **Research Job History** — View and manage past research jobs.
8. **Admin Panel** — Password-protected toggle for AI service availability.
9. **RAGAS Evaluation Dashboard** — Publicly viewable, manually triggered AI quality scoring dashboard.
10. **Rate Limiting** — Per-user request throttling to protect API budget.

## 2.3 User Classes and Characteristics

### 2.3.1 Standard User (Authenticated)

- Registers and logs into the system using email and password.
- Uploads PDF research documents and queries them via Q&A or Deep Research modes.
- Manages their own documents, chat sessions, and research jobs.
- Has no visibility into other users' data.
- Technical proficiency: General — no technical expertise required.

### 2.3.2 Admin User

- Accesses the `/admin` route protected by a separate admin password (not a user account).
- Can toggle the AI service on and off.
- Can view and manually trigger RAGAS evaluation runs on the evaluation dashboard.
- Technical proficiency: Basic administrative familiarity.

### 2.3.3 Unauthenticated Visitor

- May access the RAGAS evaluation dashboard at its public URL (read-only).
- May access the `/health` endpoint.
- Cannot access any document, chat, or research functionality.

## 2.4 Operating Environment

### 2.4.1 Development Environment

| Component     | Technology                              |
|---------------|-----------------------------------------|
| OS            | Windows / macOS / Linux                 |
| Frontend      | React 18 + Vite + Tailwind CSS + shadcn/ui |
| Backend       | Python 3.11+, FastAPI                   |
| Vector DB     | ChromaDB (local persistent)             |
| Database      | SQLite (local development)              |
| File Storage  | Local filesystem (`uploads/` folder)   |
| LLM Embeddings| **Gemini Embeddings API** (same as production — see C2 note below) |

> **⚠️ Embedding Model Constraint (C2):** The embedding model must be **identical** in both local and production environments. Dev uses `HuggingFace all-MiniLM-L6-v2` (384 dimensions) and prod uses `Gemini Embeddings` (768 dimensions) — these are incompatible vector spaces. Any chunk indexed locally with a different model cannot be searched in production. Therefore, **both environments shall use Gemini Embeddings API**. Gemini's embedding API has a generous free quota sufficient for development use. Local development requires a valid `GEMINI_API_KEY` in `.env`.

### 2.4.2 Production Environment

| Component     | Technology                              |
|---------------|-----------------------------------------|
| Frontend      | React 18 + Vite → Vercel (free tier)   |
| Backend       | FastAPI → Render (free tier)           |
| Eval Dashboard| Streamlit → Render (separate service)  |
| Vector DB     | ChromaDB Cloud (free tier)              |
| Database      | Supabase PostgreSQL (free tier)         |
| File Storage  | Supabase Storage (free tier)           |
| LLM           | Google Gemini 2.5 Flash API            |
| Embeddings    | Gemini Embeddings API                   |
| Keep-alive    | UptimeRobot pinging `/api/v1/health` every 5 minutes |

## 2.5 Design and Implementation Constraints

- The entire system shall be implementable and deployable at zero monthly cost.
- No paid cloud services, paid databases, or paid hosting shall be required.
- All configuration shall reside in `.env` files; no values shall be hardcoded in source code.
- The backend shall expose a single codebase that switches between local and production environments via the `ENVIRONMENT` environment variable.
- The system shall use a layered architecture: Route → Controller → Service → Repository/Database. Business logic shall not reside in route handlers.
- All database schemas shall follow third normal form (3NF) to avoid redundancy.
- The system shall not require Redis, Celery, or any worker queue infrastructure in v1. Asynchronous jobs shall be handled via FastAPI `BackgroundTasks`.

## 2.6 Assumptions and Dependencies

1. The development team has a Google AI Studio account and has generated a Gemini API key.
2. The Tavily API free tier provides sufficient web search credits for development and demonstration.
3. Supabase free tier provides a minimum of 500 MB PostgreSQL storage and 1 GB file storage.
4. ChromaDB Cloud free tier supports the expected volume of document embeddings.
5. Render free-tier services may cold-start after 15 minutes of inactivity; UptimeRobot pings shall prevent this for the main backend.
6. The user's browser supports modern JavaScript (ES2020+) and `fetch` API.
7. All PDF documents uploaded by users are text-extractable (not purely scanned images).
8. Email delivery for password reset shall use a transactional email service (Resend free tier or SMTP via a free Gmail app password).

---

---

# 3. System Features

This section specifies all functional requirements organized by feature module.

---

## 3.1 Authentication & Session Management

### 3.1.1 Overview

The system shall implement a fully custom JWT-based authentication system. Supabase Auth shall **not** be used for user identity management. Users shall be stored in a `users` table in the PostgreSQL database with bcrypt-hashed passwords. The system shall use a dual-token strategy: a short-lived **Access Token** and a long-lived **Refresh Token**.

### 3.1.2 User Registration

- **FR-AUTH-001**: The system shall provide a `POST /api/v1/auth/register` endpoint that accepts `email`, `password`, and `full_name`.
- **FR-AUTH-002**: The system shall validate that the `email` field conforms to RFC 5322 email format before processing.
- **FR-AUTH-003**: The system shall enforce the following password policy:
  - Minimum length: `[ENV: PASSWORD_MIN_LENGTH]` characters (default: 8)
  - Must contain at least one uppercase letter
  - Must contain at least one digit
  - Must contain at least one special character (`!@#$%^&*`)
- **FR-AUTH-004**: The system shall reject registration if the provided email already exists in the `users` table, returning HTTP 409 Conflict.
- **FR-AUTH-005**: The system shall hash the user's password using bcrypt with a work factor of `[ENV: BCRYPT_WORK_FACTOR]` (default: 12) before storing it. The plaintext password shall never be persisted.
- **FR-AUTH-006**: Upon successful registration, the system shall return HTTP 201 Created with the user's `id`, `email`, and `full_name`. It shall not return the password hash.
- **FR-AUTH-007**: The system shall sanitize all text inputs (trim whitespace, validate character sets) before processing to prevent injection.

### 3.1.3 User Login

- **FR-AUTH-008**: The system shall provide a `POST /api/v1/auth/login` endpoint accepting `email` and `password`.
- **FR-AUTH-009**: The system shall look up the user by email, then verify the submitted password against the stored bcrypt hash using a constant-time comparison function.
- **FR-AUTH-010**: On failed login (wrong email or password), the system shall return HTTP 401 Unauthorized with a generic message `"Invalid email or password"`. The response shall not distinguish between a non-existent email and a wrong password (to prevent user enumeration attacks).
- **FR-AUTH-011**: On successful login, the system shall generate and return:
  - An **Access Token** (JWT, signed with `JWT_SECRET_KEY` from env, expiry `[ENV: ACCESS_TOKEN_EXPIRE_MINUTES]` minutes, default 15)
  - A **Refresh Token** (opaque UUID, stored in the `refresh_tokens` table, expiry `[ENV: REFRESH_TOKEN_EXPIRE_DAYS]` days, default 7)
- **FR-AUTH-012**: The Refresh Token shall be set as an `httpOnly` cookie with the following attributes, governed by the `ENVIRONMENT` variable:
  - **Production** (`ENVIRONMENT=production`): `HttpOnly=true; Secure=true; SameSite=None`. `SameSite=None` is mandatory because the frontend (Vercel) and backend (Render) are on different domains — a cross-origin context. `SameSite=None` requires the `Secure` flag, which is guaranteed by HTTPS on both platforms. Using `SameSite=Strict` in this cross-origin setup would cause the browser to silently block the cookie on every refresh call, permanently breaking token rotation in production.
  - **Development** (`ENVIRONMENT=local`): `HttpOnly=true; Secure=false; SameSite=Lax`. `SameSite=None` requires `Secure=true`, which is unavailable on `localhost` HTTP. `SameSite=Lax` is a safe fallback for local development.
  - The cookie attributes shall be constructed dynamically in `auth_service.py` based on the `ENVIRONMENT` value. No cookie attribute shall be hardcoded.
  - The Refresh Token shall not be returned in the JSON response body under any circumstances.
- **FR-AUTH-013**: The Access Token shall be returned in the JSON response body and stored by the frontend in React component state (in-memory). It shall not be stored in `localStorage` or `sessionStorage`.
- **FR-AUTH-014**: The JWT Access Token payload shall contain: `user_id`, `email`, `iat` (issued at), `exp` (expiration).
- **FR-AUTH-015**: The system shall update `last_login` timestamp on the `users` table upon successful login.

### 3.1.4 Token Refresh

- **FR-AUTH-016**: The system shall provide a `POST /api/v1/auth/refresh` endpoint.
- **FR-AUTH-017**: The endpoint shall read the Refresh Token from the `httpOnly` cookie. No body parameter is required.
- **FR-AUTH-018**: The system shall validate the Refresh Token by:
  1. Looking it up in the `refresh_tokens` table.
  2. Verifying it has not expired (comparing `expires_at` to current UTC time).
  3. Verifying it has not been revoked (`is_revoked = false`).
- **FR-AUTH-019**: On valid Refresh Token, the system shall issue a new Access Token and return it in the JSON response body.
- **FR-AUTH-020**: The Refresh Token itself shall be rotated on each use: the old token record shall be marked `is_revoked = true`, and a new Refresh Token record shall be inserted, with a new `httpOnly` cookie set.
- **FR-AUTH-021**: On invalid or expired Refresh Token, the system shall return HTTP 401 Unauthorized, and the frontend shall redirect the user to the login page.

### 3.1.5 Logout

- **FR-AUTH-022**: The system shall provide a `POST /api/v1/auth/logout` endpoint (JWT required).
- **FR-AUTH-023**: On logout, the system shall mark the user's current Refresh Token as revoked in the `refresh_tokens` table.
- **FR-AUTH-024**: The server shall clear the `httpOnly` cookie by setting it with an expired `Max-Age`.
- **FR-AUTH-025**: The frontend shall clear the in-memory Access Token state on logout and redirect to the login page.

### 3.1.6 Password Reset

- **FR-AUTH-026**: The system shall provide a `POST /api/v1/auth/forgot-password` endpoint accepting `email`.
- **FR-AUTH-027**: If the email exists, the system shall generate a cryptographically secure random token, store its SHA-256 hash in the `password_reset_tokens` table with expiry `[ENV: PASSWORD_RESET_EXPIRE_MINUTES]` minutes (default: 30), and send the plaintext token to the user's email as part of a reset link.
- **FR-AUTH-028**: If the email does not exist, the system shall still return HTTP 200 OK with the message `"If this email is registered, you will receive a reset link."` This prevents email enumeration.
- **FR-AUTH-029**: The system shall provide a `POST /api/v1/auth/reset-password` endpoint accepting `token` and `new_password`.
- **FR-AUTH-030**: The system shall validate the token by hashing the submitted token and comparing it to the stored hash. The token must not be expired and must not have been previously used.
- **FR-AUTH-031**: On valid token, the system shall update the user's password hash, mark the reset token as `used = true`, and return HTTP 200 OK.
- **FR-AUTH-032**: The new password shall be subject to the same password policy as defined in FR-AUTH-003.

### 3.1.7 JWT Middleware

- **FR-AUTH-033**: All protected endpoints shall be guarded by a FastAPI dependency (`get_current_user`) that extracts the JWT from the `Authorization: Bearer <token>` header.
- **FR-AUTH-034**: The middleware shall verify the JWT signature using `JWT_SECRET_KEY`, validate the `exp` claim, and extract `user_id` from the payload.
- **FR-AUTH-035**: On invalid or expired JWT, the middleware shall return HTTP 401 Unauthorized. The frontend shall automatically call `POST /api/v1/auth/refresh` and retry the request once. If the refresh also fails, the user shall be redirected to login.

---

## 3.2 Document Management

### 3.2.1 Upload

- **FR-DOC-001**: The system shall provide a `POST /api/v1/documents/upload` endpoint (JWT required) accepting a PDF file via `multipart/form-data`.
- **FR-DOC-002**: The system shall reject files that exceed `[ENV: MAX_PDF_SIZE_MB]` megabytes with HTTP 413 Payload Too Large.
- **FR-DOC-003**: The system shall reject files whose MIME type is not `application/pdf` with HTTP 415 Unsupported Media Type.
- **FR-DOC-004**: Before accepting an upload, the system shall check if the user's document count has reached `[ENV: MAX_DOCUMENTS_PER_USER]` (default: 5).
- **FR-DOC-005**: If the document limit is reached, the system shall return HTTP 409 Conflict with a response body indicating the limit and a list of existing document IDs and filenames so the frontend can present a deletion prompt to the user.
- **FR-DOC-006**: On a successful upload, the system shall:
  1. Save the file to Supabase Storage (production) or the local `uploads/` folder (development) under a path structured as `{user_id}/{uuid}_{original_filename}`.
  2. Extract text from the PDF using `pdfplumber` or `PyMuPDF`.
  3. Split the extracted text into overlapping chunks using LangChain's `RecursiveCharacterTextSplitter` with `chunk_size=[ENV: CHUNK_SIZE]` (default: 1000) and `chunk_overlap=[ENV: CHUNK_OVERLAP]` (default: 200).
  4. Generate embeddings for each chunk using the configured embedding model.
  5. Insert all chunk vectors into the ChromaDB collection namespaced by `user_id` (collection name: `user_{user_id}`).
  6. Insert a record into the `documents` table with `id`, `user_id`, `filename`, `storage_path`, `chunk_count`, and `uploaded_at`.
  7. Return HTTP 201 Created with the new document record.
- **FR-DOC-007**: If any step in FR-DOC-006 fails after the file has been saved, the system shall perform a rollback: delete the file from storage and remove any partially inserted vectors from ChromaDB.
- **FR-DOC-008**: After a successful upload, the system shall automatically trigger suggested question generation (see Section 3.2.4) and return the questions in the upload response.

### 3.2.2 List Documents

- **FR-DOC-009**: The system shall provide a `GET /api/v1/documents` endpoint (JWT required) returning all documents belonging to the authenticated user, ordered by `uploaded_at` descending.
- **FR-DOC-010**: Each document record in the response shall include: `id`, `filename`, `chunk_count`, `uploaded_at`, and `storage_path` (for display purposes).
- **FR-DOC-011**: The response shall include a `document_count` and `document_limit` field so the frontend can display usage (e.g., "3 / 5 documents used").

### 3.2.3 Search Documents

- **FR-DOC-012**: The document list panel shall support client-side filtering by filename as the user types in a search input field.
- **FR-DOC-013**: The search shall be case-insensitive and shall match partial filename substrings.
- **FR-DOC-014**: No additional API endpoint is required for document search; filtering shall be performed on the already-fetched document list in the frontend.

### 3.2.4 Suggested Questions

- **FR-DOC-015**: The system shall provide a `GET /api/v1/documents/{document_id}/suggested-questions` endpoint (JWT required).
- **FR-DOC-016**: The system shall generate `[ENV: SUGGESTED_QUESTIONS_COUNT]` (default: 5) questions by sending the first retrieved chunks of the document to the LLM with a prompt instructing it to generate thoughtful, document-specific questions.
- **FR-DOC-017**: Generated questions shall be stored in a `suggested_questions` table linked to `document_id`, so repeated requests for the same document return cached results without re-calling the LLM.
- **FR-DOC-018**: Suggested questions shall be displayed in the frontend document panel as clickable chips. Clicking a chip shall pre-fill the chat input and submit it in the active chat session.

### 3.2.5 Delete Document

- **FR-DOC-019**: The system shall provide a `DELETE /api/v1/documents/{document_id}` endpoint (JWT required).
- **FR-DOC-020**: The system shall verify that the document with `document_id` belongs to the authenticated user before deletion. If the document belongs to another user, the system shall return HTTP 403 Forbidden.
- **FR-DOC-021**: On authorized deletion, the system shall:
  1. Delete the file from Supabase Storage (production) or local `uploads/` folder (development).
  2. Delete all chunk vectors from the ChromaDB collection for `user_id` where the chunk metadata field `document_id` matches.
  3. Delete the record from the `documents` table.
  4. Delete associated `suggested_questions` records for that document.
  5. Return HTTP 200 OK with a success message.
- **FR-DOC-022**: If any deletion step fails, the system shall log the error, continue executing all remaining deletion steps, and return HTTP 200 OK with a `warnings` array listing which steps failed (e.g., `{ "success": true, "warnings": ["Failed to delete vectors from ChromaDB: timeout"] }`). HTTP 207 Multi-Status is intentionally avoided — it requires a custom response schema and complex frontend handling that is disproportionate for a v1 student project. The 200 + warnings pattern conveys the same information with zero frontend complexity.

---

## 3.3 Q&A Chat — Mode 1

### 3.3.1 Chat Session Management

- **FR-CHAT-001**: The system shall support multiple simultaneous named chat sessions per user, presented in a left-sidebar layout consistent with the ChatGPT conversation pattern.
- **FR-CHAT-002**: The system shall provide a `POST /api/v1/chat/sessions` endpoint (JWT required) to create a new chat session, accepting an optional `title` field. If no title is provided, the system shall use the first user message as the session title (truncated to `[ENV: SESSION_TITLE_MAX_LENGTH]` characters, default: 50). Before creating a new session, the system shall verify the user's session count has not reached `[ENV: MAX_SESSIONS_PER_USER]` (default: 20). If the limit is reached, the system shall return HTTP 409 Conflict with a message indicating the limit and suggesting the user delete older sessions. **[COST GUARD — prevents unbounded Supabase storage growth from chat_messages]**
- **FR-CHAT-003**: The system shall provide a `GET /api/v1/chat/sessions` endpoint (JWT required) returning all chat sessions for the authenticated user ordered by `updated_at` descending.
- **FR-CHAT-004**: The system shall provide a `DELETE /api/v1/chat/sessions/{session_id}` endpoint (JWT required) that deletes the session and all its associated messages.
- **FR-CHAT-005**: The system shall provide a `PATCH /api/v1/chat/sessions/{session_id}` endpoint (JWT required) allowing the user to rename a session title.

### 3.3.2 Sending a Message

- **FR-CHAT-006**: The system shall provide a `POST /api/v1/chat/{session_id}/messages` endpoint (JWT required) accepting a `query` (string) field.
- **FR-CHAT-007**: The system shall validate that `query` is not empty and does not exceed `[ENV: MAX_CHAT_QUERY_LENGTH]` characters (default: 2000).
- **FR-CHAT-008**: Upon receiving a query, the system shall:
  1. Store the user's message in `chat_messages` with `role = 'user'`.
  2. Retrieve the last `[ENV: CHAT_CONTEXT_WINDOW]` messages from the session (default: 10) to build conversation context.
  3. Call the Q&A agent (see FR-CHAT-009 for agent architecture).
  4. Store the assistant's response in `chat_messages` with `role = 'assistant'`, including `sources` (JSONB) and `confidence` fields.
  5. Return the complete assistant message object.
- **FR-CHAT-009**: **Mode 1 Q&A Agent Architecture.** The Q&A agent shall be implemented as a **LangChain tool-calling agent** (using `create_tool_calling_agent` or equivalent) with two registered tools: `rag_search` and `web_search`. The agent decision logic shall follow this explicit rule:
  - **Step 1 — Always attempt RAG first**: The agent shall call `rag_search` on every query. This returns the top `[ENV: RAG_TOP_K]` chunks and the top cosine similarity score.
  - **Step 2 — Conditionally use Web Search**: The agent shall invoke `web_search` (Tavily) **only if** one or more of the following conditions is true:
    - The user has zero documents uploaded (ChromaDB collection is empty for this user).
    - The top RAG cosine score is below `[ENV: WEB_SEARCH_FALLBACK_THRESHOLD]` (default: 0.50), indicating the documents do not contain relevant information for this query.
  - **Step 3 — Synthesize**: The agent calls the LLM once with the retrieved context (RAG chunks and/or web results) to generate the final answer.
  - This architecture ensures web search is only called when necessary, protecting the Tavily API quota. **[COST GUARD]**
  - The agent shall be constructed once at application startup and reused across requests (stateless tool functions, stateful conversation injected per call).
- **FR-CHAT-010**: The system shall retrieve the top `[ENV: RAG_TOP_K]` (default: 5) most semantically similar chunks from the user's ChromaDB collection for RAG-based queries.

### 3.3.3 Citation Display

- **FR-CHAT-011**: Every assistant response shall include a `sources` object with two distinct sections:
  - `document_sources`: A list of `{ filename, page_number, chunk_preview, cosine_score }` objects from RAG results.
  - `web_sources`: A list of `{ url, title, snippet }` objects from Tavily web search results.
- **FR-CHAT-012**: If only RAG was used, `web_sources` shall be an empty array. If only web search was used, `document_sources` shall be an empty array.
- **FR-CHAT-013**: The frontend shall render document citations and web citations in visually distinct sections below each assistant message, clearly labelled "From Your Documents" and "From the Web".

### 3.3.4 Confidence Indicator

- **FR-CHAT-014**: Each assistant response shall include a `confidence` field with value `"high"`, `"medium"`, or `"low"` calculated as follows:
  ```
  score = top_chunk_cosine_similarity (from ChromaDB retrieval)
  High   → score >= CONFIDENCE_HIGH_THRESHOLD   [ENV: CONFIDENCE_HIGH_THRESHOLD, default: 0.75]
  Medium → score >= CONFIDENCE_MEDIUM_THRESHOLD [ENV: CONFIDENCE_MEDIUM_THRESHOLD, default: 0.50]
  Low    → score < CONFIDENCE_MEDIUM_THRESHOLD
  ```
- **FR-CHAT-015**: If no document sources were used (pure web search), confidence shall default to `"low"`.
- **FR-CHAT-016**: The frontend shall render the confidence level as a filled dot indicator (e.g., ●●●●● for High in green, ●●●○○ for Medium in amber, ●●○○○ for Low in red) adjacent to the assistant message.

### 3.3.5 Chat History

- **FR-CHAT-017**: The system shall provide a `GET /api/v1/chat/{session_id}/messages` endpoint (JWT required) returning messages for that session.
- **FR-CHAT-018**: The endpoint shall support pagination via `limit` and `offset` query parameters with a default page size of `[ENV: CHAT_HISTORY_LIMIT]` messages (default: 10 most recent).
- **FR-CHAT-019**: Messages shall be returned in ascending chronological order (oldest first) so the frontend can render them as a conversation thread.

### 3.3.6 Message Deletion

- **FR-CHAT-020**: The system shall provide a `DELETE /api/v1/chat/messages/{message_id}` endpoint (JWT required).
- **FR-CHAT-021**: The system shall verify that the message belongs to a session owned by the authenticated user before deleting.
- **FR-CHAT-022**: The frontend shall provide a per-message delete option (e.g., a hover-reveal trash icon) for messages the user has sent.

### 3.3.7 Tool Use Indicator

- **FR-CHAT-023**: Each assistant response shall include a `tools_used` array (e.g., `["rag_search", "web_search"]`) so the frontend can display a small tool badge indicating which tools the agent invoked for that response.

---

## 3.4 Deep Research — Mode 2

### 3.4.1 Initiating a Research Job

- **FR-RES-001**: The system shall provide a `POST /api/v1/research` endpoint (JWT required) accepting a `topic` string.
- **FR-RES-002**: The `topic` field shall not exceed `[ENV: MAX_RESEARCH_TOPIC_LENGTH]` characters (default: 300) and shall not be empty. This limit is a deliberate cost-control measure to reduce LLM token consumption.
- **FR-RES-003**: Before creating a new job, the system shall check if the user already has a research job in any active state (`queued`, `planning`, `researching`, `reflecting`, `synthesizing`, `writing`). If so, the system shall return HTTP 409 Conflict with the message `"A research job is already in progress. Please wait for it to complete or cancel it."` **[COST GUARD]**
- **FR-RES-004**: On acceptance, the system shall:
  1. Insert a new record into `research_jobs` with `status = 'queued'`.
  2. Schedule `run_research_agent(job_id, topic, user_id)` as a FastAPI `BackgroundTask`.
  3. Return HTTP 202 Accepted with `{ "job_id": "<uuid>", "status": "queued" }`.
- **FR-RES-005**: The endpoint shall return HTTP 202 immediately — it shall never hold the HTTP connection open while the research runs.

### 3.4.2 Job Status Polling

- **FR-RES-006**: The system shall provide a `GET /api/v1/research/{job_id}/status` endpoint (JWT required).
- **FR-RES-007**: The system shall verify the job belongs to the authenticated user.
- **FR-RES-008**: The response shall include: `job_id`, `status`, `topic`, `progress` (JSONB — see below), `confidence` (when complete), `created_at`, `updated_at`. The `progress` field shall contain `{ "current_step": "<description>", "steps_done": <int>, "total_steps": <int>, "current_node": "<node_name>" }`. Example during Researcher node: `{ "current_step": "Researching sub-question 3 of 5", "steps_done": 2, "total_steps": 5, "current_node": "researching" }`.
- **FR-RES-009**: The valid status values shall be: `queued` → `planning` → `researching` → `reflecting` → `synthesizing` → `writing` → `complete` | `failed`.
- **FR-RES-010**: The frontend shall poll this endpoint every `[ENV: REACT_APP_RESEARCH_POLL_INTERVAL_MS]` milliseconds (default: 3000) using a `setInterval`. Polling shall stop when status is `complete` or `failed`.
- **FR-RES-011**: The frontend shall render a live progress stepper showing the current active status step with a loading animation and completed steps in a "done" visual state. Within the `researching` node, the stepper shall also display the sub-question progress text from the `progress.current_step` field (e.g., "Researching sub-question 3 of 5") to give the user granular progress visibility during the longest-running node.

### 3.4.3 The Research Agent (LangGraph State Machine)

- **FR-RES-012**: The research agent shall be implemented as a LangGraph state machine with the following `AgentState` fields:
  - `user_id` (str)
  - `job_id` (str)
  - `topic` (str)
  - `sub_questions` (list[str]) — generated by Planner
  - `research_findings` (dict[str, str]) — keyed by sub_question
  - `reflection_gaps` (list[str]) — identified by Reflector
  - `iteration_count` (int) — initialized to 0, max `[ENV: MAX_REFLECTION_ITERATIONS]` (default: 3)
  - `chunk_scores` (list[float]) — cosine scores from all RAG calls
  - `web_used` (bool) — set to True if any web search tool was invoked
  - `final_synthesis` (str)
  - `report_path` (str)

- **FR-RES-013**: The state machine shall contain the following nodes:

  **Planner Node:**
  - Receives the `topic`.
  - Calls the LLM with a structured prompt to decompose the topic into `[ENV: MAX_SUB_QUESTIONS]` (default: 5) distinct sub-questions.
  - Populates `sub_questions` in AgentState.
  - Calls `update_job_status(job_id, 'planning')`.

  **Researcher Node:**
  - Iterates over each sub-question in `sub_questions`.
  - For each sub-question, calls the RAG Search tool and optionally the Web Search tool (see M7 fix: web search is called only if RAG cosine score is below `[ENV: WEB_SEARCH_FALLBACK_THRESHOLD]`).
  - Before processing each sub-question, updates the `research_jobs.progress` column: `{ "current_step": "Researching sub-question <i> of <total>", "steps_done": <i-1>, "total_steps": <total>, "current_node": "researching" }`.
  - Appends results to `research_findings[sub_question]`.
  - Accumulates cosine scores into `chunk_scores`. Sets `web_used = True` if web search was used.
  - Calls `update_job_status(job_id, 'researching')`.

  **Reflector Node:**
  - Calls the LLM with all `research_findings` and the original `topic`.
  - The LLM evaluates whether the compiled research has coverage gaps.
  - Populates `reflection_gaps` list.
  - Increments `iteration_count`.
  - Calls `update_job_status(job_id, 'reflecting')`.

  **Conditional Edge (after Reflector):**
  - If `len(reflection_gaps) > 0 AND iteration_count < MAX_REFLECTION_ITERATIONS`: → Gap Filler Node
  - Otherwise: → Synthesizer Node

  > **Web Search Decision Logic (M7):** Both the Mode 1 Q&A agent and the Mode 2 Researcher Node shall use the same web search trigger rule: web search (`tavily.search()`) is invoked **only if** the top RAG cosine score for a given query is below `[ENV: WEB_SEARCH_FALLBACK_THRESHOLD]` (default: 0.50), or if the user's ChromaDB collection is empty. This rule must be implemented as a shared utility function `should_use_web_search(top_score: float, collection_empty: bool) -> bool` in `rag/retriever.py` and called identically by both the Q&A agent and the Researcher Node. Web search is never called unconditionally. This is a budget-protection constraint. **[COST GUARD]**

  **Gap Filler Node:**
  - For each identified gap, generates a targeted sub-question and calls the Researcher tools.
  - Appends new findings to `research_findings`.
  - Returns to Reflector Node.

  **Synthesizer Node:**
  - Calls the LLM with all `research_findings` to produce a coherent `final_synthesis`.
  - Calls `update_job_status(job_id, 'synthesizing')`.

  **Writer Node:**
  - Calls `docx_writer.generate_report()` with `final_synthesis`, `research_findings`, `sub_questions`, `reflection_gaps`, `chunk_scores`, and `web_used`.
  - Saves the DOCX to Supabase Storage (production) or local `reports/` folder (development) under `{user_id}/reports/{job_id}.docx`.
  - Updates `research_jobs` with `status = 'complete'`, `report_path`, and computed `confidence`.
  - Calls `update_job_status(job_id, 'complete')`.

  **Error Handling:**
  - Any unhandled exception in any node shall be caught, logged, and result in `update_job_status(job_id, 'failed')`.

### 3.4.4 Confidence Score for Research Reports

- **FR-RES-014**: The aggregate confidence score for a research report shall be computed as:
  ```
  base_score  = mean(chunk_scores)   [mean of all cosine similarity scores across all RAG calls]
  web_penalty = WEB_SEARCH_PENALTY if web_used else 0.0
               [ENV: WEB_SEARCH_PENALTY, default: 0.10]
  final_score = base_score - web_penalty

  High   → final_score >= RESEARCH_CONFIDENCE_HIGH   [ENV: RESEARCH_CONFIDENCE_HIGH, default: 0.70]
  Medium → final_score >= RESEARCH_CONFIDENCE_MEDIUM [ENV: RESEARCH_CONFIDENCE_MEDIUM, default: 0.45]
  Low    → final_score < RESEARCH_CONFIDENCE_MEDIUM
  ```
- **FR-RES-015**: The confidence label and score shall be stored in the `research_jobs` table and displayed in the frontend before and after the download button.

### 3.4.5 Report Generation (DOCX)

- **FR-RES-016**: The generated DOCX report shall contain the following sections in order:
  1. **Title Page** — Report title (derived from topic), generation date, confidence label + score.
  2. **Executive Summary** — A 2–3 paragraph synthesis of key findings.
  3. **Research Sub-Questions** — Numbered list of all sub-questions investigated.
  4. **Findings per Sub-Question** — One section per sub-question with the researched findings and inline citations (filename/page or URL).
  5. **Coverage Gaps Analysis** — List of identified gaps and whether they were resolved.
  6. **Final Synthesis** — The complete synthesized narrative.
  7. **References** — Numbered list of all cited documents and web sources.
- **FR-RES-017**: The report shall be generated using `python-docx`. No paid Word API shall be used.
- **FR-RES-018**: The DOCX file shall be named `docmind_report_{job_id[:8]}.docx` to avoid user-facing UUIDs.

### 3.4.6 Report Download

- **FR-RES-019**: The system shall provide a `GET /api/v1/research/{job_id}/download` endpoint (JWT required).
- **FR-RES-020**: The system shall verify job ownership and that the job status is `complete` before serving the file.
- **FR-RES-021**: The response shall set `Content-Disposition: attachment; filename="docmind_report_{job_id[:8]}.docx"` and `Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document`.

### 3.4.7 Cancel Research Job

- **FR-RES-022**: The system shall provide a `DELETE /api/v1/research/{job_id}` endpoint (JWT required) for job cancellation.
- **FR-RES-023**: If the job is in any active state, the system shall set `status = 'cancelled'` in the database.
- **FR-RES-024**: Since FastAPI `BackgroundTasks` does not natively support cancellation, the running agent task shall check a `is_cancelled` flag at the beginning of each node by querying the job status. If `cancelled`, the node shall return immediately without further processing. **[Implementation Note: the agent reads `research_jobs.status` at the start of each node; if it is `cancelled`, it exits early.]**

### 3.4.8 Research Job History

- **FR-RES-025**: The system shall provide a `GET /api/v1/research/history` endpoint (JWT required) returning the user's past research jobs, limited to `[ENV: RESEARCH_JOB_HISTORY_LIMIT]` most recent records (default: 3), ordered by `created_at` descending.
- **FR-RES-026**: Each job record in the response shall include: `job_id`, `topic`, `status`, `confidence`, `created_at`, `report_path` (null if not complete).
- **FR-RES-027**: The frontend shall render a "Past Research" panel listing these jobs. Completed jobs shall display a download button.
- **FR-RES-028**: Research job records and their associated DOCX files shall be automatically deleted after `[ENV: RESEARCH_JOB_RETENTION_DAYS]` days (default: 7). **[Implementation Note: cleanup shall be triggered in the FastAPI `startup` event handler (`@app.on_event("startup")`), not on the `/health` endpoint. The startup handler shall query for all `research_jobs` records where `expires_at < NOW()` and delete them along with their files. Running cleanup on `/health` is an anti-pattern as health endpoints must remain fast and lightweight.]**

- **FR-RES-029**: **[Stale Job Recovery]** On application startup, the system shall query for any `research_jobs` record in a non-terminal state (`queued`, `planning`, `researching`, `reflecting`, `synthesizing`, `writing`) where `updated_at` is older than `[ENV: STALE_JOB_TIMEOUT_MINUTES]` (default: 20) minutes. Each such record shall be automatically updated to `status = 'failed'` with `error_message = 'Job was interrupted by a server restart.'` This requirement exists because Render may restart the backend service (cold start, deploy, crash), which kills all running `BackgroundTasks`. Without this cleanup, FR-RES-003's active-job check would permanently block the user from starting a new research job after any server interruption.

---

## 3.5 Admin Panel

- **FR-ADMIN-001**: The system shall provide a `/admin` route in the frontend, accessible to anyone who knows the URL, but actionable only with the admin password.
- **FR-ADMIN-002**: The admin panel shall display the current AI service status (ON/OFF) fetched from `GET /api/v1/admin/status`.
- **FR-ADMIN-003**: `GET /api/v1/admin/status` shall not require authentication. It returns `{ "ai_enabled": true/false }`.
- **FR-ADMIN-004**: `POST /api/v1/admin/toggle` shall require the `ADMIN_PASSWORD` env variable to be passed in the `X-Admin-Password` request header. If the password does not match, the system returns HTTP 403 Forbidden.
- **FR-ADMIN-005**: The AI service toggle state shall be stored in the `app_settings` table with `key = 'ai_enabled'` and `value = 'true'` or `'false'`. This persists across server restarts.
- **FR-ADMIN-006**: When `ai_enabled = false`, all endpoints that invoke the LLM or the agent (`/chat`, `/research`, `/documents/suggested-questions`) shall return HTTP 503 Service Unavailable with message `"AI service is temporarily unavailable."` before reaching the service layer.
- **FR-ADMIN-007**: The admin panel (`/admin` route) shall display a clearly labelled link to the RAGAS Evaluation Dashboard (URL sourced from `[ENV: REACT_APP_EVAL_DASHBOARD_URL]`). The link shall open the dashboard in a new browser tab. The admin panel shall **not** implement a "Run Evaluation" button that attempts to trigger the Streamlit service programmatically — Streamlit does not expose a REST API and such a trigger mechanism is undefined and unimplementable. The RAGAS evaluation shall be triggered exclusively from within the Streamlit dashboard itself (after admin password entry), as specified in FR-EVAL-003.

---

## 3.6 RAGAS Evaluation Dashboard

- **FR-EVAL-001**: The RAGAS evaluation dashboard shall be a separate Streamlit application deployed as a second free-tier service on Render.
- **FR-EVAL-002**: The dashboard shall be publicly accessible (no login required) in read-only mode.
- **FR-EVAL-003**: CRUD operations (triggering a new evaluation run) shall be accessible only after entering the `ADMIN_PASSWORD` in a password input field within the Streamlit app.
- **FR-EVAL-004**: The dashboard shall evaluate the following 3 RAGAS metrics only (no ground truth required):
  - **Faithfulness** — measures whether the answer is grounded in the retrieved context.
  - **Answer Relevancy** — measures how relevant the answer is to the question.
  - **Context Precision** — measures whether the retrieved context is useful.
- **FR-EVAL-005**: The evaluation shall be run against a hardcoded test dataset of `[ENV: EVAL_DATASET_SIZE]` (default: 10) Q&A pairs stored in `eval_dashboard/test_dataset.py`.
- **FR-EVAL-006**: Each metric result shall be displayed with a pass/fail colour code: green if score ≥ `[ENV: EVAL_PASS_THRESHOLD]` (default: 0.70), red if below.
- **FR-EVAL-007**: The dashboard shall support a "Live Test" input where the admin (after entering `ADMIN_PASSWORD`) can type any question and see its 3 metric scores computed in real time. The Live Test feature shall call the DocMind AI backend's Q&A endpoint to generate an answer, then run RAGAS metrics against it. The backend URL shall be configured via `[ENV: EVAL_BACKEND_URL]` (e.g., `https://docmind.onrender.com`) in the `eval_dashboard/.env` file. The `eval_dashboard/` folder shall have its own `.env` and `.env.example` files (see Appendix B and Appendix A eval section).
- **FR-EVAL-008**: All evaluation results shall be stored in the `eval_results` table in Supabase.
- **FR-EVAL-009**: The dashboard shall display a historical chart of average metric scores across past evaluation runs.

---

---

# 4. External Interface Requirements

## 4.1 User Interfaces

### 4.1.1 Design Language

The user interface shall be built with **Vite + React 18 + Tailwind CSS + shadcn/ui**. The design system shall conform to the following principles:

- **Component Library**: All UI primitives (buttons, inputs, dialogs, cards, dropdowns, toasts, skeleton loaders, badges) shall use **shadcn/ui** components. shadcn/ui components are copied directly into the project under `src/components/ui/` and are fully customisable — do not wrap or re-implement primitives that shadcn already provides.
- **Styling**: All styling shall use **Tailwind CSS utility classes** exclusively. No custom CSS files shall be written except for `src/styles/globals.css` which contains only: CSS variable definitions (for the colour palette and shadcn/ui theme tokens), the `@tailwind` directives, and any global resets. Component-level `style={}` props and inline styles shall not be used.
- **Color Palette**: Configured via Tailwind's `tailwind.config.js` and shadcn/ui's CSS variables in `globals.css`. The palette shall follow a **clean, minimal, document-centric** aesthetic:
  - Background: `neutral-50` / `white`
  - Surface (cards, panels): `white` with `border border-neutral-200 shadow-sm rounded-xl`
  - Primary accent: muted indigo — configured as `--primary` in the shadcn/ui theme token. Suggested value: `#5B6CF6`.
  - Muted text: `text-neutral-500`
  - Destructive: shadcn/ui default red token
  - No aggressive background fills. Panels shall feel light and airy.
- **Typography**: Configured via Tailwind. Font family: **`DM Sans`** or **`Plus Jakarta Sans`** — imported from Google Fonts in `index.html`. Set as `font-sans` in `tailwind.config.js`. Body copy: `text-sm` / `text-base`. Headings: `font-semibold`. Avoid `font-bold` on body text.
- **Card Components**: Use shadcn/ui `<Card>`, `<CardHeader>`, `<CardContent>` primitives. Document and research job cards shall display: filename, file size (`file_size_kb` formatted as MB), chunk count, and upload date. Cards shall use `rounded-xl border border-neutral-200 shadow-sm`.
- **Sidebar**: Built with Tailwind flex/grid. Left sidebar for navigation (Documents, Chat Sessions, Research Jobs) with icon + label. Active state: `bg-primary/10 text-primary font-medium`. Icons: **`lucide-react`** (already a shadcn/ui dependency — no additional icon library required).
- **Spacing**: Use Tailwind spacing scale consistently. Panel padding: `p-4` or `p-6`. Gaps between cards: `gap-3` or `gap-4`.
- **Loading States**: Use shadcn/ui `<Skeleton />` component for all loading placeholders — document list, chat sessions, chat history, research job history.
- **Toasts / Notifications**: Use shadcn/ui `<Sonner />` (or `useToast`) for all non-blocking notifications.
- **Dialogs / Confirmations**: All destructive-action confirmation dialogs shall use shadcn/ui `<AlertDialog>`.
- **Forms**: All form inputs shall use shadcn/ui `<Input>`, `<Label>`, `<Button>`. Form state and validation shall use **React Hook Form** + **Zod**. No custom form state management.
- **Mobile Responsive**: The layout shall collapse to a hamburger-menu-based drawer navigation (`shadcn/ui <Sheet>`) on screens narrower than `md` (768px Tailwind breakpoint).

### 4.1.2 Pages and Layouts

| Page / Route     | Description                                                      |
|------------------|------------------------------------------------------------------|
| `/login`         | Login form (email + password) + link to signup + forgot password |
| `/signup`        | Registration form (full name + email + password + confirm)       |
| `/forgot-password` | Email input for reset link                                     |
| `/reset-password?token=...` | New password + confirm password form               |
| `/dashboard`     | Main app layout: sidebar + document panel + chat window          |
| `/research`      | Research job input + progress stepper + past research jobs panel |
| `/admin`         | AI service toggle + RAGAS dashboard link                         |

### 4.1.3 Dashboard Layout

The main `/dashboard` page shall be divided into three panels:

- **Left Panel (Sidebar)** — Chat session list (ChatGPT-style), "New Chat" button, navigation links.
- **Center Panel** — Active chat window: message thread, input bar, tool badge, confidence indicator, citations.
- **Right Panel (Documents)** — Document upload drop zone, document list with search, per-document suggested question chips, document delete button.

### 4.1.4 Accessibility

- All interactive elements shall have `aria-label` attributes.
- Color-only information shall have a text fallback.
- Font size shall not be smaller than 14px for body copy.

## 4.2 Hardware Interfaces

The system has no direct hardware interface requirements. All hardware interaction (webcam, sensors) is out of scope for DocMind AI.

## 4.3 Software Interfaces

| External Service       | Interface Type         | Purpose                                    | Auth Method           |
|------------------------|------------------------|--------------------------------------------|-----------------------|
| Google Gemini API      | REST API (HTTPS)       | LLM inference + embeddings                 | API Key in header     |
| Tavily Search API      | REST API (HTTPS)       | Live web search during agent research      | API Key in header     |
| Supabase PostgreSQL    | `supabase-py` client   | Primary relational database                | Service Role Key      |
| Supabase Storage       | `supabase-py` client   | PDF file storage                           | Service Role Key      |
| ChromaDB Cloud         | `chromadb` Python SDK  | Vector storage and similarity search       | API Key               |
| Resend / SMTP          | REST API / SMTP        | Transactional email for password reset     | API Key / App Password|

## 4.4 Communication Interfaces

- All communication between frontend and backend shall use HTTPS in production.
- In development, HTTP on `localhost` is acceptable.
- All API requests shall use `Content-Type: application/json` unless file upload (`multipart/form-data`).
- The frontend shall set `Authorization: Bearer <access_token>` on all protected API calls.
- CORS origins shall be configured via `[ENV: CORS_ORIGINS]` as a comma-separated list of allowed origins.
- The `httpOnly` cookie containing the Refresh Token shall use `SameSite=None; Secure=true` in production (cross-origin: Vercel frontend → Render backend) and `SameSite=Lax; Secure=false` in development. See FR-AUTH-012 for the full environment-aware cookie specification.

---

---

# 5. Non-Functional Requirements

## 5.1 Performance Requirements

- **NFR-PERF-001**: The system shall respond to all non-AI endpoints (auth, document list, chat history) within 800ms under normal load.
- **NFR-PERF-002**: The RAG retrieval step (ChromaDB semantic search for top-K chunks) shall complete within 2 seconds.
- **NFR-PERF-003**: A single Q&A agent response (RAG + LLM inference) shall complete within 15 seconds.
- **NFR-PERF-004**: The research agent shall complete a full job within 3 minutes under typical conditions (5 sub-questions, no excessive gap-filling iterations).
- **NFR-PERF-005**: API calls to the LLM shall be minimized. The agent shall not make redundant LLM calls. Each node shall call the LLM exactly once per execution.
- **NFR-PERF-006**: Pagination shall be implemented on all list endpoints that may return more than 20 items (chat messages, document list). Default page size shall be controlled via `[ENV: DEFAULT_PAGE_SIZE]` (default: 20).
- **NFR-PERF-007**: Vite's production build (`vite build`) shall be used for all deployments. Vite performs automatic minification (via esbuild) and code splitting at dynamic import boundaries — no additional Webpack or Rollup configuration is required. Lazy loading shall be applied to the Research and Admin pages as specified in Section 6.3.4.
- **NFR-PERF-008**: N+1 database query patterns shall be explicitly avoided. All related data needed for a response shall be fetched in a single query using SQL JOINs or batch queries.
- **NFR-PERF-009**: Image assets in the frontend shall be optimized and served in `WebP` format where possible.
- **NFR-PERF-010**: **[FUTURE SCOPE]** The system can support response caching using an in-memory or Redis cache layer in a future version for performance improvement on repeated queries.

## 5.2 Reliability Requirements

- **NFR-REL-001**: The backend service shall be kept alive on Render's free tier by UptimeRobot pinging `GET /api/v1/health` every **5 minutes** (not 14 minutes — 5 minutes is the safest interval within UptimeRobot's free tier to guarantee the 15-minute Render sleep threshold is never crossed).
- **NFR-REL-002**: Research jobs in background tasks shall not be lost on server restart. Job state is persisted in the `research_jobs` table at each node transition.
- **NFR-REL-003**: If a research job is interrupted by a server restart (status stuck in an active state), the frontend shall display a "Job interrupted" message and allow the user to dismiss it.
- **NFR-REL-004**: All database writes in the document upload pipeline shall be atomic where possible. Partial failures shall trigger cleanup as specified in FR-DOC-007.
- **NFR-REL-005**: The RAGAS evaluation service on Render shall also be kept alive by UptimeRobot if required.
- **NFR-REL-006**: **[C4 — Reverse Proxy Real-IP Fix]** The FastAPI backend shall be started with Uvicorn's `--proxy-headers` flag (or the equivalent `ProxyHeadersMiddleware` added in `main.py`). Render deploys all services behind a load balancer that forwards the real client IP in the `X-Forwarded-For` header. Without trusting this header, all incoming requests appear to originate from the same proxy IP address, causing `slowapi` rate limiting to treat all users as a single entity — either blocking all users simultaneously or applying no individual throttling. The Uvicorn startup command in production shall be:
  ```
  uvicorn main:app --host 0.0.0.0 --port 10000 --proxy-headers --forwarded-allow-ips="*"
  ```
  This must be set in the Render service's Start Command field, not hardcoded in source code.

## 5.3 Usability Requirements

- **NFR-USE-001**: All forms shall display inline validation errors (not page-level toasts alone) next to the relevant field.
- **NFR-USE-002**: The document upload component shall support drag-and-drop in addition to click-to-browse.
- **NFR-USE-003**: All destructive actions (document delete, chat session delete, job cancel) shall require a confirmation dialog before execution.
- **NFR-USE-004**: Loading skeletons shall be shown for document list, chat sessions, chat history, and research job history panels while data is being fetched.
- **NFR-USE-005**: Error messages from the API shall be surfaced to the user as non-blocking toast notifications with sufficient detail to understand what went wrong (e.g., "File too large. Maximum allowed size is 10 MB").
- **NFR-USE-006**: The application shall be fully usable on screen widths from 375px (mobile) to 1920px (desktop).

## 5.4 Maintainability Requirements

- **NFR-MAIN-001**: All Python functions shall be named in `snake_case`, all React components in `PascalCase`, and all constants in `UPPER_SNAKE_CASE`.
- **NFR-MAIN-002**: Functions shall not exceed 50 lines. Logic exceeding this shall be extracted into helper functions.
- **NFR-MAIN-003**: No magic numbers or string literals shall appear in business logic. All such values shall be sourced from environment variables or named constants.
- **NFR-MAIN-004**: The backend shall follow the layered pattern: `router → controller → service → repository`. No database queries shall appear in routers or controllers.
- **NFR-MAIN-005**: All agent prompts shall be stored in `backend/agent/prompts.py` as named string constants, not inline within node function bodies.
- **NFR-MAIN-006**: The codebase shall have a predictable, documented folder structure (see Appendix B) that an AI coding assistant or new developer can navigate without explanation.
- **NFR-MAIN-007**: A `README.md` at the project root shall document local setup steps, environment variable descriptions, and the deployment process.

## 5.5 Scalability Requirements

- **NFR-SCALE-001**: The backend shall be stateless — all per-request state shall come from the database or the JWT token. No in-process session state shall be maintained.
- **NFR-SCALE-002**: ChromaDB collections shall be namespaced by `user_id`, ensuring that future horizontal scaling does not require re-partitioning.
- **NFR-SCALE-003**: **[FUTURE SCOPE]** The system is architecturally ready for a dedicated task queue (Celery + Redis / ARQ) to replace FastAPI `BackgroundTasks` for higher-throughput asynchronous research jobs.
- **NFR-SCALE-004**: **[FUTURE SCOPE]** CDN integration for static asset delivery can be added in a future version for global scalability.

---

---

# 6. System Architecture

## 6.1 Architecture Overview

DocMind AI follows a **three-tier, layered architecture** comprising a React frontend, a FastAPI backend, and a set of backing services (Supabase, ChromaDB, Gemini API, Tavily). The backend strictly enforces the layered pattern to maintain separation of concerns.

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT (Browser)                          │
│          React SPA — deployed on Vercel                      │
│   Auth Context │ API Client (axios) │ Component Tree        │
└───────────────────────────┬─────────────────────────────────┘
                            │  HTTPS / REST (JWT in header)
                            │  httpOnly Cookie (refresh token)
┌───────────────────────────▼─────────────────────────────────┐
│                   BACKEND (FastAPI)                          │
│                 deployed on Render                           │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  API Layer (Routers) — /api/v1/...                  │    │
│  │  auth/ │ documents/ │ chat/ │ research/ │ admin/    │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │ (calls)                           │
│  ┌──────────────────────▼──────────────────────────────┐    │
│  │  Controller Layer — validates input, maps to service │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │ (calls)                           │
│  ┌──────────────────────▼──────────────────────────────┐    │
│  │  Service Layer — business logic                      │    │
│  │  auth_service │ doc_service │ chat_service           │    │
│  │  research_service │ admin_service                    │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │ (calls)                           │
│  ┌──────────────────────▼──────────────────────────────┐    │
│  │  Repository Layer — database queries only            │    │
│  │  supabase_client (prod) │ sqlite_client (local)     │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │                                   │
│  ┌──────────────────────▼──────────────────────────────┐    │
│  │  Agent Layer (LangGraph)                             │    │
│  │  graph.py │ tools.py │ prompts.py                   │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │                                   │
│  ┌──────────────────────▼──────────────────────────────┐    │
│  │  RAG Layer                                           │    │
│  │  indexer.py │ retriever.py                          │    │
│  └─────────────────────────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   ┌────▼────┐       ┌──────▼──────┐    ┌──────▼──────┐
   │Supabase │       │ ChromaDB    │    │  Gemini API │
   │Postgres │       │   Cloud     │    │  + Tavily   │
   │+ Storage│       │(Vector DB)  │    │             │
   └─────────┘       └─────────────┘    └─────────────┘
```

## 6.2 Backend Architecture

### 6.2.1 Framework

FastAPI (Python 3.11+) shall be used as the backend framework for its native async support, automatic OpenAPI documentation, and Pydantic model validation.

### 6.2.2 Layered Architecture Rules

- **Routers** (`/api/v1/...`): Define HTTP routes, apply middleware dependencies (JWT validation, rate limiting). No business logic.
- **Controllers** (within the router file): Parse and validate incoming request bodies using Pydantic models. Call the appropriate service function. Return HTTP responses.
- **Services** (`/services/`): Contain all business logic. Coordinate between repositories, the agent, and external APIs. Services are not aware of HTTP.
- **Repositories** (`/database/repositories/`): Contain all database queries. Accept and return domain model objects. No business logic.
- **Agent** (`/agent/`): LangGraph graph definition, tools, and prompts. Called by `research_service`.
- **RAG** (`/rag/`): Chunk indexing and vector retrieval logic. Called by `doc_service` and agent tools.

> **⚠️ Route Registration Order (C3 — Implementation Requirement):** Within `research.py`, the route `GET /api/v1/research/history` **must be registered before** `GET /api/v1/research/{job_id}/status`. FastAPI matches routes in registration order. If `/{job_id}/status` is registered first, any request to `/history` will have `"history"` captured as the `job_id` path parameter, returning 404 or wrong data. The same principle applies to any future static path segment that could conflict with a `{param}` route. The research router shall declare routes in this order:
> 1. `POST /api/v1/research` — start job
> 2. `GET /api/v1/research/history` — list history (**must be before `/{job_id}` routes**)
> 3. `GET /api/v1/research/{job_id}/status` — poll status
> 4. `GET /api/v1/research/{job_id}/download` — download report
> 5. `DELETE /api/v1/research/{job_id}` — cancel/delete

### 6.2.3 Environment Switching

- A `config.py` module shall read `ENVIRONMENT` from the environment. If `ENVIRONMENT=local`, the system shall use SQLite for the database and local filesystem for storage. If `ENVIRONMENT=production`, it shall use Supabase PostgreSQL and Supabase Storage.
- This switching logic shall be implemented once in `config.py` and nowhere else.

## 6.3 Frontend Architecture

### 6.3.1 Component-Based Architecture

The React frontend shall organise components into two categories:

**shadcn/ui primitives** (auto-generated into `src/components/ui/` via `npx shadcn-ui add`):
`Button`, `Input`, `Label`, `Card`, `CardHeader`, `CardContent`, `CardFooter`, `Dialog`, `AlertDialog`, `Sheet`, `Skeleton`, `Badge`, `Sonner` (toast), `Separator`, `Tooltip`, `DropdownMenu`, `ScrollArea`.
These shall never be hand-written. Always use `npx shadcn-ui add <component>`.

**Feature components** (`src/components/<feature>/`):
- `components/auth/` — `LoginPage`, `SignupPage`, `ForgotPasswordPage`, `ResetPasswordPage`
- `components/documents/` — `DocumentPanel`, `DocumentCard`, `UploadDropzone`, `SuggestedQuestions`
- `components/chat/` — `ChatWindow`, `MessageBubble`, `SessionSidebar`, `CitationBlock`, `ConfidenceBar`, `ToolBadge`
- `components/research/` — `ResearchInput`, `ProgressStepper`, `JobHistoryPanel`, `ReportDownloadCard`
- `components/admin/` — `AdminPanel`, `ToggleSwitch`
- `components/shared/` — `ConfirmDialog` (wraps shadcn `<AlertDialog>`), `LoadingSpinner`

### 6.3.2 State Management

- Global authentication state (access token, user profile) shall be managed via React Context (`AuthContext`).
- Feature-level state (chat messages, document list) shall be managed via `useState` / `useReducer` within their feature components.
- All form state and validation shall use **React Hook Form** + **Zod** schema validation. Pydantic-style schemas shall be defined in `src/lib/validators/` (e.g., `loginSchema.ts`, `registerSchema.ts`, `researchSchema.ts`). This eliminates ad-hoc `useState` for every form field.
- No global state management library (Redux, Zustand) is required for v1.

### 6.3.3 API Client

- A single Axios instance (`src/api/client.ts`) shall be configured with:
  - `baseURL = import.meta.env.VITE_API_URL` (Vite exposes env vars via `import.meta.env`, not `process.env`)
  - A request interceptor that attaches `Authorization: Bearer <token>` to all requests.
  - A response interceptor that catches HTTP 401 responses, calls `POST /api/v1/auth/refresh`, updates the access token in `AuthContext`, and retries the original request once.
- All API call functions shall be organised in `src/api/` by feature (e.g., `auth.api.ts`, `documents.api.ts`, `chat.api.ts`, `research.api.ts`). No raw `axios.get(...)` calls shall appear inside React components.

### 6.3.4 Lazy Loading

- The `/research` page component shall be lazy-loaded using `React.lazy()` and `Suspense` with a shadcn/ui `<Skeleton />` fallback.
- The `/admin` page component shall be lazy-loaded the same way.
- Vite handles code splitting automatically at dynamic `import()` boundaries — no additional configuration required.

## 6.4 Agent Architecture (LangGraph)

The Deep Research agent shall be implemented as a compiled LangGraph `StateGraph`. The graph topology is:

```
[START] → planner → researcher → reflector ──┬── (gaps found & iter < max) → gap_filler → reflector
                                              └── (no gaps or iter >= max) → synthesizer → writer → [END]
```

Each node is a pure Python async function that accepts `AgentState` and returns a partial `AgentState` update. The graph is compiled once at application startup and reused across requests.

## 6.5 Deployment Architecture

```
GitHub (main branch)
        │
        ├──[push]──► Vercel Build (frontend/)
        │              └── npm run build → deploys to Vercel CDN
        │
        └──[push]──► Render Build (backend/)
                       └── pip install -r requirements.txt
                           → uvicorn main:app restarts
                           
        └──[push]──► Render Build (eval_dashboard/)
                       └── pip install -r requirements.txt
                           → streamlit run dashboard.py restarts

UptimeRobot → GET https://<render-backend>/api/v1/health (every 14 min)
```

---

---

# 7. Data Design

## 7.1 Database Schema

The production database is **Supabase PostgreSQL**. The local development database is **SQLite** with the same schema.

---

### Table: `users`

Stores all registered users. Supabase Auth is **not** used; this is a custom users table.

```sql
CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name     TEXT NOT NULL,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    last_login    TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users (email);
```

---

### Table: `refresh_tokens`

Stores hashed refresh tokens for the token rotation strategy.

```sql
CREATE TABLE refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  TEXT NOT NULL UNIQUE,   -- SHA-256 hash of the raw token
    expires_at  TIMESTAMPTZ NOT NULL,
    is_revoked  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens (user_id);
CREATE INDEX idx_refresh_tokens_token_hash ON refresh_tokens (token_hash);
```

---

### Table: `password_reset_tokens`

```sql
CREATE TABLE password_reset_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  TEXT NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    used        BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_prt_token_hash ON password_reset_tokens (token_hash);
```

---

### Table: `documents`

Stores metadata for each uploaded PDF.

```sql
CREATE TABLE documents (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename      TEXT NOT NULL,
    storage_path  TEXT NOT NULL,         -- e.g., "{user_id}/{uuid}_{filename}"
    chunk_count   INTEGER NOT NULL DEFAULT 0,
    file_size_kb  INTEGER,
    uploaded_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
    -- Note: documents are immutable after upload (no content editing).
    -- The UI shall display "Uploaded on <date>" not "Last modified".
    -- An updated_at column is intentionally omitted as documents cannot be modified.
);

CREATE INDEX idx_documents_user_id ON documents (user_id);
```

---

### Table: `suggested_questions`

Caches auto-generated questions per document to avoid repeat LLM calls.

```sql
CREATE TABLE suggested_questions (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id  UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question     TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sq_document_id ON suggested_questions (document_id);
```

---

### Table: `chat_sessions`

Named chat sessions per user, sidebar-listed.

```sql
CREATE TABLE chat_sessions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       TEXT NOT NULL DEFAULT 'New Chat',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chat_sessions_user_id ON chat_sessions (user_id);
```

---

### Table: `chat_messages`

Individual messages within each chat session.

```sql
CREATE TABLE chat_messages (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id   UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role         TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content      TEXT NOT NULL,
    sources      JSONB,   -- { document_sources: [...], web_sources: [...] }
    tools_used   JSONB,   -- e.g., ["rag_search", "web_search"]
    confidence   TEXT CHECK (confidence IN ('high', 'medium', 'low', NULL)),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chat_messages_session_id ON chat_messages (session_id);
CREATE INDEX idx_chat_messages_user_id ON chat_messages (user_id);
```

---

### Table: `research_jobs`

Tracks all deep research jobs and their progress.

```sql
CREATE TABLE research_jobs (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic        TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'queued'
                 CHECK (status IN ('queued','planning','researching',
                                   'reflecting','synthesizing','writing',
                                   'complete','failed','cancelled')),
    progress     JSONB,               -- { "current_step": "Sub-question 2 of 5",
                                     --   "steps_done": 1, "total_steps": 5,
                                     --   "current_node": "researching" }
                                     -- Updated by Researcher node per sub-question
    report_path  TEXT,                   -- storage path, set when complete
    confidence   TEXT CHECK (confidence IN ('high', 'medium', 'low', NULL)),
    confidence_score  FLOAT,             -- raw float score
    error_message     TEXT,              -- populated on 'failed'
    expires_at   TIMESTAMPTZ,            -- NOW() + RESEARCH_JOB_RETENTION_DAYS
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_research_jobs_user_id ON research_jobs (user_id);
CREATE INDEX idx_research_jobs_status ON research_jobs (status);
CREATE INDEX idx_research_jobs_expires_at ON research_jobs (expires_at);
```

---

### Table: `app_settings`

Global key-value settings (e.g., AI kill switch).

```sql
CREATE TABLE app_settings (
    key    TEXT PRIMARY KEY,
    value  TEXT NOT NULL
);

-- Seed:
INSERT INTO app_settings (key, value) VALUES ('ai_enabled', 'true');
```

---

### Table: `eval_results`

Stores RAGAS evaluation run results.

```sql
CREATE TABLE eval_results (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id            UUID NOT NULL,     -- groups questions from same run
    question          TEXT NOT NULL,
    answer            TEXT,
    faithfulness      FLOAT,
    answer_relevancy  FLOAT,
    context_precision FLOAT,
    passed            BOOLEAN,
    evaluated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_eval_results_run_id ON eval_results (run_id);
```

---

## 7.2 ChromaDB Collection Design

- Collection naming: `user_{user_id_no_hyphens}` — UUID hyphens **shall always be replaced** with underscores because ChromaDB collection names must match the regex `[a-zA-Z0-9_-]{3,63}` and hyphens within a UUID (e.g., `550e8400-e29b-41d4`) violate this pattern. The sanitization shall be applied unconditionally: `collection_name = f"user_{user_id.replace('-', '_')}"`. This logic shall live in a single helper function in `rag/retriever.py` used everywhere a collection name is constructed.
- Each chunk document stored in ChromaDB shall have the following metadata:
  ```json
  {
    "document_id": "<uuid>",
    "filename": "paper.pdf",
    "page_number": 3,
    "chunk_index": 12,
    "user_id": "<uuid>"
  }
  ```
- The `user_id` metadata field enables additional safety checks during retrieval.
- On document deletion, all vectors with `metadata.document_id == <deleted_document_id>` shall be deleted from the collection using ChromaDB's `where` filter.

## 7.3 Data Flow Diagrams

### 7.3.1 Document Upload Flow

```
User → POST /api/v1/documents/upload (PDF)
  → Router (JWT validation, rate limit)
  → Controller (file size check, MIME check)
  → doc_service.upload()
      → storage.save_file()       → Supabase Storage / local
      → rag.indexer.index_pdf()   → extract text → chunk → embed → ChromaDB
      → doc_repository.create()   → Supabase PostgreSQL (documents table)
      → doc_service.generate_suggested_questions()  → LLM → suggested_questions table
  ← HTTP 201 { document, suggested_questions }
```

### 7.3.2 Q&A Chat Flow

```
User → POST /api/v1/chat/{session_id}/messages { query }
  → Router (JWT, rate limit)
  → Controller (query length check)
  → chat_service.send_message()
      → chat_repository.save_user_message()
      → chat_repository.get_recent_messages(limit=CHAT_CONTEXT_WINDOW)
      → agent.qa_agent.run(query, context, user_id)
          → [RAG tool] rag.retriever.search() → ChromaDB
          → [Web tool] tavily.search()
          → LLM synthesis with citations
          → compute confidence score
      → chat_repository.save_assistant_message()
  ← HTTP 200 { message, sources, confidence, tools_used }
```

### 7.3.3 Deep Research Flow

```
User → POST /api/v1/research { topic }
  → Router (JWT, rate limit)
  → Controller (topic length, active job check)
  → research_service.start_job()
      → research_repository.create_job() → research_jobs table (status: queued)
      → BackgroundTasks.add_task(run_research_agent)
  ← HTTP 202 { job_id, status: "queued" }

[Background] run_research_agent(job_id, topic, user_id)
  → LangGraph: planner → researcher → reflector → [gap_filler] → synthesizer → writer
  → Each node → update_job_status(job_id, <status>)
  → Writer → docx_writer.generate() → Supabase Storage
  → research_repository.update_job(complete, report_path, confidence)

User → GET /api/v1/research/{job_id}/status [polling every 3s]
  ← { status, confidence, ... }

User → GET /api/v1/research/{job_id}/download
  ← DOCX file stream
```

---

---

# 8. API Design

## 8.1 Conventions

- **Base Path**: `/api/v1/`
- **Format**: All request and response bodies shall be JSON unless noted (file upload/download).
- **Authentication**: Protected endpoints require `Authorization: Bearer <access_token>` header.
- **HTTP Status Codes**: Standard codes shall be used consistently:
  - `200 OK` — Successful read or update.
  - `201 Created` — Successful resource creation.
  - `202 Accepted` — Async job accepted.
  - `204 No Content` — Successful deletion.
  - `400 Bad Request` — Validation failure.
  - `401 Unauthorized` — Missing or invalid JWT.
  - `403 Forbidden` — Authenticated but not authorized for this resource.
  - `404 Not Found` — Resource does not exist.
  - `409 Conflict` — Duplicate resource or business rule violation.
  - `413 Payload Too Large` — File exceeds size limit.
  - `415 Unsupported Media Type` — Wrong file type.
  - `429 Too Many Requests` — Rate limit exceeded.
  - `503 Service Unavailable` — AI service is toggled off.
- **Error Response Shape**:
  ```json
  {
    "error": {
      "code": "RESOURCE_NOT_FOUND",
      "message": "Document with id <id> not found.",
      "field": null
    }
  }
  ```

## 8.2 Complete Endpoint Specification

### Authentication Endpoints

| Method | Endpoint                          | Auth     | Description                                        |
|--------|-----------------------------------|----------|----------------------------------------------------|
| POST   | `/api/v1/auth/register`           | None     | Register new user                                  |
| POST   | `/api/v1/auth/login`              | None     | Login, receive access token + httpOnly refresh cookie |
| POST   | `/api/v1/auth/refresh`            | Cookie   | Exchange refresh token for new access token        |
| POST   | `/api/v1/auth/logout`             | JWT      | Revoke refresh token, clear cookie                 |
| POST   | `/api/v1/auth/forgot-password`    | None     | Send password reset email                         |
| POST   | `/api/v1/auth/reset-password`     | None     | Reset password with token                          |

### Document Endpoints

| Method | Endpoint                                          | Auth | Description                        |
|--------|---------------------------------------------------|------|------------------------------------|
| POST   | `/api/v1/documents/upload`                        | JWT  | Upload + index PDF                 |
| GET    | `/api/v1/documents`                               | JWT  | List user's documents              |
| DELETE | `/api/v1/documents/{document_id}`                 | JWT  | Delete document from all layers    |
| GET    | `/api/v1/documents/{document_id}/suggested-questions` | JWT | Get/generate suggested questions |

### Chat Endpoints

| Method | Endpoint                                          | Auth | Description                        |
|--------|---------------------------------------------------|------|------------------------------------|
| POST   | `/api/v1/chat/sessions`                           | JWT  | Create new chat session            |
| GET    | `/api/v1/chat/sessions`                           | JWT  | List all user sessions             |
| PATCH  | `/api/v1/chat/sessions/{session_id}`              | JWT  | Rename session                     |
| DELETE | `/api/v1/chat/sessions/{session_id}`              | JWT  | Delete session + messages          |
| POST   | `/api/v1/chat/{session_id}/messages`              | JWT  | Send message, get AI response      |
| GET    | `/api/v1/chat/{session_id}/messages`              | JWT  | Get messages (paginated)           |
| DELETE | `/api/v1/chat/messages/{message_id}`              | JWT  | Delete a specific message          |

### Research Endpoints

| Method | Endpoint                                          | Auth | Description                        |
|--------|---------------------------------------------------|------|------------------------------------|
| POST   | `/api/v1/research`                                | JWT  | Start research job (202 Accepted)  |
| GET    | `/api/v1/research/history`                        | JWT  | List past research jobs            |
| GET    | `/api/v1/research/{job_id}/status`                | JWT  | Poll job progress                  |
| GET    | `/api/v1/research/{job_id}/download`              | JWT  | Download completed DOCX report     |
| DELETE | `/api/v1/research/{job_id}`                       | JWT  | Cancel running / delete job        |

### Admin Endpoints

| Method | Endpoint                        | Auth          | Description                    |
|--------|---------------------------------|---------------|--------------------------------|
| GET    | `/api/v1/admin/status`          | None          | Get AI service on/off status   |
| POST   | `/api/v1/admin/toggle`          | Admin Header  | Toggle AI service on/off       |

### System Endpoints

| Method | Endpoint              | Auth | Description                                    |
|--------|-----------------------|------|------------------------------------------------|
| GET    | `/api/v1/health`      | None | Health check with metadata                     |

**Health Endpoint Response Example:**
```json
{
  "status": "ok",
  "ai_enabled": true,
  "environment": "production",
  "version": "1.0.0",
  "timestamp": "2025-01-01T00:00:00Z"
}
```

---

---

# 9. Configuration & Environment

## 9.1 Principle: Zero Hardcoding

Every configurable value in the system — URLs, credentials, thresholds, limits, feature flags — shall reside in environment variables. No configuration value shall appear as a literal in source code. All default values shall be documented in `.env.example`.

## 9.2 Environment Separation

The `ENVIRONMENT` variable governs which backing services the system uses:

| Variable Value   | Database     | File Storage      | Vector DB         | Embeddings                        |
|------------------|--------------|-------------------|-------------------|-----------------------------------|
| `local`          | SQLite       | Local filesystem  | ChromaDB local    | **Gemini Embeddings API**         |
| `production`     | Supabase PG  | Supabase Storage  | ChromaDB Cloud    | Gemini Embeddings API             |

> **Note:** Both environments use Gemini Embeddings to guarantee vector space compatibility. Chunks indexed locally must be searchable in production without re-indexing. A `GEMINI_API_KEY` is therefore required in the local `.env` file.

## 9.3 Frontend Environment Variables

Vite exposes environment variables to the browser via `import.meta.env`. All frontend variables **must** be prefixed with `VITE_`. Variables without this prefix are not injected into the browser bundle.

| Variable                              | Description                                           |
|---------------------------------------|-------------------------------------------------------|
| `VITE_API_URL`                        | Backend base URL (e.g., `https://docmind.onrender.com`) |
| `VITE_ENV`                            | `development` or `production`                         |
| `VITE_EVAL_DASHBOARD_URL`             | URL of the deployed RAGAS Streamlit dashboard          |
| `VITE_RESEARCH_POLL_INTERVAL_MS`      | Polling interval for research status in ms (default: 3000) |

Frontend `.env` file location: `frontend/.env` (never committed). Template: `frontend/.env.example`.

## 9.4 Backend Environment Variables

See **Appendix A** for the complete `.env.example` file with all variables, descriptions, and defaults.

---

---

# 10. Security Requirements

## 10.1 Authentication Security

- **SEC-001**: Passwords shall never be stored in plaintext. bcrypt with work factor `[ENV: BCRYPT_WORK_FACTOR]` shall be used.
- **SEC-002**: Password verification shall use constant-time comparison (bcrypt's built-in `checkpw`) to prevent timing attacks.
- **SEC-003**: JWT tokens shall be signed using HMAC-SHA256 with the `JWT_SECRET_KEY` environment variable. The secret shall be a minimum of 32 random bytes.
- **SEC-004**: Refresh Tokens shall be stored as SHA-256 hashes in the database. The raw token shall only be transmitted over HTTPS.
- **SEC-005**: The Refresh Token shall be set as an `httpOnly` cookie. In production, `SameSite=None; Secure=true` shall be used to allow cross-origin cookie transmission between Vercel (frontend) and Render (backend). In development, `SameSite=Lax; Secure=false` shall be used, as `SameSite=None` requires HTTPS which is unavailable on `localhost`. These attributes shall be read from `ENVIRONMENT` — never hardcoded. See FR-AUTH-012 for the full specification.
- **SEC-006**: The Access Token shall be stored in React in-memory state only — not in `localStorage` or `sessionStorage` — to reduce XSS risk.
- **SEC-007**: Login and registration endpoints shall not distinguish between "email not found" and "wrong password" in their error responses (prevents user enumeration).
- **SEC-008**: Password reset tokens shall expire in `[ENV: PASSWORD_RESET_EXPIRE_MINUTES]` minutes and be single-use only.

## 10.2 Input Validation

- **SEC-009**: All API request bodies shall be validated against Pydantic models before entering the service layer. Invalid input shall be rejected with HTTP 400.
- **SEC-010**: File uploads shall be validated for MIME type and file size at the router layer, before the file content is processed.
- **SEC-011**: All string inputs shall be stripped of leading/trailing whitespace. Chat query and research topic inputs shall be sanitized to remove control characters.
- **SEC-012**: The `email` field in registration and login shall be validated against a strict regex pattern consistent with RFC 5322.

## 10.3 Authorization

- **SEC-013**: Every data-access operation shall include a `WHERE user_id = <authenticated_user_id>` filter. No resource belonging to User A shall ever be accessible, modified, or deleted by User B — regardless of knowing the resource's ID.
- **SEC-014**: Admin operations shall require the `X-Admin-Password` header matching `ADMIN_PASSWORD` env variable. Admin access shall not be based on a user account in the `users` table.

## 10.4 Injection Protection

- **SEC-015**: All database queries shall use parameterized queries or the ORM's safe query-building methods. Raw string interpolation into SQL shall be prohibited.
- **SEC-016**: LLM prompts that include user-supplied content (query text, research topics) shall wrap that content in explicit delimiters (e.g., XML tags) within the prompt to reduce prompt injection risk.

## 10.5 XSS Protection

- **SEC-017**: The React frontend shall rely on React's default JSX escaping for rendering user-generated content. `dangerouslySetInnerHTML` shall not be used unless content is explicitly sanitized with DOMPurify.
- **SEC-018**: The backend shall set the `X-Content-Type-Options: nosniff` response header on all responses.

## 10.6 CORS

- **SEC-019**: CORS allowed origins shall be exclusively sourced from `[ENV: CORS_ORIGINS]`. A wildcard (`*`) origin shall never be used in production.
- **SEC-020**: Only the HTTP methods used by the application (`GET`, `POST`, `PATCH`, `DELETE`) shall be included in the `allow_methods` CORS configuration in production.

## 10.7 HTTPS

- **SEC-021**: All production traffic shall be served over HTTPS. Both Vercel (frontend) and Render (backend) provide automatic HTTPS. There shall be no unencrypted HTTP endpoints in production.

## 10.8 Secrets Management

- **SEC-022**: No secret, API key, password, or credential shall appear in source code, configuration files committed to version control, or log output.
- **SEC-023**: The `.env` file shall be listed in `.gitignore` and shall never be committed to the repository.
- **SEC-024**: A `.env.example` file shall be committed to the repository with placeholder values for all required variables.
- **SEC-025**: Production secrets shall be set via the Render and Vercel environment variable dashboards — not via any file.

## 10.9 Rate Limiting

- **SEC-026**: The backend shall implement per-IP rate limiting using `slowapi` on all endpoints.
- **SEC-027**: The rate limit shall be `[ENV: RATE_LIMIT_REQUESTS_PER_MINUTE]` requests per minute per IP (default: 30) for standard endpoints.
- **SEC-028**: AI-intensive endpoints (`/chat/{session_id}/messages`, `/research`) shall have a stricter limit of `[ENV: RATE_LIMIT_AI_REQUESTS_PER_MINUTE]` requests per minute (default: 10) to protect Gemini API budget. **[COST GUARD]**
- **SEC-029**: When a rate limit is exceeded, the system shall return HTTP 429 Too Many Requests with a `Retry-After` header indicating when the client may retry.

## 10.10 Logging

- **SEC-030**: The system shall log all requests at INFO level including: timestamp, method, path, response status code, and response time (ms).
- **SEC-031**: The system shall log all errors at ERROR level including: timestamp, endpoint, error type, and a sanitized error message. Stack traces shall be included in development logs only.
- **SEC-032**: Logs shall never contain: JWT tokens, passwords, password hashes, API keys, or user PII beyond user_id.
- **SEC-033**: Python's `logging` module shall be used for backend logging. Log format shall be structured (JSON-formatted) in production for easier parsing.

---

---

# 11. Constraints

- **CON-001**: The entire system shall be deployable at zero monthly recurring cost using the free tiers of Vercel, Render, Supabase, and ChromaDB Cloud.
- **CON-002**: No paid cloud service (AWS, GCP, Azure, paid CDN) shall be required in v1.
- **CON-003**: The backend shall not use Celery, Redis, RabbitMQ, or any external message broker. Async tasks shall use FastAPI `BackgroundTasks` only.
- **CON-004**: The vector database shall be ChromaDB. No alternative (Pinecone, Weaviate, Qdrant) shall be used in v1.
- **CON-005**: The LLM shall be Google Gemini 2.5 Flash only. No multi-provider LLM switching is implemented in v1.
- **CON-006**: The system shall use a single GitHub repository with `frontend/`, `backend/`, and `eval_dashboard/` subdirectories. Separate branches per service are not used.
- **CON-007**: Supabase Auth is explicitly excluded. User identity management is entirely custom (see Section 3.1).
- **CON-008**: PDF files are the only supported document type for upload in v1. DOCX, TXT, and other formats are out of scope.
- **CON-009**: The research job limit of one active job per user at a time is a hard constraint for v1. **[COST GUARD]**
- **CON-010**: The document limit of `[ENV: MAX_DOCUMENTS_PER_USER]` is a hard constraint for v1. **[COST GUARD]**
- **CON-011**: Render free tier services sleep after 15 minutes of inactivity. UptimeRobot is the designated mitigation. This is a known and accepted constraint.
- **CON-012**: The system does not support real-time streaming (WebSocket or Server-Sent Events) for agent responses in v1. All responses are request-response.

---

---

# 12. Assumptions & Dependencies

| # | Assumption / Dependency |
|---|-------------------------|
| A-01 | Google Gemini API free tier (AI Studio) provides sufficient quota for development, testing, and demonstration. |
| A-02 | Tavily API free tier (1,000 searches/month) is sufficient for development and demonstration use. |
| A-03 | Supabase free tier limits (500 MB DB, 1 GB Storage, 50,000 monthly active users) are not exceeded during v1 use. |
| A-04 | ChromaDB Cloud free tier provides adequate storage and query volume for per-user collections. |
| A-05 | All uploaded PDFs are text-extractable (not purely scanned images). OCR is out of scope for v1. |
| A-06 | The frontend is deployed to Vercel and uses the auto-generated Vercel URL as the production URL. A custom domain may be configured but is not required. |
| A-07 | UptimeRobot free account shall be configured to ping the Render backend every **5 minutes**. This is the safest interval to guarantee the 15-minute Render sleep threshold is never crossed. The earlier "14-minute" figure is incorrect and has been removed from this document. |
| A-08 | The RAGAS library's 3 selected metrics (Faithfulness, Answer Relevancy, Context Precision) do not require ground truth labels and can run against the system's own generated answers. |
| A-09 | A transactional email service account (Resend free tier — 3,000 emails/month, or a Gmail SMTP app password) is available for sending password reset emails. |
| A-10 | The `python-docx` library is sufficient for generating well-structured DOCX reports without requiring Microsoft Word or LibreOffice. |
| A-11 | The development environment has Python 3.11+ and Node.js 18+ installed. |
| A-12 | GitHub Actions or manual deployment is acceptable; no enterprise CI/CD tooling is required. |

---

---

# Appendix A — `.env.example`

This file shall be committed to the repository at the project root. All actual values shall be kept in a `.env` file that is listed in `.gitignore`.

```bash
# =============================================================
# DocMind AI — Environment Configuration Template
# Copy this file to .env and fill in your actual values.
# NEVER commit .env to version control.
# =============================================================

# ─── ENVIRONMENT ────────────────────────────────────────────
# "local" uses SQLite + local filesystem + local ChromaDB
# "production" uses Supabase + Supabase Storage + ChromaDB Cloud
ENVIRONMENT=local

# Application version (shown in /health endpoint)
APP_VERSION=1.0.0

# ─── CORS ────────────────────────────────────────────────────
# Comma-separated list of allowed frontend origins
# Local:      CORS_ORIGINS=http://localhost:3000
# Production: CORS_ORIGINS=https://your-app.vercel.app
CORS_ORIGINS=http://localhost:3000

# ─── JWT / AUTH ──────────────────────────────────────────────
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY=your_super_secret_key_here_minimum_32_chars
JWT_ALGORITHM=HS256

# Access token expiry in minutes (default: 15)
ACCESS_TOKEN_EXPIRE_MINUTES=15

# Refresh token expiry in days (default: 7)
REFRESH_TOKEN_EXPIRE_DAYS=7

# Password reset token expiry in minutes (default: 30)
PASSWORD_RESET_EXPIRE_MINUTES=30

# bcrypt work factor (default: 12 — increase for more security, slower hashing)
BCRYPT_WORK_FACTOR=12

# Password policy
PASSWORD_MIN_LENGTH=8

# Admin password for /admin panel and RAGAS dashboard (not a user account)
ADMIN_PASSWORD=your_admin_password_here

# ─── LLM ─────────────────────────────────────────────────────
GEMINI_API_KEY=your_gemini_api_key_from_aistudio
# NOTE: GEMINI_API_KEY is required in BOTH local and production environments.
# Both environments use Gemini Embeddings to guarantee vector space compatibility.

# ─── WEB SEARCH ──────────────────────────────────────────────
TAVILY_API_KEY=your_tavily_api_key

# ─── SUPABASE (production only) ──────────────────────────────
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_role_key

# ─── CHROMADB (production only) ──────────────────────────────
CHROMA_HOST=api.trychroma.com
CHROMA_API_KEY=your_chromadb_api_key
CHROMA_TENANT=your_tenant_name
CHROMA_DATABASE=docmind

# ─── EMAIL (for password reset) ──────────────────────────────
# Provider: "resend" or "smtp"
EMAIL_PROVIDER=resend
RESEND_API_KEY=your_resend_api_key
EMAIL_FROM_ADDRESS=noreply@yourdomain.com
# If using SMTP:
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=your_gmail@gmail.com
# SMTP_PASSWORD=your_gmail_app_password

# Frontend URL (used in password reset links)
FRONTEND_URL=http://localhost:3000

# ─── DOCUMENT MANAGEMENT ─────────────────────────────────────
# Max PDF file size in megabytes
MAX_PDF_SIZE_MB=10

# Max documents per user (cost optimization for v1)
MAX_DOCUMENTS_PER_USER=5

# Number of suggested questions to generate per document
SUGGESTED_QUESTIONS_COUNT=5

# ─── RAG CONFIGURATION ───────────────────────────────────────
# Text chunk size in characters
CHUNK_SIZE=1000

# Overlap between consecutive chunks in characters
CHUNK_OVERLAP=200

# Number of top chunks to retrieve per query
RAG_TOP_K=5

# Cosine similarity threshold below which web search is triggered as fallback
# Applies to both Mode 1 Q&A agent and Mode 2 Researcher Node
WEB_SEARCH_FALLBACK_THRESHOLD=0.50

# ─── CHAT CONFIGURATION ──────────────────────────────────────
# Number of recent messages to include as context in each query
CHAT_CONTEXT_WINDOW=10

# Default number of messages returned per history page
CHAT_HISTORY_LIMIT=10

# Max characters in a single chat message
MAX_CHAT_QUERY_LENGTH=2000

# Max characters for auto-generated session titles
SESSION_TITLE_MAX_LENGTH=50

# Max chat sessions per user (prevents unbounded Supabase storage growth)
MAX_SESSIONS_PER_USER=20

# ─── CONFIDENCE THRESHOLDS ───────────────────────────────────
CONFIDENCE_HIGH_THRESHOLD=0.75
CONFIDENCE_MEDIUM_THRESHOLD=0.50

RESEARCH_CONFIDENCE_HIGH=0.70
RESEARCH_CONFIDENCE_MEDIUM=0.45

# Penalty applied to research confidence score when web search was used
WEB_SEARCH_PENALTY=0.10

# ─── DEEP RESEARCH CONFIGURATION ─────────────────────────────
# Max characters for research topic input (cost control)
MAX_RESEARCH_TOPIC_LENGTH=300

# Max sub-questions the Planner node generates
MAX_SUB_QUESTIONS=5

# Max reflection / gap-fill iterations
MAX_REFLECTION_ITERATIONS=3

# Number of past research jobs shown in history panel
RESEARCH_JOB_HISTORY_LIMIT=3

# Days before a research job record and its report are deleted
RESEARCH_JOB_RETENTION_DAYS=7

# Minutes after which a stuck/active job is marked failed on server startup
# This handles jobs interrupted by Render restarts. Default: 20 minutes.
STALE_JOB_TIMEOUT_MINUTES=20

# ─── RATE LIMITING ───────────────────────────────────────────
# Standard endpoints: requests per minute per IP
RATE_LIMIT_REQUESTS_PER_MINUTE=30

# AI endpoints (/chat/messages, /research): requests per minute per IP (cost guard)
RATE_LIMIT_AI_REQUESTS_PER_MINUTE=10

# ─── PAGINATION ──────────────────────────────────────────────
DEFAULT_PAGE_SIZE=20

# ─── RAGAS EVALUATION (eval_dashboard/.env) ──────────────────
EVAL_DATASET_SIZE=10
EVAL_PASS_THRESHOLD=0.70
# URL of the FastAPI backend — used by Streamlit Live Test feature
EVAL_BACKEND_URL=http://localhost:8000
# Admin password (same value as ADMIN_PASSWORD above)
ADMIN_PASSWORD=your_admin_password_here

# ─── FRONTEND ENVIRONMENT VARIABLES ─────────────────────────
# (Place these in frontend/.env — Vite requires VITE_ prefix for all browser-accessible vars)
VITE_API_URL=http://localhost:8000
VITE_ENV=development
# URL of the deployed RAGAS Streamlit dashboard (shown as link in Admin panel)
VITE_EVAL_DASHBOARD_URL=https://your-eval-dashboard.onrender.com
# Polling interval for research job status in milliseconds (frontend only)
VITE_RESEARCH_POLL_INTERVAL_MS=3000
```

---

---

# Appendix B — Folder Structure

```
docmind-ai/
│
├── frontend/                          # Vite + React 18 + Tailwind CSS + shadcn/ui → Vercel
│   ├── public/
│   │   └── favicon.ico
│   ├── index.html                     # Vite entry point (Google Fonts import goes here)
│   ├── vite.config.ts                 # Vite config: path aliases (@/ → src/)
│   ├── tailwind.config.ts             # Tailwind: content paths, theme extension (colours, font)
│   ├── postcss.config.js              # Required by Tailwind
│   ├── tsconfig.json                  # TypeScript config (path aliases)
│   ├── components.json                # shadcn/ui config (generated by init)
│   ├── src/
│   │   ├── main.tsx                   # React DOM root render
│   │   ├── App.tsx                    # Route definitions (React Router) + lazy loading
│   │   ├── api/
│   │   │   ├── client.ts              # Axios instance: baseURL from import.meta.env.VITE_API_URL,
│   │   │   │                          # JWT request interceptor, 401 refresh-and-retry interceptor
│   │   │   ├── auth.api.ts            # All auth API calls (login, register, logout, refresh, etc.)
│   │   │   ├── documents.api.ts       # All document API calls
│   │   │   ├── chat.api.ts            # All chat API calls
│   │   │   └── research.api.ts        # All research API calls
│   │   ├── auth/
│   │   │   └── AuthContext.tsx        # React Context: access token, user profile,
│   │   │                              # login/logout/refresh functions
│   │   ├── components/
│   │   │   ├── ui/                    # shadcn/ui primitives (auto-generated, never hand-written)
│   │   │   │   ├── button.tsx         # npx shadcn-ui add button
│   │   │   │   ├── input.tsx          # npx shadcn-ui add input
│   │   │   │   ├── card.tsx           # npx shadcn-ui add card
│   │   │   │   ├── dialog.tsx         # npx shadcn-ui add dialog
│   │   │   │   ├── alert-dialog.tsx   # npx shadcn-ui add alert-dialog
│   │   │   │   ├── sheet.tsx          # npx shadcn-ui add sheet (mobile nav drawer)
│   │   │   │   ├── skeleton.tsx       # npx shadcn-ui add skeleton
│   │   │   │   ├── badge.tsx          # npx shadcn-ui add badge
│   │   │   │   ├── sonner.tsx         # npx shadcn-ui add sonner (toast notifications)
│   │   │   │   ├── separator.tsx
│   │   │   │   ├── tooltip.tsx
│   │   │   │   ├── dropdown-menu.tsx
│   │   │   │   └── scroll-area.tsx
│   │   │   ├── auth/
│   │   │   │   ├── LoginPage.tsx
│   │   │   │   ├── SignupPage.tsx
│   │   │   │   ├── ForgotPasswordPage.tsx
│   │   │   │   └── ResetPasswordPage.tsx
│   │   │   ├── documents/
│   │   │   │   ├── DocumentPanel.tsx  # Right panel: upload + list + search
│   │   │   │   ├── DocumentCard.tsx   # Single doc card (shadcn Card): filename, size, delete
│   │   │   │   ├── UploadDropzone.tsx # Drag-and-drop PDF uploader
│   │   │   │   └── SuggestedQuestions.tsx # Clickable question Badge chips
│   │   │   ├── chat/
│   │   │   │   ├── ChatWindow.tsx     # Center panel: message thread + input
│   │   │   │   ├── MessageBubble.tsx  # User/assistant message rendering
│   │   │   │   ├── SessionSidebar.tsx # Left panel: session list + new chat button
│   │   │   │   ├── CitationBlock.tsx  # Renders document + web citations separately
│   │   │   │   ├── ConfidenceBar.tsx  # Dot-based confidence indicator (Tailwind coloured dots)
│   │   │   │   └── ToolBadge.tsx      # shadcn Badge showing which tools were used
│   │   │   ├── research/
│   │   │   │   ├── ResearchInput.tsx  # Topic input form (React Hook Form + Zod)
│   │   │   │   ├── ProgressStepper.tsx # Live 7-step progress display
│   │   │   │   ├── JobHistoryPanel.tsx # Past research jobs list
│   │   │   │   └── ReportDownloadCard.tsx # Download button + confidence badge
│   │   │   ├── admin/
│   │   │   │   ├── AdminPanel.tsx
│   │   │   │   └── ToggleSwitch.tsx
│   │   │   └── shared/
│   │   │       └── ConfirmDialog.tsx  # Thin wrapper around shadcn <AlertDialog>
│   │   ├── lib/
│   │   │   ├── utils.ts               # shadcn/ui cn() utility (auto-generated)
│   │   │   └── validators/            # Zod schemas for all forms
│   │   │       ├── loginSchema.ts
│   │   │       ├── registerSchema.ts
│   │   │       ├── researchSchema.ts
│   │   │       └── chatSchema.ts
│   │   └── styles/
│   │       └── globals.css            # @tailwind directives + shadcn CSS variables + font import
│   ├── .env                           # VITE_API_URL etc. (never committed)
│   ├── .env.example
│   └── package.json
│
├── backend/                           # FastAPI → deployed to Render
│   ├── main.py                        # App factory: CORS, rate limiter, router includes,
│   │                                  # startup event (stale job cleanup + retention cleanup)
│   ├── config.py                      # Reads ENVIRONMENT, exports settings object
│   ├── api/
│   │   └── v1/
│   │       ├── routers/
│   │       │   ├── auth.py            # /api/v1/auth/*
│   │       │   ├── documents.py       # /api/v1/documents/*
│   │       │   ├── chat.py            # /api/v1/chat/*
│   │       │   ├── research.py        # /api/v1/research/* (history route FIRST, then /{job_id})
│   │       │   ├── admin.py           # /api/v1/admin/*
│   │       │   └── health.py          # /api/v1/health
│   │       └── models/                # Pydantic request/response models
│   │           ├── auth_models.py
│   │           ├── document_models.py
│   │           ├── chat_models.py
│   │           └── research_models.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── doc_service.py
│   │   ├── chat_service.py
│   │   └── research_service.py
│   ├── repositories/
│   │   ├── user_repository.py
│   │   ├── token_repository.py
│   │   ├── document_repository.py
│   │   ├── chat_repository.py
│   │   └── research_repository.py
│   ├── database/
│   │   ├── supabase_client.py         # production DB + storage client
│   │   └── sqlite_client.py          # local development client
│   ├── storage/
│   │   ├── supabase_storage.py
│   │   └── local_storage.py
│   ├── agent/
│   │   ├── graph.py                   # LangGraph StateGraph definition
│   │   ├── nodes/
│   │   │   ├── planner.py
│   │   │   ├── researcher.py
│   │   │   ├── reflector.py
│   │   │   ├── gap_filler.py
│   │   │   ├── synthesizer.py
│   │   │   └── writer.py
│   │   ├── tools.py                   # RAG tool, web search tool, shared should_use_web_search()
│   │   └── prompts.py                 # All LLM prompt strings as named constants
│   ├── rag/
│   │   ├── indexer.py                 # PDF extraction + chunking + embedding + ChromaDB insert
│   │   └── retriever.py              # ChromaDB semantic search + cosine score extraction
│   │                                  # + get_collection_name() + should_use_web_search()
│   ├── report/
│   │   └── docx_writer.py             # python-docx report generator
│   ├── auth/
│   │   ├── jwt_handler.py             # create/verify access tokens
│   │   ├── password_handler.py        # bcrypt hash/verify
│   │   └── dependencies.py           # get_current_user FastAPI dependency
│   ├── admin/
│   │   └── controls.py
│   ├── email/
│   │   └── email_sender.py            # Resend or SMTP email dispatch
│   ├── middleware/
│   │   └── rate_limiter.py            # slowapi configuration
│   ├── utils/
│   │   └── logger.py                  # Structured logging setup
│   ├── requirements.txt
│   └── .env                           # never committed
│
├── eval_dashboard/                    # Streamlit → separate Render service
│   ├── dashboard.py                   # Main Streamlit app
│   ├── test_dataset.py                # Hardcoded 10-15 Q&A pairs
│   ├── ragas_runner.py               # RAGAS metric computation logic
│   ├── requirements.txt
│   ├── .env                           # EVAL_BACKEND_URL, ADMIN_PASSWORD (never committed)
│   └── .env.example                  # Template with EVAL_BACKEND_URL, ADMIN_PASSWORD, EVAL_DATASET_SIZE, EVAL_PASS_THRESHOLD
│
├── .gitignore                         # .env, __pycache__, *.db, uploads/, dist/, node_modules/
├── .env.example                       # template for backend env vars (see Appendix A)
└── README.md                          # setup guide + architecture diagram + live URLs
```

---

---

# Appendix C — Glossary

| Term                      | Definition                                                                                                  |
|---------------------------|-------------------------------------------------------------------------------------------------------------|
| Access Token              | A short-lived JWT (15 min default) sent in the `Authorization` header to authenticate API requests.         |
| Refresh Token             | A long-lived opaque token (7 days default) stored in an httpOnly cookie, used to obtain new access tokens. |
| RAG                       | Retrieval-Augmented Generation — the technique of retrieving relevant text chunks from a vector database before passing them as context to an LLM. |
| Chunk                     | A fixed-size segment of text extracted from a PDF, with overlap with adjacent chunks, stored in ChromaDB as a vector. |
| Cosine Similarity         | A measure from 0 to 1 of the angular similarity between two vectors, used to rank the relevance of retrieved chunks. |
| LangGraph                 | A library for building stateful, multi-step AI agents as directed graphs, where each node is a processing step. |
| AgentState                | A typed Python dataclass/TypedDict that carries all data through the LangGraph state machine across nodes. |
| httpOnly Cookie           | A browser cookie that cannot be accessed via JavaScript, used to securely transmit the refresh token.      |
| Prompt Injection          | An attack where a user crafts malicious input that hijacks the LLM's instruction context. Mitigated by wrapping user input in delimiters. |
| N+1 Problem               | A database performance anti-pattern where N related records each trigger a separate query rather than one batched query. |
| RAGAS                     | An open-source framework for evaluating RAG systems using metrics like Faithfulness, Answer Relevancy, and Context Precision. |
| UptimeRobot               | A free external monitoring service that pings a URL at regular intervals to prevent the Render free tier from sleeping. |
| FastAPI BackgroundTasks   | A FastAPI mechanism to schedule functions to run after an HTTP response has been sent, used for async research jobs. |
| Token Rotation            | A security strategy where each use of a refresh token invalidates the old token and issues a new one.      |
| CORS                      | Cross-Origin Resource Sharing — a browser security mechanism controlled by HTTP headers that governs which frontend origins may call the backend. |

---

*End of Software Requirements Specification — DocMind AI v1.1 (Post-Review Patch — All 19 issues resolved)*
