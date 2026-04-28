# Software Requirements Specification (SRS)
## DocMind AI — AI Research & Synthesis Agent
### Version 2.0 | Phase-Wise Implementation | IEEE 830 Compliant

---

**Document Control**

| Field              | Detail                                      |
|--------------------|---------------------------------------------|
| Document Title     | Software Requirements Specification — DocMind AI |
| Version            | 2.0 — Phase-Wise Implementation             |
| Status             | Baseline — Implementation Ready              |
| Author             | Project Team — DocMind AI                    |
| Date               | 2026                                         |
| Classification     | Academic — Final Year Project                |

---

## Table of Contents

1. Introduction
2. Overall Description
3. Phase 1 — Project Foundation & Configuration
4. Phase 2 — Authentication System
5. Phase 3 — Document Management & RAG Pipeline
6. Phase 4 — Conversational Q&A (Mode 1)
7. Phase 5 — Deep Research Agent (Mode 2)
8. Phase 6 — Admin, Evaluation & Security Hardening
9. Phase 7 — Production Deployment
10. Non-Functional Requirements
11. Security Requirements
12. System Architecture
13. Data Design
14. API Design
15. Configuration & Environment
16. Constraints
17. Assumptions & Dependencies
18. Appendix A — `.env.example`
19. Appendix B — Folder Structure
20. Appendix C — Glossary

---

---

# 1. Introduction

## 1.1 Purpose

This Software Requirements Specification (SRS) defines the complete functional and non-functional requirements for **DocMind AI**, a full-stack AI Agentic Web Application. It serves as the authoritative reference for all development, testing, and deployment activities. The document is structured in accordance with IEEE Standard 830-1998.

This SRS is organized into **7 sequential implementation phases**. Each phase is independently testable, produces a working increment of the system, and results in a Git commit. This structure allows incremental development, testing, and version control throughout the project lifecycle.

Any deviation from this document shall be recorded as a change request with justification.

## 1.2 Scope

**DocMind AI** is a web-based intelligent research assistant that enables authenticated users to:

1. Upload research documents (PDFs) and ask questions about their content using a Retrieval-Augmented Generation (RAG) pipeline — referred to as **Mode 1: Conversational Q&A**.
2. Submit a research topic and receive an autonomously generated, cited, downloadable research report produced by a multi-step AI agent — referred to as **Mode 2: Deep Research**.

The system is designed for researchers, students, and knowledge workers who need to extract, synthesize, and verify information across private document collections and the live web.

**In-Scope for v1:**

- Custom JWT-based authentication with access/refresh token architecture
- Document upload, storage, indexing, search, and deletion
- Multi-session conversational Q&A with citations, confidence scores, and chat management
- Asynchronous deep research with a multi-node LangGraph state machine
- An admin panel for AI service control
- A publicly accessible RAGAS evaluation dashboard
- Full deployment on zero-cost platforms (Vercel, Render, Supabase, ChromaDB Cloud)

**Out of Scope for v1:**

- Multi-provider LLM support (OpenAI, Groq, etc.)
- User-supplied API keys
- Team/collaborative workspaces
- Real-time WebSocket streaming of agent responses
- CDN integration for global static asset delivery
- Advanced caching layers (Redis)
- Multi-tenancy at the database level beyond `user_id` scoping

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
| httpOnly Cookie    | Browser cookie inaccessible to JavaScript, used to store refresh tokens   |
| bcrypt             | Password hashing algorithm with configurable work factor                  |
| slowapi            | Python rate-limiting library compatible with FastAPI                      |
| python-docx        | Python library for generating Microsoft Word documents                    |

## 1.4 Document Conventions

- Requirements are stated using the keyword **"shall"** for mandatory requirements and **"should"** for recommended/preferred behavior.
- Configuration values that must not be hardcoded are marked with `[ENV: VARIABLE_NAME]` indicating the `.env` key that governs that value.
- Requirements marked **[COST GUARD]** indicate a deliberate cost-saving design decision.
- Each phase section includes a **Verification Checklist** — a numbered list of concrete tests to confirm the phase is complete before committing.

## 1.5 Phase-Wise Development Strategy

The system shall be developed in 7 sequential phases. Each phase:

1. Builds on the previous phase's codebase.
2. Introduces new functional requirements, database tables, API endpoints, and frontend components.
3. Includes a verification checklist that must pass before the phase is committed.
4. Results in a single Git commit with a descriptive message.
5. Produces a working, testable increment of the system.

| Phase | Name | Focus |
|-------|------|-------|
| 1 | Project Foundation & Configuration | Backend + frontend scaffolding, config, health check, DB schema |
| 2 | Authentication System | JWT auth, registration, login, refresh, logout, password reset |
| 3 | Document Management & RAG Pipeline | PDF upload, chunking, embedding, indexing, deletion |
| 4 | Conversational Q&A (Mode 1) | Multi-session chat, RAG retrieval, web search, citations |
| 5 | Deep Research Agent (Mode 2) | LangGraph state machine, async jobs, DOCX reports |
| 6 | Admin, Evaluation & Security Hardening | Admin panel, RAGAS dashboard, rate limiting |
| 7 | Production Deployment | Deploy to Vercel, Render, Supabase, ChromaDB Cloud |

---

---

# 2. Overall Description

## 2.1 Product Perspective

DocMind AI is an independently developed, standalone web application. It is designed as a portfolio-grade, production-deployed demonstration of full-stack AI engineering competencies including RAG pipelines, agentic workflows, asynchronous task orchestration, and evaluation dashboards.

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

### 2.3.2 Admin User

- Accesses the `/admin` route protected by a separate admin password (not a user account).
- Can toggle the AI service on and off.
- Can view and manually trigger RAGAS evaluation runs on the evaluation dashboard.

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
| Database      | **Local PostgreSQL** (same engine as production) |
| File Storage  | Local filesystem (`uploads/` folder)   |
| LLM/Embeddings| Gemini Embeddings API (same as production) |

> **Embedding Model Constraint:** The embedding model shall be **identical** in both local and production environments. Both environments shall use **Gemini Embeddings API** (768 dimensions). Any chunk indexed locally with a different model cannot be searched in production. Local development requires a valid `GEMINI_API_KEY` in `.env`.

> **Database Constraint:** Both local and production environments use **PostgreSQL**. Local development uses a local PostgreSQL instance. Production uses Supabase PostgreSQL. The `config.py` module reads `ENVIRONMENT` and selects the correct `DATABASE_URL`. The same DDL, same queries, same `JSONB`/`TIMESTAMPTZ`/`gen_random_uuid()` work in both environments. No dialect abstraction is needed.

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
- The system shall not require Redis, Celery, or any worker queue infrastructure in v1. Asynchronous jobs shall be handled via FastAPI `BackgroundTasks`.
- **PostgreSQL is the only database engine.** Local development uses a local PostgreSQL instance; production uses Supabase PostgreSQL. No SQLite.

---

---

# 3. Phase 1 — Project Foundation & Configuration

**Goal:** A runnable backend and frontend skeleton with a health check endpoint, a centralized configuration system, the complete database schema, and all route shells.

**Git Commit Message:** `feat: phase 1 — project foundation & configuration`

---

## 3.1 Functional Requirements

### 3.1.1 Backend Scaffold

- **FR-P1-001**: The backend shall be organized as defined in Appendix B under the `backend/` directory.
- **FR-P1-002**: A `config.py` module shall read all environment variables from `.env` using `pydantic-settings` (or `python-dotenv`) and export a typed settings object. This module is the single source of truth for all configuration. No other module shall read environment variables directly.
- **FR-P1-003**: `config.py` shall read the `ENVIRONMENT` variable (values: `local` or `production`) and set the following behavior:
  - `local`: `DATABASE_URL` connects to local PostgreSQL. File storage uses local `uploads/` folder. ChromaDB uses local persistent storage.
  - `production`: `DATABASE_URL` connects to Supabase PostgreSQL. File storage uses Supabase Storage. ChromaDB uses ChromaDB Cloud.
- **FR-P1-004**: `main.py` shall create the FastAPI application instance with:
  - CORS middleware configured from `[ENV: CORS_ORIGINS]` (comma-separated list).
  - A `@app.on_event("startup")` hook (empty body for now — Phase 5 adds stale job recovery).
  - Router includes for all API modules (stubs only — each phase adds implementations).
- **FR-P1-005**: The backend shall include a `utils/logger.py` module configuring Python's `logging` module with structured output (JSON format in production, readable format in local).

### 3.1.2 Health Endpoint

- **FR-P1-006**: The system shall provide a `GET /api/v1/health` endpoint (no authentication required).
- **FR-P1-007**: The health endpoint shall return HTTP 200 with:
  ```json
  {
    "status": "ok",
    "environment": "<local|production>",
    "version": "<APP_VERSION>",
    "timestamp": "<ISO 8601 UTC>"
  }
  ```

### 3.1.3 Database Schema

- **FR-P1-008**: The system shall create all 10 database tables on first startup if they do not exist. The DDL shall use PostgreSQL-native syntax (`gen_random_uuid()`, `TIMESTAMPTZ`, `JSONB`, `CHECK` constraints). The full schema is defined in Section 13 (Data Design).
- **FR-P1-009**: The database connection shall be established using `[ENV: DATABASE_URL]` which follows the format `postgresql://user:password@host:port/dbname`.

### 3.1.4 Frontend Scaffold

- **FR-P1-010**: The frontend shall be scaffolded as a Vite + React 18 + TypeScript project in the `frontend/` directory.
- **FR-P1-011**: Tailwind CSS shall be installed and configured with content paths covering `src/**/*.{ts,tsx}`.
- **FR-P1-012**: shadcn/ui shall be initialized (`npx shadcn-ui init`) and the following core components added: `Button`, `Input`, `Label`, `Card`, `Skeleton`, `Sonner` (toast), `AlertDialog`, `Sheet`, `Badge`, `Separator`, `Tooltip`, `DropdownMenu`, `ScrollArea`.
- **FR-P1-013**: `src/styles/globals.css` shall contain:
  - `@tailwind` directives (base, components, utilities).
  - shadcn/ui CSS variable definitions for the color palette.
  - Font import for **DM Sans** or **Plus Jakarta Sans** from Google Fonts.
  - Primary accent color: muted indigo (`#5B6CF6`).
- **FR-P1-014**: `src/api/client.ts` shall create a singleton Axios instance with:
  - `baseURL` set from `import.meta.env.VITE_API_URL`.
  - Request interceptor stub (Phase 2 adds JWT attachment).
  - Response interceptor stub (Phase 2 adds 401 auto-refresh).
  - `withCredentials: true` to enable cross-origin cookie transmission.
- **FR-P1-015**: `src/App.tsx` shall define React Router routes with placeholder page components for: `/login`, `/signup`, `/forgot-password`, `/reset-password`, `/dashboard`, `/research`, `/admin`.
- **FR-P1-016**: `frontend/.env.example` shall document all frontend environment variables.

### 3.1.5 Project Files

- **FR-P1-017**: A `.gitignore` file at the project root shall exclude: `.env`, `__pycache__/`, `*.pyc`, `uploads/`, `reports/`, `node_modules/`, `dist/`, `*.db`, `.chroma/`.
- **FR-P1-018**: A `.env.example` file at the project root shall list all backend environment variables with placeholder values and descriptions (see Appendix A).
- **FR-P1-019**: A `backend/requirements.txt` shall list all Python dependencies with pinned major versions.
- **FR-P1-020**: A `README.md` at the project root shall document local setup steps, environment variable descriptions, and the deployment process.

---

## 3.2 Environment Variables Introduced

| Variable       | Description                                           | Default |
|----------------|-------------------------------------------------------|---------|
| `ENVIRONMENT`  | `local` or `production` — governs backing services    | `local` |
| `APP_VERSION`  | Version string shown in `/health` response            | `1.0.0` |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend origins      | `http://localhost:5173` |
| `DATABASE_URL` | PostgreSQL connection string                          | `postgresql://postgres:postgres@localhost:5432/docmind` |
| `VITE_API_URL` | Backend base URL for frontend Axios client            | `http://localhost:8000` |
| `VITE_ENV`     | Frontend environment flag                             | `development` |

---

## 3.3 Verification Checklist

| # | Test | Expected Result |
|---|------|-----------------|
| 1 | Run `uvicorn main:app --reload` from `backend/` | Server starts on port 8000 without errors |
| 2 | `GET http://localhost:8000/api/v1/health` | 200 OK with `{ status: "ok", environment: "local", version: "1.0.0", timestamp: "..." }` |
| 3 | Connect to local PostgreSQL and inspect schema | All 10 tables exist with correct columns and indexes |
| 4 | Run `npm run dev` from `frontend/` | Vite dev server starts on port 5173 |
| 5 | Navigate to `http://localhost:5173/login` | Placeholder login page renders |
| 6 | Navigate to all defined routes | Each route renders its placeholder component |
| 7 | Verify `.env.example` exists at project root | All variables listed with descriptions |

---

---

# 4. Phase 2 — Authentication System

**Goal:** A complete JWT-based authentication flow with registration, login, token refresh/rotation, logout, and password reset via email.

**Git Commit Message:** `feat: phase 2 — authentication system`

**Depends On:** Phase 1 (backend scaffold, database schema, frontend skeleton)

---

## 4.1 Functional Requirements

### 4.1.1 User Registration

- **FR-P2-001**: The system shall provide a `POST /api/v1/auth/register` endpoint that accepts `email`, `password`, and `full_name`.
- **FR-P2-002**: The system shall validate that the `email` field conforms to RFC 5322 email format.
- **FR-P2-003**: The system shall enforce the following password policy:
  - Minimum length: `[ENV: PASSWORD_MIN_LENGTH]` characters (default: 8).
  - At least one uppercase letter.
  - At least one digit.
  - At least one special character (`!@#$%^&*`).
- **FR-P2-004**: The system shall reject registration if the email already exists in the `users` table, returning HTTP 409 Conflict.
- **FR-P2-005**: The system shall hash the password using bcrypt with a work factor of `[ENV: BCRYPT_WORK_FACTOR]` (default: 12). The plaintext password shall never be persisted.
- **FR-P2-006**: On success, the system shall return HTTP 201 Created with the user's `id`, `email`, and `full_name`. The password hash shall not be returned.
- **FR-P2-007**: All text inputs shall be sanitized (trim whitespace, validate character sets) before processing.

### 4.1.2 User Login

- **FR-P2-008**: The system shall provide a `POST /api/v1/auth/login` endpoint accepting `email` and `password`.
- **FR-P2-009**: The system shall verify the password against the stored bcrypt hash using a constant-time comparison function.
- **FR-P2-010**: On failed login, the system shall return HTTP 401 Unauthorized with the generic message `"Invalid email or password"`. The response shall not distinguish between a non-existent email and a wrong password.
- **FR-P2-011**: On successful login, the system shall generate and return:
  - An **Access Token** (JWT, signed with `[ENV: JWT_SECRET_KEY]`, algorithm `[ENV: JWT_ALGORITHM]` default HS256, expiry `[ENV: ACCESS_TOKEN_EXPIRE_MINUTES]` minutes, default 15).
  - A **Refresh Token** (opaque UUID, stored hashed in the `refresh_tokens` table, expiry `[ENV: REFRESH_TOKEN_EXPIRE_DAYS]` days, default 7).
- **FR-P2-012**: The Refresh Token shall be set as an `httpOnly` cookie with environment-aware attributes:
  - **Production** (`ENVIRONMENT=production`): `HttpOnly=true; Secure=true; SameSite=None`. `SameSite=None` is required because the frontend (Vercel) and backend (Render) are on different domains.
  - **Local** (`ENVIRONMENT=local`): `HttpOnly=true; Secure=false; SameSite=Lax`. `SameSite=None` requires `Secure=true`, which is unavailable on `localhost` HTTP.
  - Cookie attributes shall be constructed dynamically in `auth_service.py` based on `ENVIRONMENT`. No cookie attribute shall be hardcoded.
  - The Refresh Token shall **never** appear in the JSON response body.
- **FR-P2-013**: The Access Token shall be returned in the JSON response body and stored by the frontend in React component state (in-memory). It shall not be stored in `localStorage` or `sessionStorage`.
- **FR-P2-014**: The JWT Access Token payload shall contain: `user_id`, `email`, `iat` (issued at), `exp` (expiration).
- **FR-P2-015**: The system shall update the `last_login` timestamp on the `users` table upon successful login.

### 4.1.3 Token Refresh

- **FR-P2-016**: The system shall provide a `POST /api/v1/auth/refresh` endpoint.
- **FR-P2-017**: The endpoint shall read the Refresh Token from the `httpOnly` cookie. No body parameter is required.
- **FR-P2-018**: The system shall validate the Refresh Token by:
  1. Looking up its SHA-256 hash in the `refresh_tokens` table.
  2. Verifying it has not expired (`expires_at > NOW()`).
  3. Verifying it has not been revoked (`is_revoked = false`).
- **FR-P2-019**: On valid Refresh Token, the system shall issue a new Access Token and return it in the JSON body.
- **FR-P2-020**: The Refresh Token shall be **rotated** on each use: the old token record is marked `is_revoked = true`, a new token record is inserted, and a new `httpOnly` cookie is set.
- **FR-P2-021**: On invalid or expired Refresh Token, the system shall return HTTP 401 Unauthorized.

### 4.1.4 Logout

- **FR-P2-022**: The system shall provide a `POST /api/v1/auth/logout` endpoint (JWT required).
- **FR-P2-023**: On logout, the system shall mark the current Refresh Token as revoked.
- **FR-P2-024**: The server shall clear the `httpOnly` cookie by setting it with an expired `Max-Age`.
- **FR-P2-025**: The frontend shall clear the in-memory Access Token and redirect to `/login`.

### 4.1.5 Password Reset

- **FR-P2-026**: The system shall provide a `POST /api/v1/auth/forgot-password` endpoint accepting `email`.
- **FR-P2-027**: If the email exists, the system shall generate a cryptographically secure random token, store its SHA-256 hash in the `password_reset_tokens` table with expiry `[ENV: PASSWORD_RESET_EXPIRE_MINUTES]` minutes (default: 30), and send the plaintext token to the user's email as part of a reset link pointing to `[ENV: FRONTEND_URL]/reset-password?token=<token>`.
- **FR-P2-028**: If the email does not exist, the system shall still return HTTP 200 OK with `"If this email is registered, you will receive a reset link."` This prevents email enumeration.
- **FR-P2-029**: The system shall provide a `POST /api/v1/auth/reset-password` endpoint accepting `token` and `new_password`.
- **FR-P2-030**: The system shall validate the token by hashing it and comparing to stored hash. The token must not be expired and must not have been used.
- **FR-P2-031**: On valid token, the system shall update the user's password hash, mark the reset token as `used = true`, and return HTTP 200 OK.
- **FR-P2-032**: The new password shall be subject to the same policy as FR-P2-003.

### 4.1.6 JWT Middleware

- **FR-P2-033**: All protected endpoints shall be guarded by a FastAPI dependency (`get_current_user`) that extracts the JWT from the `Authorization: Bearer <token>` header.
- **FR-P2-034**: The middleware shall verify the JWT signature, validate the `exp` claim, and extract `user_id`.
- **FR-P2-035**: On invalid or expired JWT, the middleware shall return HTTP 401 Unauthorized. The frontend shall automatically call `POST /api/v1/auth/refresh` and retry the original request once. If the refresh also fails, the user is redirected to `/login`.

### 4.1.7 Frontend Auth Components

- **FR-P2-036**: `src/auth/AuthContext.tsx` shall provide React Context with: `accessToken` (in-memory state), `user` (profile object), `login()`, `logout()`, `refresh()` functions.
- **FR-P2-037**: `LoginPage.tsx` shall render a form with email + password inputs, a "Log in" button, links to `/signup` and `/forgot-password`. Form validation via React Hook Form + Zod.
- **FR-P2-038**: `SignupPage.tsx` shall render a form with full name, email, password, and confirm password fields. Validation shall enforce the password policy from FR-P2-003.
- **FR-P2-039**: `ForgotPasswordPage.tsx` shall render an email input and submit button.
- **FR-P2-040**: `ResetPasswordPage.tsx` shall read `token` from the URL query parameter and render new password + confirm password fields.
- **FR-P2-041**: All auth forms shall display inline validation errors next to each field using shadcn/ui `<Input>` + `<Label>` with error styling.
- **FR-P2-042**: A `ProtectedRoute` wrapper component shall check for a valid access token. If absent, it shall attempt a silent refresh. If refresh fails, it shall redirect to `/login`.
- **FR-P2-043**: The Axios response interceptor in `api/client.ts` shall catch HTTP 401 responses, call the refresh endpoint, update the access token in `AuthContext`, and retry the original request once. If the retry also returns 401, the user shall be logged out.

---

## 4.2 Backend Files Introduced

| File | Purpose |
|------|---------|
| `auth/jwt_handler.py` | Create/verify JWT access tokens |
| `auth/password_handler.py` | bcrypt hash/verify |
| `auth/dependencies.py` | `get_current_user` FastAPI dependency |
| `repositories/user_repository.py` | Users table CRUD |
| `repositories/token_repository.py` | Refresh tokens + password reset tokens CRUD |
| `services/auth_service.py` | All auth business logic |
| `api/v1/routers/auth.py` | 6 auth endpoints |
| `api/v1/models/auth_models.py` | Pydantic request/response models |
| `email/email_sender.py` | Resend or SMTP email dispatch |

## 4.3 Frontend Files Introduced

| File | Purpose |
|------|---------|
| `src/auth/AuthContext.tsx` | Auth state provider |
| `src/components/auth/LoginPage.tsx` | Login form |
| `src/components/auth/SignupPage.tsx` | Registration form |
| `src/components/auth/ForgotPasswordPage.tsx` | Forgot password form |
| `src/components/auth/ResetPasswordPage.tsx` | Reset password form |
| `src/api/auth.api.ts` | Auth API call functions |
| `src/lib/validators/loginSchema.ts` | Zod schema for login |
| `src/lib/validators/registerSchema.ts` | Zod schema for registration |

## 4.4 Environment Variables Introduced

| Variable | Description | Default |
|----------|-------------|---------|
| `JWT_SECRET_KEY` | HMAC-SHA256 signing key (min 32 random bytes) | — (required) |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | `7` |
| `PASSWORD_RESET_EXPIRE_MINUTES` | Reset token TTL | `30` |
| `BCRYPT_WORK_FACTOR` | bcrypt cost factor | `12` |
| `PASSWORD_MIN_LENGTH` | Minimum password length | `8` |
| `ADMIN_PASSWORD` | Admin panel password (not a user account) | — (required) |
| `EMAIL_PROVIDER` | `resend` or `smtp` | `resend` |
| `RESEND_API_KEY` | Resend API key (if provider=resend) | — |
| `EMAIL_FROM_ADDRESS` | Sender email for reset emails | `noreply@yourdomain.com` |
| `SMTP_HOST` | SMTP host (if provider=smtp) | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USER` | SMTP username | — |
| `SMTP_PASSWORD` | SMTP password / app password | — |
| `FRONTEND_URL` | Base URL for password reset links | `http://localhost:5173` |

---

## 4.5 Verification Checklist

| # | Test | Expected Result |
|---|------|-----------------|
| 1 | `POST /api/v1/auth/register` with valid data | 201 + `{ id, email, full_name }` |
| 2 | Register with duplicate email | 409 Conflict |
| 3 | Register with weak password | 400 + validation error |
| 4 | `POST /api/v1/auth/login` with correct credentials | 200 + access token in body + `Set-Cookie` with refresh token |
| 5 | Login with wrong password | 401 + `"Invalid email or password"` |
| 6 | Access `GET /api/v1/documents` (protected) with valid JWT | 200 (empty list) |
| 7 | Access protected endpoint with expired JWT | 401 |
| 8 | `POST /api/v1/auth/refresh` (cookie present) | 200 + new access token + rotated cookie |
| 9 | `POST /api/v1/auth/logout` | Cookie cleared, refresh token revoked in DB |
| 10 | `POST /api/v1/auth/forgot-password` with valid email | 200 + email sent (or logged locally) |
| 11 | `POST /api/v1/auth/reset-password` with valid token | 200 + password updated |
| 12 | Frontend: Register → auto redirect to login | Works |
| 13 | Frontend: Login → redirect to `/dashboard` | Access token in memory, cookie set |
| 14 | Frontend: Refresh browser on `/dashboard` | Silent refresh restores session |
| 15 | Frontend: Logout → redirect to `/login` | Token cleared |

---

---

# 5. Phase 3 — Document Management & RAG Pipeline

**Goal:** Upload PDF documents, extract and chunk text, generate embeddings via Gemini, index in ChromaDB, list/search/delete documents with full multi-layer cleanup.

**Git Commit Message:** `feat: phase 3 — document management & RAG pipeline`

**Depends On:** Phase 2 (JWT authentication)

---

## 5.1 Functional Requirements

### 5.1.1 Upload

- **FR-P3-001**: The system shall provide a `POST /api/v1/documents/upload` endpoint (JWT required) accepting a PDF file via `multipart/form-data`.
- **FR-P3-002**: The system shall reject files exceeding `[ENV: MAX_PDF_SIZE_MB]` megabytes with HTTP 413 Payload Too Large.
- **FR-P3-003**: The system shall reject files whose MIME type is not `application/pdf` with HTTP 415 Unsupported Media Type.
- **FR-P3-004**: Before accepting an upload, the system shall check if the user's document count has reached `[ENV: MAX_DOCUMENTS_PER_USER]` (default: 5). If so, it shall return HTTP 409 Conflict with existing document IDs and filenames. **[COST GUARD]**
- **FR-P3-005**: On successful upload, the system shall:
  1. Save the file to Supabase Storage (production) or the local `uploads/` folder (local) under `{user_id}/{uuid}_{original_filename}`.
  2. Extract text from the PDF using `pdfplumber` or `PyMuPDF`.
  3. Split extracted text into overlapping chunks using LangChain's `RecursiveCharacterTextSplitter` with `chunk_size=[ENV: CHUNK_SIZE]` (default: 1000) and `chunk_overlap=[ENV: CHUNK_OVERLAP]` (default: 200).
  4. Generate embeddings for each chunk using **Gemini Embeddings API**.
  5. Insert all chunk vectors into the ChromaDB collection for this user (collection name: `user_{user_id}` with hyphens replaced by underscores).
  6. Insert a record into the `documents` table with `id`, `user_id`, `filename`, `storage_path`, `chunk_count`, `file_size_kb`, and `uploaded_at`.
  7. Return HTTP 201 Created with the new document record and suggested questions.
- **FR-P3-006**: If any step in FR-P3-005 fails after the file has been saved, the system shall rollback: delete the file from storage and remove any partially inserted vectors from ChromaDB.
- **FR-P3-007**: After successful upload, the system shall automatically generate suggested questions and return them in the upload response.

### 5.1.2 List Documents

- **FR-P3-008**: The system shall provide a `GET /api/v1/documents` endpoint (JWT required) returning all documents belonging to the authenticated user, ordered by `uploaded_at` descending.
- **FR-P3-009**: Each document record shall include: `id`, `filename`, `chunk_count`, `file_size_kb`, `uploaded_at`, and `storage_path`.
- **FR-P3-010**: The response shall include `document_count` and `document_limit` fields for frontend display (e.g., "3 / 5 documents used").

### 5.1.3 Search Documents

- **FR-P3-011**: The document list panel shall support client-side filtering by filename as the user types in a search input field.
- **FR-P3-012**: The search shall be case-insensitive and match partial filename substrings.
- **FR-P3-013**: No additional API endpoint is required — filtering is performed on the already-fetched document list.

### 5.1.4 Suggested Questions

- **FR-P3-014**: The system shall provide a `GET /api/v1/documents/{document_id}/suggested-questions` endpoint (JWT required).
- **FR-P3-015**: The system shall generate `[ENV: SUGGESTED_QUESTIONS_COUNT]` (default: 5) questions by sending the first retrieved chunks of the document to the LLM with a prompt instructing it to generate thoughtful, document-specific questions.
- **FR-P3-016**: Generated questions shall be stored in the `suggested_questions` table linked to `document_id`, so repeated requests return cached results without re-calling the LLM.
- **FR-P3-017**: Suggested questions shall be displayed in the frontend as clickable chips (shadcn `<Badge>`). Clicking a chip shall pre-fill the chat input and submit it.

### 5.1.5 Delete Document

- **FR-P3-018**: The system shall provide a `DELETE /api/v1/documents/{document_id}` endpoint (JWT required).
- **FR-P3-019**: The system shall verify the document belongs to the authenticated user. If not, return HTTP 403 Forbidden.
- **FR-P3-020**: On authorized deletion, the system shall:
  1. Delete the file from Supabase Storage (production) or local `uploads/` (local).
  2. Delete all chunk vectors from ChromaDB where `metadata.document_id` matches.
  3. Delete the record from the `documents` table.
  4. Delete associated `suggested_questions` records.
  5. Return HTTP 200 OK with a success message.
- **FR-P3-021**: If any deletion step fails, the system shall log the error, continue executing remaining steps, and return HTTP 200 OK with a `warnings` array listing which steps failed.

### 5.1.6 ChromaDB Collection Naming

- **FR-P3-022**: ChromaDB collection names shall follow the format `user_{user_id_no_hyphens}` where UUID hyphens are unconditionally replaced with underscores. This logic shall live in a single helper function `get_collection_name(user_id: str) -> str` in `rag/retriever.py` and be used everywhere a collection name is constructed.

### 5.1.7 Frontend Document Components

- **FR-P3-023**: `DocumentPanel.tsx` shall render the right panel containing: upload dropzone (top), search input, and scrollable document card list.
- **FR-P3-024**: `UploadDropzone.tsx` shall support drag-and-drop and click-to-browse for PDF files. It shall show upload progress and handle errors via toast notifications.
- **FR-P3-025**: `DocumentCard.tsx` shall display: filename, file size (formatted as KB/MB), chunk count, upload date, and a delete button. Delete shall trigger a confirmation dialog (shadcn `<AlertDialog>`).
- **FR-P3-026**: `SuggestedQuestions.tsx` shall render clickable `<Badge>` chips below each document card.

### 5.1.8 Storage Abstraction

- **FR-P3-027**: File storage operations shall be abstracted behind a common interface. `storage/local_storage.py` handles local file I/O. `storage/supabase_storage.py` handles Supabase Storage API calls. `config.py` selects the appropriate storage backend based on `ENVIRONMENT`.

---

## 5.2 Backend Files Introduced

| File | Purpose |
|------|---------|
| `rag/indexer.py` | PDF extraction, chunking, embedding, ChromaDB insert |
| `rag/retriever.py` | Semantic search, `get_collection_name()`, `should_use_web_search()` |
| `storage/local_storage.py` | Local filesystem save/delete |
| `storage/supabase_storage.py` | Supabase Storage save/delete |
| `repositories/document_repository.py` | Documents + suggested_questions CRUD |
| `services/doc_service.py` | Upload orchestration, rollback, suggested questions |
| `api/v1/routers/documents.py` | 4 document endpoints |
| `api/v1/models/document_models.py` | Pydantic models |

## 5.3 Frontend Files Introduced

| File | Purpose |
|------|---------|
| `src/components/documents/DocumentPanel.tsx` | Right panel layout |
| `src/components/documents/DocumentCard.tsx` | Single document card |
| `src/components/documents/UploadDropzone.tsx` | Drag-and-drop uploader |
| `src/components/documents/SuggestedQuestions.tsx` | Clickable question chips |
| `src/api/documents.api.ts` | Document API calls |

## 5.4 Environment Variables Introduced

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key (required in BOTH local and production) | — (required) |
| `MAX_PDF_SIZE_MB` | Max PDF file size in MB | `10` |
| `MAX_DOCUMENTS_PER_USER` | Max documents per user | `5` |
| `SUGGESTED_QUESTIONS_COUNT` | Questions generated per document | `5` |
| `CHUNK_SIZE` | Text chunk size in characters | `1000` |
| `CHUNK_OVERLAP` | Overlap between chunks | `200` |
| `RAG_TOP_K` | Top chunks to retrieve per query | `5` |

---

## 5.5 Verification Checklist

| # | Test | Expected Result |
|---|------|-----------------|
| 1 | Upload valid PDF (< 10 MB) | 201 + document record + 5 suggested questions |
| 2 | Upload a `.txt` file | 415 Unsupported Media Type |
| 3 | Upload a 15 MB PDF | 413 Payload Too Large |
| 4 | Upload 6th document (limit = 5) | 409 Conflict with existing doc list |
| 5 | `GET /api/v1/documents` | List with `document_count` and `document_limit` |
| 6 | Delete a document | File removed from disk, vectors removed from ChromaDB, DB record gone |
| 7 | Query ChromaDB collection for deleted document | No vectors returned |
| 8 | `GET /api/v1/documents/{id}/suggested-questions` twice | Second call returns cached (no LLM call) |
| 9 | Frontend: drag PDF onto dropzone | Upload progress → card appears |
| 10 | Frontend: type in search box | Document list filters in real-time |
| 11 | Frontend: click delete on card | Confirmation dialog → card disappears |
| 12 | Frontend: click a suggested question chip | Chat input pre-filled |

---

---

# 6. Phase 4 — Conversational Q&A (Mode 1)

**Goal:** Multi-session chat with RAG retrieval, conditional web search, citations, confidence scores, tool indicators, and a typing indicator for UX responsiveness.

**Git Commit Message:** `feat: phase 4 — conversational Q&A (Mode 1)`

**Depends On:** Phase 3 (document management, RAG pipeline)

---

## 6.1 Functional Requirements

### 6.1.1 Chat Session Management

- **FR-P4-001**: The system shall support multiple simultaneous named chat sessions per user, presented in a left-sidebar layout.
- **FR-P4-002**: The system shall provide a `POST /api/v1/chat/sessions` endpoint (JWT required) to create a new session, accepting an optional `title`. If no title is provided, the system shall use the first user message (truncated to `[ENV: SESSION_TITLE_MAX_LENGTH]` characters, default: 50).
- **FR-P4-003**: Before creating a new session, the system shall verify the user's session count has not reached `[ENV: MAX_SESSIONS_PER_USER]` (default: 20). If reached, return HTTP 409 Conflict. **[COST GUARD]**
- **FR-P4-004**: The system shall provide a `GET /api/v1/chat/sessions` endpoint (JWT required) returning all sessions ordered by `updated_at` descending.
- **FR-P4-005**: The system shall provide a `DELETE /api/v1/chat/sessions/{session_id}` endpoint (JWT required) deleting the session and all its messages.
- **FR-P4-006**: The system shall provide a `PATCH /api/v1/chat/sessions/{session_id}` endpoint (JWT required) for renaming a session title.

### 6.1.2 Sending a Message

- **FR-P4-007**: The system shall provide a `POST /api/v1/chat/{session_id}/messages` endpoint (JWT required) accepting a `query` string.
- **FR-P4-008**: The system shall validate that `query` is not empty and does not exceed `[ENV: MAX_CHAT_QUERY_LENGTH]` characters (default: 2000).
- **FR-P4-009**: Upon receiving a query, the system shall:
  1. Store the user's message in `chat_messages` with `role = 'user'`.
  2. Retrieve the last `[ENV: CHAT_CONTEXT_WINDOW]` messages (default: 10) to build conversation context.
  3. Call the Q&A agent (FR-P4-010).
  4. Store the assistant's response in `chat_messages` with `role = 'assistant'`, including `sources` (JSONB) and `confidence` fields.
  5. Update the session's `updated_at` timestamp.
  6. Return the complete assistant message object.
- **FR-P4-010**: **Q&A Agent Architecture.** The Q&A agent shall be a **LangChain tool-calling agent** with two tools: `rag_search` and `web_search`. The decision logic:
  - **Step 1 — Always RAG first:** Call `rag_search` on every query. Returns top `[ENV: RAG_TOP_K]` chunks and the top cosine similarity score.
  - **Step 2 — Conditional web search:** Invoke `web_search` (Tavily) **only if**:
    - The user has zero documents (ChromaDB collection is empty), OR
    - The top RAG cosine score is below `[ENV: WEB_SEARCH_FALLBACK_THRESHOLD]` (default: 0.50).
  - **Step 3 — Synthesize:** Call the LLM once with retrieved context to generate the answer.
  - This logic shall be implemented via a shared utility function `should_use_web_search(top_score: float, collection_empty: bool) -> bool` in `rag/retriever.py`, reused by both Mode 1 and Mode 2. **[COST GUARD]**
  - The agent shall be constructed once at startup and reused across requests.
- **FR-P4-011**: The system shall check `ai_enabled` from the `app_settings` table before invoking the agent. If `ai_enabled = false`, the endpoint shall return HTTP 503 Service Unavailable with `"AI service is temporarily unavailable."`.

### 6.1.3 Citation Display

- **FR-P4-012**: Every assistant response shall include a `sources` object with:
  - `document_sources`: List of `{ filename, page_number, chunk_preview, cosine_score }`.
  - `web_sources`: List of `{ url, title, snippet }`.
- **FR-P4-013**: If only RAG was used, `web_sources` shall be an empty array, and vice versa.
- **FR-P4-014**: The frontend shall render document and web citations in visually distinct sections below each message, labelled "From Your Documents" and "From the Web".

### 6.1.4 Confidence Indicator

- **FR-P4-015**: Each response shall include a `confidence` field:
  ```
  score = top_chunk_cosine_similarity
  High   → score >= CONFIDENCE_HIGH_THRESHOLD   [ENV, default: 0.75]
  Medium → score >= CONFIDENCE_MEDIUM_THRESHOLD [ENV, default: 0.50]
  Low    → score < CONFIDENCE_MEDIUM_THRESHOLD
  ```
- **FR-P4-016**: If no document sources were used (pure web search), confidence defaults to `"low"`.
- **FR-P4-017**: The frontend shall render a filled dot indicator: green for High, amber for Medium, red for Low.

### 6.1.5 Tool Use Indicator

- **FR-P4-018**: Each response shall include a `tools_used` array (e.g., `["rag_search", "web_search"]`). The frontend shall display a small `<Badge>` per tool.

### 6.1.6 Chat History

- **FR-P4-019**: The system shall provide a `GET /api/v1/chat/{session_id}/messages` endpoint (JWT required) returning messages for that session.
- **FR-P4-020**: The endpoint shall support pagination via `limit` and `offset` query parameters (default: `[ENV: CHAT_HISTORY_LIMIT]`, default: 10).
- **FR-P4-021**: Messages shall be returned in ascending chronological order (oldest first).

### 6.1.7 Message Deletion

- **FR-P4-022**: The system shall provide a `DELETE /api/v1/chat/messages/{message_id}` endpoint (JWT required).
- **FR-P4-023**: The system shall verify the message belongs to a session owned by the authenticated user.
- **FR-P4-024**: The frontend shall show a hover-reveal trash icon on user messages.

### 6.1.8 Frontend Chat Components

- **FR-P4-025**: `SessionSidebar.tsx` shall render the left panel with: session list, "New Chat" button, navigation links. Active session highlighted with `bg-primary/10 text-primary`.
- **FR-P4-026**: `ChatWindow.tsx` shall render: scrollable message thread, input bar with send button, and an **animated typing indicator** (three bouncing dots) displayed while waiting for the assistant's response. The typing indicator eliminates the need for WebSocket streaming — the user sees immediate visual feedback.
- **FR-P4-027**: `MessageBubble.tsx` shall render user messages (right-aligned) and assistant messages (left-aligned) with markdown support.
- **FR-P4-028**: `CitationBlock.tsx` shall render document sources and web sources in separate expandable sections.
- **FR-P4-029**: `ConfidenceBar.tsx` shall render a colored dot indicator adjacent to the assistant message.
- **FR-P4-030**: `ToolBadge.tsx` shall render a shadcn `<Badge>` for each tool used.

### 6.1.9 Agent Prompt Storage

- **FR-P4-031**: All LLM prompts shall be stored in `agent/prompts.py` as named string constants, not inline in function bodies.
- **FR-P4-032**: User-supplied content in prompts (query text) shall be wrapped in explicit XML delimiters (e.g., `<user_query>...</user_query>`) to reduce prompt injection risk.

---

## 6.2 Backend Files Introduced

| File | Purpose |
|------|---------|
| `agent/tools.py` | `rag_search` and `web_search` tool functions |
| `agent/prompts.py` | All LLM prompt strings as named constants |
| `repositories/chat_repository.py` | Chat sessions + messages CRUD |
| `services/chat_service.py` | Session management, message handling, agent invocation |
| `api/v1/routers/chat.py` | 7 chat endpoints |
| `api/v1/models/chat_models.py` | Pydantic models |

## 6.3 Frontend Files Introduced

| File | Purpose |
|------|---------|
| `src/components/chat/SessionSidebar.tsx` | Left panel session list |
| `src/components/chat/ChatWindow.tsx` | Message thread + input + typing indicator |
| `src/components/chat/MessageBubble.tsx` | User/assistant message rendering |
| `src/components/chat/CitationBlock.tsx` | Document + web citation sections |
| `src/components/chat/ConfidenceBar.tsx` | Colored dot indicator |
| `src/components/chat/ToolBadge.tsx` | Tool usage badge |
| `src/api/chat.api.ts` | Chat API calls |
| `src/lib/validators/chatSchema.ts` | Zod schema for chat input |

## 6.4 Environment Variables Introduced

| Variable | Description | Default |
|----------|-------------|---------|
| `TAVILY_API_KEY` | Tavily web search API key | — (required) |
| `WEB_SEARCH_FALLBACK_THRESHOLD` | Cosine score below which web search triggers | `0.50` |
| `CHAT_CONTEXT_WINDOW` | Recent messages included as context | `10` |
| `CHAT_HISTORY_LIMIT` | Default messages per history page | `10` |
| `MAX_CHAT_QUERY_LENGTH` | Max characters per chat message | `2000` |
| `SESSION_TITLE_MAX_LENGTH` | Max chars for auto-generated titles | `50` |
| `MAX_SESSIONS_PER_USER` | Max chat sessions per user | `20` |
| `CONFIDENCE_HIGH_THRESHOLD` | Score >= this = "high" | `0.75` |
| `CONFIDENCE_MEDIUM_THRESHOLD` | Score >= this = "medium" | `0.50` |

---

## 6.5 Verification Checklist

| # | Test | Expected Result |
|---|------|-----------------|
| 1 | `POST /api/v1/chat/sessions` | 201 + session object |
| 2 | Create 21st session (limit = 20) | 409 Conflict |
| 3 | `GET /api/v1/chat/sessions` | Sessions ordered by `updated_at` desc |
| 4 | Send message with uploaded documents | RAG response with `document_sources` populated |
| 5 | Send message with zero documents | Web search response with `web_sources` populated |
| 6 | Send message where RAG score < 0.50 | Both `document_sources` and `web_sources` populated |
| 7 | Verify `confidence` matches threshold rules | High/Medium/Low correct for given cosine scores |
| 8 | Verify `tools_used` array | `["rag_search"]` or `["rag_search", "web_search"]` |
| 9 | `GET /api/v1/chat/{session_id}/messages?limit=5&offset=0` | Paginated, ascending order |
| 10 | `DELETE /api/v1/chat/sessions/{session_id}` | Session + all messages deleted |
| 11 | `DELETE /api/v1/chat/messages/{message_id}` for another user's message | 403 Forbidden |
| 12 | Frontend: New Chat → type query → see typing indicator → response appears | Full flow works |
| 13 | Frontend: Citations render in separate "Documents" and "Web" sections | Correct labelling |
| 14 | Frontend: Confidence dots show correct color | Green/Amber/Red |
| 15 | Frontend: Tool badge shows which tools were used | Correct badges |

---

---

# 7. Phase 5 — Deep Research Agent (Mode 2)

**Goal:** An asynchronous LangGraph research agent that decomposes a topic into sub-questions, researches each one, reflects on gaps, synthesizes findings, and generates a downloadable DOCX report — with live progress polling.

**Git Commit Message:** `feat: phase 5 — deep research agent (Mode 2)`

**Depends On:** Phase 4 (Q&A agent, RAG tools, web search tools, `should_use_web_search()`)

---

## 7.1 Functional Requirements

### 7.1.1 Initiating a Research Job

- **FR-P5-001**: The system shall provide a `POST /api/v1/research` endpoint (JWT required) accepting a `topic` string.
- **FR-P5-002**: The `topic` shall not exceed `[ENV: MAX_RESEARCH_TOPIC_LENGTH]` characters (default: 300) and shall not be empty. **[COST GUARD]**
- **FR-P5-003**: Before creating a new job, the system shall check if the user has any research job in an active state (`queued`, `planning`, `researching`, `reflecting`, `synthesizing`, `writing`). If so, return HTTP 409 Conflict with `"A research job is already in progress."` **[COST GUARD]**
- **FR-P5-004**: On acceptance:
  1. Insert a new record into `research_jobs` with `status = 'queued'` and `expires_at = NOW() + RESEARCH_JOB_RETENTION_DAYS`.
  2. Schedule `run_research_agent(job_id, topic, user_id)` as a FastAPI `BackgroundTask`.
  3. Return HTTP 202 Accepted with `{ "job_id": "<uuid>", "status": "queued" }`.
- **FR-P5-005**: The endpoint shall return HTTP 202 immediately — it shall never hold the connection open.
- **FR-P5-006**: The `ai_enabled` check (from `app_settings`) shall be performed before creating the job. If disabled, return HTTP 503.

### 7.1.2 Job Status Polling

- **FR-P5-007**: The system shall provide a `GET /api/v1/research/{job_id}/status` endpoint (JWT required).
- **FR-P5-008**: The system shall verify the job belongs to the authenticated user.
- **FR-P5-009**: The response shall include: `job_id`, `status`, `topic`, `progress` (JSONB), `confidence`, `confidence_score`, `created_at`, `updated_at`.
- **FR-P5-010**: The `progress` field shall contain:
  ```json
  {
    "current_step": "Researching sub-question 3 of 5",
    "steps_done": 2,
    "total_steps": 5,
    "current_node": "researching"
  }
  ```
- **FR-P5-011**: Valid status transitions: `queued` → `planning` → `researching` → `reflecting` → `synthesizing` → `writing` → `complete` | `failed`.
- **FR-P5-012**: The frontend shall poll every `[ENV: VITE_RESEARCH_POLL_INTERVAL_MS]` ms (default: 3000) using `setInterval`. Polling stops on `complete` or `failed`.
- **FR-P5-013**: The frontend shall render a live progress stepper showing the current active step with a loading animation, completed steps in a "done" state, and sub-question progress text from `progress.current_step` during the `researching` node.

### 7.1.3 The Research Agent (LangGraph State Machine)

- **FR-P5-014**: The research agent shall be implemented as a LangGraph `StateGraph` with the following `AgentState` fields:
  - `user_id` (str)
  - `job_id` (str)
  - `topic` (str)
  - `sub_questions` (list[str]) — generated by Planner
  - `research_findings` (dict[str, str]) — keyed by sub_question
  - `reflection_gaps` (list[str]) — identified by Reflector
  - `iteration_count` (int) — initialized to 0, max `[ENV: MAX_REFLECTION_ITERATIONS]` (default: 3)
  - `chunk_scores` (list[float]) — cosine scores from all RAG calls
  - `web_used` (bool) — True if any web search was invoked
  - `final_synthesis` (str)
  - `report_path` (str)

- **FR-P5-015**: The state machine shall contain the following nodes:

  **Planner Node:**
  - Receives the `topic`.
  - Calls the LLM to decompose the topic into `[ENV: MAX_SUB_QUESTIONS]` (default: 5) sub-questions.
  - Populates `sub_questions` in AgentState.
  - Calls `update_job_status(job_id, 'planning')`.

  **Researcher Node:**
  - Iterates over each sub-question.
  - For each: calls RAG Search, then conditionally calls Web Search (using `should_use_web_search()`).
  - Before each sub-question, updates `research_jobs.progress`: `{ "current_step": "Researching sub-question <i> of <total>", ... }`.
  - Appends results to `research_findings[sub_question]`.
  - Accumulates cosine scores into `chunk_scores`. Sets `web_used = True` if web search was used.
  - Calls `update_job_status(job_id, 'researching')`.

  **Reflector Node:**
  - Calls the LLM with all `research_findings` and the original `topic`.
  - Evaluates whether the research has coverage gaps.
  - Populates `reflection_gaps` list.
  - Increments `iteration_count`.
  - Calls `update_job_status(job_id, 'reflecting')`.

  **Conditional Edge (after Reflector):**
  - If `len(reflection_gaps) > 0 AND iteration_count < MAX_REFLECTION_ITERATIONS`: → Gap Filler Node.
  - Otherwise: → Synthesizer Node.

  **Gap Filler Node:**
  - For each identified gap, generates a targeted sub-question and calls the Researcher tools.
  - Appends new findings to `research_findings`.
  - Returns to Reflector Node.

  **Synthesizer Node:**
  - Calls the LLM with all `research_findings` to produce a coherent `final_synthesis`.
  - Calls `update_job_status(job_id, 'synthesizing')`.

  **Writer Node:**
  - Calls `docx_writer.generate_report()` with all state data.
  - Saves the DOCX to Supabase Storage (production) or local `reports/` folder (local) under `{user_id}/reports/{job_id}.docx`.
  - Updates `research_jobs` with `status = 'complete'`, `report_path`, and computed `confidence`.
  - Calls `update_job_status(job_id, 'complete')`.

  **Error Handling:**
  - Any unhandled exception in any node shall be caught, logged, and result in `update_job_status(job_id, 'failed', error_message=str(e))`.

- **FR-P5-016**: The state machine graph shall be compiled once at application startup and reused across requests.

- **FR-P5-017**: **Cancellation Check.** At the start of each node, the agent shall query `research_jobs.status` from the database. If status is `cancelled`, the node shall return immediately without further processing.

### 7.1.4 Confidence Score for Research Reports

- **FR-P5-018**: The aggregate confidence score shall be:
  ```
  base_score  = mean(chunk_scores)
  web_penalty = WEB_SEARCH_PENALTY if web_used else 0.0  [ENV, default: 0.10]
  final_score = base_score - web_penalty

  High   → final_score >= RESEARCH_CONFIDENCE_HIGH   [ENV, default: 0.70]
  Medium → final_score >= RESEARCH_CONFIDENCE_MEDIUM [ENV, default: 0.45]
  Low    → final_score < RESEARCH_CONFIDENCE_MEDIUM
  ```
- **FR-P5-019**: The confidence label and `confidence_score` float shall be stored in `research_jobs` and displayed in the frontend.

### 7.1.5 Report Generation (DOCX)

- **FR-P5-020**: The DOCX report shall contain (in order):
  1. **Title Page** — Topic, generation date, confidence label + score.
  2. **Executive Summary** — 2–3 paragraph synthesis.
  3. **Research Sub-Questions** — Numbered list.
  4. **Findings per Sub-Question** — One section per sub-question with inline citations.
  5. **Coverage Gaps Analysis** — Gaps identified and whether resolved.
  6. **Final Synthesis** — Complete narrative.
  7. **References** — Numbered list of all cited documents and web sources.
- **FR-P5-021**: Generated using `python-docx`. No paid Word API.
- **FR-P5-022**: File naming: `docmind_report_{job_id[:8]}.docx`.

### 7.1.6 Report Download

- **FR-P5-023**: The system shall provide a `GET /api/v1/research/{job_id}/download` endpoint (JWT required).
- **FR-P5-024**: The system shall verify ownership and `status = 'complete'` before serving the file.
- **FR-P5-025**: Response headers: `Content-Disposition: attachment; filename="docmind_report_{job_id[:8]}.docx"` and appropriate `Content-Type`.

### 7.1.7 Cancel Research Job

- **FR-P5-026**: The system shall provide a `DELETE /api/v1/research/{job_id}` endpoint (JWT required).
- **FR-P5-027**: If the job is in any active state, set `status = 'cancelled'`. The running agent checks this flag at each node boundary (FR-P5-017).

### 7.1.8 Research Job History

- **FR-P5-028**: The system shall provide a `GET /api/v1/research/history` endpoint (JWT required) returning the most recent `[ENV: RESEARCH_JOB_HISTORY_LIMIT]` jobs (default: 3), ordered by `created_at` descending.
- **FR-P5-029**: Each record shall include: `job_id`, `topic`, `status`, `confidence`, `confidence_score`, `created_at`, `report_path`.
- **FR-P5-030**: Completed jobs shall display a download button in the frontend.

### 7.1.9 Retention Cleanup

- **FR-P5-031**: Research jobs and their DOCX files shall be deleted after `[ENV: RESEARCH_JOB_RETENTION_DAYS]` days (default: 7). Cleanup runs in the FastAPI `@app.on_event("startup")` handler, not on `/health`.

### 7.1.10 Stale Job Recovery

- **FR-P5-032**: On startup, the system shall query for any `research_jobs` in a non-terminal state where `updated_at` is older than `[ENV: STALE_JOB_TIMEOUT_MINUTES]` (default: 20) minutes. Each shall be updated to `status = 'failed'` with `error_message = 'Job was interrupted by a server restart.'`

### 7.1.11 Route Registration Order

- **FR-P5-033**: Within `research.py`, routes shall be registered in this order:
  1. `POST /api/v1/research` — start job
  2. `GET /api/v1/research/history` — list history (**before `/{job_id}` routes**)
  3. `GET /api/v1/research/{job_id}/status` — poll status
  4. `GET /api/v1/research/{job_id}/download` — download report
  5. `DELETE /api/v1/research/{job_id}` — cancel/delete

  FastAPI matches routes in registration order. If `/{job_id}/status` is registered before `/history`, `"history"` gets captured as the `job_id` parameter.

### 7.1.12 Frontend Research Components

- **FR-P5-034**: `ResearchInput.tsx` shall render a topic input form validated with Zod (max 300 chars, non-empty). Submission disabled while a job is active.
- **FR-P5-035**: `ProgressStepper.tsx` shall render a vertical 7-step progress display: `queued → planning → researching → reflecting → synthesizing → writing → complete`. The active step shows a loading animation. During `researching`, sub-question progress text is displayed.
- **FR-P5-036**: `JobHistoryPanel.tsx` shall render past research jobs with topic, status, date, and a download button for completed jobs.
- **FR-P5-037**: `ReportDownloadCard.tsx` shall display the confidence badge and a download button that triggers file download via the download endpoint.

---

## 7.2 Backend Files Introduced

| File | Purpose |
|------|---------|
| `agent/graph.py` | LangGraph StateGraph definition + compilation |
| `agent/nodes/planner.py` | Planner node |
| `agent/nodes/researcher.py` | Researcher node |
| `agent/nodes/reflector.py` | Reflector node |
| `agent/nodes/gap_filler.py` | Gap Filler node |
| `agent/nodes/synthesizer.py` | Synthesizer node |
| `agent/nodes/writer.py` | Writer node |
| `report/docx_writer.py` | python-docx report generator |
| `repositories/research_repository.py` | Research jobs CRUD |
| `services/research_service.py` | Job orchestration, status updates, cleanup |
| `api/v1/routers/research.py` | 5 research endpoints (ordered correctly) |
| `api/v1/models/research_models.py` | Pydantic models |

## 7.3 Frontend Files Introduced

| File | Purpose |
|------|---------|
| `src/components/research/ResearchInput.tsx` | Topic input form |
| `src/components/research/ProgressStepper.tsx` | Animated progress stepper |
| `src/components/research/JobHistoryPanel.tsx` | Past jobs list |
| `src/components/research/ReportDownloadCard.tsx` | Download card + confidence |
| `src/api/research.api.ts` | Research API calls |
| `src/lib/validators/researchSchema.ts` | Zod schema for topic input |

## 7.4 Environment Variables Introduced

| Variable | Description | Default |
|----------|-------------|---------|
| `MAX_RESEARCH_TOPIC_LENGTH` | Max topic input length | `300` |
| `MAX_SUB_QUESTIONS` | Sub-questions generated by Planner | `5` |
| `MAX_REFLECTION_ITERATIONS` | Max reflect/gap-fill cycles | `3` |
| `RESEARCH_JOB_HISTORY_LIMIT` | Past jobs shown in history | `3` |
| `RESEARCH_JOB_RETENTION_DAYS` | Days before job auto-deleted | `7` |
| `STALE_JOB_TIMEOUT_MINUTES` | Minutes before stuck job marked failed | `20` |
| `RESEARCH_CONFIDENCE_HIGH` | Threshold for "high" confidence | `0.70` |
| `RESEARCH_CONFIDENCE_MEDIUM` | Threshold for "medium" confidence | `0.45` |
| `WEB_SEARCH_PENALTY` | Confidence penalty when web search used | `0.10` |
| `VITE_RESEARCH_POLL_INTERVAL_MS` | Frontend polling interval (ms) | `3000` |

---

## 7.5 Verification Checklist

| # | Test | Expected Result |
|---|------|-----------------|
| 1 | `POST /api/v1/research` with valid topic | 202 + `{ job_id, status: "queued" }` |
| 2 | Submit topic > 300 chars | 400 Bad Request |
| 3 | Submit while another job is active | 409 Conflict |
| 4 | Poll `GET /api/v1/research/{job_id}/status` repeatedly | Status progresses: queued → planning → researching → reflecting → synthesizing → writing → complete |
| 5 | During `researching`, check `progress` field | `{ current_step: "Researching sub-question 3 of 5", ... }` |
| 6 | On `complete`, check `confidence` and `report_path` | Both populated |
| 7 | `GET /api/v1/research/{job_id}/download` | Valid DOCX file downloaded with all 7 sections |
| 8 | `DELETE /api/v1/research/{job_id}` while active | Status changes to `cancelled` |
| 9 | After cancel, agent stops at next node | No further status updates |
| 10 | `GET /api/v1/research/history` | Returns last 3 jobs, ordered by `created_at` desc |
| 11 | Insert a stuck job (updated_at = 30 min ago), restart server | Job status becomes `failed` with server restart message |
| 12 | Insert an expired job (expires_at in the past), restart server | Job record and DOCX file deleted |
| 13 | Frontend: enter topic → submit → stepper animates through states | Full visual flow works |
| 14 | Frontend: download button on complete → DOCX opens in Word | File downloads correctly |
| 15 | `GET /api/v1/research/history` route resolves (not captured by `/{job_id}`) | Returns JSON array, not 404 |

---

---

# 8. Phase 6 — Admin, Evaluation & Security Hardening

**Goal:** Admin panel for AI service control, RAGAS evaluation dashboard, per-IP rate limiting, security response headers, and lazy loading for performance.

**Git Commit Message:** `feat: phase 6 — admin, evaluation & security hardening`

**Depends On:** Phase 5 (all features operational for evaluation)

---

## 8.1 Functional Requirements

### 8.1.1 Admin Panel

- **FR-P6-001**: The system shall provide a `/admin` route in the frontend accessible to anyone who knows the URL, but actionable only with the admin password.
- **FR-P6-002**: The admin panel shall display the current AI service status (ON/OFF) fetched from `GET /api/v1/admin/status`.
- **FR-P6-003**: `GET /api/v1/admin/status` shall not require authentication. Returns `{ "ai_enabled": true/false }`.
- **FR-P6-004**: `POST /api/v1/admin/toggle` shall require `[ENV: ADMIN_PASSWORD]` in the `X-Admin-Password` request header. Wrong password returns HTTP 403 Forbidden.
- **FR-P6-005**: The toggle state shall be stored in the `app_settings` table (`key = 'ai_enabled'`, `value = 'true'` or `'false'`). This persists across server restarts.
- **FR-P6-006**: When `ai_enabled = false`, all AI endpoints (`/chat/{session_id}/messages`, `/research`, `/documents/{id}/suggested-questions`) shall return HTTP 503 before reaching the service layer.
- **FR-P6-007**: The admin panel shall display a link to the RAGAS Evaluation Dashboard (URL from `[ENV: VITE_EVAL_DASHBOARD_URL]`), opening in a new tab. The admin panel shall **not** have a "Run Evaluation" button — evaluation is triggered from within the Streamlit dashboard.

### 8.1.2 RAGAS Evaluation Dashboard

- **FR-P6-008**: The RAGAS evaluation dashboard shall be a separate Streamlit application in `eval_dashboard/`.
- **FR-P6-009**: The dashboard shall be publicly accessible (no login) in read-only mode.
- **FR-P6-010**: Triggering new evaluation runs requires entering `[ENV: ADMIN_PASSWORD]` in a password input within the Streamlit app.
- **FR-P6-011**: The dashboard shall evaluate 3 RAGAS metrics (no ground truth required):
  - **Faithfulness** — Is the answer grounded in the retrieved context?
  - **Answer Relevancy** — Is the answer relevant to the question?
  - **Context Precision** — Is the retrieved context useful?
- **FR-P6-012**: Evaluation runs against a hardcoded test dataset of `[ENV: EVAL_DATASET_SIZE]` (default: 10) Q&A pairs in `eval_dashboard/test_dataset.py`.
- **FR-P6-013**: Each metric shall be color-coded: green if score ≥ `[ENV: EVAL_PASS_THRESHOLD]` (default: 0.70), red if below.
- **FR-P6-014**: A "Live Test" feature (admin-authenticated) lets the admin type a question, calls the DocMind AI backend's Q&A endpoint at `[ENV: EVAL_BACKEND_URL]`, and displays the 3 metric scores.
- **FR-P6-015**: All evaluation results shall be stored in the `eval_results` table.
- **FR-P6-016**: The dashboard shall display a historical chart of average metric scores across past runs.

### 8.1.3 Rate Limiting

- **FR-P6-017**: The backend shall implement per-IP rate limiting using `slowapi`.
- **FR-P6-018**: Standard endpoints: `[ENV: RATE_LIMIT_REQUESTS_PER_MINUTE]` requests/min/IP (default: 30).
- **FR-P6-019**: AI endpoints (`/chat/{session_id}/messages`, `/research`): `[ENV: RATE_LIMIT_AI_REQUESTS_PER_MINUTE]` requests/min/IP (default: 10). **[COST GUARD]**
- **FR-P6-020**: When rate limit is exceeded, return HTTP 429 Too Many Requests with a `Retry-After` header.

### 8.1.4 Security Headers

- **FR-P6-021**: The backend shall set `X-Content-Type-Options: nosniff` on all responses via middleware.

### 8.1.5 Lazy Loading

- **FR-P6-022**: The `/research` page component shall be lazy-loaded using `React.lazy()` + `Suspense` with a `<Skeleton />` fallback.
- **FR-P6-023**: The `/admin` page component shall be lazy-loaded the same way.

### 8.1.6 Pagination

- **FR-P6-024**: All list endpoints that may return more than 20 items shall support pagination with `limit` and `offset` parameters. Default page size: `[ENV: DEFAULT_PAGE_SIZE]` (default: 20).

---

## 8.2 Backend Files Introduced

| File | Purpose |
|------|---------|
| `api/v1/routers/admin.py` | Admin status + toggle endpoints |
| `admin/controls.py` | `app_settings` read/write helpers |
| `middleware/rate_limiter.py` | slowapi configuration |

## 8.3 Eval Dashboard Files

| File | Purpose |
|------|---------|
| `eval_dashboard/dashboard.py` | Main Streamlit app |
| `eval_dashboard/test_dataset.py` | 10 hardcoded Q&A pairs |
| `eval_dashboard/ragas_runner.py` | RAGAS metric computation |
| `eval_dashboard/requirements.txt` | Python dependencies |
| `eval_dashboard/.env` | `EVAL_BACKEND_URL`, `ADMIN_PASSWORD` (never committed) |
| `eval_dashboard/.env.example` | Template |

## 8.4 Frontend Files Introduced

| File | Purpose |
|------|---------|
| `src/components/admin/AdminPanel.tsx` | Admin page with toggle + link |
| `src/components/admin/ToggleSwitch.tsx` | AI service toggle component |

## 8.5 Environment Variables Introduced

| Variable | Description | Default |
|----------|-------------|---------|
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | Standard rate limit | `30` |
| `RATE_LIMIT_AI_REQUESTS_PER_MINUTE` | AI endpoint rate limit | `10` |
| `DEFAULT_PAGE_SIZE` | Default pagination size | `20` |
| `EVAL_DATASET_SIZE` | Test Q&A pairs count | `10` |
| `EVAL_PASS_THRESHOLD` | Score threshold for pass/fail | `0.70` |
| `EVAL_BACKEND_URL` | Backend URL for Streamlit Live Test | `http://localhost:8000` |
| `VITE_EVAL_DASHBOARD_URL` | RAGAS dashboard URL for admin link | — |

---

## 8.6 Verification Checklist

| # | Test | Expected Result |
|---|------|-----------------|
| 1 | `GET /api/v1/admin/status` | 200 + `{ ai_enabled: true }` |
| 2 | `POST /api/v1/admin/toggle` without `X-Admin-Password` | 403 Forbidden |
| 3 | `POST /api/v1/admin/toggle` with correct password | State toggled, persisted in DB |
| 4 | Send chat message when `ai_enabled = false` | 503 Service Unavailable |
| 5 | Submit research job when `ai_enabled = false` | 503 Service Unavailable |
| 6 | Send 31 requests in 1 minute to a standard endpoint | 429 Too Many Requests on 31st |
| 7 | Send 11 requests in 1 minute to `/chat/{id}/messages` | 429 on 11th |
| 8 | Check `X-Content-Type-Options` header on any response | `nosniff` present |
| 9 | Navigate to `/research` in browser | Page loads lazily (network tab shows separate chunk) |
| 10 | Navigate to `/admin` | Page loads lazily |
| 11 | Open Streamlit dashboard | Loads read-only with historical results |
| 12 | Enter admin password in Streamlit → run evaluation | 3 metric scores computed and displayed |
| 13 | Live Test: enter question in Streamlit → see scores | Faithfulness, Relevancy, Precision shown |
| 14 | Check `eval_results` table after evaluation | New records inserted |

---

---

# 9. Phase 7 — Production Deployment

**Goal:** Deploy the complete system to Vercel (frontend), Render (backend + eval dashboard), Supabase (database + storage), and ChromaDB Cloud (vectors). Verify the full end-to-end flow on production URLs.

**Git Commit Message:** `feat: phase 7 — production deployment`

**Depends On:** Phase 6 (all features complete and locally verified)

---

## 9.1 Deployment Steps

### 9.1.1 Supabase Setup

- **FR-P7-001**: Create a Supabase project and execute the full PostgreSQL DDL (Section 13) to create all 10 tables.
- **FR-P7-002**: Create a Supabase Storage bucket named `docmind` with the following policies:
  - Authenticated users can upload to `{user_id}/` paths.
  - Authenticated users can read/delete their own files.
- **FR-P7-003**: Obtain the Supabase `URL`, `anon key`, and `service role key` for environment variables.

### 9.1.2 ChromaDB Cloud Setup

- **FR-P7-004**: Create a ChromaDB Cloud account and obtain: `CHROMA_HOST`, `CHROMA_API_KEY`, `CHROMA_TENANT`, `CHROMA_DATABASE`.

### 9.1.3 Render Backend Deployment

- **FR-P7-005**: Deploy the `backend/` directory as a Render Web Service (Python, free tier).
- **FR-P7-006**: Set the Start Command to:
  ```
  uvicorn main:app --host 0.0.0.0 --port 10000 --proxy-headers --forwarded-allow-ips="*"
  ```
  The `--proxy-headers` flag is mandatory: Render deploys behind a load balancer. Without it, all requests appear from the same proxy IP, breaking per-user rate limiting.
- **FR-P7-007**: Set all backend environment variables on Render's dashboard, including `ENVIRONMENT=production`.

### 9.1.4 Render Eval Dashboard Deployment

- **FR-P7-008**: Deploy `eval_dashboard/` as a separate Render Web Service (Python, free tier).
- **FR-P7-009**: Start Command: `streamlit run dashboard.py --server.port 10000 --server.address 0.0.0.0`.
- **FR-P7-010**: Set `EVAL_BACKEND_URL` to the Render backend URL.

### 9.1.5 Vercel Frontend Deployment

- **FR-P7-011**: Deploy `frontend/` to Vercel (auto-detected as Vite project).
- **FR-P7-012**: Set frontend environment variables on Vercel:
  - `VITE_API_URL` = Render backend URL (e.g., `https://docmind-api.onrender.com`)
  - `VITE_ENV` = `production`
  - `VITE_EVAL_DASHBOARD_URL` = Render eval dashboard URL
  - `VITE_RESEARCH_POLL_INTERVAL_MS` = `3000`

### 9.1.6 Cross-Origin Configuration

- **FR-P7-013**: Update `CORS_ORIGINS` on the backend to include the Vercel frontend URL.
- **FR-P7-014**: Update `FRONTEND_URL` to the Vercel URL (for password reset email links).
- **FR-P7-015**: Verify cookie behavior: `SameSite=None; Secure=true` works in the cross-origin Vercel→Render context.

### 9.1.7 Keep-Alive

- **FR-P7-016**: Configure UptimeRobot to ping `GET https://<render-backend>/api/v1/health` every **5 minutes**. This prevents the Render free-tier service from sleeping after 15 minutes of inactivity.
- **FR-P7-017**: Optionally configure UptimeRobot for the eval dashboard service as well.

---

## 9.2 Production Environment Variables

| Variable | Production Value |
|----------|-----------------|
| `ENVIRONMENT` | `production` |
| `DATABASE_URL` | Supabase PostgreSQL connection string |
| `CORS_ORIGINS` | `https://your-app.vercel.app` |
| `FRONTEND_URL` | `https://your-app.vercel.app` |
| `SUPABASE_URL` | `https://your-project.supabase.co` |
| `SUPABASE_ANON_KEY` | From Supabase dashboard |
| `SUPABASE_SERVICE_KEY` | From Supabase dashboard |
| `CHROMA_HOST` | `api.trychroma.com` |
| `CHROMA_API_KEY` | From ChromaDB Cloud |
| `CHROMA_TENANT` | Your tenant name |
| `CHROMA_DATABASE` | `docmind` |

All other variables (JWT keys, API keys, thresholds) remain the same as local.

---

## 9.3 Verification Checklist

| # | Test | Expected Result |
|---|------|-----------------|
| 1 | `GET https://<render-url>/api/v1/health` | `{ status: "ok", environment: "production" }` |
| 2 | Register a new user via Vercel frontend | User created in Supabase PostgreSQL |
| 3 | Login → verify cross-origin cookie set | `Set-Cookie` with `SameSite=None; Secure` |
| 4 | Upload PDF via frontend | File in Supabase Storage, chunks in ChromaDB Cloud |
| 5 | Send chat message | Response with citations from ChromaDB Cloud |
| 6 | Submit research topic → poll → download DOCX | Full flow on production |
| 7 | Admin toggle → AI disabled → chat returns 503 | Works cross-origin |
| 8 | Open Streamlit eval dashboard URL | Dashboard loads publicly |
| 9 | UptimeRobot status | Shows "UP" |
| 10 | Rate limiting with real IPs | Different users get independent rate limits |
| 11 | Refresh browser on dashboard page | Silent refresh works (cookie survives) |
| 12 | Password reset email | Email received with correct Vercel reset link |

---

---

# 10. Non-Functional Requirements

## 10.1 Performance

- **NFR-PERF-001**: Non-AI endpoints (auth, document list, chat history) shall respond within 800ms.
- **NFR-PERF-002**: RAG retrieval (ChromaDB search for top-K chunks) shall complete within 2 seconds.
- **NFR-PERF-003**: A single Q&A agent response (RAG + LLM) shall complete within 15 seconds.
- **NFR-PERF-004**: A full research job shall complete within 3 minutes (5 sub-questions, no excessive gap-filling).
- **NFR-PERF-005**: The agent shall not make redundant LLM calls. Each node calls the LLM exactly once.
- **NFR-PERF-006**: Pagination on all list endpoints returning > 20 items. Default: `[ENV: DEFAULT_PAGE_SIZE]`.
- **NFR-PERF-007**: Vite production build (`vite build`) with automatic minification and code splitting at `React.lazy()` boundaries.
- **NFR-PERF-008**: N+1 database query patterns shall be explicitly avoided. Use JOINs or batch queries.
- **NFR-PERF-009**: Image assets served in WebP format where possible.

## 10.2 Reliability

- **NFR-REL-001**: UptimeRobot shall ping the backend every **5 minutes** to prevent Render free-tier cold starts.
- **NFR-REL-002**: Research job state is persisted at each node transition. Jobs are not lost on restart — they are marked as `failed` by stale job recovery (FR-P5-032).
- **NFR-REL-003**: If a research job is interrupted, the frontend displays a "Job interrupted" message.
- **NFR-REL-004**: Document upload writes shall be atomic where possible. Partial failures trigger cleanup (FR-P3-006).
- **NFR-REL-005**: The backend shall start with `--proxy-headers --forwarded-allow-ips="*"` in production. Without this, all requests appear from the same proxy IP, breaking rate limiting.

## 10.3 Usability

- **NFR-USE-001**: All forms shall display inline validation errors next to the relevant field.
- **NFR-USE-002**: Document upload shall support drag-and-drop and click-to-browse.
- **NFR-USE-003**: All destructive actions (delete document, delete session, cancel job) require a confirmation dialog.
- **NFR-USE-004**: Loading skeletons (`<Skeleton />`) shown for document list, chat sessions, chat history, and research job history while loading.
- **NFR-USE-005**: API errors surfaced as non-blocking toast notifications (shadcn `<Sonner />`).
- **NFR-USE-006**: Fully usable from 375px (mobile) to 1920px (desktop). Mobile uses `<Sheet>` drawer for navigation.
- **NFR-USE-007**: An animated typing indicator (three bouncing dots) shall be shown in the chat window while waiting for the assistant's response. This provides immediate visual feedback without WebSocket streaming.

## 10.4 Maintainability

- **NFR-MAIN-001**: Python: `snake_case` for functions. React: `PascalCase` for components. Constants: `UPPER_SNAKE_CASE`.
- **NFR-MAIN-002**: Functions shall not exceed 50 lines.
- **NFR-MAIN-003**: No magic numbers or string literals in business logic — use env vars or named constants.
- **NFR-MAIN-004**: Backend layered pattern: `router → controller → service → repository`. No DB queries in routers.
- **NFR-MAIN-005**: Agent prompts stored in `agent/prompts.py` as named constants.
- **NFR-MAIN-006**: Predictable folder structure (Appendix B).
- **NFR-MAIN-007**: `README.md` with local setup, env var descriptions, deployment guide.

## 10.5 Scalability

- **NFR-SCALE-001**: Backend is stateless — all state in the database or JWT.
- **NFR-SCALE-002**: ChromaDB collections namespaced by `user_id`.

---

---

# 11. Security Requirements

- **SEC-001**: Passwords hashed with bcrypt, work factor `[ENV: BCRYPT_WORK_FACTOR]`.
- **SEC-002**: Password verification uses constant-time comparison (bcrypt's built-in `checkpw`).
- **SEC-003**: JWT signed with HMAC-SHA256 using `[ENV: JWT_SECRET_KEY]` (min 32 random bytes).
- **SEC-004**: Refresh Tokens stored as SHA-256 hashes. Raw token only in httpOnly cookie over HTTPS.
- **SEC-005**: Refresh Token cookie: `SameSite=None; Secure=true` in production, `SameSite=Lax; Secure=false` in local. Dynamically set from `ENVIRONMENT`.
- **SEC-006**: Access Token in React in-memory state only — not `localStorage` or `sessionStorage`.
- **SEC-007**: Login/registration errors shall not distinguish "email not found" from "wrong password" (anti-enumeration).
- **SEC-008**: Password reset tokens expire in `[ENV: PASSWORD_RESET_EXPIRE_MINUTES]` and are single-use.
- **SEC-009**: All request bodies validated via Pydantic models. Invalid input → 400.
- **SEC-010**: File uploads validated for MIME type and size at the router layer.
- **SEC-011**: String inputs stripped of whitespace and control characters.
- **SEC-012**: Email validated against RFC 5322 regex.
- **SEC-013**: Every data-access query includes `WHERE user_id = <authenticated_user_id>`. No cross-user access.
- **SEC-014**: Admin operations require `X-Admin-Password` header matching `[ENV: ADMIN_PASSWORD]`.
- **SEC-015**: All database queries use parameterized queries. No raw string interpolation into SQL.
- **SEC-016**: LLM prompts wrap user-supplied content in XML delimiters to reduce prompt injection risk.
- **SEC-017**: React's default JSX escaping for user content. `dangerouslySetInnerHTML` prohibited unless sanitized with DOMPurify.
- **SEC-018**: `X-Content-Type-Options: nosniff` on all responses.
- **SEC-019**: CORS origins from `[ENV: CORS_ORIGINS]`. Wildcard `*` never used in production.
- **SEC-020**: Only `GET`, `POST`, `PATCH`, `DELETE` in CORS `allow_methods`.
- **SEC-021**: All production traffic over HTTPS (Vercel + Render provide automatic HTTPS).
- **SEC-022**: No secrets in source code, committed config files, or log output.
- **SEC-023**: `.env` in `.gitignore`. Never committed.
- **SEC-024**: `.env.example` committed with placeholder values.
- **SEC-025**: Production secrets set via Render/Vercel dashboards — not files.
- **SEC-026**: Per-IP rate limiting via slowapi on all endpoints.
- **SEC-027**: Standard limit: `[ENV: RATE_LIMIT_REQUESTS_PER_MINUTE]` (default: 30).
- **SEC-028**: AI limit: `[ENV: RATE_LIMIT_AI_REQUESTS_PER_MINUTE]` (default: 10). **[COST GUARD]**
- **SEC-029**: Rate limit exceeded → 429 + `Retry-After` header.
- **SEC-030**: Request logging at INFO: timestamp, method, path, status, response time (ms).
- **SEC-031**: Error logging at ERROR: timestamp, endpoint, error type, sanitized message. Stack traces in dev only.
- **SEC-032**: Logs shall never contain: JWT tokens, passwords, password hashes, API keys, or PII beyond `user_id`.
- **SEC-033**: Python `logging` module. JSON format in production.

---

---

# 12. System Architecture

## 12.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT (Browser)                          │
│          React SPA — deployed on Vercel                      │
│   Auth Context │ API Client (Axios) │ Component Tree        │
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
│                         │                                   │
│  ┌──────────────────────▼──────────────────────────────┐    │
│  │  Service Layer — business logic                      │    │
│  │  auth_service │ doc_service │ chat_service           │    │
│  │  research_service │ admin_controls                   │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │                                   │
│  ┌──────────────────────▼──────────────────────────────┐    │
│  │  Repository Layer — database queries only            │    │
│  │  user_repo │ token_repo │ document_repo │ chat_repo │    │
│  │  research_repo                                      │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │                                   │
│  ┌──────────────────────▼──────────────────────────────┐    │
│  │  Agent Layer (LangGraph + LangChain)                 │    │
│  │  graph.py │ tools.py │ prompts.py │ nodes/          │    │
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
   │PostgreSQL│       │ ChromaDB    │    │  Gemini API │
   │(Supabase)│       │   Cloud     │    │  + Tavily   │
   │+ Storage │       │(Vector DB)  │    │             │
   └──────────┘       └─────────────┘    └─────────────┘
```

## 12.2 Backend Layered Architecture

- **Routers** (`/api/v1/...`): Define HTTP routes, apply middleware (JWT, rate limiting). No business logic.
- **Services** (`/services/`): All business logic. Coordinate repositories, agents, external APIs. Not HTTP-aware.
- **Repositories** (`/repositories/`): All database queries. Accept/return domain objects. No business logic.
- **Agent** (`/agent/`): LangGraph graph, tools, prompts. Called by `research_service` and `chat_service`.
- **RAG** (`/rag/`): Chunk indexing and vector retrieval. Called by `doc_service` and agent tools.

## 12.3 Frontend Architecture

### 12.3.1 Component Organization

- **shadcn/ui primitives** (`src/components/ui/`): Auto-generated via `npx shadcn-ui add`. Never hand-written.
- **Feature components** (`src/components/<feature>/`): Organized by domain (auth, documents, chat, research, admin, shared).

### 12.3.2 State Management

- **Global**: `AuthContext` for access token + user profile.
- **Feature-level**: `useState` / `useReducer` within feature components.
- **Forms**: React Hook Form + Zod. Schemas in `src/lib/validators/`.
- No Redux/Zustand for v1.

### 12.3.3 API Client

- Single Axios instance in `src/api/client.ts`.
- `baseURL = import.meta.env.VITE_API_URL` (Vite uses `import.meta.env`, not `process.env`).
- Request interceptor: attaches `Authorization: Bearer <token>`.
- Response interceptor: catches 401, calls refresh, retries once.
- `withCredentials: true` for cross-origin cookies.
- API functions in `src/api/*.api.ts` — no raw Axios calls in components.

### 12.3.4 UI Design Language

- **Component Library**: shadcn/ui for all primitives.
- **Styling**: Tailwind CSS utility classes only. No custom CSS except `globals.css`.
- **Color Palette**: Background `neutral-50/white`, surface cards with `border-neutral-200 shadow-sm rounded-xl`, primary accent muted indigo `#5B6CF6`.
- **Typography**: DM Sans / Plus Jakarta Sans. Body `text-sm`/`text-base`. Headings `font-semibold`.
- **Icons**: `lucide-react` (shadcn/ui dependency).
- **Cards**: shadcn `<Card>` with `rounded-xl border border-neutral-200 shadow-sm`.
- **Loading**: shadcn `<Skeleton />` for all loading states.
- **Toasts**: shadcn `<Sonner />` for notifications.
- **Dialogs**: shadcn `<AlertDialog>` for destructive confirmations.
- **Forms**: shadcn `<Input>` + `<Label>` + `<Button>` with React Hook Form + Zod.
- **Mobile**: Collapse to hamburger-menu `<Sheet>` drawer at `md` (768px) breakpoint.

## 12.4 Agent Architecture (LangGraph)

```
[START] → planner → researcher → reflector ──┬── (gaps & iter < max) → gap_filler → reflector
                                              └── (no gaps or iter ≥ max) → synthesizer → writer → [END]
```

Each node is an async function accepting `AgentState` and returning a partial state update. The graph is compiled once at startup.

## 12.5 Deployment Architecture

```
GitHub (main branch)
        │
        ├──[push]──► Vercel Build (frontend/)
        │              └── npm run build → deploys to Vercel CDN
        │
        ├──[push]──► Render Build (backend/)
        │              └── pip install → uvicorn start
        │
        └──[push]──► Render Build (eval_dashboard/)
                       └── pip install → streamlit start

UptimeRobot → GET https://<render-backend>/api/v1/health (every 5 min)
```

---

---

# 13. Data Design

## 13.1 Database Schema

The database engine is **PostgreSQL** in both local and production environments. Local uses a local PostgreSQL instance; production uses Supabase PostgreSQL.

---

### Table: `users`

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

```sql
CREATE TABLE refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  TEXT NOT NULL UNIQUE,
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

```sql
CREATE TABLE documents (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename      TEXT NOT NULL,
    storage_path  TEXT NOT NULL,
    chunk_count   INTEGER NOT NULL DEFAULT 0,
    file_size_kb  INTEGER,
    uploaded_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
    -- No updated_at: documents are immutable after upload.
    -- UI displays "Uploaded on <date>", not "Last modified".
);

CREATE INDEX idx_documents_user_id ON documents (user_id);
```

---

### Table: `suggested_questions`

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

```sql
CREATE TABLE chat_messages (
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

CREATE INDEX idx_chat_messages_session_id ON chat_messages (session_id);
CREATE INDEX idx_chat_messages_user_id ON chat_messages (user_id);
```

---

### Table: `research_jobs`

```sql
CREATE TABLE research_jobs (
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

CREATE INDEX idx_research_jobs_user_id ON research_jobs (user_id);
CREATE INDEX idx_research_jobs_status ON research_jobs (status);
CREATE INDEX idx_research_jobs_expires_at ON research_jobs (expires_at);
```

---

### Table: `app_settings`

```sql
CREATE TABLE app_settings (
    key    TEXT PRIMARY KEY,
    value  TEXT NOT NULL
);

INSERT INTO app_settings (key, value) VALUES ('ai_enabled', 'true');
```

---

### Table: `eval_results`

```sql
CREATE TABLE eval_results (
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

CREATE INDEX idx_eval_results_run_id ON eval_results (run_id);
```

---

## 13.2 ChromaDB Collection Design

- **Collection naming**: `user_{user_id_no_hyphens}` — hyphens replaced with underscores via `get_collection_name()` in `rag/retriever.py`.
- **Chunk metadata**:
  ```json
  {
    "document_id": "<uuid>",
    "filename": "paper.pdf",
    "page_number": 3,
    "chunk_index": 12,
    "user_id": "<uuid>"
  }
  ```
- On document deletion, vectors with `metadata.document_id == <deleted_id>` are removed via ChromaDB's `where` filter.

## 13.3 Data Flow Diagrams

### Document Upload Flow
```
User → POST /api/v1/documents/upload (PDF)
  → Router (JWT, rate limit)
  → Service: doc_service.upload()
      → storage.save_file()       → Supabase Storage / local
      → rag.indexer.index_pdf()   → extract → chunk → embed → ChromaDB
      → document_repository.create()   → PostgreSQL
      → doc_service.generate_suggested_questions() → LLM → suggested_questions table
  ← HTTP 201 { document, suggested_questions }
```

### Q&A Chat Flow
```
User → POST /api/v1/chat/{session_id}/messages { query }
  → Router (JWT, rate limit)
  → Service: chat_service.send_message()
      → chat_repository.save_user_message()
      → chat_repository.get_recent_messages(CHAT_CONTEXT_WINDOW)
      → Q&A Agent:
          → rag_search tool → ChromaDB
          → web_search tool → Tavily (conditional)
          → LLM synthesis
      → chat_repository.save_assistant_message()
  ← HTTP 200 { message, sources, confidence, tools_used }
```

### Deep Research Flow
```
User → POST /api/v1/research { topic }
  → Router (JWT, rate limit)
  → Service: research_service.start_job()
      → research_repository.create_job(status: queued)
      → BackgroundTasks.add_task(run_research_agent)
  ← HTTP 202 { job_id, status: "queued" }

[Background] run_research_agent(job_id, topic, user_id)
  → LangGraph: planner → researcher → reflector → [gap_filler] → synthesizer → writer
  → Each node: update_job_status(job_id, <status>)
  → Writer: docx_writer.generate() → Storage
  → research_repository.complete_job(report_path, confidence)

User → GET /api/v1/research/{job_id}/status [poll every 3s]
  ← { status, progress, confidence }

User → GET /api/v1/research/{job_id}/download
  ← DOCX file stream
```

---

---

# 14. API Design

## 14.1 Conventions

- **Base Path**: `/api/v1/`
- **Format**: JSON for all request/response bodies (except file upload/download).
- **Authentication**: Protected endpoints require `Authorization: Bearer <access_token>`.
- **Standard HTTP Status Codes**:

| Code | Meaning |
|------|---------|
| 200 | Successful read/update |
| 201 | Resource created |
| 202 | Async job accepted |
| 400 | Validation failure |
| 401 | Missing/invalid JWT |
| 403 | Authenticated but unauthorized |
| 404 | Resource not found |
| 409 | Duplicate/business rule conflict |
| 413 | File too large |
| 415 | Wrong file type |
| 429 | Rate limit exceeded |
| 503 | AI service disabled |

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

## 14.2 Complete Endpoint Reference

### Authentication (Phase 2)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/register` | None | Register new user |
| POST | `/api/v1/auth/login` | None | Login → access token + refresh cookie |
| POST | `/api/v1/auth/refresh` | Cookie | Exchange refresh token for new access token |
| POST | `/api/v1/auth/logout` | JWT | Revoke refresh token, clear cookie |
| POST | `/api/v1/auth/forgot-password` | None | Send password reset email |
| POST | `/api/v1/auth/reset-password` | None | Reset password with token |

### Documents (Phase 3)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/documents/upload` | JWT | Upload + index PDF |
| GET | `/api/v1/documents` | JWT | List user's documents |
| DELETE | `/api/v1/documents/{document_id}` | JWT | Delete document from all layers |
| GET | `/api/v1/documents/{document_id}/suggested-questions` | JWT | Get/generate questions |

### Chat (Phase 4)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/chat/sessions` | JWT | Create new session |
| GET | `/api/v1/chat/sessions` | JWT | List all sessions |
| PATCH | `/api/v1/chat/sessions/{session_id}` | JWT | Rename session |
| DELETE | `/api/v1/chat/sessions/{session_id}` | JWT | Delete session + messages |
| POST | `/api/v1/chat/{session_id}/messages` | JWT | Send message, get AI response |
| GET | `/api/v1/chat/{session_id}/messages` | JWT | Get messages (paginated) |
| DELETE | `/api/v1/chat/messages/{message_id}` | JWT | Delete a message |

### Research (Phase 5)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/research` | JWT | Start research job (202) |
| GET | `/api/v1/research/history` | JWT | List past jobs |
| GET | `/api/v1/research/{job_id}/status` | JWT | Poll job progress |
| GET | `/api/v1/research/{job_id}/download` | JWT | Download DOCX report |
| DELETE | `/api/v1/research/{job_id}` | JWT | Cancel/delete job |

> **Route Order**: `/research/history` MUST be registered before `/{job_id}` routes.

### Admin (Phase 6)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/admin/status` | None | Get AI on/off status |
| POST | `/api/v1/admin/toggle` | Admin Header | Toggle AI service |

### System (Phase 1)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/health` | None | Health check |

---

---

# 15. Configuration & Environment

## 15.1 Principle

Every configurable value resides in environment variables. No value is hardcoded. All defaults are documented in `.env.example`.

## 15.2 Environment Switching

| `ENVIRONMENT` | Database | File Storage | Vector DB | Embeddings |
|---------------|----------|-------------|-----------|------------|
| `local` | Local PostgreSQL | Local filesystem | ChromaDB local | Gemini Embeddings API |
| `production` | Supabase PostgreSQL | Supabase Storage | ChromaDB Cloud | Gemini Embeddings API |

Both environments use Gemini Embeddings to guarantee vector space compatibility.

## 15.3 Frontend Variables

Vite requires the `VITE_` prefix for all browser-accessible variables. Access via `import.meta.env.VITE_*`.

| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | Backend base URL |
| `VITE_ENV` | `development` or `production` |
| `VITE_EVAL_DASHBOARD_URL` | RAGAS Streamlit dashboard URL |
| `VITE_RESEARCH_POLL_INTERVAL_MS` | Research polling interval (ms) |

## 15.4 Complete Variable Reference

See **Appendix A** for the full `.env.example` with all variables, descriptions, and defaults.

---

---

# 16. Constraints

- **CON-001**: Zero monthly cost using free tiers of Vercel, Render, Supabase, ChromaDB Cloud.
- **CON-002**: No paid cloud services required.
- **CON-003**: No Celery, Redis, or message brokers. Async via FastAPI `BackgroundTasks`.
- **CON-004**: ChromaDB only. No Pinecone, Weaviate, Qdrant.
- **CON-005**: Google Gemini 2.5 Flash only. No multi-provider LLM switching.
- **CON-006**: Single GitHub repo with `frontend/`, `backend/`, `eval_dashboard/` subdirectories.
- **CON-007**: Supabase Auth explicitly excluded. Custom JWT auth only.
- **CON-008**: PDF only for uploads. No DOCX, TXT, or other document formats.
- **CON-009**: One active research job per user. **[COST GUARD]**
- **CON-010**: `MAX_DOCUMENTS_PER_USER` is a hard limit. **[COST GUARD]**
- **CON-011**: Render free tier sleeps after 15 min. UptimeRobot (5 min pings) mitigates.
- **CON-012**: No WebSocket/SSE streaming. All responses are request-response. Typing indicator provides UX feedback.
- **CON-013**: PostgreSQL only. No SQLite. Local dev requires a local PostgreSQL instance.

---

---

# 17. Assumptions & Dependencies

| # | Assumption / Dependency |
|---|-------------------------|
| A-01 | Google Gemini API free tier (AI Studio) provides sufficient quota. |
| A-02 | Tavily free tier (1,000 searches/month) sufficient for dev and demo. |
| A-03 | Supabase free tier (500 MB DB, 1 GB Storage) not exceeded. |
| A-04 | ChromaDB Cloud free tier provides adequate storage and query volume. |
| A-05 | All uploaded PDFs are text-extractable (not scanned images). |
| A-06 | Frontend deployed to Vercel with auto-generated URL. |
| A-07 | UptimeRobot pings every **5 minutes**. |
| A-08 | RAGAS metrics (Faithfulness, Answer Relevancy, Context Precision) do not require ground truth. |
| A-09 | Email service available (Resend free tier or Gmail SMTP app password). |
| A-10 | `python-docx` is sufficient for DOCX generation. |
| A-11 | Dev environment has Python 3.11+, Node.js 18+, and PostgreSQL 14+. |
| A-12 | GitHub manual or auto-deploy is acceptable. |

---

---

# Appendix A — `.env.example`

```bash
# =============================================================
# DocMind AI — Environment Configuration
# Copy to .env and fill in actual values. NEVER commit .env.
# =============================================================

# ─── ENVIRONMENT ─────────────────────────────────────────────
# "local"      → Local PostgreSQL + local filesystem + local ChromaDB
# "production" → Supabase PostgreSQL + Supabase Storage + ChromaDB Cloud
ENVIRONMENT=local

APP_VERSION=1.0.0

# ─── DATABASE ────────────────────────────────────────────────
# Local:      postgresql://postgres:postgres@localhost:5432/docmind
# Production: postgresql://postgres.<ref>:<password>@<host>:5432/postgres
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/docmind

# ─── CORS ────────────────────────────────────────────────────
# Local:      http://localhost:5173
# Production: https://your-app.vercel.app
CORS_ORIGINS=http://localhost:5173

# ─── JWT / AUTH ──────────────────────────────────────────────
# Generate: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY=your_super_secret_key_here_minimum_32_chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
PASSWORD_RESET_EXPIRE_MINUTES=30
BCRYPT_WORK_FACTOR=12
PASSWORD_MIN_LENGTH=8

# Admin password for /admin panel and RAGAS dashboard
ADMIN_PASSWORD=your_admin_password_here

# ─── LLM ─────────────────────────────────────────────────────
# Required in BOTH local and production (Gemini Embeddings used everywhere)
GEMINI_API_KEY=your_gemini_api_key_from_aistudio

# ─── WEB SEARCH ──────────────────────────────────────────────
TAVILY_API_KEY=your_tavily_api_key

# ─── SUPABASE (production only) ──────────────────────────────
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_role_key

# ─── CHROMADB ────────────────────────────────────────────────
# Local:      leave CHROMA_HOST blank — uses local persistent storage
# Production: set all four values from ChromaDB Cloud dashboard
CHROMA_HOST=
CHROMA_API_KEY=
CHROMA_TENANT=
CHROMA_DATABASE=

# ─── EMAIL (password reset) ──────────────────────────────────
EMAIL_PROVIDER=resend
RESEND_API_KEY=your_resend_api_key
EMAIL_FROM_ADDRESS=noreply@yourdomain.com
# If using SMTP instead:
# EMAIL_PROVIDER=smtp
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=your_gmail@gmail.com
# SMTP_PASSWORD=your_gmail_app_password

# Frontend URL (used in password reset email links)
# Local:      http://localhost:5173
# Production: https://your-app.vercel.app
FRONTEND_URL=http://localhost:5173

# ─── DOCUMENT MANAGEMENT ─────────────────────────────────────
MAX_PDF_SIZE_MB=10
MAX_DOCUMENTS_PER_USER=5
SUGGESTED_QUESTIONS_COUNT=5

# ─── RAG CONFIGURATION ───────────────────────────────────────
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
RAG_TOP_K=5

# Cosine threshold below which web search triggers (both Mode 1 and Mode 2)
WEB_SEARCH_FALLBACK_THRESHOLD=0.50

# ─── CHAT (MODE 1) ───────────────────────────────────────────
CHAT_CONTEXT_WINDOW=10
CHAT_HISTORY_LIMIT=10
MAX_CHAT_QUERY_LENGTH=2000
SESSION_TITLE_MAX_LENGTH=50
MAX_SESSIONS_PER_USER=20

# ─── CONFIDENCE ──────────────────────────────────────────────
CONFIDENCE_HIGH_THRESHOLD=0.75
CONFIDENCE_MEDIUM_THRESHOLD=0.50
RESEARCH_CONFIDENCE_HIGH=0.70
RESEARCH_CONFIDENCE_MEDIUM=0.45
WEB_SEARCH_PENALTY=0.10

# ─── DEEP RESEARCH (MODE 2) ──────────────────────────────────
MAX_RESEARCH_TOPIC_LENGTH=300
MAX_SUB_QUESTIONS=5
MAX_REFLECTION_ITERATIONS=3
RESEARCH_JOB_HISTORY_LIMIT=3
RESEARCH_JOB_RETENTION_DAYS=7
STALE_JOB_TIMEOUT_MINUTES=20

# ─── RATE LIMITING ───────────────────────────────────────────
RATE_LIMIT_REQUESTS_PER_MINUTE=30
RATE_LIMIT_AI_REQUESTS_PER_MINUTE=10

# ─── PAGINATION ──────────────────────────────────────────────
DEFAULT_PAGE_SIZE=20

# ─── RAGAS EVALUATION ────────────────────────────────────────
# These go in eval_dashboard/.env (separate from backend .env)
EVAL_DATASET_SIZE=10
EVAL_PASS_THRESHOLD=0.70
# Backend URL for Streamlit Live Test
# Local:      http://localhost:8000
# Production: https://your-backend.onrender.com
EVAL_BACKEND_URL=http://localhost:8000

# ─── FRONTEND (.env in frontend/) ────────────────────────────
# Vite requires VITE_ prefix for browser-accessible vars
# VITE_API_URL=http://localhost:8000
# VITE_ENV=development
# VITE_EVAL_DASHBOARD_URL=https://your-eval-dashboard.onrender.com
# VITE_RESEARCH_POLL_INTERVAL_MS=3000
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
│   ├── index.html                     # Vite entry point (Google Fonts import)
│   ├── vite.config.ts                 # Path aliases (@/ → src/)
│   ├── tailwind.config.ts             # Content paths, theme (colours, font)
│   ├── postcss.config.js
│   ├── tsconfig.json                  # Path aliases
│   ├── components.json                # shadcn/ui config
│   ├── src/
│   │   ├── main.tsx                   # React DOM root
│   │   ├── App.tsx                    # Routes + lazy loading
│   │   ├── api/
│   │   │   ├── client.ts             # Axios instance + interceptors
│   │   │   ├── auth.api.ts           # Auth API calls
│   │   │   ├── documents.api.ts      # Document API calls
│   │   │   ├── chat.api.ts           # Chat API calls
│   │   │   └── research.api.ts       # Research API calls
│   │   ├── auth/
│   │   │   └── AuthContext.tsx        # React Context: token, user, login/logout/refresh
│   │   ├── components/
│   │   │   ├── ui/                    # shadcn/ui primitives (auto-generated)
│   │   │   │   ├── button.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   ├── dialog.tsx
│   │   │   │   ├── alert-dialog.tsx
│   │   │   │   ├── sheet.tsx
│   │   │   │   ├── skeleton.tsx
│   │   │   │   ├── badge.tsx
│   │   │   │   ├── sonner.tsx
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
│   │   │   │   ├── DocumentPanel.tsx
│   │   │   │   ├── DocumentCard.tsx
│   │   │   │   ├── UploadDropzone.tsx
│   │   │   │   └── SuggestedQuestions.tsx
│   │   │   ├── chat/
│   │   │   │   ├── ChatWindow.tsx
│   │   │   │   ├── MessageBubble.tsx
│   │   │   │   ├── SessionSidebar.tsx
│   │   │   │   ├── CitationBlock.tsx
│   │   │   │   ├── ConfidenceBar.tsx
│   │   │   │   └── ToolBadge.tsx
│   │   │   ├── research/
│   │   │   │   ├── ResearchInput.tsx
│   │   │   │   ├── ProgressStepper.tsx
│   │   │   │   ├── JobHistoryPanel.tsx
│   │   │   │   └── ReportDownloadCard.tsx
│   │   │   ├── admin/
│   │   │   │   ├── AdminPanel.tsx
│   │   │   │   └── ToggleSwitch.tsx
│   │   │   └── shared/
│   │   │       └── ConfirmDialog.tsx
│   │   ├── lib/
│   │   │   ├── utils.ts               # shadcn cn() utility
│   │   │   └── validators/
│   │   │       ├── loginSchema.ts
│   │   │       ├── registerSchema.ts
│   │   │       ├── researchSchema.ts
│   │   │       └── chatSchema.ts
│   │   └── styles/
│   │       └── globals.css
│   ├── .env.example
│   └── package.json
│
├── backend/                           # FastAPI → Render
│   ├── main.py                        # App factory: CORS, rate limiter, routers, startup events
│   ├── config.py                      # ENVIRONMENT switch, typed settings
│   ├── api/
│   │   └── v1/
│   │       ├── routers/
│   │       │   ├── auth.py
│   │       │   ├── documents.py
│   │       │   ├── chat.py
│   │       │   ├── research.py        # history route BEFORE /{job_id} routes
│   │       │   ├── admin.py
│   │       │   └── health.py
│   │       └── models/
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
│   │   └── db_client.py              # PostgreSQL connection (reads DATABASE_URL)
│   ├── storage/
│   │   ├── supabase_storage.py
│   │   └── local_storage.py
│   ├── agent/
│   │   ├── graph.py                   # LangGraph StateGraph
│   │   ├── nodes/
│   │   │   ├── planner.py
│   │   │   ├── researcher.py
│   │   │   ├── reflector.py
│   │   │   ├── gap_filler.py
│   │   │   ├── synthesizer.py
│   │   │   └── writer.py
│   │   ├── tools.py                   # rag_search, web_search tools
│   │   └── prompts.py                 # All LLM prompt constants
│   ├── rag/
│   │   ├── indexer.py                 # PDF → chunks → embeddings → ChromaDB
│   │   └── retriever.py              # Semantic search + get_collection_name() + should_use_web_search()
│   ├── report/
│   │   └── docx_writer.py
│   ├── auth/
│   │   ├── jwt_handler.py
│   │   ├── password_handler.py
│   │   └── dependencies.py
│   ├── admin/
│   │   └── controls.py
│   ├── email/
│   │   └── email_sender.py
│   ├── middleware/
│   │   └── rate_limiter.py
│   ├── utils/
│   │   └── logger.py
│   ├── requirements.txt
│   └── .env                           # never committed
│
├── eval_dashboard/                    # Streamlit → separate Render service
│   ├── dashboard.py
│   ├── test_dataset.py
│   ├── ragas_runner.py
│   ├── requirements.txt
│   ├── .env                           # never committed
│   └── .env.example
│
├── .gitignore
├── .env.example                       # Backend env template
└── README.md
```

---

---

# Appendix C — Glossary

| Term | Definition |
|------|-----------|
| Access Token | Short-lived JWT (15 min) in `Authorization` header for API auth |
| Refresh Token | Long-lived opaque token (7 days) in httpOnly cookie for session renewal |
| RAG | Retrieval-Augmented Generation — vector search + LLM synthesis |
| Chunk | Fixed-size text segment from a PDF, stored as a vector in ChromaDB |
| Cosine Similarity | 0–1 measure of vector similarity for ranking retrieved chunks |
| LangGraph | Library for stateful multi-step AI agents as directed graphs |
| AgentState | Typed dict carrying data through the LangGraph state machine |
| httpOnly Cookie | Browser cookie inaccessible to JavaScript, carries refresh token |
| Prompt Injection | Attack where user input hijacks LLM instructions. Mitigated by XML delimiters |
| N+1 Problem | DB anti-pattern: N records each trigger a separate query instead of one batch |
| RAGAS | Open-source RAG evaluation framework |
| UptimeRobot | Free ping service preventing Render free-tier cold starts |
| BackgroundTasks | FastAPI mechanism to run functions after HTTP response is sent |
| Token Rotation | Security strategy: each refresh token use invalidates old + issues new |
| CORS | Browser security mechanism controlling which origins may call the backend |
| slowapi | Python rate-limiting library for FastAPI |
| Typing Indicator | Animated bouncing dots shown in chat while awaiting AI response |

---

*End of Software Requirements Specification — DocMind AI v2.0 (Phase-Wise Implementation)*
