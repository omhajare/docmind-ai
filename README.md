# DocMind AI — AI Research & Synthesis Agent

A full-stack AI-powered research assistant with two core modes:

1. **Mode 1: Conversational Q&A** — Upload PDFs, ask questions, get RAG-powered answers with citations.
2. **Mode 2: Deep Research** — Submit a topic, get an autonomously generated DOCX research report.

## Tech Stack

| Layer       | Technology                                      |
|-------------|-------------------------------------------------|
| Frontend    | React 18 + Vite + TypeScript + Tailwind + shadcn/ui |
| Backend     | Python 3.11+ / FastAPI                          |
| Database    | PostgreSQL (local) / Supabase PostgreSQL (prod) |
| Vector DB   | ChromaDB (local) / ChromaDB Cloud (prod)        |
| LLM         | Google Gemini 2.5 Flash + Gemini Embeddings     |
| Web Search  | Tavily API                                      |
| Eval        | Streamlit + RAGAS                               |

## Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 14+** (running locally)

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/docmind-ai.git
cd docmind-ai
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Create local PostgreSQL database
# (connect to psql and run:)
# CREATE DATABASE docmind;

# Configure environment
cp ../.env.example .env
# Edit .env with your DATABASE_URL and other values

# Start the server
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env

# Start dev server
npm run dev
```

### 4. Verify

- Backend health: `GET http://localhost:8000/api/v1/health`
- Frontend: `http://localhost:5173`

## Environment Variables

Copy `.env.example` to `.env` in the project root (for backend) and `frontend/.env.example` to `frontend/.env` (for frontend).

Key variables:

| Variable | Description |
|----------|-------------|
| `ENVIRONMENT` | `local` or `production` |
| `DATABASE_URL` | PostgreSQL connection string |
| `GEMINI_API_KEY` | Google Gemini API key (required in both envs) |
| `TAVILY_API_KEY` | Tavily web search API key |
| `JWT_SECRET_KEY` | Secret for signing JWTs |
| `CORS_ORIGINS` | Allowed frontend origins |

See `.env.example` for the full list with defaults.

## Project Structure

```
docmind-ai/
├── frontend/          # React + Vite + Tailwind + shadcn/ui
├── backend/           # FastAPI + LangGraph + RAG
├── eval_dashboard/    # Streamlit + RAGAS (Phase 6)
├── .env.example       # Backend env template
├── .gitignore
└── README.md
```

## Development Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Project Foundation & Configuration | ✅ |
| 2 | Authentication System | ⬜ |
| 3 | Document Management & RAG Pipeline | ⬜ |
| 4 | Conversational Q&A (Mode 1) | ⬜ |
| 5 | Deep Research Agent (Mode 2) | ⬜ |
| 6 | Admin, Evaluation & Security | ⬜ |
| 7 | Production Deployment | ⬜ |

## Deployment

- **Frontend** → Vercel
- **Backend** → Render (start: `uvicorn main:app --host 0.0.0.0 --port 10000 --proxy-headers --forwarded-allow-ips="*"`)
- **Database** → Supabase PostgreSQL
- **Vectors** → ChromaDB Cloud
- **Eval Dashboard** → Render (Streamlit)
- **Keep-alive** → UptimeRobot (5 min ping)
