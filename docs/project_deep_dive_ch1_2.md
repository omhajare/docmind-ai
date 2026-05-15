# PROJECT DEEP DIVE — DocMind AI

> Written after reading every single file in this repository. Every claim is backed by actual code. Nothing is guessed.

---

# CHAPTER 1: WHY THIS PROJECT EXISTS

Imagine you are a university researcher. You have 15 PDF papers on your desk about transformer architectures. You need to write a literature review. So you open each paper, skim it, highlight sentences, tab between them, copy quotes into a Google Doc, and try to stitch together a coherent narrative. It takes you three days. Half the time you are not even thinking — you are just searching, scrolling, finding which paper said what.

Now imagine someone hands you a tool. You drop all 15 PDFs into it. You type: "What are the key differences between attention mechanisms discussed across these papers?" And in under ten seconds, the tool reads every paper, finds the relevant paragraphs, cites exactly which paper and which page each fact came from, tells you how confident it is in the answer, and if your papers don't cover something, it goes and searches the internet for you automatically.

That is Mode 1 of DocMind AI.

But you also need to write that literature review. So you type a research topic: "Compare and contrast self-attention, cross-attention, and multi-head attention in modern transformer architectures." And instead of a chat response, the tool goes away quietly and decomposes your topic into sub-questions, researches each one across your documents and the web, checks whether it missed anything, goes back to fill gaps, synthesizes everything into a narrative, and hands you a downloadable Word document with an executive summary, findings, gap analysis, and references. All formatted. All cited.

That is Mode 2 of DocMind AI.

Before this tool existed, the gap was simple: Large Language Models like ChatGPT could answer questions, but they hallucinated — they made things up because they had no access to YOUR specific documents. And even if you pasted text into the chat window, it could not search across multiple documents, track which source said what, or tell you how much it was guessing. DocMind AI exists to close that gap. It grounds AI responses in YOUR data, tells you when it is uncertain, and automates the research process that used to take days.

---

# CHAPTER 2: THE PLANNING PHASE

## What Was Built First and Why

The README has a Development Phases table showing Phase 1 (Foundation) as complete and Phases 2-7 as unchecked. But ALL phases are fully implemented in code — the README was never updated. The ordering tells us the build sequence:

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

- **No WebSocket/streaming** — chat is synchronous HTTP
- **No RBAC** — no `role` column on users. Admin is a shared password
- **No unit tests** — zero test files. RAGAS is the only quality validation
- **No Docker** — no Dockerfile or docker-compose
- **No file formats beyond PDF** — only `application/pdf` accepted
- **No real-time collaboration** — single-user sessions

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
  ┌─────────────────────────────────────────────────┐
  │ MIDDLEWARE: CORS + Rate Limiter + Security Hdrs  │
  ├─────────────────────────────────────────────────┤
  │ ROUTERS: auth | documents | chat | research     │
  │          admin | eval | health                   │
  ├─────────────────────────────────────────────────┤
  │ SERVICES: auth_service | doc_service             │
  │           chat_service | research_service        │
  ├─────────────────────────────────────────────────┤
  │ AI LAYER:  rag/indexer + rag/retriever           │
  │            agent/graph + agent/nodes (LangGraph) │
  │            agent/tools + agent/prompts            │
  ├─────────────────────────────────────────────────┤
  │ REPOSITORIES: user | token | document | chat     │
  │               research | eval                    │
  └────────┬──────────┬──────────┬──────────┬───────┘
           │          │          │          │
      PostgreSQL  ChromaDB  Gemini API  Tavily API
      (psycopg2)  (vectors)  (LLM+Embed) (Web Search)

SEPARATE PROCESS:
  Streamlit Eval Dashboard --> Backend API as eval@docmind.ai
  ragas_runner.py --> RAGAS lib --> Gemini (LLM-as-Judge)
```
