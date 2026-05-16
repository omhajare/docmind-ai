# 🧠 DocMind AI — Intelligent Research & Synthesis Agent

DocMind AI is a state-of-the-art full-stack platform designed to transform how users interact with documents and conduct research. It leverages advanced LLMs, retrieval-augmented generation (RAG), and autonomous agent workflows to provide two distinct modes of intelligence.

---

## 🚀 Core Features

### 🔹 Mode 1: Conversational Q&A (RAG)
*   **Context-Aware Chat:** Upload PDFs and ask complex questions.
*   **Source Citations:** Every answer includes precise citations from your uploaded documents.
*   **Hybrid Search:** Intelligent fallback to web search when document context is insufficient.
*   **Session Management:** Save and resume multiple chat threads with persistent history.

### 🔹 Mode 2: Deep Research Agent
*   **Autonomous Research:** LangGraph-powered agent that decomposes topics into sub-questions.
*   **Multi-Source Synthesis:** Synthesizes information from both your private library and the live web.
*   **Professional Reporting:** Automatically generates comprehensive `.docx` research reports.
*   **Reflection Loop:** The agent reviews its own findings to ensure accuracy and depth.

### 🔹 Advanced Platform Capabilities
*   **Admin Dashboard:** Monitor system health, user activity, and AI performance logs.
*   **RAGAS Evaluation:** Built-in dashboard to evaluate the quality (faithfulness, relevancy) of AI responses.
*   **Secure Auth:** Robust authentication with JWT, password hashing, and role-based access control.
*   **Responsive Design:** Modern, premium UI built with Tailwind CSS 4 and shadcn/ui.

---

## 🛠️ Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 19, Vite, TypeScript, Tailwind CSS 4, shadcn/ui, Lucide, Sonner |
| **Backend** | FastAPI (Python 3.11+), Uvicorn, Pydantic, Slowapi (Rate Limiting) |
| **AI / ML** | LangChain, LangGraph (Agentic Workflows), Google Gemini 2.0 Flash |
| **Database** | PostgreSQL (Local/Supabase), ChromaDB (Vector Store) |
| **Search & Mail** | Tavily (Web Search), Resend (Transactional Emails) |
| **Evaluation** | Streamlit, RAGAS, Plotly |

---

## 📂 Project Structure

```text
docmind-ai/
├── backend/            # FastAPI server, AI agents, and RAG logic
│   ├── agent/          # LangGraph research agent nodes and graph
│   ├── api/            # API routers (v1)
│   ├── rag/            # Document indexing and retrieval logic
│   ├── database/       # DB client and migrations
│   └── repositories/   # Data access layer
├── frontend/           # React + TypeScript dashboard
│   ├── src/components/ # Feature-based UI components
│   └── src/api/        # Axios service layers
├── eval_dashboard/     # Streamlit app for RAGAS evaluation
├── docs/               # System architecture and user guides
└── .env.example        # Master environment template
```

---

## 📖 Documentation

For in-depth technical details, please refer to the following:
*   [Technical Deep Dive](docs/TECHNICAL_DEEP_DIVE.md) — Detailed backend & AI architecture.
*   [Project Deep Dive](docs/PROJECT_DEEP_DIVE.md) — Comprehensive project overview.
*   [System Design Diagram](docs/DocMindSystemDesign.png) — Visual architecture overview.

---

## ⚙️ Getting Started

### 1️⃣ Prerequisites
*   Python 3.11+
*   Node.js 20+
*   PostgreSQL 14+ (or Supabase account)

### 2️⃣ Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # venv\Scripts\activate on Windows
pip install -r requirements.txt
cp ../.env.example .env   # Fill in GEMINI_API_KEY, DATABASE_URL, etc.
uvicorn main:app --reload
```

### 3️⃣ Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env     # Set VITE_API_URL to http://localhost:8000
npm run dev
```

### 4️⃣ Evaluation Dashboard (Optional)
```bash
cd eval_dashboard
pip install -r requirements.txt
cp .env.example .env     # Must match backend ADMIN_PASSWORD
streamlit run dashboard.py
```

---

## 🔑 Key Environment Variables

| Variable | Description |
| :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string. |
| `GEMINI_API_KEY` | Google AI Studio key for LLM and Embeddings. |
| `TAVILY_API_KEY` | Required for Deep Research and Web Fallback. |
| `JWT_SECRET_KEY` | Secret for signing authentication tokens. |
| `ADMIN_PASSWORD` | Access key for the Admin panel and Eval dashboard. |

---

## 📜 Development Roadmap

- [x] Phase 1: Foundation & Auth
- [x] Phase 2: Document Indexing & RAG Pipeline
- [x] Phase 3: Conversational Mode 1
- [x] Phase 4: LangGraph Research Agent (Mode 2)
- [x] Phase 5: Admin & Evaluation Dashboard
- [ ] Phase 6: Production Hardening & Deployment

---

## 🛡️ License & Acknowledgements
Built with ❤️ by the DocMind team. Powered by Google Gemini and LangChain.
